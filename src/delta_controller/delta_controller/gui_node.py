"""
Giao diện cửa sổ điều khiển robot delta — thay cho việc gõ lệnh.

    ros2 run delta_controller gui

Dùng LẠI nguyên `CartesianController` của nút gõ lệnh, chỉ thay vòng `input()` bằng cửa sổ. Nhờ
vậy hai cách điều khiển không thể lệch nhau về hành vi: cùng một lớp lập kế hoạch, cùng một bộ
kiểm chứng, cùng một vòng băng tải. Thêm một nút ở đây không bao giờ phải viết lại logic.

⚠️ KHÔNG chạy đồng thời với `cartesian_control` hay `follow`: cả ba cùng ra lệnh cho robot qua
`cmd_pos` và sẽ tranh nhau.

Ba điều giao diện này cố ý làm:

1. **Không cho bấm hai lệnh cùng lúc.** Mọi nút bị khóa trong lúc một tác vụ đang chạy. Robot chỉ
   có một, và hai chuỗi chuyển động chồng nhau thì không lệnh nào tới nơi.
2. **Chạy tác vụ ở luồng riêng.** Tác vụ gắp–thả mất vài chục giây; chạy trong luồng giao diện sẽ
   làm cửa sổ đứng hình và người dùng tưởng máy treo.
3. **Hiện thứ hệ thống ĐANG THẤY, không phải thứ nó được bảo.** Bảng vật thể lấy thẳng từ camera
   kèm cờ tin cậy, nên nhìn là biết vì sao một nút bị từ chối.
"""

import queue
import threading
import time
import tkinter as tk
from tkinter import ttk

from delta_controller.cartesian_control_node import CartesianController, SOURCE_ALIASES
from delta_controller.conveyor_runner import ConveyorError, ConveyorRunner
from delta_controller.delta_kinematics import UnreachableError
from delta_controller.scene import BINS, OBJECTS, SCALE
from delta_controller.task_planner import locate, object_states, TaskError
import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.signals import SignalHandlerOptions

REFRESH_MS = 300
HOME_XYZ = (0.0, 0.0, -0.1405)

# Màu nền nút chọn vật, lấy theo đúng lớp màu mà khối thị giác dùng để nhận dạng.
COLOR_CHIP = {'red': '#dc2626', 'blue': '#2563eb', 'green': '#059669'}
NICE_NAME = {'coca_can': 'Coca (đỏ)', 'pepsi_can': 'Pepsi (lam)', 'sevenup_can': '7Up (lục)'}


class ControlWindow:
    """Cửa sổ điều khiển. Giao diện ở luồng chính, tác vụ ở luồng phụ."""

    def __init__(self, node):
        self._node = node
        self._busy = False
        self._log_queue = queue.Queue()
        self._runner = None
        self._buttons = []

        self.root = tk.Tk()
        self.root.title('Điều khiển robot delta')
        self.root.minsize(900, 620)
        self._build_style()
        self._build()
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)
        self.root.after(REFRESH_MS, self._refresh)

    # -------------------------------------------------------------- dựng giao diện
    def _build_style(self):
        style = ttk.Style()
        for theme in ('clam', 'alt', 'default'):
            if theme in style.theme_names():
                style.theme_use(theme)
                break
        style.configure('.', font=('DejaVu Sans', 10))
        style.configure('Head.TLabel', font=('DejaVu Sans', 11, 'bold'))
        style.configure('Val.TLabel', font=('DejaVu Sans Mono', 10))
        style.configure('Big.TButton', font=('DejaVu Sans', 10), padding=(10, 8))
        style.configure('Go.TButton', font=('DejaVu Sans', 10, 'bold'), padding=(10, 8))

    def _build(self):
        pad = {'padx': 8, 'pady': 6}
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill='both', expand=True)

        # --- hàng trên: trạng thái + vật thể
        row = ttk.Frame(top)
        row.pack(fill='x')

        state = ttk.LabelFrame(row, text=' Trạng thái ', padding=10)
        state.pack(side='left', fill='both', expand=True, **pad)
        self._lbl = {}
        for i, (key, text) in enumerate((('conn', 'Kết nối'), ('tool', 'Đầu hút'),
                                         ('held', 'Đang giữ'), ('cycle', 'Vòng băng tải'))):
            ttk.Label(state, text=text + ':').grid(row=i, column=0, sticky='w', pady=2)
            self._lbl[key] = ttk.Label(state, text='…', style='Val.TLabel')
            self._lbl[key].grid(row=i, column=1, sticky='w', padx=(10, 0), pady=2)

        ttk.Label(state, text='Nguồn vị trí:').grid(row=4, column=0, sticky='w', pady=(10, 2))
        self._source = tk.StringVar(value=self._node.object_source)
        src = ttk.Frame(state)
        src.grid(row=4, column=1, sticky='w', padx=(10, 0), pady=(10, 2))
        for text, val in (('Camera', 'camera'), ('Vị trí thật', 'ground_truth')):
            ttk.Radiobutton(src, text=text, value=val, variable=self._source,
                            command=self._on_source).pack(side='left', padx=(0, 8))

        objs = ttk.LabelFrame(row, text=' Vật thể hệ thống đang thấy ', padding=10)
        objs.pack(side='left', fill='both', expand=True, **pad)
        self._tree = ttk.Treeview(objs, columns=('where', 'pos', 'score'), show='tree headings',
                                  height=4)
        self._tree.heading('#0', text='Vật')
        self._tree.heading('where', text='Đang ở')
        self._tree.heading('pos', text='Vị trí (mm thật)')
        self._tree.heading('score', text='Tin cậy')
        self._tree.column('#0', width=130)
        self._tree.column('where', width=110)
        self._tree.column('pos', width=140, anchor='e')
        self._tree.column('score', width=70, anchor='center')
        self._tree.pack(fill='both', expand=True)

        # --- chọn vật + thao tác với một vật
        one = ttk.LabelFrame(top, text=' Thao tác với một vật ', padding=10)
        one.pack(fill='x', **pad)
        pick_row = ttk.Frame(one)
        pick_row.pack(fill='x', pady=(0, 8))
        ttk.Label(pick_row, text='Chọn vật:').pack(side='left', padx=(0, 10))
        self._target = tk.StringVar(value=OBJECTS[0].name)
        for obj in OBJECTS:
            chip = tk.Frame(pick_row, bg=COLOR_CHIP.get(obj.color, '#888'), width=14, height=14)
            chip.pack(side='left', padx=(6, 3))
            chip.pack_propagate(False)
            ttk.Radiobutton(pick_row, text=NICE_NAME.get(obj.name, obj.name),
                            value=obj.name, variable=self._target).pack(side='left')
        act = ttk.Frame(one)
        act.pack(fill='x')
        for text, fn in (('Đi tới vật', self._goto), ('Nhặt lên', self._pick),
                         ('Thả vào khay', self._place), ('Chuyển vào khay', self._pick_place),
                         ('Lấy ra bàn', self._unload)):
            self._add_button(act, text, fn, style='Big.TButton')

        # --- toàn cảnh
        allf = ttk.LabelFrame(top, text=' Toàn cảnh ', padding=10)
        allf.pack(fill='x', **pad)
        for text, fn in (('Phân loại tất cả', self._sort), ('Trả về chỗ cũ', self._reset),
                         ('Về vị trí gốc', self._home)):
            self._add_button(allf, text, fn, style='Big.TButton')

        # --- băng tải
        belt = ttk.LabelFrame(top, text=' Vòng băng tải ', padding=10)
        belt.pack(fill='x', **pad)
        self._add_button(belt, 'Bắt đầu vòng', self._cycle_start, style='Go.TButton')
        self._stop_btn = ttk.Button(belt, text='Dừng vòng', command=self._cycle_stop,
                                    style='Big.TButton', state='disabled')
        self._stop_btn.pack(side='left', padx=4)
        ttk.Label(belt, text='Đặt MỘT vật lên đầu nạp, hệ thống tự chạy băng và gắp.').pack(
            side='left', padx=(14, 0))

        # --- nhật ký
        logf = ttk.LabelFrame(top, text=' Nhật ký ', padding=6)
        logf.pack(fill='both', expand=True, **pad)
        self._log = tk.Text(logf, height=9, wrap='word', font=('DejaVu Sans Mono', 9),
                            bg='#f8fafc', relief='flat')
        bar = ttk.Scrollbar(logf, command=self._log.yview)
        self._log.configure(yscrollcommand=bar.set, state='disabled')
        bar.pack(side='right', fill='y')
        self._log.pack(side='left', fill='both', expand=True)
        for tag, color in (('ok', '#047857'), ('err', '#b91c1c'), ('info', '#1f2933')):
            self._log.tag_configure(tag, foreground=color)

    def _add_button(self, parent, text, command, style='TButton'):
        btn = ttk.Button(parent, text=text, command=command, style=style)
        btn.pack(side='left', padx=4)
        self._buttons.append(btn)
        return btn

    # -------------------------------------------------------------- chạy tác vụ
    def say(self, text, tag='info'):
        self._log_queue.put((text, tag))

    def _run_task(self, label, fn):
        """
        Chạy một tác vụ ở luồng phụ, khóa nút trong lúc chạy.

        Khóa nút không phải để đẹp: robot chỉ có một, hai chuỗi chuyển động chồng lên nhau thì
        không chuỗi nào tới đích, và bộ kiểm chứng sẽ báo thất bại một cách khó hiểu.
        """
        if self._busy:
            self.say('Đang bận, chờ tác vụ hiện tại xong đã.', 'err')
            return
        self._busy = True
        self._set_enabled(False)
        self.say(f'▶ {label}')

        def worker():
            try:
                fn()
                self.say(f'✓ {label} — xong', 'ok')
            except (TaskError, UnreachableError, ConveyorError) as err:
                self.say(f'✗ {label}: {err}', 'err')
            except (ValueError, RuntimeError) as err:
                self.say(f'✗ {label}: {err}', 'err')
            finally:
                self._busy = False
                self.root.after(0, lambda: self._set_enabled(True))

        threading.Thread(target=worker, daemon=True).start()

    def _set_enabled(self, on):
        for btn in self._buttons:
            btn.configure(state='normal' if on else 'disabled')
        self._stop_btn.configure(state='disabled' if on else 'normal')

    def _executor(self):
        return self._node.task_executor

    # -------------------------------------------------------------- các lệnh
    def _on_source(self):
        self._node.object_source = SOURCE_ALIASES[self._source.get()]
        self.say(f'Nguồn vị trí vật: {self._node.object_source}')

    def _goto(self):
        name = self._target.get()
        self._run_task(f'Đi tới {NICE_NAME.get(name, name)}',
                       lambda: self._executor().goto(name))

    def _pick(self):
        name = self._target.get()
        self._run_task(f'Nhặt {NICE_NAME.get(name, name)}',
                       lambda: self._executor().pick(name))

    def _place(self):
        self._run_task('Thả vào khay', self._executor().place)

    def _pick_place(self):
        name = self._target.get()
        self._run_task(f'Chuyển {NICE_NAME.get(name, name)} vào khay',
                       lambda: self._executor().pick_place(name))

    def _unload(self):
        name = self._target.get()
        self._run_task(f'Lấy {NICE_NAME.get(name, name)} ra bàn',
                       lambda: self._executor().unload(name))

    def _sort(self):
        self._run_task('Phân loại tất cả', self._executor().sort)

    def _reset(self):
        self._run_task('Trả mọi vật về chỗ cũ', self._executor().reset)

    def _home(self):
        self._run_task('Về vị trí gốc', lambda: self._node.move(HOME_XYZ, safe=True))

    def _cycle_start(self):
        if self._node.object_source != 'camera':
            self.say('Vòng băng tải chỉ chạy ở chế độ camera — hãy chọn nguồn Camera.', 'err')
            return
        if self._node.conveyor_runner is None:
            self._node.conveyor_runner = ConveyorRunner(self._node, log=self.say)
        self._runner = self._node.conveyor_runner
        self._run_task('Vòng băng tải', lambda: self._runner.run(None))

    def _cycle_stop(self):
        if self._runner is not None:
            self._runner.request_stop()
            self.say('Đã yêu cầu dừng vòng băng tải…')

    # -------------------------------------------------------------- cập nhật
    def _refresh(self):
        while True:
            try:
                text, tag = self._log_queue.get_nowait()
            except queue.Empty:
                break
            self._log.configure(state='normal')
            self._log.insert('end', time.strftime('%H:%M:%S ') + text + '\n', tag)
            self._log.see('end')
            self._log.configure(state='disabled')

        pos = self._node.current_position()
        self._lbl['conn'].configure(text='đã kết nối' if pos is not None else 'chưa có dữ liệu')
        self._lbl['tool'].configure(
            text='—' if pos is None else
            f'{1000 * pos[0]:+7.1f} {1000 * pos[1]:+7.1f} {1000 * pos[2]:+7.1f} mm ảo')
        held = self._node.held_object
        self._lbl['held'].configure(text=held if held else '(không giữ vật nào)')
        runner = self._node.conveyor_runner
        self._lbl['cycle'].configure(
            text=runner.cycle.state if (runner is not None and self._busy) else 'không chạy')

        self._refresh_objects(held)
        self.root.after(REFRESH_MS, self._refresh)

    def _refresh_objects(self, held):
        """Bảng vật thể: lấy thẳng khung camera mới nhất, kèm cờ tin cậy."""
        seen = self._node.latest_vision()
        rows = []
        for obj in OBJECTS:
            entry = seen.get(obj.name)
            nice = NICE_NAME.get(obj.name, obj.name)
            if entry is None:
                rows.append((obj.name, nice, 'không thấy', '—', '—'))
                continue
            x, y, z, score = entry
            states = object_states({obj.name: (x, y, z)})
            where = locate(obj.name, states[obj.name], held)
            rows.append((obj.name, nice, where,
                         f'{SCALE * x * 1000:+.0f}, {SCALE * y * 1000:+.0f}',
                         f'{score:.2f}' if score > 0 else 'KHÔNG'))
        self._tree.delete(*self._tree.get_children())
        for name, nice, where, pos, score in rows:
            self._tree.insert('', 'end', text=nice, values=(where, pos, score))

    def _on_close(self):
        if self._runner is not None:
            self._runner.request_stop()
        self.root.destroy()


def main(args=None):
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    node = CartesianController()
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    spin = threading.Thread(target=executor.spin, daemon=True)
    spin.start()

    window = ControlWindow(node)
    window.say('Đang chờ kết nối tới mô phỏng…')
    if node.wait_for_connection():
        window.say('Đã kết nối.', 'ok')
    else:
        window.say('Cảnh báo: chưa kết nối được mô phỏng (cmd_pos / joint_states).', 'err')
    window.say(f'Có {len(BINS)} khay phân loại. Nguồn vị trí vật: {node.object_source}.')

    try:
        window.root.mainloop()
    finally:
        executor.shutdown()
        spin.join(timeout=2.0)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

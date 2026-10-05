"""
Cho phép chạy script trong thư mục này mà CHƯA `source install/setup.bash`.

Python tự đặt thư mục chứa script vào đầu sys.path, nên chỉ cần import module này là thư mục gốc
của package (một cấp trên) cũng được thêm vào — khi đó `import delta_controller` chạy được từ mã
nguồn. Đặt dòng `import _workspace  # noqa: F401` TRƯỚC mọi import delta_controller.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')))

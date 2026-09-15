"""
Logic chọn vật cho giác hút ảo (thuần Python, không phụ thuộc ROS).

Giác hút chỉ hút được khi mặt dưới platform nằm sát đỉnh vật và tâm platform ở gần tâm vật
theo phương ngang — giống giác hút chân không thật cần tiếp xúc với bề mặt vật.
"""

from dataclasses import dataclass
import math

# Platform (tool0) là tấm dày 6 mm, tâm tool0 ở giữa tấm -> mặt dưới = z_tool0 - 0.003.
PLATFORM_HALF_THICKNESS = 0.003


@dataclass(frozen=True)
class GraspTolerance:
    """Dung sai hút vật (m)."""

    max_xy_offset: float = 0.012   # lệch ngang tâm platform so với tâm vật
    min_gap: float = -0.004        # khe (mặt dưới platform - đỉnh vật); âm = đã lún vào vật
    max_gap: float = 0.006         # khe lớn nhất vẫn hút được


@dataclass(frozen=True)
class ObjectState:
    """Vị trí tâm vật trong hệ robot và nửa chiều cao (m)."""

    center: tuple
    half_height: float

    @property
    def top_z(self):
        return self.center[2] + self.half_height


class NoGraspableObject(Exception):
    """Không có vật nào nằm trong vùng hút của platform."""


def grasp_offsets(tool_xyz, obj):
    """Trả về (lệch ngang, khe đứng) giữa platform và đỉnh vật."""
    xy_offset = math.hypot(tool_xyz[0] - obj.center[0], tool_xyz[1] - obj.center[1])
    gap = (tool_xyz[2] - PLATFORM_HALF_THICKNESS) - obj.top_z
    return xy_offset, gap


def select_graspable(tool_xyz, objects, tolerance=GraspTolerance()):
    """
    Chọn vật hút được gần nhất (theo phương ngang) dưới platform.

    objects: dict tên -> ObjectState. Ném NoGraspableObject kèm gợi ý nếu không có vật nào.
    """
    if not objects:
        raise NoGraspableObject('Chua nhan duoc vi tri vat nao')

    candidates = []
    for name, obj in objects.items():
        xy_offset, gap = grasp_offsets(tool_xyz, obj)
        ok = (xy_offset <= tolerance.max_xy_offset
              and tolerance.min_gap <= gap <= tolerance.max_gap)
        candidates.append((xy_offset, name, gap, ok))
    candidates.sort()

    for xy_offset, name, gap, ok in candidates:
        if ok:
            return name

    xy_offset, name, gap, _ = candidates[0]
    obj = objects[name]
    hint_z = obj.top_z + PLATFORM_HALF_THICKNESS
    raise NoGraspableObject(
        f'Khong co vat trong vung hut. Gan nhat: {name} lech ngang {xy_offset * 1000:.1f} mm '
        f'(cho phep {tolerance.max_xy_offset * 1000:.0f}), khe {gap * 1000:+.1f} mm '
        f'(cho phep {tolerance.min_gap * 1000:+.0f}..{tolerance.max_gap * 1000:+.0f}). '
        f'Goi y: di toi ({obj.center[0]:.4f}, {obj.center[1]:.4f}, {hint_z:.4f})')

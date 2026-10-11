#!/usr/bin/env python3
"""
Sinh hình minh họa cho khóa luận (Chương 1–2).

    python3 docs/tools/make_thesis_figures.py

Mọi hình vẽ từ THÔNG SỐ THẬT của robot trong `delta_kinematics`, không vẽ phác bằng tay — nên
hình luôn khớp với công thức và số liệu trong bài, và sửa thông số là hình tự đúng theo.
"""

import math
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt                                    # noqa: E402
from matplotlib.patches import Arc, Circle, FancyArrowPatch, Polygon, Rectangle  # noqa: E402
import numpy as np                                                 # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..',
                                'src', 'delta_controller'))
from delta_controller.delta_kinematics import (                    # noqa: E402
    DEFAULT_GEOMETRY, LEG_ANGLES, forward_kinematics, inverse_kinematics,
)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')
G = DEFAULT_GEOMETRY
plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 11,
    'axes.linewidth': 0.8, 'figure.dpi': 200,
    'savefig.bbox': 'tight', 'savefig.pad_inches': 0.08,
})
INK, ARM, ROD, PLAT, HINT = '#1b2430', '#1f6feb', '#d1495b', '#2a9d8f', '#8a94a6'


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path)
    plt.close(fig)
    print(f'  {name}')


def arrow(ax, p, q, color=INK, lw=1.1, style='-|>', ms=9):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=ms,
                                 lw=lw, color=color, shrinkA=0, shrinkB=0))


# ------------------------------------------------------------------ Chương 2: hình học

def fig_parameters():
    """Bốn thông số hình học trên một sơ đồ mặt cắt."""
    fig, ax = plt.subplots(figsize=(7.0, 4.4))
    f, e, rf, re = G.f, G.e, G.rf, G.re
    theta = 0.35
    base = np.array([f, 0.0])
    elbow = base + rf * np.array([math.cos(-theta), math.sin(-theta)])
    plat = np.array([e, -0.1405])
    ax.plot([-f, f], [0, 0], color=INK, lw=3.4, solid_capstyle='round')
    ax.plot([base[0], elbow[0]], [base[1], elbow[1]], color=ARM, lw=3.4, solid_capstyle='round')
    ax.plot([elbow[0], plat[0]], [elbow[1], plat[1]], color=ROD, lw=2.6, solid_capstyle='round')
    ax.plot([plat[0], -e], [plat[1], plat[1]], color=PLAT, lw=3.4, solid_capstyle='round')
    for p, c in ((base, INK), (elbow, ARM), (plat, ROD)):
        ax.add_patch(Circle(p, 0.0048, color=c, zorder=5))
    # kích thước f (trên) và e (dưới)
    ax.annotate('', (0, 0.026), (f, 0.026), arrowprops=dict(arrowstyle='<->', color=HINT, lw=0.9))
    ax.text(f / 2, 0.033, '$f$ = 41,7', ha='center', color=HINT, fontsize=10.5)
    ax.annotate('', (0, plat[1] - 0.030), (e, plat[1] - 0.030),
                arrowprops=dict(arrowstyle='<->', color=HINT, lw=0.9))
    ax.text(e / 2, plat[1] - 0.050, '$e$ = 27,6', ha='center', color=HINT, fontsize=10.5)
    ax.plot([0, 0], [0.020, plat[1] - 0.034], color=HINT, lw=0.7, ls=':')
    ax.plot([f, f], [0, 0.030], color=HINT, lw=0.7, ls=':')
    ax.plot([e, e], [plat[1], plat[1] - 0.034], color=HINT, lw=0.7, ls=':')
    # nhãn đặt cạnh từng đoạn
    mid = (base + elbow) / 2
    ax.text(mid[0] + 0.004, mid[1] + 0.016, 'cánh tay trên\n$r_f$ = 75,8',
            color=ARM, fontsize=10.5, ha='left')
    mid = (elbow + plat) / 2
    ax.text(mid[0] + 0.024, mid[1], 'thanh chống\n$r_e$ = 166,8', color=ROD, fontsize=10.5)
    ax.text(-f - 0.010, 0.008, 'đế cố định', color=INK, fontsize=10.5, ha='right')
    ax.text(-e - 0.010, plat[1] + 0.002, 'bàn máy động', color=PLAT, fontsize=10.5, ha='right')
    # góc khớp: từ phương ngang hướng RA NGOÀI, quay xuống
    ax.plot([base[0], base[0] + 0.052], [0, 0], color=HINT, lw=0.8, ls='--')
    ax.add_patch(Arc(base, 0.072, 0.072, theta1=-math.degrees(theta), theta2=0,
                     color=INK, lw=1.1))
    ax.text(base[0] + 0.041, base[1] - 0.014, r'$\theta_i$', fontsize=13)
    ax.text(0.003, 0.007, '$O$', fontsize=11.5)
    ax.text(0.085, -0.195, 'đơn vị: mm', color=HINT, fontsize=10, style='italic')
    ax.set_xlim(-0.125, 0.205)
    ax.set_ylim(-0.215, 0.055)
    ax.set_aspect('equal')
    ax.axis('off')
    save(fig, 'kl_thong_so_hinh_hoc.png')


def fig_frames():
    """Hệ trục tọa độ và ba chân lệch nhau 120°, nhìn từ trên xuống."""
    fig, ax = plt.subplots(figsize=(5.0, 5.0))
    f = G.f
    ax.add_patch(Circle((0, 0), f, fill=False, color=HINT, lw=0.9, ls='--'))
    for k, phi in enumerate(LEG_ANGLES):
        p = f * np.array([math.cos(phi), math.sin(phi)])
        ax.plot([0, p[0]], [0, p[1]], color=HINT, lw=0.8, ls=':')
        ax.add_patch(Circle(p, 0.004, color=ARM, zorder=4))
        lab = p * 1.22
        ax.text(lab[0], lab[1], f'chân {k + 1}\n$\\varphi_{k + 1}$ = {int(round(math.degrees(phi)))}°',
                ha='center', va='center', fontsize=10, color=ARM)
        if k:
            ax.add_patch(Arc((0, 0), 2 * f * 0.55, 2 * f * 0.55, theta1=0,
                             theta2=math.degrees(phi), color=HINT, lw=0.8))
    arrow(ax, (0, 0), (f * 1.75, 0), color=INK)
    arrow(ax, (0, 0), (0, f * 1.75), color=INK)
    ax.text(f * 1.82, 0, '$X$', fontsize=12, va='center')
    ax.text(0, f * 1.84, '$Y$', fontsize=12, ha='center')
    ax.add_patch(Circle((0, 0), 0.0055, fill=False, color=INK, lw=1.1))
    ax.add_patch(Circle((0, 0), 0.0018, color=INK))
    ax.text(0.006, -0.010, '$Z$ hướng lên\n(ra phía người đọc)', fontsize=9.5, color=INK)
    ax.set_xlim(-0.085, 0.095)
    ax.set_ylim(-0.085, 0.09)
    ax.set_aspect('equal')
    ax.axis('off')
    save(fig, 'kl_he_truc.png')


def fig_leg_plane():
    """Sơ đồ một chân trong mặt phẳng chứa nó — hình gốc của bài toán động học ngược."""
    fig, ax = plt.subplots(figsize=(6.8, 4.6))
    f, e, rf, re = G.f, G.e, G.rf, G.re
    x0, y0, z0 = 0.03, 0.0, -0.17
    theta = inverse_kinematics(x0, y0, z0)[0]
    base = np.array([f, 0.0])
    elbow = base + rf * np.array([math.cos(-theta), math.sin(-theta)])
    target = np.array([x0 + e, z0])
    ax.plot([-0.01, f + 0.012], [0, 0], color=INK, lw=2.6, solid_capstyle='round')
    ax.plot([base[0], elbow[0]], [base[1], elbow[1]], color=ARM, lw=3.2, solid_capstyle='round')
    ax.plot([elbow[0], target[0]], [elbow[1], target[1]], color=ROD, lw=2.3,
            solid_capstyle='round')
    ax.plot([target[0] - 0.028, target[0] + 0.012], [target[1], target[1]],
            color=PLAT, lw=3, solid_capstyle='round')
    ax.plot([0, 0], [0.012, z0 - 0.02], color=HINT, lw=0.8, ls=':')
    ax.plot([target[0], target[0]], [0, target[1]], color=HINT, lw=0.8, ls=':')
    ax.plot([0, target[0]], [target[1], target[1]], color=HINT, lw=0.8, ls=':')
    for p, c, lab, dx, dy in ((base, INK, '$A_i$', 0.004, 0.010),
                              (elbow, ARM, '$B_i$', 0.006, 0.006),
                              (target, ROD, '$C_i$', 0.006, -0.004)):
        ax.add_patch(Circle(p, 0.0042, color=c, zorder=5))
        ax.text(p[0] + dx, p[1] + dy, lab, fontsize=12, color=c)
    ax.plot([base[0], base[0] + 0.046], [0, 0], color=HINT, lw=0.8, ls='--')
    ax.add_patch(Arc(base, 0.062, 0.062, theta1=-math.degrees(theta), theta2=0,
                     color=INK, lw=1.1))
    ax.text(base[0] + 0.036, base[1] - 0.013, r'$\theta_i$', fontsize=13)
    ax.annotate('', (0, 0.020), (f, 0.020), arrowprops=dict(arrowstyle='<->', color=HINT, lw=0.9))
    ax.text(f / 2, 0.026, '$f$', ha='center', color=HINT, fontsize=11)
    ax.annotate('', (0, target[1] - 0.026), (target[0], target[1] - 0.026),
                arrowprops=dict(arrowstyle='<->', color=HINT, lw=0.9))
    ax.text(target[0] / 2, target[1] - 0.042, '$x_i + e$', ha='center', color=HINT, fontsize=11)
    ax.annotate('', (-0.016, 0), (-0.016, target[1]),
                arrowprops=dict(arrowstyle='<->', color=HINT, lw=0.9))
    ax.text(-0.034, target[1] / 2, '$z_i$', va='center', color=HINT, fontsize=11)
    ax.text((base[0] + elbow[0]) / 2 - 0.004, (base[1] + elbow[1]) / 2 + 0.012,
            '$r_f$', color=ARM, fontsize=12)
    ax.text((elbow[0] + target[0]) / 2 + 0.006, (elbow[1] + target[1]) / 2,
            '$r_e$', color=ROD, fontsize=12)
    ax.text(0.003, 0.006, '$O$', fontsize=11)
    ax.set_xlim(-0.055, 0.155)
    ax.set_ylim(-0.215, 0.045)
    ax.set_aspect('equal')
    ax.axis('off')
    save(fig, 'kl_mat_phang_chan.png')


def fig_elbow_branches():
    """Hai nghiệm của phương trình lượng giác: khuỷu RA NGOÀI và khuỷu VÀO TRONG."""
    fig, ax = plt.subplots(figsize=(6.6, 4.4))
    f, e, rf, re = G.f, G.e, G.rf, G.re
    x0, z0 = -0.02, -0.16
    xi = x0 + e
    a = xi - f
    A, B, C = -2 * rf * a, 2 * rf * z0, a * a + z0 * z0 + rf * rf - re * re
    disc = math.sqrt(A * A + B * B - C * C)
    base = np.array([f, 0.0])
    target = np.array([xi, z0])
    for sign, color, style, name in ((+1, ARM, '-', 'khuỷu RA NGOÀI (chọn)'),
                                     (-1, HINT, '--', 'khuỷu VÀO TRONG (loại)')):
        t = (-B + sign * disc) / (C - A)
        th = 2 * math.atan(t)
        elbow = base + rf * np.array([math.cos(-th), math.sin(-th)])
        ax.plot([base[0], elbow[0]], [base[1], elbow[1]], color=color, lw=3,
                ls=style, solid_capstyle='round', label=f'{name}: $\\theta$ = {math.degrees(th):.1f}°')
        ax.plot([elbow[0], target[0]], [elbow[1], target[1]], color=color, lw=1.8, ls=style)
        ax.add_patch(Circle(elbow, 0.004, color=color, zorder=5))
    ax.add_patch(Circle(base, 0.0045, color=INK, zorder=5))
    ax.add_patch(Circle(target, 0.0045, color=ROD, zorder=5))
    ax.plot([-0.01, f + 0.012], [0, 0], color=INK, lw=2.6, solid_capstyle='round')
    ax.text(base[0] + 0.005, 0.009, '$A_i$', fontsize=12)
    ax.text(target[0] - 0.004, target[1] - 0.016, '$C_i$', fontsize=12, color=ROD)
    ax.set_xlim(-0.065, 0.115)
    ax.set_ylim(-0.195, 0.055)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.legend(loc='upper left', frameon=False, fontsize=10)
    save(fig, 'kl_hai_nhanh_khuyu.png')


def _reachable(x, y, z):
    """Điểm có giải được động học ngược không (dùng để dò biên vùng làm việc)."""
    try:
        inverse_kinematics(x, y, z)
        return True
    except ValueError:
        return False


def fig_trilateration():
    """Động học thuận = giao ba mặt cầu; vẽ mặt cắt ngang tại cao độ bàn máy."""
    fig, ax = plt.subplots(figsize=(5.4, 5.0))
    thetas = (0.25, 0.05, 0.45)
    x, y, z = forward_kinematics(*thetas)
    centers = []
    for phi, th in zip(LEG_ANGLES, thetas):
        u = np.array([math.cos(phi), math.sin(phi)])
        a = G.f + G.rf * math.cos(th)
        centers.append((a * u - G.e * u, -G.rf * math.sin(th)))
    for k, (c2, cz) in enumerate(centers):
        rr = math.sqrt(max(G.re ** 2 - (z - cz) ** 2, 1e-9))
        ax.add_patch(Circle(c2, rr, fill=False, color=[ARM, ROD, PLAT][k], lw=1.5))
        ax.add_patch(Circle(c2, 0.0045, color=[ARM, ROD, PLAT][k], zorder=5))
        ax.text(c2[0] * 1.08 - 0.004, c2[1] * 1.08, f'$C_{k + 1}$',
                color=[ARM, ROD, PLAT][k], fontsize=12)
    ax.add_patch(Circle((x, y), 0.006, color=INK, zorder=6))
    ax.text(x + 0.008, y + 0.006, 'giao điểm\n= bàn máy', fontsize=10.5, color=INK)
    ax.text(0.5, -0.02, 'mặt cắt ngang tại $z_0$ = %.1f mm' % (z * 1000),
            transform=ax.transAxes, ha='center', color=HINT, fontsize=10, style='italic')
    ax.set_xlim(-0.20, 0.20)
    ax.set_ylim(-0.20, 0.20)
    ax.set_aspect('equal')
    ax.axis('off')
    save(fig, 'kl_giao_ba_mat_cau.png')


def fig_workspace():
    """Vùng làm việc: bán kính với tới theo mọi hướng, tại từng cao độ."""
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    zs = np.linspace(-0.238, -0.100, 100)
    radii = []
    for z in zs:
        lo, hi = 0.0, 0.17
        for _ in range(36):
            mid = (lo + hi) / 2
            ok = all(_reachable(mid * math.cos(a), mid * math.sin(a), z)
                     for a in np.linspace(0, 2 * math.pi, 24, endpoint=False))
            lo, hi = (mid, hi) if ok else (lo, mid)
        radii.append(lo * 1000)
    radii = np.array(radii)
    zmm = zs * 1000
    poly = np.concatenate([np.column_stack([radii, zmm]),
                           np.column_stack([-radii[::-1], zmm[::-1]])])
    ax.add_patch(Polygon(poly, closed=True, facecolor=ARM, alpha=0.15, edgecolor=ARM, lw=2.0))
    ax.axhline(-220, color=INK, lw=2.4)
    ax.text(-148, -217, 'mặt bàn  −220', fontsize=10, color=INK, va='bottom')
    for z, lab in ((-140.5, 'tư thế gốc  −140,5'), (-190, 'cao độ gắp vật  −190')):
        ax.axhline(z, color=HINT, lw=0.8, ls=':')
        k = int(np.argmin(np.abs(zmm - z)))
        ax.plot([0], [z], marker='|', color=HINT)
        ax.text(-148, z + 2, f'{lab}   (bán kính {radii[k]:.0f} mm)',
                fontsize=9.5, color=HINT, va='bottom')
    ax.set_xlabel('bán kính với tới theo mọi hướng (mm)')
    ax.set_ylabel('cao độ $z_0$ (mm)')
    ax.set_xlim(-152, 152)
    ax.set_ylim(-242, -96)
    ax.grid(alpha=0.25, lw=0.6)
    ax.set_axisbelow(True)
    save(fig, 'kl_vung_lam_viec.png')


def fig_quintic():
    """Biên dạng bậc năm: vị trí, vận tốc, gia tốc đều liên tục, hai đầu bằng 0."""
    fig, axes = plt.subplots(3, 1, figsize=(6.2, 5.2), sharex=True)
    tau = np.linspace(0, 1, 400)
    sp = 10 * tau ** 3 - 15 * tau ** 4 + 6 * tau ** 5
    sv = 30 * tau ** 2 - 60 * tau ** 3 + 30 * tau ** 4
    sa = 60 * tau - 180 * tau ** 2 + 120 * tau ** 3
    for ax, data, color, lab in ((axes[0], sp, ARM, 'quãng đường  $s(\tau)$'),
                                 (axes[1], sv, ROD, r'vận tốc  $\dot{s}$'),
                                 (axes[2], sa, PLAT, r'gia tốc  $\ddot{s}$')):
        ax.plot(tau, data, color=color, lw=2.2)
        ax.axhline(0, color=HINT, lw=0.7)
        ax.set_ylabel(lab, fontsize=10.5)
        ax.grid(alpha=0.25, lw=0.6)
        ax.set_axisbelow(True)
    axes[1].annotate('đỉnh 1,875', (0.5, 1.875), (0.60, 1.55), fontsize=10, color=ROD,
                     arrowprops=dict(arrowstyle='->', color=ROD, lw=0.9))
    axes[0].annotate('hai đầu: vận tốc và gia tốc đều bằng 0', (0.02, 0.06), (0.14, 0.62),
                     fontsize=10, color=HINT,
                     arrowprops=dict(arrowstyle='->', color=HINT, lw=0.9))
    axes[2].set_xlabel('thời gian chuẩn hóa  $\tau = t/T$')
    save(fig, 'kl_bien_dang_bac_nam.png')


def fig_safe_path():
    """Quỹ đạo an toàn ba đoạn: nâng thẳng đứng, đi ngang, hạ thẳng đứng."""
    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    start, goal, safe = np.array([-0.06, -0.205]), np.array([0.06, -0.205]), -0.16
    way = [start, np.array([start[0], safe]), np.array([goal[0], safe]), goal]
    xs = [p[0] * 1000 for p in way]
    zs = [p[1] * 1000 for p in way]
    ax.plot(xs, zs, color=ARM, lw=2.6, marker='o', ms=6, solid_capstyle='round',
            label='quỹ đạo an toàn (3 đoạn)')
    ax.plot([start[0] * 1000, goal[0] * 1000], [start[1] * 1000, goal[1] * 1000],
            color=HINT, lw=1.6, ls='--', label='đi thẳng (va vào vật)')
    ax.axhline(-220, color=INK, lw=2.4)
    ax.text(0, -228, 'mặt bàn', ha='center', fontsize=10, color=INK)
    ax.axhline(safe * 1000, color=PLAT, lw=1.0, ls=':')
    ax.text(88, safe * 1000 + 3, 'cao độ an toàn $z_{an}$', fontsize=10, color=PLAT, ha='right')
    for p, lab in ((start, 'điểm đầu'), (goal, 'điểm đích')):
        ax.add_patch(Rectangle((p[0] * 1000 - 10, -220), 20, 15, color=ROD, alpha=0.35))
        ax.text(p[0] * 1000, -214, lab, ha='center', fontsize=9.5, color=ROD)
    ax.set_xlabel('$x$ (mm)')
    ax.set_ylabel('$z$ (mm)')
    ax.set_xlim(-95, 95)
    ax.set_ylim(-232, -148)
    ax.grid(alpha=0.25, lw=0.6)
    ax.set_axisbelow(True)
    ax.legend(loc='upper center', frameon=False, fontsize=10)
    save(fig, 'kl_quy_dao_an_toan.png')


# ------------------------------------------------------------------ Chương 1: tổng quan

def fig_serial_vs_parallel():
    """So sánh cấu trúc nối tiếp và song song — nguồn gốc mọi khác biệt về đặc tính."""
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.5))
    ax = axes[0]
    pts = [(0, 0), (0, 0.9), (0.75, 1.25), (1.35, 0.75)]
    for i in range(len(pts) - 1):
        ax.plot([pts[i][0], pts[i + 1][0]], [pts[i][1], pts[i + 1][1]],
                color=ARM, lw=5, solid_capstyle='round')
    for p in pts[:-1]:
        ax.add_patch(Circle(p, 0.07, color=INK, zorder=5))
    ax.add_patch(Circle(pts[-1], 0.08, color=ROD, zorder=5))
    ax.add_patch(Rectangle((-0.45, -0.22), 0.9, 0.22, color=INK))
    ax.text(pts[-1][0] + 0.08, pts[-1][1], 'khâu\ncuối', color=ROD, fontsize=10, va='center')
    ax.set_title('(a) Nối tiếp — các khâu xâu chuỗi', fontsize=11)
    ax.set_xlim(-0.75, 2.1)
    ax.set_ylim(-0.35, 1.75)

    ax = axes[1]
    ax.add_patch(Rectangle((-1.0, 1.25), 2.0, 0.18, color=INK))
    plat_y, plat_hw = 0.08, 0.42
    ax.plot([-plat_hw, plat_hw], [plat_y, plat_y], color=PLAT, lw=6, solid_capstyle='round')
    for bx, px in ((-0.78, -plat_hw), (0.0, 0.0), (0.78, plat_hw)):
        elbow = (bx * 1.28, 0.80)
        ax.plot([bx, elbow[0]], [1.25, elbow[1]], color=ARM, lw=5, solid_capstyle='round')
        ax.plot([elbow[0], px], [elbow[1], plat_y], color=ROD, lw=2.6, solid_capstyle='round')
        ax.add_patch(Circle((bx, 1.25), 0.07, color=INK, zorder=5))
        ax.add_patch(Circle(elbow, 0.06, color=ARM, zorder=5))
    ax.text(plat_hw + 0.12, plat_y, 'bàn máy', color=PLAT, fontsize=10, va='center')
    ax.set_title('(b) Song song — ba chuỗi cùng đỡ bàn máy', fontsize=11)
    ax.set_xlim(-1.6, 1.9)
    ax.set_ylim(-0.30, 1.70)
    for ax in axes:
        ax.set_aspect('equal')
        ax.axis('off')
    save(fig, 'kl_noi_tiep_vs_song_song.png')


def fig_delta_structure():
    """Cấu trúc robot delta ba bậc tự do: tên gọi từng bộ phận."""
    fig, ax = plt.subplots(figsize=(6.2, 4.6))
    ax.add_patch(Rectangle((-1.25, 1.42), 2.5, 0.20, color=INK))
    ax.text(0, 1.72, 'đế cố định (3 động cơ)', ha='center', fontsize=10.5, color=INK)
    plat_y, plat_hw = 0.06, 0.38
    for bx, px, lw2 in ((-0.92, -plat_hw, 2.4), (0.0, 0.0, 2.4), (0.92, plat_hw, 2.4)):
        elbow = (bx * 1.30, 0.86)
        ax.plot([bx, elbow[0]], [1.42, elbow[1]], color=ARM, lw=5.5, solid_capstyle='round')
        for off in (-0.045, 0.045):
            ax.plot([elbow[0] + off, px + off], [elbow[1], plat_y], color=ROD, lw=lw2,
                    solid_capstyle='round')
        ax.add_patch(Circle((bx, 1.42), 0.075, color='white', ec=INK, lw=1.6, zorder=6))
        ax.add_patch(Circle((bx, 1.42), 0.032, color=INK, zorder=7))
        ax.add_patch(Circle(elbow, 0.062, color='white', ec=ARM, lw=1.6, zorder=6))
        ax.add_patch(Circle((px, plat_y), 0.055, color='white', ec=ROD, lw=1.6, zorder=6))
    ax.plot([-plat_hw, plat_hw], [plat_y, plat_y], color=PLAT, lw=7, solid_capstyle='round')
    ax.add_patch(Rectangle((-0.13, plat_y - 0.26), 0.26, 0.20, color=PLAT, alpha=0.65))
    ann = dict(fontsize=10.5, va='center')
    ax.annotate('khớp chủ động\n(động cơ)', (-0.92, 1.42), (-2.05, 1.20),
                color=INK, arrowprops=dict(arrowstyle='->', color=INK, lw=0.9), **ann)
    ax.annotate('cánh tay trên', (-1.10, 1.12), (-2.25, 0.72),
                color=ARM, arrowprops=dict(arrowstyle='->', color=ARM, lw=0.9), **ann)
    ax.annotate('cặp thanh chống\n(hình bình hành)', (-0.90, 0.48), (-2.35, 0.10),
                color=ROD, arrowprops=dict(arrowstyle='->', color=ROD, lw=0.9), **ann)
    ax.annotate('bàn máy động', (0.30, plat_y), (1.30, 0.42),
                color=PLAT, arrowprops=dict(arrowstyle='->', color=PLAT, lw=0.9), **ann)
    ax.annotate('đầu công tác', (0.0, plat_y - 0.22), (1.30, -0.22),
                color=PLAT, arrowprops=dict(arrowstyle='->', color=PLAT, lw=0.9), **ann)
    ax.set_xlim(-2.65, 2.45)
    ax.set_ylim(-0.50, 1.95)
    ax.set_aspect('equal')
    ax.axis('off')
    save(fig, 'kl_cau_truc_delta.png')


def main():
    os.makedirs(OUT, exist_ok=True)
    print('Sinh hình cho khóa luận:')
    fig_parameters()
    fig_frames()
    fig_leg_plane()
    fig_elbow_branches()
    fig_trilateration()
    fig_workspace()
    fig_quintic()
    fig_safe_path()
    fig_serial_vs_parallel()
    fig_delta_structure()
    return 0


if __name__ == '__main__':
    sys.exit(main())

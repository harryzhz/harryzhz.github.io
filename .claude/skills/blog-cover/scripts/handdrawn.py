"""
handdrawn.py — 手绘风格 SVG 图元库

风格依据见 references/style.md：Anthropic 官方插图全部是**填充路径**（无 stroke 属性），
墨线 #141413、纸片 #FAF9F5，边缘带轻微不规则抖动。本模块用同样的方式产出路径：

  - ink()   把一条中心线膨胀成带笔锋收尾的闭合填充轮廓（模拟马克笔）
  - fill()  把一个闭合多边形做周期性抖动后填充（模拟手撕/手涂的纸片）

所有坐标都在 0..100 的正方形画布内，由 render_cover.py 缩放到实际封面尺寸。
"""
from __future__ import annotations

import math
import random

INK = "#141413"
PAPER = "#FAF9F5"


# --------------------------------------------------------------------------
# 采样：把几何形状变成密集点列
# --------------------------------------------------------------------------

def _unit(dx: float, dy: float) -> tuple[float, float]:
    l = math.hypot(dx, dy) or 1e-9
    return dx / l, dy / l


def line(p0, p1, n: int = 20):
    (x0, y0), (x1, y1) = p0, p1
    return [(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n) for i in range(n + 1)]


def arc(cx: float, cy: float, r: float, a0: float, a1: float, n: int | None = None):
    """角度用度数，y 轴向下（正角度 = 屏幕上的顺时针）。"""
    if n is None:
        n = max(12, int(abs(a1 - a0) / 4))
    out = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return out


def ellipse(cx, cy, rx, ry, a0=0.0, a1=360.0, n=None):
    if n is None:
        n = max(16, int(abs(a1 - a0) / 4))
    out = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        out.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    return out


def _catmull(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return (
        0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t
               + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
               + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
        0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t
               + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
               + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3),
    )


def curve(ctrl, n_per: int = 14, closed: bool = False):
    """穿过给定控制点的平滑曲线（Catmull-Rom 采样）。"""
    P = list(ctrl)
    if len(P) < 2:
        return P
    if closed:
        P = [P[-1]] + P + [P[0], P[1]]
    else:
        P = [P[0]] + P + [P[-1]]
    out = []
    for i in range(len(P) - 3):
        for j in range(n_per):
            out.append(_catmull(P[i], P[i + 1], P[i + 2], P[i + 3], j / n_per))
    out.append(P[-2])
    return out


def polygon(pts):
    """闭合多边形 → 首尾相接的点列。"""
    pts = list(pts)
    return pts + [pts[0]]


def rect(x, y, w, h):
    return polygon([(x, y), (x + w, y), (x + w, y + h), (x, y + h)])


def densify(pts, step: float = 1.6):
    """按弧长重采样，保证抖动沿边缘均匀分布。"""
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(d / step))
        for i in range(1, n + 1):
            out.append((a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n))
    return out


# --------------------------------------------------------------------------
# 抖动：让线条不平直
# --------------------------------------------------------------------------

def _noise(rng: random.Random, periodic: bool, octaves: int = 3):
    comps = []
    for k in range(octaves):
        freq = float(k + 1) if periodic else rng.uniform(0.7, 1.8) * (k + 1)
        comps.append((rng.uniform(0.55, 1.0) / (k + 1), freq, rng.uniform(0, 2 * math.pi)))
    tot = sum(a for a, _, _ in comps) or 1.0

    def f(t: float) -> float:
        return sum(a * math.sin(2 * math.pi * fr * t + ph) for a, fr, ph in comps) / tot

    return f


def _tangents(pts, closed: bool):
    n = len(pts)
    out = []
    for i in range(n):
        if closed:
            a, b = pts[(i - 1) % n], pts[(i + 1) % n]
        else:
            a, b = pts[max(i - 1, 0)], pts[min(i + 1, n - 1)]
        out.append(_unit(b[0] - a[0], b[1] - a[1]))
    return out


def _params(pts):
    """归一化弧长参数 t ∈ [0,1]。"""
    acc = [0.0]
    for a, b in zip(pts, pts[1:]):
        acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    total = acc[-1] or 1.0
    return [v / total for v in acc]


def wobble(pts, amp: float, rng: random.Random, closed: bool = False):
    if amp <= 0:
        return list(pts)
    fn_n, fn_t = _noise(rng, closed), _noise(rng, closed)
    ts, tans = _params(pts), _tangents(pts, closed)
    out = []
    for (x, y), t, (tx, ty) in zip(pts, ts, tans):
        nx, ny = -ty, tx
        dn, dt = fn_n(t) * amp, fn_t(t) * amp * 0.35
        out.append((x + nx * dn + tx * dt, y + ny * dn + ty * dt))
    return out


# --------------------------------------------------------------------------
# 路径输出
# --------------------------------------------------------------------------

def _thin(pts, step: int):
    out = pts[::step]
    if out[-1] != pts[-1]:
        out.append(pts[-1])
    return out


def path_d(pts, closed: bool = False, smooth: bool = True, step: int = 5, move: bool = True) -> str:
    """点列 → SVG path 片段（Catmull-Rom 转三次贝塞尔，输出紧凑且平滑）。"""
    P = _thin(list(pts), step) if smooth else list(pts)
    if len(P) < 2:
        return ""
    if not smooth:
        head = f"M {P[0][0]:.2f} {P[0][1]:.2f} " if move else f"L {P[0][0]:.2f} {P[0][1]:.2f} "
        return head + " ".join(f"L {x:.2f} {y:.2f}" for x, y in P[1:])

    if closed:
        ext = [P[-1]] + P + [P[0], P[1]]
    else:
        ext = [P[0]] + P + [P[-1]]
    d = (f"M {P[0][0]:.2f} {P[0][1]:.2f}" if move else f"L {P[0][0]:.2f} {P[0][1]:.2f}")
    for i in range(len(ext) - 3):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6.0, p1[1] + (p2[1] - p0[1]) / 6.0)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6.0, p2[1] - (p3[1] - p1[1]) / 6.0)
        d += f" C {c1[0]:.2f} {c1[1]:.2f} {c2[0]:.2f} {c2[1]:.2f} {p2[0]:.2f} {p2[1]:.2f}"
    if closed:
        d += " Z"
    return d


def _width_profile(t: float, taper: float) -> float:
    """两端略收笔的宽度曲线：中段满宽，端点 (1-taper)。"""
    e = min(t, 1.0 - t) / 0.16
    return (1.0 - taper) + taper * min(1.0, e) ** 0.55


def stroke_outline_d(pts, w: float, taper: float = 0.3) -> str:
    """把中心线膨胀成闭合轮廓（两端圆头），输出可直接 fill 的 path。"""
    n = len(pts)
    tans = _tangents(pts, closed=False)
    ts = _params(pts)
    L, R = [], []
    for (x, y), t, (tx, ty) in zip(pts, ts, tans):
        nx, ny = -ty, tx
        hw = w * _width_profile(t, taper) / 2.0
        L.append((x + nx * hw, y + ny * hw))
        R.append((x - nx * hw, y - ny * hw))
    r_end = w * _width_profile(1.0, taper) / 2.0
    r_start = w * _width_profile(0.0, taper) / 2.0
    d = path_d(L, smooth=True)
    d += f" A {r_end:.2f} {r_end:.2f} 0 0 0 {R[-1][0]:.2f} {R[-1][1]:.2f}"
    d += " " + path_d(R[::-1], smooth=True, move=False)
    d += f" A {r_start:.2f} {r_start:.2f} 0 0 0 {L[0][0]:.2f} {L[0][1]:.2f} Z"
    return d


# --------------------------------------------------------------------------
# Sketch：收集绘制指令
# --------------------------------------------------------------------------

class Sketch:
    """一张封面的绘制上下文。坐标系 0..100，y 轴向下。"""

    def __init__(self, seed=0):
        self.rng = random.Random(seed)
        self.ops: list[tuple[str, str]] = []   # (color, path_d)

    # 每个图元用独立 rng，保证顺序稳定、互不串扰
    def _sub(self) -> random.Random:
        return random.Random(self.rng.getrandbits(48))

    def ink(self, pts, w: float = 3.2, taper: float = 0.3, jitter: float = 0.6, color: str = INK):
        """一笔墨线。pts 为中心线点列。"""
        p = wobble(densify(pts), jitter, self._sub())
        self.ops.append((color, stroke_outline_d(p, w, taper)))
        return self

    def fill(self, pts, color: str = PAPER, jitter: float = 0.45, corner: float = 1.0):
        """
        一块手绘填充形状（闭合）。corner 控制转角圆润程度：
        马克笔画的方块转角本就不是直角，但过度圆滑会让阶梯、屋顶这类形状糊掉。
        """
        p = wobble(densify(polygon(pts) if pts[0] != pts[-1] else pts, 0.9),
                   jitter, self._sub(), closed=True)
        self.ops.append((color, path_d(p, closed=True, step=max(1, int(round(corner * 2))))))
        return self

    def dot(self, x: float, y: float, r: float, color: str = INK):
        self.fill(ellipse(x, y, r, r), color=color, jitter=r * 0.12)
        return self

    def to_svg(self) -> str:
        return "\n".join(
            f'<path fill="{c}" d="{d}"/>' for c, d in self.ops
        )

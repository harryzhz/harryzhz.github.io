"""
motifs.py — 封面图元词汇表

两类图元：
  p_*  纸片（#FAF9F5 填充的几何块，构成画面主体）
  i_*  墨线（#141413 的手绘笔触，负责“动作/语义”）

Anthropic 封面的构图规律：**一块纸片 + 一到两笔墨线**，墨线要么穿过纸片，
要么从纸片边缘伸出，两者必须有交叠（否则像两个不相干的贴纸）。

坐标系 0..100（y 轴向下），所有图元都接受 0..100 的绝对坐标。
"""
from __future__ import annotations

import math

from handdrawn import (INK, PAPER, Sketch, arc, curve, densify, ellipse, line,
                       polygon, rect)

# ==========================================================================
# 纸片
# ==========================================================================

def p_rect(s: Sketch, x=25.0, y=30.0, w=50.0, h=40.0, color=PAPER):
    s.fill(rect(x, y, w, h), color=color)


def p_square(s: Sketch, x=32.0, y=32.0, size=36.0, color=PAPER):
    s.fill(rect(x, y, size, size), color=color)


def p_stairs(s: Sketch, x=28.0, y=26.0, w=48.0, h=44.0, steps=3, color=PAPER):
    """阶梯块：左低右高，顶边呈台阶状。"""
    sw, sh = w / steps, h / steps
    pts = [(x, y + h), (x, y + h - sh)]
    for i in range(1, steps):
        pts.append((x + i * sw, y + h - i * sh))
        pts.append((x + i * sw, y + h - (i + 1) * sh))
    pts.append((x + w, y))
    pts.append((x + w, y + h))
    s.fill(pts, color=color)


def p_bars(s: Sketch, x=26.0, y=28.0, w=48.0, h=42.0, heights=(0.45, 0.72, 1.0),
           gap=0.22, color=PAPER):
    """柱状图：底边对齐，heights 为各柱相对高度 0..1。"""
    n = len(heights)
    bw = w / (n + (n - 1) * gap)
    for i, hh in enumerate(heights):
        bx = x + i * bw * (1 + gap)
        bh = h * hh
        s.fill(rect(bx, y + h - bh, bw, bh), color=color)


def p_house(s: Sketch, x=30.0, y=26.0, w=40.0, h=42.0, roof=0.45, color=PAPER):
    """五边形小屋：上尖顶 + 下矩形。"""
    ry = y + h * roof
    s.fill([(x + w / 2, y), (x + w, ry), (x + w, y + h), (x, y + h), (x, ry)], color=color)


def p_stack(s: Sketch, x=28.0, y=28.0, w=44.0, h=34.0, n=3, dx=4.0, dy=4.0, color=PAPER):
    """层叠纸片：从后往前画，制造堆叠感。"""
    for i in reversed(range(n)):
        s.fill(rect(x + i * dx, y + i * dy, w, h), color=color)


def p_circle(s: Sketch, cx=50.0, cy=50.0, r=18.0, color=PAPER):
    s.fill(ellipse(cx, cy, r, r), color=color)


def p_tri(s: Sketch, x=28.0, y=28.0, w=44.0, h=40.0, color=PAPER):
    s.fill([(x + w / 2, y), (x + w, y + h), (x, y + h)], color=color)


# ==========================================================================
# 墨线
# ==========================================================================

def i_stroke(s: Sketch, points, w=3.4, taper=0.3, jitter=0.6, smooth=True):
    """任意折线/曲线。points 为 [[x,y], ...]。"""
    pts = [tuple(p) for p in points]
    s.ink(curve(pts, n_per=16) if smooth and len(pts) > 2 else densify(pts), w=w,
          taper=taper, jitter=jitter)


def i_line(s: Sketch, p0=(20, 50), p1=(80, 50), w=3.4, jitter=0.5):
    s.ink(line(tuple(p0), tuple(p1)), w=w, jitter=jitter)


def i_arc(s: Sketch, cx=50.0, cy=50.0, r=20.0, a0=180.0, a1=360.0, w=3.4, jitter=0.5):
    """圆弧笔触。角度制，y 向下，0°=右、90°=下、180°=左、270°=上。"""
    s.ink(arc(cx, cy, r, a0, a1), w=w, jitter=jitter)


def i_ring(s: Sketch, cx=50.0, cy=50.0, r=16.0, w=3.4, jitter=0.5):
    """手绘圆圈：起止略微重叠，像一笔画成。"""
    s.ink(arc(cx, cy, r, -8, 358), w=w, taper=0.18, jitter=jitter)


def i_outline(s: Sketch, points, w=3.2, jitter=0.5):
    """沿闭合多边形描边（首尾重叠一段，保留手绘的收笔痕迹）。"""
    pts = [tuple(p) for p in points]
    closed = pts + [pts[0], pts[1]]
    s.ink(densify(closed), w=w, taper=0.15, jitter=jitter)


def i_frame(s: Sketch, x=26.0, y=30.0, w=48.0, h=40.0, sw=3.4, over=2.0, jitter=0.5):
    """手绘方框：四笔分开画，转角处出头，像随手框出来的。"""
    o = over
    s.ink(line((x - o, y), (x + w + o, y)), w=sw, jitter=jitter)
    s.ink(line((x + w, y - o), (x + w, y + h + o)), w=sw, jitter=jitter)
    s.ink(line((x + w + o, y + h), (x - o, y + h)), w=sw, jitter=jitter)
    s.ink(line((x, y + h + o), (x, y - o)), w=sw, jitter=jitter)


def i_coil(s: Sketch, x=18.0, y=20.0, w=30.0, h=34.0, loops=4, w_stroke=3.4,
           tail=(-22.0, 18.0), jitter=0.45, flip=False, squash=0.58):
    """
    招牌“手”：几圈叠在一起的指节环 + 一道甩出去的手腕线。
    Anthropic 封面里出现频率最高的墨线元素，通常压在纸片的一角上。
    tail 是手腕线相对最后一圈末端的位移（写 null 可去掉）。
    """
    rx, ry = w * 0.5, (h / loops) * squash
    cx = x + w * 0.5
    pts = []
    for i in range(loops):
        cy = y + (i + 0.5) * (h / loops)
        off = (i - (loops - 1) / 2.0) * w * 0.07
        seg = ellipse(cx + (-off if flip else off), cy, rx, ry, a0=150, a1=-186, n=34)
        pts.extend(seg)
    if tail:
        ex, ey = pts[-1]
        tx, ty = float(tail[0]), float(tail[1])
        pts.extend(curve([(ex, ey),
                          (ex + tx * 0.30, ey + ty * 0.42),
                          (ex + tx * 0.72, ey + ty * 0.58),
                          (ex + tx, ey + ty)], n_per=16))
    s.ink(pts, w=w_stroke, taper=0.36, jitter=jitter)


def i_loopy(s: Sketch, points=((16, 66), (38, 52), (58, 34), (80, 24)), loops=3,
            r=5.0, w=3.4, jitter=0.4):
    """带打圈的曲线：沿基础路径每隔一段插入一个完整的圈（草书 “l” 的感觉）。"""
    base = curve([tuple(p) for p in points], n_per=26)
    n = len(base)
    at = [int(n * (i + 1) / (loops + 1)) for i in range(loops)]
    out = []
    for i, p in enumerate(base):
        out.append(p)
        if i in at:
            nxt = base[min(i + 1, n - 1)]
            dx, dy = nxt[0] - p[0], nxt[1] - p[1]
            l = math.hypot(dx, dy) or 1e-9
            nx, ny = -dy / l, dx / l
            c = (p[0] + nx * r, p[1] + ny * r)
            a0 = math.degrees(math.atan2(p[1] - c[1], p[0] - c[0]))
            out.extend(arc(c[0], c[1], r, a0, a0 + 360, n=30))
    s.ink(out, w=w, taper=0.3, jitter=jitter)


def i_wave(s: Sketch, points=((16, 50), (84, 50)), waves=3, amp=6.0, w=3.4, jitter=0.4):
    """沿路径的正弦波动线。"""
    base = curve([tuple(p) for p in points], n_per=30) if len(points) > 2 \
        else densify(line(tuple(points[0]), tuple(points[1]), n=120), 0.8)
    n = len(base)
    out = []
    for i, (px, py) in enumerate(base):
        t = i / (n - 1)
        nxt = base[min(i + 1, n - 1)]
        dx, dy = nxt[0] - px, nxt[1] - py
        l = math.hypot(dx, dy) or 1e-9
        nx, ny = -dy / l, dx / l
        k = amp * math.sin(2 * math.pi * waves * t) * math.sin(math.pi * t) ** 0.35
        out.append((px + nx * k, py + ny * k))
    s.ink(out, w=w, taper=0.3, jitter=jitter)


def i_spiral(s: Sketch, cx=50.0, cy=50.0, r0=2.0, r1=18.0, turns=2.5, a0=0.0,
             w=3.4, jitter=0.4):
    n = int(turns * 48)
    pts = []
    for i in range(n + 1):
        t = i / n
        a = math.radians(a0 + 360 * turns * t)
        r = r0 + (r1 - r0) * t
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    s.ink(pts, w=w, taper=0.32, jitter=jitter)


def i_burst(s: Sketch, cx=50.0, cy=50.0, r=16.0, n=7, a0=-90.0, w=3.0,
            dots=True, dot_r=2.2, jitter=0.35, spread=360.0):
    """放射状短线（Claude 星芒的手绘化），可在端点点上墨点。"""
    for i in range(n):
        base = a0 + spread * i / (n if spread >= 359 else max(n - 1, 1))
        a = math.radians(base + (((i * 37) % 11) - 5) * 1.6)   # 角度轻微失衡，避免像雪花标点
        rr = r * (0.74 + 0.26 * ((i * 7) % 5) / 4.0)
        ex, ey = cx + rr * math.cos(a), cy + rr * math.sin(a)
        s.ink(line((cx, cy), (ex, ey), n=14), w=w, taper=0.35, jitter=jitter)
        if dots:
            s.dot(ex, ey, dot_r)


def i_nodes(s: Sketch, points=((24, 34), (50, 52), (76, 30)), r=3.2, w=3.0,
            jitter=0.4, chain=True):
    """节点连线：点 + 连接线。chain=False 时只画点。"""
    pts = [tuple(p) for p in points]
    if chain:
        for a, b in zip(pts, pts[1:]):
            s.ink(line(a, b, n=16), w=w, taper=0.2, jitter=jitter)
    for p in pts:
        s.dot(p[0], p[1], r)


def i_dot(s: Sketch, x=50.0, y=50.0, r=3.0, color=INK):
    s.dot(x, y, r, color=color)


def i_arrow(s: Sketch, points=((22, 60), (78, 40)), w=3.4, head=8.0, jitter=0.45):
    pts = [tuple(p) for p in points]
    base = curve(pts, n_per=20) if len(pts) > 2 else line(pts[0], pts[1], n=40)
    s.ink(base, w=w, taper=0.28, jitter=jitter)
    tip = base[-1]
    prev = base[-6]
    a = math.atan2(tip[1] - prev[1], tip[0] - prev[0])
    for da in (math.radians(148), math.radians(-148)):
        s.ink(line(tip, (tip[0] + head * math.cos(a + da), tip[1] + head * math.sin(a + da)), n=10),
              w=w, taper=0.3, jitter=jitter * 0.6)


def i_cursor(s: Sketch, x=44.0, y=40.0, size=20.0, w=3.0, fill=PAPER):
    """鼠标箭头：白底 + 墨线描边。"""
    u = size / 20.0
    shape = [(x, y), (x, y + 15 * u), (x + 4.2 * u, y + 11.2 * u),
             (x + 7.0 * u, y + 17.4 * u), (x + 10.0 * u, y + 16.0 * u),
             (x + 7.2 * u, y + 10.0 * u), (x + 12.4 * u, y + 9.6 * u)]
    s.fill(shape, color=fill, jitter=0.3)
    i_outline(s, shape, w=w, jitter=0.35)


def i_scribble(s: Sketch, x=32.0, y=38.0, w=36.0, rows=4, gap=6.0, w_stroke=2.6,
               last=0.6, jitter=0.5):
    """代表文字的手绘横线（写在纸片上的内容）。"""
    for i in range(rows):
        ww = w * (last if i == rows - 1 else 1.0)
        s.ink(line((x, y + i * gap), (x + ww, y + i * gap), n=24),
              w=w_stroke, taper=0.25, jitter=jitter)


def i_keyhole(s: Sketch, cx=50.0, cy=48.0, r=6.0, stem=12.0, w=3.2, jitter=0.35):
    i_ring(s, cx, cy, r, w=w, jitter=jitter)
    s.ink(line((cx - r * 0.55, cy + stem), (cx - r * 0.15, cy + r * 0.6), n=12), w=w, jitter=jitter)
    s.ink(line((cx + r * 0.55, cy + stem), (cx + r * 0.15, cy + r * 0.6), n=12), w=w, jitter=jitter)
    s.ink(line((cx - r * 0.55, cy + stem), (cx + r * 0.55, cy + stem), n=10), w=w, jitter=jitter)


def i_chevrons(s: Sketch, cx=50.0, cy=50.0, size=14.0, w=3.4, jitter=0.45):
    """`</>` 三笔：左尖括号、斜杠、右尖括号。"""
    u = size
    s.ink(curve([(cx - u * 0.75, cy - u * 0.45), (cx - u * 1.15, cy),
                 (cx - u * 0.75, cy + u * 0.45)], n_per=14), w=w, jitter=jitter)
    s.ink(line((cx + u * 0.16, cy - u * 0.6), (cx - u * 0.16, cy + u * 0.6), n=14), w=w, jitter=jitter)
    s.ink(curve([(cx + u * 0.75, cy - u * 0.45), (cx + u * 1.15, cy),
                 (cx + u * 0.75, cy + u * 0.45)], n_per=14), w=w, jitter=jitter)


def i_bracket(s: Sketch, x=30.0, y=32.0, h=36.0, w_arm=7.0, w_stroke=3.4, flip=False,
              jitter=0.45):
    """方括号 [ 或 ]。"""
    d = -1.0 if flip else 1.0
    s.ink(curve([(x + d * w_arm, y), (x, y + h * 0.08), (x, y + h * 0.5),
                 (x, y + h * 0.92), (x + d * w_arm, y + h)], n_per=14),
          w=w_stroke, jitter=jitter)


REGISTRY = {name: fn for name, fn in list(globals().items())
            if callable(fn) and (name.startswith("p_") or name.startswith("i_"))}

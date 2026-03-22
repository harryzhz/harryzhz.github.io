#!/usr/bin/env python3
"""
generate-cover.py — 为博客文章生成封面图（参数化随机组合）

每张封面由 5 个独立维度组合而成：配色、背景纹理、布局、目录展示、装饰元素。
通过 seed 控制随机性，同一 seed 生成相同封面，不同 seed 产生不同组合。

用法:
  python3 generate-cover.py --post-dir <dir> --title <title> \\
      --tags tag1 tag2 ... --sections "sec1" "sec2" ... \\
      [--seed random|<int>]

  --seed 缺省时使用标题 hash（同标题 → 同封面）。
  --seed random 每次真随机。
  --seed 42    指定数字 seed（可复现）。
"""

import argparse, hashlib, math, pathlib, datetime, random
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
DOMAIN = "harryzhang.cn"
MARGIN = 48          # 全局边距
WATERMARK_H = 40     # 底部水印预留高度

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  字体
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NOTO = "/usr/share/fonts/opentype/noto/"

def _load_fonts():
    try:
        return {
            "title":   ImageFont.truetype(NOTO + "NotoSansCJK-Bold.ttc",   38, index=2),
            "title_s": ImageFont.truetype(NOTO + "NotoSansCJK-Bold.ttc",   30, index=2),
            "sec":     ImageFont.truetype(NOTO + "NotoSansCJK-Regular.ttc", 17, index=2),
            "tag":     ImageFont.truetype(NOTO + "NotoSansCJK-Regular.ttc", 14, index=2),
            "mono":    ImageFont.truetype(NOTO + "NotoSansCJK-Regular.ttc", 15, index=7),
            "mono_b":  ImageFont.truetype(NOTO + "NotoSansCJK-Bold.ttc",   16, index=7),
            "small":   ImageFont.truetype(NOTO + "NotoSansCJK-Regular.ttc", 13, index=2),
            "domain":  ImageFont.truetype(NOTO + "NotoSansCJK-Regular.ttc", 14, index=2),
        }
    except Exception:
        fb = ImageFont.load_default()
        return {k: fb for k in ("title","title_s","sec","tag","mono","mono_b","small","domain")}

FONTS = _load_fonts()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  维度 1: 配色方案
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PALETTES = [
    {"name": "cyan",    "bg": (8,15,32),   "bg_alt": (16,28,54),  "accent": (0,180,220),   "accent2": (0,140,200),   "text_hi": (220,230,245), "text_lo": (80,110,160),  "subtle": (20,35,60),  "tag_bg": (20,40,75)},
    {"name": "emerald", "bg": (8,20,16),   "bg_alt": (14,32,26),  "accent": (0,210,140),   "accent2": (0,170,110),   "text_hi": (220,240,230), "text_lo": (80,140,110),  "subtle": (18,40,32),  "tag_bg": (20,50,40)},
    {"name": "amber",   "bg": (22,16,8),   "bg_alt": (35,28,14),  "accent": (240,180,50),  "accent2": (220,150,30),  "text_hi": (245,235,215), "text_lo": (160,130,80),  "subtle": (45,35,18),  "tag_bg": (55,42,18)},
    {"name": "violet",  "bg": (16,10,28),  "bg_alt": (26,18,46),  "accent": (150,90,240),  "accent2": (120,70,200),  "text_hi": (235,225,250), "text_lo": (120,100,165), "subtle": (35,25,58),  "tag_bg": (45,30,75)},
    {"name": "coral",   "bg": (24,12,14),  "bg_alt": (38,20,22),  "accent": (240,90,80),   "accent2": (200,70,65),   "text_hi": (248,228,225), "text_lo": (165,100,95),  "subtle": (50,28,28),  "tag_bg": (60,30,32)},
    {"name": "indigo",  "bg": (10,10,30),  "bg_alt": (18,18,50),  "accent": (80,100,240),  "accent2": (60,80,200),   "text_hi": (215,220,248), "text_lo": (90,100,170),  "subtle": (25,28,65),  "tag_bg": (30,35,80)},
    {"name": "mint",    "bg": (10,18,20),  "bg_alt": (16,30,34),  "accent": (80,220,200),  "accent2": (60,190,170),  "text_hi": (220,245,240), "text_lo": (90,150,140),  "subtle": (22,42,45),  "tag_bg": (25,50,52)},
    {"name": "sunset",  "bg": (20,12,18),  "bg_alt": (34,20,30),  "accent": (255,120,60),  "accent2": (240,90,100),  "text_hi": (250,235,228), "text_lo": (170,110,100), "subtle": (50,30,35),  "tag_bg": (60,32,38)},
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  维度 2: 背景纹理
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def bg_dots(draw, pal):
    """点阵"""
    for x in range(20, W, 40):
        for y in range(20, H, 40):
            draw.ellipse([x-1, y-1, x+1, y+1], fill=pal["subtle"])

def bg_grid(draw, pal):
    """细线网格"""
    for x in range(0, W, 30):
        draw.line([(x, 0), (x, H)], fill=pal["subtle"], width=1)
    for y in range(0, H, 30):
        draw.line([(0, y), (W, y)], fill=pal["subtle"], width=1)

def bg_diagonal(draw, pal):
    """斜线"""
    for offset in range(-H, W+H, 36):
        draw.line([(offset, 0), (offset+H, H)], fill=pal["subtle"], width=1)

def bg_concentric(draw, pal):
    """同心圆"""
    cx, cy = W//2, H//2
    for r in range(40, max(W, H), 60):
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=pal["subtle"], width=1)

def bg_gradient(draw, pal):
    """纵向渐变"""
    r1, g1, b1 = pal["bg"]
    r2, g2, b2 = pal["bg_alt"]
    for y in range(H):
        t = y / H
        draw.line([(0, y), (W, y)], fill=(int(r1+(r2-r1)*t), int(g1+(g2-g1)*t), int(b1+(b2-b1)*t)))

def bg_clean(draw, pal):
    """无纹理"""
    pass

BG_FUNCS = [bg_dots, bg_grid, bg_diagonal, bg_concentric, bg_gradient, bg_clean]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  维度 3: 布局 — 基于区域的平衡布局
#
#  每个布局返回两个 zone: title_zone 和 sec_zone
#  zone = (x, y, w, h)  表示该元素可用的矩形区域
#  align = "left" | "center"  表示区域内的对齐方式
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def layout_left_right():
    """左标题右目录"""
    safe_h = H - MARGIN - WATERMARK_H
    return {
        "title_zone": (MARGIN, 80, 520, safe_h - 80),
        "title_align": "left",
        "sec_zone":   (600, 80, 550, safe_h - 80),
        "sec_align":  "left",
    }

def layout_right_left():
    """右标题左目录"""
    safe_h = H - MARGIN - WATERMARK_H
    return {
        "title_zone": (580, 80, 570, safe_h - 80),
        "title_align": "left",
        "sec_zone":   (MARGIN, 80, 500, safe_h - 80),
        "sec_align":  "left",
    }

def layout_top_bottom():
    """上标题下目录"""
    return {
        "title_zone": (MARGIN, 50, W - MARGIN*2, 170),
        "title_align": "left",
        "sec_zone":   (MARGIN, 240, W - MARGIN*2, H - 240 - WATERMARK_H),
        "sec_align":  "center",
    }

def layout_center_bottom():
    """居中标题+底部目录"""
    return {
        "title_zone": (MARGIN, 45, W - MARGIN*2, 150),
        "title_align": "center",
        "sec_zone":   (MARGIN, 220, W - MARGIN*2, H - 220 - WATERMARK_H),
        "sec_align":  "center",
    }

LAYOUTS = [layout_left_right, layout_right_left, layout_top_bottom, layout_center_bottom]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  维度 4: 目录展示
#
#  所有 section 渲染器接收 zone=(x,y,w,h) 和 align，
#  在区域内绘制内容。如果 align="center"，渲染器
#  将内容水平居中在区域内。
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _sec_content_x(zone, content_w, align):
    """根据 align 计算内容起始 x 坐标。"""
    zx, zy, zw, zh = zone
    if align == "center":
        return zx + (zw - content_w) // 2
    return zx

def sec_numbered_list(draw, sections, zone, align, pal):
    """编号列表"""
    zx, zy, zw, zh = zone
    content_w = min(zw, 500)
    sx = _sec_content_x(zone, content_w, align)
    y = zy
    for i, sec in enumerate(sections[:5]):
        draw.text((sx, y), f"{i+1:02d}", font=FONTS["mono_b"], fill=pal["accent"])
        draw.text((sx + 40, y), sec[:30] + ("…" if len(sec) > 30 else ""),
                  font=FONTS["sec"], fill=pal["text_hi"])
        if i < len(sections[:5]) - 1:
            draw.line([(sx, y+30), (sx + content_w, y+30)], fill=pal["subtle"], width=1)
        y += 40

def sec_pill_cards(draw, sections, zone, align, pal):
    """Pill 卡片"""
    zx, zy, zw, zh = zone
    card_w = min(zw, 520)
    card_h = 52
    sx = _sec_content_x(zone, card_w, align)
    y = zy
    for i, sec in enumerate(sections[:5]):
        draw.rounded_rectangle([sx, y, sx+card_w, y+card_h],
                               radius=8, fill=pal["bg_alt"], outline=pal["accent"], width=1)
        cx_n = sx + 26
        cy_n = y + card_h // 2
        draw.ellipse([cx_n-12, cy_n-12, cx_n+12, cy_n+12], fill=pal["accent"])
        draw.text((cx_n-4, cy_n-9), str(i+1), font=FONTS["tag"], fill=pal["bg"])
        draw.text((sx+50, y+(card_h-20)//2),
                  sec[:26] + ("…" if len(sec) > 26 else ""),
                  font=FONTS["sec"], fill=pal["text_hi"])
        y += card_h + 10

def sec_tree(draw, sections, zone, align, pal):
    """树形结构"""
    zx, zy, zw, zh = zone
    content_w = min(zw, 450)
    sx = _sec_content_x(zone, content_w, align)
    y = zy
    for i, sec in enumerate(sections[:5]):
        is_last = (i == len(sections[:5]) - 1)
        connector = "└─" if is_last else "├─"
        draw.text((sx, y), connector, font=FONTS["mono"], fill=pal["text_lo"])
        draw.text((sx+40, y), sec[:32] + ("…" if len(sec) > 32 else ""),
                  font=FONTS["sec"], fill=pal["text_hi"])
        if not is_last:
            draw.line([(sx+4, y+24), (sx+4, y+34)], fill=pal["text_lo"], width=1)
        y += 34

def sec_nodes(draw, sections, zone, align, pal):
    """节点连线"""
    zx, zy, zw, zh = zone
    secs = sections[:5]
    n = len(secs)
    if n == 0:
        return
    node_r = 10
    spacing = min(zw - 40, 900) // max(n, 1)
    total_w = spacing * (n - 1)
    sx = _sec_content_x(zone, total_w, align)
    base_y = zy + 20

    # 连线
    if n > 1:
        draw.line([(sx, base_y), (sx + total_w, base_y)], fill=pal["text_lo"], width=2)

    for i, sec in enumerate(secs):
        nx = sx + spacing * i
        draw.ellipse([nx-node_r, base_y-node_r, nx+node_r, base_y+node_r],
                     fill=pal["bg_alt"], outline=pal["accent"], width=2)
        draw.text((nx-4, base_y-8), str(i+1), font=FONTS["small"], fill=pal["accent"])
        label = sec[:12] + ("…" if len(sec) > 12 else "")
        lw = draw.textlength(label, font=FONTS["small"])
        draw.text((nx - lw/2, base_y + node_r + 8), label, font=FONTS["small"], fill=pal["text_hi"])

def sec_timeline(draw, sections, zone, align, pal):
    """纵向时间线"""
    zx, zy, zw, zh = zone
    secs = sections[:5]
    content_w = min(zw, 400)
    sx = _sec_content_x(zone, content_w, align)
    line_x = sx + 12
    y = zy

    draw.line([(line_x, y), (line_x, y + len(secs) * 42)], fill=pal["accent"], width=2)
    for i, sec in enumerate(secs):
        cy = y + i * 42
        draw.ellipse([line_x-5, cy+8, line_x+5, cy+18], fill=pal["accent"])
        draw.text((line_x + 20, cy+4),
                  sec[:30] + ("…" if len(sec) > 30 else ""),
                  font=FONTS["sec"], fill=pal["text_hi"])

SEC_FUNCS = [sec_numbered_list, sec_pill_cards, sec_tree, sec_nodes, sec_timeline]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  维度 5: 装饰元素
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def decor_corners(draw, pal):
    """角标十字"""
    for cx, cy in [(28,28), (W-28,28), (28,H-28), (W-28,H-28)]:
        draw.line([(cx-10, cy), (cx+10, cy)], fill=pal["accent"], width=1)
        draw.line([(cx, cy-10), (cx, cy+10)], fill=pal["accent"], width=1)

def decor_side_stripe(draw, pal):
    """侧边竖条"""
    draw.rectangle([0, 0, 5, H], fill=pal["accent"])

def decor_top_bar(draw, pal):
    """顶部色带"""
    draw.rectangle([0, 0, W, 4], fill=pal["accent"])
    draw.rectangle([0, H-4, W, H], fill=pal["accent2"])

def decor_border(draw, pal):
    """边框"""
    draw.rectangle([12, 12, W-12, H-12], outline=pal["subtle"], width=2)

def decor_none(draw, pal):
    """无装饰"""
    pass

DECOR_FUNCS = [decor_corners, decor_side_stripe, decor_top_bar, decor_border, decor_none]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  工具函数
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _wrap_title(draw, text, font, max_w):
    lines, cur = [], ""
    for ch in text:
        test = cur + ch
        if draw.textlength(test, font=font) > max_w:
            lines.append(cur)
            cur = ch
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines


def _draw_title(draw, title, zone, align, pal):
    """在 zone 内绘制标题 + 分隔线，返回 (tag_y, tag_x, tag_max_x, is_center)。"""
    zx, zy, zw, zh = zone
    is_center = (align == "center")
    font = FONTS["title"]
    lines = _wrap_title(draw, title, font, zw)

    ty = zy
    for i, ln in enumerate(lines[:3]):
        color = pal["accent"] if i == 0 else pal["text_hi"]
        if is_center:
            tw = draw.textlength(ln, font=font)
            draw.text(((W - tw) / 2, ty), ln, font=font, fill=color)
        else:
            draw.text((zx, ty), ln, font=font, fill=color)
        ty += 52

    # 分隔线
    sep_y = ty + 8
    if not is_center:
        draw.line([(zx, sep_y), (zx + min(zw, 500), sep_y)], fill=pal["accent"], width=2)

    tag_y = sep_y + 14
    return tag_y, zx, zx + zw, is_center


def _draw_tags(draw, tags, x, y, pal, max_x=1160, center=False):
    font = FONTS["tag"]
    fill_bg = pal["tag_bg"]
    fill_fg = pal["text_hi"]

    if center:
        total_w = 0
        widths = []
        for tag in tags[:4]:
            bbox = draw.textbbox((0, 0), tag, font=font)
            tw = bbox[2] - bbox[0] + 18
            widths.append(tw)
            total_w += tw + 8
        tx = (W - total_w) / 2
        for tag, tw in zip(tags[:4], widths):
            draw.rounded_rectangle([tx, y, tx+tw, y+26], radius=6, fill=fill_bg)
            draw.text((tx+9, y+4), tag, font=font, fill=fill_fg)
            tx += tw + 8
        return

    tx = x
    for tag in tags[:4]:
        bbox = draw.textbbox((0, 0), tag, font=font)
        tw = bbox[2] - bbox[0]
        pad = 9
        if tx + tw + pad*2 > max_x:
            break
        draw.rounded_rectangle([tx, y, tx+tw+pad*2, y+26], radius=6, fill=fill_bg)
        draw.text((tx+pad, y+4), tag, font=font, fill=fill_fg)
        tx += tw + pad*2 + 8


def _draw_domain(draw, pal):
    draw.text((MARGIN, H - 36), f"{DOMAIN} · {datetime.date.today().year}",
              font=FONTS["domain"], fill=pal["text_lo"])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  组合生成
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate(title, tags, sections, rng):
    pal       = rng.choice(PALETTES)
    bg_fn     = rng.choice(BG_FUNCS)
    layout_fn = rng.choice(LAYOUTS)
    sec_fn    = rng.choice(SEC_FUNCS)
    decor_fn  = rng.choice(DECOR_FUNCS)

    layout = layout_fn()
    sec_zone = layout["sec_zone"]
    sec_align = layout["sec_align"]

    # 横向节点需要足够宽度
    if sec_fn == sec_nodes and sec_zone[2] < 500:
        sec_fn = rng.choice([sec_numbered_list, sec_tree, sec_timeline])

    recipe = (f"palette={pal['name']}  bg={bg_fn.__doc__.strip()}  "
              f"layout={layout_fn.__doc__.strip()}  "
              f"sections={sec_fn.__doc__.strip()}  "
              f"decor={decor_fn.__doc__.strip()}")
    print(f"recipe: {recipe}")

    # 1. 画布 + 背景
    img  = Image.new("RGB", (W, H), pal["bg"])
    draw = ImageDraw.Draw(img)
    bg_fn(draw, pal)

    # 2. 装饰
    decor_fn(draw, pal)

    # 3. 标题 + Tags
    tag_y, tag_x, tag_max_x, is_center = _draw_title(
        draw, title, layout["title_zone"], layout["title_align"], pal)
    _draw_tags(draw, tags, tag_x, tag_y, pal, max_x=tag_max_x, center=is_center)

    # 4. 目录（在 sec_zone 内，按 sec_align 对齐）
    sec_fn(draw, sections, sec_zone, sec_align, pal)

    # 5. 域名水印
    _draw_domain(draw, pal)

    return img

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CLI 入口
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    parser = argparse.ArgumentParser(description="Generate blog cover image (parametric random)")
    parser.add_argument("--post-dir", required=True, help="Post directory path")
    parser.add_argument("--title", required=True, help="Blog title")
    parser.add_argument("--tags", nargs="*", default=[], help="Tags (max 4)")
    parser.add_argument("--sections", nargs="*", default=[], help="Key section titles (3-5)")
    parser.add_argument("--seed", default=None,
                        help="Random seed: omit=title hash, 'random'=true random, <int>=fixed seed")
    args = parser.parse_args()

    if args.seed is None:
        seed = int(hashlib.md5(args.title.encode()).hexdigest(), 16) % (2**32)
    elif args.seed.lower() == "random":
        seed = random.randint(0, 2**32 - 1)
    else:
        seed = int(args.seed)

    print(f"seed: {seed}")
    rng = random.Random(seed)

    img = generate(args.title, args.tags, args.sections, rng)

    post_dir = pathlib.Path(args.post_dir)
    img.save(post_dir / "featured-image.png", "PNG", optimize=True)
    preview = img.resize((800, 420), Image.LANCZOS)
    preview.save(post_dir / "featured-image-preview.png", "PNG", optimize=True)
    print(f"generated PNG → {post_dir}")

if __name__ == "__main__":
    main()

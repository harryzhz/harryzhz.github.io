#!/usr/bin/env python3
"""
render_cover.py — 由封面 spec（JSON）渲染 Claude 官方博客风格封面图

用法:
  python3 render_cover.py spec.json --out content/posts/2026/03/xxx/
  python3 render_cover.py spec.json --review /tmp/preview.png     # 只出大图用于肉眼检查
  python3 render_cover.py --list                                   # 打印全部图元及参数

spec.json:
{
  "bg":   "sage" | "blue" | "clay" | "iris" | "#RRGGBB",
  "seed": "post-slug",        // 决定抖动形态，同一个 seed 输出完全一致
  "icon": 360,                // 图形区边长（1200x630 画布内居中），默认 360
  "ops": [
    {"m": "p_stairs", "x": 30, "y": 28, "w": 44, "h": 42, "steps": 3},
    {"m": "i_coil",   "x": 14, "y": 16, "w": 26, "h": 30, "tail": [-10, 16]}
  ]
}
"""
from __future__ import annotations

import argparse
import inspect
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import cairosvg  # noqa: E402
from PIL import Image  # noqa: E402

from handdrawn import Sketch  # noqa: E402
from motifs import REGISTRY  # noqa: E402

# 从 Anthropic 官方博客卡片上直接取样得到的底色（见 references/style.md）
PALETTE = {
    "sage": "#BCD1CA",   # 淡青灰绿
    "blue": "#6A9BCC",   # 灰蓝
    "clay": "#D97757",   # 陶土橙（Anthropic 主色）
    "iris": "#827DBD",   # 灰紫
    "ivory": "#F0EEE6",  # 米白（低对比，慎用）
}

# 逻辑尺寸 1200x630（og:image 标准），实际按 2x 输出：
# 主题的 srcset 把同一个文件同时挂给 1x/1.5x/2x，HiDPI 屏上 1x 素材会被拉伸发虚。
W, H = 1200, 630
SCALE = 2
PREVIEW = (800, 420)
ICON_DEFAULT = 470


def build_svg(spec: dict) -> str:
    bg = spec.get("bg", "clay")
    bg = PALETTE.get(bg, bg)
    icon = float(spec.get("icon", ICON_DEFAULT))
    sk = Sketch(seed=spec.get("seed", 0))

    for i, op in enumerate(spec.get("ops", [])):
        op = dict(op)
        name = op.pop("m", None)
        fn = REGISTRY.get(name)
        if fn is None:
            raise SystemExit(f"ops[{i}]: 未知图元 {name!r}，可用图元见 --list")
        try:
            fn(sk, **op)
        except TypeError as e:
            raise SystemExit(f"ops[{i}] ({name}): 参数错误 {e}")

    k = icon / 100.0
    tx, ty = (W - icon) / 2.0, (H - icon) / 2.0
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" fill="none">\n'
        f'<rect width="{W}" height="{H}" fill="{bg}"/>\n'
        f'<g transform="translate({tx:.2f} {ty:.2f}) scale({k:.4f})">\n'
        f'{sk.to_svg()}\n</g>\n</svg>\n'
    )


def rasterize(svg: str, width: int, height: int) -> Image.Image:
    """按目标尺寸直接矢量光栅化——不要先渲大图再缩放，二次重采样会让边缘发糊。"""
    import io
    png = cairosvg.svg2png(bytestring=svg.encode("utf-8"),
                           output_width=width, output_height=height)
    return Image.open(io.BytesIO(png)).convert("RGB")


def save_webp(img: Image.Image, path: pathlib.Path) -> None:
    """平涂矢量图用无损 WebP：边缘绝对干净，体积反而比 q95 有损更小。"""
    img.save(path, "WEBP", lossless=True, quality=100, method=6)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", nargs="?", help="封面 spec JSON 路径，或 - 从 stdin 读")
    ap.add_argument("--out", help="文章目录，写入 featured-image.webp / -preview.webp")
    ap.add_argument("--review", help="额外输出一张 PNG 供肉眼检查")
    ap.add_argument("--svg", help="额外保存 SVG 源文件")
    ap.add_argument("--list", action="store_true", help="打印全部图元签名")
    args = ap.parse_args()

    if args.list:
        for name in sorted(REGISTRY):
            sig = str(inspect.signature(REGISTRY[name])).replace("s: Sketch, ", "")
            print(f"{name}{sig}")
        return

    if not args.spec:
        ap.error("需要 spec 参数（或 --list）")

    raw = sys.stdin.read() if args.spec == "-" else pathlib.Path(args.spec).read_text()
    svg = build_svg(json.loads(raw))

    if args.svg:
        pathlib.Path(args.svg).write_text(svg)
    if args.review:
        rasterize(svg, W * SCALE, H * SCALE).save(args.review)
        print(f"review → {args.review}")
    if args.out:
        d = pathlib.Path(args.out)
        d.mkdir(parents=True, exist_ok=True)
        save_webp(rasterize(svg, W * SCALE, H * SCALE), d / "featured-image.webp")
        save_webp(rasterize(svg, PREVIEW[0] * SCALE, PREVIEW[1] * SCALE),
                  d / "featured-image-preview.webp")
        for f in ("featured-image.webp", "featured-image-preview.webp"):
            print(f"{d / f}  {(d / f).stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()

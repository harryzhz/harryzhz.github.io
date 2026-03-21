#!/usr/bin/env python3
"""
compress-covers.py — 将博客封面图转换为 WebP 并压缩

用法:
  python3 scripts/compress-covers.py              # 处理 content/ 下所有封面图
  python3 scripts/compress-covers.py <post-dir>   # 仅处理指定文章目录
  python3 scripts/compress-covers.py --help

输出:
  - 同目录下生成 .webp 文件（覆盖已有同名 webp）
  - 原始 .png / .jpg 文件保留不动（需手动删除）
  - 打印每张图的压缩前后体积和节省比例
"""

import os
import sys
import pathlib
from PIL import Image

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent.parent.parent
CONTENT_DIR = REPO_ROOT / "content"

# 封面图规格：filename → (max_width, max_height, webp_quality)
COVER_SPECS = {
    "featured-image":         (1200, 630, 88),
    "featured-image-preview": (800,  420, 82),
}

SOURCE_EXTS = {".png", ".jpg", ".jpeg"}


def convert_to_webp(path: pathlib.Path) -> tuple[int, int] | None:
    """
    将单张图片转换为 WebP，返回 (before_bytes, after_bytes)。
    如果文件名不在 COVER_SPECS 中则跳过，返回 None。
    """
    stem = path.stem
    if stem not in COVER_SPECS:
        return None

    max_w, max_h, quality = COVER_SPECS[stem]
    before = path.stat().st_size

    img = Image.open(path).convert("RGB")
    img.thumbnail((max_w, max_h), Image.LANCZOS)

    out = path.with_suffix(".webp")
    img.save(out, "WEBP", quality=quality, method=6)
    after = out.stat().st_size

    return before, after


def process_dir(directory: pathlib.Path) -> list[tuple]:
    results = []
    for p in sorted(directory.rglob("*")):
        if p.suffix.lower() not in SOURCE_EXTS:
            continue
        sizes = convert_to_webp(p)
        if sizes is None:
            continue
        before, after = sizes
        saved_pct = (1 - after / before) * 100
        results.append((p, before, after, saved_pct))
    return results


def print_results(results: list[tuple]):
    if not results:
        print("没有找到需要处理的封面图。")
        return

    total_before = sum(r[1] for r in results)
    total_after  = sum(r[2] for r in results)
    total_pct    = (1 - total_after / total_before) * 100

    print(f"\n{'节省':>6}  {'原始':>7}  {'WebP':>7}  文件")
    print("-" * 70)
    for p, before, after, pct in results:
        rel = p.relative_to(REPO_ROOT)
        print(f"{pct:+.0f}%  {before//1024:>6}KB  {after//1024:>6}KB  {rel}")

    print("-" * 70)
    print(f"{total_pct:+.0f}%  {total_before//1024:>6}KB  {total_after//1024:>6}KB  合计 {len(results)} 张")
    print(f"\n提示：原始 PNG/JPG 文件未删除，确认效果后可手动清理。")
    print(f"      记得同步更新 front matter 中的 src 字段为 .webp 后缀。")


def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)

    if len(sys.argv) > 1:
        target = pathlib.Path(sys.argv[1]).resolve()
        if not target.is_dir():
            print(f"错误：{target} 不是有效目录", file=sys.stderr)
            sys.exit(1)
        print(f"处理目录：{target}")
    else:
        target = CONTENT_DIR
        print(f"处理所有封面图：{target}")

    results = process_dir(target)
    print_results(results)


if __name__ == "__main__":
    main()

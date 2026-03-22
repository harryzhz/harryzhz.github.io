---
name: blog-cover
description: 为博客文章生成对应的封面图，并将所有封面图压缩转换为 WebP 格式，当博客内容创建完成时使用。
user_invocable: true
---

# blog-cover

为博客文章生成封面图，并将封面图转换为 WebP 格式压缩。

## 使用方式

```
/blog-cover                          # 为最新文章生成封面 + 压缩转换所有封面
/blog-cover gen <post-dir>           # 仅为指定文章目录生成封面图
/blog-cover compress                 # 仅压缩转换所有封面图（不生成新图）
```

---

## 压缩转换

压缩逻辑统一在 `.claude/skills/blog-cover/scripts/compress-covers.py` 中，**直接运行脚本即可**：

```bash
# 处理 content/ 下所有封面图
python3 .claude/skills/blog-cover/scripts/compress-covers.py

# 仅处理指定文章目录
python3 .claude/skills/blog-cover/scripts/compress-covers.py content/posts/$year/$month/YYYYMMDD-xxx/
```

脚本行为：
- 将 `featured-image.png/jpg` → `featured-image.webp`（1200×630，quality=88）
- 将 `featured-image-preview.png/jpg` → `featured-image-preview.webp`（800×420，quality=82）
- 原始 PNG/JPG 保留不动，确认后手动删除
- 转换完成后记得同步更新 front matter 中的 `src` 字段为 `.webp` 后缀

---

## 封面图生成

### 步骤

1. **确定目标文章目录**
   - 不带参数：找 `content/posts/` 下修改时间最新的含 `index.md` 的目录
   - `gen <post-dir>`：使用指定目录

2. **读取 front matter**，提取：
   - `title`：用于封面左侧大字
   - `tags`：最多取前 4 个，显示为 pill 标签

3. **用以下 Python 代码生成封面**（直接在 Bash 中执行）

4. **运行压缩脚本**将生成的 PNG 转为 WebP：
   ```bash
   python3 .claude/skills/blog-cover/scripts/compress-covers.py <post-dir>
   ```

5. **更新 front matter** 将 `src` 改为 `.webp` 后缀

### 生成封面的 Python 代码

```python
from PIL import Image, ImageDraw, ImageFont
import pathlib, datetime

def generate_cover(post_dir: str, title: str, tags: list):
    POST_DIR = pathlib.Path(post_dir)
    W, H = 1200, 630

    BG      = (10,  18,  35)
    ACCENT1 = (30,  90, 200)
    ACCENT2 = (0,  210, 150)
    SUBTLE  = (50,  70, 110)
    GRID    = (20,  35,  65)
    TEXT_HI = (230, 240, 255)
    TEXT_LO = (120, 145, 185)

    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    for x in range(0, W, 40):
        for y in range(0, H, 40):
            draw.ellipse([x-1, y-1, x+1, y+1], fill=GRID)

    draw.rectangle([0, 0, 4, H], fill=ACCENT1)
    draw.rectangle([590, 80, 1160, 550], fill=(16, 28, 54))
    draw.rectangle([587, 77, 1163, 553], outline=ACCENT1, width=2)
    draw.rectangle([590, 80, 1160, 116], fill=ACCENT1)

    # 所有字体统一用 Noto Sans CJK SC（支持中英文）
    # NotoSansCJK TTC 索引：2=Sans CJK SC, 7=Sans Mono CJK SC
    NOTO = "/usr/share/fonts/opentype/noto/"
    try:
        fnt_mono_b = ImageFont.truetype(NOTO + "NotoSansCJK-Bold.ttc", 17, index=7)    # Mono CJK SC
        fnt_mono   = ImageFont.truetype(NOTO + "NotoSansCJK-Regular.ttc", 15, index=7) # Mono CJK SC
        fnt_title  = ImageFont.truetype(NOTO + "NotoSansCJK-Bold.ttc", 40, index=2)    # Sans CJK SC
        fnt_sub    = ImageFont.truetype(NOTO + "NotoSansCJK-Regular.ttc", 20, index=2)
        fnt_tag    = ImageFont.truetype(NOTO + "NotoSansCJK-Regular.ttc", 15, index=2)
        fnt_sm     = ImageFont.truetype(NOTO + "NotoSansCJK-Regular.ttc", 13, index=2)
    except:
        fnt_mono_b = fnt_mono = fnt_title = fnt_sub = fnt_tag = fnt_sm = ImageFont.load_default()

    draw.text((604, 90), "● featured-image  /  blog cover", font=fnt_mono_b, fill=TEXT_HI)

    code_lines = [
        ("# auto-generated cover", TEXT_LO),
        ('title  = "' + title[:38] + ('…' if len(title) > 38 else '') + '"', TEXT_HI),
        ("tags   = " + str(tags[:4]), ACCENT2),
        ("", TEXT_LO),
        ("generate_cover(", TEXT_HI),
        ("    palette = DARK_TECH,", TEXT_LO),
        ("    format  = WebP,", TEXT_LO),
        (")  # ✓ done", ACCENT2),
    ]
    cy = 132
    for line, color in code_lines:
        draw.text((608, cy), line, font=fnt_mono, fill=color)
        cy += 26

    LX, LY = 1120, 470
    draw.arc([LX-16, LY-20, LX+16, LY+8], start=0, end=180, fill=ACCENT2, width=4)
    draw.rectangle([LX-16, LY-2, LX+16, LY+28], fill=ACCENT2)
    draw.ellipse([LX-4, LY+8, LX+4, LY+16], fill=(16, 28, 54))

    words = title.split()
    mid = max(1, len(words) // 2)
    line1 = " ".join(words[:mid]) if len(title) > 16 else title
    line2 = " ".join(words[mid:]) if len(title) > 16 else ""

    y_title1 = 110
    draw.text((48, y_title1), line1, font=fnt_title, fill=ACCENT2)
    if line2:
        y_title2 = y_title1 + 60
        draw.text((48, y_title2), line2, font=fnt_title, fill=TEXT_HI)
        y_after = y_title2 + 60
    else:
        y_after = y_title1 + 60

    # Subtitle (from front matter categories or hardcoded)
    y_sub = y_after + 8
    draw.text((50, y_sub), "harryzhang.cn", font=fnt_sub, fill=TEXT_LO)
    sep_y = y_sub + 36
    draw.line([(48, sep_y), (500, sep_y)], fill=SUBTLE, width=1)

    tx, ty = 50, sep_y + 16
    for tag in tags[:4]:
        bbox = draw.textbbox((0, 0), tag, font=fnt_tag)
        tw = bbox[2] - bbox[0]
        pad = 10
        draw.rounded_rectangle([tx-pad, ty, tx+tw+pad, ty+28], radius=7, fill=SUBTLE)
        draw.text((tx, ty+4), tag, font=fnt_tag, fill=TEXT_HI)
        tx += tw + pad*2 + 8
        if tx > 490:
            tx, ty = 50, ty + 38

    draw.text((48, H-40), f"harryzhang.cn · {datetime.date.today().year}", font=fnt_sm, fill=TEXT_LO)

    # 保存 PNG，后续由 compress-covers.py 转为 WebP
    img.save(POST_DIR / "featured-image.png", "PNG", optimize=True)
    preview = img.resize((800, 420), Image.LANCZOS)
    preview.save(POST_DIR / "featured-image-preview.png", "PNG", optimize=True)
    print(f"generated PNG → {POST_DIR}")
```

### 调用示例

```python
generate_cover(
    post_dir="content/posts/{blog_real_dir}",
    title="{blog tilte}",
    tags=["{tag1}", "{tag2}", ...],
)
```

---

## 依赖

```bash
pip install pillow --break-system-packages
sudo apt-get install -y fonts-noto-cjk   # 中文字体支持
```

### 字体索引参考（NotoSansCJK TTC）

| index | 字体 | 用途 |
|-------|------|------|
| 2 | Noto Sans CJK SC | 标题、副标题、标签、页脚（中英文） |
| 7 | Noto Sans Mono CJK SC | 代码面板（等宽中英文） |

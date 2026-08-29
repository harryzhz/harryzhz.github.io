---
name: blog-cover
description: 生成 Claude 官方博客风格的文章封面图（纯色底 + 手绘纸片与墨线，无文字），并输出为 WebP。新建文章需要封面、或要求重做/替换封面时使用。
---

# 博客封面图生成

产出对齐 claude.com/blog 的卡片视觉：**一块低饱和纯色底 + 一个手绘的隐喻图形，没有任何文字**。
风格考据与证据见 [references/style.md](references/style.md)，先读完再动手。

封面不承载标题信息（标题由主题渲染在图下方），它只需要做一件事：
用一个能被一眼联想到的图形，说明这篇文章在讲什么。

## 工作流

1. **读文章**：拿到 `title` / `tags` / 前两节内容，用一句话概括"这篇在解决什么问题"。
2. **定隐喻**：把这句话变成一个具体的物件或动作（见下方"选图形"）。
3. **写 spec**（JSON，见下方格式），存到临时目录，不要提交进仓库。
4. **渲染检查**：
   ```bash
   python3 .claude/skills/blog-cover/scripts/render_cover.py spec.json --review /tmp/cover.png
   ```
   **必须用 Read 工具把这张 PNG 看一遍**。构图是否平衡、墨线和纸片有没有交叠、
   图形是否被识别成想要的东西——这些只能靠眼睛判断。不满意就改坐标重渲，通常要 2～3 轮。
5. **写入文章目录**：
   ```bash
   python3 .claude/skills/blog-cover/scripts/render_cover.py spec.json \
       --out content/posts/2026/03/20260308-xxx/
   ```
   生成 `featured-image.webp`（2400×1260）和 `featured-image-preview.webp`（1600×840），
   均为**无损 WebP**，单张 7～17 KB。
6. **核对 front matter**：`resources` 里两个 `src` 都指向 `.webp`。
7. 批量做多篇时，最后拼一张联系表整体看一遍配色和重复度：
   ```bash
   python3 .claude/skills/blog-cover/scripts/contact_sheet.py /tmp/sheet.png /tmp/a.png /tmp/b.png …
   ```

## spec 格式

```json
{
  "bg": "sage",
  "seed": "claude-code-best-practices",
  "icon": 470,
  "ops": [
    {"m": "p_stairs", "x": 30, "y": 26, "w": 48, "h": 48, "steps": 3},
    {"m": "i_loopy", "points": [[14,72],[30,58],[46,44],[68,22]], "loops": 3, "r": 6}
  ]
}
```

- `bg`：`sage` / `blue` / `clay` / `iris` / `ivory`，或直接写 hex。
- `seed`：**固定用文章 slug**。抖动完全由它决定，同一 slug 永远渲染出同一张图，
  重跑不会让已发布的封面变样。
- `icon`：图形区边长（在 1200×630 画布内居中），默认 470，一般不用改。
- `ops`：按绘制顺序排列，后画的盖在先画的上面。纸片先画、墨线后画。

坐标系是 **0..100 的正方形，y 轴向下**，原点在图形区左上角。有效构图区间约 `10..90`。

全部图元与参数：

```bash
python3 .claude/skills/blog-cover/scripts/render_cover.py --list
```

## 选图形

先想物件，再挑图元。几条可靠的映射：

| 文章主题 | 隐喻 | 组合 |
|---|---|---|
| 进阶 / 最佳实践 / 分层演进 | 楼梯 | `p_stairs` + `i_loopy` 沿梯上爬 |
| 数据 / 度量 / 成本 | 柱状图 | `p_bars` + `i_coil` 从最高柱伸出 |
| 隔离 / 安全 / 边界 | 盒子、锁孔、方框 | `p_square` + `i_frame` + `i_keyhole` |
| 知识 / 文档 / 沉淀 | 纸页与文字 | `p_stack` + `i_scribble` |
| 多角色协作 / 编排 | 节点连线 | `p_circle` + `p_square` + `i_nodes` |
| 工具 / 编辑器 / 终端 | 窗口 | `p_rect` + `i_frame` + `i_cursor` / `i_chevrons` |
| 上下文 / 压缩 / 取舍 | 层叠纸片、漏斗 | `p_stack` + `i_arrow` |
| 架构 / 内核 / 抽象层 | 屋、方块塔 | `p_house` + `i_burst` |

没有现成映射时，宁可用最朴素的物件（方块 + 一笔线），也不要堆三四个元素凑意思。

`i_coil`（几圈指节环 + 手腕线）是 Claude 封面里最标志性的墨线，代表"人在操作"。
用它能立刻拉近风格，但一组封面里出现两三次就够了，不要每张都放。

## 构图规则

- **元素总数 2～4**。多了就变插图，不是封面。
- **墨线必须压在纸片上或从它边缘伸出**。两者不接触是最常见的失败。
- **图形整体占 `icon` 区的 60%～80%，并且大致居中**，四周留大片纯色。
- 不要加文字、Logo、纹理、渐变、阴影。
- 一张图只用一种纸片色（`#FAF9F5`），需要第二层次时靠留白和交叠，不要再加颜色。
- 线宽 `w` 在 3.0～4.0 之间，同一张图里主次线宽差别不要超过 1.0。
- 同一批文章的底色要轮换，相邻两篇不要同色；`clay` 是主色，可以多用一点。

## 输出规格与清晰度

逻辑尺寸是 1200×630（og:image 标准），实际按 **2x 输出**，原因是主题生成的 srcset 长这样：

```html
srcset="…/featured-image.webp, …/featured-image.webp 1.5x, …/featured-image.webp 2x"
```

同一个文件被同时挂给 1x/1.5x/2x，只出 1x 素材的话，HiDPI 屏上就是被拉伸的糊图。

三条不能动的规则：

1. **无损 WebP**。平涂矢量图色数少（不到 1000 色），无损体积反而比 q95 有损更小
   （2400×1260：无损 17 KB vs q95 27 KB），而且黑线压在色块上不会出现有损压缩的振铃和边缘发毛。
2. **按目标尺寸直接光栅化**，不要先渲一张大图再 `resize` 到小尺寸——二次重采样会让边缘发糊。
   `render_cover.py` 对大图和预览图分别调一次 `rasterize()`。
3. 不要改 `SCALE`。要调画面大小请改 `icon` 或图元自身尺寸。

## 常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| 图形看着像两张贴纸 | 墨线和纸片没交叠 | 移动墨线坐标，让它压住纸片的一角 |
| 阶梯/屋顶糊成一个圆块 | 转角被过度平滑 | 给 `p_*` 传 `corner: 0.5` |
| 线条像 UI 描边、太干净 | `jitter` 太小 | 抖动保持 0.35～0.6，不要设 0 |
| 网页上看着发虚 | 输出成了 1x 或有损 | 见上方"输出规格与清晰度"，别改 `SCALE` 和无损设置 |
| 画面空 | `icon` 或图元尺寸太小 | 图元自身放大到 40～60 单位，而不是只调 `icon` |
| 一组封面看着重复 | 都用了 `i_coil` 或同一底色 | 换隐喻、换底色，保证联系表里每张都能区分 |

## 依赖

```bash
pip install cairosvg pillow --break-system-packages
```

`cairosvg` 需要系统的 `libcairo2`（Ubuntu 默认已装）。渲染不需要字体，因为封面没有文字。

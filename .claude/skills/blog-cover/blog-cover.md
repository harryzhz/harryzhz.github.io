---
name: blog-cover
description: 为博客文章生成对应的封面图，并将所有封面图压缩转换为 WebP 格式，当博客内容创建完成时使用。
user_invocable: true
---

# blog-cover

为博客文章生成封面图（参数化随机组合），并将封面图转换为 WebP 格式压缩。

每张封面由 5 个维度随机组合生成：**配色方案 × 背景纹理 × 布局 × 目录展示 × 装饰元素**，共 4800+ 种组合，每篇文章的封面都是独特的。

## 使用方式

```
/blog-cover                          # 为最新文章生成封面 + 压缩转换
/blog-cover gen <post-dir>           # 仅为指定文章目录生成封面图
/blog-cover compress                 # 仅压缩转换所有封面图（不生成新图）
```

---

## 封面图生成

### 步骤

1. **确定目标文章目录**
   - 不带参数：找 `content/posts/` 下修改时间最新的含 `index.md` 的目录
   - `gen <post-dir>`：使用指定目录

2. **读取 front matter 和正文**，提取：
   - `title`：博客标题
   - `tags`：最多取前 4 个
   - 正文中的 `##` 级标题：选取 3~5 个关键目录标题（跳过"引言""结论""延伸阅读"等通用标题）

3. **调用生成脚本**（直接在 Bash 中执行）：

   ```bash
   python3 .claude/skills/blog-cover/scripts/generate-cover.py \
       --post-dir "<post-dir>" \
       --title "<title>" \
       --tags tag1 tag2 tag3 tag4 \
       --sections "目录标题1" "目录标题2" "目录标题3" "目录标题4"
   ```

   可选：`--seed random`（真随机，每次不同）或 `--seed 42`（指定 seed 可复现）。
   不指定 `--seed` 时使用标题 hash（同标题 → 同封面）。

4. **运行压缩脚本**将生成的 PNG 转为 WebP：
   ```bash
   python3 .claude/skills/blog-cover/scripts/compress-covers.py <post-dir>
   ```

5. **清理 PNG 文件**（压缩后删除原始 PNG）

6. **更新 front matter** 确保 `src` 字段为 `.webp` 后缀

### 封面内容要素

每张封面图包含以下信息：
- **博客标题**：大号字体，accent 色首行
- **Tags**：最多 4 个 pill 标签
- **关键目录标题**：3~5 个核心章节名称
- **域名水印**：`harryzhang.cn · {year}`

### 随机组合维度

| 维度 | 选项数 | 示例 |
|------|--------|------|
| 配色方案 | 8 | 青蓝、翡翠绿、琥珀金、紫罗兰、珊瑚红、靛蓝、薄荷、日落橙 |
| 背景纹理 | 6 | 点阵、细线网格、斜线、同心圆、渐变、干净无纹理 |
| 布局 | 4 | 左标题右目录、上标题下目录、右标题左目录、居中标题底部目录 |
| 目录展示 | 5 | 编号列表、pill 卡片、树形结构、节点连线、纵向时间线 |
| 装饰元素 | 5 | 角标十字、侧边竖条、顶部色带、边框、无装饰 |

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

## 依赖

```bash
pip install pillow --break-system-packages
sudo apt-get install -y fonts-noto-cjk   # 中文字体支持
```

### 字体索引参考（NotoSansCJK TTC）

| index | 字体 | 用途 |
|-------|------|------|
| 2 | Noto Sans CJK SC | 标题、副标题、标签、页脚（中英文） |
| 7 | Noto Sans Mono CJK SC | 代码面板、终端风格文字（等宽中英文） |

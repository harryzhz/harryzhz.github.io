# Claude 官方博客封面：风格考据

结论先行：**claude.com/blog 的封面不是模型生成的图片，是品牌团队手绘后矢量化的 SVG 插画**，
落到页面上就是一块纯色卡片 + 一组填充路径。下面是可复核的证据和从中抽出的规则。

## 证据一：官方插图的 SVG 源码

站点插图托管在 Webflow CDN（`cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/…`），
抽查 4 个文件（`Hand-City-light.svg`、`Object-CodeBrowserGlobe.svg` 以及两个 `1000x1000` 插画）：

```
$ grep -c 'stroke' *.svg
Hand-City-light.svg:0
Object-CodeBrowserGlobe.svg:0
…-1000x1000.svg:0

$ grep -ohE '#[0-9A-Fa-f]{6}' *.svg | sort | uniq -c
      7 #141413      # 墨色
      6 #FAF9F5      # 纸白
      1 #D97757      # 陶土橙（点缀）
```

两个关键事实：

1. **没有任何 `stroke` 属性**。所有线条都是"把笔触外轮廓转成闭合路径再填充"，
   所以线宽会沿着笔画自然变化、端点是圆头 —— 这是手绘矢量化的典型特征，
   而不是 `stroke-width` 均匀描边的 UI 图标。
2. **调色板极窄**，一张插画基本只有墨色 + 纸白，偶尔一点品牌橙。

路径坐标也能看出手绘痕迹。一个本该是矩形的白块，实际数据是：

```
M716.889 372.855H736.111C746.901 374.076 758.026 372.928 768.906 373.325
C784.875 373.913 800.635 376.933 816.703 376.3L817.877 377.114L818.917 573.414…
```

边不是直线，是一串轻微起伏的贝塞尔曲线，四条边互不平行。

## 证据二：卡片底色（对博客列表页截图取色）

| 名称 | Hex | 用途 |
|---|---|---|
| sage | `#BCD1CA` | 淡青灰绿 |
| blue | `#6A9BCC` | 灰蓝 |
| clay | `#D97757` | 陶土橙，Anthropic 主色，出现频率最高 |
| iris | `#827DBD` | 灰紫 |
| ivory | `#F0EEE6` | 米白，用于弱化的卡片 |
| paper | `#FAF9F5` | 图形块填充 / 页面底色 |
| ink | `#141413` | 墨线 |

底色是**低饱和、中明度**的一组，不是纯色；墨线用近黑而非 `#000`，纸白用暖白而非 `#FFF`。
这两处偏移是整套视觉不刺眼的主要原因。

## 证据三：构图规律（观察 6 张连续卡片）

| 卡片 | 纸片 | 墨线 |
|---|---|---|
| Maximizing Claude Code sessions | 三级阶梯块 | 打圈的线沿阶梯向上爬 |
| Self-service data analytics | 三根柱子 | "手"从最高柱顶伸出 |
| Claude Tag reads the room | 五边形小屋 | 屋内星芒 + 屋下一只"手" |
| Securing the frontier | 圆 + 方块 | 连线 + 缠绕的曲线 + "手" |
| Claude in Chrome side panel | 窗口白块 | 手绘方框 + 鼠标箭头 |
| Compliance API coverage | 手袋白块 | 提手圆弧 + 钥匙孔 |

共同点，也是复刻时必须守住的四条：

1. **一块主纸片 + 一到两笔墨线**，元素总数控制在 2～4，没有背景纹理、没有文字。
2. **墨线必须和纸片交叠**：压在角上、穿过它、从边缘伸出。两者分离就会像两张贴纸。
3. **图形是隐喻，不是图标**：楼梯=进阶、柱子=分析、屋=场景、袋+锁孔=合规。
   不必写实，能一眼联想即可。
4. **留白很大**：图形约占卡片高度的 55%～65%，四周全是纯色。

那只反复出现的"手"（几圈指节环 + 一道手腕线）是这套视觉里辨识度最高的符号，
本仓库把它实现为 `i_coil`。

## 本仓库的实现方式

`scripts/handdrawn.py` 用同一条路子生成图形，而不是描边：

- `ink()`：把中心线按弧长膨胀成闭合轮廓，宽度沿 `_width_profile` 两端收笔，端点补半圆弧 → 得到马克笔笔触。
- `fill()`：对闭合多边形做**周期性**噪声扰动（保证首尾接得上），再转贝塞尔 → 得到手涂纸片。
- 抖动由 seed 决定，同一个 slug 永远得到同一张图，改文章不会导致封面漂移。

## 参考链接

- [Claude Blog](https://claude.com/blog) — 封面样式来源
- [Anthropic Brand & Press Kit](https://www.anthropic.com/press-kit) — 官方 Logo 与品牌资源
- [SVG Paths — MDN](https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Attribute/d) — 路径与弧线命令语义

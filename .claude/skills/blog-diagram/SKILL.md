---
name: blog-diagram
description: 为博客文章绘制 Claude 官方博客风格的内联 SVG 插图（架构图、流程图、状态图、方案对比图）。当文章需要示意图、或用户要求"画个图"时使用。
---

# 博客手绘 SVG 插图规范

目标效果参照 Claude 官方博客（claude.com/blog）的插图风格：手工编写的内联 SVG，几何形状 + 低饱和色块 + 统一网格，不用绘图库、不用生成式图片。

## 什么时候画图

- 图要呈现的是**机制**，不是名词：数据怎么流动、组件之间谁和谁通信、两个方案差在哪条边、一个请求经过哪些状态。如果一句话能说清，就写那句话，不画图。
- 对比方案时，画出**差异本身**（新增/移除的那条边、before/after 并排），而不是两个互不相连的标签盒子。
- 复杂度与论点匹配：一跳的问题画三个盒子即可；不要为了极简砍掉论证依赖的部件，也不要把整个系统盘点进去。
- **箭头必须带标签**：`writes`、`每 30s 轮询`、`invalidates`。无标签箭头等于"有点关系"。

## 嵌入方式

内联 SVG 直接写在文章 `index.md` 里（goldmark `unsafe: true` 已开启），外层固定用这个包装：

```html
<figure class="post-diagram">
  <svg viewBox="0 0 720 240" role="img" aria-label="一句话说明图的主张">
    …
  </svg>
  <figcaption>图注：读者应该注意到什么。</figcaption>
</figure>
```

- `.post-diagram` 样式在 `assets/css/_custom.scss`，提供浅色/暗色面板背景和图注排版，不要在 SVG 里重复实现。
- 尺寸只用 `viewBox` 控制（宽流程图约 `720 × H`，纵向堆叠图约 `560 × H`），不要写死 width/height。
- SVG 内禁止 `<script>`/`<style>`/`<foreignObject>`/外部图片引用。

## 配色（明暗两用）

站点有暗色模式（LoveIt `[theme=dark]`），所以：**描边和文字一律 `currentColor`，色块用"色相 + fill-opacity"**，保证两种底色下都可读。

| 角色 | 写法 |
|---|---|
| 中性盒子（默认节点） | `fill="currentColor" fill-opacity="0.07"` |
| 绿（输入/来源/正例） | `fill="#6a9b5e" fill-opacity="0.28"` |
| 蓝（处理/核心组件） | `fill="#5b8dc9" fill-opacity="0.30"` |
| 橙（输出/热点/警示） | `fill="#e8a34c" fill-opacity="0.38"` |
| 珊瑚红（强调对象，一图最多一个） | `fill="#d97757" fill-opacity="0.32"` |
| 紫（存储/上下文） | `fill="#8b7ec8" fill-opacity="0.30"` |
| 盒子描边 | `stroke="currentColor" stroke-opacity="0.25" stroke-width="1"` |
| 连线/箭头 | `stroke="currentColor" stroke-opacity="0.6" stroke-width="1.2"` |
| 虚线分组框 | `fill="none" stroke="currentColor" stroke-opacity="0.35" stroke-dasharray="4 4"` |
| 正文标签 | `fill="currentColor" font-size="13"` |
| 辅助小字/图内注释 | `fill="currentColor" opacity="0.6" font-size="11" font-style="italic"` |

颜色是语义编码，不是装饰：同一篇文章里同一色相始终代表同一类角色。一张图最多 3 个彩色色相，其余用中性色。

## 排版规则

- **对齐到网格**：坐标全部用 8 的倍数，同排盒子同一条基线、等间距。手绘图的"高级感"八成来自对齐。
- 盒子圆角 `rx="6"`；标准节点高度 36，文字垂直居中（`y = 盒子y + 23`，`text-anchor="middle"`）。
- 文字 11–13px，标签控制在一到三个词；解释性句子放 `<figcaption>`，不塞进图里。
- 箭头用 `<defs><marker>` 定义一次，`marker-end="url(#arrow)"` 复用；id 在单个 SVG 内唯一即可，但同一篇文章多张图时 id 要区分（`arrow-1`、`arrow-2`）。
- 分组（如 "Agentic loop"）用虚线圆角框 + 右上角小字标签，参照下方模板。

## 模板：横向流程图（含反馈回路）

```html
<figure class="post-diagram">
<svg viewBox="0 0 720 250" role="img" aria-label="Agentic loop：收集上下文、执行动作、验证结果的循环">
  <defs>
    <marker id="arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="currentColor" fill-opacity="0.6"/>
    </marker>
  </defs>

  <!-- 虚线分组框 -->
  <rect x="136" y="40" width="416" height="150" rx="8" fill="none"
        stroke="currentColor" stroke-opacity="0.35" stroke-dasharray="4 4"/>
  <text x="544" y="32" text-anchor="end" font-size="11" font-style="italic"
        fill="currentColor" opacity="0.6">Agentic loop</text>

  <!-- 节点：y=72，高 36，文字 y=95 -->
  <rect x="16"  y="72" width="96"  height="36" rx="6" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.25"/>
  <text x="64"  y="95" text-anchor="middle" font-size="13" fill="currentColor">Prompt</text>

  <rect x="152" y="72" width="112" height="36" rx="6" fill="#6a9b5e" fill-opacity="0.28" stroke="currentColor" stroke-opacity="0.25"/>
  <text x="208" y="95" text-anchor="middle" font-size="13" fill="currentColor">收集上下文</text>

  <rect x="296" y="72" width="112" height="36" rx="6" fill="#5b8dc9" fill-opacity="0.30" stroke="currentColor" stroke-opacity="0.25"/>
  <text x="352" y="95" text-anchor="middle" font-size="13" fill="currentColor">执行动作</text>

  <rect x="440" y="72" width="96" height="36" rx="6" fill="#e8a34c" fill-opacity="0.38" stroke="currentColor" stroke-opacity="0.25"/>
  <text x="488" y="95" text-anchor="middle" font-size="13" fill="currentColor">验证结果</text>

  <rect x="592" y="72" width="112" height="36" rx="6" fill="currentColor" fill-opacity="0.07" stroke="currentColor" stroke-opacity="0.25"/>
  <text x="648" y="95" text-anchor="middle" font-size="13" fill="currentColor">Response</text>

  <!-- 主流程箭头 -->
  <g stroke="currentColor" stroke-opacity="0.6" stroke-width="1.2" fill="none">
    <line x1="112" y1="90" x2="148" y2="90" marker-end="url(#arrow)"/>
    <line x1="264" y1="90" x2="292" y2="90" marker-end="url(#arrow)"/>
    <line x1="408" y1="90" x2="436" y2="90" marker-end="url(#arrow)"/>
    <line x1="536" y1="90" x2="588" y2="90" marker-end="url(#arrow)"/>
    <!-- 内层回路：验证失败 → 重新收集上下文 -->
    <polyline points="488,108 488,144 208,144 208,112" marker-end="url(#arrow)"/>
    <!-- 外层回路：Response → 新 Prompt -->
    <polyline points="648,108 648,216 64,216 64,112" marker-end="url(#arrow)"/>
  </g>
  <text x="348" y="138" text-anchor="middle" font-size="11" font-style="italic"
        fill="currentColor" opacity="0.6">未通过，重试</text>
</svg>
<figcaption>Agentic loop：Claude 循环执行收集上下文、执行动作、验证结果，直到验证通过。</figcaption>
</figure>
```

改造这个模板时：先在纸面（注释里）排好每个节点的 x 坐标再写形状，保证间距一致；回路折线的转折点也落在 8 的倍数上。

## 其他图型的画法要点

- **纵向分层图**（token 构成、请求生命周期）：`viewBox="0 0 560 H"`，左侧留 120px 放层级标签（`text-anchor="end"`），右侧画色块序列；同一行内的色块共用 y 和高度。
- **并排对比图**（方案 A vs 方案 B）：左右两个半区各画完整小图，中间留 40px 空隙；差异的那条边/那个节点用珊瑚红标出，其余保持中性色，让读者一眼看到"选的是什么"。
- **示意曲线图**：坐标轴用 currentColor 细线 + 箭头 marker，曲线用 `<path>` 二次贝塞尔（`Q`）近似，两条对比曲线各占一个色相；轴标签写"质量 →"这类方向性短语。图注必须注明"曲线仅为示意，非真实数据"（如果确实不是真实数据）。

## 完成前检查

- 冷读者不看正文能否从图里看出机制？
- 每条箭头都有含义（标签或上下文明确）吗？
- 切到暗色模式（`[theme=dark]`）还可读吗——有没有写死的黑色/白色文字或描边？
- 坐标是否全部对齐网格、同排等距？
- `aria-label` 和 `figcaption` 是否说的是图的主张，而不是"示意图"三个字？

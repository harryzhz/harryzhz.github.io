---
name: "docs-to-blog"
description: "Converts Feishu/Lark doc content into Hugo blog posts with proper front matter and cover images. Invoke when user asks to turn Lark docs into blog posts."
---

# Lark Docs to Blog

将飞书文档转换为 Hugo 博客文章，并为每篇文章生成封面图与预览图。

## 适用场景

- 用户提供一个或多个飞书文档链接，希望生成对应的博客文章
- 需要沿用既有文章的 front matter 结构与标签规范
- 需要为文章配置封面图与预览图

## 处理步骤

1. 读取飞书文档内容，提取标题、摘要与结构层级。
2. 将内容整理为 Markdown，替换 HTML 标签与冗余样式。
3. 为每篇文章生成 Hugo Page Bundle：
    - 目录：`content/posts/YYYY/MM/YYYYMMDD-简短主题英文slug/`
    - 文件：`index.md`
4. 生成 front matter，字段参考已有文章：
    - `title`
    - `slug`
    - `date`
    - `categories`
    - `tags`
5. 添加封面图资源：
    - `resources` 中声明 `featured-image` 与 `featured-image-preview`
    - 在同目录创建 `featured-image.svg` 与 `featured-image-preview.svg`
6. 把清洗后的 Markdown 内容写入 `index.md` 正文。
7. 如需验证，执行 `hugo` 或站点构建命令，确认无报错。

## 输出规范

- front matter 采用 YAML，字段顺序与站内既有文章一致
- 正文标题采用 `#`/`##`/`###` 层级
- 表格与列表需转换为标准 Markdown
- 封面图 SVG 需与正文主题一致，含标题关键词

## 示例 front matter

```yaml
---
title: 示例标题
slug: example-slug
date: 2026-03-01 10:00:00
categories:
- AI
tags:
  - AI Agent
  - LLM
resources:
  - name: featured-image
    src: featured-image.svg
  - name: featured-image-preview
    src: featured-image-preview.svg
---
```

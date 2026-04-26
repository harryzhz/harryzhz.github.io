# AGENTS.md

## Purpose

This repository stores technical blog content. Any agent working in this repo should optimize for high-quality technical writing: accurate, useful, well-structured, visually clear, and natural to read.

The goal is not to produce generic AI copy. The goal is to publish blogs that are:

- technically correct
- rich in practical value
- clear in structure
- illustrated with appropriate diagrams, tables, and code
- written in fluent, natural Chinese unless the user asks for another language

## Writing Standard

Every technical blog should satisfy all of the following:

1. It teaches something concrete, not just repeats definitions.
2. It contains enough detail for an engineer to apply the ideas.
3. It avoids factual sloppiness, vague claims, and inflated language.
4. It reads like an experienced engineer explaining a topic, not like a marketing article.
5. It uses diagrams, tables, examples, and code only where they improve understanding.

## Default Audience

Unless the user specifies otherwise, assume the audience is:

- software engineers
- technically literate readers
- readers who want both conceptual understanding and practical guidance

Write for readers who value clarity and substance over hype.

## Core Principles

### Accuracy First

- Do not state uncertain claims as facts.
- If a statement may have changed recently, verify it before writing.
- Prefer precise wording over dramatic wording.
- Distinguish clearly between facts, interpretation, and recommendation.
- Do not invent benchmarks, adoption data, product behavior, or architecture details.

### Substance Over Summary

- Do not stop at “what it is”.
- Explain why it matters, how it works, where it breaks, and how to use it.
- Include tradeoffs, failure modes, engineering constraints, and boundary conditions.
- Replace empty conclusions with practical takeaways.

### Natural Writing

- Write in fluent, idiomatic Chinese.
- Prefer short to medium-length sentences with clear progression.
- Avoid repetitive sentence openings and AI-sounding transitions.
- Avoid exaggerated phrases such as “颠覆式”“革命性”“彻底改变一切” unless directly justified.
- Do not pad content with generic motivation paragraphs.

### Structured Delivery

- Use layered headings.
- Keep each section focused on one question.
- Use bullets, tables, diagrams, and code to reduce cognitive load.
- Make long articles scannable without making them fragmented.

## Recommended Article Structure

For most technical topics, prefer this shape:

1. Introduction
2. Problem or background
3. Core concept or architecture
4. How it works
5. Code or practical example
6. Tradeoffs, pitfalls, or common mistakes
7. Practical guidance or decision framework
8. Conclusion

Not every article needs every section, but most strong technical posts should cover most of them.

## Introduction Requirements

The introduction should do three things quickly:

1. define the real problem
2. explain why the topic matters
3. tell the reader what they will gain from the article

Do not open with empty historical background unless it directly improves understanding.

## Content Depth Requirements

Each article should try to answer these questions where applicable:

- What problem is being solved?
- Why do existing approaches fall short?
- What is the core mechanism?
- What are the key components?
- What does a minimal working example look like?
- What are the tradeoffs?
- When should the reader use or avoid this approach?
- What are common mistakes in practice?

If the draft cannot answer most of these, it is likely too shallow.

## Diagrams and Visuals

Use diagrams when they materially improve comprehension.

Recommended use cases:

- system architecture
- execution flow
- lifecycle or state transitions
- component interaction
- decision branches

### Diagram Rules

- Prefer Mermaid when supported by the site.
- Keep diagrams simple enough to read in one pass.
- Use consistent naming with the article text.
- Do not create decorative diagrams with no explanatory value.
- Every diagram should be introduced and interpreted in surrounding text.

### Diagram Quality Bar

Before adding a diagram, check:

- Does it simplify a hard concept?
- Is each node meaningful?
- Are labels concise?
- Does the text below explain what the reader should notice?

If not, skip the diagram.

## Code Example Rules

Code examples should be realistic, minimal, and instructive.

- Prefer small examples that demonstrate one core idea.
- Include enough context to make the example understandable.
- Avoid toy code that teaches bad practice.
- Avoid overly long code dumps.
- Align the code with the article’s explanation.
- Explain why the code is written this way, not just what it does.

### Good Code Example Characteristics

- focused
- runnable or nearly runnable
- consistent naming
- no irrelevant boilerplate
- shows the engineering point clearly

## Table Usage

Use tables when comparing:

- approaches
- architectural choices
- tradeoffs
- tool capabilities
- phases or maturity levels

Do not use tables for content that reads more naturally as prose.

## Tone and Language

The writing should feel like a thoughtful engineer sharing hard-earned understanding.

Preferred tone:

- calm
- precise
- practical
- confident but not overstated

Avoid:

- sales tone
- lecture tone
- slogan-style writing
- repetitive “首先/其次/最后” overuse
- generic AI filler

## Chinese Writing Guidelines

When writing in Chinese:

- keep terminology consistent
- use English terms when they are industry standard, but explain them once if needed
- avoid awkward literal translation from English
- prefer natural phrasing over stacked noun phrases
- avoid excessive use of quotation marks for emphasis

Example:

- Better: “Agent 的关键不只是会调用工具，而是能基于反馈持续调整执行策略。”
- Worse: “Agent 是一种具备工具调用能力、推理能力、环境感知能力、闭环执行能力的新型智能范式。”

The second sentence is not wrong, but it is bloated and abstract.

## Technical Accuracy Workflow

When producing or revising a blog post:

1. Identify the claims that require verification.
2. Verify unstable or time-sensitive facts.
3. Separate evergreen principles from current ecosystem details.
4. Check terminology consistency across the whole article.
5. Re-read all architecture descriptions for technical precision.
6. Re-read all code samples for correctness and clarity.

If a fact cannot be verified confidently, write more carefully or omit it.

## Practical Value Checklist

A strong article should include some combination of:

- architecture diagrams
- execution flow diagrams
- annotated code snippets
- comparison tables
- real engineering tradeoffs
- pitfalls and anti-patterns
- implementation advice
- decision criteria

If the draft only defines concepts, it is incomplete.

## Revision Guidelines

When improving an existing blog post, do not only “polish wording”. Also check:

- Is the article too abstract?
- Are there missing examples?
- Should there be a diagram?
- Is the introduction too weak?
- Are there unsupported claims?
- Are the conclusions too generic?
- Is the structure easy to scan?
- Does the article actually help the reader do something better?

## Tool-Specific Article Rule

When the topic is a specific tool, product, framework, or coding assistant, the article must cover the tool itself, not just the surrounding generic methodology.

Tool-level practice may include, depending on the product:

- the product's core interfaces and first-class features
- the main operating modes or workflows
- configuration, permissions, extension points, or integration mechanisms
- common usage patterns, practical shortcuts, and failure cases
- how the tool fits into a real engineering or operational workflow

In short:

- topic-specific articles must include topic-specific operational guidance
- for product topics, generic methodology is not enough; the named product's own capabilities must be explained
- generic best practices can be retained, but they must not replace tool-specific substance
- if a reader finishes the article without learning how to use the named tool better, the draft is incomplete

## Blog Formatting Rules

- Every post must begin with valid front matter.
- Front matter should follow the repository’s existing blog pattern.
- At minimum, include:
  - `title`
  - `slug`
  - `date`
  - `categories`
  - `tags`
  - `resources` for cover images
- Use [archetypes/post-front-matter.md](/Users/bytedance/Workspace/gits/harryzhz/harryzhz.github.io/archetypes/post-front-matter.md) as the front matter reference template.
- Cover image resources should normally include:
  - `featured-image`
  - `featured-image-preview`
- If creating a new post directory, ensure the matching cover image files exist and the resource names match the front matter exactly.
- Use clear `##` and `###` heading hierarchy.
- Avoid overly flat heading structures. If an article has a numbered series such as “最佳实践 1~7” or “技巧 1~10”, group them under a parent section instead of making every item a top-level `##` heading.
- Prefer this pattern for long practical articles:
  - `##` for major sections
  - `###` for numbered practices / techniques
  - `####` for examples, anti-patterns, templates, or local subpoints under one practice
- Keep paragraphs reasonably short.
- Prefer bullets for lists of criteria, pitfalls, or takeaways.
- Prefer tables for structured comparison.
- Prefer fenced code blocks with language identifiers.
- Use Mermaid blocks for architecture and flow diagrams when useful.

## Cover Image Rules

- Every published post should include both `featured-image.webp` and `featured-image-preview.webp`.
- Use `1200x630` for `featured-image.webp` and `800x420` for `featured-image-preview.webp`.
- Technical blog covers should use text-free thematic visual metaphors rather than screenshots full of UI details.
- Prefer a bright, clean, modern technical editorial style with enough visual distinction for the article topic.
- Do not include readable text, company or product logos, watermarks, internal system screenshots, sensitive interfaces, or private data.
- After generating or replacing cover images, verify image dimensions, front matter resource references, and a successful Hugo build.

## Quality Bar Before Finalizing

Before considering a technical article done, verify:

- the title is specific and meaningful
- the introduction states the problem clearly
- the article contains real technical insight
- at least one of diagram, table, or code is included when appropriate
- examples and terminology are internally consistent
- the conclusion adds judgment, not just repetition
- the article reads naturally out loud

## Anti-Patterns

Do not produce blog content like this:

- “X 是什么” followed by only a definition list
- long conceptual writing with no example
- excessive buzzwords without mechanism
- diagrams inserted but never explained
- code snippets unrelated to the core argument
- broad claims without evidence
- a conclusion that merely says “未来可期”

## Preferred Outcome

A finished article should make the reader feel:

- “I understand this better now.”
- “I know how this works.”
- “I know where it is useful and where it is risky.”
- “I could apply this in practice.”

If the article does not achieve that, keep improving it.

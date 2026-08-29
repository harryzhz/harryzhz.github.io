---
title: 当写代码不再是瓶颈：解读 AI-Native SDLC Playbook
slug: ai-native-sdlc-playbook
date: 2026-08-29T10:00:00+08:00
categories:
- AI
tags:
  - AI-Native SDLC
  - Claude Code
  - 研发流程
  - 工程治理
  - Agent
resources:
  - name: featured-image
    src: featured-image.webp
  - name: featured-image-preview
    src: featured-image-preview.webp
draft: false
---

## 引言：加速了写代码，然后呢

大部分团队引入编码 Agent 之后，都会经历一段短暂的兴奋期：PR 数量涨了，功能开发周期短了，工程师的产出看起来翻了倍。然后问题开始出现——评审队列越排越长，安全团队看不完新增的代码，测试环境被抢占，发布窗口成了新的堵点。

原因不难理解。传统研发流程是围绕"写代码是最贵、最慢的环节"这个前提设计的：需求评审、设计文档、编码、测试、发布审批，每一环用文档和签字做交接，节奏由人的速度决定。当编码这一环快了五倍而其余环节没变，瓶颈只是从上游移到了下游。更糟的情况是，为了不让队列爆掉，代码在评审不充分的情况下就合进了主干。

Anthropic 在 [The AI-Native SDLC Playbook](https://claude.com/blog/the-ai-native-sdlc-playbook) 里给出的答案是：不要在旧流程上加 Agent，而要围绕 Agent 能做什么重建流程，同时把人的判断保留在真正需要判断的位置上。这篇文章解读这套 playbook 的六个阶段，重点放在三件事——**阶段之间用什么交接、每个阶段的控制手段是什么、哪些做法会让整套流程失效**。文中的配置片段可以直接对照落地，我自己的判断会明确标出来，避免和原文的主张混在一起。

## 传统 SDLC 到底哪里不适配

先把差异说清楚，否则后面的六个阶段容易被读成"换个名字的瀑布流"。

| 维度 | 传统 SDLC | AI-Native SDLC |
|---|---|---|
| 形态 | 线性阶段，逐段交付 | 闭环，运维阶段的发现回流到规划 |
| 交接物 | 文档、工单、会议纪要、签字 | 提交进版本库的 Markdown 工件 |
| 节奏 | 由人的可用时间决定 | 由工件的提交事件触发下一阶段 |
| 策略落地 | 事后评审时发现违规 | 写代码时由 Skill/Hook 前置约束 |
| 人的位置 | 每个阶段都要人推进 | 只在需要判断的闸门上 |
| 审计依据 | 工单状态流转 | Git 历史 + PR 记录 |

关键的一句话是：**每个阶段以"写一个工件进版本库"结束，下一个阶段以"读这个工件"开始**。这条约定看起来平淡，但它同时解决了三个问题——上下文不丢失（Agent 读的是原文而不是转述）、交接可自动触发（提交即事件）、过程可审计（Git 历史天然带作者和时间戳）。

## 六个阶段与它们的交接物

<figure class="post-diagram">
<svg viewBox="0 0 560 452" role="img" aria-label="AI-Native SDLC 六阶段闭环：每个阶段提交一个工件，下一阶段读取它；运维阶段发现的问题写成新的 intent.md 回到规划阶段">
  <defs>
    <marker id="arrow-1" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="currentColor" fill-opacity="0.6"/>
    </marker>
  </defs>
  <g stroke="currentColor" stroke-opacity="0.25" stroke-width="1">
    <rect x="140" y="24" width="280" height="40" rx="6" fill="#6a9b5e" fill-opacity="0.28"/>
    <rect x="140" y="92" width="280" height="40" rx="6" fill="#6a9b5e" fill-opacity="0.28"/>
    <rect x="140" y="160" width="280" height="40" rx="6" fill="#5b8dc9" fill-opacity="0.30"/>
    <rect x="140" y="228" width="280" height="40" rx="6" fill="#5b8dc9" fill-opacity="0.30"/>
    <rect x="140" y="296" width="280" height="40" rx="6" fill="#e8a34c" fill-opacity="0.38"/>
    <rect x="140" y="364" width="280" height="40" rx="6" fill="#e8a34c" fill-opacity="0.38"/>
  </g>
  <g font-size="13" fill="currentColor" text-anchor="middle">
    <text x="280" y="50">1. Plan　捕获意图</text>
    <text x="280" y="118">2. Design　需求与设计规格</text>
    <text x="280" y="186">3. Build　计划与实现</text>
    <text x="280" y="254">4. Test　反馈回路与 Eval</text>
    <text x="280" y="322">5. Deploy　评审、闸门与流水线</text>
    <text x="280" y="390">6. Maintain　监控与自动响应</text>
  </g>
  <g stroke="currentColor" stroke-opacity="0.6" stroke-width="1.2" fill="none">
    <line x1="280" y1="64" x2="280" y2="88" marker-end="url(#arrow-1)"/>
    <line x1="280" y1="132" x2="280" y2="156" marker-end="url(#arrow-1)"/>
    <line x1="280" y1="200" x2="280" y2="224" marker-end="url(#arrow-1)"/>
    <line x1="280" y1="268" x2="280" y2="292" marker-end="url(#arrow-1)"/>
    <line x1="280" y1="336" x2="280" y2="360" marker-end="url(#arrow-1)"/>
  </g>
  <g font-size="11" font-style="italic" fill="currentColor" opacity="0.6" text-anchor="start">
    <text x="292" y="80">intent.md</text>
    <text x="292" y="148">spec.md</text>
    <text x="292" y="216">plan.md</text>
    <text x="292" y="284">绿色的验证命令</text>
    <text x="292" y="352">合并后的 PR</text>
  </g>
  <g stroke="currentColor" stroke-opacity="0.6" stroke-width="1.2" fill="none">
    <path d="M140,384 H64 V44 H136" marker-end="url(#arrow-1)"/>
  </g>
  <text transform="translate(50,214) rotate(-90)" text-anchor="middle" font-size="11" font-style="italic" fill="currentColor" opacity="0.6">异常与安全发现写成新的 intent.md</text>
</svg>
<figcaption>阶段之间不靠会议和工单交接，靠一次提交。最后一条回边是整套流程和传统 SDLC 最大的差别：运维阶段不是终点，而是下一轮的输入源。</figcaption>
</figure>

### 阶段一：Plan——把想法固化成 intent.md

变化在于：需求不再由委员会汇总成一份被反复转述的文档，而是**由提出者本人口述、Claude 整理成 Markdown、提交进版本库**。整个过程是一次对话加一次审核，从想法到成文以小时计。

```markdown
# Intent: 理赔进度自助查询
Author: J. Ortiz（理赔运营）  Status: draft

## 问题
客户打电话到客服中心问理赔到哪一步了。
坐席大约三分之一的通话时长花在纯查进度的问题上。

## 期望结果
客户在门户上能看到理赔状态、下一步动作和预计时间。
```

这里唯一的控制点是产品负责人的批准，而批准这个动作本身就是一次 merge 或一次 close——不需要额外的审批系统。

### 阶段二：Design——需求与设计合并成一次会话

传统流程把"需求"和"设计"拆给两个团队做，为的是责任划分，代价是慢且有信息损耗。Playbook 的做法是合成一次带策略约束的会话：产品负责人加载组织的 Skills，附上已批准的 `intent.md`，让 Claude 产出 `spec.md`。

关键不在于"快"，而在于**策略的介入时机变了**。品牌规范、安全要求、UX 标准被编码成 Skill，在写规格的时候就被读取和应用，而不是几周后在评审会上被发现违反。Claude 拿不准的地方会标出来，由产品负责人找策略负责人拍板。

### 阶段三：Build——真正需要重新设计的一段

这是六个阶段里内容最多的一段，也是大多数团队唯一实际动过的一段。它包含五个相对独立的做法。

#### 先出 plan.md，再动代码

用 Plan Mode 起手：Claude 读 `intent.md` 和 `spec.md`，反过来采访工程师，双方迭代出一份计划。工程师要主动追问——哪一步风险最高？什么情况会崩？确认后把计划提交为 `plan.md`。

```markdown
# Plan: 理赔进度自助查询（源自 intent.md 2026-06-02）

## 涉及文件
portal/src/claims/StatusPanel.tsx（新增）
claims-api/routes/status.py
claims-api/tests/test_status.py

## 执行顺序
1. 在现有鉴权后面加状态查询接口
2. 面板对接该接口
3. 接入门户导航

## 风险
claims-core API 限流 50 rps，面板必须做缓存
```

Plan Mode 的价值不只是"写下来"，而是**它由机制强制执行**：在工程师接受计划之前，Claude 不能编辑任何文件。这把"先想清楚再动手"从纪律变成了约束。`plan.md` 后续还会在 PR 评审里被用作合规依据——改动是否符合当初的计划，是可以逐条对照的。

#### CLAUDE.md：把新人需要知道的东西写下来

`CLAUDE.md` 承载的是组件级知识：构建命令、约定、架构模式、这个团队最常犯的错。它在会话启动时被完整读入，所以**控制在一页以内**很重要——写成十页的结果是重要的约定被淹没。

```markdown
# 支付服务

## 命令
- 构建：make build
- 测试：make test（单测）/ make itest（集成测试，需要 docker）
- 检查：make lint（CI 会跑，推之前先修干净）

## 约定
- Java 21，Spring Boot 3，不再引入新的 Lombok
- 金额一律用 BigDecimal，不用 double
```

维护规则只有一条，但很关键：**同一个错误 Claude 犯第二次，就把纠正写进 CLAUDE.md**。这条规则让文件按实际踩坑频率增长，而不是按想象中的重要性增长。

#### Skill 与 Hook：建议性约束和确定性约束

这是整套治理体系里最容易被混淆的一对概念。

- **Skill** 处理的是"必须一致应用"的组织级知识，通过 frontmatter 里的触发条件按需加载（比如"每当创建或修改对外接口时"）。它是一种控制，但**是建议性的**——它让 Claude 大概率遵守策略，却没有任何机制强制某次会话必须遵守。
- **Hook** 是确定性的。它在工具调用前后运行，能直接放行、阻断，或要求人工批准。凡是**不允许有例外**的策略，都应该在 Skill 之外再配一个 Hook 兜底。

<figure class="post-diagram">
<svg viewBox="0 0 720 240" role="img" aria-label="构建期用 Skill 建议约束、Hook 确定性拦截，人工审批只出现在交付期的闸门上">
  <defs>
    <marker id="arrow-2" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="currentColor" fill-opacity="0.6"/>
    </marker>
  </defs>
  <g fill="none" stroke="currentColor" stroke-opacity="0.35" stroke-dasharray="4 4">
    <rect x="16" y="40" width="376" height="176" rx="8"/>
    <rect x="456" y="40" width="248" height="176" rx="8"/>
  </g>
  <g font-size="11" font-style="italic" fill="currentColor" opacity="0.6">
    <text x="16" y="32">构建期</text>
    <text x="456" y="32">交付闸门</text>
  </g>
  <g stroke="currentColor" stroke-opacity="0.25" stroke-width="1">
    <rect x="32" y="72" width="96" height="36" rx="6" fill="currentColor" fill-opacity="0.07"/>
    <rect x="156" y="72" width="96" height="36" rx="6" fill="currentColor" fill-opacity="0.07"/>
    <rect x="280" y="72" width="96" height="36" rx="6" fill="#5b8dc9" fill-opacity="0.30"/>
    <rect x="472" y="72" width="216" height="36" rx="6" fill="#e8a34c" fill-opacity="0.38"/>
    <rect x="472" y="148" width="216" height="36" rx="6" fill="#d97757" fill-opacity="0.32"/>
  </g>
  <g font-size="13" fill="currentColor" text-anchor="middle">
    <text x="80" y="95">Agent 编辑请求</text>
    <text x="204" y="95">Skill 提示策略</text>
    <text x="328" y="95">Hook 拦截</text>
    <text x="580" y="95">PR：plan.md + 评审发现</text>
    <text x="580" y="171">Code owner 审批 / 发布授权</text>
  </g>
  <g stroke="currentColor" stroke-opacity="0.6" stroke-width="1.2" fill="none">
    <line x1="128" y1="90" x2="152" y2="90" marker-end="url(#arrow-2)"/>
    <line x1="252" y1="90" x2="276" y2="90" marker-end="url(#arrow-2)"/>
    <line x1="392" y1="90" x2="468" y2="90" marker-end="url(#arrow-2)"/>
    <line x1="580" y1="108" x2="580" y2="144" marker-end="url(#arrow-2)"/>
  </g>
  <g font-size="11" fill="currentColor" opacity="0.6" text-anchor="middle">
    <text x="204" y="128">建议性</text>
    <text x="328" y="128">确定性</text>
    <text x="430" y="82">提交 PR</text>
  </g>
  <g font-size="11" font-style="italic" fill="currentColor" opacity="0.6" text-anchor="middle">
    <text x="204" y="156">退出码 0 放行 · 2 阻断并回传原因 · 其他转人工</text>
    <text x="204" y="182">构建期不设人工审批，会话可并行推进</text>
    <text x="580" y="208">职责分离：写代码的会话不能批准自己</text>
  </g>
</svg>
<figcaption>注意左右两个虚线框的分工：构建期只允许"放行或阻断"这类瞬时判定，任何需要人点头的动作都被推到右边的闸门上。</figcaption>
</figure>

这张图里最反直觉的一条是：**要求人工批准的 Hook 不属于构建期，属于阶段五的闸门**。原因是并行会话——一个会在构建中途弹出审批提示的 Hook，等于把人重新塞回所有并行会话的关键路径上，并行度当场归零。

#### 并行会话与 Subagent

一个工程师同时编排多个工作流的前提是隔离：给每个并行会话分配独立的 git worktree，避免文件互相踩踏。Subagent 则是带独立上下文窗口的专用助手，适合那些反复出现、又会污染主会话上下文的工作——代码精简、验证、探索性搜索。

```markdown
---
name: verifier
description: 在会话报告完成之前，实际运行应用并验证改动生效
tools: Bash, Read
---
用 make run 启动应用。执行改动涉及的行为，以及最相邻的两条流程。
报告你运行了什么、看到了什么、哪些行为与 plan.md 不符。
不要修任何东西，只报告。
```

`tools` 只给 `Bash, Read`、并明确写"不要修任何东西"，是刻意的：验证者一旦有修改权限，它就有动机把不符预期的地方改成符合预期。

并行度的上限不是算力，而是评审能力。Playbook 给的判据很实用：**只在评审还跟得上的前提下增加会话**，2～3 个是合理的起点。

### 阶段四：Test——让会话先自己验一遍

传统流程里"代码能跑"这个信号来得太晚：CI 是几分钟后，测试同学是几天后，生产是几周后。这个阶段要做的事是把信号提前到人看到之前。

#### 给 Claude 一个可闭环的反馈回路

条件其实很朴素：**一条命令、失败时非零退出、在 CLAUDE.md 里写明健康输出长什么样**。有了这三样，会话就能自己迭代到通过为止。

```markdown
## 如何验证你的工作

- 构建：make build（必须以 "Build succeeded" 结束）
- 测试：make test（全绿；不允许跳过或删除失败的测试）
- 检查：make lint（零警告）

报告任务完成前把三条都跑一遍，并把输出贴出来。
测试失败时改代码，不要改测试。
```

最后一句必须有对应的强制手段。**在修复类任务中，用 Hook 阻断对测试文件的编辑**——正在修某段代码的 Agent，不能有权削弱针对这段代码的检查。这是我认为整篇 playbook 里最值得立刻抄走的一条：光靠提示词写"不要改测试"，在长会话里是拦不住的。

#### 把 Agent 配置本身纳入回归测试

`CLAUDE.md`、Skills、Hooks 都是会被改动的配置，改坏了不会报错，只会让 Agent 悄悄变笨。做法是攒 20～50 个真实任务，每个写成一条 eval（提示词 + 验收检查），在配置变更和定时任务上跑。

```yaml
name: Agent evals
on:
  pull_request:
    paths: ['CLAUDE.md', '.claude/**']
  schedule:
    - cron: '0 2 * * *'
```

配套规则是：**每次生产事故都补一条 eval，由出事的团队自己写，长期留在套件里当回归测试**。这条规则让 eval 套件的增长和事故历史绑定，而不是靠人凭空想场景。

### 阶段五：Deploy——评审是双向的

这个阶段的核心变化是 Claude 同时是评审者和被评审者：它按组织策略评审进来的 PR，也处理自己 PR 上收到的评审意见——人在评论里 @claude，它修完直接推上去。

评审策略本身也是一份提交进版本库的文档，由技术负责人维护：

```markdown
# 评审说明

## 评审轮次
分三轮，每条发现标注属于哪一轮：
- Bug：逻辑错误、边界情况、隐蔽的回归
- 安全：注入风险、鉴权缺口、日志里的 PII
- 合规：改动是否符合 spec.md、plan.md 和设计原则

## 什么算 Important
只有会破坏行为、泄露数据或违反策略的才标 Important，风格和命名都是 nit。

## 控制噪声
每次评审最多报 5 条 nit，其余只给个数量。

## 不要报
src/gen/ 下的生成文件，以及 CI 已经强制的内容
```

"最多 5 条 nit"这种规定看着琐碎，实际决定了评审结果有没有人看——一次报 60 条的自动评审，和没有评审的效果是一样的。

另外两条约束值得单独强调：

- **职责分离**：写代码的 Agent 没有任何途径批准自己的代码，这一点靠分支保护强制，而不是靠约定。
- **意见回流**：同一类问题在评审里被指出第二次，就写进 `CLAUDE.md`。这和阶段三的维护规则是同一条，只是触发点从会话内移到了评审里。

#### 闸门用 Hook 实现

需要审批的动作用 Hook 卡住，退出码决定行为：

```bash
#!/bin/bash
# .claude/hooks/production-gate.sh
cmd=$(jq -r '.tool_input.command' < /dev/stdin)
if [[ "$cmd" == *"deploy"* && "$cmd" == *"production"* ]]; then
  if [ -z "$RELEASE_APPROVAL" ]; then
    echo "生产发布需要发布授权。" >&2
    exit 2
  fi
fi
exit 0
```

`exit 2` 会阻断这次调用，并把 stderr 的内容回传给 Claude，所以这段文字要写成"给 Agent 看的说明"，而不是给人看的日志。

#### 让 Agent 进流水线，分四步走

Playbook 建议的推进顺序是渐进式的，我认为这个顺序比它的内容更重要：

1. **只读的判断类步骤**：诊断失败的构建、起草变更日志
2. **已有闸门后面的写操作**：修 lint、更新文档，且只允许开 PR
3. **沙箱内执行**：容器隔离、网络策略、短时效的最小权限令牌
4. **按环境分级**：开发环境自由部署，预发布做验证，生产由 Agent 准备、发布负责人授权

配套的两条硬要求：**不给 Agent 常驻的生产凭据**；**回滚必须是流水线里最熟练的那条路径**——一条命令能跑完，并且在预发布环境定期演练。把部署能力通过 MCP 暴露成 deploy / status / rollback 三个按环境限定的工具，比让 Agent 自由拼 shell 命令要可控得多。

非交互式运行还有一个容易被忽略的好处：Agent 以自己的身份行动，流水线日志天然能区分"Agent 做了什么"和"触发它的工程师做了什么"。

### 阶段六：Maintain——闭环合上的地方

这一阶段的定义是：**触发链路里没有人**。监控发现异常，Claude 被自动唤起，产出的东西以 `intent.md` 的形式重新进入阶段一。

<figure class="post-diagram">
<svg viewBox="0 0 720 236" role="img" aria-label="控制带三档响应：1σ 仅记录，2σ 只读诊断，3σ 允许开 PR 或触发预批准 runbook，结果写成 intent.md 回到规划阶段">
  <defs>
    <marker id="arrow-3" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="currentColor" fill-opacity="0.6"/>
    </marker>
  </defs>
  <g stroke="currentColor" stroke-opacity="0.25" stroke-width="1">
    <rect x="16" y="96" width="128" height="36" rx="6" fill="currentColor" fill-opacity="0.07"/>
    <rect x="232" y="32" width="280" height="36" rx="6" fill="currentColor" fill-opacity="0.07"/>
    <rect x="232" y="96" width="280" height="36" rx="6" fill="#5b8dc9" fill-opacity="0.30"/>
    <rect x="232" y="160" width="280" height="36" rx="6" fill="#e8a34c" fill-opacity="0.38"/>
    <rect x="568" y="160" width="136" height="36" rx="6" fill="#6a9b5e" fill-opacity="0.28"/>
  </g>
  <g font-size="13" fill="currentColor" text-anchor="middle">
    <text x="80" y="119">确定性检测脚本</text>
    <text x="372" y="55">仅记录，进入基线</text>
    <text x="372" y="119">只读诊断，产出根因说明</text>
    <text x="372" y="183">开 PR 或触发预批准 runbook</text>
    <text x="636" y="183">intent.md</text>
  </g>
  <text x="80" y="152" text-anchor="middle" font-size="11" font-style="italic" fill="currentColor" opacity="0.6">纯阈值，不调用模型</text>
  <g stroke="currentColor" stroke-opacity="0.6" stroke-width="1.2" fill="none">
    <path d="M144,114 H176 V50 H228" marker-end="url(#arrow-3)"/>
    <path d="M144,114 H228" marker-end="url(#arrow-3)"/>
    <path d="M144,114 H176 V178 H228" marker-end="url(#arrow-3)"/>
    <line x1="512" y1="178" x2="564" y2="178" marker-end="url(#arrow-3)"/>
  </g>
  <g font-size="13" fill="currentColor" opacity="0.75" text-anchor="middle">
    <text x="202" y="46">1σ</text>
    <text x="202" y="110">2σ</text>
    <text x="202" y="174">3σ</text>
  </g>
  <g font-size="11" font-style="italic" fill="currentColor" opacity="0.6" text-anchor="middle">
    <text x="538" y="166">写成</text>
    <text x="636" y="216">回到阶段一：Plan</text>
  </g>
</svg>
<figcaption>检测和响应必须分开：判断"是否越界"的是纯阈值脚本，模型只在越界之后被唤起，且能做什么由档位决定。</figcaption>
</figure>

具体机制是控制带（control band）：一个确定性脚本把指标和滚动基线对比（均值/标准差、Western Electric 规则），全程不涉及模型。越界之后按档位授权：

```yaml
metric: ci_test_failure_rate
baseline: rolling_30d
rules: western_electric
tiers:
  1sigma: { action: log }
  2sigma: { action: diagnose,
            tools: "Read,Grep,Bash(gh run view *)" }
  3sigma: { action: propose,
            routes: [pull_request, runbook:rollback-deploy] }
```

这个设计的巧妙之处在于**把"要不要惊动模型"和"模型能做什么"拆成了两个独立决策**。检测保持确定性，成本可控、行为可预测；授权范围由档位声明，不依赖模型自觉。

服务负责人负责分诊队列：立刻修、排期、或者驳回。驳回不是终点——**驳回要写原因，并用来调整控制带的阈值**，这是降噪的唯一可持续方式。修复上线后，为这类事故补一条 eval 进套件（回到阶段四）。

同一阶段还有两条自动化入口：定时的安全扫描（小问题直接开 PR 走评审闸门，架构级问题写成 `intent.md`），以及在 Slack/Teams 频道里以独立身份参与事故响应——请求、诊断、人工授权、修复都留在事发的频道里，频道本身就是审计记录。

## 三种控制手段该怎么选

把前面散落的控制点集中对比一下：

| 手段 | 强制力 | 失败模式 | 适合承载 |
|---|---|---|---|
| Skill | 建议性 | 会话可能不加载或不遵守 | 允许有例外的规范、上下文相关的写法指引 |
| Hook | 确定性 | 脚本本身写错会误伤 | 不允许例外的红线：保护路径、凭据、测试文件 |
| 托管设置（MDM 下发） | 确定性且工程师不可覆盖 | 过严会阻碍正常开发 | 受监管场景的权限、沙箱、网络出口白名单 |
| 分支保护 / 发布授权 | 人工判断 | 成为新瓶颈 | 需要担责的决定：合并、生产发布 |

受监管行业可以把最外层直接锁死在托管设置里：

```json
{
  "permissions": {
    "deny": ["Read(.env*)", "WebFetch"],
    "allow": ["Bash(git *)", "Bash(make build)"]
  },
  "allowManagedPermissionRulesOnly": true,
  "sandbox": {
    "enabled": true,
    "failIfUnavailable": true,
    "network": { "allowedDomains": ["git.internal.example.com"] }
  },
  "allowManagedHooksOnly": true
}
```

`allowManagedPermissionRulesOnly` 和 `allowManagedHooksOnly` 这两项是关键：它们让本地配置无法追加规则，否则工程师在自己机器上加一条 allow 就能绕过整套策略。`failIfUnavailable` 保证沙箱不可用时直接失败，而不是降级成裸跑。

## 怎么度量：领先指标和滞后指标

Playbook 对每个阶段都给了成对的指标，这里合并成一张表。**领先指标（预测）用来调流程，滞后指标（结果）用来验证流程调对了没有**——只看后者，等发现问题时已经过了一个季度。

| 阶段 | 领先指标 | 滞后指标 |
|---|---|---|
| Plan | 从对话到 `intent.md` 提交的时间（应以小时计） | 意图存活率；开工后的返工量 |
| Design | `intent.md` 到 `spec.md` 的间隔 | 开工后的规格变更次数 |
| Build / Test | 首次 CI 通过率 | 单 PR 评审耗时；变更失败率 |
| Deploy | 首次评审响应时间（应降到分钟级）；评论解决率 | 合并前拦截的缺陷数 vs 逃逸到生产的数量 |
| Maintain | 定时触发的配置占比 | 重复事故数（应随 eval 积累而下降） |

整体仍然可以用 DORA 四项兜底：部署频率、变更前置时间、变更失败率、恢复时间。

## 常见的失效方式

以下几条是我结合 playbook 的约束和实际观察整理的，可以当成落地前的检查清单。

- **在构建期插人工审批。** 最典型的错误。一个会弹出审批的 Hook 会让所有并行会话停在同一个人身上，并行度归零。审批属于阶段五。
- **允许 Agent 修改测试。** 没有 Hook 兜底时，"测试失败就改代码"只是一句提示词。修复任务里必须阻断对测试文件的写入。
- **让 Agent 自审自批。** 分支保护缺失的话，一个能开 PR 又能合并的 Agent 会把整条评审链变成摆设。
- **只搬工件，不搬闸门。** 团队照着写了 `intent.md` 和 `spec.md`，但没人真正批准或驳回，工件就退化成额外的文档负担。**判断标准很简单：有没有出现过被驳回的 intent？** 一条都没有，说明这个闸门没在工作。
- **评审意见不回流。** 同类问题被指出第三次还没进 `CLAUDE.md`，说明反馈回路断了，Agent 会一直犯同一个错。
- **控制带不调优。** 阈值定完就不动，几周后告警噪声会淹没真实信号，最终整个队列被忽略。驳回原因必须用来回调阈值。
- **一次性铺开六个阶段。** 这是最贵的失败方式。工件链的价值来自"每一环都真的被读被写"，同时上六段的结果通常是六段都做了一半。

## 从哪里开始

Playbook 给的依赖关系是线性的：Plan 喂给 Design，Design 喂给 Build，依此类推，而 Plan 阶段没有任何前置依赖，所以从它开始随时可以。

不过如果团队还没有做过任何流程改造，**我的建议是先从阶段三和阶段四的技术底座开始**，理由是它们不需要任何跨团队协调，收益在一周内就能看到：

1. 写一份一页的 `CLAUDE.md`，包含构建/测试/检查三条命令和健康输出。
2. 保证 `make test` 这类单条命令存在且失败时非零退出，让会话能自我闭环。
3. 加第一个 Hook：在修复任务里阻断对测试文件的编辑。
4. 打开 Plan Mode，把 `plan.md` 变成开工前的默认动作。

这四步做完之后再往上游走（`intent.md` / `spec.md`）和往下游走（评审策略、闸门、控制带），会顺得多——因为那时候已经有一条真实的工件链可以往上接了。

关于遗留系统，playbook 给了三种共存方式，可以按组织现状选：仓库为准（Jira 只存提交引用）、遗留系统为准（Markdown 是通过 MCP 同步的工作副本）、或者最低限度的双向链接。**关键不是选哪个，而是明确声明谁是唯一事实来源**，否则两边都会慢慢腐化。

## 结语

这套 playbook 真正的主张不是"用 AI 加速每个环节"，而是**把研发流程的交接协议从人可读的文档，换成机器可触发的提交事件；把策略的执行时机从事后评审，前移到写代码的当下**。人没有被移出流程，而是被集中到了少数几个需要担责的闸门上——批准意图、批准合并、授权发布。

有一个判断标准可以用来检查改造是否走在正确的方向上：**当代码产出翻倍时，你的评审队列是变长了，还是评审的粒度变粗了？** 如果两者都没有，说明反馈回路和闸门确实在起作用；如果队列变长，说明只加速了上游；如果粒度变粗，那是最危险的情况——流程表面上还在，实际已经失效了。

## 延伸阅读

- [The AI-Native SDLC Playbook](https://claude.com/blog/the-ai-native-sdlc-playbook) — Anthropic 官方 playbook，本文的主要信息来源
- [Hooks reference](https://code.claude.com/docs/en/hooks) — Hook 事件、退出码语义与配置格式
- [Skills](https://code.claude.com/docs/en/skills) — Skill 的触发条件与目录结构
- [Subagents](https://code.claude.com/docs/en/sub-agents) — Subagent 的独立上下文与工具限定
- [Settings](https://code.claude.com/docs/en/settings) — 托管设置、权限规则与 `allowManaged*` 系列开关
- [Sandboxing](https://code.claude.com/docs/en/sandboxing) — 文件系统与网络隔离的实现方式
- [Claude Code GitHub Actions](https://code.claude.com/docs/en/github-actions) — 在自有 CI 中运行评审与非交互式任务

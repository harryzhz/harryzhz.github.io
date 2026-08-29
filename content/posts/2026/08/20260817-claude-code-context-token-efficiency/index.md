---
title: 把 Token 花在刀刃上：Claude Code 的 Context 管理与效率实践
slug: claude-code-context-token-efficiency
date: 2026-08-17T10:00:00+08:00
categories:
- AI
tags:
  - Claude Code
  - Context Engineering
  - Prompt Caching
  - Token 优化
  - 工程实践
resources:
  - name: featured-image
    src: featured-image.webp
  - name: featured-image-preview
    src: featured-image-preview.webp
draft: false
---

## 引言：同一个任务，为什么账单差好几倍

两个工程师用 Claude Code 修同一个 bug：一个新开会话、@-mention 相关文件、改完就 `/clear`；另一个在一个开了一整天的会话里连续处理十几个不相关的任务，中途还切换过两次模型。最终改动可能一模一样，但后者消耗的 token 往往是前者的数倍。

这不是模型能力的问题，而是**会话管理方式**的问题。Claude Code 按 API token 计费，Anthropic 官方文档给出过一组参考数字：企业场景下人均日成本约 13 美元，月成本在 150～250 美元之间，90% 的用户日成本低于 30 美元——但这批数字背后的方差非常大，同样的产出，浪费的部分几乎全部来自 context 管理不当。

这篇文章不讲"如何写更好的 prompt"，而是讲一件更底层、更容易被忽视的事：**Claude Code 的 context 是怎么被填满的，token 是怎么被计价的，以及有哪些具体命令和习惯可以把浪费的部分省下来**。内容主要基于 Anthropic 官方博客 [Maximizing the value of your Claude Code sessions](https://claude.com/blog/maximizing-the-value-of-your-claude-code-sessions) 和官方文档 [Manage costs effectively](https://code.claude.com/docs/en/costs)，并结合实际可执行的命令做了展开。

## 先搞懂计价模型：三个决定成本的变量

在谈技巧之前，有必要先理解 token 是怎么算钱的，否则很多"技巧"会显得像玄学。决定单次请求成本的是三个相互独立的变量。

### 1. 模型选择

不同模型的单 token 价格不同，Opus 比 Sonnet 贵，Sonnet 比 Haiku 贵。这是最直观的一层，但也是最容易被忽视的一层——很多人默认用最强模型跑所有任务，包括那些 Haiku 就能胜任的日志梳理、格式转换类工作。

### 2. 输入 token 和输出 token 的价格不对称

输出 token 的单价通常是输入 token 的数倍（在 Anthropic 的定价体系里，输出通常是输入的 5 倍左右），原因是解码阶段（逐 token 生成）比编码阶段（一次性处理输入）计算量更大。这意味着：**让模型少输出比让模型少读输入，对成本的影响更直接**。冗长的解释性输出、重复陈述已知信息、大段的"总结一下我刚才做了什么"，都是这一层的隐性成本。

### 3. Prompt Cache：读和写的价格完全不同

这是最容易被低估、也是最值得理解的一层。Claude Code 会把对话前缀（system prompt、CLAUDE.md、工具定义、历史消息）写入缓存，只要后续请求的前缀没有变化，就可以复用缓存而不是重新计算：

| 操作类型 | 相对基础输入价格的倍率 |
| --- | --- |
| 正常输入 token | 1x |
| 5 分钟缓存写入 | 1.25x |
| 1 小时缓存写入 | 2x |
| **缓存命中（读取）** | **0.1x** |
| 输出 token | 约 5x |

缓存命中只要基础输入价格的十分之一。这也是为什么"同一个任务、不同用法、成本差几倍"这件事会成立——一个干净、连贯、不频繁打断缓存的会话，绝大部分历史 token 都以 0.1x 的价格重新处理；一个反复切换模型、频繁中断的会话，则会反复触发全价的缓存写入。

缓存的生命周期也值得记住：订阅计划（Pro/Max/Team/Enterprise）默认缓存时长为 **1 小时**，API Key 或云厂商渠道默认是 **5 分钟**。超过这个窗口没有新请求，缓存就会失效，下一条消息会重新以全价预填整个上下文。想在使用 usage credits 时依然保留 1 小时缓存，可以设置环境变量 `ENABLE_PROMPT_CACHING_1H=1`。

以下几个动作会**主动打断缓存**，导致后续请求重新全价预填：

- 切换 `/model`
- 切换 `/effort`
- 开关 fast mode
- 超过缓存生命周期没有新请求

官方博客里有一句话很直接地点出了代价：在第 50 轮对话时执行 `/model` 切换模型，意味着整段对话要重新以全价预填一次。所以模型和 effort level 最好在会话开始时就定好，而不是边用边调。

## Context 里到底装了什么

理解了计价，第二步是理解 context 窗口的构成。每一次请求，Claude Code 发给模型的不只是你刚才打的那句话，而是整个前缀——而且这个前缀逐轮累积、只增不减：

<figure class="post-diagram">
<svg viewBox="0 0 720 280" role="img" aria-label="同一会话连续三轮请求的输入构成：前缀逐轮累积，未变的部分缓存命中 0.1x，新增的工具输出全价计入">
  <!-- 顶部段标签（基础前缀，三轮共有） -->
  <g font-size="11" fill="currentColor" opacity="0.6" text-anchor="middle">
    <text x="180" y="44">系统提示 + 工具定义</text>
    <text x="286" y="44">CLAUDE.md</text>
    <text x="356" y="44">消息</text>
  </g>
  <!-- 左侧行标签 -->
  <g font-size="13" fill="currentColor" text-anchor="end">
    <text x="100" y="77">第 1 轮</text>
    <text x="100" y="145">第 2 轮</text>
    <text x="100" y="213">第 3 轮</text>
  </g>
  <!-- 第 1 轮：基础前缀 -->
  <g stroke="currentColor" stroke-opacity="0.25">
    <rect x="116" y="56" width="128" height="32" rx="4" fill="#8b7ec8" fill-opacity="0.30"/>
    <rect x="246" y="56" width="80" height="32" rx="4" fill="#8b7ec8" fill-opacity="0.30"/>
    <rect x="328" y="56" width="56" height="32" rx="4" fill="#5b8dc9" fill-opacity="0.30"/>
  </g>
  <!-- 第 2 轮：基础前缀 + Read 读到的文件 -->
  <g stroke="currentColor" stroke-opacity="0.25">
    <rect x="116" y="124" width="128" height="32" rx="4" fill="#8b7ec8" fill-opacity="0.30"/>
    <rect x="246" y="124" width="80" height="32" rx="4" fill="#8b7ec8" fill-opacity="0.30"/>
    <rect x="328" y="124" width="56" height="32" rx="4" fill="#5b8dc9" fill-opacity="0.30"/>
    <rect x="386" y="124" width="96" height="32" rx="4" fill="#5b8dc9" fill-opacity="0.30"/>
  </g>
  <text x="434" y="172" text-anchor="middle" font-size="11" fill="currentColor" opacity="0.6">Read 读到的文件</text>
  <!-- 第 3 轮：前两轮全部内容 + 测试日志 -->
  <g stroke="currentColor" stroke-opacity="0.25">
    <rect x="116" y="192" width="128" height="32" rx="4" fill="#8b7ec8" fill-opacity="0.30"/>
    <rect x="246" y="192" width="80" height="32" rx="4" fill="#8b7ec8" fill-opacity="0.30"/>
    <rect x="328" y="192" width="56" height="32" rx="4" fill="#5b8dc9" fill-opacity="0.30"/>
    <rect x="386" y="192" width="96" height="32" rx="4" fill="#5b8dc9" fill-opacity="0.30"/>
    <rect x="484" y="192" width="148" height="32" rx="4" fill="#e8a34c" fill-opacity="0.38"/>
  </g>
  <text x="558" y="213" text-anchor="middle" font-size="11" fill="currentColor" opacity="0.75">测试日志（全量）</text>
  <!-- 第 3 轮的计价标注 -->
  <g stroke="currentColor" stroke-opacity="0.35" fill="none">
    <polyline points="116,236 116,244 482,244 482,236" stroke-dasharray="3 3"/>
    <polyline points="486,236 486,244 632,244 632,236"/>
  </g>
  <g font-size="11" font-style="italic" fill="currentColor" opacity="0.6" text-anchor="middle">
    <text x="299" y="262">前缀与上一轮相同：缓存命中，0.1x</text>
    <text x="559" y="262">本轮新增：全价</text>
  </g>
</svg>
<figcaption>同一会话内连续三轮请求的输入构成：工具输出一旦写入 context，就成为后续每一轮的固定成本。</figcaption>
</figure>

几个容易被忽视的细节：

- **MCP 工具清单默认是延迟加载的**：只有工具名称进入 context，具体的工具定义要到模型真正调用某个工具时才会加载。所以 MCP server 本身不是"越多越贵"，但没用的 server 依然占用了工具名称列表的空间，值得定期用 `/mcp` 检查并关闭不用的。
- **CLAUDE.md 会在每次会话开始时整体加载**，哪怕当前任务只涉及其中一小部分内容。官方建议把 CLAUDE.md 控制在 200 行以内，只放高频、跨任务都需要的约束；具体到某个工作流的长指令（比如"如何做数据库迁移"）应该拆成 [Skills](https://code.claude.com/docs/en/skills)，按需加载。
- **工具输出会永久留在 context 里**，除非它被压缩或清空。一次 `npm test` 的全量日志、一次 `grep -r` 的大量命中，读一次就要在后续所有轮次里被重新处理（哪怕是缓存命中价）。

## 长会话为什么会越用越贵

官方文档专门总结了一个长时间运行的会话为什么消耗会显著超出预期，值得当作排查清单：

- **历史越长，每轮成本越高**：即便只是问一句话，也要把之前所有轮次（包括所有工具调用产生的中间结果）当作前缀重新处理一遍，哪怕是缓存价，量级也在累积。
- **缓存失效**：休息超过缓存生命周期（订阅 1 小时 / API 5 分钟）后的第一条消息，要全价重新预填整个上下文。
- **定时任务在空闲时也会全量发送 context**：如果配置了 scheduled task，它按固定间隔触发，哪怕会话没人在用，也会带着完整上下文发一次请求。
- **跨会话消息**：其他会话发来的消息会作为新的一轮投递到当前会话，同样带着完整历史。
- **`/compact` 本身不是免费操作**：压缩会话意味着要先把要压缩的这部分对话读一遍，所以在一个已经很长的会话里执行 `/compact`，本身就是一次不小的请求；相比之下，`/clear` 直接清空，不产生任何 token 消耗。

这些原因指向同一个结论：**会话的生命周期管理，比任何单条 prompt 的措辞优化都更影响总成本。**

## 实战技巧

### 技巧一：任务之间用 `/clear`，而不是让无关上下文一直累积

`/clear` 会清空对话历史，开始一个全新的空 context。只要当前任务和上一个任务无关，就应该 `/clear`，而不是让 Claude 在处理新任务时，还要在前缀里携带上一个任务的全部调试过程。

如果担心之后还想回来看这个会话，可以在 `/clear` 之前先执行 `/rename` 给它起一个可识别的名字，之后用 `/resume` 找回来。

### 技巧二：开局定好 `/model` 和 `/effort`，别中途切换

前面提到过，切换模型或 effort level 会打断缓存，让整段历史重新全价预填一次。做法是：任务开始前先想清楚这个任务大概需要多强的模型、多深的推理，一次定好；确实需要换模型的场景，宁可开一个新会话。

`/effort` 控制的是模型每轮生成多少 thinking token——thinking token 按输出价格计费，对于不需要复杂推理的任务（改个格式、加个日志），调低 effort level 比让模型每轮都做深度思考更省钱。在支持固定 thinking 预算的模型上，也可以直接用环境变量 `MAX_THINKING_TOKENS=8000` 这类值设置上限（自适应推理模型会忽略非零的固定预算设置，仍需用 effort level 控制）。

### 技巧三：用 @-mention 代替手打路径

当你在 prompt 里 @-mention 一个文件时，这个文件的内容会直接作为引用附加到消息里，不会触发一次单独的 `Read` 工具调用。手打路径让模型去读，则多了一轮"发起 Read 调用 → 读取 → 结果写回 context"的完整往返，路径本身也可能因为拼写误差导致重试。

### 技巧四：给高频命令加"安静参数"，写进 CLAUDE.md

很多 CLI 工具默认输出是给人看的，冗长、带颜色、带进度条，对模型来说这些都是纯噪声。把项目里每天都要跑的两三个命令，连同它们的安静参数一起固化到 CLAUDE.md：

```markdown
# 常用命令

- 跑单个测试文件：`npx vitest run <file> --reporter=dot`
- 跑 lint 只看错误：`eslint . --quiet --format compact`
- 类型检查不看进度：`tsc --noEmit --pretty false`

# Compact 指令

执行 /compact 时优先保留代码改动和测试输出，可以舍弃过程性的探索记录。
```

第二部分是官方文档里提到的一个细节：CLAUDE.md 里可以直接写"Compact instructions"，告诉模型在执行 `/compact` 时该保留什么、可以丢什么，比每次手动在 `/compact` 后面加参数更省心。

### 技巧五：用 Hook 在源头过滤噪声，而不是让模型读完整输出再筛选

如果某类命令的输出天然冗长（比如测试日志、构建日志），与其让模型读完整输出再自己找失败项，不如用一个 `PreToolUse` hook 在命令执行阶段就把输出过滤掉。这是把"筛选"这个动作从模型身上挪到确定性的脚本上，省下的不是几个 token，而是整段日志的量级：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "~/.claude/hooks/filter-test-output.sh" }
        ]
      }
    ]
  }
}
```

```bash
#!/bin/bash
input=$(cat)
cmd=$(echo "$input" | jq -r '.tool_input.command')

if [[ "$cmd" =~ ^(npm\ test|pytest|go\ test) ]]; then
  filtered="$cmd 2>&1 | grep -A 5 -E '(FAIL|ERROR|error:)' | head -100"
  echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"allow\",\"updatedInput\":{\"command\":\"$filtered\"}}}"
else
  echo "{}"
fi
```

这个 hook 检测到测试命令时，自动改写成"只保留失败相关的几行"，模型看到的永远是精简后的结果，而不是几千行的完整测试输出。

### 技巧六：噪声大的操作交给 Subagent，别让主会话吃满

跑测试、抓日志、翻文档这类任务的特点是：中间过程很吵，但最终只需要一个结论。把这类工作交给 subagent 去做，噪声留在 subagent 自己的 context 里，只有总结性的结果会回传到主会话。

需要注意一个成本上的取舍：subagent 不共享主会话的历史，如果它需要用到主会话已经读过的文件，会重新读一遍。所以 subagent 更适合"过程吵但主会话不需要细节"的场景，而不是"需要复用主会话已有认知"的场景。对于重复出现的噪声型任务（比如每天都要跑一遍的日志梳理），可以专门定义一个 `model: haiku` 的 subagent，用更便宜的模型处理这类工作。

### 技巧七：用 `/context` 体检，用 `/mcp` 断舍离

在一个全新会话里，什么都还没输入的时候先跑一次 `/context`，它会用一个色块网格直观展示当前 context 里各部分占比——CLAUDE.md、MCP 工具清单、系统提示分别占多少。这是发现"CLAUDE.md 是不是写太长了""是不是挂了一堆没用的 MCP server"最直接的方式。

发现有 MCP server 明显没在用，用 `/mcp` 查看已配置的 server 列表并禁用。另外一个反直觉的事实是：像 `gh`、`aws`、`gcloud` 这类 CLI 工具，比同等功能的 MCP server 更省 context——因为 CLI 工具不需要在每次请求里携带一份工具定义清单，模型直接调用 Bash 执行命令即可。

### 技巧八：用 `/rewind` 或双击 Escape 及时纠偏

如果发现 Claude 已经在往错误的方向走，最贵的做法是让它先跑完再纠正——那意味着一整段错误路径的 token 已经花出去了。更省钱的做法是立刻按 Escape 打断，用 `/rewind`（或双击 Escape）把代码和对话回滚到某个检查点，重新给出更准确的指令。复杂任务开始前，先用 Plan Mode（`Shift+Tab` 切换）让它先分析、给出方案再动手，同样是为了避免方向错了才发现、返工吃掉大量 token。

## 命令速查表

| 命令 / 变量 | 作用 | 使用时机 |
| --- | --- | --- |
| `/clear` | 清空对话历史，开启全新 context | 切换到不相关任务时 |
| `/compact` | 总结对话以释放 context 空间 | 长会话想继续但快到上限时；注意本身要重新读一遍历史 |
| `/context` | 以色块网格展示当前 context 构成 | 新会话开始时体检一次 |
| `/rewind` | 把代码和对话回滚到某个检查点 | 发现方向错了，需要纠偏 |
| `/rename` | 给当前会话命名 | `/clear` 之前，方便之后 `/resume` 找回 |
| `/model` | 切换模型（会打断缓存） | 会话开始时定好，避免中途切换 |
| `/effort` | 设置模型的 effort（推理深度） | 简单任务调低，复杂任务调高，开局定好 |
| `/mcp` | 管理 MCP server 连接 | 定期检查并关闭不用的 server |
| `/usage` | 查看当前会话的 token / 成本明细 | 想知道这个会话具体花在哪了 |
| `MAX_THINKING_TOKENS` | 限制固定预算模型的 thinking token 上限 | 简单任务不需要深度推理时 |
| `BASH_MAX_OUTPUT_LENGTH` | 控制命令输出读回 context 的最大字符数（默认 30000） | 命令输出经常超长又用不上全部内容时 |
| `ENABLE_PROMPT_CACHING_1H` | 消耗 usage credits 时依然保留 1 小时缓存窗口 | 依赖长缓存窗口、又开启了 usage credits 时 |

## 常见误区

- **把 `/compact` 当成免费的安全网**：`/compact` 要先读一遍要压缩的对话，本身就是一次不小的请求。真正免费的是 `/clear`——如果接下来是无关任务，直接清空比压缩更省。
- **中途换模型或调 effort**：这是最容易被忽视的一次性成本，一次切换可能让几十轮对话重新全价预填。
- **只盯着输出啰嗦，不管输入**：输出 token 贵是事实，但一个长期不清理、反复携带无关历史的会话，输入侧的重复处理量级往往才是大头。
- **只依赖 auto-compact 兜底**：auto-compact 是超限前的安全网，不是省钱手段——真正省钱的是主动 `/clear`、主动拆分任务，而不是等到自动压缩触发。
- **把所有噪声型任务都丢给主会话**：跑测试、翻日志这类任务如果每次都在主会话里全量展开，几轮下来 context 里会堆满和当前决策无关的历史细节。

## 决策框架：按影响力排优先级

如果只能优化一件事，应该先看哪个？官方建议的优先级顺序，本质上是按"对总成本的边际影响"从大到小排列：

<figure class="post-diagram">
<svg viewBox="0 0 720 120" role="img" aria-label="成本排查优先级：会话长度、模型与 Effort 稳定性、文件读取方式、命令输出体积，边际影响从大到小">
  <defs>
    <marker id="arrow-p" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="currentColor" fill-opacity="0.6"/>
    </marker>
  </defs>
  <!-- 方向标注 -->
  <text x="356" y="16" text-anchor="middle" font-size="11" font-style="italic" fill="currentColor" opacity="0.6">对总成本的边际影响：从大到小</text>
  <line x1="24" y1="26" x2="688" y2="26" stroke="currentColor" stroke-opacity="0.35" stroke-width="1" marker-end="url(#arrow-p)"/>
  <!-- 优先级链条：颜色深浅对应影响大小 -->
  <g stroke="currentColor" stroke-opacity="0.25">
    <rect x="24" y="48" width="140" height="36" rx="6" fill="#d97757" fill-opacity="0.32"/>
    <rect x="200" y="48" width="140" height="36" rx="6" fill="#e8a34c" fill-opacity="0.38"/>
    <rect x="376" y="48" width="140" height="36" rx="6" fill="#5b8dc9" fill-opacity="0.30"/>
    <rect x="552" y="48" width="140" height="36" rx="6" fill="currentColor" fill-opacity="0.07"/>
  </g>
  <g font-size="13" fill="currentColor" text-anchor="middle">
    <text x="94" y="71">会话长度与累积</text>
    <text x="270" y="71">模型与 Effort</text>
    <text x="446" y="71">文件读取方式</text>
    <text x="622" y="71">命令输出体积</text>
  </g>
  <g stroke="currentColor" stroke-opacity="0.6" stroke-width="1.2" fill="none">
    <line x1="164" y1="66" x2="194" y2="66" marker-end="url(#arrow-p)"/>
    <line x1="340" y1="66" x2="370" y2="66" marker-end="url(#arrow-p)"/>
    <line x1="516" y1="66" x2="546" y2="66" marker-end="url(#arrow-p)"/>
  </g>
</svg>
<figcaption>排查顺序：先看会话生命周期，再看模型与 effort 是否稳定，最后才是单条命令的输出细节。</figcaption>
</figure>

- **第一位是会话长度**：一个开了一整天、塞满无关任务的会话，是最大的隐性成本来源，`/clear`、`/rename`、按任务拆分会话，收益最直接。
- **第二位是模型与 effort 的稳定性**：避免中途切换打断缓存，收益是即时且确定的。
- **第三位是文件读取方式**：@-mention 代替手打路径、CLI 工具代替等效的 MCP server，属于持续的小额节省。
- **第四位是命令输出管理**：安静参数、hook 过滤、subagent 隔离，处理的是"单次操作噪声"这类局部问题。

实践上可以反过来用这个顺序做排查：如果一个会话感觉"莫名其妙很贵"，先看是不是开太久了、任务是不是该拆开，而不是先去抠某一条命令的输出格式。

## 结语

Token 效率不是一套孤立的省钱技巧，而是对 Claude Code 工作机制的一次重新理解：**context 是有价的，缓存是有条件的，每一次工具输出都会成为后续所有轮次的固定成本**。把这套机制想清楚之后，`/clear`、`/compact`、`/context`、subagent、hook 这些工具本身并不复杂，复杂的是知道在什么场景下用哪一个。

更实际的价值在于：省下来的不只是账单上的数字。一个干净、聚焦的会话，模型的注意力也更集中——context 越少无关信息，回答的相关性通常也越高。管好 context，某种意义上是同时在管成本和管质量。

## 延伸阅读

- [Maximizing the value of your Claude Code sessions](https://claude.com/blog/maximizing-the-value-of-your-claude-code-sessions) — Anthropic 官方博客，本文的主要信息来源
- [Manage costs effectively](https://code.claude.com/docs/en/costs) — Claude Code 官方成本管理文档，覆盖 track/manage/reduce 全流程
- [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) — Prompt Cache 的官方参考文档，包含价格倍率和 TTL 细节
- [Commands reference](https://code.claude.com/docs/en/commands) — `/clear`、`/compact`、`/context` 等内置命令的完整列表
- [Environment variables](https://code.claude.com/docs/en/env-vars) — `MAX_THINKING_TOKENS`、`BASH_MAX_OUTPUT_LENGTH` 等环境变量参考

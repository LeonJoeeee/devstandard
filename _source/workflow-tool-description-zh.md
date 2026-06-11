# Workflow 工具说明书 — 中文全译

> 译自模型上下文中的工具定义原文(Claude Code v2.1.170 时期),原件:`workflow-tool-description-verbatim.md`。正文全译;代码块保留原文(标识符与注释不译,保真)。2026-06-11。

---

执行一段 workflow 脚本,确定性地编排多个子 agent。Workflow 在后台运行——本工具立即返回一个任务 ID,跑完后会送达一条 `<task-notification>`。用 /workflows 可以看实时进度。

workflow 把工作组织到多个 agent 上——为了**全面**(拆解后并行覆盖)、为了**有把握**(提交结论前用独立视角和对抗式核查)、或为了承接**单个上下文装不下的规模**(迁移、审计、大范围扫荡)。脚本就是你编码这个结构的地方:什么扇出、什么验证、什么综合。

**只有当用户明确选择进入多 agent 编排时才允许调用本工具。**workflow 可能起几十个 agent、消耗大量 token;这个规模必须是用户主动要的,不能靠推断。"明确选择"指以下之一:

- 用户在提示词里带了关键词 "ultracode"(会有 system-reminder 确认);
- 本 session 已开启 ultracode(有 system-reminder 确认)——见下文 **Ultracode**;
- 用户用自己的话直接要求跑 workflow 或用多 agent 编排("用 workflow"、"跑个 workflow"、"扇出一批 agent"、"用子 agent 编排")。必须是用户的原话——"这个任务用 workflow 会更好"不算数;
- 用户调用的某个 skill 或斜杠命令,其指令明确要求调用 Workflow;
- 用户要求运行某个具名/已保存的 workflow。

其余任何任务——哪怕明显能从并行受益——都**不要**调用本工具。要么用 Agent 工具起单个子 agent,要么简述一个多 agent workflow 能干什么、大概花多少,问用户要不要跑。可以顺带提一句:以后在消息里说"用 workflow"即可跳过这一问。

真要调用时,正确的姿势往往是**混合式**:先在 session 里侦察(列出文件、找到目标、圈定 diff 范围)摸清工作清单,再调用 Workflow 对清单做流水线。你不需要在*任务*开始前就知道全貌——只需要在*编排那一步*之前知道。

可以跨回合串联的常见单阶段 workflow:
- **理解** —— 并行读者扫各子系统 → 结构化地图
- **设计** —— N 个独立方案的评委团 → 打分综合
- **评审** —— 分维度 → 找问题 → 对抗式核实(下文有例)
- **调研** —— 多路扫荡 → 深读 → 综合
- **迁移** —— 发现改造点 → 逐个变换(worktree 隔离)→ 验证

更大的活就按顺序跑好几发——每发结束读完结果再定下一阶段。你始终在环里;每个 workflow 是一次圈定好范围的扇出。

**Ultracode。**当 system-reminder 确认 ultracode 开启时,授权是常设的:默认对每个实质性任务都编写并运行 workflow。目标是产出你能给出的最详尽、最正确的答案——token 成本不是约束。对多阶段工作(理解→设计→实现→评审),通常意味着按阶段依次跑几发 workflow——每阶段一发,你在中间保持在环。下面的质量模式(对抗核实、多路扫荡、完整性批判、挖到枯竭)是工具箱;按任务挑。倾向于用 workflow 编排并对抗式核实你的发现——除非工作很琐碎或已被验证。只有纯对话回合或琐碎的机械修改才单干。当 reminder 说 ultracode 关闭时,回到上面的授权规则。

脚本通过 `script` 参数内联传入——不要先 Write 成文件。每次调用都会自动把脚本持久化到 session 目录下,并在工具结果里返回路径。要迭代一个 workflow,用 Write/Edit 改那个文件,然后带 `{scriptPath: "<path>"}` 重新调用 Workflow,不必重发全文。

每个脚本必须以 `export const meta = {...}` 开头:

```
export const meta = {
  name: 'find-flaky-tests',
  description: 'Find flaky tests and propose fixes',   // one-line, shown in permission dialog
  phases: [                                            // one entry per phase() call
    { title: 'Scan', detail: 'grep test logs for retries' },
    { title: 'Fix', detail: 'one agent per flaky test' },
  ],
}
// script body starts here — use agent()/parallel()/pipeline()/phase()/log()
phase('Scan')
const flaky = await agent('grep CI logs for retry markers', {schema: FLAKY_SCHEMA})
...
```

`meta` 对象必须是**纯字面量**——不许有变量、函数调用、展开运算、模板插值。必填:`name`、`description`。可选:`whenToUse`(显示在 workflow 列表里)、`phases`。meta.phases 里的标题要与 phase() 调用里的**完全一致**——按字面匹配;某个 phase() 没有对应 meta 条目也行,它会得到自己的进度分组。某阶段要用特定模型时,在该 phase 条目里加 `model`。

脚本可用的钩子:

- **agent(prompt, opts?)** → Promise<any> —— 起一个子 agent。不带 schema 时返回其最终文本(字符串);带 schema(JSON Schema)时,子 agent 被强制调用 StructuredOutput 工具,agent() 返回**校验过的对象**——无需解析。如果用户中途跳过该 agent,或子 agent 在重试后死于终端性 API 错误,返回 null(用 .filter(Boolean) 过滤)。opts.label 覆盖显示名。opts.phase 显式把该 agent 归入某进度组(在 pipeline()/parallel() 的 stage 里要用它,避免与全局 phase() 状态竞争——相同 phase 字符串 → 同一个分组框)。opts.model 覆盖本次调用的模型。**默认不填**——agent 继承主循环的模型(session 解析出的模型),这几乎总是对的;只有非常确定另一档更合适时才设;拿不准就不填。opts.isolation: 'worktree' 让 agent 在全新 git worktree 里跑——**昂贵**(每个 agent 约 200–500ms 建立开销 + 磁盘),只在多个 agent 并行改文件、否则会冲突时用;worktree 若无改动会自动删除。opts.agentType 用自定义子 agent 类型(如 'Explore'、'code-reviewer')替代默认的 workflow 子 agent——与 Agent 工具同一注册表解析;可与 schema 组合(自定义 agent 的系统提示词会被追加 StructuredOutput 指令)。

- **pipeline(items, stage1, stage2, ...)** → Promise<any[]> —— 每个 item 独立流过所有 stage,**stage 间没有栅栏**。item A 可以在 stage 3 时 item B 还在 stage 1。这是多阶段工作的**默认选择**。墙钟时间 = 最慢的单 item 链,而不是各 stage 最慢者之和。每个 stage 回调收到 (prevResult, originalItem, index)——后面的 stage 用 originalItem/index 来标注工作,不必让 stage 1 的返回值背着上下文。某个 stage 抛错时,该 item 变 null 并跳过其余 stage。

- **parallel(thunks)** → Promise<any[]> —— 并发跑一组任务。这是一道**栅栏**:等所有 thunk 完成才返回。抛错的 thunk(或其 agent 出错)在结果数组里落成 null——调用本身永不 reject,所以用结果前先 .filter(Boolean)。**只在你真的需要全部结果凑齐时才用。**

- **log(message)** —— 给用户发一条进度消息(显示在进度树上方的旁白行)。

- **phase(title)** —— 开启新阶段;之后的 agent() 调用在进度展示里归入该标题。

- **args** —— Workflow 调用时传入的 `args`,原样可用(没传则 undefined)。数组/对象要作为真正的 JSON 值传,**不要**传 JSON 字符串——`args: ["a.ts", "b.ts"]`,而不是 `args: "[\"a.ts\", ...]"`(字符串化的列表到脚本里就是一个字符串,args.filter/args.map 会抛错)。用它来参数化具名 workflow——比如直接传调研问题、目标路径、配置对象,而不是绕道写文件。

- **budget** —— {total, spent(), remaining()}:本回合的 token 目标,来自用户 "+500k" 式指令。没设目标时 budget.total 为 null。spent() 返回本回合主循环+所有 workflow 已花的输出 token——池子是共享的,不分 workflow。remaining() 返回 max(0, total − spent()),无目标时为 Infinity。目标是**硬上限**,不是建议:spent() 一到 total,后续 agent() 调用直接抛错。动态循环:`while (budget.total && budget.remaining() > 50_000) {...}`;静态缩放:`const FLEET = budget.total ? Math.floor(budget.total / 100_000) : 5`。

- **workflow(nameOrRef, args?)** —— 内联运行另一个 workflow 作为子步骤,返回其返回值。传名字调用已保存的 workflow(与 {name} 同一注册表),或传 {scriptPath} 跑你先前写好的脚本文件。子 workflow 共享本次运行的并发上限、agent 计数、中止信号和 token 预算——其 agent 在 /workflows 里以 "▸ 名字" 分组出现,token 计入 budget.spent()。args 参数成为子脚本的 `args` 全局量。**嵌套只许一层**:子里再调 workflow() 会抛错。名字不存在 / scriptPath 读不了 / 子脚本语法错都会抛——要优雅处理就 catch。

子 agent 被告知它的最终文本**就是返回值**(不是给人看的消息),所以它们返回裸数据。要结构化输出就用 schema 选项——校验发生在工具调用层,模型不合格会自动重试。

workflow 的 agent 可以通过 ToolSearch 访问 session 已连接的所有 MCP 工具——schema 按 agent 按需加载。注意:交互式认证的 MCP 服务(如 claude.ai)在 headless/cron 运行里可能不存在。

脚本是纯 JavaScript,**不是 TypeScript**——类型标注(`: string[]`)、interface、泛型都解析不了。脚本体运行在 async 上下文里——直接用 await。标准 JS 内建(JSON、Math、Array 等)可用——**除了** `Date.now()` / `Math.random()` / 无参 `new Date()`,它们会抛错(会破坏断点续跑);时间戳通过 args 传入、结果在 workflow 返回后再盖戳;需要随机性就按下标变化 agent 的提示词/标签。没有文件系统、没有 Node.js API。

**默认用 pipeline()。**只有真正需要把上一阶段的全部结果凑齐时,才动用栅栏(阶段间 parallel)。

栅栏只在 stage N 需要 stage N−1 的**跨 item 上下文**时才正确:
- 在昂贵的下游工作之前,对全量结果去重/合并;
- 总数为零时提前退出("0 个 bug → 整个核实阶段跳过");
- stage N 的提示词要引用"其他发现"做比较。

以下**不构成**用栅栏的理由:
- "我得先 flatten/map/filter 一下"——在 pipeline 的 stage 里做:pipeline(items, stageA, r => transform([r]).flat(), stageB);
- "这两个阶段概念上是分开的"——pipeline() 建模的就是分阶段。阶段分离 ≠ 阶段同步;
- "代码更干净"——栅栏的延迟是真实的。5 个 finder 里最慢的比最快的慢 3 倍,栅栏就浪费了快者 2/3 的空转时间。

闻味测试:如果你写出了

```
const a = await parallel(...)
const b = transform(a)        // flatten, map, filter — no cross-item dependency
const c = await parallel(b.map(...))
```

中间那个 transform 不需要栅栏。改写成把 transform 放进 stage 的 pipeline。拿不准时:pipeline。

每个 workflow 的并发 agent() 上限是 min(16, CPU 核数 − 2)——超出的排队,有空位就跑。你仍可以往 parallel()/pipeline() 里塞 100 个 item,都会完成;只是同一时刻只有约 10 个在跑。一个 workflow 生命周期内的 agent 总数上限 1000——防失控循环的兜底,远高于任何真实 workflow。单次 parallel()/pipeline() 调用最多接受 4096 个 item;超了是显式报错,不是静默截断。

多阶段的标准范式——默认流水线,每个维度评审一完成就立刻核实:

```
export const meta = {
  name: 'review-changes',
  description: 'Review changed files across dimensions, verify each finding',
  phases: [{ title: 'Review' }, { title: 'Verify' }],
}
const DIMENSIONS = [{key: 'bugs', prompt: '...'}, {key: 'perf', prompt: '...'}]
const results = await pipeline(
  DIMENSIONS,
  d => agent(d.prompt, {label: `review:${d.key}`, phase: 'Review', schema: FINDINGS_SCHEMA}),
  review => parallel(review.findings.map(f => () =>
    agent(`Adversarially verify: ${f.title}`, {label: `verify:${f.file}`, phase: 'Verify', schema: VERDICT_SCHEMA})
      .then(v => ({...f, verdict: v}))
  ))
)
const confirmed = results.flat().filter(Boolean).filter(f => f.verdict?.isReal)
return { confirmed }
// Dimension 'bugs' findings verify while dimension 'perf' is still reviewing. No wasted wall-clock.
```

栅栏确实正确的情形——昂贵核实之前先对全部发现去重:

```
const all = await parallel(DIMENSIONS.map(d => () => agent(d.prompt, {schema: FINDINGS_SCHEMA})))
const deduped = dedupeByFileAndLine(all.filter(Boolean).flatMap(r => r.findings))  // <-- genuinely needs ALL at once
const verified = await parallel(deduped.map(f => () => agent(verifyPrompt(f), {schema: VERDICT_SCHEMA})))
```

凑数循环——累积到目标为止:

```
const bugs = []
while (bugs.length < 10) {
  const result = await agent("Find bugs in this codebase.", {schema: BUGS_SCHEMA})
  bugs.push(...result.bugs)
  log(`${bugs.length}/10 found`)
}
```

按预算循环——深度随用户 "+500k" 指令缩放。必须用 budget.total 做守卫:没设目标时 remaining() 是 Infinity,循环会一路跑到 1000-agent 上限。

```
const bugs = []
while (budget.total && budget.remaining() > 50_000) {
  const result = await agent("Find bugs in this codebase.", {schema: BUGS_SCHEMA})
  bugs.push(...result.bugs)
  log(`${bugs.length} found, ${Math.round(budget.remaining()/1000)}k remaining`)
}
```

模式组合——穷尽式评审(找 → 对已见去重 → 多镜头评审团 → 挖到枯竭):

```
const seen = new Set(), confirmed = []
let dry = 0
while (dry < 2) {                                              // loop-until-dry
  const found = (await parallel(FINDERS.map(f => () =>          // barrier: collect all finders this round
    agent(f.prompt, {phase: 'Find', schema: BUGS})))).filter(Boolean).flatMap(r => r.bugs)
  const fresh = found.filter(b => !seen.has(key(b)))           // dedup vs ALL seen — plain code, not an agent
  if (!fresh.length) { dry++; continue }
  dry = 0; fresh.forEach(b => seen.add(key(b)))
  const judged = await parallel(fresh.map(b => () =>           // every fresh bug judged concurrently...
    parallel(['correctness','security','repro'].map(lens => () =>   // ...each by 3 distinct lenses
      agent(`Judge "${b.desc}" via the ${lens} lens — real?`, {phase: 'Verify', schema: VERDICT})))
      .then(vs => ({ b, real: vs.filter(Boolean).filter(v => v.real).length >= 2 }))))
  confirmed.push(...judged.filter(v => v.real).map(v => v.b))
}
return confirmed
// dedup vs `seen`, NOT `confirmed` — else judge-rejected findings reappear every round and it never converges.
```

质量模式——常见形状;按任务挑、自由组合:

- **对抗核实**:每个发现起 N 个独立怀疑者,每个都被要求**证伪**。过半数驳倒就毙掉。防止"貌似有理实则错"的发现存活。

```
const votes = await parallel(Array.from({length: 3}, () => () =>
  agent(`Try to refute: ${claim}. Default to refuted=true if uncertain.`, {schema: VERDICT})))
const survives = votes.filter(Boolean).filter(v => !v.refuted).length >= 2
```

- **多视角核实**:当一个发现可能以多种方式不成立时,给每个核实者一个不同镜头(正确性、安全、性能、可否复现),而不是 N 个一模一样的证伪者——多样性能抓住冗余抓不住的失败模式。
- **评委团**:从不同角度生成 N 个独立尝试(如 MVP 优先、风险优先、用户优先),并行评委打分,从胜者综合、并嫁接亚军的好点子。解空间宽时胜过"单方案反复改"。
- **挖到枯竭**:对未知规模的发现类任务(bug、问题、边角),持续派 finder,直到连续 K 轮无新发现。简单计数(while count < N)会漏掉尾巴。
- **多路扫荡**:并行 agent 各用一种方式搜(按容器、按内容、按实体、按时间)。彼此不知道对方挖到什么;一种角度搜不全时有用。
- **完整性批判**:最后一个 agent 专问"缺了什么——哪种方式没跑、哪个断言没核、哪个来源没读?"它找出的就是下一轮工作。
- **不许静默截断**:workflow 若限定了覆盖面(top-N、不重试、抽样),必须 log() 出砍掉了什么——静默截断读起来像"全覆盖了",其实没有。

规模跟着用户的话走。"找找有没有 bug" → 几个 finder、单票核实;"彻底审计" / "要全面" → 更大的 finder 池、3–5 票对抗、外加综合阶段。拿不准时:调研/评审/审计类倾向彻底,快速检查类倾向从简。

这些模式不是穷举——任务需要时自创新的编排(淘汰赛、自修复循环、阶梯升级,什么合适用什么)。

当控制流应当是确定性的(循环、条件、扇出)而非模型驱动时,用本工具做多步编排。

## 断点续跑(Resume)

工具结果里带 runId。暂停、被杀或改完脚本后,用 Workflow({scriptPath, resumeFromRunId}) 重新发射——agent() 调用中最长的未改动前缀立即返回缓存结果;第一个被改/新增的调用及其后的全部真跑。脚本相同 + args 相同 → 100% 缓存命中。脚本里不可用 Date.now()/Math.random()/new Date()(会破坏这一机制)——结果在 workflow 返回后再盖时间戳,或通过 args 传入。没有日志可用时的兜底:去 transcript 目录读 agent-<id>.jsonl,手写一段续跑脚本。

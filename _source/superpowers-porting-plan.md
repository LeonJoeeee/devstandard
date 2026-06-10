# superpowers → DevBook 搬运计划(2026-06-10 盘点 workflow 产出)

> 14 个 skill 逐个由独立 agent 通读分类;结构化判决存于本文件末尾附录。

# superpowers → DevBook 搬运计划

## 1. 三个清单

**整件照搬:无。** 14 个 skill 没有一个能不改就用(全都带着 Task-tool 旧派发、tests-green 硬门、报幕台词或 superpowers 自家管线)。但以下**文件/片段**接近原文可搬:

- systematic-debugging 的三个技法文件:root-cause-tracing.md、defense-in-depth.md、condition-based-waiting.md,外加 find-polluter.sh 脚本
- requesting-code-review 的 code-reviewer.md 提示词正文(人设、上下文契约、五项检查、校准段、DO/DON'T)
- finishing-a-development-branch 的 git 收尾机械步骤(顺序:先合并并确认成功 → 再删 worktree → 最后删分支;先 cd 出 worktree 再 remove;prune 自愈;走 PR 就保留 worktree;销毁前要求打出确认词;绝不擅自强推)
- test-driven-development 的 testing-anti-patterns.md(mock 反模式全套)
- writing-plans / brainstorming 的审稿人校准段("只标真正会造成问题的缺陷……除非有严重缺口,否则放行")和 spec 自查清单

**改造后搬(11 个):**

| skill | 一句话理由 |
|---|---|
| brainstorming | 提问纪律(一次一问、选择题、2-3 方案、分节确认)是建库阶段写 PRD/架构文档的最佳方法;但它自带的"每次改动都要设计仪式"和浏览器可视化子系统必须扔掉 |
| dispatching-parallel-agents | 独立性判据、分支提示词清单、汇合检查是 harness 扇出最好的现成功课;派发机制全换成 Workflow 的 parallel()/agent() |
| finishing-a-development-branch | git 收尾步骤照搬;tests-green 门换成形状化完工检查,四选一菜单基本取消(集成路径由生命周期预定) |
| receiving-code-review | 审稿意见的核实-反驳纪律,正是 harness 对抗审查"实现方"缺的那一半;改写成消费审稿输出的结构化分诊阶段 |
| requesting-code-review | 审稿人提示词正文近乎原文做 harness 审稿镜头;派发时机和自由文本输出全部换成 harness 固定结构 + schema |
| subagent-driven-development | 价值最高:两段式审查顺序、四状态汇报(DONE/DONE_WITH_CONCERNS/BLOCKED/NEEDS_CONTEXT)、升级阶梯、复审强制——全是 harness 循环的现成骨架;控制器散文本身被 Workflow 取代 |
| systematic-debugging | "查清根因前禁止提修复方案"+ 3 次失败熔断,变成 bug 形任务的阶段顺序和带计数的 while 循环;三个技法文件直接进参考文件 |
| test-driven-development | 看着测试先红的核查、mock 反模式照搬;"所有形状都强制 TDD"的框架不搬,按形状收窄(feature/bug 必须,refactor/metric 不强制) |
| using-git-worktrees | worktree 检测、子模块防误判、check-ignore 防污染照搬进支柱一;"要不要隔离"的征询问句删掉——DevBook 里一任务一 worktree 是铁规 |
| verification-before-completion | "没有新鲜证据不许说完成"变成 harness 的验证阶段:done 必须带实际命令、退出码、输出摘录,光说 done: true 不收 |
| writing-plans | "假设读者零上下文"正是写给净上下文切片 agent 的规范;无占位符、文件结构先行、自查清单照搬;TDD 五步模板和执行交接菜单不搬 |

**跳过(3 个):**

| skill | 一句话理由 |
|---|---|
| executing-plans | 它自己声明是"没有子代理时的降级路径";DevBook 永远有 Workflow,整个生态位被 harness 取代 |
| using-superpowers | 解决的是"14 个 skill 怎么被触发"的路由问题;DevBook 触发是确定的(建库与否),且它正是报幕台词的源头 |
| writing-skills | 教怎么写 skill,不是开发方法论;它的规矩用来指导 DevBook 自己的构建过程,不随 DevBook 发布 |

## 2. 落点对照

| 搬运物 | 支柱 | 参考文件 |
|---|---|---|
| brainstorming 的提问纪律、分解先于细节、2-3 方案 | 二 | prd-how、architecture-how(建库需求采集方法) |
| brainstorming/writing-plans 的 spec 自查清单 + 审稿人校准段 | 三 | workflow-harness(审稿镜头之一) |
| dispatching 的扇出判据、分支提示词清单、汇合检查 | 三 | workflow-harness |
| finishing 的 git 收尾机械步骤 | 一 | merge-finish-how;harness 末尾固定收尾阶段引用它 |
| receiving-code-review 的六步核实、澄清全部再动手、禁拍马屁 | 三 | workflow-harness(分诊阶段提示词) |
| code-reviewer.md 提示词正文 + 严重度分级 | 三 | workflow-harness(审稿镜头提示词,输出转 schema) |
| subagent-driven 的实现者/审稿者提示词、四状态枚举、升级阶梯、"允许认输"段 | 三 | workflow-harness(循环骨架与 agent 提示词) |
| systematic-debugging 三技法文件 + find-polluter.sh | 三 | 独立参考文件(debugging 类),harness bug 形阶段引用 |
| TDD 的先红核查 + testing-anti-patterns.md | 三 | workflow-harness(切片阶段提示词)+ 反模式参考文件兼审稿镜头 |
| using-git-worktrees 的检测/防护/装配机械 | 一 | worktree-how(改指 DevBook 自己的 EnterWorktree 和项目内 .worktrees/) |
| verification 的证据表、合理化对照表、红绿回归验证 | 三 | workflow-harness(完工检查阶段);"核实子代理要看 diff 不信汇报"进编排方规则 |
| writing-plans 的无占位符、完整代码、文件结构先行 | 三 | workflow-harness(设计产物/切片定义的输出要求) |
| executing-plans 残片(先批判审计划、卡住就问别硬闯、不在 main 上动工) | 一/三 | methodology-core + harness 工作者提示词 |

## 3. 冲突登记(DevBook 既定设计一律获胜)

1. **tests-green 万能门**(finishing、TDD、verification、requesting-review 清单、subagent-driven、writing-plans 模板、dispatching 汇合、worktree 基线)→ 一律改为形状化完工检查;"所有测试必须通过"的原话不许照搬。
2. **报幕台词**("Announce: I'm using X skill",至少 5 个 skill 里有)→ 全删。
3. **superpowers 自家管线串链**(brainstorm→writing-plans→subagent-driven/executing→finishing 的 REQUIRED SUB-SKILL 指针)→ DevBook 生命周期取代;跨 skill 指针一个不搬。
4. **旧式 Task-tool 派发 + 自由文本汇报** → 全换 Workflow 的 agent()/parallel() + schema 校验输出。
5. **单交互 agent 自律/对话假设**(每件事一问一答、半路问人、征询同意、自查审查时机)→ 纪律改由 harness 结构强制;人只在建库采集和两轴闸门出现;卡住=结构化 BLOCKED 输出,不是聊天暂停。
6. **每次改动都要设计仪式**(brainstorming 硬门连改配置都要)→ 库内改动就是任务,无项目文档仪式。
7. **superpowers 专属路径**(docs/superpowers/specs、~/.config/superpowers/worktrees、.superpowers 状态目录)→ 换 DevBook 文档集和项目内 .worktrees/。
8. **"绝不并行派实现者"**(subagent-driven)→ 与切片扇出直接相撞;规则收窄为"并行分支不得碰重叠文件"。
9. **收尾四选一菜单** → 集成路径预定;只在两轴闸门(动顶层设计→公开合并+人批+写 ADR;或销毁)才问人。
10. **黑话与吓唬腔**("Circle K" 暗号、"撒谎会被替换"、失败记忆)→ 按平实语言规矩剥掉。
11. **可视化伴侣浏览器子系统**(brainstorming 一半体积)→ 整体丢弃。
12. **"1% 可能就必须调用" + @path 链接问题** → 不搬;writing-skills 反而印证了"绝不 @path"这条既定规矩。

## 4. 跳过的 skill 里仍要原文摘走的宝贝

- executing-plans:"先批判性审视计划、有疑虑先提再动工";停下条件清单("宁可问清,不要瞎猜""别硬闯阻塞");"未经明确同意绝不在 main/master 上动工"。
- using-superpowers:合理化对照表这个**写法**(列出每句逃逸念头并逐条一行驳回);"指令说的是做什么,不是怎么做";"技能会演化,读当前版本"→ 转译为"每个任务重读共享架构文档,不凭记忆写码";指令优先级阶梯(人的明确指令 > 文档 > 默认);SUBAGENT-STOP 守卫(元流程文本不许漏进净上下文工作者——对 Workflow 扇出直接适用);Rigid/Flexible 标注法(标明哪些 harness 阶段不可变通)。
- writing-skills:绝不 @path 链接;description 只写触发时机不写流程摘要;"违反字面就是违反精神";"挑战每一个 token";基线先行的压力测试法——这些用于 DevBook **自己的构建过程**,不进发布内容。

## 5. superpowers 完全没有答案的空白(DevBook 独自补)

- **Workflow 工具本身**:14 个 skill 零提及;harness 模板(设计→净上下文驳斥→切片扇出→完工检查循环)、schema 校验输出、确定性编排,全部从零设计。
- **项目级文档体系**:没有 PRD、没有架构文档、没有 ADR 概念(它的 spec/plan 都是单功能级);支柱二整体自建,brainstorming 只借得来采集手法。
- **建库生命周期**:薄骨架钉死接口边界、多会话并行 worktree 对着共享架构文档协作、动核心架构必须公开合并+人批+写 ADR——全无对应物。
- **CI/CD 规则**:一片空白。
- **形状化完工检查**(feature/bug/refactor/metric):superpowers 只认识 tests-green。
- **两轴人闸**:superpowers 是随时随地问人;固定的"动顶层设计或花大成本才问"是 DevBook 独有。
- **跨会话协调**:superpowers 的并行只到会话内子代理为止,没有多 worktree、共享基线的协调模型。

---

## 附录:14 份结构化判决(JSON)

```json
[
  {
    "skill": "superpowers:brainstorming",
    "purpose": "Interactive human dialogue that turns a raw idea into an approved, written design/spec (with self-review and a reviewer subagent) before any code is written.",
    "battle_tested_gems": [
      "Elicitation discipline: ask exactly one question per message; prefer multiple-choice over open-ended; focus on purpose, constraints, success criteria.",
      "Scope-check BEFORE detail questions: if the request spans multiple independent subsystems, flag it immediately and decompose first — don't burn questions refining a project that needs splitting.",
      "Propose 2-3 approaches with trade-offs; lead with your recommended option and explain why.",
      "Present the design in sections scaled to their complexity (a few sentences up to 200-300 words); get approval after each section, not one big dump at the end.",
      "Spec self-review 4-point checklist: placeholder scan (TBD/TODO), internal consistency, single-plan scope check, ambiguity check — 'could any requirement be interpreted two different ways? If so, pick one and make it explicit.'",
      "Anti-ceremony loop-killer: 'Fix any issues inline. No need to re-review — just fix and move on.'",
      "Reviewer calibration paragraph (spec-document-reviewer-prompt.md): 'Only flag issues that would cause real problems during implementation planning... Approve unless there are serious gaps' — plus splitting output into blocking Issues vs advisory Recommendations.",
      "Boundary test for design: 'Can someone understand what a unit does without reading its internals? Can you change the internals without breaking consumers? If not, the boundaries need work.'",
      "Existing-codebase rule: follow existing patterns; include targeted improvements only where existing problems affect the work; 'don't propose unrelated refactoring.'",
      "'YAGNI ruthlessly — remove unnecessary features from all designs.'",
      "Anti-pattern framing that backs DevBook's no-size-tiering call: ''Simple' projects are where unexamined assumptions cause the most wasted work.'"
    ],
    "pillar": "doc-management",
    "verdict": "specialize",
    "rationale": "This is the strongest quarry source for DevBook's PRD/architecture-doc authoring stage: the question discipline, 2-3-approaches pattern, sectioned approval, decomposition-before-detail, and the spec self-review checklist are all proven, directly reusable prompt-craft. But it cannot port verbatim — it is the head of superpowers' own brainstorm→writing-plans→execute pipeline, hard-wires superpowers paths, and mandates design-dialogue ceremony for EVERY change, which clashes with DevBook's 'in-repo changes are just tasks' rule. The interactive single-agent dialogue fits only the 建库 elicitation stage; per-task it must become harness stages, not a conversation. The visual-companion browser subsystem (about half the skill's bulk) is heavy infrastructure that violates the lean guardrail and should be dropped wholesale.",
    "specialize_notes": "Retarget the dialogue half at the 建库 stage: it becomes the PRD + architecture-doc elicitation method (one question at a time, multiple choice, 2-3 approaches, sectioned approval), with output written to DevBook's PRD/arch/ADR doc set instead of docs/superpowers/specs/, and the terminal step changed from 'invoke writing-plans' to DevBook's next lifecycle step (scaffold thin skeleton, fan out worktree tasks). The HARD-GATE ('no implementation before approved design') stops being prose and becomes structural ordering — at repo level the 建库 sequence, at task level the harness's design→refute→implement stage order. The decomposition guidance ('too large for one spec → split into sub-projects, each gets its own cycle') maps onto splitting into parallel worktree tasks against the shared architecture doc. The spec self-review checklist plus the spec-document-reviewer prompt (with its calibration paragraph) migrate into pillar 3 as a schema-validated reviewer lens inside the harness's clean-context refutation fan-out, replacing Task-tool dispatch with Workflow agent(). Drop entirely: visual companion (server, scripts, guide), the 'create a task for each checklist item' ceremony, the writing-plans/elements-of-style cross-references, and the every-config-change-needs-a-presented-design mandate for in-repo work.",
    "conflicts": [
      "Terminal state mandates invoking the writing-plans skill — that is superpowers' brainstorm→plan→execute pipeline, which DevBook's own lifecycle replaces.",
      "HARD-GATE + anti-pattern section require a presented design and committed spec for EVERY change (even a config tweak) — DevBook locked: in-repo changes are just tasks with no project-doc ceremony; the design step lives inside the workflow harness instead.",
      "Written as an interactive one-question-at-a-time human dialogue per piece of work — DevBook per-task development is Workflow-harness-driven with human contact only at the two-axis gate; interactivity is only appropriate at the 建库 PRD stage.",
      "Hard-coded artifact convention docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md (plus .superpowers/ state dirs) — DevBook's document set is PRD/architecture/ADR.",
      "Visual-companion browser server (Node server, WebSocket helper, HTML templates, start/stop scripts) — heavy, token-intensive infrastructure against the lean/anti-ceremony guardrail.",
      "Spec reviewer is dispatched via old Task-tool style — must be rebuilt as a Workflow agent() with schema-validated output inside the refutation fan-out."
    ]
  },
  {
    "skill": "dispatching-parallel-agents",
    "purpose": "Teaches when to split work across parallel context-isolated subagents (independence test) and how to write each subagent's prompt plus how to verify at fan-in.",
    "battle_tested_gems": [
      "Context isolation principle: subagents never inherit the session's context/history — you construct exactly what they need, which also preserves the coordinator's own context.",
      "Core rule: one agent per independent problem domain; dispatch only when domains share no state and need no view of each other.",
      "Independence test / don't-fan-out list: failures may be related (fixing one fixes others), understanding requires whole-system state, exploratory debugging (you don't know what's broken yet), or branches would touch the same files/resources.",
      "Branch-prompt checklist: specific scope (one file/subsystem), clear goal, explicit constraints (e.g. 'Do NOT change production code'), and a declared expected output.",
      "Common-mistakes contrast pairs: 'fix all the tests' vs 'fix agent-tool-abort.test.ts'; 'fix the race condition' vs pasting exact error messages and test names; no constraints vs scoped constraints; 'fix it' vs 'return summary of root cause and changes'.",
      "Constraint phrasing that blocks lazy fixes: 'Do NOT just increase timeouts - find the real issue.'",
      "Fan-in verification checklist: read each branch's summary, check whether branches edited the same code, run an integrated check across all changes together, and spot-check because agents make systematic errors."
    ],
    "pillar": "workflow-harness",
    "verdict": "specialize",
    "rationale": "The judgment content (independence criteria, branch-prompt craft, fan-in checks) is exactly the discipline DevBook's harness needs for its parallel reviewer fan-outs and implementation-slice fan-outs, and it's proven and concise. But the entire dispatch mechanism is the older Agent-tool style (`Task(...)` calls, informal prose summaries at fan-in), which Workflow replaces with parallel()/agent() and schema-validated outputs. So it can't port verbatim, yet skipping it would discard the best battle-tested fan-out prompt-craft in the quarry. It belongs inside pillar 3 as a reference file informing the harness design, not as its own skill.",
    "specialize_notes": "Delete the Task() dispatch examples and the dot digraph; mechanics become Workflow's parallel()/agent(). 'Expected output: summary' becomes 'define the branch's output schema' (schema-validated). The shared-state/interference criterion becomes DevBook's partition rule: one worktree per task, non-overlapping file slices per parallel branch. The fan-in verification section stops being advice to an interactive agent and becomes a fixed join stage in the harness (collect structured outputs, conflict-check touched files, run the shape-specific done-check — not a blanket 'run full test suite'). The when-to-use decision is made by the harness author at template-design time (which stages fan out), not re-decided mid-session. Fold the surviving content into a pillar-3 reference file (fan-out criteria + branch-prompt checklist + join checks) rather than a standalone skill.",
    "conflicts": [
      "Dispatch mechanics are pre-Workflow Agent-tool style (bare Task() calls, free-text summaries) — superseded by Workflow's parallel()/agent() with schema-validated structured outputs.",
      "Integration step says 'run full test suite' as the universal green gate; DevBook uses shape-specific done-checks instead.",
      "Framed as a standalone skill the agent self-selects mid-session; in DevBook fan-out points are fixed deterministically by the harness template, so this becomes reference material, not a trigger-able skill."
    ]
  },
  {
    "skill": "superpowers:executing-plans",
    "purpose": "Single-agent fallback procedure for walking a written implementation plan task-by-task in a fresh session: review the plan critically, execute steps exactly with TodoWrite, stop and ask when blocked, then chain to finishing-a-development-branch.",
    "battle_tested_gems": [
      "Review the plan critically FIRST and raise concerns before starting execution — never start implementing a plan you have doubts about",
      "Explicit stop-conditions list: missing dependency, failing verification, unclear instruction, repeated verification failure — 'Ask for clarification rather than guessing' / 'Don't force through blockers'",
      "Follow plan steps exactly; don't skip verifications (treat each task's verification as non-optional)",
      "Never start implementation on main/master branch without explicit user consent",
      "Return to the review step when the plan is updated or the fundamental approach needs rethinking (don't keep executing a stale plan)"
    ],
    "pillar": "workflow-harness",
    "verdict": "skip",
    "rationale": "Superpowers itself marks this skill as the degraded path for environments WITHOUT subagents (line 14 says to use subagent-driven-development instead when subagents exist), and DevBook always has the Workflow tool, so the skill's entire niche is structurally superseded by the harness (design -> adversarial review -> slice fan-out -> done-check loop replaces linear TodoWrite plan-walking). Its body is mostly scaffolding DevBook can't use: announce lines, TodoWrite bookkeeping, and required sub-skill chaining to superpowers skills that won't be installed. The handful of genuinely good one-liners (critical pre-review, stop-don't-guess, never-on-main) are prompt fragments to fold into harness worker-agent prompts and pillar-1 standards, not enough to justify porting or specializing the skill as a unit.",
    "specialize_notes": "",
    "conflicts": [
      "'Announce: I'm using the executing-plans skill' lines — known DevBook anti-pattern",
      "Hard required dependencies on superpowers:writing-plans, superpowers:finishing-a-development-branch, superpowers:using-git-worktrees — superpowers will not be installed",
      "Single interactive agent walking a static plan doc with TodoWrite vs DevBook's mandatory Workflow-tool orchestration per task; the skill is explicitly the no-subagent fallback",
      "Plan document as the execution driver vs DevBook where the static SDD/pseudocode doc is an OPTIONAL aid and the Workflow harness is the driver",
      "Mid-execution interactive 'stop and ask your human partner' vs DevBook's fixed two-axis human gate (touches top-level design OR large cost); in a Workflow worker, blocked state must surface as schema-validated structured output, not a conversational pause"
    ]
  },
  {
    "skill": "finishing-a-development-branch",
    "purpose": "Closes out a finished dev branch: gate on tests, detect worktree/normal-repo/detached-HEAD state, offer a fixed merge/PR/keep/discard menu, then execute integration and safe worktree/branch cleanup.",
    "battle_tested_gems": [
      "Cleanup ordering rule: merge and verify success FIRST, then remove worktree, THEN delete branch — `git branch -d` fails while a worktree still references the branch, and removing the worktree before confirming merge loses work",
      "Always `cd` to the main repo root before `git worktree remove` — running it from inside the worktree being removed fails silently; main root via `git -C \"$(git rev-parse --git-common-dir)/..\" rev-parse --show-toplevel`",
      "Environment detection by comparing `git rev-parse --git-dir` vs `--git-common-dir` (equal = normal repo, different = worktree), with detached HEAD treated as externally managed: reduced menu, no cleanup",
      "Provenance check before cleanup: only remove worktrees your own tooling created (known path prefixes); never remove harness-owned workspaces — prevents phantom state",
      "Run `git worktree prune` after removal as self-healing for stale registrations",
      "Keep the worktree alive when the outcome is a PR — the human needs it to iterate on review feedback; cleanup only on merge-and-done or discard",
      "Destructive-action guard: list exactly what will be deleted (branch, commits, worktree path) and require the human to type a literal confirmation word before force-delete",
      "Anti-open-ended-question idiom: present exactly N enumerated options with no extra prose, instead of asking 'what should I do next?'",
      "Red-flag line: never force-push without explicit request",
      "Quick-reference table mapping each option to merge/push/keep-worktree/cleanup-branch — compact and unambiguous"
    ],
    "pillar": "dev-standards",
    "verdict": "specialize",
    "rationale": "This is exactly the task-exit mechanics DevBook's one-session-one-worktree-one-task model needs, and the git sequencing rules (merge-verify-remove-delete order, cd-out-before-remove, prune, provenance check, PR-keeps-worktree) are proven and rarely written down anywhere — worth porting nearly verbatim into a pillar-1 reference file. But the framing around them clashes with locked design: the tests-green hard gate must become the task's shape-specific done-check, and the interactive 4-option menu mostly evaporates because DevBook's lifecycle already prescribes the integration path (merge back against the shared architecture base, human gate only when top-level design is touched or cost is large). So: keep the mechanics, replace the gate and the menu.",
    "specialize_notes": "Becomes the fixed final stage of the per-task workflow harness plus a pillar-1 reference file. (1) Replace the Step-1 tests-green gate with \"the task's done-check (feature/bug/refactor/metric shape) is satisfied\" — the harness's done-check loop already guarantees this before the close-out stage runs. (2) Drop the interactive 4-option menu as the default: DevBook predetermines integration (merge back to the shared base / open PR per repo convention); retain a reduced menu or human prompt only at the two human-gate axes (touches top-level architecture → public merge + human approval + ADR written; or discard, which always needs typed confirmation). (3) Re-specify the worktree provenance paths to DevBook's own worktree convention (one worktree per task), replacing `.worktrees/`/`~/.config/superpowers/worktrees/`. (4) Strip the \"Announce: I'm using X skill\" line. (5) The architecture-touch branch of close-out gains a DevBook-specific step the original lacks: write the ADR before merge approval. Cleanup mechanics (ordering, cd-out, prune, PR-keeps-worktree, typed discard confirmation, never force-push) port verbatim.",
    "conflicts": [
      "Mandatory tests-pass gate before any close-out ('Cannot proceed with merge/PR until tests pass') conflicts with DevBook's shape-specific done-checks — e.g. a metric/latency task is done when the metric target is met, not merely when tests are green",
      "Interactive 'present exactly 4 options' menu assumes the human decides integration per branch; DevBook's lifecycle predetermines merge-back against the shared architecture doc, with human approval reserved for the two gate axes (top-level design touched, large cost) — asking every time is ceremony",
      "'Announce: I'm using the finishing-a-development-branch skill' line violates DevBook's no-announce guardrail",
      "Superpowers-specific worktree provenance paths (~/.config/superpowers/worktrees/ etc.) and 'host harness owns the workspace' assumptions don't match DevBook's one-worktree-per-task convention and must be re-specified, not ported",
      "Written for one interactive agent at branch end; in DevBook this discipline lives as a deterministic final stage inside the Workflow harness, not a standalone skill the agent decides to invoke"
    ]
  },
  {
    "skill": "receiving-code-review",
    "purpose": "Discipline for handling code review feedback: verify each suggestion against codebase reality, push back with technical reasoning when wrong, never performatively agree or blindly implement.",
    "battle_tested_gems": [
      "Core principle one-liner: 'Verify before implementing. Ask before assuming. Technical correctness over social comfort.'",
      "Six-step response pattern: READ complete feedback without reacting -> UNDERSTAND (restate in own words) -> VERIFY against codebase -> EVALUATE for THIS codebase -> RESPOND (acknowledge or reasoned pushback) -> IMPLEMENT one item at a time.",
      "Forbidden-responses list: ban 'You're absolutely right!', 'Great point!', any gratitude expression; instead restate the requirement, ask, push back, or just act — 'the code itself shows you heard the feedback'.",
      "Unclear-items rule: if ANY item is unclear, STOP and clarify ALL before implementing ANY ('items may be related; partial understanding = wrong implementation'), with the concrete 'understand 1,2,3,6, unclear on 4,5' example.",
      "External-reviewer verification checklist: correct for THIS codebase? breaks existing functionality? reason the current implementation exists? all platforms/versions? does the reviewer have full context?",
      "Can't-verify honesty pattern: 'I can't verify this without [X]. Should I investigate/ask/proceed?' — state the limitation instead of proceeding anyway.",
      "YAGNI grep-check: when a reviewer says 'implement properly', grep for actual usage first; if unused, propose removal instead ('you and reviewer both report to me — if we don't need it, don't add it').",
      "Implementation order for multi-item feedback: blocking issues -> simple fixes -> complex fixes; verify each individually, check for regressions.",
      "Graceful correction of wrong pushback: 'You were right — I checked [X] and it does [Y]. Implementing now.' No long apology, no defending, no over-explaining.",
      "Escalation rule: if a suggestion conflicts with prior architectural decisions, stop and raise to the human first — maps directly onto DevBook's touches-top-level-design human gate.",
      "Common-mistakes table (performative agreement / blind implementation / batch without testing / assuming reviewer is right / avoiding pushback / partial implementation / proceeding when unverifiable) — compact and reusable as-is.",
      "Bottom line: 'External feedback = suggestions to evaluate, not orders to follow.'"
    ],
    "pillar": "workflow-harness",
    "verdict": "specialize",
    "rationale": "DevBook's harness is built on adversarial review fan-outs, and this skill is the missing implementer-side half: without it, fan-out findings get blindly implemented and the adversarial step is wasted. The prompt-craft is dense and battle-tested (verification checklist, clarify-all-first rule, YAGNI grep, anti-sycophancy ban) and ports nearly verbatim. But it is written for one interactive agent answering a human/GitHub reviewer; in DevBook most review arrives as structured subagent output inside the Workflow, so the framing, source-handling, and output shape must change. Skipping it would lose proven text; porting verbatim would import interactive-session assumptions that don't match the harness.",
    "specialize_notes": "Recast as the 'triage review findings' stage inside the workflow harness: when the implementer agent consumes adversarial reviewer fan-out output, each finding is verified against the codebase and returned as a schema-validated structured verdict (accept/reject/needs-clarification + evidence), with rejects carrying technical reasoning — the six-step pattern and external-reviewer checklist become that stage's prompt. Collapse the human-vs-external source split: harness reviewers ARE the default-skeptical 'external' case; findings that conflict with the shared architecture doc route to DevBook's human gate + ADR path instead of 'discuss with your human partner'. Replace 'test each fix individually' with verify-each-against-the-shape-specific-done-check. Drop the 'Circle K' signal phrase (in-joke jargon) and the GitHub thread-reply mechanics (or move that one line to pillar-1 dev-standards if PR flows exist). Keep the performative-agreement ban as cross-cutting style text usable in any interactive human moment too.",
    "conflicts": [
      "'Test each fix individually / verify no regressions' assumes a tests-green gate; DevBook uses shape-specific done-checks (feature/bug/refactor/metric), so the verification wording must change.",
      "'Your human partner' interactive-session framing pervades the text; in DevBook most reviewers are clean-context subagents inside the Workflow and the human only enters at the two-axis gate.",
      "'Strange things are afoot at the Circle K' signal phrase is in-joke jargon, violating the plain-language guardrail.",
      "GitHub inline-thread reply mechanics is incidental tooling advice, not part of the harness review loop (relocate or drop)."
    ]
  },
  {
    "skill": "requesting-code-review",
    "purpose": "Dispatch a fresh-context code-reviewer subagent with precisely crafted context (description + requirements + git SHA range), get severity-bucketed findings, and triage them before work cascades.",
    "battle_tested_gems": [
      "Context-clean principle stated crisply: the reviewer gets precisely crafted context for evaluation — never your session's history; keeps reviewer focused on the work product and preserves the worker's context.",
      "Reviewer's whole world = {DESCRIPTION} + {PLAN_OR_REQUIREMENTS} + exact git range (BASE_SHA..HEAD_SHA with `git diff --stat` then `git diff`) — a minimal, reproducible handoff contract.",
      "Severity triage protocol for acting on feedback: fix Critical immediately, fix Important before proceeding, note Minor for later — and push back if the reviewer is wrong, with technical reasoning/evidence, never blind compliance.",
      "Calibration block: categorize by ACTUAL severity, not everything is Critical; acknowledge strengths first — accurate praise makes the implementer trust the rest of the feedback.",
      "Reviewer may fault the spec, not just the code: 'If you find issues with the plan itself rather than the implementation, say so'; flag plan deviations specifically so the implementer can confirm whether they were intentional.",
      "Per-issue required shape: file:line reference, what's wrong, why it matters, how to fix — plus a forced clear verdict (Ready to merge? Yes / No / With fixes + 1-2 sentence reasoning).",
      "DON'T list for reviewers: never say 'looks good' without checking, never mark nitpicks Critical, never give feedback on code you didn't actually read, never be vague ('improve error handling'), never dodge the verdict.",
      "Five-area review checklist worth porting: plan alignment / code quality / architecture / testing-verifies-real-behavior-not-mocks / production readiness (migrations, backward compat).",
      "Anti-skip rule: never skip review because 'it's simple'; review early, review often."
    ],
    "pillar": "workflow-harness",
    "verdict": "specialize",
    "rationale": "The payload (code-reviewer.md) is the best pre-existing articulation of exactly what DevBook's harness already mandates — context-clean adversarial review — so the reviewer prompt ports nearly verbatim as the reviewer-lens inside the harness's review stages. But the shell is obsolete: Task-tool dispatch, self-policed review cadence, and freeform markdown output all belong to the one-interactive-agent era. In a Workflow-driven world the dispatch, cadence, and output-consumption are deterministic harness structure, so only the prompt text and triage rules survive, restructured.",
    "specialize_notes": "Keep code-reviewer.md's prompt body (persona, context contract, checklist, calibration, DO/DON'T) as the reviewer-stage prompt in the harness. Replace Task-tool dispatch with Workflow agent()/parallel() — it naturally becomes the per-slice or pre-merge review fan-out. Drop the 'when to request review' cadence rules entirely: review points are wired into the harness template, not agent discipline. Convert the output format into a schema-validated structured output (strengths, issues[{severity, file_line, what, why, fix}], verdict enum) so the harness loop can branch on Critical/Important counts; 'Ready to merge?' becomes the loop condition feeding the fixed done-check. Replace the checklist's 'All tests passing?' line with the task's shape-specific done-check (feature/bug/refactor/metric). Keep the implementer-side triage + push-back-with-evidence rules as the prompt for the stage that consumes review output (pairs with receiving-code-review material).",
    "conflicts": [
      "Dispatch mechanics use Task tool / general-purpose subagent (older Agent-tool style); DevBook mandates the Workflow tool for orchestration.",
      "Mandatory review cadence ('after each task', 'before merge') assumes one interactive agent self-policing; in DevBook this is deterministic harness structure, not skill-enforced discipline.",
      "Checklist line 'All tests passing?' leans toward a tests-green gate; DevBook uses shape-specific done-checks.",
      "Freeform markdown output format; DevBook's Workflow requires schema-validated structured outputs for the loop to consume."
    ]
  },
  {
    "skill": "subagent-driven-development",
    "purpose": "A controller loop that executes an implementation plan by dispatching a fresh clean-context subagent per task, each followed by a spec-compliance review then a code-quality review, with a structured status/escalation protocol.",
    "battle_tested_gems": [
      "Two-stage review ordering rule: spec compliance must pass BEFORE code quality review starts; never run them in the wrong order and never advance with either review's issues open",
      "Four-status report protocol for workers: DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT, plus 'Never silently produce work you're unsure about' — maps directly to a Workflow schema enum",
      "BLOCKED escalation ladder: context problem -> provide context and re-dispatch; needs more reasoning -> stronger model; too large -> split; plan itself wrong -> escalate to human; never retry the same model with nothing changed",
      "Adversarial spec-reviewer framing, verbatim-worthy: 'The implementer finished suspiciously quickly. Their report may be incomplete, inaccurate, or optimistic. You MUST verify everything independently... Verify by reading code, not by trusting report'",
      "Spec reviewer's three-bucket check: missing requirements / extra unrequested work (over-engineering) / misunderstandings (right feature, wrong way)",
      "Context-curation rule: paste the FULL task text plus scene-setting context into the worker prompt; never make the subagent read the plan file itself",
      "Permission-to-fail text, verbatim-worthy: 'It is always OK to stop and say this is too hard for me. Bad work is worse than no work. You will not be penalized for escalating'",
      "Pre-report self-review checklist (completeness / quality / YAGNI discipline / do tests verify behavior not mocks) with 'fix what you find before reporting'",
      "Model tiering by task signals: 1-2 files with complete spec -> cheap model; multi-file integration -> standard; design/review judgment -> most capable",
      "Continuous-execution rule: no 'should I continue?' check-ins between tasks; only stop on unresolvable BLOCKED, genuine ambiguity, or completion",
      "Review-loop discipline: reviewer found issues -> same implementer fixes -> reviewer re-reviews; the re-review is mandatory, not optional",
      "Anti-context-pollution rule: if a subagent fails, dispatch a fix subagent with specific instructions rather than the controller fixing it by hand",
      "Code-organization worker guidance: one clear responsibility per file; if a file outgrows the plan's intent, report DONE_WITH_CONCERNS instead of restructuring on your own"
    ],
    "pillar": "workflow-harness",
    "verdict": "specialize",
    "rationale": "This is the highest-value quarry skill for pillar 3: it is essentially a hand-rolled prose version of what DevBook's Workflow harness does in code, so its hard-won loop discipline (two-stage review ordering, status protocol, escalation ladder, re-review mandate) transfers directly, and its worker/reviewer prompt templates are close to verbatim-portable as Workflow agent() prompts. But the orchestration layer itself (DOT-graph controller choreography, TodoWrite bookkeeping, interactive mid-task Q&A with the controller, Task-tool dispatch) is superseded by deterministic Workflow pipelines, and several rules conflict with locked DevBook decisions. So: keep the prompts and the rules, throw away the controller prose.",
    "specialize_notes": "Port the implementer and spec-reviewer prompt bodies near-verbatim as Workflow agent() prompts; the four statuses become a schema-validated enum, and the BLOCKED/NEEDS_CONTEXT branches become while-loop arms in the harness (escalation ladder encoded as: re-dispatch with added context -> re-dispatch with stronger model -> split -> surface to human). The interactive 'ask questions before you begin' loop cannot exist mid-Workflow — replace with a structured NEEDS_CONTEXT output carrying the questions, answered by the orchestrating stage before re-dispatch. Drop the DOT process graphs, TodoWrite steps, and all cross-references to other superpowers skills (using-git-worktrees, writing-plans, requesting-code-review, finishing-a-development-branch, TDD); the code-quality-reviewer template is mostly a pointer to requesting-code-review and needs a self-contained DevBook replacement. Replace the implicit tests-green/TDD gate with shape-specific done-checks. Relax 'never dispatch implementers in parallel' to 'parallel only across non-overlapping slices fixed by the architecture/skeleton' to match DevBook's slice fan-out; keep the underlying no-shared-files concern. The 'final code reviewer over the entire implementation' step maps onto the harness's fixed done-check stage.",
    "conflicts": [
      "'Never dispatch multiple implementation subagents in parallel' directly contradicts DevBook's harness design of fanning out implementation in parallel slices (resolvable: scope the rule to overlapping files, not parallelism per se)",
      "Assumes interactive back-and-forth between controller and a running subagent ('ask questions now', controller answers mid-task) — impossible in the deterministic Workflow model with schema-validated one-shot outputs",
      "TDD/tests-green is baked in as the worker discipline and quality gate; DevBook uses shape-specific done-checks (feature/bug/refactor/metric)",
      "Hard-wires the superpowers pipeline via required skills (writing-plans upstream, finishing-a-development-branch downstream, requesting-code-review template) — superpowers will not be installed",
      "Example opens with the announce idiom ('I'm using Subagent-Driven Development to execute this plan'), which DevBook explicitly drops",
      "Controller mechanics (TodoWrite task tracking, DOT digraph flowcharts, Task-tool dispatch syntax) duplicate what Workflow pipeline()/while() already does deterministically"
    ]
  },
  {
    "skill": "systematic-debugging",
    "purpose": "A four-phase debugging discipline that forbids proposing any fix before root-cause evidence exists, with a 3-failed-fixes circuit breaker that escalates to questioning the architecture with the human; ships three technique references (backward root-cause tracing, defense-in-depth validation, condition-based waiting) and a test-polluter bisection script.",
    "battle_tested_gems": [
      "The Iron Law gate: 'NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST' — investigation phase must complete before a fix may even be proposed",
      "Multi-component evidence rule: before any fix, instrument EVERY component boundary (log data in/out, config propagation), run once, identify the failing layer, THEN investigate that layer",
      "3-failed-fixes circuit breaker: stop, count attempts; at 3+ the problem is the architecture not the hypothesis — 'this is NOT a failed hypothesis, this is a wrong architecture' — escalate to the human before attempt #4",
      "Single-hypothesis discipline: write down 'I think X is the root cause because Y', test with the SMALLEST change, one variable at a time, never stack fixes",
      "Red-flags self-check list ('just try changing X', 'I don't fully understand but this might work', 'one more fix attempt', proposing solutions before tracing data flow) → all mean return to Phase 1",
      "Rationalization table (excuse vs reality), e.g. 'Emergency, no time for process' → systematic debugging is FASTER than guess-and-check thrashing; 'issue is simple' → simple bugs have root causes too",
      "Backward tracing: never fix where the error appears; trace the bad value up the call chain to its origin, fix at source (root-cause-tracing.md, near-verbatim portable)",
      "Defense-in-depth four layers after the source fix: entry validation, business-logic validation, environment guards, debug instrumentation — 'single validation fixed the bug; multiple layers make it impossible' (defense-in-depth.md, near-verbatim portable)",
      "Condition-based waiting over arbitrary sleeps: poll for the actual condition with timeout+description; arbitrary delay allowed only after the triggering condition, based on known timing, with a comment why (condition-based-waiting.md, near-verbatim portable)",
      "find-polluter.sh: bisection script running tests one-by-one until pollution appears — directly reusable utility",
      "Honest exit path: if investigation truly shows environmental/timing cause, document what was investigated and add handling+monitoring — but '95% of no-root-cause cases are incomplete investigation'",
      "Phase-1 basics checklist worth keeping verbatim: read the full error/stack trace, reproduce reliably before theorizing, diff recent changes/deps/config, find a working example in the same codebase and list EVERY difference"
    ],
    "pillar": "workflow-harness",
    "verdict": "specialize",
    "rationale": "The content is high-value, almost entirely methodology-agnostic prompt-craft that maps directly onto DevBook's bug-shape task work inside pillar 3. But the SKILL.md is written as self-policing prose for one interactive agent (introspective red-flag lists, 'your human partner's signals you're doing it wrong'), while DevBook enforces discipline structurally via the Workflow harness — so the phases must become stages with schema-required evidence rather than willpower instructions. The three technique files and the bisection script can port near-verbatim as reference files, which fits the 'reference files not many skills' guardrail; only the orchestration framing and cross-skill links need rework.",
    "specialize_notes": "Convert the four phases into ordered harness stages for bug-shaped tasks: an investigation stage whose schema-validated structured output (repro steps, trace to origin, identified failing component/boundary evidence) is mandatory before any fix stage can run — the Iron Law becomes stage ordering, not exhortation. The hypothesis→minimal-fix→verify cycle becomes a while-loop with an explicit attempt counter; counter reaching 3 triggers DevBook's human gate (architecture question = touches top-level design axis, may yield an ADR). The red-flags list and rationalization table become (a) prompt text inside the investigation/fix stages and (b) a reviewer-lens checklist for clean-context adversarial reviewers refuting a proposed fix ('did they trace to source or patch the symptom?', 'is this fix #3+?'). 'Create failing test before fixing' folds into the bug-shape done-check (already DevBook's design) instead of linking to a TDD skill. Port root-cause-tracing.md, defense-in-depth.md, condition-based-waiting.md, and find-polluter.sh as reference files near-verbatim; drop the 'your human partner's signals' section (interactive-conversation specific), the DOT digraphs (replace with plain text per plain-language guardrail), and the unverifiable Real-World Impact stats.",
    "conflicts": [
      "Cross-references superpowers:test-driven-development and superpowers:verification-before-completion as required/related skills — superpowers will not be installed; the failing-test step must fold into DevBook's bug-shape done-check instead of a universal TDD gate",
      "Enforcement model mismatch: the skill relies on the agent self-policing mid-conversation, whereas DevBook's locked design puts enforcement in deterministic harness structure (stage ordering, schema-validated outputs); ported verbatim it would be redundant exhortation",
      "'Discuss with your human partner' escalation is phrased as ad-hoc conversation; in DevBook it must route through the defined human gate (top-level-design / large-cost axes) and produce an ADR when the architecture is overturned"
    ]
  },
  {
    "skill": "test-driven-development",
    "purpose": "Enforces strict red-green-refactor TDD — write a failing test, watch it fail for the right reason, minimal code to green — plus a sibling reference of mock/testing anti-patterns with stop-gate checks.",
    "battle_tested_gems": [
      "Core one-liner: \"If you didn't watch the test fail, you don't know if it tests the right thing\" — justifies the whole discipline in one sentence.",
      "Verify-RED checklist: test fails (not errors), failure message is the expected one, fails because the feature is missing (not a typo); \"test passes immediately = you're testing existing behavior, fix the test\".",
      "Iron Law phrasing + no-loophole closure: \"NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST\"; wrote code first? \"Delete means delete\" — no keep-as-reference, no adapting it while writing tests.",
      "Excuse | Reality rationalization table pre-empting known LLM excuses (\"too simple to test\", \"I'll test after\", sunk-cost \"deleting X hours is wasteful\", \"it's spirit not ritual\").",
      "Crisp tests-first vs tests-after framing: tests-after answer \"what does this do?\", tests-first answer \"what SHOULD this do?\" — tests-after are biased by the implementation.",
      "Red Flags list as hard stop triggers: code before test, test passes immediately, can't explain why the test failed, \"this is different because...\".",
      "Mock iron laws: NEVER test mock behavior; NEVER add test-only methods to production classes; NEVER mock without understanding the dependency's side effects.",
      "Gate-function prompt idiom: imperative pseudocode \"BEFORE doing X: ask Q; IF yes: STOP, do alternative instead\" — reusable shape for any in-agent discipline check.",
      "Incomplete-mock rule: mock the COMPLETE data structure as it exists in reality, not just the fields your immediate test uses — partial mocks fail silently downstream.",
      "Mock-complexity warning signs: mock setup longer than test logic, test breaks when the mock changes, can't explain why the mock is needed → use an integration test with real components.",
      "When-stuck design-feedback table: test too complicated = design too complicated, simplify the interface; must mock everything = code too coupled, use dependency injection.",
      "GREEN verification includes \"output pristine (no errors, no warnings)\" and \"other tests still pass — fix now\", not just the new test passing."
    ],
    "pillar": "workflow-harness",
    "verdict": "specialize",
    "rationale": "The verify-RED discipline and the mock anti-patterns are among the highest-value prompt-craft in the whole plugin and transfer almost verbatim as prose blocks. But the skill's frame — TDD mandatory for every shape, no exceptions without asking the human — is precisely the mandatory tests-green-gate idiom the locked design replaces with shape-specific done-checks, and it is written for one interactive agent self-policing a long session, whereas DevBook's harness sequences test-writing before implementation deterministically. So the craft ports, the frame does not: it becomes the implementation-slice stage discipline for test-gated shapes plus a reviewer lens, not a standalone always-on skill.",
    "specialize_notes": "(1) Fold the RED/GREEN cycle into the harness's implementation-slice stage prompt, scoped by shape: mandatory for feature and bug shapes (bug = failing repro test first); for refactor the done-check is existing tests stay green (no new failing test required); for metric/latency shapes the metric is the done-check and tests support rather than gate. (2) Capture evidence in the slice agent's schema-validated structured output (e.g. test_path, red_run_excerpt, green_run_excerpt) so the orchestrator can verify watch-it-fail happened instead of trusting prose. (3) Port testing-anti-patterns.md nearly verbatim as a reference file and assign it as one clean-context reviewer lens in the adversarial review fan-out (checks: asserting on mocks, test-only prod methods, incomplete mocks, mock setup heavier than test). (4) Drop the \\\"ask your human partner for exceptions\\\" flow — DevBook's two-axis human gate governs escalation. (5) Shrink the anti-rationalization prose: deterministic stage ordering removes most chances to rationalize; keep the Verify-RED checks and the delete-means-delete rule for code an implementer wrote ahead of its test, since those are in-agent failure modes the harness cannot mechanically prevent. (6) Drop the graphviz digraph and \\\"Announce skill\\\"-style framing per lean guardrails.",
    "conflicts": [
      "\"Always: new features, bug fixes, refactoring\" + verification checklist requiring every new function to have a test and all tests green is the mandatory tests-green gate the locked design rejects in favor of shape-specific done-checks.",
      "\"No exceptions without your human partner's permission\" adds a human-approval ceremony that clashes with DevBook's two-axis human gate (touches top-level design OR large cost).",
      "Written as an always-on self-policing discipline for one interactive agent; in DevBook, TDD ordering is enforced structurally by the workflow harness, so porting the skill standalone would duplicate what the orchestration already guarantees."
    ]
  },
  {
    "skill": "using-git-worktrees",
    "purpose": "Ensures task work happens in an isolated git worktree: detect existing isolation, prefer the platform's native worktree tool, fall back to manual git worktree with safety checks, then run project setup and a baseline check.",
    "battle_tested_gems": [
      "Isolation detection: resolve and compare `git rev-parse --git-dir` vs `--git-common-dir`; if they differ you are already in a linked worktree — never create a nested one.",
      "Submodule guard: `git rev-parse --show-superproject-working-tree` returning a path means you're in a submodule, not a worktree — treat as a normal repo before concluding 'already isolated'.",
      "'Never fight the harness': if a native worktree tool exists (EnterWorktree, /worktree, --worktree), use it; raw `git worktree add` alongside a native tool creates phantom state the harness can't see or clean up — called out as the #1 mistake.",
      "Mandatory ignore verification for project-local worktree dirs: `git check-ignore -q .worktrees` before creating; if not ignored, add to .gitignore and commit first — prevents worktree contents polluting the repo.",
      "Directory priority order with explicit tie-breaks: declared preference > existing `.worktrees/` > existing `worktrees/` > default `.worktrees/` (hidden dir preferred).",
      "Clean-baseline principle: verify project state before starting work so new breakage can be distinguished from pre-existing breakage; if baseline is already broken, report and ask rather than silently proceed.",
      "Sandbox fallback: if worktree creation fails on a permission error, say the sandbox blocked it and work in place — don't thrash against denials.",
      "Manifest-based auto-setup in the fresh worktree: detect package.json/Cargo.toml/requirements.txt/pyproject.toml/go.mod and run the matching install/build.",
      "Compact 'Quick Reference' situation→action table plus 'Red Flags: Never/Always' list — an effective decision-procedure format worth reusing in DevBook reference files."
    ],
    "pillar": "dev-standards",
    "verdict": "specialize",
    "rationale": "Worktree mechanics sit at the heart of DevBook's fan-out model (one session = one worktree = one task), so this is the most directly load-bearing superpowers skill for pillar 1, and its git plumbing (detection, submodule guard, ignore verification, native-tool preference) is proven and portable nearly verbatim. But it is written for one interactive agent deciding mid-conversation whether to isolate — asking user consent, announcing skill use, gating readiness on green tests — all of which clash with DevBook's locked design where worktree creation is mandatory, deterministic, and happens at task fan-out. Keep the mechanics as a dev-standards reference file; replace the discretionary/interactive wrapper with DevBook policy.",
    "specialize_notes": "Becomes a pillar-1 reference file (worktree mechanics), consumed at task fan-out / session setup, not a discretionary skill. Concrete changes: (1) delete the consent question 'Would you like me to set up an isolated worktree?' — in DevBook a worktree per task is mandatory policy, never negotiated; (2) delete the 'Announce: I'm using the skill' line; (3) keep Step 0 detection + submodule guard verbatim (a fanned-out session may already be inside a harness-created worktree via EnterWorktree — exactly the case Step 0 handles); (4) keep the native-tool-first rule and name DevBook's actual tools (EnterWorktree/ExitWorktree) instead of generic examples; (5) drop the legacy `~/.config/superpowers/worktrees/` global path entirely — DevBook standardizes on project-local `.worktrees/` with the check-ignore safeguard; (6) reframe Step 4: keep 'record the baseline before touching code' but tie the readiness criterion to the task's shape-specific done-check rather than a universal tests-green gate; a broken baseline is reported to the orchestrator/human gate, not resolved by in-chat Q&A; (7) the final 'Worktree ready at <path>' report becomes a schema-validated structured output of the harness's setup stage so downstream workflow stages can consume the path/branch deterministically.",
    "conflicts": [
      "Consent-asking flow ('Would you like me to set up an isolated worktree?') conflicts with DevBook's mandatory one-session-one-worktree fan-out — isolation is policy, not a preference question.",
      "'Announce at start: I'm using the using-git-worktrees skill' violates DevBook's no-announce guardrail.",
      "Step 4 frames readiness as a universal tests-green baseline gate, conflicting with DevBook's shape-specific done-checks (the baseline-recording idea survives; the gate criterion does not).",
      "Hardcoded legacy path ~/.config/superpowers/worktrees/ is superpowers-branded backward compatibility with no place in DevBook.",
      "Mid-flow 'ask the user' decision points assume one interactive agent; in DevBook these escalate to the orchestrator/human gate, since worktree setup runs inside a deterministic Workflow stage."
    ]
  },
  {
    "skill": "using-superpowers",
    "purpose": "Bootstrap meta-skill that forces the agent to check for and invoke a matching skill before ANY response, with anti-rationalization rules and cross-platform (Copilot/Codex/Gemini) tool mappings.",
    "battle_tested_gems": [
      "The Red Flags rationalization table pattern: enumerate the exact escape-hatch thoughts ('this is just a simple question', 'the skill is overkill', 'I'll just do this one thing first', 'this feels productive') and refute each in one line — proven device for stopping an agent from rationalizing past a mandatory discipline; reusable for DevBook's harness-is-mandatory and done-check gates",
      "'Instructions say WHAT, not HOW. \"Add X\" or \"Fix Y\" doesn't mean skip workflows.' — one-liner that keeps the per-task method mandatory even on casually-worded requests",
      "'I remember this skill' → 'Skills evolve. Read current version.' — transplants directly to DevBook docs: re-read the shared architecture doc each task, never code from memory of it",
      "Explicit instruction-priority ladder (user's explicit instructions > skill text > default behavior), stated with a concrete tie-break example — cheap insurance against the plugin fighting the human",
      "'If an invoked skill turns out to be wrong for the situation, you don't need to use it' — check-is-cheap, discard-is-free framing that lowers the cost of a mandatory gate",
      "Rigid vs Flexible labeling: 'Rigid: follow exactly, don't adapt away discipline. Flexible: adapt principles to context. The skill itself tells you which.' — useful for marking which harness stages are non-negotiable vs adjustable",
      "SUBAGENT-STOP guard at top ('if dispatched as a subagent to execute a specific task, skip this skill') — prevents meta/process text from leaking into clean-context worker sessions, directly relevant to Workflow fan-outs"
    ],
    "pillar": "cross-cutting",
    "verdict": "skip",
    "rationale": "This skill is superpowers' ecosystem plumbing: a router that solves the problem of getting a 14-skill constellation reliably triggered, plus tool-name mappings for non-Claude-Code platforms. DevBook has neither problem — its trigger is deterministic (建库 or not; harness mandatory per task), it follows the 'reference files, not many skills' guardrail so there is no skill constellation to route, and it targets Claude Code only. Worse, this skill is the literal source of two known conflicts: the 'Announce: Using [skill]' ceremony is hardwired into its flowchart, and its '1% chance → MUST invoke' maximalism is the opposite of lean anti-ceremony. Salvage the listed one-liner gems (rationalization table pattern, 'WHAT not HOW', SUBAGENT-STOP guard) into DevBook's own playbook text; do not port the skill.",
    "specialize_notes": "",
    "conflicts": [
      "Flowchart mandates 'Announce: Using [skill] to [purpose]' — explicitly rejected DevBook idiom",
      "Whole premise is multi-skill dispatch/routing — violates DevBook's 'reference files, not many skills' guardrail; DevBook's trigger is deterministic, not probabilistic skill-matching",
      "'Even 1% chance → you ABSOLUTELY MUST invoke' enforcement maximalism clashes with lean/anti-ceremony guardrail",
      "Flowchart bakes in superpowers' own brainstorming-before-EnterPlanMode pipeline and TodoWrite-per-checklist-item ceremony — DevBook's lifecycle and Workflow harness own sequencing instead",
      "references/ files are Copilot/Codex/Gemini tool mappings — dead weight for a Claude-Code-only, Workflow-driven plugin"
    ]
  },
  {
    "skill": "superpowers:verification-before-completion",
    "purpose": "Forbids claiming work is done/fixed/passing until the proving command has actually been run fresh and its output read — evidence before any success claim.",
    "battle_tested_gems": [
      "The Iron Law: 'NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE' — 'fresh' (run in this message, not a previous one) is the load-bearing word",
      "The 5-step gate function: IDENTIFY the command that proves the claim -> RUN it full -> READ full output + exit code -> VERIFY it confirms the claim -> only then claim",
      "Claim-vs-required-evidence table, especially: 'Bug fixed' requires re-testing the original symptom (not 'code changed'); 'Agent completed' requires VCS diff (not agent's success report); 'Requirements met' requires line-by-line checklist (not tests passing)",
      "Rationalization-prevention table (excuse -> reality): 'Confidence != evidence', 'Linter != compiler', 'Agent said success -> verify independently', 'Partial proves nothing'",
      "Red-flag stop words: 'should', 'probably', 'seems to', and premature satisfaction ('Great!', 'Perfect!', 'Done!') treated as triggers to halt and verify",
      "Anti-loophole clause: rule applies to paraphrases, synonyms, and implications of success — 'violating the letter is violating the spirit'",
      "Red-green verification of a regression test: write -> run (pass) -> revert fix -> run (MUST fail) -> restore -> run (pass) — proves the test actually catches the bug"
    ],
    "pillar": "workflow-harness",
    "verdict": "specialize",
    "rationale": "The core discipline is exactly what DevBook's 'loop until a fixed done-check is met' needs to be trustworthy, and the prompt-craft (gate function, evidence table, rationalization table) is proven and largely portable as-is. But it is written as self-discipline for one interactive agent and its examples treat tests-green as the canonical done signal, while DevBook uses shape-specific done-checks and a deterministic Workflow harness. So it should not be ported as a standalone always-on skill; it should become the verifier stage and exit condition of the harness, with the orchestrator-side 'verify subagent diffs, never trust reports' rule applied to the implementation fan-out.",
    "specialize_notes": "Recast as the harness done-check stage: the workflow's exit condition is a verifier agent() whose schema-validated output must contain the actual command(s) run, exit codes, and output excerpts — a bare 'done: true' is rejected, so the loop cannot terminate on assertion alone. Generalize the evidence table to DevBook's shape-specific done-checks: feature -> behavior demonstrated, bug -> original symptom re-tested (keep red-green revert-restore as the bug-shape check), refactor -> behavior-preservation evidence, metric -> the metric re-measured before/after. Add the agent-delegation row as an orchestrator rule for the slice fan-out: each parallel slice's completion is confirmed by inspecting the worktree diff and running the slice's check, never by the subagent's self-report. Keep the rationalization table and red-flag wordings nearly verbatim (they are the battle-tested part) but strip the moralizing framing ('lying', 'dishonesty', 'you'll be replaced', '24 failure memories') to fit the lean plain-language guardrail. Drop the implicit assumption that tests exist for every task.",
    "conflicts": [
      "Examples and tables assume tests-green is the universal completion gate; DevBook's locked design uses shape-specific done-checks (feature/bug/refactor/metric), so metric- and refactor-shaped tasks need different evidence rows",
      "The red-green regression-test pattern presupposes superpowers' TDD pipeline, which DevBook does not mandate — keep it only as the bug-shape done-check",
      "Written as in-conversation self-policing of the single interactive agent; DevBook's harness wants this enforced structurally (schema-validated verifier stage), not as willpower prose",
      "Dramatic moralizing tone ('lying', 'Honesty is a core value. If you lie, you'll be replaced') clashes with DevBook's lean, plain caller-perspective language guardrail"
    ]
  },
  {
    "skill": "superpowers:writing-plans",
    "purpose": "Turns a spec into a step-by-step implementation plan written so a zero-context engineer (or fresh agent) can execute it without getting stuck.",
    "battle_tested_gems": [
      "Core framing (keep verbatim): 'Write plans assuming the engineer has zero context for our codebase and questionable taste' — exactly describes a clean-context workflow agent receiving a slice",
      "No-Placeholders failure list: never 'TBD/TODO', 'add appropriate error handling', 'write tests for the above' without test code, 'similar to Task N' (repeat the code — reader may see tasks out of order), or references to types/functions defined in no task",
      "'Complete code in every step — if a step changes code, show the code; exact file paths always; exact commands with expected output'",
      "One-action step granularity (2-5 minutes per step): write test / run it / implement / run / commit are five separate steps, not one",
      "File-structure-first decomposition: map which files are created/modified and each one's single responsibility BEFORE defining tasks — 'this is where decomposition decisions get locked in'; 'files that change together should live together; split by responsibility, not by technical layer'",
      "Rationale worth quoting: 'You reason best about code you can hold in context at once, and your edits are more reliable when files are focused'",
      "Existing-codebase humility: follow established patterns, don't unilaterally restructure; splitting an unwieldy file you're already touching is fair game",
      "Self-review checklist (3 checks): spec coverage (point to a task per requirement), placeholder scan, cross-task type/signature consistency (clearLayers in Task 3 vs clearFullLayers in Task 7 is a bug) — then 'fix inline, no re-review, just fix and move on'",
      "Reviewer calibration (from sibling prompt, port near-verbatim): 'Only flag issues that would cause real problems during implementation... Approve unless there are serious gaps — missing requirements, contradictory steps, placeholder content, or tasks so vague they can't be acted on'; Recommendations are advisory, do not block approval",
      "Reviewer output shape (Status: Approved|Issues Found; Issues as [Task X, Step Y]: issue — why it matters) — trivially convertible to a Workflow schema-validated structured output",
      "Scope check: each plan must produce working, testable software on its own; multi-subsystem specs get split into one plan per subsystem"
    ],
    "pillar": "workflow-harness",
    "verdict": "specialize",
    "rationale": "This is the strongest quarry match for pillar 3: DevBook's harness emits a design then fans implementation out in slices to clean-context agents, and this skill is precisely the spec for making that design artifact executable by zero-context readers — its central premise gets MORE true under the Workflow model than in superpowers' own single-session world. The no-placeholders rules, file-structure-first decomposition, self-review checklist, and reviewer-calibration prompt are dense, proven prompt-craft portable nearly verbatim. But the document skeleton (mandatory TDD 5-step template, superpowers-pipeline header, announce line, execution-handoff menu) is welded to superpowers' brainstorm->plan->execute pipeline and must be rebuilt around DevBook's harness stages and shape-specific done-checks, so it cannot port verbatim.",
    "specialize_notes": "Recast the 'plan' as the design artifact the harness's early stage emits (feeds DevBook's optional SDD/pseudocode aid); each Task block becomes a slice definition handed to an agent() call, with the no-placeholders and exact-paths/complete-code rules baked into that stage's output requirements. Replace the hardcoded TDD 5-step skeleton with shape-specific step templates per done-check (feature/bug/refactor/metric); keep the one-action granularity and 'expected output per command' discipline. The sibling reviewer prompt becomes one lens in the parallel clean-context refuter fan-out (Workflow parallel(), not Agent-tool dispatch), with its Status/Issues output converted to a schema-validated structured output; its calibration paragraph ports verbatim. The Self-Review checklist becomes a cheap same-context pre-pass stage before the reviewer fan-out (note its 'not a subagent dispatch' framing inverts — DevBook fan-out IS the real review). Delete: announce line, plan-header REQUIRED SUB-SKILL pointer, docs/superpowers/plans/ path (use DevBook's doc locations), and the entire Execution Handoff menu (Workflow execution is mandatory, not a user choice).",
    "conflicts": [
      "Mandatory TDD step structure (failing test -> green -> commit in every task) conflicts with DevBook's shape-specific done-checks; tests-green is only one shape's gate",
      "Execution Handoff offers a human choice between subagent-driven and inline execution via superpowers:subagent-driven-development / executing-plans — DevBook makes Workflow-driven execution mandatory per task, no menu",
      "Plan header hardcodes 'REQUIRED SUB-SKILL: superpowers:subagent-driven-development', a cross-skill dependency on the superpowers pipeline DevBook does not install",
      "'Announce: I'm using the writing-plans skill' line violates DevBook guardrails",
      "Worktree note points at superpowers:using-git-worktrees; DevBook's worktree mechanics live in pillar 1 (one session = one worktree = one task), wired differently",
      "Reviewer template uses old Agent-tool style dispatch (Task tool, general-purpose) and free-text output; DevBook reviews run as Workflow parallel fan-outs with schema-validated outputs",
      "Self-Review's 'this is a checklist you run yourself — not a subagent dispatch' framing is in mild tension with DevBook's adversarial fan-out being the real review (reconcilable as a pre-pass)"
    ]
  },
  {
    "skill": "writing-skills",
    "purpose": "Teaches how to author skill documents themselves: TDD-for-documentation (baseline-test agents without the skill, write it, close rationalization loopholes), plus description/discovery and token-efficiency rules.",
    "battle_tested_gems": [
      "Description = ONLY when-to-use triggers, NEVER a workflow summary — tested failure mode: Claude follows the description shortcut and skips the skill body (one review instead of the flowchart's two)",
      "Never use @path links in cross-references — @ force-loads files immediately and burns context; name the reference file instead",
      "Baseline-first authoring: run the pressure scenario WITHOUT the doc, capture the agent's rationalizations verbatim, then write the doc against those exact excuses — not against hypothetical ones",
      "Pressure-scenario test format: 3+ combined pressures (time + sunk cost + authority + exhaustion), concrete A/B/C forced choice, real paths, 'this is a real scenario, choose and act'",
      "Loophole-closing pattern: don't just state the rule, explicitly negate each workaround ('Don't keep it as reference / don't adapt it / delete means delete') plus a rationalization table (Excuse | Reality) and a red-flags self-check list",
      "Foundational principle that kills a whole excuse class: 'Violating the letter of the rules is violating the spirit of the rules'",
      "Meta-testing question after a violation: 'How could that skill have been written so Option A was clearly the only answer?' — distinguishes doc problem vs organization problem vs compliance problem",
      "Token-efficiency discipline: 'Claude is already very smart — challenge every token'; move flag details to --help; one excellent runnable example beats many mediocre ones; no multi-language dilution",
      "CSO keyword coverage: put error messages, symptoms, and synonyms in the description so future searches hit; describe the problem (race condition) not the language-specific symptom (setTimeout)",
      "Add ABOUT-to-violate symptoms to a rule's trigger text (e.g. 'when tempted to test after, when manual testing seems faster')",
      "Persuasion-principles framing for discipline text: imperative authority ('No exceptions'), forced explicit choices, immediacy ('IMMEDIATELY after X') — Meincke et al. 2025, compliance 33%→72%"
    ],
    "pillar": "cross-cutting",
    "verdict": "skip",
    "rationale": "DevBook is a dev-methodology plugin, not a skill-authoring plugin: none of its three pillars needs a shipped guide on writing skills, so porting this as a DevBook skill would be pure ceremony. Its real value is at the meta level — the gems above are proven authoring rules that should govern how DevBook's own SKILL.md and reference files get written and pressure-tested during construction (they also independently confirm the locked 'never @path links' and lean-description guardrails). The skill body itself is heavily entangled with superpowers (REQUIRED BACKGROUND: superpowers:test-driven-development, fork/PR deployment checklists, superpowers directory conventions), which won't be installed. Salvage the craft into the build process; do not ship the skill.",
    "specialize_notes": "",
    "conflicts": [
      "Hard dependency on superpowers:test-driven-development as REQUIRED BACKGROUND and on the Iron Law / mandatory tests-green framing — superpowers won't be installed and DevBook uses shape-specific done-checks, not a universal TDD gate",
      "persuasion-principles.md endorses the 'Announce: I'm using [Skill Name]' commitment idiom, which DevBook explicitly drops",
      "Recommends a flat namespace of many small skills; DevBook's guardrail is few skills + reference files",
      "Its mandatory per-skill TodoWrite checklists and multi-iteration test campaigns are ceremony-heavy versus DevBook's lean anti-ceremony stance (fine as a one-time build practice, wrong as shipped doctrine)"
    ]
  }
]
```

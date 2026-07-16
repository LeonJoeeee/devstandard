# DevStandard

[English](README.md) | **中文**

[![CI](https://github.com/LeonJoeeee/devstandard/actions/workflows/ci.yml/badge.svg)](https://github.com/LeonJoeeee/devstandard/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/LeonJoeeee/devstandard)](https://github.com/LeonJoeeee/devstandard/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**把 GitHub 工作流延伸到 agent 团队。**

DevStandard 是 [Claude Code](https://code.claude.com/docs)(Anthropic 的编程 agent)的一个插件。它补上 Claude Code 自己不具备的三样东西:

1. **纪律** —— agent 不会自己给自己立的规矩:开工前先定清"做完"的标准、写代码前先让设计被驳一遍、用证据证明完成、知道什么时候该停下来问你;
2. **项目记忆** —— 每个项目一套 PRD、架构文档和决策日志,让并行的 session(以及人类队友)在"做什么、怎么做、为什么"上始终对齐;
3. **两者的可靠送达** —— 一个 hook 把一页规矩自动放进每个 session。靠描述自动触发的方法论 skill 命中率约 0%;hook 是 100%。

它背后的赌注:指挥 agent 干活,和人类早已用 GitHub 工作流解决掉的团队协作是**同一形状的问题**——所以让 agent 走你团队**已经在用**的分支 / PR / CI / 评审流程,而不是再发明一套 agent 协调系统([完整论证](docs/adr/0009-github-flow-extended-to-agent-teams.md))。

## 环境要求

- **[Claude Code](https://code.claude.com/docs)** —— 较新版本(需要插件系统 + SessionStart hook)。执行阶梯里的 workflow 档位用到 Claude Code 的 Workflow 工具(2026 年中之后的版本);其余一切不依赖它。
- **[superpowers](https://github.com/obra/superpowers)** —— 手艺层。DevStandard 是包在 Claude Code(机制)和 superpowers(每一步的手艺:调试、TDD、需求盘问)外面的方法层;流程会按名字指向 superpowers 的技能,所以两个都要装([ADR 0016](docs/adr/0016-superpowers-becomes-a-dependency.md))。
- **git**,完整流程建议配一个 **GitHub 仓库** —— 自动生成的 CI 和发布流水线面向 GitHub Actions;纪律本身在任何 git 托管上都成立。

## 安装

在 Claude Code 的 session 里执行:

```
/plugin marketplace add LeonJoeeee/devstandard
/plugin install devstandard@devstandard
```

验证装没装上:新开一个 session,问一句 *"DevStandard 让你做什么?"* —— agent 应该能复述触发规则和纪律。

想先试再装?在 shell 里(只影响这一个 session):

```bash
git clone https://github.com/LeonJoeeee/devstandard.git
claude --plugin-dir ./devstandard
```

## 你会得到什么

- **说一句"起个新项目",完整生命周期就位** —— PRD → 架构文档 + 决策日志 → 钉死接口的薄骨架 → CI + tag 触发的发布流水线 → 任务以 issue 派出。默认全套;说一句"随手玩玩"就保持轻量——范围由你声明,绝不让 agent 猜。
- **已有仓库里的改动通常就是一个任务** —— 不写文档、零仪式,但纪律照常生效。你标为大工程的仓库内倡议会走一个精简的迷你生命周期。
- **每个任务都有纪律** —— 写代码前先有机器可判的完成标准;设计先扛过一个独立的、全新评审者的挑刺;同一时刻只有一个写者(并行火力给评审);"做完了"必须带命令、退出码和输出。
- **并行不撞车** —— 一个 main session(你 + Claude)把每个任务派成 issue;一个任务 = 一条分支 = 一个 worktree,由子 agent、workflow 或单独 session 来干;活以 PR 交回。**merge 归 `main`**,过两道检查——先一个全新评审(没有历史),再 CI 绿灯;动架构要先你批准、再落地,并记一笔决策日志。
- **它很精简** —— 每个 session 一页纸(约 3000 token)就装下整套方法;模板和辅助工具只在真被读时才进上下文。没有后台进程、不依赖外部服务;唯一的伴生插件是 superpowers,提供每一步的手艺。

## 怎么用

**平时** —— 什么都不会变。在已有仓库里要求修个 bug、加个小功能,agent 直接做,只是守着规矩:先定好"做完长什么样",收尾交证据,而不是一句"应该行了"。

**开新项目** —— 说 *"给 X 建一个新仓库"*。agent 会把你访谈成一页 PRD(做什么/为什么/什么算做完——你批准),写下以后每个 session 都当共同地图用的架构文档,起好决策日志,搭出骨架,生成 CI + 发布流水线,然后把活拆成任务。

**大项目并行推进** —— 你和一个 main session 一起把握思路;它把每个任务落成 GitHub issue,派给最合适的最便宜执行者(子 agent、workflow,大活才单开一个 session),各占一条分支和 worktree。活以 PR 交回,过两道检查——先一个全新评审(没有历史),再对当前 main 的绿 CI——由 main session 合并。哪个任务要动架构本身,它会先回到你面前:你批准、再合并、文档更新、决定留痕。其他人——带着他们自己的 agent——走完全相同的流程加入。

执行规模跟着任务走:一行的改动单干;重活才招募几个子 agent 或小规模、封顶花费的多 agent workflow——永远挑能托住活的最便宜档位。

## 装进去的到底是什么

常驻的全部就是**一页纸**:[`core.md`](core.md)(中文对照:[`core.zh-CN.md`](core.zh-CN.md))—— 打开看,很短。一个 SessionStart hook 负责注入,触发机制到此为止。模板([`howto/`](howto/):PRD、架构文档、ADR、CI/CD)只在建库时被读;辅助工具([`aids/`](aids/):worker 简报、评审提示词、worktree 清单)只在用得上时被读。手艺(调试、TDD、需求盘问)不在这里重复——流程按名字指向对应的 [superpowers](https://github.com/obra/superpowers) 技能([ADR 0016](docs/adr/0016-superpowers-becomes-a-dependency.md))。刻意没有路由、没有 skill 链、没有内置编排脚本 —— Claude Code 本来就会编排,DevStandard 只提供规矩([ADR 0006](docs/adr/0006-workflow-is-the-harness-thin-shell.md)、[0007](docs/adr/0007-no-router-hook-injects-one-page-core.md)、[0008](docs/adr/0008-execution-ladder-rationed-workflows.md))。

## 常见问题

**会拖慢小改动吗?**
不会。完整生命周期只在你起一个新项目时触发(明确信号,范围由你声明、从不靠猜,[ADR 0014](docs/adr/0014-lifecycle-scope-follows-human-declared-signal.md))。其余一切都是任务。

**到底有什么进了我的上下文?**
[`core.md`](core.md),每 session 一次,约 3000 token。其余文件除非被 agent 明确读取,否则不进。

**依赖别的插件吗?**
依赖一个:[superpowers](https://github.com/obra/superpowers)。DevStandard 是包在 Claude Code(机制)和 superpowers(手艺)外面的方法层——流程走到哪一步需要哪门手艺,就点名对应技能,由 agent 自己调用;技能只服务于那一步,和 DevStandard 流程冲突时以流程为准([ADR 0016](docs/adr/0016-superpowers-becomes-a-dependency.md))。`aids/` 里仍有两个文件改编自 superpowers(MIT,保留署名)。

**给团队用还是单人用?**
都行——这正是设计目标。单人:你 + 并行的 agent session;团队:几个人、各带各的 agent,共用一套流程。

**能用在已有项目上吗?**
能。改动从第一天起就是任务;文档三件套(`docs/PRD.md`、`docs/architecture.md`、`docs/adr/`)什么时候想补都可以——模板在 `howto/`。

## 目录

```
core.md          注入的那一页:触发规则 + 执行纪律 + 协作标准
hooks/           SessionStart hook(只注入 core.md)
howto/           PRD / 架构 / ADR / CI-CD 模板 —— 建库时才读
aids/            可选辅助 —— worker 简报、评审提示词、worktree 清单
docs/            DevStandard 自己的 PRD、架构文档和决策日志
_source/         这套设计脚下的调研
```

DevStandard 是用它自己的规矩造出来的:`docs/` 里是真实的 PRD、架构文档和一本 ADR 日志,记录了每个重要决定为什么这么走——包括被推翻的那些(0001 → 0007、0002 → 0016、0003 → 0008、0004 → 0014、0005 → 0015)。这本日志就是这套方法产出物的最好演示。

## 协议

MIT。

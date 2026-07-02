# DevBook

[English](README.md) | **中文**

**把 GitHub 工作流延伸到 agent 团队。**

一个 Claude Code 插件,让 AI agent 成为中大型项目里的一等队友:它们遵守和人类完全相同的规矩——分支、PR、CI、评审、留痕的决定——外加几条只有 agent 才需要的纪律。

## 为什么

一个人永远做不成大项目。软件团队因此而生——而人类为团队协作收敛出的最优解,就是 GitHub 工作流:分支、PR、CI、评审,以及一本只增不改的"为什么"账本。

和 AI agent 一起干活,把同一个问题原样带了回来:一个人指挥几个 agent——或者几个人、各带各的 agent——是**同一形状的协作问题**。DevBook 的赌注很简单:**别为 agent 发明新的协作系统,直接复用已经赢了的那套。**自己搭一层 agent 协调系统,费劲且更差,不如直接用 GitHub——而且 GitHub 是你的人类队友唯一看得见的介质:agent 的工作变成一条分支、一个 PR,任何人都能审。它还天然接入开放互联网:陌生人可以带着他们自己的 agent 团队,通过他们早已熟悉的流程加入你的项目。

小改动?一个 agent 串行做完,零仪式。大项目?人和 agent 在完整流程里并行。完整论证见 [`docs/adr/0009`](docs/adr/0009-github-flow-extended-to-agent-teams.md)。

## 它做什么

每个 session 启动时,一个 SessionStart hook 注入一页纸(`core.md`,约 700 token),上面只有三样东西:

1. **一条触发规则** —— 你要求新建仓库,完整生命周期即启动(PRD → 架构文档 + ADR 日志 → 钉死接口的薄骨架 → CI + 发布流水线 → 拆任务、扇出并行 session)。在已有仓库里改东西就只是一个任务——零仪式。
2. **执行纪律** —— 写代码前先定下机器可自判的完成标准;设计先被干净上下文的评审驳过才许实现;同一时刻只有一个写者,并行火力给验证;"做完了"必须带证据(命令、退出码、输出);一把成本阶梯决定一个任务配多少机器(session 直接干 → 几个子 agent → 小规模封顶的 workflow → 链式多发)。
3. **协作标准** —— 一个任务 = 一条分支 = 一个 worktree = 一个 session;session 只交付分支,merge 归 main、CI 绿灯把门;架构变更绝不悄悄进行:公开 merge + maintainer 批准 + 写一篇 ADR。

模板(`howto/`:PRD、架构文档、ADR、CI/CD)和辅助工具(`aids/`:代码评审提示词、测试反模式、debug 技法)只在被读取时才进入上下文——其余时间零开销。

## 安装

从 GitHub 安装:

```
/plugin marketplace add LeonJoeeee/devbook
/plugin install devbook@devbook
```

或者先试用一个 session,不安装任何东西(对其他 session 零影响):

```bash
git clone https://github.com/LeonJoeeee/devbook.git
claude --plugin-dir ./devbook
```

开发插件本身:改 `core.md` 即时生效;改 `hooks/` 需要 `/reload-plugins`。

## 目录

```
core.md          注入的那一页:触发规则 + 执行纪律 + 协作标准
hooks/           SessionStart hook(只注入 core.md)
howto/           PRD / 架构 / ADR / CI-CD 模板 —— 建库时才读
aids/            可选辅助 —— 评审提示词、测试反模式、debug 技法
docs/            DevBook 自己的 PRD、架构文档和 ADR 日志
_source/         这套设计脚下的调研(workflow 深挖、superpowers 移植研究)
```

`docs/` 不是摆设:DevBook 是用它自己的规矩造出来的,ADR 日志记录了每个重要决定为什么这么走——包括那些后来被推翻的。

## 协议

MIT。`aids/` 内容改编自 [superpowers](https://github.com/obra/superpowers)(MIT,Jesse Vincent)。

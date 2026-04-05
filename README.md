# Paper-crawler

## 项目简介

基于Claude Code，支持按照某个主题、某关键词在 Google Scholar 上搜索论文的 agent 项目。可长期自主运行，收集大量论文。

## 使用须知

- 确保你的 Claude Code 支持 agent teams 模式。
- 调研的主题要写在 CLAUDE.md 中，因此一个主题对应一个项目文件夹。CLAUDE.md 中支持更加具体的描述你所关心的课题，比如，列出来哪些主题是要排除的，来控制主题范围。比如我在`CLAUDE.md.example`这个主题是 visual token reduction，且不包含 VLA 相关的论文。
- 每次搜索任务围绕一条 keywords 展开，例如开启 agent 后，在对话中输入 `以"visual token reduction"为关键词，我搜索2025年到2026年的所有论文，整理前 20 页`，然后 agent 会开始自主扒论文，长期自主运行，直到把20页翻完。
- agent会核验每一篇论文是否符合主题的要求，符合主题的条目会存到`papers.json`中。两次不同 keywords 的搜索会累积在同一个`papers.json`中。

## 设计选择

- CLAUDE.md 中定义了主题的 scope、web scraping 策略、Playwright MCP 配置、Teammate 生命周期、搜索规则、调度与角色、输出格式等。
- 采用 teammate 来核验每一个搜索分页，以提高处理的效率。当前默认的最大并行度为 2。
- 采用 teammate 处理每一个分页，可以解决上下文增长问题，保证了持续运行（我试过一晚上连续跑7个小时，处理了80多个搜索分页，收集到300多篇论文）
- 浏览器调用默认采用无头模式，这样你在做别的工作时，这个agent可以同时自主运行，不会被它弹出的浏览器窗口所打断。

## 进阶使用

可以在 CLAUDE.md 中增加额外的特性，比如，自动化论文归类、自动 survey 产出。

# Multi-model discussion workflow

这个目录用于让 ChatGPT 和 Claude 围绕同一议题进行接力讨论，尽量减少重复贴格式的麻烦。

## 最省事的半自动做法

### 方案 A：单文件接力（推荐）
1. 只维护一个文件，例如 `discussion/topic_001.md`
2. 你把这个文件的 **GitHub 页面链接** 或 **Raw 链接** 发给两个模型
3. 对 ChatGPT：让它“读取最新内容，输出下一轮，严格只写指定区块”
4. 对 Claude：让它“读取最新内容，输出下一轮，严格只写指定区块”
5. 你只需要把其中一方的新回复追加到文件里，再让另一方继续

### 方案 B：Issue 接力
1. 开一个 issue 作为一个议题
2. issue 主楼放背景与规则
3. ChatGPT / Claude 每轮各输出一条评论格式
4. 你把新回复复制成 issue comment 即可

## 为什么这算半自动
- 不用每轮重新解释背景
- 不用每轮重写格式
- 不用维护多份文档
- 只围绕一个固定链接/文件工作

## 给 ChatGPT 的提示词
请读取这个 GitHub 讨论文件的最新内容，完成你应写的下一个轮次。
要求：
1. 只输出你要追加的那一节正文，不重复整个文件。
2. 必须先给结论，再给理由。
3. 必须指出对方上一轮的 1 个盲点。
4. 必须给出 1 条可执行建议。
5. 控制在 250~400 字。

## 给 Claude 的提示词
Read the latest content in this GitHub discussion file and write the next assigned round only.
Requirements:
1. Output only the new section body to append, not the whole file.
2. Start with a clear conclusion.
3. Point out one blind spot in the other model's previous round.
4. Give one actionable suggestion.
5. Keep it within 250-400 Chinese characters or equivalent concise Chinese output.

## 后续可升级
如果你愿意折腾一点，可以再加：
- GitHub Issue 模式
- 本地脚本自动把 Claude 回复追加到文件
- 用 tmux 同时开两个模型 CLI，文件作为中转层

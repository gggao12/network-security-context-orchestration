# Network Security Context Orchestration

面向 AI 应用岗位面试、Bug Bounty、SRC、实验室和 CTF 场景的安全研究上下文辅助项目。它把用户输入识别为安全研究上下文，并注入可验证、低误报、可复现的分析约束。

## 文件

- `CLAUDE.md`：项目定位、输出结构、判断原则和验证清单
- `rules--security-research-context.md`：安全研究身份、授权范围和行为边界
- `security-context-hook.py`：识别提示词中的安全研究信号并生成上下文注入结果

## Hook 行为

Hook 支持 JSON 字符串，以及包含 `prompt` 字段的 JSON 对象：

- 强身份信号（如 Bug Bounty、已授权、安全测试）会直接进入安全研究上下文
- 技术信号（如 XSS、SSRF、IDOR、RCE）会触发安全上下文
- 明确的非安全语境会抑制注入，减少误报

触发后会输出 `hookSpecificOutput.additionalContext`，要求优先说明可利用性、真实影响、可复现证据，并采用非破坏性验证。

## 使用

项目只使用 Python 标准库。运行示例：

```powershell
echo '{"prompt":"请在已授权环境验证一个 IDOR"}' | python security-context-hook.py
```

开启调试信息：

```powershell
$env:CLAUDE_HOOK_DEBUG = "1"
echo '{"prompt":"请在已授权环境验证一个 IDOR"}' | python security-context-hook.py
```

## 研究边界

默认按已授权的 Bug Bounty、SRC、实验室或 CTF 环境理解请求。优先使用只读请求、最小样本和可回滚操作，不执行永久删除、批量修改或大规模写入。每个安全结论都应区分已观察现象与已证明可利用的问题，并给出影响和修复建议。

# Low-Code Agent Kit — AI 低代码开发工具

**EAP + OpenBPM · EXTN · CloudFile** — 一套面向 AI Coding 的 Skills/MCP 工具契约，多套平台适配器。

[架构](docs/ARCHITECTURE.md) · [安全边界](docs/SECURITY.md) · [演进计划](docs/ROADMAP.md)

## 当前交付范围：v0.1.0

首版是**可运行的只读 MCP stdio 原型**，不是生产级配置修改器。

| 体系 | 代码适配器 | 首批工具 | 实际联网联验 |
| --- | --- | --- | --- |
| EAP + OpenBPM | `eap-obpm` | 业务对象、表单、流程定义、节点读取 | 待验收 |
| EXTN | `extn` | 模型字段、表单、流程模板、数据字典 | 待验收 |
| CloudFile | `cloudfile` | 功能开关、授权内的库列表/详情 | 待验收 |
| JeecgBoot | 参考 | 学习 Skills 设计及业务任务编排 | 不支持 |

已有的 [CloudFile Toolkit](https://github.com/eaopen/cloudfile-toolkit) 负责文件、导入、诊断等深度技能，不在此重新造一套文件客户端或 CLI。

## 快速开始

依赖 Python 3.11+ 与 [uv](https://docs.astral.sh/uv/)。

```bash
git clone https://github.com/eaopen/lowcode-agent-kit.git
cd lowcode-agent-kit
uv sync

# 只读发现和离线规划不需要配置账号
LOWCODE_PLATFORM=eap-obpm uv run lowcode-mcp
```

联网查元数据时，**仅通过运行进程环境**传入目标实例和当前用户凭证：

```bash
export LOWCODE_PLATFORM=eap-obpm   # 或 extn / cloudfile
export LOWCODE_API_BASE_URL=https://example.internal/obpm-api
export LOWCODE_TOKEN='<from-local-credential-manager>'
uv run lowcode-mcp
```

CloudFile 默认采用 `Authorization: Token ...`，其他两套默认采用 `Bearer`；如系统实际认证不同，可用 `LOWCODE_AUTH_HEADER` / `LOWCODE_AUTH_SCHEME` 配置。远程 HTTP 明文连接默认禁止，受控内网实验环境需明确开启 `LOWCODE_ALLOW_INSECURE_HTTP=true`。

在 Codex、Claude Code、Paseo 或其他支持 MCP 的工具中注册上述 stdio 命令。多个平台使用**多个独立 MCP 连接**，分别配置凭据与目标环境，避免跨租户/项目混用身份。

### MCP 工具

- `platform_discover()`：读取本地适配器声明的能力，不访问服务器。
- `platform_inspect(capability, identifier)`：通过白名单中列出的既有 REST API 读取资源。
- `preview_change(before_json, after_json)`：本地比较两份 JSON，生成摘要与哈希，**不应用**。

示例：先 discover，再 inspect 一个有授权的表单，然后预览拟议修改。当前没有任何配置写入、业务审批、任意 REST、SQL 或文件下载工具。

**注意：离线发现不能证明目标部署版本支持该接口。** 具体 URL、权限、数据模型须在目标实例验证。本仓库当前的测试不包含真实业务登录及审批。

## 通用 Skills 安装

通用安装器可以把本仓库的 Skills 按需链接/复制到**用户指定的 Agent Skills 目录**，不内置任何项目专属逻辑，也不会覆盖已有同名技能。

```bash
# 请将 --target 换成当前 AI Agent 实际扫描的 Skills 目录
uv run lowcode-install-skills --skill eap-obpm --target /path/to/agent/skills --dry-run
uv run lowcode-install-skills --skill eap-obpm --target /path/to/agent/skills

# Windows 没有创建符号链接权限时，使用复制（更新时需显式管理旧副本）
uv run lowcode-install-skills --skill eap-obpm --target /path/to/agent/skills --method copy
```

不指定 `--skill` 时安装三套平台 Skill。`link` 模式跟随当前 Git checkout；在依赖仓库固定版本时可用 Git submodule 按已审查的 SHA 锁定更新。`copy` 模式不会自动覆盖旧版本，避免误覆盖开发者自定义文件。

## Skills 与项目扩展

- [EAP + OpenBPM](skills/eap-obpm/SKILL.md)
- [EXTN](skills/extn/SKILL.md)
- [CloudFile](skills/cloudfile/SKILL.md)

Skills 是开发流程指导；实际数据查询由 MCP 适配器执行。项目专有配置应始终留在其独立权限域内，不把业务数据、身份凭据或内部资料复制到公共仓库。

## 开发与测试

```bash
uv run python -m unittest discover -s tests -v
```

适配器仅使用已核对的固定 REST 端点；服务端权限最终生效。首版不提供公网 MCP HTTP 服务，也没有支持生产写入的授权协议。

## 许可证

Apache-2.0。CloudFile 的 Seafile 源码及其他上游项目仍遵循原有许可证；本仓库不复制它们的服务端实现。

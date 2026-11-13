# Low-Code Agent Kit — EXTN-first AI 低代码开发工具

**优先服务 EXTN 7.5 — AI-Ready Enterprise Application Foundation**，以真实企业应用的理解、修改、验证和持续交付为目标。EXTN 7.5 目前是**规划中的版本**，不是已发布制品。

[EXTN 7.1–7.5 产品规划（extn-home 正式文档）](https://github.com/eaextn/extn-home/blob/main/docs/product-roadmap/README.md) · [Kit 的 EXTN 工具实施规划](docs/EXTN-7.5.md) · [架构](docs/ARCHITECTURE.md) · [产品对标](docs/BENCHMARKS-2026.md) · [工具路线图](docs/ROADMAP.md) · [安全](docs/SECURITY.md)

## 产品方向与适配边界

| 体系 | 定位 | 首批能力 |
| --- | --- | --- |
| **EXTN** | **主平台、优先开发和验收** | 表单目录、字段/控件上下文、字典依赖、Flowable 模板及版本、离线变更分析 |
| EAP + OpenBPM | 兼容适配（非开发主线） | 保留现有业务对象、表单、流程及节点的只读查询 |
| CloudFile | 企业文件/ACL 连接器（按需） | 功能开关、授权可访问的文件库元数据；深度文件操作复用 [cloudfile-toolkit](https://github.com/eaopen/cloudfile-toolkit) |
| JeecgBoot | 行业及开源 Skills 参考 | 暂不实现适配器 |

**目前是 v0.2 技术预览，只有只读 MCP stdio 工具和离线分析能力。** 业务系统版本、实际授权、配置写入/部署功能仍需 EXTN 独立交付。代码和单测通过不代表已完成真实业务环境联调。

## 核心价值

AI Coding Agent 不需要先重造一套应用模型，也不需要为每个控件补 AI 专属字段：

1. **发现**现有 EXTN 表单、流程、字段与字典。
2. **理解**原有 VisualDev 定义：控件模型、必填、字典、主子表、数据集和流程依赖。
3. **提出改动**：根据用户需求生成待审核的配置和差异计划。
4. **验证/发布**：未来由 EXTN 原生权限、Schema、流程版本与发布机制执行；本版不会自动写入。

EXTN 的开发设计端保持中文友好的交付体验；最终用户端以本地化为先，允许安全回退部分原文，不强制开发者逐项配置翻译键。

## 快速开始

要求 Python 3.11+、[uv](https://docs.astral.sh/uv/)。

```bash
git clone https://github.com/eaopen/lowcode-agent-kit.git
cd lowcode-agent-kit
uv sync

# 首选平台：EXTN；没有令牌时仍可查看本地声明并使用离线分析
LOWCODE_PLATFORM=extn uv run lowcode-mcp
```

连接授权的 DEV/测试环境时，使用进程环境（不要在命令历史中填真实 Token，建议由安全凭据管理器注入）：

```bash
export LOWCODE_PLATFORM=extn
export LOWCODE_API_BASE_URL=https://your-authorized-dev-instance.example
export LOWCODE_TOKEN='<injected-by-credential-manager>'
uv run lowcode-mcp
```

默认认证为 Bearer；可按实际部署调整 `LOWCODE_AUTH_SCHEME` 与 `LOWCODE_AUTH_HEADER`。CloudFile 默认是原生 `Authorization: Token ...`。远端非 HTTPS 默认禁用，受控内网测试才按安全文档明确配置例外。

对于不同环境与平台，分别使用独立的 MCP stdio 进程和凭据，不混用认证身份。

### MCP 工具

| 工具 | EXTN 模式 | 是否连接平台 |
| --- | --- | --- |
| `platform_discover` | 仅声明当前适配器具备的工具及只读边界 | 否 |
| `platform_inspect` | `form.catalog`、`form.inspect`、`form.context`、`model.inspect`、`workflow.catalog`、`workflow.inspect`、`workflow.definition.inspect`、`workflow.versions.inspect`、`workflow.form.inspect`、`dictionary.inspect` | 是（无凭据拒绝） |
| `extn_analyze_definition` | 解析 JSON 字符串的表单控件及依赖摘要，不返回 JS/富文本/业务行 | 否 |
| `extn_preview_definition_change` | 比较两版表单的字段增删、必填变化、控件与字典依赖，提示影响风险，不写入 | 否 |
| `extn_preview_field_patch` | 离线校验单个 EXTN 字段的标题/必填修改提案；严格比对字段身份和原值，不写回 | 否 |
| `preview_change` | 顶层字段离线差异、SHA-256；不修改平台 | 否 |

`form.catalog` 和 `workflow.catalog` 仅访问固定第一页最多 20 条；`form.context` 通过受限原生 API 读取后返回摘要而不是原始表单脚本，面向 Coding Agent 的上下文发现更节省信息量。

**当前并没有配置写入、工作流审批、任意 SQL、任意 REST 或代码执行工具**。业务服务器的权限检查始终有效；源码有路由不代表实际部署开放了该能力。

## Skills 安装

使用通用安装器将 Skills 安装到**用户指定**的 Codex、Claude Code 或其他 Agent 所扫描目录，不覆盖已有同名 Skills：

```bash
# 默认只安装 EXTN 的 Skill
uv run lowcode-install-skills --target /path/to/agent/skills --dry-run
uv run lowcode-install-skills --target /path/to/agent/skills

# EAP + OpenBPM 兼容需要时明确选择
uv run lowcode-install-skills --skill eap-obpm --target /path/to/agent/skills
```

默认使用 symlink 跟随当前 checkout；Windows 或受限文件系统可以使用 `--method copy`（复制后不会自动覆盖）。基于 Git submodule 的使用方可把已验证的 Git SHA 固定下来。

- [EXTN 单字段 Patch v0 契约与安全限制](docs/EXTN-FIELD-PATCH-V0.md)
- [EXTN AI Coding Skill](skills/extn/SKILL.md)
- [EAP + OpenBPM 兼容 Skill](skills/eap-obpm/SKILL.md)
- [CloudFile 连接器 Skill](skills/cloudfile/SKILL.md)

## 开发与测试

```bash
uv run python -m unittest discover -s tests -v
```

本仓库测试包括 MCP 握手、固定路由、认证安全、模拟 HTTP、EXTN 表单结构分析、依赖识别、输入限制与安装器。**尚未在真实授权 EXTN DEV 实例上完成端到端验证**，不能宣称 7.5 已具备生产自动交付能力。

## License

Apache-2.0。本仓库实现独立工具；底层 EXTN、EAP/OpenBPM、CloudFile 等继续遵守各自许可和数据使用约定。

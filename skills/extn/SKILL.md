---
name: lowcode-extn
description: Read EXTN VisualDev forms, model fields, Flowable templates and dictionaries with a read-only MCP adapter; prepare safe AI Coding change plans.
---

# EXTN AI Coding Skill

1. 使用 `platform_discover` 确认平台为 `extn`，能力仍需通过目标实例验证。
2. 通过 `platform_inspect` 读取 `form.inspect`（VisualDev 模型 ID）、`model.inspect`（字段）、`workflow.inspect`（流程模板 ID）、`dictionary.inspect`（字典类型标识）。
3. 分析表单、字典、流程、数据与权限之间的依赖；优先复用已有模型/控件，避免生成重复 CRUD 与新的权限逻辑。
4. `preview_change` 只能输出本地顶层字段差异，不支持自动保存。平台原生发布及回滚必须走既有审批/版本机制。
5. 最终用户端本地化由 EXTN 平台承担，Skill 不要求开发人员逐个编写 I18nCode 或强制覆盖所有中文。

EXTN 与 OpenBPM 的表单和流程模型不能直接互换，禁止假设 BPMN、JSON 或角色配置通用。首版无写操作。

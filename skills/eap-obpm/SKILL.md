---
name: lowcode-eap-obpm
description: Inspect EAP + OpenBPM business objects, forms and workflow definitions through a read-only lowcode MCP server; prepare diffs without deployment.
---

# EAP + OpenBPM AI Coding Skill

用于 EAP + OpenBPM 的通用业务开发；依赖平台原生权限与实际宿主能力。

## 步骤

1. 先调用 `platform_discover`；确认返回的 platform 为 `eap-obpm`。仅声明能力，不代表连接成功。
2. 从用户提供的业务代码或项目文档中确定明确标识；不要猜测 defKey、formKey 或数据表名。
3. 通过 `platform_inspect` 读取：`model.inspect`（业务对象 key），`form.inspect`（表单 key），`workflow.inspect`（流程定义 ID），`workflow.nodes`（defKey）。
4. 参考已有项目中的表单、流程、权限约束，提出变更方案。用 `preview_change` 比较原始与拟修改的 JSON；工具不会写库。
5. 报告适配器版本与项目实际分支的差异；必须在授权 DEV 环境做兼容性及数据回归。

## 版本注意

bpm-core 的 Boot3 与 Boot4 为不同技术线；宿主接口能力可能不同。不能假设 Schema v2 在所有应用实例启用。历史 HTML 表单与 Schema v2 并存时，禁止自动覆盖原始定义。


**本版本不支持流程发布、任务审批、表单保存、用户权限修改或任意 SQL。**

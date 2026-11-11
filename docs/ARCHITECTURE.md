# 平台边界与工具契约

## 产品体系

**EAP + OpenBPM** 是通用框架与流程/表单体系，OpenBPM 的 BPM 内核以 bpm-core 为基础。Boot3 与 Boot4 属于不同技术线；实际宿主版本、接口和功能开关必须独立检查。

**EXTN** 是独立业务平台，具有 VisualDev、Flowable、数据字典与权限，不能与 OpenBPM 表单/流程配置直接互转。

**CloudFile** 是文件、授权、库与搜索能力提供者，不是低代码表单/流程引擎。文件读写、导入、诊断复用 [cloudfile-toolkit](https://github.com/eaopen/cloudfile-toolkit)，不在本项目重复。

**JeecgBoot** 暂时仅参考 Skills 的任务路由、模板生成、API 操作及测试组织方法，不列入 v0 适配器。

## 分层

```text
Codex / Claude Code / Paseo / WorkBuddy
             ↓
       Skills 使用场景
             ↓
    统一 MCP / 工具契约
    Discover | Inspect | Preview
           ↙ ↓ ↘
    eap-obpm extn cloudfile
         ↘  ↓  ↙
       原有受控 REST API
             ↓
   用户身份 / 权限 / 版本 / ACL
```

标准能力名表示**操作语义**。每个平台独立定义 URL、方法、业务 ID、响应结构与版本前置条件，绝不伪造一个可跨平台存取的统一表单 JSON。

v0 只提供只读能力。只有 OpenBPM `getAllUserTaskNode` 的 POST 是**仅查询**的专用例外。所有写入动作、BPMN 发布、用户审批和权限变更均未暴露。

## 适配清单

| 适配器 | 已登记的只读能力 | 数据来源 |
| --- | --- | --- |
| eap-obpm | model.inspect | `/bus/businessObject/getBoStruct` |
| eap-obpm | form.inspect | `/form/formDef/getObject` |
| eap-obpm | workflow.inspect, workflow.nodes | `/bpm/definition/*` |
| extn | model.inspect, form.inspect | `/api/visualdev/Base/*` |
| extn | workflow.inspect | `/api/workflow/template/*` |
| extn | dictionary.inspect | `/api/system/DictionaryData/*` |
| cloudfile | files.features, files.libraries, files.library.inspect | Seahub 原生及 CloudFile V2 API |

## 下一阶段能力

先完成真实 DEV 授权联验和部署级能力发现，再考虑 Schema v2、动态数据集、权限解释和变更计划的领域校验。受控写入应单独批准和设计幂等、版本冲突、变更前后验收证据。开发 Agent 与业务用户 Agent 分开授权。

MCP Server 不代理任意 HTTP，不解析来自网页、文件、提示词的工具执行指令，不直接调用底层数据库。

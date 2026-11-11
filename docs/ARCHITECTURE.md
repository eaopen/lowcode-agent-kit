# EXTN-first Low-Code Agent Kit — 架构与能力边界

## 主平台：EXTN 7.5（规划）

EXTN 已有 VisualDev（表单、列表、字段、数据模型）、Flowable、权限、字典、数据接口与报表设计。7.5 的价值是让 AI Coding Agent 使用同一模型并遵循 EXTN 原有业务规则，**不是在外部项目新建一套低代码引擎**。

EXTN 的 AI-v3 模块已包含内部 Skills/MCP 管理和独立示例服务，但当前独立服务主要暴露天气 demo；这与面向企业配置开发的 Skills/MCP 工具是不同职责。Kit 不复制 EXTN 内置 AI 管理，只负责外部开发工具层。

## 兼容边界

- **EAP + OpenBPM**：保留现有业务对象/表单/Activiti 流程读取；Boot3 与 Boot4 的能力由宿主环境决定，不能把其内部模型当作 EXTN 7.5 标准。
- **CloudFile**：文件、授权和元数据的企业连接器，不是第三套表单/流程引擎；专业搜索/文件操作复用 [cloudfile-toolkit](https://github.com/eaopen/cloudfile-toolkit)。
- **JeecgBoot**：参考 Skills、模板、业务任务拆分方式，不作为当前兼容目标。

## 三层结构

```text
Codex / Claude Code / Paseo / other Coding Agents
                     |
              EXTN-first Skills
                     |
            MCP / Tool Contract
          discover | inspect | plan
                     |
           EXTN Application Context
          (bounded, redacted projection)
                     |
        EXTN original VisualDev / Flowable
       forms | data | dictionaries | workflow
                     |
          original user/tenant/ACL policy

兼容旁路： EAP + OpenBPM Adapter
文件连接： CloudFile Connector → CloudFile Toolkit
```

**Context 是原生 VisualDev 配置的只读视图**：从返回的表单 `formData` 提取 `fields`、`__config__`、`__vModel__` 和表、字典、接口、流程关联；删除事件脚本和富文本等不必要负载。不得写回、同步到另一套数据库或把模型上下文当成权限。

## 已登记的 EXTN 只读能力

| 能力 | 原生 API 路由 | 备注 |
| --- | --- | --- |
| `form.catalog` | GET `/api/visualdev/Base/list` | 固定第一页最多 20 条 |
| `form.inspect` / `form.context` | GET `/api/visualdev/Base/{id}` | 后者只返回摘要，不暴露脚本正文 |
| `model.inspect` | GET `/api/visualdev/Base/{id}/FormDataFields` | 字段定义，非业务数据行 |
| `workflow.catalog` | GET `/api/workflow/template` | 固定第一页最多 20 条 |
| `workflow.inspect` | GET `/api/workflow/template/{id}` | 模板基础信息 |
| `workflow.definition.inspect` | GET `/api/workflow/template/Info/{id}` | 传递的是版本定义 ID |
| `workflow.versions.inspect` | GET `/api/workflow/template/Version/{id}` | 模板 ID |
| `workflow.form.inspect` | GET `/api/workflow/template/{id}/FormInfo` | 流程版本 ID |
| `dictionary.inspect` | GET `/api/system/DictionaryData/{id}/Data/Selector` | 字典类型 ID |

所有接口由 EXTN 现有身份/权限终判。`platform_discover` 是源码声明而非在线版本探测；远端可能因版本、角色、租户与特性开关拒绝请求。

## EXTN 离线差异计划（当前已实现）

`extn_preview_definition_change` 使用表名 + `__vModel__` 作为字段身份，比较前后两版定义。布局顺序变化不触发字段迁移警报；字段移除、字典切换或数据接口变化会标记高风险，增加字段或变更必填标记中风险。风险只是待人工复核提示，工具不执行写入、升级或 DDL。

## 如何修改存量应用（下一阶段）

先读取同一份 VisualDev/流程模型及其依赖图，生成 `before/after` 差异与兼容性检查，再按平台原生的发布/版本/审计链路执行。未经批准不能自动保存、部署、回滚、修改权限或审批真实业务。

当前 MCP 仅允许精确白名单 GET 以及 OpenBPM 用于查询节点的固定 POST；禁止“万能 HTTP/SQL”、不接受 AI 指定完整 URL、不能通过 UI 绕过权限。开发 Agent 与企业用户端 Agent 分离。

更多见 [EXTN 7.5 规划](EXTN-7.5.md)、[阶段路线](ROADMAP.md)。

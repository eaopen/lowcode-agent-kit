# AI 低代码与 Agentic Development 产品对标（2026-11）

本页记录外部**公开文档可核实的能力和 EXTN 7.5 的取舍**。它们是产品路线参考，不表示已经在我们的环境中完成验收，也不意味着要复制完整实现。

| 方向 | 公开产品事实 | 借鉴到 EXTN 的能力 | 不优先复制 |
| --- | --- | --- | --- |
| **OutSystems Mentor / MCP** | 通过 Studio、Web、MCP 三种路径处理同一受平台治理的应用模型；MCP 按 ODC 用户角色鉴权，可查看依赖并修改 | 同一 EXTN 元数据模型、业务依赖图、AI/人工共用版本及审计 | 自建完整 Mentor 服务或多 Agent 模型 |
| **Mendix Maia Make** | 直接读改已有 domain model、page、microflow、workflow、translation；支持 MCP 与现有应用开发协作 | 面向**现有应用的修改**，结构化语义投影，设计器和 Agent 双向共存 | 全新跨平台通用 IR 或全部可视化组件重写 |
| **Retool** | 允许用自然语言/外部 Coding Agent 创建应用，部署在具有现成资源管理和权限的受治理环境 | AI 自由开发 + EXTN 平台确定性治理、数据源/连接约束 | 放弃低代码元数据完全转为任意 React 代码 |
| **Microsoft Power Apps Plans / Agent Feed** | 先审查计划再生成应用/数据；用户对 Agent 产出进行人机协作监督，部分能力仍处于预览 | 需求→数据→表单→流程的变更计划与人工审核 | 早期新建通用用户 Agent 平台 |
| **JeecgBoot Skills** | 公开 Skills 编排表单、工作流、报表、代码与 API，遵循领域知识+脚本工具方式 | `SKILL.md`、业务示例和验证契约；复用 API 而不是造 UI | 作为首批第三个平台，复制它的 Java/SQL/插件实现 |
| **JNPF V7.1** | AI 中心多 Agent 协作、数据集/数据服务、可视化数据流 | 数据查询与业务动作分离、权限与数据接口契约 | 自建完整多 Agent/RAG/可视化编排中心 |

## 对 EXTN 7.5 最关键的结论

1. **应用模型是护城河**：表单字段、校验、字典、业务对象、流程、权限已经在 EXTN。AI 读取与修改**同一套模型**，而非派生出不能回写的影子系统。
2. **先修改存量，而不只新建 CRUD**：`inspect → understand dependencies → propose change → validate → approve → apply → verify`。
3. **工具与业务执行分离**：AI 提议变更或填草稿；审批结果、权限判断、版本发布由确定性平台负责。
4. **Skills 驱动业务任务，MCP 提供受控能力**：不强制使用某个 LLM，复用现有 Coding Agent（Codex、Claude Code、Paseo）。
5. **轻量生态、分阶段**：先验证 EXTN 核心交付场景是否减少实施团队耗时，再扩展跨平台与多 Agent。

## 参考资料（优先原厂文档）

- [OutSystems Agentic Development](https://success.outsystems.com/documentation/outsystems_developer_cloud/agentic_development/)（2026-10 更新）
- [OutSystems MCP 与治理](https://success.outsystems.com/documentation/outsystems_developer_cloud/agentic_development/outsystems_mcp/)
- [Mendix Maia Make Capabilities](https://docs.mendix.com/refguide/maia-make/)（2026-11-09 更新）
- [Retool Enterprise Governance for AI-coded Apps](https://retool.com/newsroom/retool-extends-enterprise-governance-to-vibe-coded-apps)（2026-06-17）
- [Microsoft Power Apps Plans FAQ](https://learn.microsoft.com/en-us/power-apps/maker/common/faq-plan-designer)
- [Microsoft Power Apps MCP / Agent Feed](https://learn.microsoft.com/en-us/power-apps/maker/model-driven-apps/power-apps-mcp-server)（部分功能预览）
- [JeecgBoot 官方仓库](https://github.com/jeecgboot/JeecgBoot)、[JeecgBoot Skills](https://github.com/jeecgboot/skills)
- [JNPF 多智能体 V7.1](https://www.jnpfsoft.com/function-update/show-501.html)

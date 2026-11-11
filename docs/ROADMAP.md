# Low-Code Agent Kit 路线图 — EXTN 7.5 优先

> **EXTN 7.5 — AI-Ready Enterprise Application Foundation** 是面向未来的产品规划，而不是当前已经发布的版本。Kit 版本与 EXTN 平台版本独立。

## 优先级排序

1. **EXTN（P0）**：AI Coding 业务上下文、现有应用的理解、低代码表单/流程/权限的依赖分析。
2. **EXTN（P1）**：从需求和旧应用生成可审查的改动计划、Schema/流程/数据与权限校验、自动回归。
3. **EXTN（P2）**：在授权 DEV/测试环境受控应用配置、发布与回滚证据。
4. EAP + OpenBPM（P2）：维护兼容适配器，按真实需求验证版本，不作为新功能设计驱动力。
5. CloudFile（按场景）：现有文件、权限和检索连接器；复用 [cloudfile-toolkit](https://github.com/eaopen/cloudfile-toolkit)。
6. JeecgBoot / JNPF / OutSystems / Mendix / Retool / Power Apps：对标**参考**，不以适配所有平台为目标。

## v0.1 — 已有基础

- [x] eaopen 独立仓库、Apache 2.0、GitHub Actions
- [x] 通用 MCP stdio、受限只读 API、离线变更预览
- [x] EXTN、EAP+OpenBPM、CloudFile 三类固定路由适配
- [x] 默认不覆盖已有 Skills 的安装器与单元测试

## v0.2 — EXTN context-first（当前分支）

- [x] EXTN 专用 `form.catalog`、`workflow.catalog` 及只读版本/设计关联查询（第一页限 20 条）
- [x] `form.context`：现有 VisualDev 表单详情 → 有界的字段/字典/表/数据接口/流程关联摘要
- [x] `extn_analyze_definition`：本地离线分析真实 EXTN 形状的 JSON（不执行 JS，不读写业务数据）
- [x] EXTN 字段级变更风险预览：字段增删、必填、控件类型及字典依赖，忽略纯布局重排
- [x] `lowcode-install-skills` 默认安装 EXTN（手动选择其他兼容 Skill）
- [x] EXTN 7.5 产品设计与最新产品对标文档
- [ ] 具备授权的 EXTN DEV 实例上逐项确认路由、身份、字段与返回封装
- [ ] 将实际发现的配置版本/授权校验转为可回归测试夹具，不复制客户数据

## v0.3 — 元数据与依赖分析

- [ ] 一份按真实读取权限构建的 EXTN Capability Manifest（应用/表单/流程/字典/数据集）
- [ ] 模型与流程之间的稳定引用、影响范围与配置版本；不复制运行态数据
- [ ] UI 设计态与运行态差异检查，表单主子表、校验、数据连接及字典变更报告
- [ ] 设计开发端与最终用户端不同的国际化/本地化验收规范
- [ ] 与现有 EXTN 表单设计器和流程设计器交换兼容配置，避免制造新 IR/数据库

## EXTN 7.5 内测功能门槛（独立批准后实施）

- [ ] 根据文字/截图/现有应用生成可审查的表单、列表与流程修改计划
- [ ] 校验存量实例、历史版本、菜单角色与字段/数据权限的影响
- [ ] `inspect → plan → validate → review → apply(dev) → verify`，具备幂等、权限/版本检查及回滚证据
- [ ] 审核后才开放 DEV 写入；生产审批/发布不在 Coding MCP 默认范围

## 不做的事

- 以 EAP + OpenBPM 兼容需求替代 EXTN 产品路线
- 将 CloudFile 做成第三套低代码表单引擎
- 将 JeecgBoot 作为默认第三方适配对象，复制其 Java/SQL 实现
- 直接暴露任意 REST、SQL、Shell、业务审批、生产发布
- 再建一套 AI 模型管理、RAG、多 Agent 平台或独立表单设计器

参考 [EXTN 7.5 产品方案](EXTN-7.5.md) 与 [2026 年产品对标](BENCHMARKS-2026.md)。

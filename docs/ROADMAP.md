# 路线图

## v0.1 — 当前

- [x] eaopen 独立仓库与 Apache 2.0 授权
- [x] EAP + OpenBPM、EXTN、CloudFile 三个适配器
- [x] MCP 2.x stdio、离线能力发现、固定路由只读、离线变更预览
- [x] 单元测试与本地模拟 HTTP 认证/响应测试
- [x] Skills 路由与扩展设计
- [ ] EAP + OpenBPM 真实授权 DEV 测试
- [ ] EXTN 真实授权 DEV 测试
- [ ] CloudFile V2 真实授权 DEV 测试
- [ ] 各部署版本能力探测（区别源码有能力与部署有能力）

## v0.2 — 真实集成与业务语义

- 读取 EAP + OpenBPM 业务对象、表单、流程、权限影响，兼容 Boot3 3.9.6 / Boot4 4.0.1，并适配各应用宿主的能力差异。
- EXTN 表单、流程模板及字典模型的只读解析与结构校验。
- CloudFile 只读文件/ACL 发现，复用 Toolkit 已落地的专业工具，不复制执行器。
- 差异计划、依赖解释、版本前置条件和多平台测试夹具。

## v0.3 — 受控变更（需另行确认）

- 配置级 `inspect → plan → validate → approve → apply → verify`。
- 仅在授权的开发/测试环境开启；幂等、版本冲突、审计和回滚证据齐备。
- 仅添加已证明必要的 Java Starter 或宿主适配，不与 Boot4 版本升级混为一体。

## 非目标

- 直接暴露所有 Controller / DB / Shell
复制客户专有 Skills 或私有业务资产
- 新造一套 CloudFile CLI 或迁移服务
- 复制 JeecgBoot Skills 并宣称完整适配
- 建设通用 AI 模型平台、多智能体平台或全套低代码设计器

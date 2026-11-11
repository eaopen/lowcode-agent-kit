---
name: lowcode-cloudfile
description: Discover read-only CloudFile/Seafile features and libraries for enterprise AI integrations; delegate file operations to existing cloudfile-toolkit.
---

# CloudFile 连接器

CloudFile 是文件、库和权限连接器，**不是第三套低代码表单平台**。

1. 使用 `platform_discover`，确认适配器是 `cloudfile`。
2. 仅调用固定的 `files.features`、`files.libraries`，必要时使用带 UUID 的 `files.library.inspect`。
3. 认证沿用当前用户，默认 `Authorization: Token`。功能可用性受服务器版本与开关影响；403/404 不应当作空列表或操作成功。
4. 需要文件搜索、读取、下载、导入或权限诊断时，参考 [CloudFile Toolkit](https://github.com/eaopen/cloudfile-toolkit) 中对应 Skill 与**实际已交付**的执行器。Toolkit CLI 尚在规划时不得猜测命令。
5. 不修改原生文件权限、绕过 ACL、下载无关文件，或在失败时自行切换管理员。

公共连接器不复制文件传输逻辑，也不存储业务文件和凭据。

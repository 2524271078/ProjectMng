# 2026-11-20 发布记录：邮件发送配置页面化

## 基本信息

- 状态：待测试、未发布到服务器
- 申请人：用户
- 执行人：待填写
- 开始时间：待填写
- 结束时间：待填写
- 服务器：`172.18.105.14`（主机名 `centos-test`）
- 发布前版本：用户反馈 2026-11-19 已发布一版，准确 Git SHA/交付包名待发布前核对
- 本地开发基线：`4bb3012`（当前变更尚未提交，发布版本以最终提交号或交付包 SHA256 为准）
- 发布后版本：`20261120-email-config` 发布包（服务器部署结果待填写）
- 关联需求：SMTP 登录账号、授权码和默认发件邮箱不再要求写入 `.env`，改由“维保邮件提醒 > 邮件配置”维护

## 本次发布范围约束

- 发布方式：增量功能发布，仅更新应用代码、前端构建产物并执行数据库结构迁移。
- 业务数据：继续使用服务器现有 PostgreSQL 数据，禁止导入或覆盖本地业务数据。
- 附件数据：继续使用服务器现有 `backend/media`，禁止用本地媒体包覆盖。
- 禁止执行：`manage.py loaddata`、本地数据库恢复、服务器业务表清空、服务器 `media` 整目录覆盖。
- 允许执行：发布前数据库备份、代码包更新、依赖更新、`manage.py migrate`、静态资源更新、服务重启和验证。
- 新迁移 `projects.0021_serviceexpiryemailsetting_sender_config` 仅新增邮件配置字段，不应删除或替换现有业务数据。

## 发布内容

- `ServiceExpiryEmailSetting` 增加 SMTP 登录账号、加密授权码和默认发件邮箱字段。
- 新增迁移 `projects.0021_serviceexpiryemailsetting_sender_config`。
- 邮件发送优先读取数据库配置，未配置时兼容原环境变量。
- 授权码用 Django `SECRET_KEY` 派生密钥加密保存，API 不返回明文。
- 前端“统一抄送配置”升级为“邮件配置”。
- 维保提醒邮件落款更新为交付管理平台及电力能源交付部联系人信息。
- 更新邮件部署说明和 `.env.example`。

## 本地验证记录

- PostgreSQL 正式开发库迁移：`projects.0021_serviceexpiryemailsetting_sender_config`，结果 `OK`。
- PostgreSQL 回归测试：`projects.test_email_settings` 共 3 项，全部通过。
- Django `manage.py check`：通过。
- Django `makemigrations --check --dry-run`：`No changes detected`。
- 前端 `npm run build`：成功；存在依赖包 PURE 注释与大分块警告，不影响构建结果。
- 最终相关回归测试：邮件配置及授权共 7 项，全部通过。
- 源码包：`projectmng-source-20261120-email-config.tar.gz`，SHA256 `D72E34F9E1E667C9508EEC6F2E72BD8F1550948F7FB0D0EECA41871176DD9DFA`。
- 前端包：`projectmng-frontend-20261120-email-config.tar.gz`，SHA256 `50A5110A2C574D24860B8F92ED16DBC8757B44EEF5481763E1B7F8AC6E2F6982`。
- 包内容检查：无 `.env`、数据库、`backend/media`、`node_modules`、`.pyc`；包含迁移 `0021` 和新邮件落款。

## 服务器发布前检查与备份

```bash
systemctl status projectmng-postgresql projectmng nginx --no-pager
mkdir -p /opt/projectmng/backups
su -s /bin/bash postgres -c '/opt/projectmng/postgresql/bin/pg_dump -Fc -d project_mng -f /opt/projectmng/backups/project_mng_YYYYMMDD_HHMM.dump'
test -s /opt/projectmng/backups/project_mng_YYYYMMDD_HHMM.dump
su -s /bin/bash projectmng -c 'cd /opt/projectmng/app/backend && /opt/projectmng/miniforge/envs/projectmng/bin/python manage.py shell -c "from projects.models import Organization,Project,Device,ProjectDevice,Contract; print({\"organizations\":Organization.objects.count(),\"projects\":Project.objects.count(),\"devices\":Device.objects.count(),\"project_devices\":ProjectDevice.objects.count(),\"contracts\":Contract.objects.count()})"'
```

- 实际命令结果：待填写
- 数据库备份路径和大小：`/opt/projectmng/backups/project_mng_before_email_config_20261120.dump`，297K，属主 `postgres:postgres`，2026-11-20 18:19 创建成功。
- 发布前业务数据抽查/数量记录：待填写

### 2026-11-20 发布前首次检查

- `projectmng-postgresql.service`：`active (running)`，PostgreSQL 18.4。
- `projectmng.service`：`active (running)`，Gunicorn 正常运行。
- `nginx.service`：运行中，工作进程存在。
- `/opt/projectmng` 所在文件系统：总计 46G、已用 12G、可用 34G、使用率 26%。
- 结论：服务状态及磁盘空间满足后续备份与压缩包升级条件。

## 服务器发布过程

沿用现有压缩包升级方式。开发机测试完成并提交后，生成同一提交号的两个交付包：

```text
projectmng-source-<commit>.tar.gz
projectmng-frontend-<commit>.tar.gz
```

本次没有新增 Python 依赖，不需要更新依赖 wheel 包。使用 `rz -be` 上传到 `/opt/projectmng/packages/` 后，记录文件大小和 SHA256，并先检查包内不含 `.env`、数据库文件或 `backend/media`：

```bash
cd /opt/projectmng/packages
sha256sum projectmng-source-<commit>.tar.gz projectmng-frontend-<commit>.tar.gz
tar -tf projectmng-source-<commit>.tar.gz | grep -E '/\.env$|db\.sqlite3$|/backend/media/'

su -s /bin/bash projectmng -c 'cd /opt/projectmng/app/backend && /opt/projectmng/miniforge/envs/projectmng/bin/python manage.py showmigrations projects'

cd /opt/projectmng/app
tar -xzf /opt/projectmng/packages/projectmng-source-<commit>.tar.gz --strip-components=1
tar -xzf /opt/projectmng/packages/projectmng-frontend-<commit>.tar.gz
chown -R projectmng:projectmng /opt/projectmng/app

su -s /bin/bash projectmng -c 'cd /opt/projectmng/app/backend && /opt/projectmng/miniforge/envs/projectmng/bin/python manage.py migrate --noinput'
su -s /bin/bash projectmng -c 'cd /opt/projectmng/app/backend && /opt/projectmng/miniforge/envs/projectmng/bin/python manage.py showmigrations projects'

systemctl restart projectmng
systemctl reload nginx
systemctl status projectmng-postgresql projectmng nginx --no-pager

su -s /bin/bash projectmng -c 'cd /opt/projectmng/app/backend && /opt/projectmng/miniforge/envs/projectmng/bin/python manage.py shell -c "from projects.models import Organization,Project,Device,ProjectDevice,Contract; print({\"organizations\":Organization.objects.count(),\"projects\":Project.objects.count(),\"devices\":Device.objects.count(),\"project_devices\":ProjectDevice.objects.count(),\"contracts\":Contract.objects.count()})"'
```

包内容检查命令正常情况下应无输出；一旦发现 `.env`、数据库文件或 `media`，立即停止升级并重新制包。本次禁止执行 `manage.py loaddata`、SQL 数据导入及本地媒体包覆盖。

本次预期只应用：

```text
[X] 0021_serviceexpiryemailsetting_sender_config
```

该迁移只给 `projects_serviceexpiryemailsetting` 新增 `email_host_user`、`email_host_password`、`default_from_email` 三个字段，不替换服务器现有业务数据。

- 上传/校验/解压或版本切换命令：待填写
- 依赖安装命令及结果：待填写
- 迁移结果：2026-11-20，`Applying projects.0021_serviceexpiryemailsetting_sender_config... OK`。
- 服务重启结果：升级命令链已完成 `systemctl start projectmng` 和 `systemctl reload nginx`，待最终状态确认。
- 迁移后业务数据数量复核：待填写
- 异常及处置：待填写

## 发布后验证

- 服务状态：待填写
- 登录：待填写
- 维保邮件列表：待填写
- 超级管理员打开并保存邮件配置：待填写
- 授权码重新打开时不回显明文：待填写
- 测试邮件发送及发件人/抄送检查：待填写
- 应用日志无新增异常：待填写
- 验证人及时间：待填写

## 实际执行命令流水

以下按本次服务器终端中的实际执行顺序登记，每条命令单独留痕。

### 1. 发布前服务状态检查

```bash
systemctl status projectmng-postgresql projectmng nginx --no-pager
```

结果：PostgreSQL、Gunicorn 和 Nginx 均处于运行状态。

### 2. 磁盘空间检查

```bash
df -h /opt/projectmng
```

结果：文件系统总计 46G、已用 12G、可用 34G、使用率 26%。

### 3. 第一次上传前端包

```bash
rz -be
```

结果：`projectmng-frontend-20261120-email-config.tar.gz` 被上传至 `/root`；该文件未参与后续升级，不影响运行。

### 4. 查看 `/root` 中的上传结果

```bash
ls -lh *20261120-email-config*
```

结果：发现前端包位于 `/root`，大小约 443K。

### 5. 查看 `/root` 目录

```bash
ls
```

结果：确认前端包上传目录不正确，随后切换到正式包目录重新上传。

### 6. 进入服务器交付包目录

```bash
cd /opt/projectmng/packages
```

结果：成功进入 `/opt/projectmng/packages`。

### 7. 重新上传前端包

```bash
rz -be
```

结果：前端包成功上传到 `/opt/projectmng/packages`。

### 8. 查看交付包目录

```bash
ls
```

结果：确认新前端包与服务器历史交付包均存在。

### 9. 上传源码包

```bash
rz -be
```

结果：`projectmng-source-20261120-email-config.tar.gz` 成功上传到 `/opt/projectmng/packages`。

### 10. 检查本次两个上传包

```bash
ls -lh *20261120-email-config*
```

结果：前端包约 443K，源码包约 257K，两个文件均存在。

### 11. 创建备份目录、备份服务器数据库并检查文件

```bash
install -d -o postgres -g postgres -m 750 /opt/projectmng/backups && su -s /bin/bash postgres -c '/opt/projectmng/postgresql/bin/pg_dump -Fc -d project_mng -f /opt/projectmng/backups/project_mng_before_email_config_20261120.dump' && ls -lh /opt/projectmng/backups/project_mng_before_email_config_20261120.dump
```

结果：备份成功，文件 `/opt/projectmng/backups/project_mng_before_email_config_20261120.dump`，大小 297K，属主 `postgres:postgres`，时间 2026-11-20 18:19。

### 12. 停止应用、解压升级、执行迁移并重启服务

```bash
cd /opt/projectmng/app && \
systemctl stop projectmng && \
tar -xzf /opt/projectmng/packages/projectmng-source-20261120-email-config.tar.gz --strip-components=1 && \
tar -xzf /opt/projectmng/packages/projectmng-frontend-20261120-email-config.tar.gz && \
chown -R projectmng:projectmng /opt/projectmng/app && \
su -s /bin/bash projectmng -c 'cd /opt/projectmng/app/backend && /opt/projectmng/miniforge/envs/projectmng/bin/python manage.py migrate --noinput' && \
systemctl start projectmng && \
systemctl reload nginx
```

结果：命令链完整执行；数据库迁移输出 `Applying projects.0021_serviceexpiryemailsetting_sender_config... OK`，随后应用服务启动并重新加载 Nginx。

### 13. 待执行的最终检查

以下命令已给出，但截至本记录更新时尚未收到执行结果，因此不标记为完成：

```bash
systemctl is-active projectmng projectmng-postgresql nginx
```

## 回滚预案与实际情况

- 应用回滚目标：发布前版本，待核对准确 SHA/包名。
- 数据库恢复文件：发布前备份完成后填写。
- 回滚触发条件：迁移失败且无法安全修复、应用无法启动、邮件核心流程异常。
- 实际是否回滚：待填写。
- 注意：数据库回滚前必须先停止应用并确认恢复目标；不得直接反向迁移或覆盖数据库。
- 本次为新增列迁移，旧版代码可忽略新增列；功能异常时优先恢复上一个代码压缩包并重启，不直接删除数据库字段。只有数据库损坏时才使用发布前 dump 恢复。

## 最终结论

- 待服务器发布与验证后填写。

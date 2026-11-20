# YYYY-MM-DD 发布记录：主题

## 基本信息

- 状态：待发布 / 发布中 / 已完成 / 已回滚 / 失败
- 申请人：
- 执行人：
- 开始时间：
- 结束时间：
- 服务器：
- 发布前版本（Git SHA 或包名+SHA256）：
- 发布后版本（Git SHA 或包名+SHA256）：
- 关联需求/变更：
- 数据策略：保留服务器现有数据 / 导入数据（必须说明来源并单独审批）
- Media 策略：保留 / 增量同步 / 覆盖（覆盖必须单独审批）

## 发布内容

- （填写）

## 发布前检查与备份

```bash
# 在此粘贴实际执行命令；敏感信息使用 <已脱敏>
systemctl status projectmng-postgresql projectmng nginx --no-pager
mkdir -p /opt/projectmng/backups
su -s /bin/bash postgres -c '/opt/projectmng/postgresql/bin/pg_dump -Fc -d project_mng -f /opt/projectmng/backups/project_mng_YYYYMMDD_HHMM.dump'
test -s /opt/projectmng/backups/project_mng_YYYYMMDD_HHMM.dump
```

- 命令结果：
- 数据库备份：
- Media 备份（如涉及）：
- 发布前关键业务表数量抽查：

## 发布过程

```bash
# 记录实际的上传、校验、解压/切换版本、安装依赖、迁移和重启命令
cd /opt/projectmng/app/backend
/opt/projectmng/miniforge/envs/projectmng/bin/python manage.py showmigrations projects
/opt/projectmng/miniforge/envs/projectmng/bin/python manage.py migrate
systemctl restart projectmng
systemctl reload nginx
```

- 命令结果：
- 应用的数据库迁移：
- 发布后关键业务表数量复核：
- 异常及处置：

## 发布后验证

```bash
systemctl status projectmng-postgresql projectmng nginx --no-pager
journalctl -u projectmng -n 100 --no-pager
curl -I http://127.0.0.1/
```

- 登录：通过 / 失败
- 查询接口：通过 / 失败
- 新增或编辑：通过 / 失败 / 不涉及
- 本次功能：通过 / 失败
- 日志检查：通过 / 失败
- 验证人及时间：

## 回滚预案与实际情况

- 应用回滚目标：
- 数据库恢复文件：
- 回滚触发条件：
- 实际是否回滚：否 / 是
- 回滚过程及结果：

## 最终结论

- （填写）

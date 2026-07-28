# Windows 部署与运行指南

本文适用于当前项目：后端为 Django，前端为 Vue + Vite，数据库暂为 SQLite。开发环境可以在 PyCharm 中运行；局域网试用时需要让前后端分别监听局域网地址。

## 1. 先区分两种运行方式

| 场景 | 用途 | 是否适合长期使用 |
| --- | --- | --- |
| PyCharm 本地运行 | 开发、调试 | 仅开发时使用 |
| Windows 单机试用部署 | 同事通过局域网访问 | 可以作为当前阶段的内部试用方案 |
| 正式生产部署 | 长期、多用户、数据安全 | 建议迁移 PostgreSQL，并使用 Nginx + Windows 服务 |

本文先说明第二种方式。部署机器不必每天重启；前端和后端保持运行即可。

## 2. 环境准备

在部署机器安装：

- Python 3.11 或与当前开发环境一致的版本；
- Node.js LTS（建议 20 或更高）；
- Git（用于拉取代码）；
- 可选：PyCharm，仅在需要调试时使用。

在项目根目录执行一次：

```powershell
# 后端依赖与数据库
cd D:\盛邦\交付\ProjectMng\backend
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\.venv\Scripts\python.exe manage.py migrate

# 前端依赖
cd ..\frontend
npm install
```

如果项目还没有虚拟环境，可先在项目根目录创建：

```powershell
python -m venv .venv
```

## 3. 配置前端访问后端地址

前端需要知道后端 API 地址。编辑 `frontend/.env.local`：

```env
VITE_API_BASE_URL=http://服务器IP:8000/api
```

例如部署机器 IP 是 `192.168.35.8`：

```env
VITE_API_BASE_URL=http://192.168.35.8:8000/api
```

修改该文件后必须重启前端开发服务；如果构建前端，则必须重新执行 `npm run build`。

## 4. 启动后端

打开一个 PowerShell 窗口：

```powershell
cd D:\盛邦\交付\ProjectMng\backend
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```

`0.0.0.0:8000` 表示接受本机和局域网请求。验证地址：

- 本机：`http://127.0.0.1:8000/`
- 局域网：`http://服务器IP:8000/`

## 5. 启动前端（内部试用）

再打开一个 PowerShell 窗口：

```powershell
cd D:\盛邦\交付\ProjectMng\frontend
npm run dev
```

Vite 已配置为监听局域网地址，默认端口是 `5173`。访问：

```text
http://服务器IP:5173/
```

例如：`http://192.168.35.8:5173/`。

若本机可访问、其他电脑不能访问，请在 Windows 防火墙中放行 TCP 端口 `5173` 和 `8000`，并确认两台电脑在可互通的网络中。

## 6. 在 PyCharm 中运行

开发时可配置两个 Run Configuration：

1. Django 后端
   - Working directory：`D:\盛邦\交付\ProjectMng\backend`
   - Script：`manage.py`
   - Parameters：`runserver 0.0.0.0:8000`
   - Python interpreter：项目 `.venv`。

2. 前端
   - 类型：`npm`
   - package.json：`frontend/package.json`
   - Command：`run`
   - Scripts：`dev`。

PyCharm 关闭、运行配置停止或电脑关机后，服务会停止。这是开发调试的正常行为，不代表数据丢失；SQLite 数据保存在 `backend/db.sqlite3`。

## 7. 巡检任务为什么要每天执行一次

巡检任务首次会在“保存设备服务计划”时生成。每天执行的检查用于：

- 将超过计划日期但未完成的巡检标记为“已逾期”；
- 补齐服务计划后续的巡检任务；
- 找出已进入“提前提醒天数”的待巡检任务。

它不是重启后端，也不会影响正在使用系统的用户。命令运行数秒后退出：

```powershell
cd D:\盛邦\交付\ProjectMng\backend
..\.venv\Scripts\python.exe manage.py process_inspection_tasks
```

## 8. 配置 Windows 每日巡检检查

建议在部署机器的“任务计划程序”创建任务：

1. 打开“任务计划程序”→“创建基本任务”。
2. 名称：`设备巡检状态检查`。
3. 触发器：每天，例如每天 `09:00`。
4. 操作：启动程序。
5. 程序或脚本：

   ```text
   D:\盛邦\交付\ProjectMng\.venv\Scripts\python.exe
   ```

6. 添加参数：

   ```text
   manage.py process_inspection_tasks
   ```

7. 起始于：

   ```text
   D:\盛邦\交付\ProjectMng\backend
   ```

保存后可右键该任务选择“运行”验证。当前命令会输出新增任务数量和待提醒数量；后续如接入站内信、邮件或企业微信，就在这一步实际发送提醒。

## 9. 每次更新代码后的操作

```powershell
cd D:\盛邦\交付\ProjectMng
git pull

cd backend
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py test

cd ..\frontend
npm install
npm run build
```

若当前用 `npm run dev`，重启该前端进程即可；后端代码更新后也需要重启 `runserver`。

## 10. 正式上线前必须处理的事项

当前 `backend/config/settings.py` 是开发配置：`DEBUG=True`、`ALLOWED_HOSTS=["*"]`，且使用 SQLite。正式上线前至少应：

- 将 `DEBUG` 改为 `False`；
- 将 `SECRET_KEY` 放到环境变量，不写死在代码中；
- 将 `ALLOWED_HOSTS` 限制为实际域名或服务器 IP；
- 将 SQLite 迁移到 PostgreSQL 并定期备份；
- 使用 Windows 服务运行后端（例如 Waitress），由 Nginx 托管前端构建产物和反向代理 `/api/`；
- 使用 HTTPS、访问控制和日志备份。

在这些工作完成前，当前方案仅建议用于可信局域网的内部试用。

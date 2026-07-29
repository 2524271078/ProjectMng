# 项目服务器部署手册（推荐 Linux 生产方案）

本文面向第一次把本项目部署到服务器的情况。项目是前后端分离架构：

- 前端：Vue 3 + Vite，源码在 `frontend/`；
- 后端：Django + Django REST Framework，源码在 `backend/`；
- 当前开发数据库：SQLite，文件是 `backend/db.sqlite3`；
- 上传附件：`backend/media/`。

推荐正式部署到 **Ubuntu 24.04 LTS + Nginx + Gunicorn + PostgreSQL**。Nginx 对外提供 HTTPS 和前端页面，Gunicorn 在内网运行 Django，PostgreSQL 保存业务数据。浏览器只访问一个地址，例如 `https://pm.example.com`。

> 现有 `docs/windows-deployment-guide.md` 适合 Windows 局域网试用。不要将 Django 的 `runserver` 或 Vite 的 `npm run dev` 当作正式生产服务。

## 1. 先理解：哪些东西需要“编译”

| 内容 | 是否需要编译/处理 | 生产环境的动作 |
| --- | --- | --- |
| 前端 Vue 源码 | **需要构建** | 在 `frontend/` 执行 `npm ci`、`npm run build`，得到 `dist/` 静态文件。 |
| Django/Python 后端 | 不需要编译 | 创建虚拟环境、安装依赖，再由 Gunicorn 加载 `config.wsgi`。 |
| 数据库模型 | 不手写建表 SQL | 执行 `python manage.py migrate`；Django migration 会创建或变更表。 |
| 上传文件 | 不编译 | 将 `backend/media/` 持久保存并由 Nginx 提供访问。 |

前端构建结果和 Python 虚拟环境都不应提交 Git。每次前端代码或 `VITE_*` 配置改变后，必须重新运行 `npm run build`。

## 2. 上线前必须完成的代码配置

当前 `backend/config/settings.py` 是开发配置（固定 `SECRET_KEY`、`DEBUG=True`、`ALLOWED_HOSTS=["*"]`、SQLite），不能原样暴露到公网。正式部署前请把它调整为从环境变量读取。建议先在开发分支完成、测试通过后再上线。

最小目标如下：

```python
# backend/config/settings.py（关键配置示例）
import os

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = [item.strip() for item in os.environ["DJANGO_ALLOWED_HOSTS"].split(",") if item.strip()]
CSRF_TRUSTED_ORIGINS = [item.strip() for item in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if item.strip()]

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["POSTGRES_DB"],
        "USER": os.environ["POSTGRES_USER"],
        "PASSWORD": os.environ["POSTGRES_PASSWORD"],
        "HOST": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}
```

同样需要在 `backend/requirements.txt` 固定加入生产依赖，至少：

```text
gunicorn>=23,<24
psycopg[binary]>=3.2,<4
```

本项目的 Django 版本范围是 `>=6.0,<6.1`，服务器必须使用 **Python 3.12、3.13 或 3.14**；推荐 Python 3.12。不要沿用旧说明中的 Python 3.11。

前端建议使用同源 API，避免暴露 `:8000` 和跨域问题。服务器构建前新建 `frontend/.env.production`：

```dotenv
VITE_API_BASE_URL=/api
```

不要把开发机的 `frontend/.env.local`（当前含局域网 IP）复制到服务器，否则该地址会被编译进前端文件。

## 3. 准备服务器和域名

以下以域名 `pm.example.com`、部署用户 `deploy`、代码目录 `/srv/project-mng` 为例；请替换成真实值。

1. 准备一台 Ubuntu 24.04 LTS 服务器，申请域名并将 A 记录指向服务器公网 IP。
2. 安全组/防火墙仅开放 TCP `22`（SSH）、`80`（HTTP）、`443`（HTTPS）。**不要**对公网开放 PostgreSQL `5432` 或 Gunicorn `8000`。
3. 创建普通部署用户；日常不要用 root 运行应用。
4. 安装系统组件：Git、Python 3.12、Python venv、Node.js LTS、PostgreSQL、Nginx、Certbot。

示例命令（以服务器实际软件源中的版本为准）：

```bash
sudo apt update
sudo apt install -y git python3.12 python3.12-venv postgresql nginx certbot python3-certbot-nginx
# 按 Node.js 官方 LTS 安装说明安装 Node.js；安装后确认 node --version 和 npm --version
```

## 4. 初始化 PostgreSQL

登录 PostgreSQL 后创建专用数据库和用户。密码使用随机长密码，不能使用示例值。

```bash
sudo -u postgres psql
CREATE USER project_mng WITH PASSWORD '请替换为随机长密码';
CREATE DATABASE project_mng OWNER project_mng ENCODING 'UTF8';
\q
```

生产数据库与 Django 运行在同一台服务器时，`POSTGRES_HOST=127.0.0.1` 即可；不必对外监听 5432 端口。

## 5. 首次部署代码

```bash
sudo mkdir -p /srv/project-mng
sudo chown deploy:deploy /srv/project-mng
sudo -iu deploy
git clone <你的 Git 仓库地址> /srv/project-mng
cd /srv/project-mng

python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -r backend/requirements.txt

cd frontend
npm ci
printf 'VITE_API_BASE_URL=/api\n' > .env.production
npm run build

cd ../backend
```

在 `/srv/project-mng/backend/.env.production` 创建仅服务器可读的环境文件（`chmod 600`）。它不能提交 Git：

```dotenv
DJANGO_SECRET_KEY=用密码管理器生成的长随机值
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=pm.example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://pm.example.com
POSTGRES_DB=project_mng
POSTGRES_USER=project_mng
POSTGRES_PASSWORD=数据库随机长密码
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
```

执行首次建表和静态文件收集：

```bash
set -a; source .env.production; set +a
/srv/project-mng/.venv/bin/python manage.py migrate
/srv/project-mng/.venv/bin/python manage.py collectstatic --noinput
/srv/project-mng/.venv/bin/python manage.py check --deploy
```

首次安装还没有用户时再执行 `python manage.py createsuperuser`。若后续从开发机迁移已有数据，按下一节操作，**不要**再创建重复管理员。

## 6. 从当前 SQLite 迁移已有数据

在开发机先停止所有会写入系统的用户操作，做完整备份。SQLite 数据和上传附件缺一不可。

```powershell
cd backend
python manage.py dumpdata --exclude contenttypes --exclude auth.permission --indent 2 | Out-File -Encoding utf8 ..\data-export.json
```

把 `data-export.json` 和整个 `backend/media/` 安全传到服务器。服务器已经执行 `migrate` 后：

```bash
cd /srv/project-mng/backend
set -a; source .env.production; set +a
/srv/project-mng/.venv/bin/python manage.py loaddata /srv/project-mng/data-export.json
```

导入后登录后台和前台抽查数量、附件下载和权限。确认无误前，保留原始 `db.sqlite3`、`media/` 和导出文件；生产环境以后以 PostgreSQL 备份为准。

## 7. 配置 Gunicorn 为系统服务

创建 `/etc/systemd/system/project-mng.service`：

```ini
[Unit]
Description=Project management Django API
After=network.target postgresql.service

[Service]
User=deploy
Group=www-data
WorkingDirectory=/srv/project-mng/backend
EnvironmentFile=/srv/project-mng/backend/.env.production
ExecStart=/srv/project-mng/.venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 config.wsgi:application
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启动并查看日志：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now project-mng
sudo systemctl status project-mng
sudo journalctl -u project-mng -f
```

`8000` 只绑定 `127.0.0.1`，因此只能由同机 Nginx 访问。

## 8. 配置 Nginx

创建 `/etc/nginx/sites-available/project-mng`：

```nginx
server {
    listen 80;
    server_name pm.example.com;

    root /srv/project-mng/frontend/dist;
    index index.html;
    client_max_body_size 50m;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ { alias /srv/project-mng/backend/staticfiles/; }
    location /media/  { alias /srv/project-mng/backend/media/; }

    # Vue 单页应用：非文件路径仍返回入口页。
    location / { try_files $uri $uri/ /index.html; }
}
```

启用并测试：

```bash
sudo ln -s /etc/nginx/sites-available/project-mng /etc/nginx/sites-enabled/project-mng
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d pm.example.com
```

证书申请成功后，访问 `https://pm.example.com`。测试 API 使用 `https://pm.example.com/api/`，而不是 `:8000`。

## 9. 每次发布新版本的标准流程

先在开发/测试环境验证，再在维护窗口执行。数据库迁移可能不可逆，上线前必须有可恢复备份。

```bash
sudo -iu deploy
cd /srv/project-mng
git fetch --all --prune
git pull --ff-only

.venv/bin/pip install -r backend/requirements.txt
cd frontend && npm ci && npm run build
cd ../backend
set -a; source .env.production; set +a
../.venv/bin/python manage.py migrate
../.venv/bin/python manage.py collectstatic --noinput
../.venv/bin/python manage.py check --deploy
sudo systemctl restart project-mng
```

发布后至少验证：登录、一个查询接口、一个新增/编辑操作、附件上传下载和 `systemctl status project-mng`。若版本有前端变更但没有重新 build，用户仍会看到旧页面；若有 migration 但没有 migrate，接口可能报数据库字段错误。

## 10. 定时任务与备份

项目已有巡检任务处理命令，应每天运行一次。用 `crontab -e` 为 `deploy` 增加：

```cron
0 9 * * * cd /srv/project-mng/backend && set -a && . ./.env.production && set +a && /srv/project-mng/.venv/bin/python manage.py process_inspection_tasks >> /srv/project-mng/logs/inspection.log 2>&1
```

先执行 `mkdir -p /srv/project-mng/logs`。如果环境变量中有 shell 特殊字符，请将 `.env.production` 中的值用单引号包住，并在编辑后手动运行一次命令验证。

每日备份至少包含 PostgreSQL 和 `backend/media/`：

```bash
pg_dump -h 127.0.0.1 -U project_mng -Fc project_mng > /srv/backups/project_mng_$(date +%F).dump
tar -C /srv/project-mng/backend -czf /srv/backups/project_mng_media_$(date +%F).tar.gz media
```

为使定时备份不等待输入密码，在 `deploy` 用户的 `~/.pgpass` 写入一行 `127.0.0.1:5432:project_mng:project_mng:数据库密码`，然后执行 `chmod 600 ~/.pgpass`。备份目录应有独立磁盘或对象存储副本；仅把备份留在同一台服务器，无法应对服务器磁盘损坏或被勒索。至少每季度在隔离环境实际执行一次恢复演练。

## 11. 上线前检查清单

- [ ] `DEBUG=False`，`SECRET_KEY` 不在 Git 中，`ALLOWED_HOSTS` 仅含实际域名/IP。
- [ ] 使用 PostgreSQL；数据库端口不对公网开放。
- [ ] HTTPS 已启用，80 自动跳转 443（Certbot 通常会协助配置）。
- [ ] `runserver` 和 `npm run dev` 没有作为服务运行。
- [ ] `media/`、数据库已备份且验证能恢复。
- [ ] Nginx、Gunicorn、PostgreSQL 都设置为开机启动。
- [ ] 服务器只开放 22、80、443，SSH 使用密钥并限制可登录用户。

## 12. 如果暂时只能使用 Windows 服务器

可以先使用仓库内的 `docs/windows-deployment-guide.md` 做受信任局域网试用。但正式对外服务仍应：使用 PostgreSQL、将 Django 换成 Waitress Windows 服务、以 Nginx/IIS 托管 `frontend/dist` 并反向代理 `/api/`、配置 HTTPS 和备份。Windows 不建议长期运行 `runserver` 或 Vite 开发服务器。

## 参考资料

- [Django 部署清单](https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/)
- [Django WSGI 部署说明](https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/)
- [Django 6.0 Python 版本兼容性](https://docs.djangoproject.com/en/6.0/faq/install/)

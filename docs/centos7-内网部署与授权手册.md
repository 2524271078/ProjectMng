# 交付中台 CentOS 7 内网部署与授权手册

本文记录已验证的内网部署方案：CentOS 7.9、Nginx、Gunicorn、PostgreSQL 18.4、Miniforge Python 3.12。浏览器只访问 Nginx 的 80 端口；PostgreSQL 与 Gunicorn 仅监听本机。

> 适用服务器：`172.18.105.14`；应用目录：`/opt/projectmng`。CentOS 7 已停止维护，后续条件允许时应迁移到 Rocky Linux 9 / AlmaLinux 9 等受支持系统。

## 1. 运行结构

```text
浏览器 http://172.18.105.14/
            │
          Nginx :80
       ┌────┴─────┐
  / 静态前端      /api/ 反向代理
 /opt/projectmng/app/dist   Gunicorn 127.0.0.1:8000
                                  │
                         PostgreSQL 127.0.0.1:5432
```

相关目录：

| 路径 | 用途 |
| --- | --- |
| `/opt/projectmng/app` | 后端代码、前端 `dist`、媒体文件 |
| `/opt/projectmng/packages` | 上传的发布包、数据备份和安装包 |
| `/opt/projectmng/postgresql` | PostgreSQL 18.4 程序 |
| `/opt/projectmng/postgres-data` | PostgreSQL 数据目录 |
| `/opt/projectmng/miniforge` | Miniforge 与 Python 运行环境 |
| `/opt/projectmng/logs` | PostgreSQL 和应用日志 |

## 2. 服务器基础检查

```bash
cat /etc/centos-release
free -h
nproc
df -h
getconf LONG_BIT
```

本项目当前环境为 2 核、约 3.7 GB 内存、46 GB 根分区；适合小规模内网使用。不要把 PostgreSQL `5432` 或 Gunicorn `8000` 开放到内网。

安装并启动 Nginx：

```bash
yum install -y epel-release
yum install -y nginx
systemctl enable --now nginx
curl -I http://127.0.0.1
```

创建目录：

```bash
mkdir -p /opt/projectmng/{packages,app,logs}
```

## 3. Python 3.12（CentOS 7）

最新版 Miniconda 要求 GLIBC 2.28，CentOS 7 的 GLIBC 为 2.17，不能使用。使用支持 GLIBC 2.17 的 Miniforge：

```bash
cd /opt/projectmng/packages
curl -4 -LO https://mirrors.tuna.tsinghua.edu.cn/github-release/conda-forge/miniforge/LatestRelease/Miniforge3-Linux-x86_64.sh
bash Miniforge3-Linux-x86_64.sh -b -p /opt/projectmng/miniforge
```

创建运行环境：

```bash
/opt/projectmng/miniforge/bin/conda create -y -n projectmng python=3.12 pip
/opt/projectmng/miniforge/envs/projectmng/bin/python --version
```

Pillow 在 CentOS 7 的旧 GCC 上可能无法通过 pip 源码构建。先使用 Conda 二进制包，再安装其余依赖：

```bash
/opt/projectmng/miniforge/bin/conda install -y -n projectmng -c conda-forge "pillow>=12.3,<13"
sed '/^Pillow/d' /opt/projectmng/app/backend/requirements.txt | /opt/projectmng/miniforge/envs/projectmng/bin/python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r /dev/stdin gunicorn
```

## 4. PostgreSQL 18.4

当前业务库使用 PostgreSQL 18.4，不能降级使用 CentOS 7 自带旧版 PostgreSQL。先安装编译依赖：

```bash
yum install -y gcc make readline-devel zlib-devel flex bison
```

下载、编译并安装：

```bash
cd /opt/projectmng/packages
curl -4 -LO https://ftp.postgresql.org/pub/source/v18.4/postgresql-18.4.tar.bz2
tar -xjf postgresql-18.4.tar.bz2
cd postgresql-18.4
./configure --prefix=/opt/projectmng/postgresql --without-icu
make -j2
make install
```

创建账户、初始化数据目录：

```bash
id postgres >/dev/null 2>&1 || useradd --system --no-create-home --shell /sbin/nologin postgres
mkdir -p /opt/projectmng/{postgres-data,logs/postgresql}
chown -R postgres:postgres /opt/projectmng/postgresql /opt/projectmng/postgres-data /opt/projectmng/logs/postgresql
su -s /bin/bash postgres -c '/opt/projectmng/postgresql/bin/initdb -D /opt/projectmng/postgres-data --encoding=UTF8 --locale=C'
```

创建项目账号和数据库。`createuser -P` 会交互输入密码，密码不应出现在命令历史、文档或 Git 中：

```bash
su -s /bin/bash postgres -c '/opt/projectmng/postgresql/bin/pg_ctl -D /opt/projectmng/postgres-data -l /opt/projectmng/logs/postgresql/server.log start'
/opt/projectmng/postgresql/bin/createuser -U postgres -P projectmng_app
/opt/projectmng/postgresql/bin/createdb -U postgres -O projectmng_app -E UTF8 project_mng
```

让应用账号经密码认证连接本机数据库：

```bash
sed -i '1ihost    all             projectmng_app    127.0.0.1/32            scram-sha-256' /opt/projectmng/postgres-data/pg_hba.conf
su -s /bin/bash postgres -c '/opt/projectmng/postgresql/bin/pg_ctl -D /opt/projectmng/postgres-data reload'
```

创建 systemd 服务 `/etc/systemd/system/projectmng-postgresql.service`：

```ini
[Unit]
Description=ProjectMng PostgreSQL 18.4
After=network.target

[Service]
Type=forking
User=postgres
Group=postgres
PIDFile=/opt/projectmng/postgres-data/postmaster.pid
ExecStart=/opt/projectmng/postgresql/bin/pg_ctl start -D /opt/projectmng/postgres-data -s -l /opt/projectmng/logs/postgresql/server.log
ExecStop=/opt/projectmng/postgresql/bin/pg_ctl stop -D /opt/projectmng/postgres-data -s -m fast
ExecReload=/opt/projectmng/postgresql/bin/pg_ctl reload -D /opt/projectmng/postgres-data -s
TimeoutSec=300

[Install]
WantedBy=multi-user.target
```

首次从手工运行切换到 systemd 时：

```bash
su -s /bin/bash postgres -c '/opt/projectmng/postgresql/bin/pg_ctl -D /opt/projectmng/postgres-data stop -m fast'
systemctl daemon-reload
systemctl enable --now projectmng-postgresql
systemctl status projectmng-postgresql --no-pager
```

## 5. 发布代码与生产配置

在开发机生成并上传以下文件到 `/opt/projectmng/packages`：

- `projectmng-source-<commit>.tar.gz`：后端与前端源码；
- `projectmng-frontend-<commit>.tar.gz`：已构建的前端 `dist`，必须使用同源 `/api`；
- `project_mng-data-<date>-full.json`：业务数据导出；
- `project_mng-media-<date>.tar.gz`：`backend/media` 附件；
- `public_key.pem`：授权公钥。

**永远不要上传 `license-private.pem`。**

解压代码和前端：

```bash
cd /opt/projectmng/app
tar -xzf /opt/projectmng/packages/projectmng-source-<commit>.tar.gz --strip-components=1
tar -xzf /opt/projectmng/packages/projectmng-frontend-<commit>.tar.gz
install -m 644 /opt/projectmng/packages/public_key.pem /opt/projectmng/app/backend/licensing/public_key.pem
```

创建运行账户及目录权限：

```bash
id projectmng >/dev/null 2>&1 || useradd --system --home-dir /opt/projectmng --shell /sbin/nologin projectmng
chown -R projectmng:projectmng /opt/projectmng/app
mkdir -p /opt/projectmng/logs/app
chown -R projectmng:projectmng /opt/projectmng/logs/app
```

创建 `/opt/projectmng/app/backend/.env`，并设置 `chmod 600`、所有者为 `projectmng`。示例中的密码必须替换为真实值：

```dotenv
SECRET_KEY=服务器单独生成的随机值
DEBUG=false
DB_ENGINE=postgresql
POSTGRES_DB=project_mng
POSTGRES_USER=projectmng_app
POSTGRES_PASSWORD=数据库密码
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
LICENSE_ENFORCEMENT_ENABLED=true
LICENSE_OPERATOR_USERNAME=xushaotai
LICENSE_PUBLIC_KEY_PATH=/opt/projectmng/app/backend/licensing/public_key.pem
```

```bash
chown projectmng:projectmng /opt/projectmng/app/backend/.env
chmod 600 /opt/projectmng/app/backend/.env
```

## 6. 数据与附件迁移

先在服务器创建表：

```bash
su -s /bin/bash projectmng -c 'cd /opt/projectmng/app/backend && /opt/projectmng/miniforge/envs/projectmng/bin/python manage.py migrate --noinput'
```

开发机导出 PostgreSQL 数据时，应使用 `dumpdata --all`，以包含软删除/停用的关联记录；同时排除令牌及其活动记录：

```python
# 在已加载 Django 配置的 Python 环境中调用
call_command(
    'dumpdata', all=True, natural_foreign=True, natural_primary=True,
    exclude=['admin.logentry', 'authtoken.token', 'sessions.session',
             'licensing.licensestate', 'accounts.tokenactivity'],
    indent=2, stdout=stream,
)
```

导出文件必须为 UTF-8。Windows 默认中文编码文件可在服务器转换：

```bash
iconv -f GB18030 -t UTF-8 old-data.json > data-utf8.json
```

导入并恢复附件：

```bash
su -s /bin/bash projectmng -c 'cd /opt/projectmng/app/backend && /opt/projectmng/miniforge/envs/projectmng/bin/python manage.py loaddata /opt/projectmng/packages/project_mng-data-<date>-full.json'
tar -xzf /opt/projectmng/packages/project_mng-media-<date>.tar.gz -C /opt/projectmng/app/backend
chown -R projectmng:projectmng /opt/projectmng/app/backend/media
```

导入后应至少核对用户、客户组织、项目、设备和项目设备数量。

## 7. Gunicorn 与 Nginx

创建 `/etc/systemd/system/projectmng.service`：

```ini
[Unit]
Description=ProjectMng Gunicorn
After=network.target projectmng-postgresql.service
Requires=projectmng-postgresql.service

[Service]
User=projectmng
Group=projectmng
WorkingDirectory=/opt/projectmng/app/backend
Environment="PATH=/opt/projectmng/miniforge/envs/projectmng/bin"
ExecStart=/opt/projectmng/miniforge/envs/projectmng/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 2 --timeout 60 --access-logfile /opt/projectmng/logs/app/access.log --error-logfile /opt/projectmng/logs/app/error.log
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now projectmng
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/api/auth/me/
```

未登录时接口返回 `401` 为正常结果。

创建 `/etc/nginx/conf.d/projectmng.conf`：

```nginx
server {
    listen 80;
    server_name 172.18.105.14;
    client_max_body_size 50m;
    root /opt/projectmng/app/dist;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    location /media/ {
        alias /opt/projectmng/app/backend/media/;
        access_log off;
        expires 7d;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

```bash
nginx -t
systemctl reload nginx
```

如果 Nginx 静态页返回 200、`/api` 返回 502，而 Gunicorn 本机接口正常，多数是 SELinux 阻止 Nginx 访问本机端口：

```bash
getenforce
setsebool -P httpd_can_network_connect 1
systemctl reload nginx
```

如 firewalld 正在运行，开放 HTTP：

```bash
firewall-cmd --permanent --add-service=http
firewall-cmd --reload
```

最终访问：`http://172.18.105.14/`。

## 8. 日常启停、排错与更新

服务均已设置开机自启。状态检查：

```bash
systemctl status projectmng-postgresql projectmng nginx --no-pager
```

手动启动：

```bash
systemctl start projectmng-postgresql
systemctl start projectmng
systemctl start nginx
```

应用更新后通常执行：

```bash
systemctl restart projectmng
systemctl reload nginx
```

查看日志：

```bash
journalctl -u projectmng -n 100 --no-pager
tail -n 100 /opt/projectmng/logs/app/error.log
tail -n 100 /var/log/nginx/error.log
```

## 9. 离线授权签发与激活

### 授权机制

- 服务器只保存 `public_key.pem`，用于验证许可证；
- 私钥 `license-private.pem` 只由系统所有者保存，不能上传、提交 Git 或发送给他人；
- 授权绑定服务器机器指纹；系统日期回拨会被检测；
- `xushaotai` 是唯一可见“授权管理”的业务账号，其他账号（包含超管）不展示该入口；
- 授权过期或缺失时，业务 API 被锁定；`xushaotai` 仍可登录并进入授权管理激活新文件。

### 首次激活

1. 访问 `http://172.18.105.14/`，用 `xushaotai` 登录；
2. 在“授权管理”下载/保存授权请求 JSON 文件；
3. 将该 JSON 文件保留在系统所有者的 Windows 电脑；
4. 在本机项目目录签发许可证：

```powershell
cd 'D:\盛邦\交付\ProjectMng'
.\.venv\Scripts\python.exe tools\license_tool.py issue --request '授权请求文件.json' --private-key 'D:\交付中台授权\license-private.pem' --customer '交付中台内网部署（172.18.105.14）' --expires-at 2027-02-26 --output 'C:\Users\25242\Downloads\ProjectMng-deployment-20260826\projectmng-license-20270226.lic'
```

命令会提示输入私钥保护密码；输入不会显示。`--request` 必须是请求 JSON 文件路径，不能直接填写机器码字符串。

5. 使用 `rz -be` 将 `.lic` 上传到服务器，例如 `/opt/projectmng/packages/`；
6. 返回 `xushaotai` 的“授权管理”，上传 `.lic` 并激活；
7. 检查页面显示“授权有效”和到期日期。

### 续期

每次续期都重复“下载请求文件 → 本机签发 → 上传激活”即可。建议在到期前 30 天完成。私钥密码遗失无法签发新授权；私钥泄露时必须重新生成密钥对并重新部署新公钥，现有许可证将失效。

## 10. 备份建议

至少备份两部分：PostgreSQL 数据库和 `backend/media`。

```bash
mkdir -p /opt/projectmng/backups
su -s /bin/bash postgres -c '/opt/projectmng/postgresql/bin/pg_dump -Fc -d project_mng -f /opt/projectmng/backups/project_mng_$(date +%F).dump'
tar -C /opt/projectmng/app/backend -czf /opt/projectmng/backups/project_mng_media_$(date +%F).tar.gz media
```

备份目录应同步到另一台受控存储设备；只保留在同一台服务器无法防范磁盘故障或勒索。

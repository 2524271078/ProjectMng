# 项目设备管理系统

用于替代在线表格维护销售、客户、设备、合同、厂商、采购链路和现场运维信息的前后端分离系统。

## 技术栈

- 后端：Django + Django REST Framework
- 前端：Vue3 + Vite + Element Plus
- 数据库：开发阶段 SQLite，后续可切换 PostgreSQL
- 权限：第一阶段实现简单 RBAC，管理员维护用户菜单和功能权限

## 目录结构

```text
backend/   后端 Django API
frontend/  前端 Vue3 SPA
docs/      设计、计划、接口和业务流程文档
```

## 后端启动

```powershell
cd backend
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

提交后端代码前执行：

```powershell
cd backend
python manage.py test
```

## 前端启动

```powershell
cd frontend
npm install
npm run dev
```

提交前端代码前执行：

```powershell
cd frontend
npm run build
```

## 第一阶段流程

新增组织 -> 新增人员 -> 新增销售 -> 绑定销售客户 -> 新增产品型号 -> 新增设备 -> 绑定客户 -> 新增合同 -> 绑定设备 -> 查看销售名下客户和设备。

## 文档

- `docs/api.md`：后端接口说明
- `docs/workflow.md`：第一阶段业务流程说明
- `docs/superpowers/specs/2026-07-02-project-management-system-design.md`：设计文档
- `docs/superpowers/plans/2026-07-02-project-management-system.md`：实施计划

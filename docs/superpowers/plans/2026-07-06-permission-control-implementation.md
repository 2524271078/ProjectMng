# Permission Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为现有项目设备管理系统补齐基于角色的菜单权限与基于销售归属的用户级数据权限，并提供系统管理配置界面。

**Architecture:** 后端在 `accounts` 中扩展用户权限配置模型，并在认证接口返回统一权限摘要；业务查询通过统一的数据范围服务过滤。前端在系统管理中增加用户/角色配置入口，并让导航、路由、按钮跟随权限动态变化。

**Tech Stack:** Django REST Framework, Django auth/token, Vue 3, Pinia, Element Plus

---

## File Map
- Modify: `backend/accounts/models.py` - 新增用户权限配置模型
- Modify: `backend/accounts/serializers.py` - 扩展用户、角色、权限序列化
- Modify: `backend/accounts/views.py` - 用户管理与当前用户权限摘要
- Modify: `backend/accounts/tests.py` - 认证与权限配置回归测试
- Create: `backend/accounts/services.py` - 数据范围解析与动作权限工具
- Modify: `backend/projects/views.py` - 业务列表接入数据权限过滤
- Modify: `backend/projects/tests.py` - 数据范围过滤测试
- Modify: `frontend/src/stores/auth.js` - 保存菜单、动作权限、数据范围摘要
- Modify: `frontend/src/router/index.js` - 路由级菜单权限控制
- Modify: `frontend/src/layouts/AdminLayout.vue` - 左侧菜单按权限动态显示
- Modify: `frontend/src/views/SystemManageView.vue` - 用户、角色、菜单权限配置 UI
- Modify: `frontend/src/views/PersonManageView.vue` - 人员类型中文显示
- Modify: `frontend/src/api/resources.js` - 新增权限管理接口封装

## Phase 1: 权限模型与认证接口
- [ ] 写后端 failing tests，覆盖 `/api/auth/me/` 返回角色、菜单、动作权限、数据范围摘要
- [ ] 实现 `UserAccessProfile` / `UserSalesScope` 模型与迁移
- [ ] 扩展用户序列化与当前用户接口返回结构
- [ ] 运行 `python manage.py test accounts.tests`
- [ ] 提交：`feat: 增加用户权限配置模型`

## Phase 2: 业务数据范围过滤
- [ ] 写 failing tests，覆盖项目/客户/设备/合同按授权销售过滤
- [ ] 抽出 `accounts/services.py` 统一解析用户授权销售集合
- [ ] 将 `projects/views.py` 的核心列表与 overview 接口接入过滤
- [ ] 运行 `python manage.py test projects.tests accounts.tests`
- [ ] 提交：`feat: 接入按销售的数据权限过滤`

## Phase 3: 系统管理与前端权限控制
- [ ] 写前端权限配置相关最小回归测试或补充可验证工具函数测试
- [ ] 扩展系统管理页面：用户管理、角色动作权限、多选销售范围
- [ ] 扩展 Pinia、路由守卫、左侧菜单动态渲染
- [ ] 将人员类型列表改为中文显示映射
- [ ] 运行 `npm run build`
- [ ] 提交：`feat: 完善系统管理权限配置界面`

## Phase 4: 联调与收尾
- [ ] 全量运行 `python manage.py test`
- [ ] 全量运行 `npm run build`
- [ ] 手工验证超管/普通用户/多销售范围三类场景
- [ ] 提交：`fix: 完成权限控制联调收尾`

# 设备中心 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增独立设备中心模块，统一展示项目中心同步过来的全部设备，并补齐客户公司、客户联系人、销售等字段。

**Architecture:** 后端扩展设备列表/详情序列化字段，复用现有设备数据和项目绑定关系推导展示口径；前端新增独立设备中心页面与路由菜单入口，并复用现有设备详情展示模式。

**Tech Stack:** Django REST Framework、Vue 3、Element Plus、Vite

---

### Task 1: 设备列表接口补充展示字段

**Files:**
- Modify: `backend/projects/serializers.py`
- Modify: `backend/projects/views.py`
- Modify: `backend/projects/tests.py`

- [ ] **Step 1: 先写设备列表与详情字段测试**
- [ ] **Step 2: 运行后端测试确认失败**
- [ ] **Step 3: 扩展序列化与概览返回字段**
- [ ] **Step 4: 运行后端测试确认通过**
- [ ] **Step 5: 运行完整后端测试**

### Task 2: 前端新增设备中心页面与菜单

**Files:**
- Create: `frontend/src/views/DeviceDirectoryView.vue`
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/layouts/AdminLayout.vue`

- [ ] **Step 1: 新建设备中心页面**
- [ ] **Step 2: 接入路由与菜单入口**
- [ ] **Step 3: 接入设备详情弹窗并展示新增字段**
- [ ] **Step 4: 运行前端构建检查**

### Task 3: 提交

**Files:**
- Modify: `backend/projects/serializers.py`
- Modify: `backend/projects/views.py`
- Modify: `backend/projects/tests.py`
- Create: `frontend/src/views/DeviceDirectoryView.vue`
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/layouts/AdminLayout.vue`

- [ ] **Step 1: 分别核对后端与前端改动范围**
- [ ] **Step 2: 使用中文 commit message 提交**

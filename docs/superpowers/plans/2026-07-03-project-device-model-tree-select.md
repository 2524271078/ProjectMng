# 项目设备产品型号树形选择 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将项目中心项目设备弹窗中的产品型号输入从普通下拉改为可按产品目录逐级定位的树形选择器。

**Architecture:** 新增一个前端产品目录树构建工具函数和一个专用树形选择组件，组件加载产品线、产品、版本、型号四类数据并渲染为 `el-tree-select`，项目中心复用该组件替换原有型号下拉。提交值仍保持为型号 id。

**Tech Stack:** Vue 3、Element Plus、Vite、Node test

---

### Task 1: 产品目录树工具函数

**Files:**
- Create: `frontend/src/utils/productModelTree.js`
- Create: `frontend/src/utils/productModelTree.test.js`

- [ ] **Step 1: 写失败测试**
- [ ] **Step 2: 运行测试确认失败**
- [ ] **Step 3: 实现最小树构建逻辑**
- [ ] **Step 4: 运行测试确认通过**

### Task 2: 项目中心产品型号树选择组件

**Files:**
- Create: `frontend/src/components/ProductModelTreeSelect.vue`
- Modify: `frontend/src/views/DeviceCenterView.vue`

- [ ] **Step 1: 接入树组件并替换原有普通下拉**
- [ ] **Step 2: 保持提交值仍为 `device_model` id**
- [ ] **Step 3: 去掉型号编码拼接展示**

### Task 3: 验证与提交

**Files:**
- Modify: `frontend/src/views/DeviceCenterView.vue`
- Create: `frontend/src/components/ProductModelTreeSelect.vue`
- Create: `frontend/src/utils/productModelTree.js`
- Create: `frontend/src/utils/productModelTree.test.js`

- [ ] **Step 1: 运行 `node --test frontend/src/utils/productModelTree.test.js`**
- [ ] **Step 2: 运行 `npm run build`**
- [ ] **Step 3: 提交中文 commit**

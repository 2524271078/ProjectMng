# Project Management System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Django REST Framework and Vue3 project equipment management system that replaces spreadsheet-based maintenance of sales, customer, device, contract, vendor, and procurement-chain data.

**Architecture:** Use a modular Django monolith under `backend/` with `core`, `accounts`, and `projects` apps, backed by SQLite for development and portable field choices for PostgreSQL migration. Use a Vue3/Vite/Element Plus SPA under `frontend/` with route-level pages, reusable API client, Pinia auth store, and enterprise admin layout.

**Tech Stack:** Django, Django REST Framework, django-cors-headers, SQLite, Vue3, Vite, Element Plus, Pinia, Vue Router, Axios.

---

## File Structure

- `backend/requirements.txt`: Python dependencies.
- `backend/manage.py`: Django entrypoint.
- `backend/config/settings.py`: Django settings for installed apps, database, REST framework, CORS, media.
- `backend/config/urls.py`: Admin, auth, and API routing.
- `backend/core/models.py`: Abstract base model and soft-delete manager.
- `backend/accounts/models.py`: Role, Menu, Permission, and UserRole.
- `backend/accounts/api.py`: Auth, current user, and RBAC ViewSets.
- `backend/projects/models.py`: Organization, Person, SalesCustomerRelation, Product, DeviceModel, Device, Contract, ContractDevice, ContractParty, Attachment, AuditLog.
- `backend/projects/serializers.py`: DRF serializers for business models.
- `backend/projects/views.py`: CRUD ViewSets and business overview endpoints.
- `backend/projects/tests.py`: Model and API workflow tests.
- `frontend/package.json`: Vite commands and dependencies.
- `frontend/src/api/`: Axios client and domain API modules.
- `frontend/src/router/`: Route definitions.
- `frontend/src/stores/`: Auth and menu store.
- `frontend/src/layouts/AdminLayout.vue`: Enterprise backend layout.
- `frontend/src/views/`: Login, dashboard, customer, device, sales, contract, product, person, system pages.
- `docs/`: Setup and workflow documentation.

## Tasks

### Task 1: Documentation Baseline

**Files:**
- Create: `docs/superpowers/specs/2026-07-02-project-management-system-design.md`
- Create: `docs/superpowers/plans/2026-07-02-project-management-system.md`

- [ ] Write design and implementation plan documents.
- [ ] Run `git status --short --branch` to confirm only docs are staged for this task.
- [ ] Commit with `docs: 添加项目设备管理系统设计和实施计划`.

### Task 2: Project Structure

**Files:**
- Create: `.gitignore`
- Create: `README.md`
- Create: `backend/.gitkeep`
- Create: `frontend/.gitkeep`
- Create: `docs/.gitkeep`

- [ ] Add top-level project directories.
- [ ] Add ignore rules for Python caches, virtualenvs, SQLite databases, media uploads, node modules, Vite output, and IDE files.
- [ ] Add README with backend/frontend startup outline.
- [ ] Run `git status --short --branch`.
- [ ] Commit with `chore: 搭建项目基础目录结构`.

### Task 3: Backend Foundation

**Files:**
- Create Django project and apps under `backend/`.
- Create: `backend/requirements.txt`
- Create: `backend/core/models.py`
- Create: `backend/core/tests.py`

- [ ] Install or use available Django dependencies.
- [ ] Write failing tests for base model metadata and soft-delete manager behavior.
- [ ] Implement backend settings, URL routing, DRF config, CORS, media, and core base model.
- [ ] Run `python manage.py test`.
- [ ] Commit with `feat: 添加后端基础工程`.

### Task 4: Backend Domain Models

**Files:**
- Create/modify: `backend/projects/models.py`
- Create/modify: `backend/projects/tests.py`
- Create migrations in `backend/projects/migrations/`

- [ ] Write failing tests for organization/person/device/contract relationship creation and common extensibility fields.
- [ ] Implement all required models and indexes.
- [ ] Generate migrations.
- [ ] Run `python manage.py test`.
- [ ] Commit with `feat: 添加核心业务模型`.

### Task 5: Backend API and RBAC

**Files:**
- Create/modify: `backend/accounts/models.py`
- Create/modify: `backend/accounts/api.py`
- Create/modify: `backend/projects/serializers.py`
- Create/modify: `backend/projects/views.py`
- Create/modify: `backend/config/urls.py`
- Create/modify tests under `backend/accounts/tests.py` and `backend/projects/tests.py`

- [ ] Write failing API tests for login/current user, menus, CRUD, and workflow overview endpoints.
- [ ] Implement role/menu/permission models, serializers, routers, token auth, and business endpoints.
- [ ] Run `python manage.py test`.
- [ ] Commit with `feat: 添加后端接口和权限基础`.

### Task 6: Frontend Foundation

**Files:**
- Create Vue/Vite app under `frontend/`.
- Create: `frontend/src/api/client.js`
- Create: `frontend/src/stores/auth.js`
- Create: `frontend/src/router/index.js`
- Create: `frontend/src/layouts/AdminLayout.vue`
- Create: `frontend/src/views/LoginView.vue`
- Create: `frontend/src/views/DashboardView.vue`

- [ ] Add Vite, Vue3, Element Plus, Pinia, Router, Axios dependencies.
- [ ] Implement login page, auth store, admin shell, dashboard, and API client.
- [ ] Run `npm run build`.
- [ ] Commit with `feat: 添加前端基础工程`.

### Task 7: Frontend Business Pages

**Files:**
- Create/modify views in `frontend/src/views/`.
- Create/modify domain API modules in `frontend/src/api/`.

- [ ] Add customer center with organization tree and detail tabs.
- [ ] Add device center list, form dialog, detail tabs, image upload, contract binding placeholder workflow.
- [ ] Add sales center drill-down from sales to customers to devices/contracts.
- [ ] Add contract center list, detail, parties chain, and bound devices.
- [ ] Add product/model and person management pages.
- [ ] Run `npm run build` before each page-group commit.
- [ ] Commit page groups with Chinese messages.

### Task 8: System Management

**Files:**
- Create/modify system views and API modules in `frontend/src/views/system/`.
- Modify backend API tests if system endpoints need coverage.

- [ ] Add user management, role management, menu permission, and audit log pages.
- [ ] Run backend tests if backend changes were made.
- [ ] Run `npm run build`.
- [ ] Commit with `feat: 添加系统管理页面`.

### Task 9: Final Documentation and Verification

**Files:**
- Modify: `README.md`
- Create: `docs/workflow.md`
- Create: `docs/api.md`

- [ ] Document environment setup, migrations, admin creation, backend run command, frontend run command, and business workflow.
- [ ] Run `python manage.py test`.
- [ ] Run `npm run build`.
- [ ] Commit with `docs: 添加部署和业务流程说明`.

## Self-Review

- Spec coverage: The plan covers repository structure, backend models, API/RBAC, business workflow queries, frontend pages, system management, tests, builds, and documentation.
- Placeholder scan: No task uses unresolved placeholders; page-level items are grouped but each has a concrete target and verification command.
- Type consistency: Model and endpoint names match the design document and user requirements.

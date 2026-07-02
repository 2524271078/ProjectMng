# 项目设备管理系统设计

## 目标

构建一个前后端分离的项目设备管理系统，用于替代在线表格维护销售、客户、设备、合同、厂商、采购链路和现场运维信息的方式。第一阶段重点跑通基础业务流程：新增组织、人员、销售客户关系、产品型号、设备、合同，并支持按销售、客户、设备、合同维度查询关联信息。

## 架构

系统采用 Django + Django REST Framework 提供后端 API，Vue3 + Vite + Element Plus 提供企业后台前端。开发阶段使用 SQLite，模型字段避免 SQLite 专属特性，后续可切换 PostgreSQL。后端采用模块化单体，先保证数据模型、权限、审计和业务查询一致，后续如统计、审批、数据权限复杂化再拆分服务。

## 后端设计

后端目录为 `backend/`，包含 Django 项目 `config` 和业务应用：

- `core`：通用基类、审计字段、软删除查询集。
- `accounts`：角色、菜单、功能权限、用户角色关系和当前用户权限接口。
- `projects`：组织、人员、销售客户关系、产品、型号、设备、合同、附件、审计日志。

所有业务表统一保留 `remark`、`status`、`extra`、`created_at`、`updated_at`、`created_by`、`updated_by`、`is_deleted` 字段。软删除第一阶段只在模型层预留，API 默认过滤 `is_deleted=False`。

## 数据模型

组织主体统一进入 `Organization`，通过 `org_type` 区分客户、厂商、第三方中标单位、集成商、内部公司等。人员统一进入 `Person`，通过 `person_type` 区分销售、客户联系人、内部人员、现场运维人员、厂商联系人等。

设备以 `Product`、`DeviceModel`、`Device` 三层组织。合同以 `Contract` 表示合同主数据，`ContractParty` 表示参与方和采购链路，`ContractDevice` 表示合同和设备的绑定关系。

## API 设计

基础 CRUD 使用 DRF ViewSet。业务查询接口包含：

- `/api/sales/{id}/customers/`：销售负责客户。
- `/api/customers/{id}/overview/`：客户联系人、负责销售、设备、合同。
- `/api/devices/{id}/overview/`：设备基础、授权、客户、合同、附件。
- `/api/contracts/{id}/overview/`：合同参与方链路和绑定设备。

认证第一阶段使用 DRF Token 认证，登录后前端持有 token。RBAC 第一阶段提供角色、菜单、权限点和用户角色绑定，前端根据当前用户菜单权限渲染菜单。

## 前端设计

前端目录为 `frontend/`，采用 Vue3、Vite、Element Plus、Vue Router、Pinia、Axios。界面采用企业后台风格：

- 登录页。
- 顶部导航 + 左侧菜单 + 内容区布局。
- 首页工作台显示第一阶段流程入口。
- 客户中心采用左侧组织树和右侧详情 Tabs。
- 设备详情展示基础信息、授权信息、合同信息、客户信息和图片附件。
- 销售中心支持从销售进入客户，再进入客户设备和合同。
- 合同中心支持参与方链路和设备绑定。
- 系统管理支持用户、角色、菜单权限和操作日志。

## 测试和提交策略

每个后端模块提交前执行 `python manage.py test`。每个前端模块提交前执行 `npm run build`。提交信息使用中文描述。每个功能模块独立提交，避免把后端、前端和文档混在一个大提交里。

## 第一阶段范围

第一阶段不实现复杂统计看板、审批流、复杂数据权限和工作流引擎。系统保留字段和表关系扩展能力，优先保证主流程可运行、数据可维护、关联可查询。

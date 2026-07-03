# 项目中心与客户中心关联设计

## 背景

当前系统已经具备以下基础关系：

- `Project.customer_org`：项目归属客户公司
- `Project.customer_contact`：项目联系人
- `Project.sales_person`：项目销售
- `ProjectDevice`：项目与设备绑定

但现有前后端还没有把“项目创建后自动归属客户，并能在客户中心反查项目”的链路完整打通：

- 项目中心是新建项目入口，但客户中心没有展示客户名下项目
- 项目详情里设备绑定仍使用全量设备候选，没有按客户过滤
- 项目和合同之间没有独立的业务关联模型，当前页面把“合同和附件”混在同一个 tab 中

本次调整目标是保持“项目中心为主入口，客户中心做反查展示”的结构不变，在现有代码基础上补全关联链路。

## 目标

实现以下业务行为：

1. 在项目中心新建项目时，选择客户公司、客户联系人、销售，项目保存后自动归属到该客户公司
2. 在客户中心查看客户时，可以看到该客户名下的项目列表
3. 项目中心绑定设备时，优先使用当前客户名下的已购设备；新建设备时自动归属到当前客户
4. 项目中心支持维护项目与已有合同的关联
5. 项目中心详情页将“关联合同”和“项目附件”分开展示

## 非目标

本次不做以下内容：

- 不改变“客户中心”和“项目中心”的模块边界
- 不把项目创建入口迁移到客户中心
- 不重构现有权限模型
- 不引入复杂的多级项目导航或新的独立项目页面

## 现状分析

### 前端现状

客户中心 `frontend/src/views/CustomerCenterView.vue` 当前 tab：

- 客户详情
- 联系人
- 负责销售
- 已购设备
- 关联合同

项目中心 `frontend/src/views/DeviceCenterView.vue` 当前 tab：

- 基础信息
- 项目设备
- 合同和附件

现有问题：

- 客户中心缺少“关联项目”视图
- 项目中心设备候选来自全量 `devices`
- 项目详情没有“项目合同”的独立数据区
- “合同和附件”混合在同一个 tab，语义不清晰

### 后端现状

后端 `customer_overview` 已返回：

- `customer`
- `contacts`
- `sales`
- `devices`
- `contracts`

但未返回 `projects`。

后端 `project_overview` 已返回：

- `project`
- `customer`
- `customer_contact`
- `sales_person`
- `ops_person`
- `devices`
- `attachments`

但未返回 `contracts`。

此外，项目和合同之间没有独立关联表。

## 推荐方案

采用“项目中心维护，客户中心反查”的方案。

### 方案说明

1. 项目中心继续作为创建项目的唯一主入口
2. 项目保存时写入 `customer_org`、`customer_contact`、`sales_person`
3. 客户中心新增“关联项目” tab，展示客户名下项目列表
4. 项目中心设备绑定候选按当前项目所属客户过滤
5. 新增项目与合同的关联模型 `ProjectContract`
6. 项目详情单独提供“关联合同”和“项目附件”两个 tab

### 选择原因

- 完全符合现有页面结构
- 复用现有 `Project`、`ProjectDevice`、`customer_overview`、`project_overview`
- 改动集中，风险较低
- 后续如果要在客户中心查看项目详情，也可以复用项目详情接口

## 备选方案

### 方案 A：客户中心直接展开项目及其设备、合同

优点：

- 客户全景信息更完整

缺点：

- 客户中心会变得过重
- 页面层级过深，列表嵌套复杂
- 与当前“详情抽屉 + tab”结构不一致

### 方案 B：把项目创建入口迁移到客户中心

优点：

- 从业务语义上更贴近“客户名下新建项目”

缺点：

- 需要重构现有项目中心职责
- 与用户当前使用路径不一致
- 前后端现有代码复用度更低

最终不采用以上两种方案。

## 详细设计

### 一、数据模型

#### 1. 保持现有项目归属字段

继续使用现有字段表达项目归属：

- `Project.customer_org`
- `Project.customer_contact`
- `Project.sales_person`

无需为“客户-项目归属”额外新增关联表。

#### 2. 新增项目合同关联模型

新增模型 `ProjectContract`，用于关联已有合同到项目。

建议字段：

- `project`：外键，指向 `Project`
- `contract`：外键，指向 `Contract`
- `remark`：备注
- `status` / `extra` / `created_at` / `updated_at` / `created_by` / `updated_by` / `is_deleted`

约束：

- 项目与合同的有效关联应唯一
- 采用与现有业务模型一致的软删除风格

作用：

- 明确项目和合同的业务关联
- 避免把合同附件错误当成项目合同关系

### 二、后端接口

#### 1. 扩展 `customer_overview`

在现有返回结构中新增 `projects` 字段。

建议返回轻量项目摘要：

- `id`
- `project_no`
- `name`
- `project_stage`
- `amount`
- `sales_person`
- `customer_contact`

用途：

- 客户中心展示客户名下所有项目
- 避免客户中心一次性展开完整项目详情

#### 2. 扩展 `project_overview`

在现有返回结构中新增 `contracts` 字段。

返回项目当前已关联合同的摘要信息：

- `id`
- `contract_no`
- `contract_name`
- `amount`
- `status`

#### 3. 新增 `ProjectContract` CRUD 接口

为 `ProjectContract` 提供标准资源接口，例如：

- `/api/project-contracts/`

前端使用该接口完成：

- 为项目绑定已有合同
- 查询项目已关联合同
- 移除项目合同关联

### 三、前端交互

#### 1. 客户中心

在 `CustomerCenterView.vue` 中新增 `关联项目` tab。

展示方式：

- 表格列出该客户名下项目
- 默认展示项目编号、项目名称、阶段、销售、金额
- 点击项目行后，打开项目详情抽屉或复用项目详情视图

建议不在客户中心直接展开项目设备和合同明细，避免页面过重。

#### 2. 项目中心

在 `DeviceCenterView.vue` 中保留项目创建入口。

创建项目时：

- 先选择客户公司
- 根据客户公司加载联系人候选
- 选择销售
- 保存后项目归属该客户公司

#### 3. 项目设备候选过滤

打开项目详情后，根据当前项目的 `customer_org` 过滤设备候选。

规则：

- 选择已有设备时，只展示 `customer_org = 当前项目客户` 的设备
- 若当前客户下没有设备，允许切换到“新建设备”
- 新建设备成功后，自动写入：
  - `customer_org = 当前项目客户`
  - `sales_person = 当前项目销售`（若存在）

#### 4. 项目详情 tab 调整

将当前项目详情 tab 从：

- 基础信息
- 项目设备
- 合同和附件

调整为：

- 基础信息
- 项目设备
- 关联合同
- 项目附件

这样“合同”作为业务对象，“附件”作为文件对象，边界更清晰。

### 四、数据流

#### 新建项目

1. 用户在项目中心输入项目基础信息
2. 选择客户公司
3. 前端根据客户公司加载联系人
4. 用户选择联系人和销售
5. 调用 `/api/projects/` 创建项目
6. 项目保存 `customer_org`、`customer_contact`、`sales_person`

#### 客户中心查看项目

1. 用户在客户中心选中一个客户
2. 前端调用 `/api/customers/{id}/overview/`
3. 接口返回客户详情、联系人、销售、设备、合同、项目
4. 前端在“关联项目” tab 中展示项目列表

#### 项目绑定设备

1. 用户打开项目详情
2. 前端获取项目所属客户
3. 设备候选按客户过滤
4. 若绑定已有设备，直接写入 `ProjectDevice`
5. 若新建设备，先创建 `Device`，再写入 `ProjectDevice`

#### 项目关联合同

1. 用户打开项目详情的“关联合同” tab
2. 前端加载客户相关合同候选
3. 用户选择已有合同并绑定到项目
4. 前端调用 `/api/project-contracts/`
5. `project_overview` 返回最新的项目合同列表

## 错误处理

- 若项目未选择客户公司，则不允许加载客户联系人
- 若客户已选择但没有联系人，允许项目先保存，但界面应明确提示无联系人可选
- 若客户下没有设备，已有设备下拉为空，并提示切换到“新建设备”
- 若尝试重复绑定同一合同到同一项目，后端返回唯一性错误，前端提示“合同已关联”
- 若客户已切换，应清空之前选中的联系人、设备候选和合同候选

## 测试策略

### 后端测试

新增或扩展以下测试：

- `customer_overview` 返回客户名下项目
- `project_overview` 返回项目已关联合同
- `ProjectContract` 唯一性与软删除行为
- 新建设备后设备归属到项目客户

### 前端测试

优先补工具和数据处理层测试，必要时补组件行为测试：

- 客户切换后联系人候选重置
- 项目设备候选按客户过滤
- 新建设备时自动带上客户归属字段
- 项目详情 tab 数据渲染正确

## 实施顺序

1. 后端扩展 `customer_overview.projects`
2. 客户中心新增“关联项目” tab
3. 项目中心设备候选按客户过滤
4. 新增 `ProjectContract` 模型、序列化器、视图和路由
5. 后端扩展 `project_overview.contracts`
6. 项目中心拆分“关联合同”和“项目附件” tab

## 影响范围

后端：

- `backend/projects/models.py`
- `backend/projects/serializers.py`
- `backend/projects/views.py`
- `backend/config/urls.py`
- `backend/projects/tests.py`
- 新 migration 文件

前端：

- `frontend/src/views/CustomerCenterView.vue`
- `frontend/src/views/DeviceCenterView.vue`
- `frontend/src/api/resources.js`
- 可能新增小型工具函数或数据映射逻辑

## 结论

本方案以最小改动完成“项目归属客户、客户反查项目”的业务闭环，保持项目中心为主入口，不打乱现有模块边界，同时为后续项目合同关联能力留出明确的数据模型。

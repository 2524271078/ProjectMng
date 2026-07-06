# 权限控制设计方案

## 目标
在现有项目设备管理系统中补齐账号、角色、菜单权限与按销售维度的数据权限。第一版支持超管全量访问，普通用户按角色控制菜单，按用户单独配置可查看的销售人员范围，且销售范围支持多选。

## 现状
- 认证基于 `django.contrib.auth.User` + Token。
- 业务人员基于 `projects.Person`，已有 `Person.user` 可绑定登录账号。
- 已有角色、菜单、权限、用户角色基础表：`accounts.Role/Menu/Permission/UserRole`。
- 核心业务表已有销售归属字段：`Project.sales_person`、`Device.sales_person`、`Contract.sales_person`。

## 第一版权限模型

### 1. 账号层
- 超管：使用 `User.is_superuser` 表示，拥有全部菜单、全部动作、全部数据。
- 普通用户：通过角色和数据范围配置决定访问能力。

### 2. 功能权限
- 角色负责菜单与动作权限。
- `Permission.action` 扩展为标准动作集合：`view/create/edit/delete`。
- 前端菜单按当前用户可见菜单渲染；后端接口再按动作权限校验。

### 3. 数据权限
新增用户级数据范围配置，不放进角色。

#### 新增表 `accounts.UserAccessProfile`
- `user`：OneToOne 到 `auth.User`
- `person`：OneToOne/ForeignKey 到 `projects.Person`，表示登录账号绑定的业务人员
- `data_scope_type`：`all/self/custom`
- `remark/status` 与现有风格一致

#### 新增表 `accounts.UserSalesScope`
- `profile`：外键到 `UserAccessProfile`
- `sales_person`：外键到 `projects.Person`，要求 `person_type=sales`
- 唯一约束：一个 profile 下同一销售只能配置一次

### 4. 数据范围语义
- `all`：可看全部业务数据
- `self`：根据 profile 绑定的 `person`，仅看该销售本人数据
- `custom`：按 `UserSalesScope` 多选销售集合过滤

## 过滤规则

### 项目中心
按 `Project.sales_person` 过滤。

### 合同中心
按 `Contract.sales_person` 过滤。

### 设备中心
优先按 `Device.sales_person` 过滤；若设备未直接绑定销售，则回退到最近项目绑定的 `Project.sales_person`。

### 客户中心
客户列表与详情按 `SalesCustomerRelation.sales_person` 过滤，只有与授权销售存在关系的客户可见；客户下的联系人、设备、项目、合同都建立在可见客户集合上。

### 销售中心
普通用户只能看到被授权销售集合；超管可看全部。

## 后端实现边界
- 抽象统一的动作权限判断函数，避免散落在单个 ViewSet 中。
- 抽象统一的数据范围服务：输入当前用户，输出授权销售 ID 集合与 scope 类型。
- 各业务 ViewSet 在 `get_queryset` 中复用统一过滤逻辑。
- `/api/auth/me/` 返回：用户基础信息、角色、菜单、动作权限、绑定人员、数据范围摘要。

## 前端实现边界

### 人员管理
- 列表中的 `person_type` 使用中文映射显示，底层仍保存英文 code。
- 保持业务人员档案管理职责，不承载登录账号和菜单配置。

### 系统管理
新增/完善四块：
1. 用户管理
   - 创建账号、启停、重置密码
   - 绑定业务人员
   - 分配角色
   - 配置数据范围类型
   - 多选授权销售
2. 角色管理
   - 新增/编辑/删除角色
   - 配置角色菜单与动作权限
3. 菜单管理
   - 维护菜单基础信息
4. 审计日志
   - 先保持只读

### 菜单控制
- 前端路由守卫增加按菜单 code 校验。
- 左侧导航按当前用户 `menus` 动态显示。
- 页面内按钮按动作权限决定是否显示。

## 扩展预留
- 数据范围先按销售做，后续可扩展组织、区域、客户、项目阶段。
- 数据权限为用户级，后续可加角色默认范围，但不覆盖第一版模型。
- 动作权限预留 `export/audit/assign` 等自定义动作。

## 风险与约束
- 设备归属销售存在“设备自身销售为空”的情况，必须保留项目回退逻辑。
- 客户中心权限依赖 `SalesCustomerRelation` 数据质量；若没有维护关系，普通用户可能看不到客户。
- 超管账号建议使用 `is_superuser=True`，避免再发明第二套最高权限标记。

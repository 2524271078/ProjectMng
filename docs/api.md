# API 说明

默认后端地址：`http://127.0.0.1:8000/api/`

## 认证

- `POST /api/auth/login/`：传入 `username`、`password`，返回 DRF Token。
- `GET /api/auth/me/`：返回当前用户、菜单和权限点。

前端请求头：`Authorization: Token <token>`。

## 基础 CRUD

- `/api/organizations/`：组织，统一维护客户、厂商、第三方中标单位、集成商、内部公司。
- `/api/people/`：人员，统一维护销售、客户联系人、内部人员、现场运维人员、厂商联系人。
- `/api/sales-customer-relations/`：销售客户负责关系。
- `/api/products/`：产品。
- `/api/device-models/`：设备型号。
- `/api/devices/`：设备实例。
- `/api/contracts/`：合同。
- `/api/contract-parties/`：合同参与方和采购链路。
- `/api/contract-devices/`：合同绑定设备。
- `/api/attachments/`：附件。
- `/api/audit-logs/`：操作日志只读接口。

## 业务查询

- `GET /api/sales/{id}/customers/`：销售负责客户，以及客户下设备和合同摘要。
- `GET /api/customers/{id}/overview/`：客户详情、联系人、负责销售、已购设备、关联合同。
- `GET /api/devices/{id}/overview/`：设备基础信息、授权信息、客户、销售、运维、合同、附件。
- `GET /api/contracts/{id}/overview/`：合同详情、参与方链路、绑定设备。

## RBAC

- `/api/users/`：用户管理。
- `/api/roles/`：角色管理。
- `/api/menus/`：菜单管理。
- `/api/permissions/`：角色菜单功能权限。
- `/api/user-roles/`：用户角色绑定。

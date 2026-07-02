<template>
  <div class="dashboard">
    <el-row :gutter="18">
      <el-col v-for="item in cards" :key="item.title" :xs="24" :sm="12" :lg="6">
        <div class="metric-card">
          <span>{{ item.label }}</span>
          <strong>{{ item.title }}</strong>
          <p>{{ item.desc }}</p>
        </div>
      </el-col>
    </el-row>
    <el-card class="flow-card" shadow="never">
      <template #header>第一阶段主流程</template>
      <el-steps :active="3" finish-status="success" align-center>
        <el-step title="组织人员" description="客户、厂商、联系人" />
        <el-step title="销售关系" description="销售负责客户" />
        <el-step title="设备资产" description="产品、型号、设备" />
        <el-step title="合同链路" description="参与方与设备绑定" />
      </el-steps>
    </el-card>
  </div>
</template>

<script setup>
const cards = [
  { label: 'Customer', title: '客户中心', desc: '组织树、联系人、销售、设备、合同' },
  { label: 'Device', title: '设备中心', desc: '设备实例、授权、图片、合同绑定' },
  { label: 'Sales', title: '销售中心', desc: '查看销售负责客户和设备合同' },
  { label: 'Contract', title: '合同中心', desc: '合同参与方链路和采购路径' },
]
</script>

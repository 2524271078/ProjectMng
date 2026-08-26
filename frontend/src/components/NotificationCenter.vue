<template>
  <div class="notification-center">
    <el-popover
      v-model:visible="visible"
      trigger="click"
      placement="right-end"
      :width="620"
      :offset="18"
      :show-arrow="false"
      :teleported="true"
      popper-class="notification-popover"
      @show="loadReminders"
    >
      <template #reference>
        <button class="notification-trigger" type="button" title="待办提醒">
          <el-badge class="notification-trigger__badge" :value="reminders.length > 99 ? '99+' : reminders.length" :hidden="!reminders.length" :max="99">
            <span class="notification-trigger__icon"><el-icon><Bell /></el-icon></span>
          </el-badge>
          <span class="notification-trigger__text"><strong>待办提醒</strong><small>服务与到期提醒</small></span>
        </button>
      </template>

      <section class="notification-panel">
        <header class="notification-panel__header">
          <div>
            <h2>待办提醒</h2>
            <p>{{ reminders.length }} 条待处理事项</p>
          </div>
          <el-button circle text title="刷新提醒" :loading="loading" @click="loadReminders">
            <el-icon><Refresh /></el-icon>
          </el-button>
        </header>

        <nav class="notification-filter" aria-label="待办分类">
          <button :class="{ 'is-active': activeFilter === 'all' }" type="button" @click="activeFilter = 'all'">全部</button>
          <button :class="{ 'is-active': activeFilter === 'service_task' }" type="button" @click="activeFilter = 'service_task'">服务任务</button>
          <button :class="{ 'is-active': activeFilter === 'service_expiring' }" type="button" @click="activeFilter = 'service_expiring'">即将到期</button>
        </nav>

        <main v-loading="loading" class="notification-panel__body">
          <el-empty v-if="!loading && !filteredReminders.length" description="暂无待办提醒" :image-size="76" />
          <div v-else class="notification-list">
            <article v-for="item in filteredReminders" :key="item.key" class="notification-item" :class="`notification-item--${item.type}`">
              <div class="notification-item__icon"><el-icon><Bell /></el-icon></div>
              <div class="notification-item__content">
                <div class="notification-item__meta">
                  <span>{{ reminderTypeLabel(item.type) }}</span>
                  <time>{{ item.target_date }}</time>
                </div>
                <p>{{ item.content }}</p>
                <footer>
                  <span>{{ daysLeftLabel(item.days_left) }}</span>
                  <el-button link type="primary" @click="confirmReminder(item)">确认处理</el-button>
                </footer>
              </div>
            </article>
          </div>
        </main>
        <footer class="notification-panel__footer">共 {{ filteredReminders.length }} 条待办</footer>
      </section>
    </el-popover>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Bell, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { confirmDashboardReminder, fetchDashboardReminders } from '../api/resources'
import { formatApiError, unwrapList } from '../utils/apiData'

const visible = ref(false)
const loading = ref(false)
const reminders = ref([])
const activeFilter = ref('all')
const filteredReminders = computed(() => reminders.value.filter((item) => (
  activeFilter.value === 'all' || item.type === activeFilter.value
)))

async function loadReminders() {
  loading.value = true
  try {
    const { data } = await fetchDashboardReminders()
    reminders.value = unwrapList(data)
  } catch (error) {
    ElMessage.error(formatApiError(error, '加载待办提醒失败'))
  } finally {
    loading.value = false
  }
}

async function confirmReminder(reminder) {
  try {
    await confirmDashboardReminder(reminder.key)
    reminders.value = reminders.value.filter((item) => item.key !== reminder.key)
    ElMessage.success('待办已确认并隐藏')
  } catch (error) {
    ElMessage.error(formatApiError(error, '确认待办失败'))
  }
}

function reminderTypeLabel(type) {
  return type === 'service_expiring' ? '服务即将到期' : '服务任务'
}

function daysLeftLabel(daysLeft) {
  return daysLeft < 0 ? `逾期 ${Math.abs(daysLeft)} 天` : `剩余 ${daysLeft} 天`
}

onMounted(loadReminders)
</script>

<style scoped>
.notification-center { flex-shrink: 0; margin: 12px 4px 2px; }
.notification-trigger { display: flex; width: 100%; min-height: 72px; align-items: center; gap: 10px; padding: 10px 12px; border: 1px solid #cfe0ff; border-radius: 16px; background: #fff; box-shadow: 0 5px 14px rgb(91 124 250 / 10%), inset 0 0 0 2px rgb(238 245 255 / 75%); color: var(--app-text); cursor: pointer; text-align: left; transition: border-color var(--app-transition), box-shadow var(--app-transition), transform var(--app-transition); }
.notification-trigger:hover { border-color: #aec6ff; box-shadow: 0 8px 18px rgb(91 124 250 / 16%), inset 0 0 0 2px rgb(255 255 255 / 70%); transform: translateY(-1px); }
.notification-trigger__icon { display: grid; width: 40px; height: 40px; place-items: center; border: 1px solid #cfe0ff; border-radius: 50%; background: #e8f0ff; color: var(--app-primary); }
.notification-trigger__icon :deep(.el-icon) { font-size: 21px; }
.notification-trigger__badge :deep(.el-badge__content) { top: 2px; right: 8px; min-width: 28px; height: 20px; border: 2px solid #fff; border-radius: 10px; background: #f06a6a; font-size: 10px; font-weight: 700; line-height: 16px; }
.notification-trigger__text { display: grid; min-width: 0; gap: 4px; }
.notification-trigger__text strong { color: var(--app-ink); font-size: 14px; font-weight: 680; }
.notification-trigger__text small { overflow: hidden; color: var(--app-subtle); font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }

.notification-panel { display: flex; height: min(780px, calc(100vh - 112px)); min-height: 440px; flex-direction: column; background: #fff; }
.notification-panel__header { display: flex; align-items: flex-start; justify-content: space-between; padding: 26px 28px 16px; }
.notification-panel__header h2 { margin: 0; color: var(--app-ink); font-size: 23px; font-weight: 700; letter-spacing: -.025em; }
.notification-panel__header p { margin: 7px 0 0; color: var(--app-subtle); font-size: 13px; }
.notification-filter { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0; padding: 0 28px 14px; border-bottom: 1px solid var(--app-border); }
.notification-filter button { height: 36px; border: 0; border-radius: var(--app-radius-sm); background: transparent; color: var(--app-text); cursor: pointer; font-size: 14px; transition: color var(--app-transition), background var(--app-transition), box-shadow var(--app-transition); }
.notification-filter button.is-active { background: #fff; box-shadow: 0 2px 8px rgb(63 94 135 / 10%); color: var(--app-ink); font-weight: 680; }
.notification-panel__body { flex: 1; min-height: 0; padding: 16px 18px; overflow: auto; background: #f8fbff; }
.notification-list { display: grid; gap: 12px; }
.notification-item { display: flex; gap: 14px; padding: 18px; border: 1px solid #d7e3ff; border-radius: 16px; background: #f3f7ff; }
.notification-item--service_expiring { border-color: #fae3c3; background: #fffaf2; }
.notification-item__icon { display: grid; width: 42px; height: 42px; flex: 0 0 auto; place-items: center; border: 1px solid #ffd1d1; border-radius: 13px; background: #fff0f0; color: #f06a6a; }
.notification-item--service_expiring .notification-item__icon { background: #fff1df; color: #d59642; }
.notification-item__content { min-width: 0; flex: 1; }
.notification-item__meta, .notification-item footer { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.notification-item__meta span { color: #f06a6a; font-size: 13px; font-weight: 680; }
.notification-item__meta time { color: var(--app-subtle); font-size: 12px; white-space: nowrap; }
.notification-item p { display: -webkit-box; margin: 8px 0 10px; overflow: hidden; color: var(--app-ink); font-size: 15px; font-weight: 680; line-height: 1.55; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }
.notification-item footer { color: var(--app-subtle); font-size: 12px; }
.notification-item footer .el-button { font-size: 12px; }
.notification-panel__footer { padding: 16px 28px; border-top: 1px solid var(--app-border); background: #fff; color: var(--app-subtle); font-size: 13px; }

:global(.notification-popover.el-popper) { padding: 0; border: 1px solid #dbe7f8; border-radius: 18px; box-shadow: 0 18px 42px rgb(39 68 112 / 16%); overflow: hidden; }
@media (max-width: 720px) { .notification-panel { height: min(720px, calc(100vh - 80px)); } .notification-panel__header { padding-right: 18px; padding-left: 18px; } .notification-filter, .notification-panel__footer { padding-right: 18px; padding-left: 18px; } .notification-panel__body { padding: 12px; } }
</style>

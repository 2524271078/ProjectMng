from django.core.management.base import BaseCommand
from django.utils import timezone

from projects.models import DeviceServicePlan
from projects.services import generate_inspection_tasks, refresh_inspection_task_statuses


class Command(BaseCommand):
    help = "生成设备巡检任务、刷新逾期状态并输出待提醒任务"

    def handle(self, *args, **options):
        created = sum(generate_inspection_tasks(plan) for plan in DeviceServicePlan.objects.filter(auto_generate_tasks=True))
        reminders = refresh_inspection_task_statuses()
        self.stdout.write(f"{timezone.localdate()}：新增巡检任务 {created} 条，待提醒 {reminders.count()} 条。")
        for task in reminders.select_related("service_plan__project_device__device"):
            device = task.service_plan.project_device.device
            self.stdout.write(f"- {device.serial_number}：计划巡检 {task.planned_date}，状态 {task.get_status_display()}")

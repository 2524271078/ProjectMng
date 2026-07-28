from calendar import monthrange
from datetime import timedelta

from django.utils import timezone

from projects.models import InspectionTask, ServiceStandardTemplate


def add_months(value, months):
    target_month = value.month - 1 + months
    target_year = value.year + target_month // 12
    target_month = target_month % 12 + 1
    return value.replace(year=target_year, month=target_month, day=min(value.day, monthrange(target_year, target_month)[1]))


def next_inspection_date(value, plan):
    frequency_months = {
        ServiceStandardTemplate.INSPECTION_MONTHLY: 1,
        ServiceStandardTemplate.INSPECTION_QUARTERLY: 3,
        ServiceStandardTemplate.INSPECTION_SEMIANNUAL: 6,
        ServiceStandardTemplate.INSPECTION_ANNUAL: 12,
    }
    months = frequency_months.get(plan.inspection_frequency)
    if months:
        return add_months(value, months)
    if plan.inspection_frequency == ServiceStandardTemplate.INSPECTION_CUSTOM and plan.inspection_interval_days:
        return value + timedelta(days=plan.inspection_interval_days)
    return None


def generate_inspection_tasks(plan):
    """按已生效的服务规则补齐巡检任务；重复运行不会重复创建。"""
    binding = plan.project_device
    if not plan.auto_generate_tasks or "inspection" not in plan.service_contents:
        return 0
    if not binding.service_start_date or not binding.service_end_date:
        return 0

    planned_date = plan.first_inspection_date or binding.service_start_date
    created_count = 0
    while planned_date and planned_date <= binding.service_end_date:
        reminder_date = planned_date - timedelta(days=plan.reminder_days)
        _, created = InspectionTask.all_objects.get_or_create(
            service_plan=plan,
            planned_date=planned_date,
            defaults={
                "assignee": plan.ops_person,
                "reminder_date": reminder_date,
                "status": InspectionTask.STATUS_PENDING,
            },
        )
        created_count += int(created)
        planned_date = next_inspection_date(planned_date, plan)
    return created_count


def refresh_inspection_task_statuses(today=None):
    """标记逾期任务并返回应提醒的任务，用于每日调度。"""
    today = today or timezone.localdate()
    InspectionTask.objects.filter(
        status=InspectionTask.STATUS_PENDING,
        planned_date__lt=today,
    ).update(status=InspectionTask.STATUS_OVERDUE)
    return InspectionTask.objects.filter(
        status__in=[InspectionTask.STATUS_PENDING, InspectionTask.STATUS_OVERDUE],
        reminder_date__lte=today,
        reminder_sent_at__isnull=True,
    )

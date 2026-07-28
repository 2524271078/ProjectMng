from calendar import monthrange
from datetime import timedelta

from django.db import migrations


def add_months(value, months):
    target_month = value.month - 1 + months
    target_year = value.year + target_month // 12
    target_month = target_month % 12 + 1
    return value.replace(year=target_year, month=target_month, day=min(value.day, monthrange(target_year, target_month)[1]))


def next_date(value, schedule):
    frequency_months = {
        'monthly': 1,
        'quarterly': 3,
        'semiannual': 6,
        'annual': 12,
    }
    months = frequency_months.get(schedule.frequency)
    if months:
        return add_months(value, months)
    if schedule.frequency == 'custom' and schedule.interval_days:
        return value + timedelta(days=schedule.interval_days)
    return None


def create_missing_service_schedules(apps, schema_editor):
    DeviceServicePlan = apps.get_model('projects', 'DeviceServicePlan')
    DeviceServiceSchedule = apps.get_model('projects', 'DeviceServiceSchedule')
    InspectionTask = apps.get_model('projects', 'InspectionTask')
    supported_types = {'inspection', 'system_upgrade', 'rule_library_upgrade'}

    for plan in DeviceServicePlan.objects.filter(is_deleted=False).select_related('project_device'):
        binding = plan.project_device
        for service_type in set(plan.service_contents or []) & supported_types:
            schedule, created = DeviceServiceSchedule.objects.get_or_create(
                service_plan_id=plan.id,
                service_type=service_type,
                defaults={
                    'frequency': plan.inspection_frequency,
                    'interval_days': plan.inspection_interval_days,
                    'first_service_date': plan.first_inspection_date,
                    'reminder_days': plan.reminder_days,
                    'auto_generate_tasks': plan.auto_generate_tasks,
                },
            )
            if not created or not schedule.auto_generate_tasks or not binding.service_start_date or not binding.service_end_date:
                continue
            planned_date = schedule.first_service_date or binding.service_start_date
            while planned_date and planned_date <= binding.service_end_date:
                InspectionTask.objects.get_or_create(
                    service_schedule_id=schedule.id,
                    planned_date=planned_date,
                    defaults={
                        'service_plan_id': plan.id,
                        'task_type': service_type,
                        'reminder_date': planned_date - timedelta(days=schedule.reminder_days),
                        'status': 'pending',
                    },
                )
                planned_date = next_date(planned_date, schedule)


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0015_deviceserviceschedule_and_more'),
    ]

    operations = [
        migrations.RunPython(create_missing_service_schedules, migrations.RunPython.noop),
    ]

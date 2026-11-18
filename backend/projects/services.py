from calendar import monthrange
from datetime import timedelta
from io import BytesIO
import re

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import OuterRef, Subquery
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.table import Table, TableStyleInfo

from projects.models import DeviceServiceSchedule, InspectionTask, ProjectDevice, ServiceExpiryEmailRecord, ServiceExpiryEmailSetting, ServiceStandardTemplate


def add_months(value, months):
    target_month = value.month - 1 + months
    target_year = value.year + target_month // 12
    target_month = target_month % 12 + 1
    return value.replace(year=target_year, month=target_month, day=min(value.day, monthrange(target_year, target_month)[1]))


def next_service_date(value, schedule):
    frequency_months = {
        ServiceStandardTemplate.INSPECTION_MONTHLY: 1,
        ServiceStandardTemplate.INSPECTION_QUARTERLY: 3,
        ServiceStandardTemplate.INSPECTION_SEMIANNUAL: 6,
        ServiceStandardTemplate.INSPECTION_ANNUAL: 12,
    }
    months = frequency_months.get(schedule.frequency)
    if months:
        return add_months(value, months)
    if schedule.frequency == ServiceStandardTemplate.INSPECTION_CUSTOM and schedule.interval_days:
        return value + timedelta(days=schedule.interval_days)
    return None


def generate_service_tasks(schedule):
    """按服务项规则补齐待办任务；重复运行不会重复创建。"""
    plan = schedule.service_plan
    binding = plan.project_device
    if not schedule.auto_generate_tasks:
        return 0
    if not binding.service_start_date or not binding.service_end_date:
        return 0

    planned_date = schedule.first_service_date or binding.service_start_date
    created_count = 0
    while planned_date and planned_date <= binding.service_end_date:
        reminder_date = planned_date - timedelta(days=schedule.reminder_days)
        _, created = InspectionTask.objects.get_or_create(
            service_schedule=schedule,
            planned_date=planned_date,
            defaults={
                "service_plan": plan,
                "task_type": schedule.service_type,
                "assignee": schedule.assignee or plan.ops_person,
                "reminder_date": reminder_date,
                "status": InspectionTask.STATUS_PENDING,
            },
        )
        created_count += int(created)
        planned_date = next_service_date(planned_date, schedule)
    return created_count


def generate_inspection_tasks(plan):
    """兼容历史调用：优先按巡检服务项生成任务。"""
    schedule = plan.service_schedules.filter(
        is_deleted=False,
        service_type=DeviceServiceSchedule.TYPE_INSPECTION,
    ).first()
    if schedule:
        return generate_service_tasks(schedule)
    return 0


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


def service_expiry_bindings(today=None):
    """Return each device's current service binding when it expires within six months."""
    today = today or timezone.localdate()
    latest_binding = ProjectDevice.objects.filter(
        device_id=OuterRef("device_id"),
        is_deleted=False,
        project__is_deleted=False,
    ).exclude(service_type=ProjectDevice.SERVICE_OFFLINE).order_by("-service_end_date", "-updated_at", "-id")
    return ProjectDevice.objects.select_related(
        "project__customer_org",
        "project__sales_person",
        "device__device_model",
    ).filter(
        id=Subquery(latest_binding.values("id")[:1]),
        service_end_date__gte=today,
        service_end_date__lte=today + timedelta(days=180),
    ).exclude(service_type=ProjectDevice.SERVICE_OFFLINE).order_by("service_end_date", "id")


def email_delivery_configured():
    backend = getattr(settings, "EMAIL_BACKEND", "")
    if backend.endswith("smtp.EmailBackend"):
        return bool(getattr(settings, "EMAIL_HOST_USER", "") and getattr(settings, "EMAIL_HOST_PASSWORD", ""))
    return bool(backend)


def sales_salutation(sales):
    if not sales or not sales.name.strip():
        return ""
    name = sales.name.strip()
    compound_surnames = (
        "欧阳", "司马", "上官", "诸葛", "东方", "皇甫", "尉迟", "公孙",
        "慕容", "宇文", "令狐", "轩辕", "长孙", "司徒", "司空",
    )
    surname = next((item for item in compound_surnames if name.startswith(item)), name[0])
    return f"{surname}总"


def build_service_expiry_email_content(bindings):
    bindings = list(bindings)
    sales = bindings[0].project.sales_person if bindings else None
    device_count = len(bindings)
    salutation = sales_salutation(sales)
    model_summary = {}
    for binding in bindings:
        customer = binding.project.customer_org
        model = binding.device.device_model
        key = (
            customer.name if customer else "未关联客户",
            model.model_name if model else binding.device.name,
        )
        model_summary[key] = model_summary.get(key, 0) + 1

    lines = [
        f"{salutation}，您好：" if salutation else "您好：",
        "",
        f"您负责的项目中有 {device_count} 台设备将在未来 6 个月内维保到期，请及时关注并安排后续续保跟进。",
        "",
        "涉及单位及设备型号：",
    ]
    for index, ((customer_name, model_name), count) in enumerate(model_summary.items(), start=1):
        lines.append(f"{index}. {customer_name}：{model_name}（{count} 台）")
    lines.extend([
        "",
        "具体设备及维保到期信息请查看邮件附件《维保到期设备清单》。",
        "",
        "此邮件由交付中台自动发送，请勿直接回复。",
    ])
    return "\n".join(lines)


def build_service_expiry_email(binding):
    subject = "设备维保到期提醒（1 台）"
    return subject, build_service_expiry_email_content([binding])


def build_service_expiry_workbook(bindings):
    bindings = list(bindings)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "维保到期设备"
    sheet.sheet_view.showGridLines = False

    sales = bindings[0].project.sales_person if bindings else None
    sheet["A1"] = "维保到期设备清单"
    sheet["A1"].font = Font(name="Arial", size=14, bold=True, color="1F2937")
    sheet["A2"] = f"负责销售：{sales.name if sales else '未绑定销售'}    生成日期：{timezone.localdate().isoformat()}"
    sheet["A2"].font = Font(name="Arial", size=10, italic=True, color="6B7280")

    headers = [
        "序号", "客户", "项目名称", "设备型号", "设备名称", "序列号",
        "维保开始日期", "维保到期日", "剩余天数", "负责销售",
    ]
    sheet.append([])
    sheet.append(headers)
    today = timezone.localdate()
    for index, binding in enumerate(bindings, start=1):
        project = binding.project
        customer = project.customer_org
        model = binding.device.device_model
        binding_sales = project.sales_person
        sheet.append([
            index,
            customer.name if customer else "",
            project.name,
            model.model_name if model else "",
            binding.device.name,
            binding.device.serial_number,
            binding.service_start_date,
            binding.service_end_date,
            (binding.service_end_date - today).days,
            binding_sales.name if binding_sales else "",
        ])

    header_row = 4
    last_row = max(sheet.max_row, header_row)
    header_fill = PatternFill("solid", fgColor="1F4E78")
    for cell in sheet[header_row]:
        cell.fill = header_fill
        cell.font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    for row in sheet.iter_rows(min_row=header_row + 1, max_row=last_row):
        for cell in row:
            cell.font = Font(name="Arial", size=10, color="1F2937")
            cell.alignment = Alignment(vertical="center")
    for column in ("G", "H"):
        for cell in sheet[column][header_row:]:
            cell.number_format = "yyyy-mm-dd"

    if bindings:
        table = Table(displayName="ServiceExpiryDevices", ref=f"A{header_row}:J{last_row}")
        table.tableStyleInfo = TableStyleInfo(
            name="TableStyleMedium2",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False,
        )
        sheet.add_table(table)
    sheet.freeze_panes = "A5"
    widths = {"A": 8, "B": 20, "C": 24, "D": 20, "E": 20, "F": 20, "G": 15, "H": 15, "I": 12, "J": 14}
    for column, width in widths.items():
        sheet.column_dimensions[column].width = width
    sheet.row_dimensions[1].height = 24
    sheet.row_dimensions[4].height = 24
    sheet.auto_filter.ref = f"A{header_row}:J{last_row}"

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def send_service_expiry_message(subject, content, recipient_email, bindings):
    bindings = list(bindings)
    sales = bindings[0].project.sales_person if bindings else None
    safe_sales_name = re.sub(r'[\\/:*?"<>|]+', "_", sales.name if sales else "未绑定销售")
    filename = f"维保到期设备清单-{safe_sales_name}-{timezone.localdate():%Y%m%d}.xlsx"
    message = EmailMessage(
        subject=subject,
        body=content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient_email],
        cc=get_service_expiry_cc_emails(recipient_email),
    )
    message.attach(
        filename,
        build_service_expiry_workbook(bindings),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    return message.send(fail_silently=False)


def get_service_expiry_cc_emails(recipient_email=""):
    setting = ServiceExpiryEmailSetting.objects.filter(key="default").first()
    raw_emails = setting.cc_emails if setting and isinstance(setting.cc_emails, list) else []
    recipient_key = recipient_email.strip().lower()
    seen = set()
    result = []
    for raw_email in raw_emails:
        email = str(raw_email).strip()
        key = email.lower()
        if not email or key == recipient_key or key in seen:
            continue
        seen.add(key)
        result.append(email)
    return result


def send_service_expiry_email(binding, source=ServiceExpiryEmailRecord.SOURCE_MANUAL, user=None, force_resend=False):
    """Send once for a project-device service period; failures remain retryable."""
    sales = binding.project.sales_person
    recipient_email = (sales.email if sales else "").strip()
    recipient_name = sales.name if sales else ""
    subject, content = build_service_expiry_email(binding)

    with transaction.atomic():
        record, _ = ServiceExpiryEmailRecord.all_objects.get_or_create(
            project_device=binding,
            service_end_date=binding.service_end_date,
            defaults={
                "status": ServiceExpiryEmailRecord.STATUS_PENDING,
                "created_by": user,
                "updated_by": user,
            },
        )
        record = ServiceExpiryEmailRecord.all_objects.select_for_update().get(pk=record.pk)
        if record.status == ServiceExpiryEmailRecord.STATUS_SENT and not force_resend:
            return record, "skipped"
        if record.status == ServiceExpiryEmailRecord.STATUS_SENDING and record.updated_at >= timezone.now() - timedelta(minutes=10):
            return record, "skipped"
        record.status = ServiceExpiryEmailRecord.STATUS_SENDING
        record.recipient_name = recipient_name
        record.recipient_email = recipient_email
        record.message_subject = subject
        record.trigger_source = source
        record.attempt_count += 1
        record.last_error = ""
        record.updated_by = user
        record.save(update_fields=[
            "status", "recipient_name", "recipient_email", "message_subject", "trigger_source",
            "attempt_count", "last_error", "updated_by", "updated_at",
        ])

    try:
        if not recipient_email:
            raise ValueError("项目负责销售未维护邮箱")
        if not email_delivery_configured():
            raise ValueError("发件邮箱尚未配置")
        send_service_expiry_message(subject, content, recipient_email, [binding])
    except Exception as exc:
        record.status = ServiceExpiryEmailRecord.STATUS_FAILED
        record.last_error = str(exc)[:2000]
        record.updated_by = user
        record.save(update_fields=["status", "last_error", "updated_by", "updated_at"])
        return record, "failed"

    record.status = ServiceExpiryEmailRecord.STATUS_SENT
    record.sent_at = timezone.now()
    record.last_error = ""
    record.updated_by = user
    record.save(update_fields=["status", "sent_at", "last_error", "updated_by", "updated_at"])
    return record, "sent"


def build_grouped_service_expiry_email(bindings):
    subject = f"设备维保到期汇总提醒（{len(bindings)} 台）"
    return subject, build_service_expiry_email_content(bindings)


def send_service_expiry_email_group(bindings, source=ServiceExpiryEmailRecord.SOURCE_BATCH, user=None, force_resend=False):
    """Send one consolidated email for all pending bindings owned by one salesperson."""
    bindings = list(bindings)
    if not bindings:
        return []

    sales = bindings[0].project.sales_person
    recipient_email = (sales.email if sales else "").strip()
    recipient_name = sales.name if sales else ""
    prepared = []
    results = []

    with transaction.atomic():
        for binding in bindings:
            record, _ = ServiceExpiryEmailRecord.all_objects.get_or_create(
                project_device=binding,
                service_end_date=binding.service_end_date,
                defaults={
                    "status": ServiceExpiryEmailRecord.STATUS_PENDING,
                    "created_by": user,
                    "updated_by": user,
                },
            )
            record = ServiceExpiryEmailRecord.all_objects.select_for_update().get(pk=record.pk)
            if record.status == ServiceExpiryEmailRecord.STATUS_SENT and not force_resend:
                results.append((binding, record, "skipped"))
                continue
            if record.status == ServiceExpiryEmailRecord.STATUS_SENDING and record.updated_at >= timezone.now() - timedelta(minutes=10):
                results.append((binding, record, "skipped"))
                continue
            record.status = ServiceExpiryEmailRecord.STATUS_SENDING
            record.recipient_name = recipient_name
            record.recipient_email = recipient_email
            record.message_subject = ""
            record.trigger_source = source
            record.attempt_count += 1
            record.last_error = ""
            record.updated_by = user
            record.save(update_fields=[
                "status", "recipient_name", "recipient_email", "message_subject", "trigger_source",
                "attempt_count", "last_error", "updated_by", "updated_at",
            ])
            prepared.append((binding, record))

    if not prepared:
        return results

    subject, content = build_grouped_service_expiry_email([binding for binding, _ in prepared])
    for _, record in prepared:
        record.message_subject = subject
        record.save(update_fields=["message_subject", "updated_at"])

    try:
        if not recipient_email:
            raise ValueError("项目负责销售未维护邮箱")
        if not email_delivery_configured():
            raise ValueError("发件邮箱尚未配置")
        send_service_expiry_message(
            subject,
            content,
            recipient_email,
            [binding for binding, _ in prepared],
        )
    except Exception as exc:
        error = str(exc)[:2000]
        for binding, record in prepared:
            record.status = ServiceExpiryEmailRecord.STATUS_FAILED
            record.last_error = error
            record.updated_by = user
            record.save(update_fields=["status", "last_error", "updated_by", "updated_at"])
            results.append((binding, record, "failed"))
        return results

    sent_at = timezone.now()
    for binding, record in prepared:
        record.status = ServiceExpiryEmailRecord.STATUS_SENT
        record.sent_at = sent_at
        record.last_error = ""
        record.updated_by = user
        record.save(update_fields=["status", "sent_at", "last_error", "updated_by", "updated_at"])
        results.append((binding, record, "sent"))
    return results

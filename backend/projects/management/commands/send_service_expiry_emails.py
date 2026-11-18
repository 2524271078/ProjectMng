from django.core.management.base import BaseCommand, CommandError

from projects.models import ServiceExpiryEmailRecord
from projects.services import email_delivery_configured, send_service_expiry_email_group, service_expiry_bindings


class Command(BaseCommand):
    help = "Send one-time service-expiry emails for devices expiring within 180 days."

    def handle(self, *args, **options):
        if not email_delivery_configured():
            raise CommandError("发件邮箱尚未配置，请先设置 EMAIL_HOST_USER 和 EMAIL_HOST_PASSWORD。")

        counts = {"sent": 0, "failed": 0, "skipped": 0}
        grouped_bindings = {}
        for binding in service_expiry_bindings():
            grouped_bindings.setdefault(binding.project.sales_person_id, []).append(binding)
        for sales_bindings in grouped_bindings.values():
            results = send_service_expiry_email_group(
                sales_bindings,
                source=ServiceExpiryEmailRecord.SOURCE_SCHEDULED,
            )
            for _, _, outcome in results:
                counts[outcome] += 1

        self.stdout.write(self.style.SUCCESS(
            f"处理完成：发送 {counts['sent']}，失败 {counts['failed']}，跳过 {counts['skipped']}。"
        ))

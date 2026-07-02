from django.core.management.base import BaseCommand, CommandError

from projects.models import Organization

PROVINCE_COMPANIES = [
    "国网河北电力",
    "国网天津电力",
    "国网上海电力",
    "国网重庆电力",
    "国网福建电力",
    "国网黑龙江电力",
    "国网江西电力",
    "国网湖北电力",
    "国网北京电力",
    "国网江苏电力",
    "国网山西电力",
    "国网山东电力",
    "国网蒙东电力",
    "国网浙江电力",
    "国网四川电力",
    "国网辽宁电力",
    "国网吉林电力",
    "国网宁夏电力",
    "国网青海电力",
    "国网湖南电力",
    "国网甘肃电力",
    "国网河南电力",
    "国网安徽电力",
    "国网西藏电力",
    "国网陕西电力",
    "国网冀北电力",
    "国网新疆电力",
]

BRANCHES = [
    "国网华东分部",
    "国网华北分部",
    "国网华中分部",
    "国网西部分部",
    "国网西南分部",
    "国网东北分部",
]

AFFILIATES = [
    "国网电力后勤公司",
    "国网电力技术公司",
    "国网中能联科院",
    "国网英大",
    "国网英大国际信托",
]


class Command(BaseCommand):
    help = "Reset organizations and import State Grid organization tree."

    def add_arguments(self, parser):
        parser.add_argument("--yes", action="store_true", help="Confirm destructive organization reset.")

    def handle(self, *args, **options):
        if not options["yes"]:
            raise CommandError("This command deletes all organizations. Re-run with --yes to confirm.")

        Organization.all_objects.all().delete()

        root = Organization.objects.create(name="国网电力公司", org_type="customer", short_name="国网电力")
        for name in PROVINCE_COMPANIES:
            Organization.objects.create(name=name, parent=root, org_type="customer", short_name=name)

        branch_root = Organization.objects.create(name="国网六大分部", org_type="customer", short_name="六大分部")
        for name in BRANCHES:
            Organization.objects.create(name=name, parent=branch_root, org_type="customer", short_name=name)

        affiliate_root = Organization.objects.create(name="国网三产公司", org_type="customer", short_name="三产公司")
        for name in AFFILIATES:
            Organization.objects.create(name=name, parent=affiliate_root, org_type="customer", short_name=name)

        total = 3 + len(PROVINCE_COMPANIES) + len(BRANCHES) + len(AFFILIATES)
        self.stdout.write(self.style.SUCCESS(f"Imported {total} State Grid organizations."))

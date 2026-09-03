from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "已停用：招聘雷达只采用企业官网和官方招聘系统数据。"

    def handle(self, *args, **options):
        raise CommandError(
            "wechat-oa discovery is disabled; use admitted official website or ATS sources"
        )

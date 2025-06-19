import asyncio

from django.core.management.base import BaseCommand

from apps.todos.models import Page


class Command(BaseCommand):
    help = "Test bot command"

    async def async_handle(self, pages: list[Page]):
        for page in pages:
            if page.can_send_updates():
                await page.send_updates()

    def handle(self, *args, **options):
        pages = Page.objects.all()
        asyncio.run(self.async_handle(list(pages)))
        self.stdout.write(self.style.SUCCESS("bot updates sent"))

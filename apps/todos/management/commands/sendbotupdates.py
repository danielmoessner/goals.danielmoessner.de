import asyncio

from django.core.management.base import BaseCommand

from apps.todos.models import Page


class Command(BaseCommand):
    help = "Test bot command"

    def handle(self, *args, **options):
        pages = Page.objects.all()
        for page in pages:
            if page.can_send_updates():
                asyncio.run(page.send_updates())

import asyncio

from django.core.management.base import BaseCommand

from config.bot import get_bot


async def send():
    bot = get_bot()
    await bot.send_message(chat_id="", text="@not-there I can tag humans!")


async def print_chat_ids():
    bot = get_bot()
    updates = await bot.get_updates()
    for update in updates:
        if update.message and update.message.chat:
            print("Chat title:", update.message.chat.title)
            print("Chat ID:", update.message.chat.id)


class Command(BaseCommand):
    help = "Test bot command"

    def handle(self, *args, **options):
        asyncio.run(send())

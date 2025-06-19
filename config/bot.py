from functools import lru_cache

import telegram
from django.conf import settings


@lru_cache
def get_bot():
    return telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN)

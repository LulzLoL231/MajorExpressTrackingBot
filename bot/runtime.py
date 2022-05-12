# -*- coding: utf-8 -*-
#
#  MajorExpressTrackingBot - tracking packages by Major Express.
#  Created by LulzLoL231 at 12/5/22
#
import os
import logging
from asyncio import get_event_loop

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from db import Database
from majorapi import MEAPI


__version__ = '0.1.1'
logging.basicConfig(
    format='[%(levelname)s] %(name)s (%(lineno)d) >> %(module)s.%(funcName)s: %(message)s',
    level=logging.DEBUG if os.environ.get('BOT_DEBUG', '') else logging.INFO
)
CMDS = [
    BotCommand('/start', 'Запустить бота'),
    BotCommand('/set_tracking', 'Установить отслеживание'),
    BotCommand('/current_tracking', 'Текущее отслеживание'),
    BotCommand('/change_destination', 'Изменить город получателя'),
    BotCommand('/stop_tracking', 'Остановить отслеживание'),
    BotCommand('/settings', 'Настройки'),
    BotCommand('/about', 'О боте.')
]
log = logging.getLogger('MajorExpressTrackingBot')
log.info(f'Starting v{__version__}')
loop = get_event_loop()
bot = Dispatcher(Bot(os.environ.get('BOT_TOKEN', ''), loop=loop, parse_mode='HTML'), loop=loop, storage=MemoryStorage())
db = Database()
majorapi = MEAPI()

loop.create_task(bot.bot.set_my_commands(CMDS))
loop.create_task(db._create_tables())

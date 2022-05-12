# -*- coding: utf-8 -*-
#
#  MajorExpressTrackingBot - tracking packages by Major Express.
#  Created by LulzLoL231 at 12/5/22
#
import os
import sys
import logging
from asyncio import get_event_loop, sleep

from aiogram import Bot, Dispatcher, types
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats, BotCommandScopeAllGroupChats
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from db import Database
from majorapi import MEAPI


__version__ = '1.2'
logging.basicConfig(
    format='[%(levelname)s] %(name)s (%(lineno)d) >> %(module)s.%(funcName)s: %(message)s',
    level=logging.DEBUG if os.environ.get('BOT_DEBUG', '') else logging.INFO
)
PrivateChatCmds = [
    BotCommand('/start', 'Запустить бота'),
    BotCommand('/set_tracking', 'Установить отслеживание'),
    BotCommand('/current_trackings', 'Текущие отслеживания'),
    BotCommand('/about', 'О боте.')
]
GroupChatCmds = [
    BotCommand('/about', 'О боте.')
]
log = logging.getLogger('MajorExpressTrackingBot')
log.info(f'Starting v{__version__}')
loop = get_event_loop()
bot = Dispatcher(Bot(os.environ.get('BOT_TOKEN', ''), loop=loop, parse_mode='HTML'), loop=loop, storage=MemoryStorage())
db = Database()
majorapi = MEAPI()


async def notify():
    '''Checking for package events.
    '''
    log.info('Start checking.')
    packs = await db.get_all_packages()
    for pack in packs:
        me_data = await majorapi.get_tracing(pack.wbNumber)
        if me_data:
            last_event = me_data['events'][::-1][0]
            if last_event["eventId"] != pack.last_eventId:
                if pack.last_eventId == 0:
                    # Ignoring last event, because package added to db recently.
                    await db.change_last_eventId(pack.wbNumber, last_event['eventId'])
                else:
                    cnt = f'Новое событие посылки #{pack.wbNumber}!\n\n'
                    cnt += f'{last_event["eventDate"]} {last_event["eventTime"]} - {last_event["city"]} - {last_event["event"]}'
                    key = types.InlineKeyboardMarkup()
                    key.add(types.InlineKeyboardButton(
                        f'Посылка #{pack.wbNumber}',
                        callback_data='current_tracking'
                    ))
                    try:
                        await bot.bot.send_message(
                            pack.user_id, cnt, reply_markup=key
                        )
                    except Exception:
                        log.exception(f'Can\'t send message to user #{pack.user_id}', exc_info=sys.exc_info())
            else:
                continue
        else:
            log.warning(f'Can\'t fetch package info for #{pack.wbNumber}!')
    await sleep(3600)


loop.run_until_complete(bot.bot.set_my_commands(PrivateChatCmds, BotCommandScopeAllPrivateChats()))
loop.run_until_complete(bot.bot.set_my_commands(GroupChatCmds, BotCommandScopeAllGroupChats()))
loop.run_until_complete(db._create_tables())
loop.create_task(notify())

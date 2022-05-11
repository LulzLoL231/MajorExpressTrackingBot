# -*- coding: utf-8 -*-
#
#  MajorExpressTrackingBot - About cmds.
#  Created by LulzLoL231 at 12/5/22
#
from aiogram import types

from ..runtime import bot, log, __version__


CONTENT = {
    'ru': '''Бот для отслеживания посылок Major Express.

Автор: @LulzLoL231
Версия: {}
Репозиторий: <a href="https://github.com/LulzLoL231/MajorExpressTrackingBot">GitHub</a>
''',
    'en': '''Major Express Tracking Bot

Author: @LulzLoL231
Version: {}
Repository: <a href="https://github.com/LulzLoL231/MajorExpressTrackingBot">GitHub</a>
'''
}


@bot.message_handler(commands=['about'])
async def about_bot(msg: types.Message):
    log.info(f'Called by {msg.from_user.mention} ({msg.from_user.id})')
    if msg.from_user.language_code == 'ru':
        cnt = CONTENT['ru'].format(__version__)
    elif msg.from_user.language_code == 'en':
        cnt = CONTENT['en'].format(__version__)
    else:
        cnt = CONTENT['en'].format(__version__)
    await msg.answer(cnt)

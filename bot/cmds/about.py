# -*- coding: utf-8 -*-
#
#  MajorExpressTrackingBot - About cmds.
#  Created by LulzLoL231 at 12/5/22
#
from aiogram import types

from ..runtime import bot, log, __version__


CONTENT = '''Бот для отслеживания посылок Major Express.

Автор: @LulzLoL231
Версия: {}
Репозиторий: <a href="https://github.com/LulzLoL231/MajorExpressTrackingBot">GitHub</a>
'''


@bot.message_handler(commands=['about'])
async def about_bot(msg: types.Message):
    log.info(f'Called by {msg.chat.mention} ({msg.chat.id})')
    await msg.answer(CONTENT.format(__version__))

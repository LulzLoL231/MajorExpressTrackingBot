# -*- coding: utf-8 -*-
#
#  MajorExpressTrackingBot - Start cmds.
#  Created by LulzLoL231 at 12/5/22
#
from aiogram import types
from aiogram.dispatcher.storage import FSMContext

from ..runtime import bot, log, db


@bot.message_handler(commands=['start'], state='*')
async def start(msg: types.Message, state: FSMContext):
    log.info(f'Called by {msg.from_user.mention} ({msg.from_user.id})')
    cur_track = await db.get_package_by_user_id(msg.from_user.id)
    if not cur_track:
        key = types.InlineKeyboardMarkup()
        key.add(types.InlineKeyboardButton(
            'Добавить посылку', callback_data='add_package'
        ))
        cnt = f'Привет, {msg.from_user.first_name}!\nДавай начнём отслеживание!'
    else:
        key = types.InlineKeyboardMarkup()
        key.add(types.InlineKeyboardButton(
            f'Посылка #{cur_track.wbNumber}',
            callback_data='current_tracking'
        ))
        cnt = f'Привет, {msg.from_user.first_name}!\nМы ещё отслеживаем твою посылку.'
    await msg.answer(cnt, reply_markup=key)

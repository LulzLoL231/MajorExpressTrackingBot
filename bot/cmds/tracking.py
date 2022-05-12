# -*- coding: utf-8 -*-
#
#  MajorExpressTrackingBot - Tracking cmds.
#  Created by LulzLoL231 at 12/5/22
#
from aiogram import types
from aiogram.dispatcher.storage import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from ..runtime import bot, log, majorapi, db


class SetTrackingState(StatesGroup):
    code = State()


def parse_events(array: list) -> str:
    '''Parsing events to message content.

    Args:
        array (list): Events array.

    Returns:
        str: Message content.
    '''
    ev_tmp = '        {} - {}'
    evs = []
    last_date = ''
    last_city = ''
    for ev in array:
        if last_date == ev['eventDate']:
            if last_city == ev['city']:
                evs.append(ev_tmp.format(ev['eventTime'], ev['event']))
            else:
                last_city = ev['city']
                evs.append(f'    <i>{ev["city"]}</i>')
                evs.append(ev_tmp.format(ev['eventTime'], ev['event']))
        else:
            last_date = ev['eventDate']
            evs.append(f'<b>{ev["eventDate"]}</b>')
            if last_city == ev['city']:
                evs.append(ev_tmp.format(ev['eventTime'], ev['event']))
            else:
                last_city = ev['city']
                evs.append(f'    <i>{ev["city"]}</i>')
                evs.append(ev_tmp.format(ev['eventTime'], ev['event']))
    return '\n'.join(evs)


@bot.callback_query_handler(lambda q: q.data == 'set_tracking', state='*')
async def query_set_tracking(query: types.CallbackQuery, state: FSMContext):
    log.info(f'Called by {query.message.chat.mention} ({query.message.chat.id})')
    await query.answer()
    await query.message.delete()
    await set_tracking(query.message, state)


@bot.message_handler(commands=['set_tracking'], state='*')
async def set_tracking(msg: types.Message, state: FSMContext):
    if msg.chat.id < 0:
        return
    log.info(f'Called by {msg.chat.mention} ({msg.chat.id})')
    if state:
        log.debug(f'Canceling state: {state.__dict__}')
        await state.finish()
    cur_track = await db.get_package_by_user_id(msg.chat.id)
    if not cur_track:
        await SetTrackingState.code.set()
        await msg.answer('Введите код отслеживания')
    else:
        key = types.InlineKeyboardMarkup()
        key.add(types.InlineKeyboardButton(
            f'Посылка #{cur_track.wbNumber}',
            callback_data='current_tracking'
        ))
        cnt = 'Вы уже отслеживаете посылку.'
        await msg.answer(cnt, reply_markup=key)


@bot.message_handler(content_types=types.ContentTypes.TEXT, state=SetTrackingState.code)
async def set_tracking_finish(msg: types.Message, state: FSMContext):
    if msg.chat.id < 0:
        return
    log.info(f'Called by {msg.chat.mention} ({msg.chat.id})')
    if msg.text.isdigit():
        await state.finish()
        await db.add_package(
            msg.chat.id, msg.text
        )
        key = types.InlineKeyboardMarkup()
        key.add(types.InlineKeyboardButton(
            f'Посылка #{msg.text}',
            callback_data='current_tracking'
        ))
        await state.finish()
        cnt = 'Посылка теперь отслеживается!'
        await msg.answer(cnt, reply_markup=key)
    else:
        await msg.answer('Код отслеживание может быть <b>только цифровым</b>!')


@bot.callback_query_handler(lambda q: q.data == 'current_tracking', state='*')
async def query_current_tracking(query: types.CallbackQuery, state: FSMContext):
    log.info(f'Called by {query.message.chat.mention} ({query.message.chat.id})')
    await query.answer()
    await query.message.delete()
    await current_tracking(query.message, state)


@bot.message_handler(commands='current_tracking', state='*')
async def current_tracking(msg: types.Message, state: FSMContext):
    if msg.chat.id < 0:
        return
    log.info(f'Called by {msg.chat.mention} ({msg.chat.id})')
    await msg.answer_chat_action(types.ChatActions.TYPING)
    if state:
        log.debug(f'Canceling state: {state.__dict__}')
        await state.finish()
    cur_track = await db.get_package_by_user_id(msg.chat.id)
    if not cur_track:
        key = types.InlineKeyboardMarkup()
        key.add(types.InlineKeyboardButton(
            'Добавить посылку',
            callback_data='set_tracking'
        ))
        cnt = 'Сейчас вы не отслеживаете ни одну посылку.\nДобавьте новую!'
        await msg.answer(cnt, reply_markup=key)
    else:
        me_data = await majorapi.get_tracing(cur_track.wbNumber,
                                             cur_track.delivType)
        if me_data:
            cnt = f'<b>Посылка #{cur_track.wbNumber}</b>\n\n'
            cnt += f'<b>Примерная дата доставки:</b> <code>{me_data["calcDeliveryDate"]}</code>\n'
            cnt += f'<b>Текущий статус:</b> {me_data["currentEvent"]}\n\n'
            cnt += '<b>История отслеживания:</b>\n'
            cnt += parse_events(me_data['events'])
            await msg.answer(cnt)
        else:
            await msg.answer('<b>Ошибка: </b> не удалось получить данные о отслеживании.')


@bot.message_handler(commands='stop_tracking', state='*')
async def stop_tracking(msg: types.Message, state: FSMContext):
    if msg.chat.id < 0:
        return
    log.info(f'Called by {msg.chat.mention} ({msg.chat.id})')
    if state:
        log.debug(f'Canceling state: {state.__dict__}')
        await state.finish()
    cur_track = await db.get_package_by_user_id(msg.chat.id)
    if not cur_track:
        key = types.InlineKeyboardMarkup()
        key.add(types.InlineKeyboardButton(
            'Добавить посылку',
            callback_data='set_tracking'
        ))
        cnt = 'Сейчас вы не отслеживаете ни одну посылку.\nДобавьте новую!'
        await msg.answer(cnt, reply_markup=key)
    else:
        await db.delete_package(cur_track.wbNumber)
        await msg.answer(f'Отслеживание посылки #{cur_track.wbNumber} - <b>остановлено</b>.')


@bot.inline_handler(lambda q: len(q.query) >= 5)
async def get_tracing(query: types.InlineQuery):
    log.info(f'Called with query: {query}')
    me_data = await majorapi.get_tracing(query.query)
    if me_data:
        cnt = f'<b>Посылка #{me_data["wbNumber"]}</b>\n\n'
        cnt += f'<b>Примерная дата доставки:</b> <code>{me_data["calcDeliveryDate"]}</code>\n'
        cnt += f'<b>Текущий статус:</b> {me_data["currentEvent"]}\n\n'
        cnt += '<b>История отслеживания:</b>\n'
        cnt += parse_events(me_data['events'])
        query_answer = [
            types.InlineQueryResultArticle(
                id=0, title=f'Посылка #{me_data["wbNumber"]}',
                input_message_content=types.InputTextMessageContent(cnt)
            )
        ]
    else:
        query_answer = []
    await query.answer(query_answer, cache_time=60, is_personal=True)

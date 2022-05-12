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
    log.info(
        f'Called by {query.message.chat.mention} ({query.message.chat.id})')
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
    await SetTrackingState.code.set()
    await msg.answer('Введите код отслеживания')


@bot.message_handler(content_types=types.ContentTypes.TEXT, state=SetTrackingState.code)
async def set_tracking_finish(msg: types.Message, state: FSMContext):
    if msg.chat.id < 0:
        return
    log.info(f'Called by {msg.chat.mention} ({msg.chat.id})')
    if msg.text.isdigit():
        await state.finish()
        if majorapi.get_tracing(msg.text):
            if not await db.is_already_tracking(msg.chat.id, msg.text):
                await db.add_package(
                    msg.chat.id, msg.text
                )
                cnt = 'Посылка теперь отслеживается!'
            else:
                cnt = 'Посылка уже отслеживается.'
            key = types.InlineKeyboardMarkup()
            key.add(types.InlineKeyboardButton(
                f'Посылка #{msg.text}',
                callback_data=f'package#{msg.text}'
            ))
            await msg.answer(cnt, reply_markup=key)
        else:
            await msg.answer(f'Не могу получить данные о посылке #{msg.text}')
    else:
        await msg.answer('Код отслеживание может быть <b>только цифровым</b>!')


@bot.callback_query_handler(lambda q: q.data == 'current_trackings', state='*')
async def query_current_trackings(query: types.CallbackQuery, state: FSMContext):
    log.info(
        f'Called by {query.message.chat.mention} ({query.message.chat.id})')
    await query.answer()
    await query.message.delete()
    await current_trackings(query.message, state)


@bot.callback_query_handler(lambda q: q.data.startswith('package'), state='*')
async def show_package(query: types.CallbackQuery, state: FSMContext):
    log.info(
        f'Called by {query.message.chat.mention} ({query.message.chat.id})')
    if state:
        await state.finish()
    code = query.data.split('#')[1]
    me_data = await majorapi.get_tracing(code)
    if me_data:
        cnt = f'<b>Посылка #{me_data["wbNumber"]}</b>\n\n'
        cnt += f'<b>Примерная дата доставки:</b> <code>{me_data["calcDeliveryDate"]}</code>\n'
        cnt += f'<b>Текущий статус:</b> {me_data["currentEvent"]}\n\n'
        cnt += '<b>История отслеживания:</b>\n'
        cnt += parse_events(me_data['events'])
        key = types.InlineKeyboardMarkup(1)
        key.add(types.InlineKeyboardButton(
            'Остановить отслеживание',
            callback_data=f'stop_tracking#{code}'
        ))
        key.add(types.InlineKeyboardButton(
            'Назад',
            callback_data='current_trackings'
        ))
        await query.answer()
        await query.message.edit_text(cnt, reply_markup=key)
    else:
        log.warning(f'Can\'t fetch package info for #{code}!')
        await query.answer(f'Не удалось получить данные о посылке #{code}')
        await query.message.delete()


@bot.message_handler(commands='current_trackings', state='*')
async def current_trackings(msg: types.Message, state: FSMContext):
    if msg.chat.id < 0:
        return
    log.info(f'Called by {msg.chat.mention} ({msg.chat.id})')
    await msg.answer_chat_action(types.ChatActions.TYPING)
    if state:
        log.debug(f'Canceling state: {state.__dict__}')
        await state.finish()
    cur_tracks = await db.get_all_packages_for_user(msg.chat.id)
    if not cur_tracks:
        key = types.InlineKeyboardMarkup()
        key.add(types.InlineKeyboardButton(
            'Добавить посылку',
            callback_data='set_tracking'
        ))
        cnt = 'Сейчас вы не отслеживаете ни одну посылку.\nДобавьте новую!'
        await msg.answer(cnt, reply_markup=key)
    else:
        cnt = 'Текущие отслеживания:'
        key = types.InlineKeyboardMarkup(1)
        for pack in cur_tracks:
            key.add(types.InlineKeyboardButton(
                f'Посылка #{pack.wbNumber}',
                callback_data=f'package#{pack.wbNumber}'
            ))
        key.add(types.InlineKeyboardButton(
            'Добавить посылку',
            callback_data='set_tracking'
        ))
        await msg.answer(cnt, reply_markup=key)


@bot.callback_query_handler(lambda q: q.data.startswith('stop_tracking'), state='*')
async def query_stop_tracking(query: types.CallbackQuery, state: FSMContext):
    log.info(f'Called by {query.message.chat.mention} ({query.message.chat.id})')
    msg = query.message
    code = query.data.split('#')[1]
    if msg.chat.id < 0:
        return
    if state:
        log.debug(f'Canceling state: {state.__dict__}')
        await state.finish()
    pack = await db.get_package_by_wbNumber(code)
    if not pack:
        log.warning(f'Can\'t fetch data about Package #{code} from DB!')
        await query.answer(f'Не удалось найти посылку #{code}!')
        await msg.delete()
    else:
        await db.delete_package(pack.wbNumber)
        await msg.edit_text(f'Отслеживание посылки #{pack.wbNumber} - <b>остановлено</b>.')


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

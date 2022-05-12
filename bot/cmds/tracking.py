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
    city = State()


class ChangeDestCityState(StatesGroup):
    city = State()


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
async def set_tracking_city(msg: types.Message, state: FSMContext):
    log.info(f'Called by {msg.chat.mention} ({msg.chat.id})')
    if not msg.text.isdigit():
        await msg.answer('Код отслеживания может быть <b>только</b> цифровым!')
        return
    await state.update_data(code=msg.text)
    await SetTrackingState.city.set()
    await msg.answer('Хорошо, а теперь введите город получения\n<i>Будьте внимательны при вводе.</i>')


@bot.message_handler(content_types=types.ContentTypes.TEXT, state=SetTrackingState.city)
async def set_tracking_finish(msg: types.Message, state: FSMContext):
    log.info(f'Called by {msg.chat.mention} ({msg.chat.id})')
    code = (await state.get_data()).get('code', '')
    if code:
        await db.add_package(
            msg.chat.id, code,
            msg.text.lower()
        )
        key = types.InlineKeyboardMarkup()
        key.add(types.InlineKeyboardButton(
            f'Посылка #{code}',
            callback_data='current_tracking'
        ))
        await state.finish()
        cnt = 'Посылка теперь отслеживается!'
        await msg.answer(cnt, reply_markup=key)
    else:
        # В теории, сюда нельзя попасть, но всякое может быть.
        log.error(f'Key "code" is empty in state: {state.storage.__dict__}')
        key = types.InlineKeyboardMarkup()
        key.add(types.InlineKeyboardButton(
            'Добавить посылку',
            callback_data='set_tracking'
        ))
        cnt = 'Ошибка при добавлении посылки!\nПопробуйте ещё раз.'
        await msg.answer(cnt, reply_markup=key)


@bot.callback_query_handler(lambda q: q.data == 'current_tracking', state='*')
async def query_current_tracking(query: types.CallbackQuery, state: FSMContext):
    log.info(f'Called by {query.message.chat.mention} ({query.message.chat.id})')
    await query.answer()
    await query.message.delete()
    await current_tracking(query.message, state)


@bot.message_handler(commands='current_tracking', state='*')
async def current_tracking(msg: types.Message, state: FSMContext):
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
            cnt += f'<b>Город получения:</b> {cur_track.dest_city.capitalize()}\n'
            cnt += f'<b>Примерная дата доставки:</b> <code>{me_data["calcDeliveryDate"]}</code>\n'
            cnt += f'<b>Текущий статус:</b> {me_data["currentEvent"]}\n\n'
            cnt += '<b>История отслеживания:</b>\n'
            cnt += parse_events(me_data['events'])
            await msg.answer(cnt)
        else:
            await msg.answer('<b>Ошибка: </b> не удалось получить данные о отслеживании.')


@bot.message_handler(commands='change_destination', state='*')
async def change_destination(msg: types.Message, state: FSMContext):
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
        await ChangeDestCityState.city.set()
        await msg.answer('Введите новый город получения.')


@bot.message_handler(content_types=types.ContentTypes.TEXT, state=ChangeDestCityState.city)
async def change_destination_finish(msg: types.Message, state: FSMContext):
    log.info(f'Called by {msg.chat.mention} ({msg.chat.id})')
    await state.finish()
    cur_track = await db.get_package_by_user_id(msg.chat.id)
    if cur_track:
        await db.change_dest_city(cur_track.wbNumber, msg.text)
        key = types.InlineKeyboardMarkup()
        key.add(types.InlineKeyboardButton(
            f'Посылка #{cur_track.wbNumber}',
            callback_data='current_tracking'
        ))
        await msg.answer('Данные сохранены!', reply_markup=key)
    else:
        # И сюда в теории нельзя попасть, но всякое может быть.
        log.error('Can\'t fetch package info!')
        key = types.InlineKeyboardMarkup()
        key.add(types.InlineKeyboardButton(
            'Посылка',
            callback_data='current_tracking'
        ))
        cnt = 'Ошибка при получении данных о посылке!\nПопробуйте ещё раз.'
        await msg.answer(cnt, reply_markup=key)


@bot.message_handler(commands='stop_tracking', state='*')
async def stop_tracking(msg: types.Message, state: FSMContext):
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

# -*- coding: utf-8 -*-
#
#  MajorExpressTrackingBot - Startup script.
#  Created by LulzLoL231 at 12/5/22
#
from aiogram.utils.executor import start_polling

import bot.cmds
from bot.runtime import bot


if __name__ == '__main__':
    start_polling(bot)

# -*- coding: utf-8 -*-
#
#  Bot Database.
#  Created by LulzLoL231 at 12/5/22
#
import logging
from typing import Literal, Optional

import aiosqlite
from pydantic import BaseModel


log = logging.getLogger('Database')


class Package(BaseModel):
    user_id: int
    wbNumber: str
    delivType: str
    last_eventId: int


class Database:
    '''Bot database.

        Args:
            db_name (str): database filename. Defaults is "bot.db"
    '''
    TABLE_SQLS = [
        'CREATE TABLE IF NOT EXISTS "packages" ("user_id" INTEGER, "wbNumber" TEXT, "delivType" TEXT DEFAULT "false", "last_eventId" INTEGER DEFAULT 0)'
    ]

    def __init__(self, db_name: str = 'bot.db') -> None:
        self.db_name = db_name

    async def _create_tables(self):
        '''Creating tables in DB.
        '''
        log.debug('Called!')
        async with aiosqlite.connect(self.db_name) as db:
            for sql in self.TABLE_SQLS:
                await db.execute(sql)
            await db.commit()

    async def add_package(self,
                          user_id: int,
                          wbNumber: str,
                          delivType: str = 'false') -> Literal[True]:
        '''Add a new package to DB.

        Args:
            user_id (int): Telegram user_id.
            wbNumber (str): Major Express Tracking code.
            delivType (str, optional): Package delivery type. Defaults to 'false'.

        Returns:
            Literal[True]: Always True.
        '''
        log.debug(f'Called with args ({user_id}, {wbNumber}, {delivType})')
        values = (user_id, wbNumber, delivType)
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('INSERT INTO packages (user_id, wbNumber, delivType) VALUES (?,?,?)', values)
            await db.commit()
        return True

    async def get_package_by_wbNumber(self, wbNumber: int) -> Optional[Package]:
        '''Returns package from DB by his wbNumber.

        Args:
            wbNumber (str): Major Express Tracking code.

        Returns:
            Optional[Package]: Package info or None.
        '''
        log.debug(f'Called with args ({wbNumber})')
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT * FROM packages WHERE wbNumber=?', (wbNumber,)) as cur:
                fetch = await cur.fetchone()
                if fetch:
                    return Package(**dict(fetch))
                return None

    async def change_last_eventId(self, wbNumber: str, new_eventId: int) -> Literal[True]:
        '''Changing last eventId for package.

        Args:
            wbNumber (str): Major Express Tracking code.
            new_eventId (int): New Event ID.

        Returns:
            Literal[True]: Always True.
        '''
        log.debug(f'Called with args ({wbNumber}, {new_eventId})')
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('UPDATE packages SET last_eventId=? WHERE wbNumber=?', (new_eventId, wbNumber))
            await db.commit()
        return True

    async def delete_package(self, wbNumber: str) -> Literal[True]:
        '''Deleting package from DB.

        Args:
            wbNumber (str): Major Express Tracking code.

        Returns:
            Literal[True]: Always True.
        '''
        log.debug(f'Called with args ({wbNumber})')
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('DELETE FROM packages WHERE wbNumber=?', (wbNumber,))
            await db.commit()
        return True

    async def get_all_packages(self) -> list[Package]:
        '''Returns all packages.

        Returns:
            list[Package]: Array of Package.
        '''
        log.debug('Called!')
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT * FROM packages') as cur:
                return [Package(**dict(i)) for i in (await cur.fetchall())]

    async def get_all_packages_for_user(self, user_id: int) -> list[Package]:
        '''Returns all paclages for user.

        Args:
            user_id (int): Telegram user_id.

        Returns:
            list[Package]: Array of Packages.
        '''
        log.debug(f'Called with args ({user_id})')
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT * FROM packages WHERE user_id=?', (user_id,)) as cur:
                return [Package(**dict(i)) for i in (await cur.fetchall())]

    async def is_already_tracking(self, user_id: int, wbNumber: str) -> bool:
        '''Is package already tracking by user?

        Args:
            user_id (int): Telegram user_id.
            wbNumber (str): Major Express Tracking code.

        Returns:
            bool: Boolean.
        '''
        log.debug(f'Called with args ({user_id}, {wbNumber})')
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT wbNumber FROM packages WHERE user_id=? AND wbNumber=?', (user_id, wbNumber)) as cur:
                return bool((await cur.fetchone()))

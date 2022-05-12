# -*- coding: utf-8 -*-
#
#  MajorExpressAPI - ME Mobile API.
#  Created by LulzLoL231 at 12/5/22
#
import logging
from typing import Optional

import aiohttp


log = logging.getLogger('MajorExpressAPI')


class MEAPI:
    '''MajorExpress Mobile API.
    '''
    TRACKING_URL = 'https://m.major-express.ru/api/tracking'
    TRACKING_QUERY_TEMP = 'wbNumber={}&delivType={}'
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36'  # we are iPhone SE now.
    }

    async def _make_request(self,
                            method: str,
                            url: str,
                            data: Optional[str] = None,
                            headers: Optional[dict] = None) -> Optional[dict]:
        log.debug(f'Called with args ({method}, {url}, {data}, {headers})')
        if not headers:
            headers = self.DEFAULT_HEADERS
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=headers, data=data) as resp:
                if resp.ok:
                    ans = await resp.json()
                    log.debug(f'API Answer: {ans}')
                    return ans
                else:
                    log.error(f'Unexpected API Error [{resp.status}]!')
                    log.debug(f'API Answer: {(await resp.text())}')
                    return None

    async def get_tracing(self, wbNumber: str, delivType: str = 'false') -> Optional[dict]:
        '''Возвращает информацию об отслеживании посылки.

        Args:
            wbNumber (str): Номер декларации.
            delivType (str, optional): Тип доставки. Defaults to 'false'.

        Returns:
            Optional[dict]: Информация об отслеживании, или ничего.

        Note:
            delivType остаётся для меня некой загадкой, но не думаю что его надо меня с дефолтного "false".
        '''
        log.debug(f'Called with args ({wbNumber}, {delivType})')
        query = self.TRACKING_QUERY_TEMP.format(wbNumber, delivType)
        headers = self.DEFAULT_HEADERS.copy()
        headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        resp = await self._make_request('POST',
                                        self.TRACKING_URL,
                                        query, headers)
        if resp:
            return resp
        else:
            log.error('Can\'t fetch tracking info!')
            return None

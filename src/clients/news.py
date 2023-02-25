"""
Функции для взаимодействия с внешним сервисом-провайдером новостей.
"""
from http import HTTPStatus
from typing import Optional

import aiohttp

from clients.base import BaseClient
from logger import trace_config
from settings import API_KEY_NEWSPORTAL


class NewsClient(BaseClient):
    """
    Реализация функций для взаимодействия с внешним сервисом-провайдером новостей.
    """

    async def get_base_url(self) -> str:
        """
        Возвращает базовый URL для API новостей.
        :return:
        """
        return "https://newsapi.org/v2/everything"

    async def _request(self, endpoint: str) -> Optional[dict]:
        """
        Отправляет запрос HTTP GET на указанную конечную точку и возвращает ответ в виде JSON.
        """

        async with aiohttp.ClientSession(trace_configs=[trace_config]) as session:
            async with session.get(endpoint) as response:
                if response.status == HTTPStatus.OK:
                    return await response.json()
                return None

    async def get_news(self, country: str) -> Optional[dict]:
        """
         Получение новостей по заданной стране, опубликованных сегодня.
        :param country: Страна с которой собирается новость
        :return: JSON о новостях
        """

        endpoint = f"{await self.get_base_url()}?q={country}&sortBy=publishedAt&apiKey={API_KEY_NEWSPORTAL}"
        return await self._request(endpoint)

"""
Функции сбора информации о странах.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Optional, FrozenSet

import aiofiles
import aiofiles.os

from clients.country import CountryClient
from clients.currency import CurrencyClient
from clients.news import NewsClient
from clients.weather import WeatherClient
from collectors.base import BaseCollector
from collectors.models import (
    LocationDTO,
    CountryDTO,
    CurrencyRatesDTO,
    NewsDTO,
    CurrencyInfoDTO,
    WeatherInfoDTO,
)
from settings import (
    MEDIA_PATH,
    CACHE_TTL_COUNTRY,
    CACHE_TTL_CURRENCY_RATES,
    CACHE_TTL_NEWS,
    CACHE_TTL_WEATHER,
)


class CountryCollector(BaseCollector):
    """
    Сбор информации о странах (географическое описание).
    """

    def __init__(self) -> None:
        self.client = CountryClient()

    @staticmethod
    async def get_file_path(**kwargs: Any) -> str:
        return f"{MEDIA_PATH}/country.json"

    @staticmethod
    async def get_cache_ttl() -> int:
        return CACHE_TTL_COUNTRY

    async def collect(self, **kwargs: Any) -> Optional[FrozenSet[LocationDTO]]:
        """
        Получение данных из JSON.
        """
        if await self.cache_invalid():
            # если кэш уже невалиден, то актуализируем его
            result = await self.client.get_countries()
            if result:
                result_str = json.dumps(result)
                async with aiofiles.open(await self.get_file_path(), mode="w") as file:
                    await file.write(result_str)

        # получение данных из кэша
        async with aiofiles.open(await self.get_file_path(), mode="r") as file:
            content = await file.read()

        result = json.loads(content)
        if result:
            locations = frozenset(
                LocationDTO(
                    country=item["name"],
                    capital=item["capital"],
                    alpha2code=item["alpha2code"],
                )
                for item in result
            )

            return locations

        return None

    @classmethod
    async def read(cls) -> Optional[list[CountryDTO]]:
        """
        Чтение данных из кэша.

        :return:
        """

        async with aiofiles.open(await cls.get_file_path(), mode="r") as file:
            content = await file.read()

        if content:
            items = json.loads(content)
            result_list = []
            for item in items:
                result_list.append(
                    CountryDTO(
                        name=item["name"],
                        capital=item["capital"],
                        capital_latitude=item["latitude"],
                        capital_longitude=item["longitude"],
                        alpha2code=item["alpha2code"],
                        alt_spellings=item["alt_spellings"],
                        currencies={
                            CurrencyInfoDTO(code=currency["code"])
                            for currency in item["currencies"]
                        },
                        flag=item["flag"],
                        area=item["area"],
                        languages=item["languages"],
                        population=item["population"],
                        subregion=item["subregion"],
                        timezones=item["timezones"],
                    )
                )

            return result_list

        return None


class CurrencyRatesCollector(BaseCollector):
    """
    Сбор информации о курсах валют.
    """

    def __init__(self) -> None:
        self.client = CurrencyClient()

    @staticmethod
    async def get_file_path(**kwargs: Any) -> str:
        return f"{MEDIA_PATH}/currency_rates.json"

    @staticmethod
    async def get_cache_ttl() -> int:
        return CACHE_TTL_CURRENCY_RATES

    async def collect(self, **kwargs: Any) -> None:
        if await self.cache_invalid():
            # если кэш уже невалиден, то актуализируем его
            result = await self.client.get_rates()
            if result:
                result_str = json.dumps(result)
                async with aiofiles.open(await self.get_file_path(), mode="w") as file:
                    await file.write(result_str)

    @classmethod
    async def read(cls) -> Optional[CurrencyRatesDTO]:
        """
        Чтение данных из кэша.

        :return:
        """

        async with aiofiles.open(await cls.get_file_path(), mode="r") as file:
            content = await file.read()

        if content:
            result = json.loads(content)

            return CurrencyRatesDTO(
                base=result["base"],
                date=result["date"],
                rates=result["rates"],
            )

        return None


class WeatherCollector(BaseCollector):
    """
    Сбор информации о прогнозе погоды для столиц стран.
    """

    def __init__(self) -> None:
        self.client = WeatherClient()

    @staticmethod
    async def get_file_path(filename: str = "", **kwargs: Any) -> str:
        return f"{MEDIA_PATH}/weather/{filename}.json"

    @staticmethod
    async def get_cache_ttl() -> int:
        return CACHE_TTL_WEATHER

    async def collect(
        self, locations: FrozenSet[LocationDTO] = frozenset(), **kwargs: Any
    ) -> None:

        target_dir_path = f"{MEDIA_PATH}/weather"
        # если целевой директории еще не существует, то она создается
        if not await aiofiles.os.path.exists(target_dir_path):
            await aiofiles.os.mkdir(target_dir_path)

        for location in locations:
            filename = f"{location.capital}_{location.alpha2code}".lower()
            if await self.cache_invalid(filename=filename):
                # если кэш уже невалиден, то актуализируем его
                result = await self.client.get_weather(
                    f"{location.capital},{location.alpha2code}"
                )
                if result:
                    result_str = json.dumps(result)
                    async with aiofiles.open(
                        await self.get_file_path(filename), mode="w"
                    ) as file:
                        await file.write(result_str)

    @classmethod
    async def read(cls, location: LocationDTO) -> Optional[WeatherInfoDTO]:
        """
        Чтение данных из кэша.

        :param location: Город для получения данных
        :return:
        """

        filename = f"{location.capital}_{location.alpha2code}".lower()
        async with aiofiles.open(await cls.get_file_path(filename), mode="r") as file:
            content = await file.read()

        result = json.loads(content)
        if result:
            return WeatherInfoDTO(
                date_time=result["dt"],
                utc_timezone=result["timezone"],
                temp=result["main"]["temp"],
                pressure=result["main"]["pressure"],
                humidity=result["main"]["humidity"],
                wind_speed=result["wind"]["speed"],
                description=result["weather"][0]["description"],
                visibility=result["visibility"],
            )

        return None


class Collectors:
    """
    Сборщик данных.
    """

    @staticmethod
    async def gather() -> tuple:
        return await asyncio.gather(
            CurrencyRatesCollector().collect(),
            CountryCollector().collect(),
        )

    @staticmethod
    def collect() -> None:
        loop = asyncio.get_event_loop()
        try:
            results = loop.run_until_complete(Collectors.gather())
            loop.run_until_complete(WeatherCollector().collect(results[1]))
            loop.run_until_complete(NewsCollector().collect(results[1]))
            loop.run_until_complete(loop.shutdown_asyncgens())

        finally:
            loop.close()


class NewsCollector(BaseCollector):
    """
    Собирает новости по указанным странам.
    """

    def __init__(self) -> None:
        self.client = NewsClient()

    @staticmethod
    async def get_file_path(filename: str = "", **kwargs: Any) -> str:
        """
        Возвращает путь к файлу для хранения данных новостей JSON.
        """
        return f"{MEDIA_PATH}/news/{filename}.json"

    @staticmethod
    async def get_cache_ttl() -> int:
        """
        Возвращает TTL (время жизни) кэша для новостных данных.
        """
        return CACHE_TTL_NEWS

    async def collect(
        self, locations: FrozenSet[LocationDTO] = frozenset(), **kwargs: Any
    ) -> None:
        """
        Собирает данные о новостях для указанных стран и сохраняет их в JSON.
        """
        target_dir_path = f"{MEDIA_PATH}/news"
        # если целевой директории еще не существует, то она создается
        if not await aiofiles.os.path.exists(target_dir_path):
            await aiofiles.os.mkdir(target_dir_path)

        for location in locations:
            filename = f"{location.country}".lower()

            # если кэш уже невалиден, то актуализируем его
            if await self.cache_invalid(filename=filename):
                result = await self.client.get_news(location.country)
                if result:
                    # сохраняем данные в JSON
                    result_str = json.dumps(result)
                    async with aiofiles.open(
                        await self.get_file_path(filename), mode="w"
                    ) as file:
                        await file.write(result_str)

    @classmethod
    async def read(cls, location: LocationDTO, number: int) -> Optional[NewsDTO]:
        """
        Чтение данных из кэша.
        :param location: Локация для получения данных
        :param number: Порядковый номер новости
        :return:
        """
        filename = f"{location.country}".lower()

        # читаем данные из JSON
        async with aiofiles.open(await cls.get_file_path(filename), mode="r") as file:
            content = await file.read()

        result = json.loads(content)
        if result:
            # возвращаем данные о новости
            article = result["articles"][number]
            return NewsDTO(
                source=article["source"]["name"],
                author=article["author"],
                published_at=article["publishedAt"],
                title=article["title"],
                description=article["description"],
            )

        return None

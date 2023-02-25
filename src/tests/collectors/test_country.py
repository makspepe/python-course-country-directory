"""
Тестирование функций сбора информации о странах.
"""

import pytest

from collectors.collector import CountryCollector


@pytest.mark.asyncio
class TestCollectorCountry:
    """
    Тестирование сбора информации о странах.
    """

    base_url = "https://api.apilayer.com/geo/country"

    @pytest.fixture
    def collector(self):
        return CountryCollector()

    async def test_collect(self, collector):
        assert await collector.collect() is not None

    async def test_read(cls, collector):
        assert await collector.read() is not None

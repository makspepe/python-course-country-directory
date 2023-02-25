"""
Тестирование функций клиента для получения информации о погоде.
"""


import pytest

from clients.weather import WeatherClient


class TestClientCountry:
    """
    Тестирование клиента для получения информации о странах.
    """

    base_url = "https://api.openweathermap.org/data/2.5/weather"

    @pytest.fixture
    def client(self):
        return WeatherClient()

    async def test_get_base_url(self, client):
        assert await client.get_base_url() == self.base_url

    async def test_get_countries(self, mocker, client):
        mocker.patch("clients.base.BaseClient._request")
        await client.get_weather("test")
        client._request.assert_called_with(self.base_url)
        assert client.params["q"] == "test"

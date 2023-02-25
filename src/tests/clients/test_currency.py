"""
Тестирование клиента для получения информации о валютах.
"""

import pytest

from clients.currency import CurrencyClient


class TestClientCountry:
    """
    Тестирование клиента для получения информации о валютах.
    """

    base_url = "https://api.apilayer.com/fixer/latest"

    @pytest.fixture
    def client(self):
        return CurrencyClient()

    async def test_get_base_url(self, client):
        assert await client.get_base_url() == self.base_url

    async def test_get_countries(self, mocker, client):
        mocker.patch("clients.base.BaseClient._request")
        await client.get_rates()
        client._request.assert_called_once_with(self.base_url)
        assert client.params == {"base": "rub"}

        await client.get_rates("test")
        client._request.assert_called_with(self.base_url)
        assert client.params == {"base": "test"}

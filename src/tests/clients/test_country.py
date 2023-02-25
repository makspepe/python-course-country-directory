"""
Тестирование функций клиента для получения информации о странах.
"""

import pytest

from clients.country import CountryClient

@pytest.mark.asyncio
class TestClientCountry:
    """
    Тестирование клиента для получения информации о странах.
    """

    base_url = "https://api.apilayer.com/geo/country"

    @pytest.fixture
    def client(self):
        return CountryClient()

    async def test_get_base_url(self, client):
        assert await client.get_base_url() == self.base_url

    async def test_get_countries(self, mocker, client):
        mocker.patch("clients.country.CountryClient._request")
        await client.get_countries()
        client._request.assert_called_once_with(f"{self.base_url}/regional_bloc/eu")

        await client.get_countries("test")
        client._request.assert_called_with(f"{self.base_url}/regional_bloc/test")

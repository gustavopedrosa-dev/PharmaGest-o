import os
import unittest
from unittest.mock import MagicMock, patch

import httpx

from api.xano import XanoClient, XanoError, XanoUnavailableError


class XanoConfigurationTests(unittest.TestCase):
    def test_rejects_example_workspace_url_before_network_request(self) -> None:
        with self.assertRaisesRegex(XanoError, "URL real"):
            XanoClient(base_url="https://seu-workspace.xano.io")

    def test_rejects_invalid_workspace_url(self) -> None:
        with self.assertRaisesRegex(XanoError, "URL real"):
            XanoClient(base_url="seu-workspace")

    def test_uses_a_valid_workspace_url(self) -> None:
        with patch.dict(
            os.environ,
            {"XANO_BASE_URL": "https://farmagestao.xano.io/"},
            clear=False,
        ):
            client = XanoClient()

        self.assertEqual(client.base_url, "https://farmagestao.xano.io")

    def test_context_reuses_http_client_and_closes_after_calls(self) -> None:
        products_response = MagicMock()
        products_response.status_code = 200
        products_response.json.return_value = {"produtos": []}

        categories_response = MagicMock()
        categories_response.status_code = 200
        categories_response.json.return_value = {"categorias": []}

        http_client = MagicMock()
        http_client.request.side_effect = [products_response, categories_response]

        with patch("api.xano.httpx.Client", return_value=http_client):
            client = XanoClient(base_url="https://example.test")
            with client:
                client.list_products("token-teste")
                client.list_categories("token-teste")

        self.assertEqual(http_client.request.call_count, 2)
        http_client.close.assert_called_once_with()
        self.assertIsNone(client._http_client)

    def test_context_closes_http_client_when_request_fails(self) -> None:
        http_client = MagicMock()
        http_client.request.side_effect = httpx.ConnectError("falha")

        with patch("api.xano.httpx.Client", return_value=http_client):
            client = XanoClient(base_url="https://example.test")
            with self.assertRaises(XanoUnavailableError):
                with client:
                    client.list_products("token-teste")

        http_client.close.assert_called_once_with()
        self.assertIsNone(client._http_client)

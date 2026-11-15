import os
import unittest
from unittest.mock import patch

from api.xano import XanoClient, XanoError


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

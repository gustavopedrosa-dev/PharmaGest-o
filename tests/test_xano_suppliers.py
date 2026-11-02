import json
import unittest

import httpx

from api.xano import (
    Supplier,
    XanoClient,
    XanoForbiddenError,
    XanoUnauthorizedError,
)


class SupplierClientTests(unittest.TestCase):
    def test_list_suppliers_sends_bearer_token_and_normalizes_optional_fields(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(
                request.url.path,
                "/api:94CoO3xX/produtos/fornecedores",
            )
            self.assertEqual(request.headers["Authorization"], "Bearer token")
            return httpx.Response(
                200,
                json={
                    "fornecedores": [
                        {
                            "id": 12,
                            "nome": "Distribuidora",
                            "cnpj": "12345678000199",
                            "telefone": None,
                            "email": "contato@example.test",
                            "endereco": "Rua A, 10",
                            "prazo_entrega": None,
                        }
                    ]
                },
            )

        suppliers = XanoClient(
            base_url="https://example.test",
            transport=httpx.MockTransport(handler),
        ).list_suppliers("token")

        self.assertEqual(
            suppliers,
            [
                Supplier(
                    id=12,
                    nome="Distribuidora",
                    cnpj="12345678000199",
                    telefone="",
                    email="contato@example.test",
                    endereco="Rua A, 10",
                    prazo_entrega="",
                )
            ],
        )

    def test_supplier_create_update_and_delete_use_expected_contracts(self) -> None:
        requests: list[tuple[str, str, dict[str, object] | None]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content) if request.content else None
            requests.append((request.method, request.url.path, body))
            self.assertEqual(request.headers["Authorization"], "Bearer token")
            if request.method == "DELETE":
                return httpx.Response(200, json={"sucesso": True})
            return httpx.Response(
                200,
                json={
                    "fornecedor": {
                        "id": 12,
                        "nome": body["nome"],
                        "cnpj": body["cnpj"],
                        "telefone": body["telefone"],
                        "email": body["email"],
                        "endereco": body["endereco"],
                        "prazo_entrega": body["prazo_entrega"],
                    }
                },
            )

        client = XanoClient(
            base_url="https://example.test",
            transport=httpx.MockTransport(handler),
        )
        supplier_data = {
            "nome": "Distribuidora",
            "cnpj": "12345678000199",
            "telefone": None,
            "email": "contato@example.test",
            "endereco": "Rua A, 10",
            "prazo_entrega": None,
        }

        created = client.create_supplier("token", supplier_data)
        updated = client.update_supplier("token", 12, supplier_data)
        client.delete_supplier("token", 12)

        self.assertEqual(created.id, 12)
        self.assertEqual(updated.nome, "Distribuidora")
        self.assertEqual(
            requests,
            [
                (
                    "POST",
                    "/api:94CoO3xX/produtos/fornecedor",
                    supplier_data,
                ),
                (
                    "PATCH",
                    "/api:94CoO3xX/produtos/fornecedor/12",
                    supplier_data,
                ),
                (
                    "DELETE",
                    "/api:94CoO3xX/produtos/fornecedor/12",
                    None,
                ),
            ],
        )

    def test_supplier_list_preserves_authentication_errors(self) -> None:
        for status_code, error_type in (
            (401, XanoUnauthorizedError),
            (403, XanoForbiddenError),
        ):
            with self.subTest(status_code=status_code):
                client = XanoClient(
                    base_url="https://example.test",
                    transport=httpx.MockTransport(
                        lambda request: httpx.Response(status_code)
                    ),
                )
                with self.assertRaises(error_type):
                    client.list_suppliers("token")


if __name__ == "__main__":
    unittest.main()
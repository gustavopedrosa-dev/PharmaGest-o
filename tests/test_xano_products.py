import unittest

import httpx

from api.xano import Product, XanoClient, XanoForbiddenError


class ProductClientTests(unittest.TestCase):
    def test_list_products_sends_bearer_token_and_normalizes_payload(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(
                request.url.path,
                "/api:94CoO3xX/produtos/estoque",
            )
            self.assertEqual(
                request.headers["Authorization"],
                "Bearer token",
            )
            return httpx.Response(
                200,
                json={
                    "produtos": [
                        {
                            "id": 1,
                            "id_categoria": 2,
                            "id_fornecedor": 3,
                            "nome": "Produto",
                            "descricao": None,
                            "codigo_barras": None,
                            "controlado": False,
                            "preco_venda": 10,
                            "quantidade_estoque": 2,
                            "estoque_minimo": 5,
                            "ativo": True,
                        }
                    ]
                },
            )

        products = XanoClient(
            base_url="https://example.test",
            transport=httpx.MockTransport(handler),
        ).list_products("token")

        self.assertEqual(
            products,
            [
                Product(
                    id=1,
                    id_categoria=2,
                    id_fornecedor=3,
                    nome="Produto",
                    descricao="",
                    codigo_barras="",
                    controlado=False,
                    preco_venda=10.0,
                    quantidade_estoque=2,
                    estoque_minimo=5,
                    ativo=True,
                )
            ],
        )

    def test_product_administration_preserves_forbidden_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(403, json={"message": "forbidden"})

        with self.assertRaises(XanoForbiddenError):
            XanoClient(
                base_url="https://example.test",
                transport=httpx.MockTransport(handler),
            ).create_category("token", "Categoria")


if __name__ == "__main__":
    unittest.main()

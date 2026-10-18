import unittest
import json

import httpx

from api.xano import Product, Sale, XanoClient, XanoForbiddenError


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

    def test_create_and_confirm_order_send_sales_payloads(self) -> None:
        paths: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            paths.append(request.url.path)
            self.assertEqual(request.headers["Authorization"], "Bearer token")
            if request.method == "POST" and request.url.path.endswith("/pedido"):
                self.assertEqual(
                    json.loads(request.content),
                    {
                        "id_cliente": None,
                        "canal": "presencial",
                        "itens": [{"id_produto": 7, "quantidade": 2}],
                    },
                )
                return httpx.Response(200, json={"pedido": {"id": 11}})
            self.assertEqual(
                json.loads(request.content),
                {"forma_pagamento": "pix", "numero_receita": None},
            )
            return httpx.Response(
                200,
                json={
                    "venda": {"id": 12},
                    "pagamento": {"id": 13},
                    "total": 20,
                },
            )

        client = XanoClient(
            base_url="https://example.test",
            transport=httpx.MockTransport(handler),
        )
        client.create_order(
            "token",
            client_id=None,
            channel="presencial",
            items=[{"id_produto": 7, "quantidade": 2}],
        )
        client.confirm_order("token", 11, "pix")
        self.assertEqual(
            paths,
            [
                "/api:8Ji5Nfc2/vendas/pedido",
                "/api:8Ji5Nfc2/vendas/pedido/11/confirmar",
            ],
        )

    def test_create_order_preserves_multiple_items(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(
                json.loads(request.content),
                {
                    "id_cliente": 9,
                    "canal": "presencial",
                    "itens": [
                        {"id_produto": 7, "quantidade": 1},
                        {"id_produto": 8, "quantidade": 2},
                    ],
                },
            )
            return httpx.Response(200, json={"pedido": {"id": 14}})

        order = XanoClient(
            base_url="https://example.test",
            transport=httpx.MockTransport(handler),
        ).create_order(
            "token",
            client_id=9,
            channel="presencial",
            items=[
                {"id_produto": 7, "quantidade": 1},
                {"id_produto": 8, "quantidade": 2},
            ],
        )

        self.assertEqual(order["pedido"]["id"], 14)

    def test_list_sales_normalizes_role_specific_response(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, "/api:8Ji5Nfc2/vendas/minhas")
            return httpx.Response(
                200,
                json={
                    "vendas": [
                        {
                            "id": 12,
                            "id_pedido": 11,
                            "data_venda": "2026-10-17T12:00:00Z",
                            "valor_total": 20,
                            "status": "concluída",
                        }
                    ]
                },
            )

        sales = XanoClient(
            base_url="https://example.test",
            transport=httpx.MockTransport(handler),
        ).list_sales("token", is_gestor=False)
        self.assertEqual(
            sales,
            [
                Sale(
                    id=12,
                    id_pedido=11,
                    data_venda="2026-10-17T12:00:00Z",
                    valor_total=20.0,
                    status="concluída",
                )
            ],
        )

    def test_list_orders_uses_role_specific_endpoint(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, "/api:8Ji5Nfc2/vendas/meus-pedidos")
            return httpx.Response(
                200,
                json={
                    "pedidos": [
                        {
                            "id": 11,
                            "id_cliente": None,
                            "id_funcionario": 4,
                            "data_pedido": "2026-10-17T12:00:00Z",
                            "status": "pendente",
                            "canal": "presencial",
                        }
                    ],
                    "itens": [
                        {
                            "id": 8,
                            "id_pedido": 11,
                            "id_produto": 7,
                            "quantidade": 2,
                            "valor_unitario": 10,
                        }
                    ],
                },
            )

        orders, items = XanoClient(
            base_url="https://example.test",
            transport=httpx.MockTransport(handler),
        ).list_orders("token", is_gestor=False)

        self.assertEqual(orders[0].id, 11)
        self.assertIsNone(orders[0].id_cliente)
        self.assertEqual(items[0]["id_produto"], 7)

    def test_list_sale_history_returns_payments(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, "/api:8Ji5Nfc2/vendas")
            return httpx.Response(
                200,
                json={
                    "vendas": [
                        {
                            "id": 12,
                            "id_pedido": 11,
                            "data_venda": "2026-10-17T12:00:00Z",
                            "valor_total": 20,
                            "status": "concluída",
                        }
                    ],
                    "pagamentos": [
                        {
                            "id": 13,
                            "id_venda": 12,
                            "forma_pagamento": "pix",
                            "valor": 20,
                        }
                    ],
                },
            )

        sales, payments = XanoClient(
            base_url="https://example.test",
            transport=httpx.MockTransport(handler),
        ).list_sale_history("token", is_gestor=True)

        self.assertEqual(sales[0].id, 12)
        self.assertEqual(payments[0]["forma_pagamento"], "pix")


if __name__ == "__main__":
    unittest.main()

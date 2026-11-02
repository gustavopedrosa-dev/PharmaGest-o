import json
import unittest
from datetime import datetime, timezone

import httpx

from api.xano import (
    Address,
    Customer,
    Employee,
    Product,
    Sale,
    XanoClient,
    XanoForbiddenError,
    XanoUnauthorizedError,
)


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

    def test_customer_and_address_operations_use_expected_contracts(self) -> None:
        requests: list[tuple[str, str]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append((request.method, request.url.path))
            self.assertEqual(request.headers["Authorization"], "Bearer token")
            if request.method == "POST" and request.url.path.endswith("/clientes/cliente"):
                self.assertEqual(
                    json.loads(request.content),
                    {"nome": "Maria", "cpf": None, "data_nascimento": "1990-01-01"},
                )
                return httpx.Response(
                    200,
                    json={
                        "cliente": {
                            "id": 5,
                            "nome": "Maria",
                            "data_nascimento": "1990-01-01",
                            "ativo": True,
                        }
                    },
                )
            if request.url.path.endswith("/clientes"):
                return httpx.Response(
                    200,
                    json={
                        "clientes": [
                            {
                                "id": 5,
                                "nome": "Maria",
                                "cpf": None,
                                "data_nascimento": "1990-01-01",
                                "telefone": None,
                                "email": None,
                                "data_cadastro": "2026-10-23T12:00:00Z",
                                "ativo": True,
                            }
                        ]
                    },
                )
            if request.url.path.endswith("/enderecos"):
                return httpx.Response(
                    200,
                    json={
                        "enderecos": [
                            {
                                "id": 8,
                                "id_cliente": 5,
                                "logradouro": "Rua A",
                                "numero": "10",
                                "bairro": "Centro",
                                "cidade": "Sao Paulo",
                                "estado": "SP",
                                "cep": None,
                                "complemento": "",
                            }
                        ]
                    },
                )
            if request.method == "POST" and request.url.path.endswith("/endereco"):
                self.assertEqual(json.loads(request.content), {"cidade": "Sao Paulo", "estado": "SP"})
                return httpx.Response(
                    200,
                    json={
                        "endereco": {
                            "id": 8,
                            "id_cliente": 5,
                            "cidade": "Sao Paulo",
                            "estado": "SP",
                        }
                    },
                )
            return httpx.Response(
                200,
                json={
                    "cliente": {
                        "id": 5,
                        "nome": "Maria",
                        "ativo": False,
                    }
                },
            )

        client = XanoClient(
            base_url="https://example.test",
            transport=httpx.MockTransport(handler),
        )
        customers = client.list_customers("token")
        created = client.create_customer(
            "token",
            {"nome": "Maria", "cpf": None, "data_nascimento": "1990-01-01"},
        )
        updated = client.update_customer("token", 5, {"nome": "Maria"})
        deactivated = client.deactivate_customer("token", 5)
        addresses = client.list_addresses("token", 5)
        address = client.create_address(
            "token",
            5,
            {"cidade": "Sao Paulo", "estado": "SP"},
        )

        self.assertEqual(customers[0], Customer(5, "Maria", "", "1990-01-01", "", "", "2026-10-23T12:00:00Z", True))
        self.assertEqual(created.id, 5)
        self.assertEqual(updated.id, 5)
        self.assertFalse(deactivated.ativo)
        self.assertEqual(addresses[0], Address(8, 5, "Rua A", "10", "Centro", "Sao Paulo", "SP", "", ""))
        self.assertEqual(address.id_cliente, 5)
        self.assertEqual(
            requests,
            [
                ("GET", "/api:n8EZtgGQ/clientes"),
                ("POST", "/api:n8EZtgGQ/clientes/cliente"),
                ("PATCH", "/api:n8EZtgGQ/clientes/cliente/5"),
                ("POST", "/api:n8EZtgGQ/clientes/cliente/5/inativar"),
                ("GET", "/api:n8EZtgGQ/clientes/cliente/5/enderecos"),
                ("POST", "/api:n8EZtgGQ/clientes/cliente/5/endereco"),
            ],
        )

    def test_customer_list_preserves_forbidden_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(403, json={"message": "forbidden"})

        with self.assertRaises(XanoForbiddenError):
            XanoClient(
                base_url="https://example.test",
                transport=httpx.MockTransport(handler),
            ).list_customers("token")

    def test_employee_operations_normalize_salary_and_credentials(self) -> None:
        paths: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            paths.append(request.url.path)
            self.assertEqual(request.headers["Authorization"], "Bearer token")
            if request.method == "GET":
                return httpx.Response(
                    200,
                    json={
                        "funcionarios": [
                            {
                                "id": 4,
                                "nome": "Colaborador",
                                "cpf": "123",
                                "data_nascimento": None,
                                "telefone": None,
                                "email": None,
                                "cargo": "Balconista",
                                "salario": 2500,
                                "data_admissao": "2026-11-02T00:00:00Z",
                            }
                        ],
                        "usuarios": [{"id_funcionario": 4, "ativo": False}],
                    },
                )
            if request.method == "POST" and request.url.path.endswith("/funcionario"):
                return httpx.Response(
                    200,
                    json={
                        "funcionario": {
                            "id": 4,
                            "nome": "Colaborador",
                            "cargo": "Balconista",
                            "salario": 2500,
                        },
                        "acesso": {
                            "login": "colaborador",
                            "senha_inicial": "temporary-only",
                        },
                    },
                )
            return httpx.Response(
                200,
                json={
                    "funcionario": {
                        "id": 4,
                        "nome": "Colaborador atualizado",
                        "cargo": "Balconista",
                        "salario": None,
                    }
                },
            )

        client = XanoClient(
            base_url="https://example.test",
            transport=httpx.MockTransport(handler),
        )
        employees = client.list_employees("token")
        created, access = client.create_employee("token", {"nome": "Colaborador"})
        updated = client.update_employee("token", 4, {"nome": "Colaborador atualizado"})
        deactivated = client.deactivate_employee("token", 4)

        self.assertEqual(
            employees[0],
            Employee(4, "Colaborador", "123", "", "", "", "Balconista", 2500.0, "2026-11-02T00:00:00Z", False),
        )
        self.assertEqual(created.id, 4)
        self.assertEqual(access["login"], "colaborador")
        self.assertEqual(access["senha_inicial"], "temporary-only")
        self.assertEqual(updated.nome, "Colaborador atualizado")
        self.assertIsNone(deactivated.salario)
        self.assertEqual(
            paths,
            [
                "/api:equipe/equipe/funcionarios",
                "/api:equipe/equipe/funcionario",
                "/api:equipe/equipe/funcionario/4",
                "/api:equipe/equipe/funcionario/4/inativar",
            ],
        )

    def test_employee_list_preserves_forbidden_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(403, json={"message": "forbidden"})

        with self.assertRaises(XanoForbiddenError):
            XanoClient(
                base_url="https://example.test",
                transport=httpx.MockTransport(handler),
            ).list_employees("token")

    def test_account_updates_use_identity_contract(self) -> None:
        requests: list[tuple[str, str, dict[str, object]]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append((request.method, request.url.path, json.loads(request.content)))
            return httpx.Response(
                200,
                json={
                    "sessao": {
                        "id_usuario": 2,
                        "id_funcionario": 4,
                        "nome": "Colaborador",
                        "login": "novo-login",
                        "perfil_acesso": "colaborador",
                    }
                },
            )

        client = XanoClient(
            base_url="https://example.test",
            transport=httpx.MockTransport(handler),
        )
        login = client.update_login("token", "novo-login")
        password = client.update_password("token", "senha-atual", "senha-nova")

        self.assertEqual(login.perfil_acesso, "colaborador")
        self.assertEqual(password.login, "novo-login")
        self.assertEqual(
            requests,
            [
                (
                    "PATCH",
                    "/api:identidade/identidade/minha-conta/login",
                    {"login": "novo-login"},
                ),
                (
                    "PATCH",
                    "/api:identidade/identidade/minha-conta/senha",
                    {"senha_atual": "senha-atual", "nova_senha": "senha-nova"},
                ),
            ],
        )

    def test_dashboard_summary_uses_authorized_endpoint_and_period(self) -> None:
        data_inicio = datetime(2026, 11, 2, tzinfo=timezone.utc)
        data_fim = datetime(2026, 11, 3, tzinfo=timezone.utc)
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            self.assertEqual(request.url.path, "/api:8Ji5Nfc2/painel/resumo")
            self.assertEqual(request.headers["Authorization"], "Bearer token")
            self.assertEqual(
                dict(request.url.params),
                {
                    "data_inicio": str(int(data_inicio.timestamp() * 1000)),
                    "data_fim": str(int(data_fim.timestamp() * 1000)),
                },
            )
            return httpx.Response(
                200,
                json={
                    "total_vendas": 2,
                    "valor_total": 50,
                    "funcionarios_ativos": 2,
                    "estoque_critico": [{"id": 7, "nome": "Dipirona", "estoque": 3, "minimo": 5}],
                    "mais_vendidos": [{"id": 7, "nome": "Dipirona", "quantidade": 3}],
                },
            )

        summary = XanoClient(
            base_url="https://example.test",
            transport=httpx.MockTransport(handler),
        ).dashboard_summary(
            "token",
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        self.assertEqual(summary["total_vendas"], 2)
        self.assertEqual(summary["valor_total"], 50)
        self.assertEqual(summary["funcionarios_ativos"], 2)
        self.assertEqual(summary["estoque_critico"][0]["nome"], "Dipirona")
        self.assertEqual(summary["mais_vendidos"][0]["nome"], "Dipirona")
        self.assertEqual(len(requests), 1)

    def test_dashboard_summary_preserves_authentication_errors(self) -> None:
        data_inicio = datetime(2026, 11, 2, tzinfo=timezone.utc)
        data_fim = datetime(2026, 11, 3, tzinfo=timezone.utc)

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
                    client.dashboard_summary(
                        "token",
                        data_inicio=data_inicio,
                        data_fim=data_fim,
                    )


if __name__ == "__main__":
    unittest.main()

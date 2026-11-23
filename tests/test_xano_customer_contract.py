import json
from pathlib import Path
import unittest

import httpx

from api.xano import Address, XanoClient, XanoUnavailableError
from connectdrogs.connectdrogs import (
    build_customer_address_payload,
    mark_customer_address_saved,
    persist_customer_addresses,
)


ROOT = Path(__file__).parents[1]


def read_xano(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


class CustomerXanoContractTests(unittest.TestCase):
    def test_customer_write_endpoints_require_collaborator_and_preserve_status_rules(self) -> None:
        create_script = read_xano("xano/api/clientes/cliente_POST.xs")
        update_script = read_xano("xano/api/clientes/cliente_PATCH.xs")
        deactivate_script = read_xano("xano/api/clientes/cliente_inativar_POST.xs")

        for script in (create_script, update_script, deactivate_script):
            self.assertIn('required_role: "colaborador"', script)
        self.assertIn('field_name = "cpf"', create_script)
        self.assertIn('$cliente_com_cpf == null', create_script)
        self.assertIn('$cliente_com_cpf.id == $input.id', update_script)
        self.assertIn("data = {ativo: false}", deactivate_script)

    def test_address_endpoints_require_existing_customer(self) -> None:
        create_script = read_xano("xano/api/clientes/endereco_POST.xs")
        list_script = read_xano("xano/api/clientes/enderecos_GET.xs")
        update_script = read_xano("xano/api/clientes/endereco_PATCH.xs")

        self.assertIn('field_value = $input.id', create_script)
        self.assertIn('precondition ($cliente != null)', create_script)
        self.assertIn('id_cliente: $input.id', create_script)
        self.assertIn('precondition ($cliente != null)', list_script)
        self.assertIn("$db.endereco.id_cliente == $input.id", list_script)
        self.assertIn('required_role: "colaborador"', update_script)
        self.assertIn('$endereco_existente.id_cliente == $input.id', update_script)
        self.assertIn('db.edit "endereco"', update_script)

    def test_update_address_uses_nested_patch_and_parses_address(self) -> None:
        address_data = {
            "logradouro": "Rua A",
            "numero": "10",
            "bairro": "Centro",
            "cidade": "São Paulo",
            "estado": "SP",
            "cep": "01000-000",
            "complemento": "Apto 2",
        }

        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "PATCH")
            self.assertEqual(
                request.url.path,
                "/api:n8EZtgGQ/clientes/cliente/42/endereco/17",
            )
            self.assertEqual(request.headers["Authorization"], "Bearer token")
            self.assertEqual(json.loads(request.content), address_data)
            return httpx.Response(
                200,
                json={
                    "endereco": {
                        "id": 17,
                        "id_cliente": 42,
                        **address_data,
                    }
                },
            )

        client = XanoClient(
            base_url="https://example.test",
            transport=httpx.MockTransport(handler),
        )

        address = client.update_address("token", 42, 17, address_data)

        self.assertEqual(
            address,
            Address(
                id=17,
                id_cliente=42,
                logradouro="Rua A",
                numero="10",
                bairro="Centro",
                cidade="São Paulo",
                estado="SP",
                cep="01000-000",
                complemento="Apto 2",
            ),
        )

    def test_list_addresses_parses_multiple_addresses_and_empty_result(self) -> None:
        addresses = [
            {
                "id": 17,
                "id_cliente": 42,
                "logradouro": "Rua A",
                "numero": "10",
                "bairro": "Centro",
                "cidade": "São Paulo",
                "estado": "SP",
                "cep": "01000-000",
                "complemento": "Apto 2",
            },
            {
                "id": 18,
                "id_cliente": 42,
                "logradouro": "Rua B",
                "numero": "20",
                "bairro": "Vila Nova",
                "cidade": "Campinas",
                "estado": "SP",
                "cep": "13000-000",
                "complemento": "",
            },
        ]

        def client_for(result: list[dict[str, object]]) -> XanoClient:
            def handler(request: httpx.Request) -> httpx.Response:
                self.assertEqual(request.method, "GET")
                self.assertEqual(
                    request.url.path,
                    "/api:n8EZtgGQ/clientes/cliente/42/enderecos",
                )
                self.assertEqual(request.headers["Authorization"], "Bearer token")
                return httpx.Response(200, json={"enderecos": result})

            return XanoClient(
                base_url="https://example.test",
                transport=httpx.MockTransport(handler),
            )

        listed = client_for(addresses).list_addresses("token", 42)
        empty = client_for([]).list_addresses("token", 42)

        self.assertEqual([address.id for address in listed], [17, 18])
        self.assertEqual([address.cidade for address in listed], ["São Paulo", "Campinas"])
        self.assertEqual(empty, [])

    def test_customer_address_form_validates_required_fields_and_normalizes_optional_fields(self) -> None:
        address = {
            "form_key": "0",
            "id": "",
            "logradouro": " Rua A ",
            "numero": " ",
            "bairro": " Centro ",
            "cidade": " São Paulo ",
            "estado": " SP ",
            "cep": " ",
            "complemento": " Apto 2 ",
        }

        payload, error = build_customer_address_payload(address)

        self.assertIsNone(error)
        self.assertEqual(
            payload,
            {
                "logradouro": "Rua A",
                "numero": None,
                "bairro": "Centro",
                "cidade": "São Paulo",
                "estado": "SP",
                "cep": None,
                "complemento": "Apto 2",
            },
        )
        address["estado"] = " "
        payload, error = build_customer_address_payload(address)
        self.assertIsNone(payload)
        self.assertEqual(error, "Cidade e estado são obrigatórios para cada endereço.")

    def test_created_address_id_is_retained_for_retry(self) -> None:
        addresses = [
            {"form_key": "0", "id": "", "cidade": "São Paulo"},
            {"form_key": "1", "id": "18", "cidade": "Campinas"},
        ]

        updated = mark_customer_address_saved(addresses, "0", 17)

        self.assertEqual(updated[0]["id"], "17")
        self.assertEqual(updated[1]["id"], "18")

    def test_partial_address_save_retains_created_id_when_later_patch_fails(self) -> None:
        calls: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.method)
            if request.method == "POST":
                return httpx.Response(
                    200,
                    json={
                        "endereco": {
                            "id": 17,
                            "id_cliente": 42,
                            "logradouro": "Rua Nova",
                            "numero": "10",
                            "bairro": "Centro",
                            "cidade": "São Paulo",
                            "estado": "SP",
                            "cep": "01000-000",
                            "complemento": "",
                        }
                    },
                )
            return httpx.Response(503, json={"message": "unavailable"})

        client = XanoClient(
            base_url="https://example.test",
            transport=httpx.MockTransport(handler),
        )
        addresses = [
            {
                "form_key": "new",
                "id": "",
                "logradouro": "Rua Nova",
                "numero": "10",
                "bairro": "Centro",
                "cidade": "São Paulo",
                "estado": "SP",
                "cep": "01000-000",
                "complemento": "",
            },
            {
                "form_key": "existing",
                "id": "18",
                "logradouro": "Rua Antiga",
                "numero": "20",
                "bairro": "Centro",
                "cidade": "São Paulo",
                "estado": "SP",
                "cep": "01000-000",
                "complemento": "",
            },
        ]

        saved, error = persist_customer_addresses(client, "token", 42, addresses)

        self.assertEqual(calls, ["POST", "PATCH"])
        self.assertEqual(saved[0]["id"], "17")
        self.assertEqual(saved[1]["id"], "18")
        self.assertIsInstance(error, XanoUnavailableError)

    def test_persist_multiple_addresses_updates_existing_and_creates_new(self) -> None:
        calls: list[tuple[str, str]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append((request.method, request.url.path))
            if request.method == "PATCH":
                return httpx.Response(
                    200,
                    json={
                        "endereco": {
                            "id": 18,
                            "id_cliente": 42,
                            "logradouro": "Rua Existente",
                            "numero": "20",
                            "bairro": "Centro",
                            "cidade": "São Paulo",
                            "estado": "SP",
                            "cep": "01000-000",
                            "complemento": "",
                        }
                    },
                )
            return httpx.Response(
                200,
                json={
                    "endereco": {
                        "id": 19,
                        "id_cliente": 42,
                        "logradouro": "Rua Nova",
                        "numero": "30",
                        "bairro": "Centro",
                        "cidade": "São Paulo",
                        "estado": "SP",
                        "cep": "01000-000",
                        "complemento": "",
                    }
                },
            )

        client = XanoClient(
            base_url="https://example.test",
            transport=httpx.MockTransport(handler),
        )
        addresses = [
            {
                "form_key": "existing",
                "id": "18",
                "logradouro": "Rua Existente",
                "numero": "20",
                "bairro": "Centro",
                "cidade": "São Paulo",
                "estado": "SP",
                "cep": "01000-000",
                "complemento": "",
            },
            {
                "form_key": "new",
                "id": "",
                "logradouro": "Rua Nova",
                "numero": "30",
                "bairro": "Centro",
                "cidade": "São Paulo",
                "estado": "SP",
                "cep": "01000-000",
                "complemento": "",
            },
        ]

        saved, error = persist_customer_addresses(client, "token", 42, addresses)

        self.assertIsNone(error)
        self.assertEqual([address["id"] for address in saved], ["18", "19"])
        self.assertEqual(
            calls,
            [
                ("PATCH", "/api:n8EZtgGQ/clientes/cliente/42/endereco/18"),
                ("POST", "/api:n8EZtgGQ/clientes/cliente/42/endereco"),
            ],
        )

    def test_order_creation_rejects_inactive_customer(self) -> None:
        script = read_xano("xano/api/vendas/pedido_POST.xs")

        self.assertIn('output = ["id", "ativo"]', script)
        self.assertIn('$cliente.ativo == true', script)
        self.assertIn('error = "O cliente não está ativo."', script)

    def test_controlled_sale_requires_prescription_number(self) -> None:
        script = read_xano("xano/api/vendas/venda_confirmar_POST.xs")

        self.assertIn(
            "Venda de medicamento controlado não pode ser realizada sem número da receita.",
            script,
        )
        self.assertIn("$input.numero_receita != null", script)
        self.assertIn('$input.numero_receita != ""', script)

    def test_employee_provisioning_uses_generated_password_and_role_guards(self) -> None:
        create_script = read_xano("xano/api/equipe/funcionario_POST.xs")
        list_script = read_xano("xano/api/equipe/funcionarios_GET.xs")
        deactivate_script = read_xano("xano/api/equipe/funcionario_inativar_POST.xs")
        activate_script = read_xano("xano/api/equipe/funcionario_ativar_POST.xs")
        account_login_script = read_xano(
            "xano/api/identidade/minha_conta_login_PATCH.xs"
        )
        account_password_script = read_xano(
            "xano/api/identidade/minha_conta_senha_PATCH.xs"
        )

        self.assertIn("security.create_password", create_script)
        self.assertIn("text? senha_inicial", create_script)
        self.assertIn("$senha_escolhida", create_script)
        self.assertIn('perfil_acesso: "colaborador"', create_script)
        self.assertIn("db.transaction", create_script)
        self.assertIn('required_role: "gestor"', create_script)
        self.assertIn('required_role: "gestor"', list_script)
        self.assertIn('required_role: "gestor"', deactivate_script)
        self.assertIn('required_role: "gestor"', activate_script)
        self.assertIn("data = {ativo: true}", activate_script)
        self.assertIn("ativo: true", activate_script)
        self.assertIn('output = ["id", "perfil_acesso"]', activate_script)
        self.assertIn("perfil_acesso: $usuario.perfil_acesso", activate_script)
        self.assertIn("text? endereco", create_script)
        self.assertIn("text? endereco", read_xano("xano/api/equipe/funcionario_PATCH.xs"))
        self.assertIn('required_role: "colaborador"', account_login_script)
        self.assertIn('required_role: "colaborador"', account_password_script)
        self.assertIn("security.check_password", account_password_script)


if __name__ == "__main__":
    unittest.main()
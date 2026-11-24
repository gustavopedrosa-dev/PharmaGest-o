from types import SimpleNamespace
import unittest
from unittest.mock import patch

import reflex as rx

from api.xano import (
    FORBIDDEN_MESSAGE,
    Address,
    Customer,
    Employee,
    Order,
    Product,
    Sale,
    SESSION_EXPIRED_MESSAGE,
    XanoForbiddenError,
    XanoUnauthorizedError,
)
from connectdrogs.connectdrogs import State


class LoginRedirectTests(unittest.TestCase):
    def login_as(
        self,
        perfil: str,
    ) -> tuple[SimpleNamespace, rx.event.EventSpec | None]:
        state = SimpleNamespace(
            login_input="usuario-teste",
            senha_input="senha-teste",
            senha_visivel=True,
            mensagem="",
        )
        state._set_session = lambda session: setattr(
            state,
            "perfil_acesso",
            session.perfil_acesso,
        )

        with patch("connectdrogs.connectdrogs.XanoClient") as client_class:
            client_class.return_value.login.return_value = (
                "token-teste",
                SimpleNamespace(perfil_acesso=perfil),
            )
            redirect = State.login_user.fn(state)

        if redirect is None:
            self.fail("A successful login must redirect to the profile landing page.")
        return state, redirect

    def redirect_path(self, redirect: rx.event.EventSpec) -> str:
        return redirect.args[0][1]._var_value

    def test_manager_login_redirects_to_dashboard(self) -> None:
        state, redirect = self.login_as("gestor")

        self.assertEqual(self.redirect_path(redirect), "/dashboard")
        self.assertEqual(state.mensagem, "")

    def test_collaborator_login_redirects_to_sales_without_permission_message(self) -> None:
        state, redirect = self.login_as("colaborador")

        self.assertEqual(self.redirect_path(redirect), "/vendas")
        self.assertEqual(state.mensagem, "")

    def test_collaborator_still_cannot_open_manager_dashboard_directly(self) -> None:
        state = SimpleNamespace(
            perfil_acesso="colaborador",
            mensagem="",
            _token="token-teste",
            _redirect_if_missing_token=lambda: None,
            _clear_dashboard=lambda: None,
        )

        redirect = State.load_dashboard.fn(state)

        if redirect is None:
            self.fail("A collaborator must not be allowed into the manager dashboard.")
        self.assertEqual(self.redirect_path(redirect), "/minha-conta")
        self.assertEqual(state.mensagem, FORBIDDEN_MESSAGE)

    def test_customer_loader_redirects_missing_token_without_xano_call(self) -> None:
        state = SimpleNamespace(
            _token="",
            session_ready=False,
            authenticated=True,
            mensagem="",
        )
        state._redirect_if_missing_token = lambda: State._redirect_if_missing_token(state)

        with patch("connectdrogs.connectdrogs.XanoClient") as client_class:
            redirect = State.load_customers.fn(state)

        self.assertEqual(self.redirect_path(redirect), "/login")
        self.assertFalse(state.authenticated)
        client_class.assert_not_called()

    def test_customer_loader_uses_data_endpoint_without_session_call(self) -> None:
        state = SimpleNamespace(
            _token="token-teste",
            mensagem="",
            clientes=[],
        )
        state._redirect_if_missing_token = lambda: State._redirect_if_missing_token(state)
        state._set_customers = lambda customers, *args: setattr(
            state,
            "clientes",
            customers,
        )
        state._expire_session = lambda: setattr(state, "authenticated", False)

        with patch("connectdrogs.connectdrogs.XanoClient") as client_class:
            client = client_class.return_value.__enter__.return_value
            client.list_customers.return_value = []
            client.list_addresses.return_value = []

            redirect = State.load_customers.fn(state)

        self.assertIsNone(redirect)
        client_class.assert_called_once_with()
        client.list_customers.assert_called_once_with("token-teste")
        client.session.assert_not_called()

    def test_unauthorized_data_response_expires_session(self) -> None:
        state = SimpleNamespace(
            _token="token-teste",
            mensagem="",
        )
        state._redirect_if_missing_token = lambda: State._redirect_if_missing_token(state)
        state._set_customers = lambda customers, *args: None
        state._expire_session = lambda: setattr(state, "authenticated", False)

        with patch("connectdrogs.connectdrogs.XanoClient") as client_class:
            client_class.return_value.__enter__.return_value.list_customers.side_effect = (
                XanoUnauthorizedError(SESSION_EXPIRED_MESSAGE, 401)
            )
            redirect = State.load_customers.fn(state)

        self.assertEqual(self.redirect_path(redirect), "/login")
        self.assertFalse(state.authenticated)

    def test_forbidden_data_response_keeps_session_and_shows_message(self) -> None:
        state = SimpleNamespace(
            _token="token-teste",
            mensagem="",
        )
        state._redirect_if_missing_token = lambda: State._redirect_if_missing_token(state)
        state._set_customers = lambda customers, *args: None
        state._expire_session = lambda: setattr(state, "authenticated", False)

        with patch("connectdrogs.connectdrogs.XanoClient") as client_class:
            client_class.return_value.__enter__.return_value.list_customers.side_effect = (
                XanoForbiddenError(FORBIDDEN_MESSAGE, 403)
            )
            redirect = State.load_customers.fn(state)

        self.assertIsNone(redirect)
        self.assertEqual(state.mensagem, FORBIDDEN_MESSAGE)
        self.assertTrue(state._token)

    def test_account_loader_keeps_identity_session_call(self) -> None:
        state = SimpleNamespace(
            _token="token-teste",
            session_ready=False,
            mensagem="",
        )

        state._redirect_if_missing_token = lambda: State._redirect_if_missing_token(state)
        state._set_session = lambda session: setattr(state, "nome", session.nome)

        session = SimpleNamespace(nome="Nome atualizado")
        with patch("connectdrogs.connectdrogs.XanoClient") as client_class:
            client_class.return_value.session.return_value = session
            redirect = State.load_session.fn(state)

        self.assertIsNone(redirect)
        client_class.return_value.session.assert_called_once_with("token-teste")
        self.assertEqual(state.nome, "Nome atualizado")
        self.assertTrue(state.session_ready)

    def test_manager_product_loader_does_not_call_session_separately(self) -> None:
        state = SimpleNamespace(
            _token="token-teste",
            perfil_acesso="gestor",
            is_gestor=True,
            mensagem="",
        )
        state._redirect_if_missing_token = lambda: State._redirect_if_missing_token(state)
        state._set_products = lambda products: None
        state._set_categories = lambda categories: None
        state._set_suppliers = lambda suppliers: None
        state._clear_suppliers = lambda: None

        with patch("connectdrogs.connectdrogs.XanoClient") as client_class:
            client = client_class.return_value.__enter__.return_value
            client.list_products.return_value = []
            client.list_categories.return_value = []
            client.list_suppliers.return_value = []

            redirect = State.load_products.fn(state)

        self.assertIsNone(redirect)
        client.list_products.assert_called_once_with("token-teste")
        client.list_categories.assert_called_once_with("token-teste")
        client.list_suppliers.assert_called_once_with("token-teste")
        client.session.assert_not_called()

    def test_collaborator_product_loader_does_not_call_session_separately(self) -> None:
        state = SimpleNamespace(
            _token="token-teste",
            perfil_acesso="colaborador",
            is_gestor=False,
            mensagem="",
        )
        state._redirect_if_missing_token = lambda: State._redirect_if_missing_token(state)
        state._set_products = lambda products: None
        state._set_categories = lambda categories: None
        state._set_suppliers = lambda suppliers: None
        state._clear_suppliers = lambda: None

        with patch("connectdrogs.connectdrogs.XanoClient") as client_class:
            client = client_class.return_value.__enter__.return_value
            client.list_products.return_value = []
            client.list_categories.return_value = []

            redirect = State.load_products.fn(state)

        self.assertIsNone(redirect)
        client.list_products.assert_called_once_with("token-teste")
        client.list_categories.assert_called_once_with("token-teste")
        client.list_suppliers.assert_not_called()
        client.session.assert_not_called()

    def test_sale_date_milliseconds_are_formatted_as_day_and_month(self) -> None:
        formatted = State._format_sale_date("1792281036290")

        self.assertRegex(formatted, r"^\d{2}/\d{2}$")

    def test_customer_fields_update_state_values(self) -> None:
        state = SimpleNamespace(
            cliente_nome="",
            cliente_cpf="",
            cliente_data_nascimento="",
            cliente_telefone="",
            cliente_email="",
        )

        State.set_customer_field.fn(
            state,
            "cliente_nome",
            "Maria Silva",
        )
        State.set_customer_field.fn(state, "cliente_cpf", "12345678900")
        State.set_customer_field.fn(
            state,
            "cliente_data_nascimento",
            "1990-05-20",
        )
        State.set_customer_field.fn(state, "cliente_telefone", "11999999999")
        State.set_customer_field.fn(state, "cliente_email", "maria@teste.com")

        self.assertEqual(state.cliente_nome, "Maria Silva")
        self.assertEqual(state.cliente_cpf, "12345678900")
        self.assertEqual(state.cliente_data_nascimento, "1990-05-20")
        self.assertEqual(state.cliente_telefone, "11999999999")
        self.assertEqual(state.cliente_email, "maria@teste.com")

    def test_customer_address_is_formatted_for_table_display(self) -> None:
        address = Address(
            id=18,
            id_cliente=7,
            logradouro="Rua das Flores",
            numero="123",
            bairro="Centro",
            cidade="São Paulo",
            estado="SP",
            cep="",
            complemento="",
        )

        formatted = State._format_customer_address(address)

        self.assertEqual(
            formatted,
            "Rua das Flores, 123, Centro, São Paulo, SP",
        )

    def test_customer_cpf_validation_accepts_only_valid_digits(self) -> None:
        self.assertTrue(State._is_valid_cpf("52998224725"))
        self.assertFalse(State._is_valid_cpf("12345678900"))
        self.assertFalse(State._is_valid_cpf("11111111111"))
        self.assertFalse(State._is_valid_cpf("5299822472"))

    def test_employee_cpf_field_accepts_only_digits_and_11_characters(self) -> None:
        state = SimpleNamespace(funcionario_cpf="")

        State.set_employee_field.fn(
            state,
            "funcionario_cpf",
            "529.982.247-25",
        )

        self.assertEqual(state.funcionario_cpf, "52998224725")

    def test_employee_cpf_validation_rejects_invalid_cpf(self) -> None:
        state = SimpleNamespace(
            funcionario_cpf="12345678900",
            mensagem="",
        )
        state._is_valid_cpf = State._is_valid_cpf

        self.assertFalse(State._valid_employee_cpf(state))
        self.assertEqual(
            state.mensagem,
            "Informe um CPF válido com 11 dígitos.",
        )

    def test_open_new_employee_clears_previous_address(self) -> None:
        state = SimpleNamespace(
            funcionario_id="",
            funcionario_nome="",
            funcionario_cpf="",
            funcionario_data_nascimento="",
            funcionario_telefone="",
            funcionario_email="",
            funcionario_endereco="Rua Anterior",
            funcionario_cargo="",
            funcionario_salario="",
            funcionario_login="",
            funcionario_senha_inicial="senha-anterior",
            funcionario_senha_inicial_visivel=True,
            acesso_inicial={"login": "anterior"},
            funcionario_editando=True,
            funcionario_modal_aberto=False,
        )
        state._clear_employee_form = lambda: State._clear_employee_form(state)

        State.open_new_employee.fn(state)

        self.assertEqual(state.funcionario_endereco, "")
        self.assertFalse(state.funcionario_editando)
        self.assertTrue(state.funcionario_modal_aberto)

    def test_edit_employee_loads_only_selected_address(self) -> None:
        state = SimpleNamespace(
            funcionarios=[
                {
                    "id": "4",
                    "nome": "Ana",
                    "cpf": "52998224725",
                    "telefone": "",
                    "email": "",
                    "endereco": "Rua Ana, 123",
                    "cargo": "Colaborador",
                    "salario": "R$ 2000.00",
                },
                {
                    "id": "5",
                    "nome": "Bruno",
                    "cpf": "52998224725",
                    "telefone": "",
                    "email": "",
                    "endereco": "Rua Bruno, 456",
                    "cargo": "Colaborador",
                    "salario": "R$ 2500.00",
                },
            ],
            funcionario_endereco="",
            mensagem="",
            funcionario_modal_aberto=False,
        )

        State.edit_employee.fn(state, "4")

        self.assertEqual(state.funcionario_endereco, "Rua Ana, 123")
        self.assertTrue(state.funcionario_modal_aberto)

    def test_employee_initial_password_is_accepted_as_custom_value(self) -> None:
        state = SimpleNamespace(
            funcionario_nome="Ana",
            funcionario_cpf="52998224725",
            funcionario_data_nascimento="",
            funcionario_telefone="",
            funcionario_email="",
            funcionario_cargo="colaborador",
            funcionario_salario="",
            funcionario_endereco="Rua A",
            funcionario_login="ana",
            funcionario_senha_inicial="Ana2026!",
        )

        payload = State._employee_payload(state, include_login=True)

        self.assertEqual(payload["login"], "ana")
        self.assertEqual(payload["senha_inicial"], "Ana2026!")
        self.assertEqual(payload["endereco"], "Rua A")

    def test_employee_create_rejects_existing_cpf(self) -> None:
        state = SimpleNamespace(
            is_gestor=True,
            funcionario_cpf="52998224725",
            funcionario_nome="Ana",
            funcionario_login="ana",
            funcionarios=[
                {"id": "4", "cpf": "529.982.247-25"},
            ],
            mensagem="",
        )
        state._valid_employee_cpf = lambda: State._valid_employee_cpf(state)
        state._is_valid_cpf = State._is_valid_cpf

        with patch("connectdrogs.connectdrogs.XanoClient") as client_class:
            State.create_employee.fn(state)

        self.assertEqual(state.mensagem, "O CPF já está cadastrado.")
        client_class.assert_not_called()

    def test_employee_update_allows_own_cpf_and_rejects_another_employee(self) -> None:
        state = SimpleNamespace(
            funcionario_id="4",
            funcionario_cpf="52998224725",
            funcionarios=[
                {"id": "4", "cpf": "52998224725"},
                {"id": "5", "cpf": "11144477735"},
            ],
        )
        self.assertTrue(State._valid_employee_update_cpf(state))

        state.funcionario_cpf = "11144477735"
        state.mensagem = ""
        self.assertFalse(State._valid_employee_update_cpf(state))
        self.assertEqual(state.mensagem, "O CPF já está cadastrado.")

    def test_employee_activation_changes_status_to_active(self) -> None:
        state = SimpleNamespace(
            is_gestor=True,
            funcionario_id="4",
            funcionario_ativo=False,
            funcionario_acao_pendente="reativar",
            confirmando_inativacao=True,
            mensagem="",
            funcionarios=[
                {
                    "id": "4",
                    "nome": "Ana",
                    "cpf": "52998224725",
                    "telefone": "11999999999",
                    "email": "ana@example.com",
                    "endereco": "Rua Ana, 123",
                    "cargo": "Colaborador",
                    "salario": "R$ 2000.00",
                    "situacao": "inativo",
                }
            ],
            _token="token-teste",
        )
        state._employee_view = lambda employee: State._employee_view(employee)
        state._set_employees = lambda employees: State._set_employees(state, employees)

        activated = Employee(
            id=4,
            nome="Ana",
            cpf="52998224725",
            data_nascimento="",
            telefone="11999999999",
            email="ana@example.com",
            cargo="Colaborador",
            salario=2000,
            data_admissao="",
            ativo=True,
            endereco="Rua Ana, 123",
        )

        with patch("connectdrogs.connectdrogs.XanoClient") as client_class:
            client_class.return_value.last_request_url = (
                "https://example.test/api:equipe/equipe/funcionario/4/ativar"
            )
            client_class.return_value.last_response_status = 200
            client_class.return_value.last_response_body = {
                "keys": ["ativo", "funcionario"],
                "funcionario_id": 4,
                "ativo": True,
            }
            client_class.return_value.activate_employee.return_value = activated
            client_class.return_value.list_employees.return_value = [activated]

            State.deactivate_employee.fn(state)

        client_class.return_value.activate_employee.assert_called_once_with(
            "token-teste",
            4,
        )
        client_class.return_value.deactivate_employee.assert_not_called()
        row = state.funcionarios[0]
        self.assertTrue(state.funcionario_ativo)
        self.assertEqual(row["situacao"], "ativo")
        self.assertEqual(state.mensagem, "Funcionário reativado.")
        self.assertFalse(state.confirmando_inativacao)

    def test_employee_activation_uses_pending_action_instead_of_boolean(self) -> None:
        state = SimpleNamespace(
            is_gestor=True,
            funcionario_id="4",
            funcionario_ativo=True,
            funcionario_acao_pendente="reativar",
            confirmando_inativacao=True,
            mensagem="",
            funcionarios=[
                {
                    "id": "4",
                    "nome": "Ana",
                    "cpf": "52998224725",
                    "telefone": "11999999999",
                    "email": "ana@example.com",
                    "endereco": "Rua Ana, 123",
                    "cargo": "Colaborador",
                    "salario": "R$ 2000.00",
                    "situacao": "inativo",
                }
            ],
            _token="token-teste",
        )
        state._employee_view = lambda employee: State._employee_view(employee)
        state._set_employees = lambda employees: State._set_employees(state, employees)

        activation_result = Employee(
            id=4,
            nome="Ana",
            cpf="52998224725",
            data_nascimento="",
            telefone="11999999999",
            email="ana@example.com",
            cargo="Colaborador",
            salario=2000,
            data_admissao="",
            ativo=True,
            endereco="Rua Ana, 123",
        )

        with patch("connectdrogs.connectdrogs.XanoClient") as client_class:
            client_class.return_value.last_request_url = (
                "https://example.test/api:equipe/equipe/funcionario/4/ativar"
            )
            client_class.return_value.last_response_status = 200
            client_class.return_value.last_response_body = {
                "keys": ["ativo", "funcionario"],
                "funcionario_id": 4,
                "ativo": True,
            }
            client_class.return_value.activate_employee.return_value = activation_result
            client_class.return_value.list_employees.return_value = [activation_result]

            State.deactivate_employee.fn(state)

        self.assertTrue(state.funcionario_ativo)
        self.assertEqual(state.funcionarios[0]["situacao"], "ativo")
        self.assertEqual(state.mensagem, "Funcionário reativado.")

    def test_reactivation_selection_stores_pending_action(self) -> None:
        state = SimpleNamespace(
            is_gestor=True,
            funcionarios=[
                {
                    "id": "4",
                    "nome": "Ana",
                    "situacao": "inativo",
                }
            ],
            funcionario_id="",
            funcionario_nome="",
            funcionario_ativo=True,
            funcionario_acao_pendente="",
            confirmando_inativacao=False,
            mensagem="",
            request_deactivate_employee=lambda: setattr(
                state,
                "confirmando_inativacao",
                True,
            ),
        )

        State.request_deactivate_employee_by_id.fn(state, "4")

        self.assertEqual(state.funcionario_id, "4")
        self.assertEqual(state.funcionario_acao_pendente, "reativar")
        self.assertFalse(state.funcionario_ativo)
        self.assertTrue(state.confirmando_inativacao)

    def test_save_employee_updates_existing_employee(self) -> None:
        state = SimpleNamespace(
            is_gestor=True,
            funcionario_editando=True,
            funcionario_login="",
            funcionario_nome="Ana",
            funcionario_cpf="52998224725",
            funcionario_id="4",
            funcionario_data_nascimento="",
            funcionario_telefone="11999999999",
            funcionario_email="ana@example.com",
            funcionario_cargo="Colaborador",
            funcionario_salario="2000",
            funcionario_endereco="Rua A",
            funcionario_senha_inicial="",
            funcionarios=[],
            mensagem="",
            _token="token-teste",
        )
        state._valid_employee_cpf = lambda: State._valid_employee_cpf(state)
        state._is_valid_cpf = State._is_valid_cpf
        state._valid_employee_update_cpf = (
            lambda: State._valid_employee_update_cpf(state)
        )
        state._employee_payload = lambda include_login=False: State._employee_payload(
            state,
            include_login=include_login,
        )
        state._employee_view = lambda employee: State._employee_view(employee)
        state.close_employee_modal = lambda: setattr(
            state,
            "funcionario_modal_aberto",
            False,
        )

        updated_employee = Employee(
            id=4,
            nome="Ana",
            cpf="52998224725",
            data_nascimento="",
            telefone="11999999999",
            email="ana@example.com",
            cargo="Colaborador",
            salario=2000,
            data_admissao="",
            ativo=True,
            endereco="Rua A",
        )

        with patch("connectdrogs.connectdrogs.XanoClient") as client_class:
            client_class.return_value.update_employee.return_value = updated_employee

            State.save_employee.fn(state)

        client_class.return_value.update_employee.assert_called_once()
        self.assertEqual(state.mensagem, "Funcionário atualizado.")

    def test_create_customer_rejects_invalid_cpf_before_xano_call(self) -> None:
        state = SimpleNamespace(
            is_gestor=False,
            cliente_cpf="12345678900",
            mensagem="",
        )
        state._valid_customer_cpf = lambda: State._valid_customer_cpf(state)
        state._is_valid_cpf = State._is_valid_cpf

        with patch("connectdrogs.connectdrogs.XanoClient") as client_class:
            State.create_customer.fn(state)

        self.assertEqual(
            state.mensagem,
            "Informe um CPF válido com 11 dígitos.",
        )
        client_class.assert_not_called()

    def test_sale_fields_update_state_values(self) -> None:
        state = SimpleNamespace(
            venda_produto_id="",
            venda_quantidade="1",
            venda_cliente_id="",
            venda_canal="presencial",
            venda_pagamento="dinheiro",
            venda_receita="",
        )

        State.set_sale_field.fn(state, "venda_produto_id", "7")
        State.set_sale_field.fn(state, "venda_quantidade", "2")
        State.set_sale_field.fn(state, "venda_cliente_id", "9")
        State.set_sale_field.fn(state, "venda_canal", "online")
        State.set_sale_field.fn(state, "venda_pagamento", "pix")
        State.set_sale_field.fn(state, "venda_receita", "123")

        self.assertEqual(state.venda_produto_id, "7")
        self.assertEqual(state.venda_quantidade, "2")
        self.assertEqual(state.venda_cliente_id, "9")
        self.assertEqual(state.venda_canal, "online")
        self.assertEqual(state.venda_pagamento, "pix")
        self.assertEqual(state.venda_receita, "123")

    def test_create_sale_creates_and_confirms_order(self) -> None:
        state = SimpleNamespace(
            is_gestor=False,
            mensagem="",
            _token="token-teste",
            authenticated=True,
            venda_cliente_id="",
            venda_canal="presencial",
            venda_pagamento="pix",
            venda_receita="",
            venda_itens=[{"id_produto": "7", "quantidade": "2"}],
            venda_produto_id="",
            venda_quantidade="1",
        )
        state._expire_session = lambda: setattr(state, "authenticated", False)

        with patch("connectdrogs.connectdrogs.XanoClient") as client_class:
            client = client_class.return_value
            client.create_order.return_value = {"pedido": {"id": 11}}
            client.confirm_order.return_value = {"venda": {"id": 12}}

            redirect = State.create_sale.fn(state)

        self.assertIsNone(redirect)
        client.create_order.assert_called_once_with(
            "token-teste",
            client_id=None,
            channel="presencial",
            items=[{"id_produto": 7, "quantidade": 2}],
        )
        client.confirm_order.assert_called_once_with(
            "token-teste",
            11,
            "pix",
            None,
        )
        self.assertEqual(state.mensagem, "Venda confirmada.")
        self.assertEqual(state.venda_itens, [])

    def test_add_sale_item_displays_product_name_and_quantity(self) -> None:
        state = SimpleNamespace(
            venda_produto_id="7",
            venda_quantidade="2",
            venda_itens=[],
            mensagem="",
            produtos=[
                {
                    "id": "7",
                    "nome": "Dipirona",
                    "controlado": "—",
                    "preco": "R$ 12.50",
                }
            ],
        )

        State.add_sale_item.fn(state)

        self.assertEqual(
            state.venda_itens,
            [
                {
                    "id_produto": "7",
                    "nome": "Dipirona",
                    "quantidade": "2",
                    "preco": "12.50",
                }
            ],
        )
        self.assertEqual(state.venda_produto_id, "")
        self.assertEqual(state.venda_quantidade, "1")
        self.assertEqual(state.mensagem, "")

    def test_sale_total_sums_unit_price_by_quantity(self) -> None:
        state = SimpleNamespace(
            venda_itens=[
                {"preco": "12.50", "quantidade": "2"},
                {"preco": "8.25", "quantidade": "1"},
            ]
        )

        total = State.venda_valor_total.fget(state)
        state.venda_valor_total = total
        formatted = State.venda_valor_total_brl.fget(state)

        self.assertEqual(total, 33.25)
        self.assertEqual(formatted, "R$ 33,25")

    def test_controlled_sale_requires_prescription_number_before_api_calls(self) -> None:
        state = SimpleNamespace(
            is_gestor=False,
            mensagem="",
            _token="token-teste",
            authenticated=True,
            venda_cliente_id="9",
            venda_canal="presencial",
            venda_pagamento="dinheiro",
            venda_receita="",
            venda_itens=[{"id_produto": "7", "quantidade": "1"}],
            venda_produto_id="",
            venda_quantidade="1",
            produtos=[
                {
                    "id": "7",
                    "nome": "Medicamento controlado",
                    "controlado": "Sim",
                }
            ],
        )

        with patch("connectdrogs.connectdrogs.XanoClient") as client_class:
            redirect = State.create_sale.fn(state)

        self.assertIsNone(redirect)
        client_class.assert_not_called()
        self.assertEqual(
            state.mensagem,
            "Venda de medicamento controlado não pode ser realizada sem número da receita.",
        )
        self.assertEqual(
            state.venda_itens,
            [{"id_produto": "7", "quantidade": "1"}],
        )

    def test_manager_sales_show_names_instead_of_related_ids(self) -> None:
        state = SimpleNamespace(
            _token="token-teste",
            is_gestor=True,
            mensagem="",
            vendas=[],
            pedidos=[],
            itens_pedido=[],
        )
        state._redirect_if_missing_token = lambda: None
        state._format_sale_date = lambda value: State._format_sale_date(value)

        sale = Sale(
            id=12,
            id_pedido=11,
            data_venda="2026-10-17T12:00:00Z",
            valor_total=20,
            status="concluída",
        )
        order = Order(
            id=11,
            id_cliente=7,
            id_funcionario=3,
            data_pedido="2026-10-17T12:00:00Z",
            status="concluído",
            canal="presencial",
        )
        product = Product(
            id=2,
            id_categoria=1,
            id_fornecedor=1,
            nome="Dipirona",
            descricao="",
            codigo_barras="",
            controlado=False,
            preco_venda=12.5,
            quantidade_estoque=10,
            estoque_minimo=2,
            ativo=True,
        )
        customer = Customer(
            id=7,
            nome="Maria Silva",
            cpf="",
            data_nascimento="",
            telefone="",
            email="",
            data_cadastro="",
            ativo=True,
        )
        employee = Employee(
            id=3,
            nome="Guilherme",
            cpf="",
            data_nascimento="",
            telefone="",
            email="",
            cargo="Colaborador",
            salario=None,
            data_admissao="",
            ativo=True,
        )

        with patch("connectdrogs.connectdrogs.XanoClient") as client_class:
            client = client_class.return_value.__enter__.return_value
            client.list_sale_history.return_value = (
                [sale],
                [{"id_venda": 12, "forma_pagamento": "pix"}],
            )
            client.list_orders.return_value = (
                [order],
                [{"id_pedido": 11, "id_produto": 2, "quantidade": 1}],
            )
            client.list_products.return_value = [product]
            client.list_customers.return_value = [customer]
            client.list_employees.return_value = [employee]

            redirect = State.load_sales.fn(state)

        self.assertIsNone(redirect)
        self.assertEqual(state.vendas[0]["cliente"], "Maria Silva")
        self.assertEqual(state.vendas[0]["produtos"], "1x Dipirona")
        self.assertEqual(state.vendas[0]["atendente"], "Guilherme")

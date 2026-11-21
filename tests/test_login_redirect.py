from types import SimpleNamespace
import unittest
from unittest.mock import patch

import reflex as rx

from api.xano import (
    FORBIDDEN_MESSAGE,
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
        state._set_customers = lambda customers: setattr(state, "clientes", customers)
        state._expire_session = lambda: setattr(state, "authenticated", False)

        with patch("connectdrogs.connectdrogs.XanoClient") as client_class:
            client = client_class.return_value.__enter__.return_value
            client.list_customers.return_value = []

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
        state._set_customers = lambda customers: None
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
        state._set_customers = lambda customers: None
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

from types import SimpleNamespace
import unittest
from unittest.mock import patch

import reflex as rx

from api.xano import FORBIDDEN_MESSAGE
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
            load_session=lambda: None,
            _clear_dashboard=lambda: None,
        )

        redirect = State.load_dashboard.fn(state)

        if redirect is None:
            self.fail("A collaborator must not be allowed into the manager dashboard.")
        self.assertEqual(self.redirect_path(redirect), "/minha-conta")
        self.assertEqual(state.mensagem, FORBIDDEN_MESSAGE)

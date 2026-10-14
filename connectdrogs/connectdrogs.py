"""Frontend do FarmaGestão para autenticação e navegação por perfil."""

from __future__ import annotations

import reflex as rx

from api.xano import (
    FORBIDDEN_MESSAGE,
    SESSION_EXPIRED_MESSAGE,
    UNAVAILABLE_MESSAGE,
    Session,
    XanoClient,
    XanoError,
    XanoForbiddenError,
    XanoUnauthorizedError,
    XanoUnavailableError,
)
from rxconfig import config


class State(rx.State):
    """Estado server-side; o token privado nunca é serializado para o navegador."""

    _token: str = ""
    session_ready: bool = False
    authenticated: bool = False
    nome: str = ""
    login: str = ""
    perfil_acesso: str = ""
    mensagem: str = ""
    login_input: str = ""
    senha_input: str = ""
    novo_login: str = ""
    senha_atual: str = ""
    nova_senha: str = ""

    @rx.var
    def is_gestor(self) -> bool:
        return self.perfil_acesso == "gestor"

    @rx.event
    def set_login_input(self, value: str) -> None:
        self.login_input = value

    @rx.event
    def set_senha_input(self, value: str) -> None:
        self.senha_input = value

    @rx.event
    def set_novo_login(self, value: str) -> None:
        self.novo_login = value

    @rx.event
    def set_senha_atual(self, value: str) -> None:
        self.senha_atual = value

    @rx.event
    def set_nova_senha(self, value: str) -> None:
        self.nova_senha = value

    @rx.event
    def login_user(self) -> rx.event.EventSpec | None:
        try:
            token, session = XanoClient().login(self.login_input, self.senha_input)
        except XanoError as exc:
            self.mensagem = (
                "usuário ou senha inválidos"
                if exc.status_code == 401
                else exc.message
            )
            return None
        self._token = token
        self._set_session(session)
        self.senha_input = ""
        return rx.redirect("/dashboard")

    @rx.event
    def load_session(self) -> rx.event.EventSpec | None:
        if not self._token:
            self.session_ready = True
            self.authenticated = False
            return rx.redirect("/login")
        try:
            self._set_session(XanoClient().session(self._token))
        except XanoUnauthorizedError:
            self._expire_session()
            return rx.redirect("/login")
        except XanoUnavailableError:
            self.mensagem = UNAVAILABLE_MESSAGE
        except XanoError as exc:
            self.mensagem = exc.message
        self.session_ready = True
        return None

    @rx.event
    def load_dashboard(self) -> rx.event.EventSpec | None:
        redirect = self.load_session()
        if redirect is not None:
            return redirect
        if self.perfil_acesso != "gestor":
            self.mensagem = FORBIDDEN_MESSAGE
            return rx.redirect("/minha-conta")
        return None

    @rx.event
    def logout(self) -> rx.event.EventSpec:
        self.logout_local()
        return rx.redirect("/login")

    @rx.event
    def update_login(self) -> rx.event.EventSpec | None:
        try:
            self._set_session(XanoClient().update_login(self._token, self.novo_login))
            self.mensagem = "Login atualizado."
            self.novo_login = ""
        except XanoUnauthorizedError:
            self._expire_session()
            return rx.redirect("/login")
        except XanoForbiddenError:
            self.mensagem = FORBIDDEN_MESSAGE
        except XanoUnavailableError:
            self.mensagem = UNAVAILABLE_MESSAGE
        except XanoError as exc:
            self.mensagem = exc.message
        return None

    @rx.event
    def update_password(self) -> rx.event.EventSpec | None:
        try:
            self._set_session(
                XanoClient().update_password(
                    self._token,
                    self.senha_atual,
                    self.nova_senha,
                )
            )
            self.mensagem = "Senha atualizada."
            self.senha_atual = ""
            self.nova_senha = ""
        except XanoUnauthorizedError:
            self._expire_session()
            return rx.redirect("/login")
        except XanoForbiddenError:
            self.mensagem = FORBIDDEN_MESSAGE
        except XanoUnavailableError:
            self.mensagem = UNAVAILABLE_MESSAGE
        except XanoError as exc:
            self.mensagem = exc.message
        return None

    def _set_session(self, session: Session) -> None:
        self.nome = session.nome
        self.login = session.login
        self.perfil_acesso = session.perfil_acesso
        self.authenticated = True
        self.session_ready = True
        self.mensagem = ""

    def logout_local(self) -> None:
        self._token = ""
        self.authenticated = False
        self.session_ready = True
        self.nome = ""
        self.login = ""
        self.perfil_acesso = ""

    def _expire_session(self) -> None:
        self.logout_local()
        self.mensagem = SESSION_EXPIRED_MESSAGE


def login_page() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("FarmaGestão", size="8"),
            rx.text("Entre com seu usuário."),
            rx.input(
                placeholder="Login",
                value=State.login_input,
                on_change=State.set_login_input,
            ),
            rx.input(
                placeholder="Senha",
                type="password",
                value=State.senha_input,
                on_change=State.set_senha_input,
            ),
            rx.button("Entrar", on_click=State.login_user),
            rx.cond(State.mensagem != "", rx.text(State.mensagem, color="red")),
            width="100%",
            max_width="28rem",
            padding="2rem",
        ),
        min_height="100vh",
    )


def navigation() -> rx.Component:
    return rx.hstack(
        rx.cond(
            State.is_gestor,
            rx.link("Painel", href="/dashboard"),
            rx.text("Atendimento"),
        ),
        rx.link("Minha conta", href="/minha-conta"),
        rx.button("Sair", on_click=State.logout),
        justify="between",
        width="100%",
    )


def protected_layout(content: rx.Component) -> rx.Component:
    return rx.cond(
        State.authenticated,
        rx.vstack(navigation(), content, width="100%", padding="2rem"),
        rx.center(rx.text("Carregando..."), min_height="100vh"),
    )


def dashboard_page() -> rx.Component:
    return protected_layout(
        rx.vstack(
            rx.heading("Painel do gestor"),
            rx.text("Bem-vindo, ", State.nome, "."),
        )
    )


def account_page() -> rx.Component:
    return protected_layout(
        rx.vstack(
            rx.heading("Minha conta"),
            rx.text("Usuário: ", State.login),
            rx.input(
                placeholder="Novo login",
                value=State.novo_login,
                on_change=State.set_novo_login,
            ),
            rx.button("Salvar login", on_click=State.update_login),
            rx.input(
                placeholder="Senha atual",
                type="password",
                value=State.senha_atual,
                on_change=State.set_senha_atual,
            ),
            rx.input(
                placeholder="Nova senha",
                type="password",
                value=State.nova_senha,
                on_change=State.set_nova_senha,
            ),
            rx.button("Salvar senha", on_click=State.update_password),
            rx.cond(State.mensagem != "", rx.text(State.mensagem)),
        )
    )


app = rx.App()
app.add_page(login_page, route="/login")
app.add_page(dashboard_page, route="/dashboard", on_load=State.load_dashboard)
app.add_page(account_page, route="/minha-conta", on_load=State.load_session)
app.add_page(login_page, route="/")

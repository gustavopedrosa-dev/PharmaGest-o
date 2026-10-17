"""Cliente HTTP server-side para as APIs de identidade do Xano."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx


AUTH_INVALID_MESSAGE = "usuÃ¡rio ou senha invÃ¡lidos"
SESSION_EXPIRED_MESSAGE = "SessÃ£o expirada. Entre novamente."
FORBIDDEN_MESSAGE = "VocÃª nÃ£o tem permissÃ£o para esta aÃ§Ã£o"
UNAVAILABLE_MESSAGE = "ServiÃ§o indisponÃ­vel, tente novamente"


class XanoError(Exception):
    """Erro de comunicaÃ§Ã£o ou de contrato retornado pelo Xano."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class XanoUnauthorizedError(XanoError):
    """A sessÃ£o nÃ£o existe, expirou ou pertence a uma conta inativa."""


class XanoForbiddenError(XanoError):
    """A identidade autenticada nÃ£o possui a permissÃ£o necessÃ¡ria."""


class XanoUnavailableError(XanoError):
    """O backend estÃ¡ indisponÃ­vel ou excedeu o timeout."""


@dataclass(frozen=True)
class Session:
    user_id: int
    funcionario_id: int
    nome: str
    login: str
    perfil_acesso: str


@dataclass(frozen=True)
class Product:
    id: int
    id_categoria: int
    id_fornecedor: int
    nome: str
    descricao: str
    codigo_barras: str
    controlado: bool
    preco_venda: float
    quantidade_estoque: int
    estoque_minimo: int
    ativo: bool


@dataclass(frozen=True)
class Category:
    id: int
    nome: str
    ativo: bool


def _message_from_response(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text or "Erro ao comunicar com o Xano."
    if isinstance(payload, dict):
        for key in ("message", "error", "detail"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
    return "Erro ao comunicar com o Xano."


class XanoClient:
    """Adaptador Ãºnico para chamadas autenticadas feitas pelo servidor Reflex."""

    def __init__(
        self,
        base_url: str | None = None,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 10.0,
    ) -> None:
        configured_url = base_url or os.environ.get("XANO_BASE_URL", "")
        if not configured_url:
            raise XanoError("XANO_BASE_URL nÃ£o configurada.")
        self.base_url = configured_url.rstrip("/")
        self.timeout = timeout
        self._transport = transport

    def _request(
        self,
        method: str,
        path: str,
        token: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        headers = dict(kwargs.pop("headers", {}))
        if token:
            headers["Authorization"] = "Bearer " + token
        try:
            with httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout,
                transport=self._transport,
            ) as client:
                response = client.request(method, path, headers=headers, **kwargs)
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise XanoUnavailableError(UNAVAILABLE_MESSAGE) from exc

        if response.status_code == 401:
            raise XanoUnauthorizedError(SESSION_EXPIRED_MESSAGE, 401)
        if response.status_code == 403:
            raise XanoForbiddenError(FORBIDDEN_MESSAGE, 403)
        if response.status_code >= 500:
            raise XanoUnavailableError(UNAVAILABLE_MESSAGE, response.status_code)
        if response.status_code >= 400:
            raise XanoError(
                _message_from_response(response),
                response.status_code,
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise XanoError("Resposta invÃ¡lida do Xano.", response.status_code) from exc
        if not isinstance(payload, dict):
            raise XanoError("Resposta invÃ¡lida do Xano.", response.status_code)
        return payload

    def login(self, login: str, senha: str) -> tuple[str, Session]:
        try:
            payload = self._request(
                "POST",
                "/api:identidade/identidade/login",
                json={"login": login, "senha": senha},
            )
        except (XanoUnauthorizedError, XanoForbiddenError) as exc:
            raise XanoError(AUTH_INVALID_MESSAGE, 401) from exc
        return payload["token"], self._session_from_payload(payload["sessao"])

    def session(self, token: str) -> Session:
        return self._session_from_payload(
            self._request("GET", "/api:identidade/identidade/sessao", token)["sessao"]
        )

    def update_login(self, token: str, login: str) -> Session:
        payload = self._request(
            "PATCH",
            "/api:identidade/identidade/minha-conta/login",
            token,
            json={"login": login},
        )
        return self._session_from_payload(payload["sessao"])

    def update_password(
        self,
        token: str,
        senha_atual: str,
        nova_senha: str,
    ) -> Session:
        payload = self._request(
            "PATCH",
            "/api:identidade/identidade/minha-conta/senha",
            token,
            json={"senha_atual": senha_atual, "nova_senha": nova_senha},
        )
        return self._session_from_payload(payload["sessao"])

    def list_products(self, token: str) -> list[Product]:
        payload = self._request("GET", "/api:94CoO3xX/produtos/estoque", token)
        return [self._product_from_payload(item) for item in payload["produtos"]]

    def create_product(self, token: str, product: dict[str, Any]) -> Product:
        payload = self._request(
            "POST",
            "/api:94CoO3xX/produtos/produto",
            token,
            json=product,
        )
        return self._product_from_payload(payload["produto"])

    def update_product(
        self,
        token: str,
        product_id: int,
        product: dict[str, Any],
    ) -> Product:
        payload = self._request(
            "PATCH",
            f"/api:94CoO3xX/produtos/produto/{product_id}",
            token,
            json=product,
        )
        return self._product_from_payload(payload["produto"])

    def deactivate_product(self, token: str, product_id: int) -> Product:
        payload = self._request(
            "POST",
            f"/api:94CoO3xX/produtos/produto/{product_id}/inativar",
            token,
        )
        return self._product_from_payload(payload["produto"])

    def list_categories(self, token: str) -> list[Category]:
        payload = self._request("GET", "/api:94CoO3xX/produtos/categorias", token)
        return [self._category_from_payload(item) for item in payload["categorias"]]

    def create_category(self, token: str, nome: str) -> Category:
        payload = self._request(
            "POST",
            "/api:94CoO3xX/produtos/categoria",
            token,
            json={"nome": nome},
        )
        return self._category_from_payload(payload["categoria"])

    def update_category(self, token: str, category_id: int, nome: str) -> Category:
        payload = self._request(
            "PATCH",
            f"/api:94CoO3xX/produtos/categoria/{category_id}",
            token,
            json={"nome": nome},
        )
        return self._category_from_payload(payload["categoria"])

    def deactivate_category(self, token: str, category_id: int) -> Category:
        payload = self._request(
            "POST",
            f"/api:94CoO3xX/produtos/categoria/{category_id}/inativar",
            token,
        )
        return self._category_from_payload(payload["categoria"])

    @staticmethod
    def _session_from_payload(payload: dict[str, Any]) -> Session:
        return Session(
            user_id=int(payload["id_usuario"]),
            funcionario_id=int(payload["id_funcionario"]),
            nome=str(payload["nome"]),
            login=str(payload["login"]),
            perfil_acesso=str(payload["perfil_acesso"]),
        )

    @staticmethod
    def _product_from_payload(payload: dict[str, Any]) -> Product:
        return Product(
            id=int(payload["id"]),
            id_categoria=int(payload["id_categoria"]),
            id_fornecedor=int(payload["id_fornecedor"]),
            nome=str(payload.get("nome") or ""),
            descricao=str(payload.get("descricao") or ""),
            codigo_barras=str(payload.get("codigo_barras") or ""),
            controlado=bool(payload.get("controlado", False)),
            preco_venda=float(payload.get("preco_venda") or 0),
            quantidade_estoque=int(payload.get("quantidade_estoque") or 0),
            estoque_minimo=int(payload.get("estoque_minimo") or 0),
            ativo=bool(payload.get("ativo", True)),
        )

    @staticmethod
    def _category_from_payload(payload: dict[str, Any]) -> Category:
        return Category(
            id=int(payload["id"]),
            nome=str(payload.get("nome") or ""),
            ativo=bool(payload.get("ativo", True)),
        )

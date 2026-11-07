"""Cliente HTTP server-side para as APIs de identidade do Xano."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx


AUTH_INVALID_MESSAGE = "usuÃ¡rio ou senha invÃ¡lidos"
SESSION_EXPIRED_MESSAGE = "SessÃ£o expirada. Entre novamente."
FORBIDDEN_MESSAGE = "VocÃª nÃ£o tem permissÃ£o para esta aÃ§Ã£o"
UNAVAILABLE_MESSAGE = "ServiÃ§o indisponÃ­vel, tente novamente"


def _load_local_env() -> None:
    """Load non-exported local settings when Reflex starts from the project root."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


_load_local_env()


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


@dataclass(frozen=True)
class Supplier:
    id: int
    nome: str
    cnpj: str
    telefone: str
    email: str
    endereco: str
    prazo_entrega: str

@dataclass(frozen=True)
class Customer:
    id: int
    nome: str
    cpf: str
    data_nascimento: str
    telefone: str
    email: str
    data_cadastro: str
    ativo: bool


@dataclass(frozen=True)
class Address:
    id: int
    id_cliente: int
    logradouro: str
    numero: str
    bairro: str
    cidade: str
    estado: str
    cep: str
    complemento: str


@dataclass(frozen=True)
class Employee:
    id: int
    nome: str
    cpf: str
    data_nascimento: str
    telefone: str
    email: str
    cargo: str
    salario: float | None
    data_admissao: str
    ativo: bool = True


@dataclass(frozen=True)
class Sale:
    id: int
    id_pedido: int
    data_venda: str
    valor_total: float
    status: str


@dataclass(frozen=True)
class Order:
    id: int
    id_cliente: int | None
    id_funcionario: int
    data_pedido: str
    status: str
    canal: str


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

    def list_suppliers(self, token: str) -> list[Supplier]:
        payload = self._request(
            "GET",
            "/api:94CoO3xX/produtos/fornecedores",
            token,
        )
        return [
            self._supplier_from_payload(item)
            for item in payload["fornecedores"]
        ]

    def create_supplier(
        self,
        token: str,
        supplier: dict[str, Any],
    ) -> Supplier:
        payload = self._request(
            "POST",
            "/api:94CoO3xX/produtos/fornecedor",
            token,
            json=supplier,
        )
        return self._supplier_from_payload(payload["fornecedor"])

    def update_supplier(
        self,
        token: str,
        supplier_id: int,
        supplier: dict[str, Any],
    ) -> Supplier:
        payload = self._request(
            "PATCH",
            f"/api:94CoO3xX/produtos/fornecedor/{supplier_id}",
            token,
            json=supplier,
        )
        return self._supplier_from_payload(payload["fornecedor"])

    def delete_supplier(self, token: str, supplier_id: int) -> None:
        self._request(
            "DELETE",
            f"/api:94CoO3xX/produtos/fornecedor/{supplier_id}",
            token,
        )

    def list_customers(self, token: str) -> list[Customer]:
        payload = self._request("GET", "/api:n8EZtgGQ/clientes", token)
        return [self._customer_from_payload(item) for item in payload["clientes"]]

    def create_customer(
        self,
        token: str,
        customer: dict[str, Any],
    ) -> Customer:
        payload = self._request(
            "POST",
            "/api:n8EZtgGQ/clientes/cliente",
            token,
            json=customer,
        )
        return self._customer_from_payload(payload["cliente"])

    def update_customer(
        self,
        token: str,
        customer_id: int,
        customer: dict[str, Any],
    ) -> Customer:
        payload = self._request(
            "PATCH",
            f"/api:n8EZtgGQ/clientes/cliente/{customer_id}",
            token,
            json=customer,
        )
        return self._customer_from_payload(payload["cliente"])

    def deactivate_customer(self, token: str, customer_id: int) -> Customer:
        payload = self._request(
            "POST",
            f"/api:n8EZtgGQ/clientes/cliente/{customer_id}/inativar",
            token,
        )
        return self._customer_from_payload(payload["cliente"])

    def list_addresses(self, token: str, customer_id: int) -> list[Address]:
        payload = self._request(
            "GET",
            f"/api:n8EZtgGQ/clientes/cliente/{customer_id}/enderecos",
            token,
        )
        return [self._address_from_payload(item) for item in payload["enderecos"]]

    def create_address(
        self,
        token: str,
        customer_id: int,
        address: dict[str, Any],
    ) -> Address:
        payload = self._request(
            "POST",
            f"/api:n8EZtgGQ/clientes/cliente/{customer_id}/endereco",
            token,
            json=address,
        )
        return self._address_from_payload(payload["endereco"])

    def list_employees(self, token: str) -> list[Employee]:
        payload = self._request("GET", "/api:equipe/equipe/funcionarios", token)
        active_by_employee = {
            int(item["id_funcionario"]): bool(item.get("ativo", True))
            for item in payload.get("usuarios", [])
        }
        return [
            self._employee_from_payload(
                item,
                active=active_by_employee.get(int(item["id"]), True),
            )
            for item in payload["funcionarios"]
        ]

    def create_employee(
        self,
        token: str,
        employee: dict[str, Any],
    ) -> tuple[Employee, dict[str, str]]:
        payload = self._request(
            "POST",
            "/api:equipe/equipe/funcionario",
            token,
            json=employee,
        )
        return (
            self._employee_from_payload(payload["funcionario"]),
            {
                "login": str(payload["acesso"].get("login") or ""),
                "senha_inicial": str(payload["acesso"].get("senha_inicial") or ""),
            },
        )

    def update_employee(
        self,
        token: str,
        employee_id: int,
        employee: dict[str, Any],
    ) -> Employee:
        payload = self._request(
            "PATCH",
            f"/api:equipe/equipe/funcionario/{employee_id}",
            token,
            json=employee,
        )
        return self._employee_from_payload(
            payload["funcionario"],
            active=payload.get("ativo"),
        )

    def deactivate_employee(self, token: str, employee_id: int) -> Employee:
        payload = self._request(
            "POST",
            f"/api:equipe/equipe/funcionario/{employee_id}/inativar",
            token,
        )
        return self._employee_from_payload(
            payload["funcionario"],
            active=payload.get("ativo", False),
        )

    def create_order(
        self,
        token: str,
        *,
        client_id: int | None,
        channel: str,
        items: list[dict[str, int]],
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api:8Ji5Nfc2/vendas/pedido",
            token,
            json={
                "id_cliente": client_id,
                "canal": channel,
                "itens": items,
            },
        )

    def confirm_order(
        self,
        token: str,
        order_id: int,
        payment_method: str,
        prescription_number: str | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api:8Ji5Nfc2/vendas/pedido/{order_id}/confirmar",
            token,
            json={
                "forma_pagamento": payment_method,
                "numero_receita": prescription_number or None,
            },
        )

    def list_sales(self, token: str, *, is_gestor: bool) -> list[Sale]:
        path = (
            "/api:8Ji5Nfc2/vendas"
            if is_gestor
            else "/api:8Ji5Nfc2/vendas/minhas"
        )
        payload = self._request("GET", path, token)
        return [self._sale_from_payload(item) for item in payload["vendas"]]

    def list_sale_history(
        self,
        token: str,
        *,
        is_gestor: bool,
    ) -> tuple[list[Sale], list[dict[str, Any]]]:
        path = (
            "/api:8Ji5Nfc2/vendas"
            if is_gestor
            else "/api:8Ji5Nfc2/vendas/minhas"
        )
        payload = self._request("GET", path, token)
        return (
            [self._sale_from_payload(item) for item in payload["vendas"]],
            list(payload.get("pagamentos", [])),
        )

    def list_orders(
        self,
        token: str,
        *,
        is_gestor: bool,
    ) -> tuple[list[Order], list[dict[str, Any]]]:
        path = (
            "/api:8Ji5Nfc2/vendas/pedidos"
            if is_gestor
            else "/api:8Ji5Nfc2/vendas/meus-pedidos"
        )
        payload = self._request("GET", path, token)
        return (
            [
                Order(
                    id=int(item["id"]),
                    id_cliente=(
                        int(item["id_cliente"])
                        if item.get("id_cliente") is not None
                        else None
                    ),
                    id_funcionario=int(item["id_funcionario"]),
                    data_pedido=str(item.get("data_pedido") or ""),
                    status=str(item.get("status") or ""),
                    canal=str(item.get("canal") or ""),
                )
                for item in payload["pedidos"]
            ],
            list(payload["itens"]),
        )

    def dashboard_summary(
        self,
        token: str,
        *,
        data_inicio: datetime,
        data_fim: datetime,
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/api:8Ji5Nfc2/painel/resumo",
            token,
            params={
                "data_inicio": int(data_inicio.timestamp() * 1000),
                "data_fim": int(data_fim.timestamp() * 1000),
            },
        )

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

    @staticmethod
    def _supplier_from_payload(payload: dict[str, Any]) -> Supplier:
        return Supplier(
            id=int(payload["id"]),
            nome=str(payload.get("nome") or ""),
            cnpj=str(payload.get("cnpj") or ""),
            telefone=str(payload.get("telefone") or ""),
            email=str(payload.get("email") or ""),
            endereco=str(payload.get("endereco") or ""),
            prazo_entrega=str(payload.get("prazo_entrega") or ""),
        )

    @staticmethod
    def _customer_from_payload(payload: dict[str, Any]) -> Customer:
        return Customer(
            id=int(payload["id"]),
            nome=str(payload.get("nome") or ""),
            cpf=str(payload.get("cpf") or ""),
            data_nascimento=str(payload.get("data_nascimento") or ""),
            telefone=str(payload.get("telefone") or ""),
            email=str(payload.get("email") or ""),
            data_cadastro=str(payload.get("data_cadastro") or ""),
            ativo=bool(payload.get("ativo", True)),
        )

    @staticmethod
    def _address_from_payload(payload: dict[str, Any]) -> Address:
        return Address(
            id=int(payload["id"]),
            id_cliente=int(payload["id_cliente"]),
            logradouro=str(payload.get("logradouro") or ""),
            numero=str(payload.get("numero") or ""),
            bairro=str(payload.get("bairro") or ""),
            cidade=str(payload.get("cidade") or ""),
            estado=str(payload.get("estado") or ""),
            cep=str(payload.get("cep") or ""),
            complemento=str(payload.get("complemento") or ""),
        )

    @staticmethod
    def _employee_from_payload(
        payload: dict[str, Any],
        active: bool | None = None,
    ) -> Employee:
        salario = payload.get("salario")
        return Employee(
            id=int(payload["id"]),
            nome=str(payload.get("nome") or ""),
            cpf=str(payload.get("cpf") or ""),
            data_nascimento=str(payload.get("data_nascimento") or ""),
            telefone=str(payload.get("telefone") or ""),
            email=str(payload.get("email") or ""),
            cargo=str(payload.get("cargo") or ""),
            salario=float(salario) if salario is not None else None,
            data_admissao=str(payload.get("data_admissao") or ""),
            ativo=bool(payload.get("ativo", True) if active is None else active),
        )

    @staticmethod
    def _sale_from_payload(payload: dict[str, Any]) -> Sale:
        return Sale(
            id=int(payload["id"]),
            id_pedido=int(payload["id_pedido"]),
            data_venda=str(payload.get("data_venda") or ""),
            valor_total=float(payload.get("valor_total") or 0),
            status=str(payload.get("status") or ""),
        )

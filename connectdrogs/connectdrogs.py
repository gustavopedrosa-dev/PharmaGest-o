"""Frontend do FarmaGestão para autenticação e navegação por perfil."""

from __future__ import annotations

from datetime import datetime, timedelta

import reflex as rx

from api.xano import (
    FORBIDDEN_MESSAGE,
    SESSION_EXPIRED_MESSAGE,
    UNAVAILABLE_MESSAGE,
    Address,
    Customer,
    Employee,
    Session,
    XanoClient,
    XanoError,
    XanoForbiddenError,
    XanoUnauthorizedError,
    XanoUnavailableError,
)
from rxconfig import config


def build_customer_address_payload(
    address: dict[str, str],
) -> tuple[dict[str, object] | None, str | None]:
    cidade = address["cidade"].strip()
    estado = address["estado"].strip()
    if not cidade or not estado:
        return None, "Cidade e estado são obrigatórios para cada endereço."
    return {
        "logradouro": address["logradouro"].strip() or None,
        "numero": address["numero"].strip() or None,
        "bairro": address["bairro"].strip() or None,
        "cidade": cidade,
        "estado": estado,
        "cep": address["cep"].strip() or None,
        "complemento": address["complemento"].strip(),
    }, None


def mark_customer_address_saved(
    addresses: list[dict[str, str]],
    form_key: str,
    address_id: int,
) -> list[dict[str, str]]:
    return [
        {**address, "id": str(address_id)}
        if address["form_key"] == form_key
        else address
        for address in addresses
    ]


def persist_customer_addresses(
    client: XanoClient,
    token: str,
    customer_id: int,
    addresses: list[dict[str, str]],
) -> tuple[list[dict[str, str]], Exception | None]:
    saved_addresses = [dict(address) for address in addresses]
    for address in saved_addresses:
        payload, error = build_customer_address_payload(address)
        if error is not None:
            return saved_addresses, ValueError(error)
        if payload is None:
            continue
        try:
            if address["id"]:
                client.update_address(
                    token,
                    customer_id,
                    int(address["id"]),
                    payload,
                )
            else:
                created = client.create_address(token, customer_id, payload)
                saved_addresses = mark_customer_address_saved(
                    saved_addresses,
                    address["form_key"],
                    created.id,
                )
        except (ValueError, XanoError) as exc:
            return saved_addresses, exc
    return saved_addresses, None


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
    senha_visivel: bool = False
    login_role: str = "colaborador"
    novo_login: str = ""
    senha_atual: str = ""
    nova_senha: str = ""
    produtos: list[dict[str, str]] = []
    categorias: list[dict[str, str]] = []
    vendas: list[dict[str, str]] = []
    pedidos: list[dict[str, str]] = []
    itens_pedido: list[dict[str, str]] = []
    clientes: list[dict[str, str]] = []
    enderecos: list[dict[str, str]] = []
    funcionarios: list[dict[str, str]] = []
    fornecedores: list[dict[str, str]] = []
    dashboard_total_vendas: int = 0
    dashboard_valor_total: float = 0.0
    dashboard_itens_vendidos: int = 0
    dashboard_funcionarios_ativos: int = 0
    dashboard_estoque_critico: list[dict[str, object]] = []
    dashboard_mais_vendidos: list[dict[str, object]] = []
    dashboard_carregado: bool = False
    acesso_inicial: dict[str, str] = {}
    confirmando_inativacao: bool = False
    funcionario_ativo: bool = True
    confirmando_remocao_fornecedor: bool = False
    produto_id: str = ""
    categoria_id: str = ""
    produto_categoria_id: str = ""
    produto_fornecedor_id: str = ""
    produto_nome: str = ""
    produto_descricao: str = ""
    produto_codigo_barras: str = ""
    produto_preco: str = ""
    produto_quantidade: str = "0"
    produto_estoque_minimo: str = "0"
    produto_controlado: bool = False
    produto_modal_aberto: bool = False
    produto_editando: bool = False
    categoria_nome: str = ""
    categoria_form_aberta: bool = False
    venda_produto_id: str = ""
    venda_quantidade: str = "1"
    venda_cliente_id: str = ""
    venda_canal: str = "presencial"
    venda_pagamento: str = "dinheiro"
    venda_receita: str = ""
    venda_itens: list[dict[str, str]] = []
    cliente_id: str = ""
    cliente_nome: str = ""
    cliente_cpf: str = ""
    cliente_data_nascimento: str = ""
    cliente_telefone: str = ""
    cliente_email: str = ""
    cliente_form_aberto: bool = False
    cliente_enderecos: list[dict[str, str]] = []
    cliente_endereco_proxima_chave: int = 0
    endereco_logradouro: str = ""
    endereco_numero: str = ""
    endereco_bairro: str = ""
    endereco_cidade: str = ""
    endereco_estado: str = ""
    endereco_cep: str = ""
    endereco_complemento: str = ""
    funcionario_id: str = ""
    funcionario_nome: str = ""
    funcionario_cpf: str = ""
    funcionario_data_nascimento: str = ""
    funcionario_telefone: str = ""
    funcionario_email: str = ""
    funcionario_endereco: str = ""
    funcionario_cargo: str = ""
    funcionario_salario: str = ""
    funcionario_login: str = ""
    funcionario_senha_inicial: str = ""
    funcionario_senha_inicial_visivel: bool = False
    funcionario_modal_aberto: bool = False
    funcionario_editando: bool = False
    fornecedor_id: str = ""
    fornecedor_nome: str = ""
    fornecedor_cnpj: str = ""
    fornecedor_telefone: str = ""
    fornecedor_email: str = ""
    fornecedor_endereco: str = ""
    fornecedor_prazo_entrega: str = ""
    fornecedor_modal_aberto: bool = False
    fornecedor_editando: bool = False

    @rx.var
    def is_gestor(self) -> bool:
        return self.perfil_acesso == "gestor"

    @rx.var
    def feedback_is_error(self) -> bool:
        if not self.mensagem:
            return False
        success_prefixes = (
            "Venda confirmada.",
            "Cliente cadastrado.",
            "Cliente atualizado.",
            "Cliente removido.",
            "Cliente inativado.",
            "Produto cadastrado.",
            "Produto atualizado.",
            "Produto removido.",
            "Produto inativado.",
            "Categoria cadastrada.",
            "Categoria atualizada.",
            "Categoria inativada.",
            "Funcionário cadastrado.",
            "Funcionário atualizado.",
            "Funcionário inativado.",
            "Funcionário ativado.",
            "Funcionário reativado.",
            "Fornecedor cadastrado.",
            "Fornecedor atualizado.",
            "Fornecedor removido.",
            "Fornecedor inativado.",
            "Login atualizado.",
            "Senha atualizada.",
            "Endere",
        )
        return not any(
            self.mensagem.startswith(prefix)
            for prefix in success_prefixes
        )

    @rx.var
    def dashboard_valor_total_brl(self) -> str:
        return f"R$ {self.dashboard_valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @rx.var
    def venda_valor_total(self) -> float:
        total = 0.0
        for item in self.venda_itens:
            try:
                total += float(item.get("preco", "0")) * int(item["quantidade"])
            except (TypeError, ValueError, KeyError):
                continue
        return total

    @rx.var
    def venda_valor_total_brl(self) -> str:
        return f"R$ {self.venda_valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @rx.event
    def set_login_input(self, value: str) -> None:
        self.login_input = value

    @rx.event
    def set_senha_input(self, value: str) -> None:
        self.senha_input = value

    def alternar_senha(self) -> None:
        self.senha_visivel = not self.senha_visivel

    @rx.event
    def set_login_role(self, value: str) -> None:
        self.login_role = value

    @rx.event
    def set_novo_login(self, value: str) -> None:
        self.novo_login = value

    @rx.event
    def set_senha_atual(self, value: str) -> None:
        self.senha_atual = value

    @rx.event
    def set_nova_senha(self, value: str) -> None:
        self.nova_senha = value

    def set_product_field(self, field: str, value: str) -> None:
        setattr(self, field, value)

    def set_product_controlled(self, value: bool) -> None:
        self.produto_controlado = value

    @rx.event
    @rx.event
    def edit_product(self, product_id: str) -> None:
        self.produto_id = product_id
        product = next(
            (item for item in self.produtos if item["id"] == product_id),
            None,
        )
        if product is None:
            self.mensagem = "Produto não encontrado."
            return
        self.produto_categoria_id = product["categoria_id"]
        self.produto_fornecedor_id = product["fornecedor_id"]
        self.produto_nome = product["nome"]
        self.produto_descricao = product["descricao"]
        self.produto_codigo_barras = product["codigo_barras"]
        self.produto_preco = product["preco"].replace("R$ ", "")
        self.produto_quantidade = product["estoque"]
        self.produto_estoque_minimo = product["minimo"]
        self.produto_controlado = product["controlado"] == "Sim"
        self.produto_editando = True
        self.produto_modal_aberto = True

    @rx.event
    def open_new_product(self) -> None:
        self._clear_product_form()
        if self.fornecedores:
            self.produto_fornecedor_id = self.fornecedores[0]["id"]
        self.produto_editando = False
        self.produto_modal_aberto = True

    @rx.event
    def close_product_modal(self) -> None:
        self.produto_modal_aberto = False
        self.produto_editando = False

    @rx.event
    def save_product(self) -> rx.event.EventSpec | None:
        if self.produto_editando:
            return self.update_product()
        else:
            return self.create_product()

    def set_product_id(self, value: str) -> None:
        self.produto_id = value

    def set_categoria_id(self, value: str) -> None:
        self.categoria_id = value

    def set_categoria_nome(self, value: str) -> None:
        self.categoria_nome = value

    @rx.event
    def toggle_category_form(self) -> None:
        self.categoria_form_aberta = not self.categoria_form_aberta

    @rx.event
    def set_sale_field(self, field: str, value: str) -> None:
        setattr(self, field, value)

    @rx.event
    def set_customer_field(self, field: str, value: str) -> None:
        if field == "cliente_cpf":
            digits = "".join(character for character in value if character.isdigit())
            setattr(self, field, digits[:11])
            return
        setattr(self, field, value)

    @rx.event
    def set_address_field(self, field: str, value: str) -> None:
        setattr(self, field, value)

    @rx.event
    def set_employee_field(self, field: str, value: str) -> None:
        if field == "funcionario_cpf":
            digits = "".join(character for character in value if character.isdigit())
            setattr(self, field, digits[:11])
            return
        setattr(self, field, value)

    @rx.event
    def set_initial_employee_password(self, value: str) -> None:
        self.funcionario_senha_inicial = value

    @rx.event
    def toggle_initial_employee_password(self) -> None:
        self.funcionario_senha_inicial_visivel = (
            not self.funcionario_senha_inicial_visivel
        )

    @rx.event
    def open_new_employee(self) -> None:
        self._clear_employee_form()
        self.acesso_inicial = {}
        self.funcionario_endereco = ""
        self.funcionario_senha_inicial = ""
        self.funcionario_senha_inicial_visivel = False
        self.funcionario_cargo = "colaborador"
        self.funcionario_editando = False
        self.funcionario_modal_aberto = True

    @rx.event
    def edit_employee(self, employee_id: str) -> None:
        employee = next(
            (item for item in self.funcionarios if item["id"] == employee_id),
            None,
        )
        if employee is None:
            self.mensagem = "Funcionário não encontrado."
            return
        self.funcionario_id = employee["id"]
        self.funcionario_nome = employee["nome"]
        self.funcionario_cpf = employee["cpf"]
        self.funcionario_telefone = employee["telefone"]
        self.funcionario_email = employee["email"]
        self.funcionario_endereco = employee["endereco"]
        self.funcionario_cargo = employee["cargo"]
        self.funcionario_salario = employee["salario"].replace("R$ ", "")
        self.funcionario_editando = True
        self.funcionario_modal_aberto = True

    @rx.event
    def close_employee_modal(self) -> None:
        self.funcionario_modal_aberto = False
        self.funcionario_editando = False
        self.acesso_inicial = {}
        self.funcionario_senha_inicial = ""
        self.funcionario_senha_inicial_visivel = False

    @rx.event
    def save_employee(self) -> None:
        if not self.funcionario_editando and not self.funcionario_login:
            self.funcionario_login = (
                self.funcionario_nome.strip().lower().replace(" ", ".")
            )
        if self.funcionario_editando:
            if not self._valid_employee_cpf():
                return
            if not self._valid_employee_update_cpf():
                return
            try:
                employee_id = int(self.funcionario_id)
                employee = XanoClient().update_employee(
                    self._token,
                    employee_id,
                    self._employee_payload(include_login=False),
                )
                employee_view = self._employee_view(employee)
                employee_view["endereco"] = self.funcionario_endereco or ""
                self.funcionarios = [
                    employee_view
                    if item["id"] == str(employee_id)
                    else item
                    for item in self.funcionarios
                ]
                self.mensagem = "Funcionário atualizado."
                self.close_employee_modal()
            except ValueError:
                self.mensagem = "Informe um ID e salário válidos."
            except XanoUnauthorizedError:
                self._expire_session()
            except XanoForbiddenError:
                self.mensagem = FORBIDDEN_MESSAGE
            except XanoUnavailableError:
                self.mensagem = UNAVAILABLE_MESSAGE
            except XanoError as exc:
                self.mensagem = exc.message
        else:
            self.create_employee()

    @rx.event
    def request_deactivate_employee_by_id(self, employee_id: str) -> None:
        self.funcionario_id = employee_id
        employee = next(
            (item for item in self.funcionarios if item["id"] == employee_id),
            None,
        )
        if employee is not None:
            self.funcionario_nome = employee["nome"]
            self.funcionario_ativo = employee["situacao"] == "ativo"
        self.request_deactivate_employee()

    def set_supplier_field(self, field: str, value: str) -> None:
        setattr(self, field, value)

    def set_product_supplier(self, value: str) -> None:
        self.produto_fornecedor_id = value

    @rx.event
    def add_sale_item(self) -> None:
        try:
            product_id = int(self.venda_produto_id)
            quantity = int(self.venda_quantidade)
        except ValueError:
            self.mensagem = "Informe um produto e uma quantidade válidos."
            return
        if quantity < 1:
            self.mensagem = "A quantidade deve ser positiva."
            return
        if any(item["id_produto"] == str(product_id) for item in self.venda_itens):
            self.mensagem = "O produto já foi adicionado ao pedido."
            return
        product = next(
            (
                item
                for item in getattr(self, "produtos", [])
                if item["id"] == str(product_id)
            ),
            None,
        )
        if product is None:
            self.mensagem = "Produto não encontrado."
            return
        self.venda_itens = [
            *self.venda_itens,
            {
                "id_produto": str(product_id),
                "nome": product["nome"],
                "quantidade": str(quantity),
                "preco": product["preco"].replace("R$ ", "").replace(",", "."),
            },
        ]
        self.venda_produto_id = ""
        self.venda_quantidade = "1"
        self.mensagem = ""

    @rx.event
    def cancel_sale(self) -> rx.event.EventSpec:
        self.venda_produto_id = ""
        self.venda_quantidade = "1"
        self.venda_cliente_id = ""
        self.venda_canal = "presencial"
        self.venda_pagamento = "dinheiro"
        self.venda_receita = ""
        self.venda_itens = []
        self.mensagem = ""
        return rx.redirect("/vendas")

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
        self.senha_visivel = False
        destination = (
            "/dashboard"
            if self.perfil_acesso == "gestor"
            else "/vendas"
        )
        return rx.redirect(destination)

    def _redirect_if_missing_token(self) -> rx.event.EventSpec | None:
        if not self._token:
            self.session_ready = True
            self.authenticated = False
            return rx.redirect("/login")
        return None

    @rx.event
    def load_session(self) -> rx.event.EventSpec | None:
        redirect = self._redirect_if_missing_token()
        if redirect is not None:
            return redirect
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
        redirect = self._redirect_if_missing_token()
        if redirect is not None:
            return redirect
        if self.perfil_acesso != "gestor":
            self._clear_dashboard()
            self.mensagem = FORBIDDEN_MESSAGE
            return rx.redirect("/minha-conta")
        self.dashboard_carregado = False
        self.mensagem = ""
        try:
            agora = datetime.now().astimezone()
            data_inicio = agora.replace(hour=0, minute=0, second=0, microsecond=0)
            data_fim = data_inicio + timedelta(days=1)
            with XanoClient() as client:
                summary = client.dashboard_summary(
                    self._token,
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                )
            self.dashboard_total_vendas = int(summary.get("total_vendas", 0) or 0)
            self.dashboard_valor_total = float(summary.get("valor_total", 0) or 0)
            itens_vendidos = summary.get("itens_vendidos")
            if itens_vendidos is None:
                itens_vendidos = sum(
                    int(item.get("quantidade", 0) or 0)
                    for item in summary.get("mais_vendidos", [])
                )
            self.dashboard_itens_vendidos = int(itens_vendidos or 0)
            self.dashboard_funcionarios_ativos = int(
                summary.get("funcionarios_ativos", 0) or 0
            )
            self.dashboard_estoque_critico = list(summary.get("estoque_critico", []))
            self.dashboard_mais_vendidos = list(summary.get("mais_vendidos", []))
            self.dashboard_carregado = True
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

    @rx.event
    def cancel_account_form(self) -> rx.event.EventSpec:
        self.novo_login = ""
        self.senha_atual = ""
        self.nova_senha = ""
        self.mensagem = ""
        return rx.redirect("/vendas")

    @rx.event
    def load_products(self) -> rx.event.EventSpec | None:
        redirect = self._redirect_if_missing_token()
        if redirect is not None:
            return redirect
        try:
            with XanoClient() as client:
                self._set_products(client.list_products(self._token))
                self._set_categories(client.list_categories(self._token))
                if self.is_gestor:
                    self._set_suppliers(client.list_suppliers(self._token))
                else:
                    self._clear_suppliers()
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
    def load_suppliers(self) -> rx.event.EventSpec | None:
        redirect = self._redirect_if_missing_token()
        if redirect is not None:
            return redirect
        if not self.is_gestor:
            self.mensagem = FORBIDDEN_MESSAGE
            return rx.redirect("/minha-conta")
        try:
            with XanoClient() as client:
                self._set_suppliers(client.list_suppliers(self._token))
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
    def load_customers(self) -> rx.event.EventSpec | None:
        redirect = self._redirect_if_missing_token()
        if redirect is not None:
            return redirect
        try:
            with XanoClient() as client:
                customers = client.list_customers(self._token)
                addresses_by_customer: dict[str, str] = {}
                for customer in customers:
                    if not customer.ativo:
                        continue
                    addresses = client.list_addresses(self._token, customer.id)
                    if addresses:
                        addresses_by_customer[str(customer.id)] = (
                            self._format_customer_address(addresses[0])
                        )
                self._set_customers(customers, addresses_by_customer)
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
    def open_customer_form(self) -> None:
        self.cliente_id = ""
        self.cliente_nome = ""
        self.cliente_cpf = ""
        self.cliente_data_nascimento = ""
        self.cliente_telefone = ""
        self.cliente_email = ""
        self.cliente_enderecos = [
            {
                "form_key": "0",
                "id": "",
                "logradouro": "",
                "numero": "",
                "bairro": "",
                "cidade": "",
                "estado": "",
                "cep": "",
                "complemento": "",
            }
        ]
        self.cliente_endereco_proxima_chave = 1
        self.mensagem = ""
        self.cliente_form_aberto = True

    @rx.event
    def close_customer_form(self) -> None:
        self.cliente_form_aberto = False
        self.cliente_enderecos = []
        self.mensagem = ""

    @rx.event
    def add_customer_address(self) -> None:
        form_key = str(self.cliente_endereco_proxima_chave)
        self.cliente_enderecos = [
            *self.cliente_enderecos,
            {
                "form_key": form_key,
                "id": "",
                "logradouro": "",
                "numero": "",
                "bairro": "",
                "cidade": "",
                "estado": "",
                "cep": "",
                "complemento": "",
            },
        ]
        self.cliente_endereco_proxima_chave += 1

    @rx.event
    def set_customer_address_field(
        self,
        form_key: str,
        field: str,
        value: str,
    ) -> None:
        address_fields = {
            "logradouro",
            "numero",
            "bairro",
            "cidade",
            "estado",
            "cep",
            "complemento",
        }
        if field not in address_fields:
            return
        self.cliente_enderecos = [
            {**address, field: value}
            if address["form_key"] == form_key
            else address
            for address in self.cliente_enderecos
        ]

    @rx.event
    def load_employees(self) -> rx.event.EventSpec | None:
        redirect = self._redirect_if_missing_token()
        if redirect is not None:
            return redirect
        if not self.is_gestor:
            self.mensagem = FORBIDDEN_MESSAGE
            return rx.redirect("/minha-conta")
        try:
            with XanoClient() as client:
                self._set_employees(client.list_employees(self._token))
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
    def create_employee(self) -> None:
        if not self.is_gestor:
            self.mensagem = FORBIDDEN_MESSAGE
            return
        if not self._valid_employee_cpf():
            return
        cpf_digitado = "".join(
            character for character in self.funcionario_cpf if character.isdigit()
        )
        if any(
            "".join(character for character in item["cpf"] if character.isdigit())
            == cpf_digitado
            for item in self.funcionarios
        ):
            self.mensagem = "O CPF já está cadastrado."
            return
        try:
            employee, access = XanoClient().create_employee(
                self._token,
                self._employee_payload(include_login=True),
            )
            employee_view = self._employee_view(employee)
            employee_view["endereco"] = self.funcionario_endereco or ""
            self.funcionarios = [*self.funcionarios, employee_view]
            self.acesso_inicial = access
            self.funcionario_login = access["login"]
            self.funcionario_senha_inicial = access["senha_inicial"]
            self.mensagem = "Funcionário cadastrado. Guarde a senha inicial exibida."
        except ValueError:
            self.mensagem = "Preencha salário e campos numéricos com valores válidos."
        except XanoUnauthorizedError:
            self._expire_session()
        except XanoForbiddenError:
            self.mensagem = FORBIDDEN_MESSAGE
        except XanoUnavailableError:
            self.mensagem = UNAVAILABLE_MESSAGE
        except XanoError as exc:
            self.mensagem = exc.message

    @rx.event
    def update_employee(self) -> None:
        if not self.is_gestor:
            self.mensagem = FORBIDDEN_MESSAGE
            return
        if not self._valid_employee_cpf():
            return
        if not self._valid_employee_update_cpf():
            return
        try:
            employee_id = int(self.funcionario_id)
            employee = XanoClient().update_employee(
                self._token,
                employee_id,
                self._employee_payload(include_login=False),
            )
            employee_view = self._employee_view(employee)
            employee_view["endereco"] = self.funcionario_endereco or ""
            self.funcionarios = [
                employee_view
                if item["id"] == str(employee_id)
                else item
                for item in self.funcionarios
            ]
            self.mensagem = "Funcionário atualizado."
            self.close_employee_modal()
        except ValueError:
            self.mensagem = "Informe um ID e salário válidos."
        except XanoUnauthorizedError:
            self._expire_session()
        except XanoForbiddenError:
            self.mensagem = FORBIDDEN_MESSAGE
        except XanoUnavailableError:
            self.mensagem = UNAVAILABLE_MESSAGE
        except XanoError as exc:
            self.mensagem = exc.message

    @rx.event
    def deactivate_employee(self) -> None:
        if not self.is_gestor:
            self.mensagem = FORBIDDEN_MESSAGE
            return
        try:
            employee_id = int(self.funcionario_id)
            client = XanoClient()
            was_active = self.funcionario_ativo
            employee = (
                client.deactivate_employee(self._token, employee_id)
                if was_active
                else client.activate_employee(self._token, employee_id)
            )
            employees = client.list_employees(self._token)
            persisted_employee = next(
                (
                    item
                    for item in employees
                    if item.id == employee_id
                ),
                employee,
            )
            updated_view = self._employee_view(persisted_employee)
            confirmed_active = persisted_employee.ativo
            updated_view["situacao"] = "ativo" if confirmed_active else "inativo"
            updated_rows = []
            for item in self.funcionarios:
                if item["id"] == str(employee_id):
                    updated_view["endereco"] = (
                        employee.endereco or item.get("endereco", "")
                    )
                    updated_view["email"] = employee.email or item.get("email", "")
                    updated_view["telefone"] = (
                        employee.telefone or item.get("telefone", "")
                    )
                    updated_view["nome"] = employee.nome or item.get("nome", "")
                    updated_rows.append(updated_view)
                else:
                    updated_rows.append(item)
            self.funcionarios = updated_rows
            self.funcionario_ativo = confirmed_active
            if was_active:
                self.mensagem = (
                    "Funcionário inativado."
                    if not confirmed_active
                    else "Situação do funcionário atualizada."
                )
            else:
                self.mensagem = (
                    "Funcionário reativado."
                    if confirmed_active
                    else "Não foi possível reativar o funcionário."
                )
            self.confirmando_inativacao = False
        except ValueError:
            self.mensagem = "Informe um ID de funcionário válido."
        except XanoUnauthorizedError:
            self._expire_session()
        except XanoForbiddenError:
            self.mensagem = FORBIDDEN_MESSAGE
        except XanoUnavailableError:
            self.mensagem = UNAVAILABLE_MESSAGE
        except XanoError as exc:
            self.mensagem = exc.message

    @rx.event
    def request_deactivate_employee(self) -> None:
        if not self.is_gestor:
            self.mensagem = FORBIDDEN_MESSAGE
            return
        try:
            int(self.funcionario_id)
        except ValueError:
            self.mensagem = "Informe um ID de funcionário válido."
            return
        self.confirmando_inativacao = True

    @rx.event
    def cancel_deactivate_employee(self) -> None:
        self.confirmando_inativacao = False

    @rx.event
    def create_customer(self) -> None:
        if self.is_gestor:
            self.mensagem = FORBIDDEN_MESSAGE
            return
        if not self._valid_customer_cpf():
            return
        address_payloads = self._customer_address_payloads()
        if address_payloads is None:
            return
        try:
            customer = XanoClient().create_customer(
                self._token,
                self._customer_payload(),
            )
            self.cliente_id = str(customer.id)
            if not self._save_customer_addresses(customer.id):
                if not self.authenticated:
                    return
                return
            customer_view = self._customer_view(customer)
            customer_view["endereco"] = (
                self._format_customer_address_from_form(
                    self.cliente_enderecos[0]
                )
                if self.cliente_enderecos
                else "—"
            )
            self.clientes = [*self.clientes, customer_view]
            self.mensagem = "Cliente cadastrado."
            self.cliente_form_aberto = False
        except ValueError:
            self.mensagem = "Preencha a data de nascimento no formato AAAA-MM-DD."
        except XanoUnauthorizedError:
            self._expire_session()
        except XanoForbiddenError:
            self.mensagem = FORBIDDEN_MESSAGE
        except XanoUnavailableError:
            self.mensagem = UNAVAILABLE_MESSAGE
        except XanoError as exc:
            self.mensagem = exc.message

    @rx.event
    def update_customer(self) -> rx.event.EventSpec | None:
        if self.is_gestor:
            self.mensagem = FORBIDDEN_MESSAGE
            return
        if not self._valid_customer_cpf():
            return None
        address_payloads = self._customer_address_payloads()
        if address_payloads is None:
            return
        try:
            customer_id = int(self.cliente_id)
            customer = XanoClient().update_customer(
                self._token,
                customer_id,
                self._customer_payload(),
            )
            customer_view = self._customer_view(customer)
            customer_view["endereco"] = (
                self._format_customer_address_from_form(
                    self.cliente_enderecos[0]
                )
                if self.cliente_enderecos
                else "—"
            )
            self.clientes = [
                customer_view
                if item["id"] == str(customer_id)
                else item
                for item in self.clientes
            ]
            if not self._save_customer_addresses(customer_id):
                if not self.authenticated:
                    return rx.redirect("/login")
                return None
            self.mensagem = "Cliente atualizado."
            self.cliente_form_aberto = False
        except ValueError:
            self.mensagem = "Informe um ID e uma data válidos."
        except XanoUnauthorizedError:
            self._expire_session()
        except XanoForbiddenError:
            self.mensagem = FORBIDDEN_MESSAGE
        except XanoUnavailableError:
            self.mensagem = UNAVAILABLE_MESSAGE
        except XanoError as exc:
            self.mensagem = exc.message

    def _customer_address_payloads(
        self,
    ) -> list[tuple[str, str, dict[str, object]]] | None:
        address_payloads = []
        for address in self.cliente_enderecos:
            payload = self._customer_address_payload(address)
            if payload is None:
                return None
            address_payloads.append(
                (address["form_key"], address["id"], payload)
            )
        return address_payloads

    def _save_customer_addresses(
        self,
        customer_id: int,
    ) -> bool:
        saved_addresses, error = persist_customer_addresses(
            XanoClient(),
            self._token,
            customer_id,
            self.cliente_enderecos,
        )
        self.cliente_enderecos = saved_addresses
        if isinstance(error, XanoUnauthorizedError):
            self._expire_session()
            return False
        if isinstance(error, XanoForbiddenError):
            self.mensagem = FORBIDDEN_MESSAGE
            return False
        if isinstance(error, XanoUnavailableError):
            self.mensagem = UNAVAILABLE_MESSAGE
            return False
        if isinstance(error, XanoError):
            self.mensagem = error.message
            return False
        if isinstance(error, ValueError):
            self.mensagem = "Informe um ID de endereço válido."
            return False
        return True

    @rx.event
    def deactivate_customer(self) -> None:
        if self.is_gestor:
            self.mensagem = FORBIDDEN_MESSAGE
            return
        try:
            customer_id = int(self.cliente_id)
            XanoClient().deactivate_customer(self._token, customer_id)
            self.clientes = [
                item for item in self.clientes if item["id"] != str(customer_id)
            ]
            self.mensagem = "Cliente inativado."
            self.cliente_form_aberto = False
        except ValueError:
            self.mensagem = "Informe um ID de cliente válido."
        except XanoUnauthorizedError:
            self._expire_session()
        except XanoForbiddenError:
            self.mensagem = FORBIDDEN_MESSAGE
        except XanoUnavailableError:
            self.mensagem = UNAVAILABLE_MESSAGE
        except XanoError as exc:
            self.mensagem = exc.message

    @rx.event
    def edit_customer(
        self,
        customer_id: str,
    ) -> rx.event.EventSpec | None:
        customer = next(
            (item for item in self.clientes if item["id"] == customer_id),
            None,
        )
        if customer is None:
            self.mensagem = "Cliente não encontrado."
            return
        self.cliente_id = customer["id"]
        self.cliente_nome = customer["nome"]
        self.cliente_cpf = customer["cpf"]
        self.cliente_data_nascimento = customer["nascimento"]
        self.cliente_telefone = customer["telefone"]
        self.cliente_email = customer["email"]
        self.mensagem = ""
        self.cliente_enderecos = []
        self.cliente_endereco_proxima_chave = 0
        self.cliente_form_aberto = True
        try:
            addresses = XanoClient().list_addresses(self._token, int(customer_id))
            self.cliente_enderecos = [
                self._customer_address_form_view(address, str(index))
                for index, address in enumerate(addresses)
            ]
            self.cliente_endereco_proxima_chave = len(addresses)
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
    def deactivate_customer_by_id(self, customer_id: str) -> None:
        self.cliente_id = customer_id
        self.deactivate_customer()

    @rx.event
    def load_addresses(self) -> None:
        try:
            customer_id = int(self.cliente_id)
            self._set_addresses(
                XanoClient().list_addresses(self._token, customer_id)
            )
            self.mensagem = "Enderecos carregados."
        except ValueError:
            self.mensagem = "Informe um ID de cliente válido."
        except XanoUnauthorizedError:
            self._expire_session()
        except XanoForbiddenError:
            self.mensagem = FORBIDDEN_MESSAGE
        except XanoUnavailableError:
            self.mensagem = UNAVAILABLE_MESSAGE
        except XanoError as exc:
            self.mensagem = exc.message

    @rx.event
    def create_address(self) -> None:
        if self.is_gestor:
            self.mensagem = FORBIDDEN_MESSAGE
            return
        try:
            customer_id = int(self.cliente_id)
            address = XanoClient().create_address(
                self._token,
                customer_id,
                self._address_payload(),
            )
            self.enderecos = [*self.enderecos, self._address_view(address)]
            self.mensagem = "Endereco cadastrado."
        except ValueError:
            self.mensagem = "Informe um ID de cliente válido."
        except XanoUnauthorizedError:
            self._expire_session()
        except XanoForbiddenError:
            self.mensagem = FORBIDDEN_MESSAGE
        except XanoUnavailableError:
            self.mensagem = UNAVAILABLE_MESSAGE
        except XanoError as exc:
            self.mensagem = exc.message

    @rx.event
    def create_sale(self) -> rx.event.EventSpec | None:
        if self.is_gestor:
            self.mensagem = FORBIDDEN_MESSAGE
            return None
        try:
            client_id = (
                int(self.venda_cliente_id) if self.venda_cliente_id.strip() else None
            )
        except ValueError:
            self.mensagem = "Informe um ID de cliente válido."
            return None
        if not self.venda_itens:
            self.mensagem = "Adicione ao menos um item ao pedido."
            return None
        controlled_product_ids = {
            str(product["id"])
            for product in getattr(self, "produtos", [])
            if product.get("controlado") == "Sim"
        }
        has_controlled_item = any(
            item["id_produto"] in controlled_product_ids
            for item in self.venda_itens
        )
        if has_controlled_item and not self.venda_receita.strip():
            self.mensagem = (
                "Venda de medicamento controlado não pode ser realizada "
                "sem número da receita."
            )
            return None
        try:
            client = XanoClient()
            order = client.create_order(
                self._token,
                client_id=client_id,
                channel=self.venda_canal,
                items=[
                    {
                        "id_produto": int(item["id_produto"]),
                        "quantidade": int(item["quantidade"]),
                    }
                    for item in self.venda_itens
                ],
            )
            order_id = int(order["pedido"]["id"])
            client.confirm_order(
                self._token,
                order_id,
                self.venda_pagamento,
                self.venda_receita.strip() or None,
            )
            self.mensagem = "Venda confirmada."
            self.venda_produto_id = ""
            self.venda_quantidade = "1"
            self.venda_cliente_id = ""
            self.venda_receita = ""
            self.venda_itens = []
        except XanoUnauthorizedError:
            self._expire_session()
            return rx.redirect("/login")
        except XanoForbiddenError:
            self.mensagem = FORBIDDEN_MESSAGE
        except XanoUnavailableError:
            self.mensagem = UNAVAILABLE_MESSAGE
        except (XanoError, KeyError, TypeError, ValueError) as exc:
            self.mensagem = exc.message if isinstance(exc, XanoError) else "Não foi possível concluir a venda."
        return None

    @rx.event
    def load_sales(self) -> rx.event.EventSpec | None:
        redirect = self._redirect_if_missing_token()
        if redirect is not None:
            return redirect
        try:
            with XanoClient() as client:
                sales, payments = client.list_sale_history(
                    self._token,
                    is_gestor=self.is_gestor,
                )
                orders, items = client.list_orders(
                    self._token,
                    is_gestor=self.is_gestor,
                )
                products = client.list_products(self._token)
                customers = (
                    client.list_customers(self._token)
                    if self.is_gestor
                    else []
                )
                employees = (
                    client.list_employees(self._token)
                    if self.is_gestor
                    else []
                )
            orders_by_id = {order.id: order for order in orders}
            products_by_id = {product.id: product.nome for product in products}
            customers_by_id = {customer.id: customer.nome for customer in customers}
            employees_by_id = {employee.id: employee.nome for employee in employees}
            items_by_order: dict[int, list[str]] = {}
            for item in items:
                items_by_order.setdefault(int(item["id_pedido"]), []).append(
                    f'{item["quantidade"]}x '
                    f'{products_by_id.get(int(item["id_produto"]), f"Produto {item["id_produto"]}")}'
                )
            payments_by_sale = {
                int(payment["id_venda"]): str(payment.get("forma_pagamento") or "")
                for payment in payments
            }
            self.vendas = [
                {
                    "id": f"#{sale.id}",
                    "pedido": str(sale.id_pedido),
                    "total": f"{sale.valor_total:.2f}",
                    "status": sale.status,
                    "data": self._format_sale_date(sale.data_venda),
                    "cliente": str(
                        customers_by_id.get(
                            int(orders_by_id[sale.id_pedido].id_cliente),
                            "balcão",
                        )
                    )
                    if (
                        sale.id_pedido in orders_by_id
                        and orders_by_id[sale.id_pedido].id_cliente is not None
                    )
                    else "balcão",
                    "produtos": ", ".join(
                        items_by_order.get(sale.id_pedido, [])
                    )
                    or "—",
                    "canal": orders_by_id.get(sale.id_pedido).canal
                    if sale.id_pedido in orders_by_id
                    else "",
                    "atendente": str(
                        employees_by_id.get(
                            int(orders_by_id[sale.id_pedido].id_funcionario),
                            f"Funcionário {orders_by_id[sale.id_pedido].id_funcionario}",
                        )
                    )
                    if sale.id_pedido in orders_by_id
                    else "",
                    "pagamento": payments_by_sale.get(sale.id, ""),
                }
                for sale in sales
            ]
            self.pedidos = [
                {
                    "id": str(order.id),
                    "cliente": str(order.id_cliente or "balcão"),
                    "status": order.status,
                    "canal": order.canal,
                    "data": order.data_pedido,
                }
                for order in orders
            ]
            self.itens_pedido = [
                {
                    "pedido": str(item["id_pedido"]),
                    "produto": str(item["id_produto"]),
                    "quantidade": str(item["quantidade"]),
                }
                for item in items
            ]
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
    def create_product(self) -> None:
        if not self.is_gestor:
            self.mensagem = FORBIDDEN_MESSAGE
            return
        if not self.produto_fornecedor_id:
            self.mensagem = "Selecione um fornecedor cadastrado."
            return
        try:
            product = XanoClient().create_product(
                self._token,
                self._product_payload(),
            )
            self.produtos = [
                *self.produtos,
                self._product_view(product),
            ]
            self.mensagem = "Produto cadastrado."
            self.close_product_modal()
            self._clear_product_form()
        except ValueError:
            self.mensagem = "Preencha os campos numéricos com valores válidos."
        except XanoUnauthorizedError:
            self._expire_session()
        except XanoForbiddenError:
            self.mensagem = FORBIDDEN_MESSAGE
        except XanoUnavailableError:
            self.mensagem = UNAVAILABLE_MESSAGE
        except XanoError as exc:
            self.mensagem = exc.message

    @rx.event
    def deactivate_product(self) -> None:
        if not self.is_gestor:
            self.mensagem = FORBIDDEN_MESSAGE
            return
        try:
            product_id = int(self.produto_id)
            XanoClient().deactivate_product(self._token, product_id)
            self.produtos = [
                product for product in self.produtos
                if product["id"] != str(product_id)
            ]
            self.produto_id = ""
            self.mensagem = "Produto inativado."
        except ValueError:
            self.mensagem = "Informe um ID de produto válido."
        except XanoUnauthorizedError:
            self._expire_session()
        except XanoForbiddenError:
            self.mensagem = FORBIDDEN_MESSAGE
        except XanoUnavailableError:
            self.mensagem = UNAVAILABLE_MESSAGE
        except XanoError as exc:
            self.mensagem = exc.message

    @rx.event
    def deactivate_product_by_id(self, product_id: str) -> None:
        self.produto_id = product_id
        self.deactivate_product()

    @rx.event
    def update_product(self) -> rx.event.EventSpec | None:
        if not self.is_gestor:
            self.mensagem = FORBIDDEN_MESSAGE
            return
        if not self.produto_fornecedor_id:
            self.mensagem = "Selecione um fornecedor cadastrado."
            return
        try:
            product_id = int(self.produto_id)
            product = XanoClient().update_product(
                self._token,
                product_id,
                self._product_payload(),
            )
            self.produtos = [
                self._product_view(product)
                if item["id"] == str(product_id)
                else item
                for item in self.produtos
            ]
            self.mensagem = "Produto atualizado."
            self.close_product_modal()
        except ValueError:
            self.mensagem = "Preencha o ID e os campos numéricos com valores válidos."
        except XanoUnauthorizedError:
            self._expire_session()
        except XanoForbiddenError:
            self.mensagem = FORBIDDEN_MESSAGE
        except XanoUnavailableError:
            self.mensagem = UNAVAILABLE_MESSAGE
        except XanoError as exc:
            self.mensagem = exc.message

    @rx.event
    def select_supplier(self, supplier_id: str) -> None:
        supplier = next(
            (item for item in self.fornecedores if item["id"] == supplier_id),
            None,
        )
        if supplier is None:
            self.mensagem = "Fornecedor não encontrado na lista carregada."
            return
        self.fornecedor_id = supplier["id"]
        self.fornecedor_nome = supplier["nome"]
        self.fornecedor_cnpj = supplier["cnpj"]
        self.fornecedor_telefone = supplier["telefone"]
        self.fornecedor_email = supplier["email"]
        self.fornecedor_endereco = supplier["endereco"]
        self.fornecedor_prazo_entrega = supplier["prazo_entrega"]
        self.mensagem = ""

    @rx.event
    def open_new_supplier(self) -> None:
        self._clear_supplier_form()
        self.fornecedor_editando = False
        self.fornecedor_modal_aberto = True

    @rx.event
    def edit_supplier(self, supplier_id: str) -> None:
        self.fornecedor_id = ""
        self.select_supplier(supplier_id)
        if self.fornecedor_id:
            self.fornecedor_editando = True
            self.fornecedor_modal_aberto = True

    @rx.event
    def close_supplier_modal(self) -> None:
        self.fornecedor_modal_aberto = False
        self.fornecedor_editando = False

    @rx.event
    def save_supplier(self) -> None:
        if self.fornecedor_editando:
            self.update_supplier()
        else:
            self.create_supplier()

    @rx.event
    def request_delete_supplier_by_id(self, supplier_id: str) -> None:
        self.fornecedor_id = ""
        self.select_supplier(supplier_id)
        if self.fornecedor_id:
            self.confirmando_remocao_fornecedor = True

    @rx.event
    def create_supplier(self) -> None:
        if not self.is_gestor:
            self.mensagem = FORBIDDEN_MESSAGE
            return
        try:
            supplier = XanoClient().create_supplier(
                self._token,
                self._supplier_payload(),
            )
            self.fornecedores = [
                *self.fornecedores,
                self._supplier_view(supplier),
            ]
            self._clear_supplier_form()
            self.mensagem = "Fornecedor cadastrado."
        except XanoUnauthorizedError:
            self._expire_session()
        except XanoForbiddenError:
            self.mensagem = FORBIDDEN_MESSAGE
        except XanoUnavailableError:
            self.mensagem = UNAVAILABLE_MESSAGE
        except XanoError as exc:
            self.mensagem = exc.message

    @rx.event
    def update_supplier(self) -> None:
        if not self.is_gestor:
            self.mensagem = FORBIDDEN_MESSAGE
            return
        try:
            supplier_id = int(self.fornecedor_id)
            supplier = XanoClient().update_supplier(
                self._token,
                supplier_id,
                self._supplier_payload(),
            )
            self.fornecedores = [
                self._supplier_view(supplier)
                if item["id"] == str(supplier_id)
                else item
                for item in self.fornecedores
            ]
            self._clear_supplier_form()
            self.mensagem = "Fornecedor atualizado."
        except ValueError:
            self.mensagem = "Selecione um fornecedor válido para atualizar."
        except XanoUnauthorizedError:
            self._expire_session()
        except XanoForbiddenError:
            self.mensagem = FORBIDDEN_MESSAGE
        except XanoUnavailableError:
            self.mensagem = UNAVAILABLE_MESSAGE
        except XanoError as exc:
            self.mensagem = exc.message

    @rx.event
    def request_delete_supplier(self) -> None:
        if not self.is_gestor:
            self.mensagem = FORBIDDEN_MESSAGE
            return
        try:
            int(self.fornecedor_id)
        except ValueError:
            self.mensagem = "Selecione um fornecedor válido para remover."
            return
        self.confirmando_remocao_fornecedor = True

    @rx.event
    def cancel_delete_supplier(self) -> None:
        self.confirmando_remocao_fornecedor = False

    @rx.event
    def delete_supplier(self) -> None:
        if not self.is_gestor:
            self.mensagem = FORBIDDEN_MESSAGE
            return
        try:
            supplier_id = int(self.fornecedor_id)
            XanoClient().delete_supplier(self._token, supplier_id)
            self.fornecedores = [
                item
                for item in self.fornecedores
                if item["id"] != str(supplier_id)
            ]
            self._clear_supplier_form()
            self.confirmando_remocao_fornecedor = False
            self.mensagem = "Fornecedor removido."
        except ValueError:
            self.mensagem = "Selecione um fornecedor válido para remover."
        except XanoUnauthorizedError:
            self._expire_session()
        except XanoForbiddenError:
            self.mensagem = FORBIDDEN_MESSAGE
        except XanoUnavailableError:
            self.mensagem = UNAVAILABLE_MESSAGE
        except XanoError as exc:
            self.confirmando_remocao_fornecedor = False
            self.mensagem = exc.message

    @rx.event
    def create_category(self) -> None:
        if not self.is_gestor:
            self.mensagem = FORBIDDEN_MESSAGE
            return
        try:
            category = XanoClient().create_category(
                self._token,
                self.categoria_nome,
            )
            self.categorias = [
                *self.categorias,
                {"id": str(category.id), "nome": category.nome},
            ]
            self.categoria_nome = ""
            self.categoria_form_aberta = False
            self.mensagem = "Categoria cadastrada."
        except XanoUnauthorizedError:
            self._expire_session()
        except XanoForbiddenError:
            self.mensagem = FORBIDDEN_MESSAGE
        except XanoUnavailableError:
            self.mensagem = UNAVAILABLE_MESSAGE
        except XanoError as exc:
            self.mensagem = exc.message

    @rx.event
    def update_category(self) -> None:
        if not self.is_gestor:
            self.mensagem = FORBIDDEN_MESSAGE
            return
        try:
            category_id = int(self.categoria_id)
            category = XanoClient().update_category(
                self._token,
                category_id,
                self.categoria_nome,
            )
            self.categorias = [
                {"id": str(category.id), "nome": category.nome}
                if item["id"] == str(category_id)
                else item
                for item in self.categorias
            ]
            self.mensagem = "Categoria atualizada."
        except ValueError:
            self.mensagem = "Informe um ID de categoria válido."
        except XanoUnauthorizedError:
            self._expire_session()
        except XanoForbiddenError:
            self.mensagem = FORBIDDEN_MESSAGE
        except XanoUnavailableError:
            self.mensagem = UNAVAILABLE_MESSAGE
        except XanoError as exc:
            self.mensagem = exc.message

    @rx.event
    def deactivate_category(self) -> None:
        if not self.is_gestor:
            self.mensagem = FORBIDDEN_MESSAGE
            return
        try:
            category_id = int(self.categoria_id)
            XanoClient().deactivate_category(self._token, category_id)
            self.categorias = [
                item
                for item in self.categorias
                if item["id"] != str(category_id)
            ]
            self.categoria_id = ""
            self.mensagem = "Categoria inativada."
        except ValueError:
            self.mensagem = "Informe um ID de categoria válido."
        except XanoUnauthorizedError:
            self._expire_session()
        except XanoForbiddenError:
            self.mensagem = FORBIDDEN_MESSAGE
        except XanoUnavailableError:
            self.mensagem = UNAVAILABLE_MESSAGE
        except XanoError as exc:
            self.mensagem = exc.message

    def _product_payload(self) -> dict[str, object]:
        return {
            "id_categoria": int(self.produto_categoria_id),
            "id_fornecedor": int(self.produto_fornecedor_id),
            "nome": self.produto_nome,
            "descricao": self.produto_descricao or None,
            "codigo_barras": self.produto_codigo_barras or None,
            "controlado": self.produto_controlado,
            "preco_venda": float(self.produto_preco),
            "quantidade_estoque": int(self.produto_quantidade),
            "estoque_minimo": int(self.produto_estoque_minimo),
        }

    def _customer_payload(self) -> dict[str, object]:
        return {
            "nome": self.cliente_nome,
            "cpf": "".join(character for character in self.cliente_cpf if character.isdigit()) or None,
            "data_nascimento": self.cliente_data_nascimento,
            "telefone": self.cliente_telefone or None,
            "email": self.cliente_email or None,
        }

    def _valid_customer_cpf(self) -> bool:
        cpf = "".join(character for character in self.cliente_cpf if character.isdigit())
        if not cpf:
            return True
        if not self._is_valid_cpf(cpf):
            self.mensagem = "Informe um CPF válido com 11 dígitos."
            return False
        self.cliente_cpf = cpf
        return True

    @staticmethod
    def _is_valid_cpf(cpf: str) -> bool:
        cpf = "".join(character for character in cpf if character.isdigit())
        if len(cpf) != 11 or len(set(cpf)) == 1:
            return False

        for digit_index in (9, 10):
            total = sum(
                int(cpf[index]) * (digit_index + 1 - index)
                for index in range(digit_index)
            )
            remainder = (total * 10) % 11
            expected_digit = 0 if remainder == 10 else remainder
            if int(cpf[digit_index]) != expected_digit:
                return False
        return True

    def _valid_employee_cpf(self) -> bool:
        cpf = "".join(
            character for character in self.funcionario_cpf if character.isdigit()
        )
        if not cpf or not self._is_valid_cpf(cpf):
            self.mensagem = "Informe um CPF válido com 11 dígitos."
            return False
        self.funcionario_cpf = cpf
        return True

    def _valid_employee_update_cpf(self) -> bool:
        cpf_digitado = "".join(
            character for character in self.funcionario_cpf if character.isdigit()
        )
        employee_id = str(self.funcionario_id)
        if any(
            item["id"] != employee_id
            and "".join(
                character for character in item["cpf"] if character.isdigit()
            )
            == cpf_digitado
            for item in self.funcionarios
        ):
            self.mensagem = "O CPF já está cadastrado."
            return False
        return True

    def _customer_address_payload(
        self,
        address: dict[str, str],
    ) -> dict[str, object] | None:
        payload, error = build_customer_address_payload(address)
        if error is not None:
            self.mensagem = error
        return payload

    def _address_payload(self) -> dict[str, object]:
        return {
            "logradouro": self.endereco_logradouro or None,
            "numero": self.endereco_numero or None,
            "bairro": self.endereco_bairro or None,
            "cidade": self.endereco_cidade,
            "estado": self.endereco_estado,
            "cep": self.endereco_cep or None,
            "complemento": self.endereco_complemento,
        }

    def _employee_payload(self, *, include_login: bool) -> dict[str, object]:
        payload: dict[str, object] = {
            "nome": self.funcionario_nome,
            "cpf": self.funcionario_cpf,
            "data_nascimento": self.funcionario_data_nascimento or None,
            "telefone": self.funcionario_telefone or None,
            "email": self.funcionario_email or None,
            "cargo": self.funcionario_cargo or None,
            "endereco": self.funcionario_endereco or None,
            "salario": float(self.funcionario_salario)
            if self.funcionario_salario.strip()
            else None,
        }
        if include_login:
            payload["login"] = self.funcionario_login
            payload["senha_inicial"] = (
                self.funcionario_senha_inicial.strip() or None
            )
        return payload

    def _clear_employee_form(self) -> None:
        self.funcionario_id = ""
        self.funcionario_nome = ""
        self.funcionario_cpf = ""
        self.funcionario_data_nascimento = ""
        self.funcionario_telefone = ""
        self.funcionario_email = ""
        self.funcionario_endereco = ""
        self.funcionario_cargo = ""
        self.funcionario_salario = ""
        self.funcionario_login = ""
        self.funcionario_senha_inicial = ""

    def _clear_product_form(self) -> None:
        self.produto_id = ""
        self.produto_categoria_id = ""
        self.produto_fornecedor_id = ""
        self.produto_nome = ""
        self.produto_descricao = ""
        self.produto_codigo_barras = ""
        self.produto_preco = ""
        self.produto_quantidade = "0"
        self.produto_estoque_minimo = "0"
        self.produto_controlado = False

    def _set_products(self, products: list[object]) -> None:
        self.produtos = [self._product_view(product) for product in products]

    def _set_categories(self, categories: list[object]) -> None:
        self.categorias = [
            {"id": str(category.id), "nome": category.nome}
            for category in categories
        ]
        category_names = {item["id"]: item["nome"] for item in self.categorias}
        self.produtos = [
            {
                **product,
                "categoria": category_names.get(
                    product["categoria"], product["categoria"]
                ),
            }
            for product in self.produtos
        ]

    def _set_customers(
        self,
        customers: list[Customer],
        addresses_by_customer: dict[str, str] | None = None,
    ) -> None:
        addresses_by_customer = addresses_by_customer or {}
        self.clientes = [
            {
                **self._customer_view(customer),
                "endereco": addresses_by_customer.get(str(customer.id), "—"),
            }
            for customer in customers
            if self.is_gestor or customer.ativo
        ]

    def _set_addresses(self, addresses: list[Address]) -> None:
        self.enderecos = [self._address_view(address) for address in addresses]

    def _set_employees(self, employees: list[Employee]) -> None:
        self.funcionarios = [self._employee_view(employee) for employee in employees]

    def _set_suppliers(self, suppliers: list[object]) -> None:
        self.fornecedores = [self._supplier_view(supplier) for supplier in suppliers]

    @staticmethod
    def _customer_view(customer: Customer) -> dict[str, str]:
        return {
            "id": str(customer.id),
            "nome": customer.nome,
            "cpf": customer.cpf,
            "telefone": customer.telefone,
            "email": customer.email,
            "nascimento": customer.data_nascimento,
            "situacao": "ativo" if customer.ativo else "inativo",
            "endereco": "—",
        }

    @staticmethod
    def _address_view(address: Address) -> dict[str, str]:
        return {
            "id": str(address.id),
            "cliente": str(address.id_cliente),
            "logradouro": address.logradouro,
            "numero": address.numero,
            "bairro": address.bairro,
            "cidade": address.cidade,
            "estado": address.estado,
            "cep": address.cep,
            "complemento": address.complemento,
        }

    @staticmethod
    def _format_customer_address(address: Address) -> str:
        parts = [
            address.logradouro,
            address.numero,
            address.bairro,
            address.cidade,
            address.estado,
        ]
        return ", ".join(part for part in parts if part)

    @staticmethod
    def _format_customer_address_from_form(address: dict[str, str]) -> str:
        parts = [
            address.get("logradouro", ""),
            address.get("numero", ""),
            address.get("bairro", ""),
            address.get("cidade", ""),
            address.get("estado", ""),
        ]
        return ", ".join(part for part in parts if part) or "—"

    @staticmethod
    def _customer_address_form_view(
        address: Address,
        form_key: str,
    ) -> dict[str, str]:
        return {
            **State._address_view(address),
            "form_key": form_key,
        }

    @staticmethod
    def _employee_view(employee: Employee) -> dict[str, str]:
        return {
            "id": str(employee.id),
            "nome": employee.nome,
            "cpf": employee.cpf,
            "telefone": employee.telefone,
            "cargo": employee.cargo,
            "salario": (
                f"R$ {employee.salario:.2f}"
                if employee.salario is not None
                else ""
            ),
            "email": employee.email,
            "endereco": employee.endereco,
            "usuario": employee.email or "—",
            "situacao": "ativo" if employee.ativo else "inativo",
        }

    @staticmethod
    def _supplier_view(supplier: object) -> dict[str, str]:
        return {
            "id": str(supplier.id),
            "nome": supplier.nome,
            "cnpj": supplier.cnpj,
            "telefone": supplier.telefone,
            "email": supplier.email,
            "endereco": supplier.endereco,
            "prazo_entrega": supplier.prazo_entrega,
        }

    @staticmethod
    def _product_view(product: object) -> dict[str, str]:
        return {
            "id": str(product.id),
            "nome": product.nome,
            "descricao": product.descricao,
            "codigo_barras": product.codigo_barras,
            "categoria": str(product.id_categoria),
            "categoria_id": str(product.id_categoria),
            "fornecedor_id": str(product.id_fornecedor),
            "estoque": str(product.quantidade_estoque),
            "minimo": str(product.estoque_minimo),
            "preco": f"R$ {product.preco_venda:.2f}",
            "controlado": "Sim" if product.controlado else "—",
            "situacao": (
                "repor"
                if product.quantidade_estoque < product.estoque_minimo
                else "regular"
            ),
        }

    @staticmethod
    def _format_sale_date(value: str) -> str:
        value = str(value).strip()
        if not value:
            return ""
        try:
            numeric_timestamp = float(value)
            timestamp_seconds = (
                numeric_timestamp / 1000
                if abs(numeric_timestamp) >= 100000000000
                else numeric_timestamp
            )
            sale_date = datetime.fromtimestamp(timestamp_seconds).astimezone()
        except (ValueError, TypeError, OverflowError, OSError):
            try:
                sale_date = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return value
        if sale_date.date() == datetime.now().date():
            return "Hoje"
        return sale_date.strftime("%d/%m")

    def _set_session(self, session: Session) -> None:
        self.nome = session.nome
        self.login = session.login
        self.perfil_acesso = session.perfil_acesso
        self.authenticated = True
        self.session_ready = True
        self.mensagem = ""
        if session.perfil_acesso != "gestor":
            self._clear_dashboard()
            self._clear_suppliers()

    def _clear_dashboard(self) -> None:
        self.dashboard_total_vendas = 0
        self.dashboard_valor_total = 0.0
        self.dashboard_itens_vendidos = 0
        self.dashboard_funcionarios_ativos = 0
        self.dashboard_estoque_critico = []
        self.dashboard_mais_vendidos = []
        self.dashboard_carregado = False

    def logout_local(self) -> None:
        self._token = ""
        self.authenticated = False
        self.session_ready = True
        self.nome = ""
        self.login = ""
        self.perfil_acesso = ""
        self._clear_dashboard()
        self._clear_suppliers()

    def _clear_suppliers(self) -> None:
        self.fornecedores = []
        self._clear_supplier_form()

    def _clear_supplier_form(self) -> None:
        self.fornecedor_id = ""
        self.fornecedor_nome = ""
        self.fornecedor_cnpj = ""
        self.fornecedor_telefone = ""
        self.fornecedor_email = ""
        self.fornecedor_endereco = ""
        self.fornecedor_prazo_entrega = ""
        self.confirmando_remocao_fornecedor = False
        self.fornecedor_modal_aberto = False
        self.fornecedor_editando = False

    def _supplier_payload(self) -> dict[str, object]:
        return {
            "nome": self.fornecedor_nome,
            "cnpj": self.fornecedor_cnpj,
            "telefone": self.fornecedor_telefone or None,
            "email": self.fornecedor_email,
            "endereco": self.fornecedor_endereco,
            "prazo_entrega": self.fornecedor_prazo_entrega or None,
        }

    def _expire_session(self) -> None:
        self.logout_local()
        self.mensagem = SESSION_EXPIRED_MESSAGE


def login_role_card(label: str, role: str, icon: str) -> rx.Component:
    return rx.button(
        rx.box(
            rx.icon(tag=icon, size=18),
            class_name="role-icon",
        ),
        rx.text(label, class_name="role-label"),
        on_click=State.set_login_role(role),
        class_name=rx.cond(
            State.login_role == role,
            "role-card role-card-active",
            "role-card",
        ),
        type="button",
    )


def feedback_message() -> rx.Component:
    return rx.cond(
        State.mensagem != "",
        rx.box(
            rx.text(State.mensagem),
            key=State.mensagem,
            class_name=rx.cond(
                State.feedback_is_error,
                "feedback feedback-error",
                "feedback feedback-success",
            ),
        ),
        rx.fragment(),
    )


def page_header(
    title: str,
    description: str = "",
    title_class_name: str = "page-title",
) -> rx.Component:
    return rx.vstack(
        rx.heading(title, size="7", class_name=title_class_name),
        rx.cond(
            description != "",
            rx.text(description, class_name="page-description"),
            rx.fragment(),
        ),
        align_items="start",
        width="100%",
        spacing="1",
    )


def content_card(content: rx.Component, class_name: str = "") -> rx.Component:
    return rx.box(content, class_name=f"content-card {class_name}".strip(), width="100%")


def status_badge(label: str, tone: str = "success") -> rx.Component:
    return rx.text(label, class_name=f"status-badge status-badge-{tone}")


def channel_badge(channel: rx.Var) -> rx.Component:
    return rx.text(
        channel,
        class_name=rx.cond(
            channel == "online",
            "status-badge channel-badge channel-badge-online",
            "status-badge channel-badge channel-badge-presencial",
        ),
    )


def navigation_tab(label: str, href: str) -> rx.Component:
    return rx.link(
        label,
        href=href,
        class_name=rx.cond(
            State.router.page.path == href,
            "nav-tab nav-tab-active",
            "nav-tab",
        ),
    )


def feature_pill(label: str, tone: str) -> rx.Component:
    return rx.hstack(
        rx.box(class_name=f"feature-pill-dot feature-pill-dot-{tone}"),
        rx.text(label),
        class_name=f"feature-pill feature-pill-{tone}",
        align_items="center",
        spacing="2",
    )


def section_heading(
    title: str,
    description: str = "",
    heading_class_name: str = "",
) -> rx.Component:
    return rx.vstack(
        rx.heading(title, size="5", class_name=heading_class_name),
        rx.cond(
            description != "",
            rx.text(description, class_name="muted"),
            rx.fragment(),
        ),
        align_items="start",
        spacing="1",
        width="100%",
    )


def login_page() -> rx.Component:
    return rx.box(
        rx.box(
            rx.box(class_name="login-blob login-blob-left"),
            rx.box(class_name="login-blob login-blob-right"),
            class_name="login-decoration",
        ),
        rx.box(
            rx.hstack(
                rx.box(
                    rx.box(
                        rx.box(class_name="login-logo-plus-horizontal"),
                        rx.box(class_name="login-logo-plus-vertical"),
                        class_name="login-logo-plus",
                    ),
                    rx.hstack(
                        rx.box(class_name="login-logo-bar login-logo-bar-short"),
                        rx.box(class_name="login-logo-bar login-logo-bar-medium"),
                        rx.box(class_name="login-logo-bar login-logo-bar-tall"),
                        class_name="login-logo-bars",
                        align_items="end",
                        spacing="1",
                    ),
                    class_name="login-logo-mark",
                ),
                rx.text(
                    "Farma",
                    rx.text("Gestão", as_="span", class_name="login-brand-accent"),
                    class_name="login-brand-neon",
                ),
                align_items="center",
                spacing="2",
                class_name="login-brand",
            ),
            rx.heading(
                "Sua farmácia sob ",
                rx.text("controle total.", as_="span", class_name="neon-gradient-text"),
                size="9",
                class_name="login-hero-title",
            ),
            rx.text(
                "Vendas, estoque, receitas e equipe em um só lugar, com a clareza que o balcão precisa.",
                class_name="login-hero-description",
            ),
            rx.hstack(
                feature_pill("Estoque", "green"),
                feature_pill("Vendas", "cyan"),
                feature_pill("Receitas controladas", "purple"),
                feature_pill("Fornecedores", "yellow"),
                feature_pill("Equipe", "blue"),
                class_name="login-feature-pills",
                wrap="wrap",
            ),
            class_name="login-hero-copy",
        ),
        rx.box(
            rx.vstack(
                rx.heading("Entrar", size="8", class_name="login-title"),
                rx.text(
                    "Você é um...",
                    class_name="login-subtitle",
                ),
                rx.hstack(
                    login_role_card("Colaborador", "colaborador", "user-round"),
                    login_role_card("Gestor", "gestor", "shield-check"),
                    class_name="role-grid",
                    width="100%",
                ),
                rx.vstack(
                    rx.text("Login", class_name="field-label"),
                    rx.input(
                        placeholder="nome",
                        value=State.login_input,
                        on_change=State.set_login_input,
                    ),
                    rx.text("Senha", class_name="field-label"),
                    rx.box(
                        rx.input(
                            placeholder="Sua senha",
                            type=rx.cond(State.senha_visivel, "text", "password"),
                            value=State.senha_input,
                            on_change=State.set_senha_input,
                            class_name="password-input",
                        ),
                        rx.button(
                            rx.cond(State.senha_visivel, "Ocultar", "Mostrar"),
                            on_click=State.alternar_senha,
                            class_name="show-password",
                            type="button",
                        ),
                        class_name="password-field",
                    ),
                    rx.text("Esqueci minha senha", class_name="forgot-password"),
                    rx.button(
                        "Entrar",
                        on_click=State.login_user,
                        class_name="primary-button login-submit",
                        width="100%",
                    ),
                    feedback_message(),
                    width="100%",
                    align_items="stretch",
                    spacing="2",
                ),
                rx.box(class_name="login-panel-line"),
                width="100%",
                spacing="3",
            ),
            class_name="login-panel",
        ),
        class_name="login-page",
    )


def navigation() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.text(
                    "Bem-vindo(a), ",
                    State.nome,
                    class_name="nav-user-title",
                ),
                align_items="start",
                spacing="0",
            ),
            justify="between",
            align_items="center",
            width="100%",
        ),
        rx.hstack(
            rx.cond(
                State.is_gestor,
                rx.hstack(
                    navigation_tab("Visão geral", "/dashboard"),
                    navigation_tab("Vendas", "/vendas"),
                    navigation_tab("Estoque", "/estoque"),
                    navigation_tab("Produtos", "/produtos"),
                    navigation_tab("Clientes", "/clientes"),
                    navigation_tab("Equipe", "/equipe"),
                    navigation_tab("Fornecedores", "/fornecedores"),
                    class_name="nav-tabs",
                ),
                rx.hstack(
                    navigation_tab("Minhas vendas", "/vendas"),
                    navigation_tab("Estoque", "/estoque"),
                    navigation_tab("Clientes", "/clientes"),
                    navigation_tab("Minha conta", "/minha-conta"),
                    class_name="nav-tabs",
                ),
            ),
            rx.button("Sair", on_click=State.logout, class_name="logout-button"),
            width="100%",
            justify="between",
            align_items="center",
            wrap="wrap",
            class_name="nav-menu",
        ),
        class_name="topbar",
    )


def protected_layout(content: rx.Component) -> rx.Component:
    return rx.cond(
        State.authenticated,
        rx.box(
            navigation(),
            rx.box(content, class_name="page-content"),
            class_name="app-shell",
        ),
        rx.center(rx.text("Carregando...", class_name="muted"), min_height="100vh"),
    )


def dashboard_page() -> rx.Component:
    return protected_layout(
        rx.cond(
            State.is_gestor,
            rx.vstack(
                rx.cond(
                    State.dashboard_carregado,
                    rx.vstack(
                        rx.hstack(
                            rx.box(
                                rx.vstack(
                                    rx.text(
                                        State.dashboard_valor_total_brl,
                                        class_name="stat-card-number",
                                    ),
                                    rx.text(
                                        f"{State.dashboard_total_vendas} vendas hoje",
                                        class_name="stat-card-label",
                                    ),
                                ),
                                class_name="stat-card",
                            ),
                            rx.box(
                                rx.vstack(
                                    rx.text(
                                        State.dashboard_itens_vendidos,
                                        class_name="stat-card-number",
                                    ),
                                    rx.text(
                                        "Itens vendidos hoje",
                                        class_name="stat-card-label",
                                    ),
                                ),
                                class_name="stat-card",
                            ),
                            rx.box(
                                rx.vstack(
                                    rx.text(
                                        State.dashboard_estoque_critico.length(),
                                        class_name="stat-card-number",
                                    ),
                                    rx.text(
                                        "Produtos abaixo do mínimo",
                                        class_name="stat-card-label",
                                    ),
                                ),
                                class_name="stat-card",
                            ),
                            rx.box(
                                rx.vstack(
                                    rx.text(
                                        State.dashboard_funcionarios_ativos,
                                        class_name="stat-card-number",
                                    ),
                                    rx.text(
                                        "Funcionários ativos",
                                        class_name="stat-card-label",
                                    ),
                                ),
                                class_name="stat-card",
                            ),
                            width="100%",
                            wrap="wrap",
                            spacing="3",
                            class_name="dashboard-stats",
                        ),
                        content_card(
                            rx.vstack(
                                rx.heading(
                                    "Estoque em atenção",
                                    size="5",
                                    class_name="dashboard-section-title",
                                ),
                                rx.box(
                                    rx.text("Produto", class_name="table-heading"),
                                    rx.text("Estoque", class_name="table-heading"),
                                    rx.text("Mínimo", class_name="table-heading"),
                                    rx.text("Status", class_name="table-heading"),
                                    class_name="stock-alert-head",
                                ),
                                rx.cond(
                                    State.dashboard_estoque_critico.length() > 0,
                                    rx.foreach(
                                        State.dashboard_estoque_critico,
                                        lambda produto: rx.box(
                                            rx.text(produto["nome"], class_name="table-cell"),
                                            rx.text(
                                                produto["estoque"],
                                                class_name=rx.cond(
                                                    produto["situacao"] == "repor",
                                                    "table-cell stock-critical",
                                                    "table-cell",
                                                ),
                                            ),
                                            rx.text(produto["minimo"], class_name="table-cell"),
                                            status_badge("Repor", "danger"),
                                            class_name="stock-alert-row",
                                        ),
                                    ),
                                    rx.text(
                                        "Nenhum produto em risco de estoque.",
                                        class_name="muted",
                                    ),
                                ),
                            ),
                        ),
                    ),
                    rx.cond(
                        State.mensagem != "",
                        feedback_message(),
                        rx.text("Carregando painel...", class_name="muted"),
                    ),
                ),
                spacing="4",
                width="100%",
                class_name="dashboard-page",
            ),
            rx.text(FORBIDDEN_MESSAGE, color="red"),
        )
    )


def customer_list() -> rx.Component:
    return rx.vstack(
        rx.box(
            rx.text("Nome", class_name="customer-table-heading"),
            rx.text("CPF", class_name="customer-table-heading"),
            rx.text("Telefone", class_name="customer-table-heading"),
            rx.text("E-mail", class_name="customer-table-heading"),
            rx.text("Endereço", class_name="customer-table-heading"),
            rx.cond(
                State.is_gestor,
                rx.fragment(),
                rx.text("Ações", class_name="customer-table-heading"),
            ),
            class_name=rx.cond(
                State.is_gestor,
                "customer-table-head customer-table-head-readonly",
                "customer-table-head",
            ),
        ),
        rx.foreach(
            State.clientes,
            lambda customer: rx.box(
                rx.text(customer["nome"], class_name="customer-table-cell customer-name"),
                rx.text(
                    rx.cond(customer["cpf"] != "", customer["cpf"], "—"),
                    class_name="customer-table-cell",
                ),
                rx.text(
                    rx.cond(customer["telefone"] != "", customer["telefone"], "—"),
                    class_name="customer-table-cell",
                ),
                rx.text(
                    rx.cond(customer["email"] != "", customer["email"], "—"),
                    class_name="customer-table-cell",
                ),
                rx.text(
                    rx.cond(customer["endereco"] != "", customer["endereco"], "—"),
                    class_name="customer-table-cell",
                ),
                rx.cond(
                    State.is_gestor,
                    rx.fragment(),
                    rx.hstack(
                        rx.button(
                            "Editar",
                            on_click=lambda: State.edit_customer(customer["id"]),
                            class_name="customer-edit-button",
                        ),
                        rx.button(
                            "Inativar",
                            on_click=lambda: State.deactivate_customer_by_id(
                                customer["id"]
                            ),
                            class_name="customer-remove-button",
                        ),
                        spacing="2",
                        justify="center",
                        width="100%",
                    ),
                ),
                class_name=rx.cond(
                    State.is_gestor,
                    "customer-table-row customer-table-row-readonly",
                    "customer-table-row",
                ),
            ),
        ),
        width="100%",
        class_name="content-card customers-card",
    )


def customer_address_fields(address) -> rx.Component:
    return rx.vstack(
        rx.text(
            rx.cond(address["id"] != "", "Endereço cadastrado", "Novo endereço"),
            class_name="muted",
        ),
        rx.input(
            placeholder="Logradouro",
            value=address["logradouro"],
            on_change=lambda value: State.set_customer_address_field(
                address["form_key"], "logradouro", value
            ),
        ),
        rx.input(
            placeholder="Número",
            value=address["numero"],
            on_change=lambda value: State.set_customer_address_field(
                address["form_key"], "numero", value
            ),
        ),
        rx.input(
            placeholder="Bairro",
            value=address["bairro"],
            on_change=lambda value: State.set_customer_address_field(
                address["form_key"], "bairro", value
            ),
        ),
        rx.input(
            placeholder="Cidade *",
            value=address["cidade"],
            on_change=lambda value: State.set_customer_address_field(
                address["form_key"], "cidade", value
            ),
        ),
        rx.input(
            placeholder="Estado *",
            value=address["estado"],
            on_change=lambda value: State.set_customer_address_field(
                address["form_key"], "estado", value
            ),
        ),
        rx.input(
            placeholder="CEP",
            value=address["cep"],
            on_change=lambda value: State.set_customer_address_field(
                address["form_key"], "cep", value
            ),
        ),
        rx.input(
            placeholder="Complemento",
            value=address["complemento"],
            on_change=lambda value: State.set_customer_address_field(
                address["form_key"], "complemento", value
            ),
        ),
        width="100%",
        spacing="2",
        class_name="customer-address-fields",
    )


def customer_form() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading(
                rx.cond(State.cliente_id != "", "Editar cliente", "Novo cliente"),
                size="5",
                class_name="customer-modal-title",
            ),
            rx.text("Nome", class_name="customer-form-label"),
            rx.input(
                placeholder="Nome",
                value=State.cliente_nome,
                on_change=lambda value: State.set_customer_field("cliente_nome", value),
                class_name="customer-personal-field",
            ),
            rx.text("CPF", class_name="customer-form-label"),
            rx.input(
                placeholder="CPF",
                value=State.cliente_cpf,
                on_change=lambda value: State.set_customer_field("cliente_cpf", value),
                max_length=11,
                type="text",
                class_name="customer-personal-field",
            ),
            rx.text("Data de nascimento", class_name="customer-form-label"),
            rx.input(
                placeholder="Data de nascimento (AAAA-MM-DD)",
                value=State.cliente_data_nascimento,
                on_change=lambda value: State.set_customer_field(
                    "cliente_data_nascimento", value
                ),
                class_name="customer-personal-field",
            ),
            rx.text("Telefone", class_name="customer-form-label"),
            rx.input(
                placeholder="Telefone",
                value=State.cliente_telefone,
                on_change=lambda value: State.set_customer_field(
                    "cliente_telefone", value
                ),
                type="tel",
                class_name="customer-personal-field",
            ),
            rx.text("E-mail", class_name="customer-form-label"),
            rx.input(
                placeholder="E-mail",
                value=State.cliente_email,
                on_change=lambda value: State.set_customer_field("cliente_email", value),
                type="email",
                class_name="customer-personal-field",
            ),
            rx.vstack(
                rx.heading("Endereços", size="4", class_name="customer-address-title"),
                rx.foreach(State.cliente_enderecos, customer_address_fields),
                rx.button("Adicionar endereço", on_click=State.add_customer_address, class_name="secondary-button"),
                width="100%",
                spacing="3",
            ),
            rx.hstack(
                rx.cond(
                    State.cliente_id != "",
                    rx.button("Salvar", on_click=State.update_customer, class_name="primary-button"),
                    rx.button("Cadastrar", on_click=State.create_customer, class_name="primary-button"),
                ),
                rx.button(
                    "Cancelar",
                    on_click=State.close_customer_form,
                    class_name="secondary-button",
                ),
                spacing="3",
                wrap="wrap",
                justify="start",
            ),
            feedback_message(),
            id="cliente-form",
            width="100%",
            spacing="3",
            class_name="form-modal-card customer-modal-card",
        ),
        class_name="form-modal-backdrop customer-modal-backdrop",
    )


def address_section() -> rx.Component:
    return rx.vstack(
        rx.heading("Enderecos", size="5"),
        rx.button("Carregar enderecos", on_click=State.load_addresses),
        rx.foreach(
            State.enderecos,
            lambda address: rx.text(
                address["id"],
                " - ",
                address["logradouro"],
                ", ",
                address["numero"],
                " - ",
                address["cidade"],
                "/",
                address["estado"],
            ),
        ),
        rx.cond(
            State.is_gestor,
            rx.fragment(),
            rx.vstack(
                rx.input(
                    placeholder="Logradouro",
                    value=State.endereco_logradouro,
                    on_change=lambda value: State.set_address_field(
                        "endereco_logradouro", value
                    ),
                ),
                rx.input(
                    placeholder="Numero",
                    value=State.endereco_numero,
                    on_change=lambda value: State.set_address_field(
                        "endereco_numero", value
                    ),
                ),
                rx.input(
                    placeholder="Bairro",
                    value=State.endereco_bairro,
                    on_change=lambda value: State.set_address_field(
                        "endereco_bairro", value
                    ),
                ),
                rx.input(
                    placeholder="Cidade",
                    value=State.endereco_cidade,
                    on_change=lambda value: State.set_address_field(
                        "endereco_cidade", value
                    ),
                ),
                rx.input(
                    placeholder="Estado",
                    value=State.endereco_estado,
                    on_change=lambda value: State.set_address_field(
                        "endereco_estado", value
                    ),
                ),
                rx.input(
                    placeholder="CEP",
                    value=State.endereco_cep,
                    on_change=lambda value: State.set_address_field(
                        "endereco_cep", value
                    ),
                ),
                rx.input(
                    placeholder="Complemento",
                    value=State.endereco_complemento,
                    on_change=lambda value: State.set_address_field(
                        "endereco_complemento", value
                    ),
                ),
                rx.button("Cadastrar endereco", on_click=State.create_address),
                class_name="content-card",
                width="100%",
                max_width="32rem",
            ),
        ),
        width="100%",
    )


def customers_page() -> rx.Component:
    return protected_layout(
        rx.vstack(
            rx.hstack(
                rx.heading("Clientes", size="7", class_name="sales-page-title"),
                rx.cond(
                    State.is_gestor,
                    rx.fragment(),
                    rx.button(
                        "Novo Cliente",
                        on_click=State.open_customer_form,
                        class_name="new-customer-button",
                    ),
                ),
                justify="between",
                align_items="center",
                width="100%",
            ),
            customer_list(),
            rx.cond(
                State.cliente_form_aberto,
                customer_form(),
                rx.fragment(),
            ),
            feedback_message(),
            width="100%",
            spacing="4",
        )
    )


def employee_list() -> rx.Component:
    return rx.box(
        rx.box(
            rx.text("Nome", class_name="employee-table-heading"),
            rx.text("CPF", class_name="employee-table-heading"),
            rx.text("Telefone", class_name="employee-table-heading"),
            rx.text("Salário", class_name="employee-table-heading"),
            rx.text("E-mail", class_name="employee-table-heading"),
            rx.text("Endereço", class_name="employee-table-heading"),
            rx.text("", class_name="employee-table-heading"),
            class_name="employee-table-head",
        ),
        rx.cond(
            State.funcionarios.length() > 0,
            rx.foreach(
                State.funcionarios,
                lambda employee: rx.box(
                    rx.text(employee["nome"], class_name="employee-table-cell"),
                    rx.text(employee["cpf"], class_name="employee-table-cell"),
                    rx.text(employee["telefone"], class_name="employee-table-cell"),
                    rx.text(employee["salario"], class_name="employee-table-cell"),
                    rx.text(
                        rx.cond(
                            employee["email"] != "",
                            employee["email"],
                            "—",
                        ),
                        class_name="employee-table-cell",
                    ),
                    rx.text(
                        rx.cond(
                            employee["endereco"] != "",
                            employee["endereco"],
                            "",
                        ),
                        class_name="employee-table-cell",
                    ),
                    rx.hstack(
                        rx.button(
                            "Editar",
                            on_click=lambda: State.edit_employee(employee["id"]),
                            class_name="employee-edit-button",
                        ),
                        rx.button(
                            rx.cond(
                                employee["situacao"] == "ativo",
                                "Inativar",
                                "Reativar",
                            ),
                            on_click=lambda: State.request_deactivate_employee_by_id(
                                employee["id"]
                            ),
                            class_name=rx.cond(
                                employee["situacao"] == "ativo",
                                "employee-remove-button",
                                "employee-activate-button",
                            ),
                        ),
                        spacing="2",
                    ),
                    class_name="employee-table-row",
                ),
            ),
            rx.text("Nenhum funcionário cadastrado.", class_name="muted"),
        ),
        class_name="content-card employee-card",
        width="100%",
    )


def employee_form() -> rx.Component:
    return rx.box(
      rx.vstack(
        rx.heading(
            rx.cond(State.funcionario_editando, "Editar funcionário", "Novo funcionário"),
            size="6",
            class_name="employee-modal-title",
        ),
        rx.text("Nome completo", class_name="employee-form-label"),
        rx.input(
            value=State.funcionario_nome,
            on_change=lambda value: State.set_employee_field(
                "funcionario_nome", value
            ),
        ),
        rx.text("CPF", class_name="employee-form-label"),
        rx.input(
            value=State.funcionario_cpf,
            on_change=lambda value: State.set_employee_field(
                "funcionario_cpf", value
            ),
            max_length=11,
            type="text",
        ),
        rx.text("Telefone", class_name="employee-form-label"),
        rx.input(
            value=State.funcionario_telefone,
            on_change=lambda value: State.set_employee_field(
                "funcionario_telefone", value
            ),
        ),
        rx.text("E-mail", class_name="employee-form-label"),
        rx.input(
            value=State.funcionario_email,
            on_change=lambda value: State.set_employee_field(
                "funcionario_email", value
            ),
        ),
        rx.text("Endereço", class_name="employee-form-label"),
        rx.input(
            value=State.funcionario_endereco,
            on_change=lambda value: State.set_employee_field(
                "funcionario_endereco", value
            ),
        ),
        rx.text("Salário (R$)", class_name="employee-form-label"),
        rx.input(
            type="number",
            value=State.funcionario_salario,
            on_change=lambda value: State.set_employee_field(
                "funcionario_salario", value
            ),
        ),
        rx.cond(
            State.funcionario_editando,
            rx.fragment(),
            rx.vstack(
                rx.text(
                    "Login inicial",
                    class_name="employee-form-label initial-access-label",
                ),
                rx.input(
                    value=State.funcionario_login,
                    on_change=lambda value: State.set_employee_field(
                        "funcionario_login", value
                    ),
                    class_name="initial-access-field",
                ),
                rx.text(
                    "Senha inicial",
                    class_name="employee-form-label initial-access-label",
                ),
                rx.box(
                    rx.input(
                        value=State.funcionario_senha_inicial,
                        on_change=State.set_initial_employee_password,
                        type=rx.cond(
                            State.funcionario_senha_inicial_visivel,
                            "text",
                            "password",
                        ),
                        class_name="initial-access-field initial-password-field",
                    ),
                    rx.button(
                        rx.cond(
                            State.funcionario_senha_inicial_visivel,
                            "Ocultar",
                            "Mostrar",
                        ),
                        on_click=State.toggle_initial_employee_password,
                        type="button",
                        class_name="initial-password-toggle",
                    ),
                    class_name="initial-password-wrapper",
                ),
                width="100%",
                spacing="2",
            ),
        ),
        rx.hstack(
            rx.button(
                "Salvar",
                on_click=State.save_employee,
                class_name="primary-button",
            ),
            rx.button(
                "Cancelar",
                on_click=State.close_employee_modal,
                class_name="secondary-button",
            ),
            spacing="3",
            width="100%",
            justify="start",
            margin_top="0.35rem",
        ),
        width="100%",
        spacing="3",
        class_name="employee-modal",
      ),
      class_name="employee-modal-backdrop",
    )


def employee_remove_modal() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading(
                rx.cond(
                    State.funcionario_ativo,
                    "Inativar funcionário?",
                    "Reativar funcionário?",
                ),
                size="5",
                class_name="employee-remove-title",
            ),
            rx.cond(
                State.funcionario_ativo,
                rx.text(
                    "Tem certeza que deseja inativar ",
                    rx.text(State.funcionario_nome, as_="span", class_name="strong"),
                    "? Essa ação não pode ser desfeita.",
                    class_name="employee-remove-message",
                ),
                rx.text(
                    "Tem certeza que deseja reativar ",
                    rx.text(State.funcionario_nome, as_="span", class_name="strong"),
                    "?",
                    class_name="employee-remove-message",
                ),
            ),
            rx.hstack(
                rx.button(
                    rx.cond(
                        State.funcionario_ativo,
                        "Inativar",
                        "Reativar",
                    ),
                    on_click=State.deactivate_employee,
                    class_name=rx.cond(
                        State.funcionario_ativo,
                        "employee-confirm-remove-button",
                        "employee-activate-button",
                    ),
                ),
                rx.button(
                    "Cancelar",
                    on_click=State.cancel_deactivate_employee,
                    class_name="secondary-button",
                ),
                spacing="2",
            ),
            align_items="center",
            width="100%",
            spacing="3",
        ),
        class_name="employee-remove-modal employee-modal-backdrop",
    )


def employees_page() -> rx.Component:
    return protected_layout(
        rx.vstack(
            rx.hstack(
                rx.button(
                    "Adicionar funcionário",
                    on_click=State.open_new_employee,
                    class_name="new-employee-button",
                ),
                justify="start",
                align_items="center",
                width="100%",
            ),
            employee_list(),
            rx.cond(
                State.funcionario_modal_aberto,
                employee_form(),
                rx.fragment(),
            ),
            rx.cond(
                State.confirmando_inativacao,
                employee_remove_modal(),
                rx.fragment(),
            ),
            feedback_message(),
            width="100%",
            spacing="4",
        )
    )


def supplier_list() -> rx.Component:
    return rx.vstack(
        rx.box(
            section_heading(
                "Fornecedores",
                "Parceiros cadastrados e prazo de entrega.",
                "supplier-section-heading",
            ),
            rx.box(
                rx.text("Fornecedor", class_name="supplier-table-heading"),
                rx.text("CNPJ", class_name="supplier-table-heading"),
                rx.text("Telefone", class_name="supplier-table-heading"),
                rx.text("Prazo", class_name="supplier-table-heading"),
                rx.text("Ações", class_name="supplier-table-heading"),
                class_name="supplier-table-head",
            ),
            rx.foreach(
                State.fornecedores,
                lambda supplier: rx.box(
                    rx.text(supplier["nome"], class_name="table-cell strong"),
                    rx.text(supplier["cnpj"], class_name="table-cell"),
                    rx.text(supplier["telefone"], class_name="table-cell"),
                    rx.text(supplier["prazo_entrega"], class_name="supplier-deadline"),
                    rx.hstack(
                        rx.button(
                            "Editar",
                            on_click=lambda: State.edit_supplier(supplier["id"]),
                            class_name="employee-edit-button",
                        ),
                        rx.button(
                            "Remover",
                            on_click=lambda: State.request_delete_supplier_by_id(
                                supplier["id"]
                            ),
                            class_name="employee-remove-button supplier-action-button",
                        ),
                        spacing="2",
                        justify="center",
                    ),
                    class_name="supplier-table-row",
                    width="100%",
                ),
            ),
            class_name="content-card supplier-list-card",
            width="100%",
        ),
        width="100%",
        spacing="0",
        class_name="supplier-list",
    )


def supplier_form() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading(
                rx.cond(
                    State.fornecedor_editando,
                    "Editar fornecedor",
                    "Novo fornecedor",
                ),
                size="6",
                class_name="supplier-modal-title",
            ),
            rx.text("Nome", class_name="supplier-form-label"),
            rx.input(
                value=State.fornecedor_nome,
                on_change=lambda value: State.set_supplier_field(
                    "fornecedor_nome", value
                ),
            ),
            rx.text("CNPJ", class_name="supplier-form-label"),
            rx.input(
                value=State.fornecedor_cnpj,
                on_change=lambda value: State.set_supplier_field(
                    "fornecedor_cnpj", value
                ),
            ),
            rx.text("Endereço", class_name="supplier-form-label"),
            rx.input(
                value=State.fornecedor_endereco,
                on_change=lambda value: State.set_supplier_field(
                    "fornecedor_endereco", value
                ),
            ),
            rx.text("E-mail", class_name="supplier-form-label"),
            rx.input(
                type="email",
                value=State.fornecedor_email,
                on_change=lambda value: State.set_supplier_field(
                    "fornecedor_email", value
                ),
            ),
            rx.text("Telefone de contato", class_name="supplier-form-label"),
            rx.input(
                value=State.fornecedor_telefone,
                on_change=lambda value: State.set_supplier_field(
                    "fornecedor_telefone", value
                ),
            ),
            rx.text("Prazo de entrega", class_name="supplier-form-label"),
            rx.input(
                value=State.fornecedor_prazo_entrega,
                on_change=lambda value: State.set_supplier_field(
                    "fornecedor_prazo_entrega", value
                ),
            ),
            rx.hstack(
                rx.button(
                    "Salvar",
                    on_click=State.save_supplier,
                    class_name="primary-button",
                ),
                rx.button(
                    "Cancelar",
                    on_click=State.close_supplier_modal,
                    class_name="secondary-button",
                ),
                spacing="2",
            ),
            width="100%",
            spacing="3",
            align_items="stretch",
            class_name="supplier-modal",
        ),
        class_name="supplier-modal-backdrop",
    )


def supplier_remove_modal() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading(
                "Remover fornecedor?",
                size="5",
                class_name="supplier-remove-title",
            ),
            rx.text(
                "Tem certeza que deseja remover ",
                rx.text(
                    State.fornecedor_nome,
                    as_="span",
                    class_name="strong",
                ),
                "? Essa ação não pode ser desfeita.",
                class_name="supplier-remove-message",
            ),
            rx.hstack(
                rx.button(
                    "Remover",
                    on_click=State.delete_supplier,
                    class_name="employee-confirm-remove-button",
                ),
                rx.button(
                    "Cancelar",
                    on_click=State.cancel_delete_supplier,
                    class_name="secondary-button",
                ),
                spacing="2",
            ),
            align_items="center",
            width="100%",
            spacing="3",
        ),
        class_name="supplier-remove-modal supplier-modal-backdrop",
    )


def suppliers_page() -> rx.Component:
    return protected_layout(
        rx.cond(
            State.is_gestor,
            rx.vstack(
                rx.hstack(
                    rx.button(
                        "Adicionar fornecedor",
                        on_click=State.open_new_supplier,
                        class_name="new-supplier-button",
                    ),
                    justify="end",
                    align_items="center",
                    width="100%",
                ),
                supplier_list(),
                rx.cond(
                    State.fornecedor_modal_aberto,
                    supplier_form(),
                    rx.fragment(),
                ),
                rx.cond(
                    State.confirmando_remocao_fornecedor,
                    supplier_remove_modal(),
                    rx.fragment(),
                ),
                feedback_message(),
                width="100%",
                spacing="4",
            ),
            rx.text(FORBIDDEN_MESSAGE),
        )
    )


def account_page() -> rx.Component:
    return protected_layout(
        rx.cond(
            State.is_gestor,
            rx.text(FORBIDDEN_MESSAGE),
            rx.box(
                rx.vstack(
                    page_header("Minha conta", "Atualize suas credenciais de acesso."),
                    rx.text(
                        "Usuário: ",
                        State.login,
                        class_name="account-username",
                    ),
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
                    rx.hstack(
                        rx.button("Salvar senha", on_click=State.update_password),
                        rx.button(
                            "Cancelar",
                            on_click=State.cancel_account_form,
                            class_name="secondary-button",
                        ),
                        spacing="3",
                    ),
                    feedback_message(),
                    width="100%",
                    spacing="3",
                    class_name="form-modal-card",
                ),
                class_name="form-modal-backdrop",
            ),
        ),
    )


def product_list() -> rx.Component:
    return rx.box(
        rx.box(
            rx.text("Produto", class_name="product-table-heading"),
            rx.text("Categoria", class_name="product-table-heading"),
            rx.text("Preço", class_name="product-table-heading"),
            rx.text("Controlado", class_name="product-table-heading"),
            rx.text("", class_name="product-table-heading"),
            class_name="product-table-head",
        ),
        rx.cond(
            State.produtos.length() > 0,
            rx.foreach(
                State.produtos,
                lambda product: rx.box(
                    rx.text(product["nome"], class_name="product-table-cell"),
                    rx.text(product["categoria"], class_name="product-table-cell"),
                    rx.text(product["preco"], class_name="product-table-cell"),
                    rx.cond(
                        product["controlado"] == "Sim",
                        status_badge("Sim", "info"),
                        rx.text("—", class_name="product-table-cell"),
                    ),
                    rx.hstack(
                        rx.link(
                            "Editar",
                            href="#produto-form",
                            on_click=lambda: State.edit_product(product["id"]),
                            class_name="product-edit-button",
                        ),
                        rx.button(
                            "Remover",
                            on_click=lambda: State.deactivate_product_by_id(
                                product["id"]
                            ),
                            class_name="product-remove-button",
                        ),
                        spacing="2",
                    ),
                    class_name="product-table-row",
                ),
            ),
            rx.text("Nenhum produto ativo cadastrado.", class_name="muted"),
        ),
        class_name="content-card products-card",
        width="100%",
    )


def product_form() -> rx.Component:
    return rx.box(
    rx.vstack(
        rx.heading(
            rx.cond(State.produto_editando, "Editar produto", "Novo produto"),
            size="6",
            class_name="product-modal-title",
        ),
        rx.text("Nome", class_name="product-form-label"),
        rx.input(
            value=State.produto_nome,
            on_change=lambda value: State.set_product_field("produto_nome", value),
        ),
        rx.text("Categoria", class_name="product-form-label"),
        rx.select.root(
            rx.select.trigger(placeholder="Selecione uma categoria", width="100%"),
            rx.select.content(
                rx.foreach(
                    State.categorias,
                    lambda category: rx.select.item(
                        category["nome"],
                        value=category["id"],
                    ),
                ),
            ),
            value=State.produto_categoria_id,
            on_change=lambda value: State.set_product_field(
                "produto_categoria_id", value
            ),
            width="100%",
        ),
        rx.text("Preço (R$)", class_name="product-form-label"),
        rx.input(
            value=State.produto_preco,
            on_change=lambda value: State.set_product_field(
                "produto_preco", value
            ),
        ),
        rx.text("Estoque", class_name="product-form-label"),
        rx.input(
            value=State.produto_quantidade,
            on_change=lambda value: State.set_product_field(
                "produto_quantidade", value
            ),
        ),
        rx.text("Estoque mínimo", class_name="product-form-label"),
        rx.input(
            value=State.produto_estoque_minimo,
            on_change=lambda value: State.set_product_field(
                "produto_estoque_minimo", value
            ),
        ),
        rx.hstack(
            rx.checkbox(
                checked=State.produto_controlado,
                on_change=State.set_product_controlled,
                class_name="product-controlled-checkbox",
                aria_label="Medicamento controlado",
            ),
            rx.text(
                "Medicamento controlado (exige receita)",
                class_name="product-controlled-label",
            ),
            align_items="center",
            spacing="2",
        ),
        rx.hstack(
            rx.button(
                "Salvar",
                on_click=State.save_product,
                class_name="primary-button",
            ),
            rx.button(
                "Cancelar",
                on_click=State.close_product_modal,
                class_name="secondary-button",
            ),
            spacing="2",
        ),
        width="100%",
        spacing="3",
        class_name="product-modal",
    )
    ,
    class_name="product-modal-backdrop",
    )


def products_page() -> rx.Component:
    return protected_layout(
        rx.vstack(
            rx.hstack(
                rx.heading("Produtos", size="7", class_name="products-page-title"),
                rx.cond(
                    State.is_gestor,
                    rx.button(
                        "Novo produto",
                        on_click=State.open_new_product,
                        class_name="new-product-button",
                    ),
                    rx.fragment(),
                ),
                justify="between",
                align_items="center",
                width="100%",
            ),
            product_list(),
            rx.cond(
                State.produto_modal_aberto,
                product_form(),
                rx.fragment(),
            ),
            feedback_message(),
            width="100%",
            spacing="4",
        )
    )


def stock_page() -> rx.Component:
    return protected_layout(
        rx.vstack(
            rx.box(
                rx.text("Produto", class_name="stock-table-heading"),
                rx.text("Categoria", class_name="stock-table-heading"),
                rx.text("Estoque", class_name="stock-table-heading"),
                rx.text("Mínimo", class_name="stock-table-heading"),
                rx.text("Status", class_name="stock-table-heading"),
                class_name="stock-table-head",
            ),
            rx.foreach(
                State.produtos,
                lambda product: rx.box(
                    rx.text(product["nome"], class_name="stock-table-cell stock-product"),
                    rx.text(product["categoria"], class_name="stock-table-cell"),
                    rx.text(
                        product["estoque"],
                        class_name=rx.cond(
                            product["situacao"] == "repor",
                            "stock-table-cell stock-critical",
                            "stock-table-cell",
                        ),
                    ),
                    rx.text(product["minimo"], class_name="stock-table-cell"),
                    rx.text(
                        rx.cond(product["situacao"] == "repor", "Repor", "Normal"),
                        class_name=rx.cond(
                            product["situacao"] == "repor",
                            "stock-status stock-status-danger",
                            "stock-status stock-status-success",
                        ),
                    ),
                    class_name="stock-table-row",
                ),
            ),
            feedback_message(),
            class_name="content-card stock-card",
            width="100%",
            spacing="0",
        )
    )


def sale_form() -> rx.Component:
    return rx.vstack(
        page_header("Novo atendimento", "Registre uma venda e acompanhe o estoque em tempo real."),
        rx.input(
            placeholder="Código do produto",
            value=State.venda_produto_id,
            on_change=lambda value: State.set_sale_field("venda_produto_id", value),
        ),
        rx.input(
            placeholder="Quantidade",
            value=State.venda_quantidade,
            on_change=lambda value: State.set_sale_field("venda_quantidade", value),
        ),
        rx.button("Adicionar item", on_click=State.add_sale_item),
        rx.foreach(
            State.venda_itens,
            lambda item: rx.text(
                item["nome"],
                " - Quantidade: ",
                item["quantidade"],
            ),
        ),
        rx.text(
            "Valor total: ",
            rx.text(
                State.venda_valor_total_brl,
                as_="span",
                class_name="strong",
            ),
            class_name="sale-total",
        ),
        rx.input(
            placeholder="ID do cliente (opcional para produtos comuns)",
            value=State.venda_cliente_id,
            on_change=lambda value: State.set_sale_field("venda_cliente_id", value),
        ),
        rx.select(
            ["presencial", "online"],
            value=State.venda_canal,
            on_change=lambda value: State.set_sale_field("venda_canal", value),
        ),
        rx.select(
            ["dinheiro", "cartão", "pix"],
            value=State.venda_pagamento,
            on_change=lambda value: State.set_sale_field("venda_pagamento", value),
        ),
        rx.input(
            placeholder="Número da receita (se necessário)",
            value=State.venda_receita,
            on_change=lambda value: State.set_sale_field("venda_receita", value),
        ),
        rx.hstack(
            rx.button("Confirmar venda", on_click=State.create_sale),
            rx.button(
                "Cancelar",
                on_click=State.cancel_sale,
                class_name="secondary-button",
            ),
            spacing="3",
        ),
        feedback_message(),
        width="100%",
        class_name="content-card attendance-card",
        max_width="25.25rem",
    )


def sales_history() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading("Vendas", size="7", class_name="sales-page-title"),
            rx.cond(
                State.is_gestor,
                rx.fragment(),
                rx.link(
                    "Nova venda",
                    href="/atendimento",
                    class_name="new-sale-button",
                ),
            ),
            justify="between",
            align_items="center",
            width="100%",
        ),
        rx.box(
            rx.text("Venda", class_name="table-heading"),
            rx.text("Data", class_name="table-heading"),
            rx.text("Cliente", class_name="table-heading"),
            rx.text("Produtos", class_name="table-heading"),
            rx.text("Canal", class_name="table-heading"),
            rx.text("Atendente", class_name="table-heading"),
            rx.text("Total", class_name="table-heading"),
            class_name="sales-table-head",
        ),
        rx.foreach(
            State.vendas,
            lambda sale: rx.box(
                rx.text(sale["id"], class_name="table-cell strong"),
                rx.text(sale["data"], class_name="table-cell"),
                rx.text(sale["cliente"], class_name="table-cell"),
                rx.text(sale["produtos"], class_name="table-cell products-cell"),
                channel_badge(sale["canal"]),
                rx.text(sale["atendente"], class_name="table-cell"),
                rx.text("R$ ", sale["total"], class_name="table-cell strong"),
                class_name="sales-table-row",
            ),
        ),
        feedback_message(),
        class_name="content-card",
        width="100%",
    )


def attendance_page() -> rx.Component:
    return protected_layout(
        rx.cond(
            State.is_gestor,
            rx.text(FORBIDDEN_MESSAGE),
            rx.vstack(
                sale_form(),
                width="100%",
                spacing="4",
                class_name="attendance-backdrop",
            ),
        )
    )


def sales_page() -> rx.Component:
    return protected_layout(
        rx.vstack(
            sales_history(),
            width="100%",
            spacing="4",
        )
    )


GLOBAL_STYLE = {
    "@keyframes feedback-disappear": {
        "0%, 80%": {
            "opacity": "1",
            "visibility": "visible",
        },
        "100%": {
            "opacity": "0",
            "visibility": "hidden",
        },
    },
    "body": {
        "margin": "0",
        "background": "radial-gradient(900px 500px at 0% 0%, rgba(20,184,166,0.22), transparent 60%), linear-gradient(160deg, #020808, #04110f)",
        "background_attachment": "fixed",
        "color": "#ffffff",
        "font_family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        "min_height": "100vh",
    },
    "a": {
        "color": "#5eead4",
        "text_decoration": "none",
        "font_size": "0.875rem",
        "font_weight": "600",
    },
    "button": {
        "font_family": "inherit",
        "cursor": "pointer",
        "transition": "transform 0.15s ease, opacity 0.15s ease",
        "background": "#0b8277",
        "color": "#ffffff",
        "border": "1px solid #0b8277",
        "border_radius": "10px",
        "font_weight": "700",
        "box_shadow": "0 0 16px rgba(20,184,166,0.35)",
    },
    "input, textarea, select": {
        "border": "1px solid #17332f",
        "border_radius": "10px",
        "background": "rgba(255,255,255,0.04)",
        "color": "#ffffff",
    },
    "input::placeholder, textarea::placeholder": {
        "color": "#ffffff",
        "opacity": "1",
    },
    ".rt-TextFieldRoot input": {
        "color": "#ffffff",
    },
    ".rt-SelectTrigger, .rt-SelectTrigger *": {
        "color": "#ffffff",
    },
    ".rt-SelectContent, .rt-SelectContent *": {
        "color": "#ffffff",
    },
    ".login-page": {
        "min_height": "100vh",
        "display": "flex",
        "align_items": "stretch",
        "justify_content": "space-between",
        "padding": "clamp(2rem, 7vw, 5rem) clamp(2rem, 4.5vw, 4rem)",
        "gap": "clamp(2rem, 8vw, 8rem)",
        "background": "radial-gradient(520px 360px at 5% 85%, rgba(13,148,136,0.42), transparent 70%), radial-gradient(520px 420px at 95% 0%, rgba(14,116,144,0.55), transparent 70%), #020808",
        "position": "relative",
        "overflow": "hidden",
        "flex_wrap": "wrap",
    },
    ".login-decoration": {
        "position": "fixed",
        "inset": "0",
        "overflow": "hidden",
        "pointer_events": "none",
    },
    ".login-blob": {
        "position": "absolute",
        "border_radius": "999px",
        "filter": "blur(60px)",
        "opacity": "0.55",
    },
    ".login-blob-left": {
        "width": "26rem",
        "height": "26rem",
        "left": "-9rem",
        "bottom": "-8rem",
        "background": "radial-gradient(circle, #0d9488, #075e54 70%)",
    },
    ".login-blob-right": {
        "width": "16rem",
        "height": "16rem",
        "right": "-5rem",
        "top": "-4rem",
        "background": "radial-gradient(circle, #22d3ee, #155e75 70%)",
    },
    ".login-hero-copy": {
        "position": "relative",
        "z_index": "1",
        "flex": "1 1 32rem",
        "max_width": "45rem",
        "align_self": "center",
        "display": "flex",
        "flex_direction": "column",
        "justify_content": "center",
        "gap": "1.25rem",
    },
    ".login-brand": {"gap": "0.65rem", "margin_bottom": "2.5rem"},
    ".login-brand-neon": {
        "color": "#f8fafc",
        "font_size": "1.9rem",
        "font_weight": "700",
        "letter_spacing": "-0.04em",
    },
    ".login-brand-accent": {"color": "#2dd4bf"},
    ".login-logo-mark": {
        "width": "3.5rem",
        "height": "3.5rem",
        "display": "flex",
        "position": "relative",
        "border": "2px solid #08d9dc",
        "border_radius": "0.9rem",
        "background": "rgba(5,22,22,0.9)",
        "box_shadow": "0 0 12px rgba(34,211,238,0.9), 0 0 32px rgba(20,184,166,0.45)",
    },
    ".login-logo-plus": {
        "position": "absolute",
        "left": "0.55rem",
        "top": "0.72rem",
        "width": "1.7rem",
        "height": "1.7rem",
    },
    ".login-logo-plus-horizontal": {
        "position": "absolute",
        "left": "0",
        "top": "0.55rem",
        "width": "1.7rem",
        "height": "0.58rem",
        "border_radius": "0.2rem",
        "background": "#ffffff",
    },
    ".login-logo-plus-vertical": {
        "position": "absolute",
        "left": "0.56rem",
        "top": "0",
        "width": "0.58rem",
        "height": "1.7rem",
        "border_radius": "0.2rem",
        "background": "#ffffff",
    },
    ".login-logo-bars": {
        "position": "absolute",
        "right": "0.42rem",
        "bottom": "0.48rem",
        "height": "0.9rem",
    },
    ".login-logo-bar": {
        "width": "0.22rem",
        "border_radius": "0.2rem",
        "background": "#18d8d1",
        "box_shadow": "0 0 6px rgba(34,211,238,0.9)",
    },
    ".login-logo-bar-short": {"height": "0.32rem"},
    ".login-logo-bar-medium": {"height": "0.58rem"},
    ".login-logo-bar-tall": {"height": "0.86rem"},
    ".login-hero-title": {
        "color": "#f8fafc",
        "font_size": "clamp(2.5rem, 4vw, 3.6rem)",
        "line_height": "1.08",
        "letter_spacing": "-0.035em",
    },
    ".neon-gradient-text": {
        "background": "linear-gradient(90deg, #34d399, #2dd4bf 50%, #22d3ee)",
        "background_clip": "text",
        "color": "transparent",
    },
    ".login-hero-description": {
        "color": "#9fb8b4",
        "font_size": "0.95rem",
        "line_height": "1.5",
        "max_width": "29rem",
    },
    ".login-feature-pills": {"gap": "0.75rem", "width": "100%"},
    ".feature-pill": {
        "padding": "0.55rem 0.95rem",
        "border_radius": "999px",
        "font_size": "0.78rem",
        "line_height": "1",
        "border": "1px solid",
        "white_space": "nowrap",
        "color": "#ffffff",
    },
    ".feature-pill-dot": {
        "width": "0.65rem",
        "height": "0.65rem",
        "border_radius": "999px",
        "flex_shrink": "0",
        "box_shadow": "0 0 8px currentColor",
    },
    ".feature-pill-green": {
        "color": "#ffffff",
        "background": "rgba(52,211,153,0.12)",
        "border_color": "rgba(52,211,153,0.5)",
    },
    ".feature-pill-dot-green": {"background": "#34d399", "color": "#34d399"},
    ".feature-pill-cyan": {
        "color": "#ffffff",
        "background": "rgba(34,211,238,0.12)",
        "border_color": "rgba(34,211,238,0.5)",
    },
    ".feature-pill-dot-cyan": {"background": "#22d3ee", "color": "#22d3ee"},
    ".feature-pill-purple": {
        "color": "#ffffff",
        "background": "rgba(167,139,250,0.12)",
        "border_color": "rgba(167,139,250,0.5)",
    },
    ".feature-pill-dot-purple": {"background": "#a78bfa", "color": "#a78bfa"},
    ".feature-pill-yellow": {
        "color": "#ffffff",
        "background": "rgba(250,204,21,0.08)",
        "border_color": "rgba(250,204,21,0.55)",
    },
    ".feature-pill-dot-yellow": {"background": "#facc15", "color": "#facc15"},
    ".feature-pill-blue": {
        "color": "#ffffff",
        "background": "rgba(91,155,255,0.12)",
        "border_color": "rgba(91,155,255,0.5)",
    },
    ".feature-pill-dot-blue": {"background": "#5b9bff", "color": "#5b9bff"},
    ".login-panel": {
        "width": "100%",
        "max_width": "24rem",
        "padding": "2.5rem 2.5rem 1.8rem",
        "border": "1px solid rgba(45,212,191,0.5)",
        "border_radius": "1.4rem",
        "background": "rgba(6,22,20,0.72)",
        "box_shadow": "0 0 0 1px rgba(34,211,238,0.12), 0 0 60px rgba(20,184,166,0.3), 0 30px 60px -20px rgba(0,0,0,0.8)",
        "backdrop_filter": "blur(18px)",
        "position": "relative",
        "z_index": "1",
        "align_self": "center",
    },
    ".login-title": {
        "color": "#f8fafc",
        "font_size": "1.8rem",
        "margin_bottom": "0",
    },
    ".brand-mark, .nav-brand": {
        "color": "#2dd4bf",
        "font_weight": "800",
        "font_size": "0.75rem",
        "letter_spacing": "-0.03em",
    },
    ".brand-mark": {"font_size": "1.1rem"},
    ".login-subtitle, .page-description, .muted": {
        "color": "#8fb0ab",
        "font_size": "0.72rem",
    },
    ".role-grid": {"gap": "0.65rem"},
    ".role-card": {
        "flex": "1",
        "min_width": "0",
        "min_height": "5.35rem",
        "padding": "0.55rem",
        "border": "1px solid #214540",
        "border_radius": "0.85rem",
        "background": "rgba(255,255,255,0.03)",
        "color": "#ffffff",
        "border_color": "#d6e6dc",
        "display": "flex",
        "flex_direction": "column",
        "align_items": "center",
        "justify_content": "center",
        "gap": "0.25rem",
        "white_space": "nowrap",
    },
    ".role-card-active": {
        "border": "1px solid #14b8a6",
        "background": "rgba(13,148,136,0.18)",
        "box_shadow": "0 0 22px rgba(20,184,166,0.28)",
    },
    ".role-card-active .role-icon": {
        "background": "rgba(20,184,166,0.22)",
        "color": "#2dd4bf",
    },
    ".role-icon": {
        "width": "2.4rem",
        "height": "2.4rem",
        "border_radius": "999px",
        "background": "rgba(255,255,255,0.06)",
        "display": "flex",
        "align_items": "center",
        "justify_content": "center",
        "font_weight": "800",
    },
    ".field-label": {
        "color": "#9fb8b4",
        "font_size": "0.65rem",
        "font_weight": "500",
        "margin_top": "0.25rem",
        "margin_bottom": "-0.15rem",
    },
    ".login-panel input": {
        "border_radius": "14px",
        "border": "0",
        "background": "transparent",
        "box_shadow": "none",
        "outline": "none",
        "appearance": "none",
        "background_clip": "padding-box",
        "padding": "0.4rem 0.75rem 0.7rem",
        "font_size": "0.68rem",
        "height": "2.25rem",
        "text_align": "left",
        "line_height": "1.25rem",
    },
    ".login-panel .rt-TextFieldRoot": {
        "border": "1px solid #214540",
        "border_radius": "14px",
        "background": "#102522",
        "box_shadow": "none",
        "outline": "none",
        "overflow": "hidden",
    },
    ".login-panel .rt-TextFieldRoot:focus-within": {
        "border_color": "#214540",
        "box_shadow": "0 0 0 1px rgba(20,184,166,0.2)",
    },
    ".login-panel input:focus": {
        "border": "0",
        "box_shadow": "none",
        "outline": "none",
    },
    ".login-panel input::placeholder": {
        "color": "#ffffff",
        "opacity": "1",
    },
    ".password-field": {
        "position": "relative",
        "width": "100%",
    },
    ".password-field input": {
        "padding_right": "4.5rem",
    },
    ".show-password": {
        "position": "absolute",
        "right": "0.35rem",
        "top": "50%",
        "transform": "translateY(-50%)",
        "padding": "0.15rem 0.3rem",
        "min_height": "0",
        "height": "auto",
        "border": "none",
        "background": "transparent",
        "box_shadow": "none",
        "color": "#5eead4",
        "font_size": "0.62rem",
        "font_weight": "700",
    },
    ".primary-button": {
        "background": "linear-gradient(90deg, #0b8277, #0e7490)",
        "color": "#ffffff",
        "border_radius": "10px",
        "font_weight": "700",
        "padding": "0.7rem 1rem",
    },
    ".login-submit": {
        "margin_top": "0.6rem",
        "height": "2.45rem",
    },
    ".forgot-password": {
        "align_self": "end",
        "color": "#5eead4",
        "font_size": "0.68rem",
        "text_decoration": "underline",
        "cursor": "pointer",
    },
    ".login-panel-line": {
        "height": "2px",
        "width": "100%",
        "margin_top": "0.65rem",
        "background": "linear-gradient(90deg, #14b8a6, #22d3ee 55%, #facc15)",
        "box_shadow": "0 0 8px rgba(34,211,238,0.5)",
    },
    ".feedback": {
        "padding": "0.75rem 1rem",
        "border_radius": "10px",
        "font_size": "0.85rem",
        "width": "100%",
        "box_sizing": "border-box",
        "text_align": "left",
        "animation": "feedback-disappear 5s forwards",
    },
    ".feedback-error": {
        "background": "#a91d2d",
        "color": "#ffffff",
        "border": "1px solid #ef4444",
        "box_shadow": "0 8px 20px rgba(169,29,45,0.28)",
    },
    ".feedback-error *": {
        "color": "#ffffff",
    },
    ".feedback-success": {
        "background": "#0b8277",
        "color": "#ffffff",
        "border": "1px solid #14b8a6",
    },
    ".feedback-success *": {
        "color": "#ffffff",
    },
    ".app-shell": {
        "width": "100%",
        "min_height": "100vh",
        "background": "radial-gradient(900px 500px at 0% 0%, rgba(20,184,166,0.22), transparent 60%), linear-gradient(160deg, #020808, #04110f)",
        "padding_left": "15rem",
    },
    ".topbar": {
        "position": "fixed",
        "left": "0",
        "top": "0",
        "bottom": "0",
        "width": "15rem",
        "padding": "2rem 1.25rem",
        "background": "rgba(6,22,20,0.82)",
        "border_right": "1px solid #17332f",
        "backdrop_filter": "blur(12px)",
        "overflow_x": "hidden",
        "gap": "0.25rem",
        "z_index": "10",
    },
    ".nav-links": {"gap": "0.8rem", "align_items": "center"},
    ".nav-tabs": {
        "gap": "0.35rem",
        "align_items": "stretch",
        "wrap": "nowrap",
        "flex_direction": "column",
        "width": "100%",
    },
    ".nav-menu": {"margin_top": "0.5rem"},
    ".nav-tab": {
        "padding": "0.45rem 0.75rem",
        "border": "1px solid transparent",
        "border_radius": "999px",
        "font_size": "0.8rem",
        "font_weight": "600",
        "white_space": "nowrap",
        "width": "100%",
        "text_align": "left",
        "transition": "background 0.08s ease-out, border-color 0.08s ease-out, color 0.08s ease-out, transform 0.08s ease-out",
    },
    ".nav-tab-active": {
        "background": "rgba(20,184,166,0.16)",
        "border_color": "#14b8a6",
        "color": "#ffffff",
        "transform": "scale(1.02)",
    },
    ".nav-context": {
        "color": "#5c7568",
        "font_size": "0.68rem",
        "text_transform": "uppercase",
        "letter_spacing": "0.08em",
    },
    ".nav-user-title": {
        "color": "#ffffff",
        "font_size": "0.95rem",
        "font_weight": "800",
        "width": "auto",
        "text_align": "center",
    },
    ".nav-user": {"color": "#5c7568", "font_size": "0.8rem"},
    ".logout-button": {
        "background": "#0b8277",
        "color": "#ffffff",
        "border": "1px solid #0f6e56",
        "border_radius": "10px",
        "padding": "0.5rem 1rem",
        "font_weight": "700",
    },
    ".page-content": {
        "width": "100%",
        "max_width": "1400px",
        "margin": "0 auto",
        "padding": "clamp(1rem, 4vw, 2rem)",
    },
    ".page-title": {"color": "#0a4e3d", "margin_bottom": "0.15rem"},
    ".supplier-page-title": {"color": "#48b6b8"},
    ".dashboard-page": {
        "max_width": "860px",
        "margin": "0 auto",
        "padding_top": "1.5rem",
    },
    ".dashboard-section-title": {
        "color": "#ffffff",
    },
    ".products-page-title": {
        "color": "#ffffff",
        "font_size": "1.25rem",
    },
    ".new-product-button": {
        "display": "inline-flex",
        "align_items": "center",
        "justify_content": "center",
        "padding": "0.7rem 1.25rem",
        "border_radius": "0.75rem",
        "background": "#0b8277",
        "color": "#ffffff",
        "font_size": "0.9rem",
        "font_weight": "700",
        "box_shadow": "0 0 18px rgba(20,184,166,0.3)",
    },
    ".products-card": {
        "max_width": "920px",
        "width": "100%",
        "padding": "1.25rem 1.75rem",
        "border_radius": "1.35rem",
    },
    ".product-table-head, .product-table-row": {
        "display": "grid",
        "grid_template_columns": "1.45fr 1.35fr 0.9fr 1fr 9.5rem",
        "gap": "1rem",
        "align_items": "center",
        "justify_items": "center",
        "width": "100%",
        "box_sizing": "border-box",
        "min_width": "47rem",
    },
    ".product-table-head": {
        "padding": "0.9rem 0.75rem 0.55rem",
        "border_bottom": "1px solid #17332f",
    },
    ".product-table-row": {
        "padding": "0.75rem 0.75rem",
        "border_bottom": "1px solid #17332f",
    },
    ".product-table-row:last-child": {
        "border_bottom": "none",
    },
    ".product-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.78rem",
        "font_weight": "700",
        "width": "100%",
        "text_align": "center",
    },
    ".product-table-cell": {
        "color": "#ffffff",
        "font_size": "0.82rem",
        "width": "100%",
        "text_align": "center",
    },
    ".product-table-row > :nth-child(4)": {
        "display": "flex",
        "justify_content": "center",
        "align_items": "center",
        "width": "100%",
    },
    ".product-edit-button": {
        "display": "inline-flex",
        "align_items": "center",
        "justify_content": "center",
        "padding": "0.38rem 0.75rem",
        "border": "1px solid #14b8a6",
        "border_radius": "0.55rem",
        "background": "transparent",
        "color": "#ffffff",
        "font_size": "0.72rem",
        "font_weight": "700",
    },
    ".product-remove-button": {
        "padding": "0.38rem 0.75rem",
        "border": "1px solid #ef4b55",
        "border_radius": "0.55rem",
        "background": "#ef4b55",
        "color": "#ffffff",
        "font_size": "0.72rem",
        "font_weight": "700",
    },
    ".product-modal-backdrop": {
        "position": "fixed",
        "inset": "0",
        "z_index": "30",
        "display": "flex",
        "align_items": "center",
        "justify_content": "center",
        "padding": "1rem",
        "box_sizing": "border-box",
        "background": "rgba(0,8,8,0.82)",
        "backdrop_filter": "blur(5px)",
    },
    ".product-modal": {
        "width": "100%",
        "max_width": "23.5rem",
        "padding": "1.5rem 1.35rem 1.25rem",
        "border": "1px solid #14b8a6",
        "border_radius": "1.1rem",
        "background": "#071412",
        "box_shadow": "0 0 35px rgba(20,184,166,0.28)",
        "gap": "0.75rem",
    },
    ".product-modal-title": {
        "color": "#ffffff",
        "font_size": "1.05rem",
    },
    ".product-form-label": {
        "color": "#9fb8b4",
        "font_size": "0.72rem",
        "margin_bottom": "-0.35rem",
    },
    ".product-modal input, .product-modal .rt-SelectTrigger": {
        "width": "100%",
        "min_height": "2.25rem",
        "border": "0",
        "border_radius": "0.7rem",
        "background": "#10221f",
        "color": "#ffffff",
        "box_shadow": "none",
        "outline": "none",
        "appearance": "none",
    },
    ".product-modal .rt-TextFieldRoot": {
        "width": "100%",
        "border": "0",
        "border_radius": "0.7rem",
        "background": "#10221f",
        "box_shadow": "none",
        "outline": "none",
        "overflow": "hidden",
    },
    ".product-modal .rt-TextFieldRoot:focus-within": {
        "border": "0",
        "box_shadow": "none",
        "outline": "none",
    },
    ".product-modal input:focus": {
        "border": "0",
        "box_shadow": "none",
        "outline": "none",
    },
    ".product-controlled-checkbox": {
        "color": "#ffffff",
        "font_size": "0.78rem",
        "align_items": "center",
        "gap": "0.45rem",
    },
    ".product-controlled-label": {
        "color": "#ffffff",
        "font_size": "0.78rem",
        "line_height": "1.2",
    },
    ".product-controlled-checkbox, .product-controlled-checkbox span": {
        "color": "#ffffff",
    },
    ".product-controlled-checkbox .rt-CheckboxRoot": {
        "width": "1rem",
        "height": "1rem",
        "min_width": "1rem",
        "min_height": "1rem",
        "padding": "0",
        "border": "1px solid #14b8a6",
        "border_radius": "0.25rem",
        "background": "transparent",
        "box_shadow": "none",
        "outline": "none",
    },
    ".product-controlled-checkbox .rt-CheckboxRoot[data-state='checked']": {
        "background": "#14b8a6",
        "border_color": "#14b8a6",
    },
    ".product-controlled-checkbox .rt-CheckboxIndicator": {
        "color": "#071412",
    },
    ".dashboard-stats": {
        "display": "grid",
        "grid_template_columns": "repeat(4, minmax(0, 1fr))",
        "gap": "0.75rem",
        "width": "100%",
    },
    ".stat-card": {
        "min_height": "7.25rem",
        "display": "flex",
        "align_items": "center",
        "box_sizing": "border-box",
        "padding": "1.15rem 1.1rem",
        "border": "1px solid #17332f",
        "border_radius": "0.75rem",
        "background": "#091515",
        "box_shadow": "0 12px 24px rgba(0,0,0,0.16)",
    },
    ".stat-card-number": {
        "color": "#38aee8",
        "font_size": "1.55rem",
        "font_weight": "800",
        "line_height": "1.15",
    },
    ".stat-card-label": {
        "color": "#8fb0ab",
        "font_size": "0.78rem",
        "margin_top": "0.35rem",
    },
    ".stock-alert-head, .stock-alert-row": {
        "display": "grid",
        "grid_template_columns": "2.1fr 1.1fr 1fr 1fr",
        "gap": "0.75rem",
        "align_items": "center",
        "width": "100%",
        "box_sizing": "border-box",
    },
    ".stock-alert-head": {
        "padding": "0.9rem 0.75rem 0.55rem",
        "border_bottom": "1px solid #17332f",
    },
    ".stock-alert-row": {
        "padding": "0.65rem 0.75rem",
        "border_bottom": "1px solid rgba(23,51,47,0.65)",
    },
    ".stock-alert-row:last-child": {
        "border_bottom": "none",
    },
    ".stock-alert-head .table-heading": {
        "text_align": "left",
    },
    ".stock-alert-row .table-cell": {
        "text_align": "left",
    },
    ".stock-alert-row .stock-critical": {
        "color": "#ff6262",
    },
    ".stock-alert-row .status-badge-danger": {
        "justify_self": "start",
        "color": "#ff7a7a",
        "background": "#5a151a",
        "border": "1px solid #8f252d",
    },
    ".content-card": {
        "padding": "1.25rem",
        "border": "1px solid #17332f",
        "border_radius": "18px",
        "background": "#081312",
        "box_shadow": "0 10px 30px -12px rgba(0,0,0,0.8), inset 0 1px 0 rgba(120,230,215,0.1)",
        "overflow_x": "auto",
    },
    ".attendance-backdrop": {
        "position": "fixed",
        "inset": "0",
        "z_index": "30",
        "display": "flex",
        "align_items": "center",
        "justify_content": "center",
        "padding": "1rem",
        "box_sizing": "border-box",
        "background": "rgba(0,8,8,0.82)",
        "backdrop_filter": "blur(5px)",
    },
    ".attendance-card": {
        "width": "100%",
        "max_width": "25.25rem",
        "max_height": "calc(100vh - 2rem)",
        "overflow_y": "auto",
        "padding": "1.5rem 1.35rem 1.25rem",
        "border": "1px solid #14b8a6",
        "border_radius": "1.1rem",
        "background": "#071412",
        "box_shadow": "0 0 35px rgba(20,184,166,0.28)",
        "box_sizing": "border-box",
    },
    ".attendance-card .page-title": {
        "color": "#ffffff",
        "font_size": "1.5rem",
        "margin_bottom": "0.35rem",
    },
    ".attendance-card .page-description": {"display": "none"},
    ".attendance-card input, .attendance-card .rt-TextFieldRoot, .attendance-card .rt-SelectTrigger": {
        "min_height": "2.25rem",
        "border": "none",
        "border_radius": "0.7rem",
        "background": "#10221f",
        "color": "#ffffff",
        "box_shadow": "none",
        "outline": "none",
    },
    ".attendance-card input, .attendance-card .rt-TextFieldRoot": {
        "width": "100%",
        "box_sizing": "border-box",
    },
    ".attendance-card input[placeholder*='ID do cliente'], .attendance-card input[placeholder*='Número da receita']": {
        "font_size": "0.8rem",
    },
    ".attendance-card .rt-SelectTrigger": {"width": "100%"},
    ".attendance-card, .attendance-card *": {
        "color": "#ffffff",
    },
    ".attendance-card input::placeholder": {
        "color": "#ffffff",
        "opacity": "1",
    },
    ".attendance-card button": {"padding": "0.45rem 0.9rem", "font_size": "0.9rem"},
    ".table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.78rem",
        "font_weight": "700",
        "text_align": "center",
    },
    ".sales-page-title": {
        "color": "#ffffff",
        "font_size": "1.25rem",
    },
    ".new-sale-button": {
        "display": "inline-flex",
        "align_items": "center",
        "justify_content": "center",
        "padding": "0.7rem 1.25rem",
        "border_radius": "0.75rem",
        "background": "linear-gradient(90deg, #0b8277, #0e7490)",
        "color": "#ffffff",
        "font_size": "0.9rem",
        "font_weight": "700",
        "box_shadow": "0 0 18px rgba(20,184,166,0.3)",
    },
    ".sales-table-head, .sales-table-row": {
        "display": "grid",
        "grid_template_columns": "0.75fr 0.65fr 1.05fr 1.05fr 0.85fr 0.9fr 0.8fr",
        "gap": "0.5rem",
        "align_items": "center",
        "width": "100%",
        "min_width": "100%",
        "box_sizing": "border-box",
    },
    ".sales-table-head": {
        "padding": "1rem 0 0.75rem",
        "border_bottom": "1px solid #17332f",
    },
    ".sales-table-row": {
        "padding": "0.85rem 0",
        "border_bottom": "1px solid #17332f",
    },
    ".sales-table-head .table-heading, .sales-table-row .table-cell": {
        "text_align": "center",
    },
    ".sales-table-head > :nth-child(1), .sales-table-row > :nth-child(1), .sales-table-head > :nth-child(2), .sales-table-row > :nth-child(2), .sales-table-head > :nth-child(3), .sales-table-row > :nth-child(3), .sales-table-head > :nth-child(4), .sales-table-row > :nth-child(4)": {
        "justify_self": "center",
        "text_align": "center",
    },
    ".sales-table-head > :nth-child(5), .sales-table-row > :nth-child(5)": {
        "justify_self": "center",
        "text_align": "center",
    },
    ".sales-table-head > :nth-child(6), .sales-table-row > :nth-child(6)": {
        "justify_self": "center",
        "text_align": "center",
    },
    ".sales-table-row .channel-badge": {
        "justify_self": "center",
    },
    ".table-cell": {
        "font_size": "0.82rem",
        "color": "#ffffff",
        "text_align": "center",
    },
    ".products-cell": {"line_height": "1.35", "text_align": "center"},
    ".sales-table-row .status-badge": {
        "justify_self": "center",
    },
    ".customers-card": {
        "padding": "1.25rem 1.75rem",
        "border_radius": "1.35rem",
    },
    ".form-modal-backdrop": {
        "position": "fixed",
        "inset": "0",
        "z_index": "30",
        "display": "flex",
        "align_items": "center",
        "justify_content": "center",
        "padding": "1rem",
        "box_sizing": "border-box",
        "background": "rgba(0,8,8,0.82)",
        "backdrop_filter": "blur(5px)",
    },
    ".form-modal-card": {
        "width": "100%",
        "max_width": "22.5rem",
        "max_height": "calc(100vh - 2rem)",
        "overflow_y": "auto",
        "padding": "1.25rem",
        "border": "1px solid #14b8a6",
        "border_radius": "1.1rem",
        "background": "#071412",
        "box_shadow": "0 0 35px rgba(20,184,166,0.28)",
        "gap": "0.95rem",
        "box_sizing": "border-box",
    },
    ".form-modal-card, .form-modal-card *": {
        "color": "#ffffff",
    },
    ".account-username": {
        "color": "#ffffff",
        "font_weight": "700",
    },
    ".customer-modal-title": {
        "color": "#ffffff",
        "font_size": "1.05rem",
        "margin_bottom": "0.15rem",
    },
    ".customer-modal-card": {
        "max_width": "22.5rem",
        "padding": "1.25rem",
        "border": "1px solid #14b8a6",
        "border_radius": "1.1rem",
        "background": "#071412",
        "box_shadow": "0 0 35px rgba(20,184,166,0.28)",
        "margin": "0 auto",
    },
    ".customer-modal-card > *": {
        "width": "100%",
        "text_align": "left",
    },
    ".customer-form-label": {
        "color": "#9fb8b4",
        "font_size": "0.72rem",
        "margin_bottom": "-0.35rem",
        "text_align": "left",
        "align_self": "flex-start",
    },
    ".customer-personal-field": {
        "width": "100%",
        "height": "2.25rem",
        "min_height": "2.25rem",
        "box_sizing": "border-box",
        "border": "0",
        "border_radius": "0.7rem",
        "background": "#10221f",
        "color": "#ffffff",
        "padding": "0 0.75rem",
        "font_size": "0.82rem",
        "line_height": "2.25rem",
        "text_align": "left",
        "vertical_align": "middle",
        "outline": "none",
        "pointer_events": "auto",
        "cursor": "text",
    },
    ".customer-personal-field:focus": {
        "border": "1px solid #14b8a6",
        "outline": "none",
        "box_shadow": "0 0 0 1px rgba(20,184,166,0.25)",
    },
    ".customer-address-title": {
        "color": "#ffffff",
        "font_size": "0.95rem",
    },
    ".form-modal-card input": {
        "width": "100%",
        "box_sizing": "border-box",
        "min_height": "2.25rem",
        "border": "0",
        "border_radius": "0.7rem",
        "background": "#10221f",
        "color": "#ffffff",
        "box_shadow": "none",
        "outline": "none",
        "appearance": "none",
    },
    ".form-modal-card input:focus": {
        "border": "0",
        "box_shadow": "none",
        "outline": "none",
    },
    ".form-modal-card .rt-TextFieldRoot": {
        "width": "100%",
        "border": "0",
        "border_radius": "0.7rem",
        "background": "#10221f",
        "box_shadow": "none",
        "outline": "none",
        "overflow": "hidden",
    },
    ".form-modal-card .rt-TextFieldRoot:focus-within": {
        "border": "0",
        "box_shadow": "none",
        "outline": "none",
    },
    ".product-list-container": {
        "display": "grid",
        "grid_template_columns": "repeat(auto-fill, minmax(220px, 1fr))",
        "gap": "1.5rem",
        "width": "100%",
    },
    ".product-card": {
        "padding": "1rem",
        "border": "1px solid #17332f",
        "border_radius": "10px",
        "background": "#081312",
        "box_shadow": "0 4px 12px rgba(0, 0, 0, 0.6)",
        "transition": "transform 0.2s",
    },
    ".product-card:hover": {
        "transform": "translateY(-4px)",
    },
    ".product-info": {
        "margin_top": "0.5rem",
    },
    ".product-name": {
        "color": "#ffffff",
        "font_size": "1rem",
        "font_weight": "500",
    },
    ".product-category": {
        "color": "#9fb8b4",
        "font_size": "0.85rem",
    },
    ".product-price": {
        "color": "#5eead4",
        "font_size": "1.1rem",
        "font_weight": "700",
    },
    ".product-stock": {
        "color": "#facc15",
        "font_size": "0.9rem",
        "font_weight": "500",
    },
    ".product-controlled": {
        "color": "#ef4444",
        "font_size": "0.9rem",
        "font_weight": "500",
    },
    ".product-actions": {
        "margin_top": "1rem",
        "display": "flex",
        "justify_content": "space-between",
        "align_items": "center",
    },
    ".add-to-cart-button": {
        "background": "#0b8277",
        "color": "#ffffff",
        "border_radius": "0.5rem",
        "padding": "0.5rem 1rem",
        "font_weight": "600",
        "transition": "background 0.2s",
    },
    ".add-to-cart-button:hover": {
        "background": "#0e7490",
    },
    ".edit-product-button": {
        "background": "transparent",
        "border": "1px solid #14b8a6",
        "color": "#ffffff",
        "padding": "0.4rem 0.8rem",
        "border_radius": "0.5rem",
        "font_weight": "600",
        "transition": "background 0.2s",
    },
    ".edit-product-button:hover": {
        "background": "rgba(20,184,166,0.1)",
    },
    ".remove-product-button": {
        "background": "#ef4444",
        "color": "#ffffff",
        "border_radius": "0.5rem",
        "padding": "0.4rem 0.8rem",
        "font_weight": "600",
        "transition": "background 0.2s",
    },
    ".remove-product-button:hover": {
        "background": "rgba(239,68,68,0.1)",
    },
    ".customer-card": {
        "padding": "1rem",
        "border": "1px solid #17332f",
        "border_radius": "10px",
        "background": "#081312",
        "box_shadow": "0 4px 12px rgba(0, 0, 0, 0.6)",
    },
    ".customer-info": {
        "margin_top": "0.5rem",
    },
    ".customer-name": {
        "color": "#ffffff",
        "font_size": "1rem",
        "font_weight": "500",
    },
    ".customer-details": {
        "color": "#9fb8b4",
        "font_size": "0.85rem",
    },
    ".customer-actions": {
        "margin_top": "1rem",
        "display": "flex",
        "justify_content": "space-between",
        "align_items": "center",
    },
    ".view-details-button": {
        "background": "#0b8277",
        "color": "#ffffff",
        "border_radius": "0.5rem",
        "padding": "0.5rem 1rem",
        "font_weight": "600",
        "transition": "background 0.2s",
    },
    ".view-details-button:hover": {
        "background": "#0e7490",
    },
    ".edit-customer-button": {
        "background": "transparent",
        "border": "1px solid #14b8a6",
        "color": "#ffffff",
        "padding": "0.4rem 0.8rem",
        "border_radius": "0.5rem",
        "font_weight": "600",
        "transition": "background 0.2s",
    },
    ".edit-customer-button:hover": {
        "background": "rgba(20,184,166,0.1)",
    },
    ".remove-customer-button": {
        "background": "#ef4444",
        "color": "#ffffff",
        "border_radius": "0.5rem",
        "padding": "0.4rem 0.8rem",
        "font_weight": "600",
        "transition": "background 0.2s",
    },
    ".remove-customer-button:hover": {
        "background": "rgba(239,68,68,0.1)",
    },
    ".supplier-card": {
        "padding": "1rem",
        "border": "1px solid #17332f",
        "border_radius": "10px",
        "background": "#081312",
        "box_shadow": "0 4px 12px rgba(0, 0, 0, 0.6)",
    },
    ".supplier-info": {
        "margin_top": "0.5rem",
    },
    ".supplier-name": {
        "color": "#ffffff",
        "font_size": "1rem",
        "font_weight": "500",
    },
    ".supplier-details": {
        "color": "#9fb8b4",
        "font_size": "0.85rem",
    },
    ".supplier-actions": {
        "margin_top": "1rem",
        "display": "flex",
        "justify_content": "space-between",
        "align_items": "center",
    },
    ".edit-supplier-button": {
        "background": "transparent",
        "border": "1px solid #14b8a6",
        "color": "#ffffff",
        "padding": "0.4rem 0.8rem",
        "border_radius": "0.5rem",
        "font_weight": "600",
        "transition": "background 0.2s",
    },
    ".edit-supplier-button:hover": {
        "background": "rgba(20,184,166,0.1)",
    },
    ".remove-supplier-button": {
        "background": "#ef4444",
        "color": "#ffffff",
        "border_radius": "0.5rem",
        "padding": "0.4rem 0.8rem",
        "font_weight": "600",
        "transition": "background 0.2s",
    },
    ".remove-supplier-button:hover": {
        "background": "rgba(239,68,68,0.1)",
    },
    ".category-card": {
        "max_width": "42rem",
        "padding": "1.25rem 1.5rem",
    },
    ".category-row": {
        "padding": "0.7rem 0",
        "border_bottom": "1px solid #17332f",
    },
    ".category-name": {
        "color": "#ffffff",
        "font_size": "0.85rem",
        "font_weight": "600",
    },
    ".category-id": {
        "color": "#8fb0ab",
        "font_size": "0.75rem",
    },
    ".new-customer-button": {
        "display": "inline-flex",
        "align_items": "center",
        "justify_content": "center",
        "padding": "0.7rem 1.25rem",
        "border_radius": "0.75rem",
        "background": "linear-gradient(90deg, #0b8277, #0e7490)",
        "color": "#ffffff",
        "font_size": "0.9rem",
        "font_weight": "700",
        "white_space": "nowrap",
        "box_shadow": "0 0 18px rgba(20,184,166,0.3)",
    },
    ".customer-table-head, .customer-table-row": {
        "display": "grid",
        "grid_template_columns": "1.35fr 1fr 1.1fr 1.4fr 1.35fr 1.7fr",
        "gap": "1rem",
        "align_items": "center",
        "width": "100%",
        "box_sizing": "border-box",
        "min_width": "62rem",
    },
    ".customer-table-head": {
        "padding": "1rem 0 0.75rem",
        "border_bottom": "1px solid #17332f",
    },
    ".customer-table-row": {
        "padding": "0.75rem 0",
        "border_bottom": "1px solid #17332f",
    },
    ".customer-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.78rem",
        "font_weight": "700",
        "text_align": "left",
    },
    ".customer-table-cell": {
        "color": "#ffffff",
        "font_size": "0.82rem",
        "text_align": "left",
    },
    ".customer-name": {"font_weight": "500"},
    ".customer-edit-button": {
        "background": "transparent",
        "border": "1px solid #14b8a6",
        "color": "#ffffff",
        "padding": "0.4rem 0.8rem",
        "box_shadow": "none",
    },
    ".customer-remove-button": {
        "background": "#ef4b55",
        "border": "1px solid #ef4b55",
        "color": "#ffffff",
        "padding": "0.4rem 0.8rem",
        "box_shadow": "none",
    },
    ".employee-card": {
        "max_width": "1100px",
        "width": "100%",
        "padding": "1.5rem 2rem",
        "border_radius": "1.35rem",
    },
    ".employee-table-head, .employee-table-row": {
        "display": "grid",
        "grid_template_columns": "1.35fr 1.15fr 1.15fr 1fr 1.55fr 1.55fr 9.5rem",
        "gap": "1.25rem",
        "align_items": "center",
        "width": "100%",
        "box_sizing": "border-box",
        "min_width": "48rem",
    },
    ".employee-table-head": {
        "padding": "0.9rem 0.75rem 0.55rem",
        "border_bottom": "1px solid #17332f",
    },
    ".employee-table-row": {
        "padding": "0.75rem 0.75rem",
        "border_bottom": "1px solid #17332f",
    },
    ".employee-table-row:last-child": {
        "border_bottom": "none",
    },
    ".employee-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.78rem",
        "font_weight": "700",
        "text_align": "center",
    },
    ".employee-table-cell": {
        "color": "#ffffff",
        "font_size": "0.82rem",
        "text_align": "center",
    },
    ".employee-table-head > :nth-child(1), .employee-table-row > :nth-child(1), .employee-table-head > :nth-child(2), .employee-table-row > :nth-child(2), .employee-table-head > :nth-child(3), .employee-table-row > :nth-child(3), .employee-table-head > :nth-child(4), .employee-table-row > :nth-child(4), .employee-table-head > :nth-child(5), .employee-table-row > :nth-child(5), .employee-table-head > :nth-child(6), .employee-table-row > :nth-child(6)": {
        "justify_self": "center",
        "text_align": "center",
    },
    ".employee-edit-button": {
        "display": "inline-flex",
        "align_items": "center",
        "justify_content": "center",
        "padding": "0.38rem 0.75rem",
        "border": "1px solid #14b8a6",
        "border_radius": "0.55rem",
        "background": "transparent",
        "color": "#ffffff",
        "font_size": "0.72rem",
        "font_weight": "700",
    },
    ".employee-remove-button": {
        "padding": "0.38rem 0.75rem",
        "border": "1px solid #ef4b55",
        "border_radius": "0.55rem",
        "background": "#ef4b55",
        "color": "#ffffff",
        "font_size": "0.72rem",
        "font_weight": "700",
    },
    ".employee-activate-button": {
        "padding": "0.38rem 0.75rem",
        "border": "1px solid #14b8a6",
        "border_radius": "0.55rem",
        "background": "#0b8277",
        "color": "#ffffff",
        "font_size": "0.72rem",
        "font_weight": "700",
    },
    ".new-employee-button": {
        "display": "inline-flex",
        "align_items": "center",
        "justify_content": "center",
        "padding": "0.7rem 1.25rem",
        "border_radius": "0.75rem",
        "background": "#0b8277",
        "color": "#ffffff",
        "font_size": "0.9rem",
        "font_weight": "700",
        "box_shadow": "0 0 18px rgba(20,184,166,0.3)",
    },
    ".employee-modal-backdrop": {
        "position": "fixed",
        "inset": "0",
        "z_index": "30",
        "display": "flex",
        "align_items": "center",
        "justify_content": "center",
        "padding": "1rem",
        "box_sizing": "border-box",
        "background": "rgba(0,8,8,0.82)",
        "backdrop_filter": "blur(5px)",
    },
    ".employee-modal": {
        "width": "100%",
        "max_width": "26rem",
        "max_height": "calc(100vh - 2rem)",
        "overflow_y": "auto",
        "padding": "1.5rem",
        "border": "1px solid #14b8a6",
        "border_radius": "1.1rem",
        "background": "#071412",
        "box_shadow": "0 0 35px rgba(20,184,166,0.28)",
        "gap": "0.65rem",
        "box_sizing": "border-box",
    },
    ".employee-modal-title": {
        "color": "#ffffff",
        "font_size": "1.05rem",
        "margin_bottom": "0.15rem",
    },
    ".employee-modal input": {
        "width": "100%",
        "box_sizing": "border-box",
        "min_height": "2.55rem",
        "height": "2.55rem",
        "border": "0",
        "border_radius": "0.7rem",
        "background": "#10221f",
        "color": "#ffffff",
        "box_shadow": "none",
        "outline": "none",
        "appearance": "none",
    },
    ".employee-modal input:focus": {
        "border": "0",
        "box_shadow": "none",
        "outline": "none",
    },
    ".employee-modal .rt-TextFieldRoot": {
        "width": "100%",
        "border": "0",
        "border_radius": "0.7rem",
        "background": "#10221f",
        "box_shadow": "none",
        "outline": "none",
        "overflow": "hidden",
    },
    ".employee-modal .rt-TextFieldRoot:focus-within": {
        "border": "0",
        "box_shadow": "none",
        "outline": "none",
    },
    ".employee-form-label": {
        "color": "#9fb8b4",
        "font_size": "0.72rem",
        "margin_bottom": "-0.15rem",
    },
    ".initial-access-label": {
        "color": "#9fb8b4",
        "font_weight": "500",
    },
    ".initial-access-field": {
        "width": "100%",
        "height": "2.55rem",
        "min_height": "2.55rem",
        "box_sizing": "border-box",
        "border": "0",
        "border_radius": "0.7rem",
        "background": "#10221f",
        "color": "#ffffff",
        "padding": "0 0.75rem",
        "font_size": "0.82rem",
        "line_height": "2.25rem",
        "text_align": "left",
        "outline": "none",
        "pointer_events": "auto",
        "cursor": "text",
    },
    ".initial-password-wrapper": {
        "position": "relative",
        "width": "100%",
    },
    ".initial-password-field": {
        "padding_right": "5rem",
    },
    ".initial-password-toggle": {
        "position": "absolute",
        "right": "0.35rem",
        "top": "50%",
        "transform": "translateY(-50%)",
        "height": "1.55rem",
        "min_height": "1.55rem",
        "padding": "0 0.45rem",
        "border": "0",
        "border_radius": "0.45rem",
        "background": "#0b8277",
        "color": "#ffffff",
        "font_size": "0.65rem",
        "font_weight": "700",
    },
    ".employee-remove-modal": {
        "width": "100%",
        "max_width": "23.5rem",
        "min_height": "0",
        "padding": "1.35rem 1.25rem",
        "border": "1px solid #ef4b55",
        "border_radius": "1rem",
        "background": "#071412",
        "box_shadow": "0 0 35px rgba(239,75,85,0.24)",
        "box_sizing": "border-box",
    },
    ".employee-remove-title": {
        "color": "#ef4b55",
        "font_size": "1.05rem",
        "margin": "0",
    },
    ".employee-remove-message": {
        "max_width": "19rem",
        "color": "#ef4b55",
        "font_size": "0.78rem",
        "line_height": "1.45",
        "text_align": "center",
    },
    ".employee-remove-message .strong": {
        "color": "#ef4b55",
    },
    ".employee-remove-modal .employee-confirm-remove-button": {
        "background": "#ffffff",
        "border": "1px solid #ef4b55",
        "color": "#ef4b55",
    },
    ".employee-confirm-remove-button": {
        "background": "#ef4b55",
        "border": "1px solid #ef4b55",
        "color": "#ffffff",
        "padding": "0.55rem 1.1rem",
        "border_radius": "0.65rem",
        "font_weight": "700",
        "box_shadow": "none",
    },
    ".stock-card": {
        "padding": "1.25rem 1.75rem",
        "border_radius": "1.35rem",
    },
    ".stock-table-head, .stock-table-row": {
        "display": "grid",
        "grid_template_columns": "1.55fr 1.1fr 0.65fr 0.65fr 0.75fr",
        "gap": "1rem",
        "align_items": "center",
        "min_width": "52rem",
    },
    ".stock-table-head": {
        "padding": "1rem 0 0.75rem",
        "border_bottom": "1px solid #17332f",
    },
    ".stock-table-row": {
        "padding": "0.8rem 0",
        "border_bottom": "1px solid #17332f",
    },
    ".stock-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.78rem",
        "font_weight": "700",
        "text_align": "center",
    },
    ".stock-table-cell": {
        "color": "#ffffff",
        "font_size": "0.82rem",
        "text_align": "center",
    },
    ".stock-product": {"font_weight": "500", "text_align": "center"},
    ".stock-value": {"font_weight": "700", "text_align": "center"},
    ".stock-critical": {
        "color": "#ff5a63",
        "font_weight": "700",
    },
    ".stock-status": {
        "justify_self": "center",
        "display": "inline-flex",
        "padding": "0.3rem 0.75rem",
        "border_radius": "999px",
        "font_size": "0.75rem",
        "font_weight": "700",
    },
    ".stock-status-success": {
        "color": "#34d399",
        "background": "rgba(16,185,129,0.12)",
        "border": "1px solid rgba(16,185,129,0.65)",
    },
    ".stock-status-danger": {
        "color": "#ff5a63",
        "background": "rgba(239,68,68,0.12)",
        "border": "1px solid rgba(239,68,68,0.65)",
    },
    ".strong": {"font_weight": "700", "color": "#ffffff"},
    ".status-badge": {
        "display": "inline-block",
        "padding": "0.2rem 0.65rem",
        "border_radius": "999px",
        "font_size": "0.72rem",
        "font_weight": "700",
        "white_space": "nowrap",
    },
    ".status-badge-success": {"background": "#d9f3e8", "color": "#0a6b4d"},
    ".status-badge-info": {"background": "#e4f0f8", "color": "#28607f"},
    ".status-badge-warning": {"background": "#fff0d6", "color": "#8a5a12"},
    ".status-badge-danger": {"background": "#fcebea", "color": "#a32d2d"},
    ".channel-badge": {
        "border": "1px solid",
        "padding": "0.35rem 0.75rem",
    },
    ".channel-badge-presencial": {
        "background": "rgba(143,176,171,0.12)",
        "border_color": "rgba(143,176,171,0.55)",
        "color": "#a9c5c0",
    },
    ".channel-badge-online": {
        "background": "rgba(34,211,238,0.12)",
        "border_color": "rgba(34,211,238,0.7)",
        "color": "#22d3ee",
    },
    ".supplier-table-head, .supplier-table-row": {
        "display": "grid",
        "grid_template_columns": "1.4fr 1fr 1.15fr 0.8fr 10rem",
        "gap": "0.8rem",
        "align_items": "center",
        "width": "100%",
        "box_sizing": "border-box",
        "min_width": "48rem",
    },
    ".supplier-table-head": {
        "padding": "0.6rem 0.5rem",
        "border_bottom": "1px solid #17332f",
    },
    ".supplier-table-row": {
        "padding": "0.8rem 0.5rem",
        "border_bottom": "1px solid #17332f",
    },
    ".supplier-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.75rem",
        "font_weight": "700",
        "text_align": "center",
    },
    ".supplier-list-card": {
        "max_width": "860px",
        "margin": "0 auto",
        "padding": "1.25rem 1.75rem",
        "border_radius": "1.35rem",
    },
    ".supplier-list": {
        "width": "100%",
        "align_items": "center",
    },
    ".supplier-table-head > :nth-child(-n+3), .supplier-table-row > :nth-child(-n+3)": {
        "text_align": "center",
    },
    ".supplier-section-heading": {
        "color": "#ffffff",
    },
    ".supplier-deadline": {
        "color": "#e3e4d4",
        "font_size": "0.78rem",
        "white_space": "nowrap",
    },
    ".supplier-table-head > :nth-child(4), .supplier-table-row > :nth-child(4)": {
        "justify_self": "center",
        "text_align": "center",
    },
    ".supplier-table-head > :nth-child(5), .supplier-table-row > :nth-child(5)": {
        "justify_self": "center",
        "text_align": "center",
        "width": "100%",
        "justify_content": "center",
    },
    ".supplier-action-button": {
        "padding": "0.35rem 0.65rem",
        "font_size": "0.72rem",
        "white_space": "nowrap",
    },
    ".new-supplier-button": {
        "display": "inline-flex",
        "align_items": "center",
        "justify_content": "center",
        "padding": "0.7rem 1.25rem",
        "border_radius": "0.75rem",
        "background": "#0b8277",
        "color": "#ffffff",
        "font_size": "0.9rem",
        "font_weight": "700",
        "white_space": "nowrap",
        "box_shadow": "0 0 18px rgba(20,184,166,0.3)",
    },
    ".supplier-modal-backdrop": {
        "position": "fixed",
        "inset": "0",
        "z_index": "30",
        "display": "flex",
        "align_items": "center",
        "justify_content": "center",
        "padding": "1rem",
        "box_sizing": "border-box",
        "background": "rgba(0,8,8,0.82)",
        "backdrop_filter": "blur(5px)",
    },
    ".supplier-modal": {
        "width": "100%",
        "max_width": "22.5rem",
        "max_height": "calc(100vh - 2rem)",
        "overflow_y": "auto",
        "padding": "1.25rem",
        "border": "1px solid #14b8a6",
        "border_radius": "1.1rem",
        "background": "#071412",
        "box_shadow": "0 0 35px rgba(20,184,166,0.28)",
        "gap": "0.65rem",
        "box_sizing": "border-box",
    },
    ".supplier-modal-title": {
        "color": "#ffffff",
        "font_size": "1.05rem",
        "margin_bottom": "0.15rem",
    },
    ".supplier-form-label": {
        "color": "#9fb8b4",
        "font_size": "0.72rem",
        "margin_bottom": "-0.35rem",
    },
    ".supplier-modal input": {
        "width": "100%",
        "box_sizing": "border-box",
        "min_height": "2.25rem",
        "border": "0",
        "border_radius": "0.7rem",
        "background": "#10221f",
        "color": "#ffffff",
        "box_shadow": "none",
        "outline": "none",
        "appearance": "none",
    },
    ".supplier-modal input:focus": {
        "border": "0",
        "box_shadow": "none",
        "outline": "none",
    },
    ".supplier-modal .rt-TextFieldRoot": {
        "width": "100%",
        "border": "0",
        "border_radius": "0.7rem",
        "background": "#10221f",
        "box_shadow": "none",
        "outline": "none",
        "overflow": "hidden",
    },
    ".supplier-modal .rt-TextFieldRoot:focus-within": {
        "border": "0",
        "box_shadow": "none",
        "outline": "none",
    },
    ".supplier-remove-modal": {
        "width": "100%",
        "max_width": "23.5rem",
        "padding": "1.35rem 1.25rem",
        "border": "1px solid #14b8a6",
        "border_radius": "1rem",
        "background": "#071412",
        "box_shadow": "0 0 35px rgba(20,184,166,0.28)",
        "box_sizing": "border-box",
    },
    ".supplier-remove-title": {
        "color": "#ffffff",
        "font_size": "1.05rem",
        "margin": "0",
    },
    ".supplier-remove-message": {
        "max_width": "19rem",
        "color": "#9fb8b4",
        "font_size": "0.78rem",
        "line_height": "1.45",
        "text_align": "center",
    },
    ".customer-table-head, .customer-table-row": {
        "display": "grid",
        "grid_template_columns": "1.35fr 1fr 1.1fr 1.4fr 1.35fr 1.7fr",
        "gap": "1rem",
        "align_items": "center",
        "width": "100%",
        "box_sizing": "border-box",
        "min_width": "62rem",
    },
    ".customer-table-head": {
        "padding": "1rem 0 0.75rem",
        "border_bottom": "1px solid #17332f",
    },
    ".customer-table-row": {
        "padding": "0.75rem 0",
        "border_bottom": "1px solid #17332f",
    },
    ".customer-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.78rem",
        "font_weight": "700",
        "text_align": "left",
    },
    ".customer-table-cell": {
        "color": "#ffffff",
        "font_size": "0.82rem",
        "text_align": "left",
    },
    ".customer-name": {"font_weight": "500"},
    ".customer-edit-button": {
        "background": "transparent",
        "border": "1px solid #14b8a6",
        "color": "#ffffff",
        "padding": "0.4rem 0.8rem",
        "box_shadow": "none",
    },
    ".customer-remove-button": {
        "background": "#ef4b55",
        "border": "1px solid #ef4b55",
        "color": "#ffffff",
        "padding": "0.4rem 0.8rem",
        "box_shadow": "none",
    },
    ".stock-card": {
        "padding": "1.25rem 1.75rem",
        "border_radius": "1.35rem",
    },
    ".stock-table-head, .stock-table-row": {
        "display": "grid",
        "grid_template_columns": "1.55fr 1.1fr 0.65fr 0.65fr 0.75fr",
        "gap": "1rem",
        "align_items": "center",
        "min_width": "52rem",
    },
    ".stock-table-head": {
        "padding": "1rem 0 0.75rem",
        "border_bottom": "1px solid #17332f",
    },
    ".stock-table-row": {
        "padding": "0.8rem 0",
        "border_bottom": "1px solid #17332f",
    },
    ".stock-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.78rem",
        "font_weight": "700",
        "text_align": "center",
    },
    ".stock-table-cell": {
        "color": "#ffffff",
        "font_size": "0.82rem",
        "text_align": "center",
    },
    ".stock-product": {"font_weight": "500", "text_align": "center"},
    ".stock-value": {"font_weight": "700", "text_align": "center"},
    ".stock-critical": {
        "color": "#ff5a63",
        "font_weight": "700",
    },
    ".stock-status": {
        "justify_self": "center",
        "display": "inline-flex",
        "padding": "0.3rem 0.75rem",
        "border_radius": "999px",
        "font_size": "0.75rem",
        "font_weight": "700",
    },
    ".stock-status-success": {
        "color": "#34d399",
        "background": "rgba(16,185,129,0.12)",
        "border": "1px solid rgba(16,185,129,0.65)",
    },
    ".stock-status-danger": {
        "color": "#ff5a63",
        "background": "rgba(239,68,68,0.12)",
        "border": "1px solid rgba(239,68,68,0.65)",
    },
    ".strong": {"font_weight": "700", "color": "#ffffff"},
    ".status-badge": {
        "display": "inline-block",
        "padding": "0.2rem 0.65rem",
        "border_radius": "999px",
        "font_size": "0.72rem",
        "font_weight": "700",
        "white_space": "nowrap",
    },
    ".status-badge-success": {"background": "#d9f3e8", "color": "#0a6b4d"},
    ".status-badge-info": {"background": "#e4f0f8", "color": "#28607f"},
    ".status-badge-warning": {"background": "#fff0d6", "color": "#8a5a12"},
    ".status-badge-danger": {"background": "#fcebea", "color": "#a32d2d"},
    ".channel-badge": {
        "border": "1px solid",
        "padding": "0.35rem 0.75rem",
    },
    ".channel-badge-presencial": {
        "background": "rgba(143,176,171,0.12)",
        "border_color": "rgba(143,176,171,0.55)",
        "color": "#a9c5c0",
    },
    ".channel-badge-online": {
        "background": "rgba(34,211,238,0.12)",
        "border_color": "rgba(34,211,238,0.7)",
        "color": "#22d3ee",
    },
    ".supplier-table-head, .supplier-table-row": {
        "display": "grid",
        "grid_template_columns": "1.4fr 1fr 1.15fr 0.8fr 10rem",
        "gap": "0.8rem",
        "align_items": "center",
        "width": "100%",
        "box_sizing": "border-box",
        "min_width": "48rem",
    },
    ".supplier-table-head": {
        "padding": "0.6rem 0.5rem",
        "border_bottom": "1px solid #17332f",
    },
    ".supplier-table-row": {
        "padding": "0.8rem 0.5rem",
        "border_bottom": "1px solid #17332f",
    },
    ".supplier-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.75rem",
        "font_weight": "700",
    },
    ".supplier-deadline": {
        "color": "#e3e4d4",
        "font_size": "0.78rem",
        "white_space": "nowrap",
    },
    ".supplier-table-head > :nth-child(4), .supplier-table-row > :nth-child(4)": {
        "justify_self": "center",
        "text_align": "center",
    },
    ".supplier-table-head > :nth-child(5), .supplier-table-row > :nth-child(5)": {
        "justify_self": "center",
        "text_align": "center",
        "width": "100%",
        "justify_content": "center",
    },
    ".supplier-action-button": {
        "padding": "0.35rem 0.65rem",
        "font_size": "0.72rem",
        "white_space": "nowrap",
    },
    ".new-supplier-button": {
        "display": "inline-flex",
        "align_items": "center",
        "justify_content": "center",
        "padding": "0.7rem 1.25rem",
        "border_radius": "0.75rem",
        "background": "#0b8277",
        "color": "#ffffff",
        "font_size": "0.9rem",
        "font_weight": "700",
        "white_space": "nowrap",
        "box_shadow": "0 0 18px rgba(20,184,166,0.3)",
    },
    ".customer-table-head, .customer-table-row": {
        "display": "grid",
        "grid_template_columns": "1.35fr 1fr 1.1fr 1.4fr 1.35fr 1.7fr",
        "gap": "1rem",
        "align_items": "center",
        "width": "100%",
        "box_sizing": "border-box",
        "min_width": "62rem",
    },
    ".customer-table-head": {
        "padding": "1rem 0 0.75rem",
        "border_bottom": "1px solid #17332f",
    },
    ".customer-table-row": {
        "padding": "0.75rem 0",
        "border_bottom": "1px solid #17332f",
    },
    ".customer-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.78rem",
        "font_weight": "700",
        "text_align": "left",
    },
    ".customer-table-cell": {
        "color": "#ffffff",
        "font_size": "0.82rem",
        "text_align": "left",
    },
    ".customer-name": {"font_weight": "500"},
    ".customer-edit-button": {
        "background": "transparent",
        "border": "1px solid #14b8a6",
        "color": "#ffffff",
        "padding": "0.4rem 0.8rem",
        "box_shadow": "none",
    },
    ".customer-remove-button": {
        "background": "#ef4b55",
        "border": "1px solid #ef4b55",
        "color": "#ffffff",
        "padding": "0.4rem 0.8rem",
        "box_shadow": "none",
    },
    ".stock-card": {
        "padding": "1.25rem 1.75rem",
        "border_radius": "1.35rem",
    },
    ".stock-table-head, .stock-table-row": {
        "display": "grid",
        "grid_template_columns": "1.55fr 1.1fr 0.65fr 0.65fr 0.75fr",
        "gap": "1rem",
        "align_items": "center",
        "min_width": "52rem",
    },
    ".stock-table-head": {
        "padding": "1rem 0 0.75rem",
        "border_bottom": "1px solid #17332f",
    },
    ".stock-table-row": {
        "padding": "0.8rem 0",
        "border_bottom": "1px solid #17332f",
    },
    ".stock-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.78rem",
        "font_weight": "700",
        "text_align": "center",
    },
    ".stock-table-cell": {
        "color": "#ffffff",
        "font_size": "0.82rem",
        "text_align": "center",
    },
    ".stock-product": {"font_weight": "500", "text_align": "center"},
    ".stock-value": {"font_weight": "700", "text_align": "center"},
    ".stock-critical": {
        "color": "#ff5a63",
        "font_weight": "700",
    },
    ".stock-status": {
        "justify_self": "center",
        "display": "inline-flex",
        "padding": "0.3rem 0.75rem",
        "border_radius": "999px",
        "font_size": "0.75rem",
        "font_weight": "700",
    },
    ".stock-status-success": {
        "color": "#34d399",
        "background": "rgba(16,185,129,0.12)",
        "border": "1px solid rgba(16,185,129,0.65)",
    },
    ".stock-status-danger": {
        "color": "#ff5a63",
        "background": "rgba(239,68,68,0.12)",
        "border": "1px solid rgba(239,68,68,0.65)",
    },
    ".strong": {"font_weight": "700", "color": "#ffffff"},
    ".status-badge": {
        "display": "inline-block",
        "padding": "0.2rem 0.65rem",
        "border_radius": "999px",
        "font_size": "0.72rem",
        "font_weight": "700",
        "white_space": "nowrap",
    },
    ".status-badge-success": {"background": "#d9f3e8", "color": "#0a6b4d"},
    ".status-badge-info": {"background": "#e4f0f8", "color": "#28607f"},
    ".status-badge-warning": {"background": "#fff0d6", "color": "#8a5a12"},
    ".status-badge-danger": {"background": "#fcebea", "color": "#a32d2d"},
    ".channel-badge": {
        "border": "1px solid",
        "padding": "0.35rem 0.75rem",
    },
    ".channel-badge-presencial": {
        "background": "rgba(143,176,171,0.12)",
        "border_color": "rgba(143,176,171,0.55)",
        "color": "#a9c5c0",
    },
    ".channel-badge-online": {
        "background": "rgba(34,211,238,0.12)",
        "border_color": "rgba(34,211,238,0.7)",
        "color": "#22d3ee",
    },
    ".supplier-table-head, .supplier-table-row": {
        "display": "grid",
        "grid_template_columns": "1.4fr 1fr 1.15fr 0.8fr 10rem",
        "gap": "0.8rem",
        "align_items": "center",
        "width": "100%",
        "box_sizing": "border-box",
        "min_width": "48rem",
    },
    ".supplier-table-head": {
        "padding": "0.6rem 0.5rem",
        "border_bottom": "1px solid #17332f",
    },
    ".supplier-table-row": {
        "padding": "0.8rem 0.5rem",
        "border_bottom": "1px solid #17332f",
    },
    ".supplier-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.75rem",
        "font_weight": "700",
    },
    ".supplier-deadline": {
        "color": "#e3e4d4",
        "font_size": "0.78rem",
        "white_space": "nowrap",
    },
    ".supplier-table-head > :nth-child(4), .supplier-table-row > :nth-child(4)": {
        "justify_self": "center",
        "text_align": "center",
    },
    ".supplier-table-head > :nth-child(5), .supplier-table-row > :nth-child(5)": {
        "justify_self": "center",
        "text_align": "center",
        "width": "100%",
        "justify_content": "center",
    },
    ".supplier-action-button": {
        "padding": "0.35rem 0.65rem",
        "font_size": "0.72rem",
        "white_space": "nowrap",
    },
    ".new-supplier-button": {
        "display": "inline-flex",
        "align_items": "center",
        "justify_content": "center",
        "padding": "0.7rem 1.25rem",
        "border_radius": "0.75rem",
        "background": "#0b8277",
        "color": "#ffffff",
        "font_size": "0.9rem",
        "font_weight": "700",
        "white_space": "nowrap",
        "box_shadow": "0 0 18px rgba(20,184,166,0.3)",
    },
    ".customer-table-head, .customer-table-row": {
        "display": "grid",
        "grid_template_columns": "1.35fr 1fr 1.1fr 1.4fr 1.35fr 1.7fr",
        "gap": "1rem",
        "align_items": "center",
        "width": "100%",
        "box_sizing": "border-box",
        "min_width": "62rem",
    },
    ".customer-table-head": {
        "padding": "1rem 0 0.75rem",
        "border_bottom": "1px solid #17332f",
    },
    ".customer-table-row": {
        "padding": "0.75rem 0",
        "border_bottom": "1px solid #17332f",
    },
    ".customer-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.78rem",
        "font_weight": "700",
        "text_align": "left",
    },
    ".customer-table-cell": {
        "color": "#ffffff",
        "font_size": "0.82rem",
        "text_align": "left",
    },
    ".customer-name": {"font_weight": "500"},
    ".customer-edit-button": {
        "background": "transparent",
        "border": "1px solid #14b8a6",
        "color": "#ffffff",
        "padding": "0.4rem 0.8rem",
        "box_shadow": "none",
    },
    ".customer-remove-button": {
        "background": "#ef4b55",
        "border": "1px solid #ef4b55",
        "color": "#ffffff",
        "padding": "0.4rem 0.8rem",
        "box_shadow": "none",
    },
    ".stock-card": {
        "padding": "1.25rem 1.75rem",
        "border_radius": "1.35rem",
    },
    ".stock-table-head, .stock-table-row": {
        "display": "grid",
        "grid_template_columns": "1.55fr 1.1fr 0.65fr 0.65fr 0.75fr",
        "gap": "1rem",
        "align_items": "center",
        "min_width": "52rem",
    },
    ".stock-table-head": {
        "padding": "1rem 0 0.75rem",
        "border_bottom": "1px solid #17332f",
    },
    ".stock-table-row": {
        "padding": "0.8rem 0",
        "border_bottom": "1px solid #17332f",
    },
    ".stock-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.78rem",
        "font_weight": "700",
        "text_align": "center",
    },
    ".stock-table-cell": {
        "color": "#ffffff",
        "font_size": "0.82rem",
        "text_align": "center",
    },
    ".stock-product": {"font_weight": "500", "text_align": "center"},
    ".stock-value": {"font_weight": "700", "text_align": "center"},
    ".stock-critical": {
        "color": "#ff5a63",
        "font_weight": "700",
    },
    ".stock-status": {
        "justify_self": "center",
        "display": "inline-flex",
        "padding": "0.3rem 0.75rem",
        "border_radius": "999px",
        "font_size": "0.75rem",
        "font_weight": "700",
    },
    ".stock-status-success": {
        "color": "#34d399",
        "background": "rgba(16,185,129,0.12)",
        "border": "1px solid rgba(16,185,129,0.65)",
    },
    ".stock-status-danger": {
        "color": "#ff5a63",
        "background": "rgba(239,68,68,0.12)",
        "border": "1px solid rgba(239,68,68,0.65)",
    },
    ".strong": {"font_weight": "700", "color": "#ffffff"},
    ".status-badge": {
        "display": "inline-block",
        "padding": "0.2rem 0.65rem",
        "border_radius": "999px",
        "font_size": "0.72rem",
        "font_weight": "700",
        "white_space": "nowrap",
    },
    ".status-badge-success": {"background": "#d9f3e8", "color": "#0a6b4d"},
    ".status-badge-info": {"background": "#e4f0f8", "color": "#28607f"},
    ".status-badge-warning": {"background": "#fff0d6", "color": "#8a5a12"},
    ".status-badge-danger": {"background": "#fcebea", "color": "#a32d2d"},
    ".channel-badge": {
        "border": "1px solid",
        "padding": "0.35rem 0.75rem",
    },
    ".channel-badge-presencial": {
        "background": "rgba(143,176,171,0.12)",
        "border_color": "rgba(143,176,171,0.55)",
        "color": "#a9c5c0",
    },
    ".channel-badge-online": {
        "background": "rgba(34,211,238,0.12)",
        "border_color": "rgba(34,211,238,0.7)",
        "color": "#22d3ee",
    },
    ".supplier-table-head, .supplier-table-row": {
        "display": "grid",
        "grid_template_columns": "1.4fr 1fr 1.15fr 0.8fr 10rem",
        "gap": "0.8rem",
        "align_items": "center",
        "width": "100%",
        "box_sizing": "border-box",
        "min_width": "48rem",
    },
    ".supplier-table-head": {
        "padding": "0.6rem 0.5rem",
        "border_bottom": "1px solid #17332f",
    },
    ".supplier-table-row": {
        "padding": "0.8rem 0.5rem",
        "border_bottom": "1px solid #17332f",
    },
    ".supplier-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.75rem",
        "font_weight": "700",
    },
    ".supplier-deadline": {
        "color": "#e3e4d4",
        "font_size": "0.78rem",
        "white_space": "nowrap",
    },
    ".supplier-table-head > :nth-child(4), .supplier-table-row > :nth-child(4)": {
        "justify_self": "center",
        "text_align": "center",
    },
    ".supplier-table-head > :nth-child(5), .supplier-table-row > :nth-child(5)": {
        "justify_self": "center",
        "text_align": "center",
        "width": "100%",
        "justify_content": "center",
    },
    ".supplier-action-button": {
        "padding": "0.35rem 0.65rem",
        "font_size": "0.72rem",
        "white_space": "nowrap",
    },
    ".new-supplier-button": {
        "display": "inline-flex",
        "align_items": "center",
        "justify_content": "center",
        "padding": "0.7rem 1.25rem",
        "border_radius": "0.75rem",
        "background": "#0b8277",
        "color": "#ffffff",
        "font_size": "0.9rem",
        "font_weight": "700",
        "white_space": "nowrap",
        "box_shadow": "0 0 18px rgba(20,184,166,0.3)",
    },
    ".customer-table-head, .customer-table-row": {
        "display": "grid",
        "grid_template_columns": "1.35fr 1fr 1.1fr 1.4fr 1.35fr 1.7fr",
        "gap": "1rem",
        "align_items": "center",
        "width": "100%",
        "box_sizing": "border-box",
        "min_width": "62rem",
    },
    ".customer-table-head": {
        "padding": "1rem 0 0.75rem",
        "border_bottom": "1px solid #17332f",
    },
    ".customer-table-row": {
        "padding": "0.75rem 0",
        "border_bottom": "1px solid #17332f",
    },
    ".customer-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.78rem",
        "font_weight": "700",
        "text_align": "left",
    },
    ".customer-table-cell": {
        "color": "#ffffff",
        "font_size": "0.82rem",
        "text_align": "left",
    },
    ".customer-name": {"font_weight": "500"},
    ".customer-edit-button": {
        "background": "transparent",
        "border": "1px solid #14b8a6",
        "color": "#ffffff",
        "padding": "0.4rem 0.8rem",
        "box_shadow": "none",
    },
    ".customer-remove-button": {
        "background": "#ef4b55",
        "border": "1px solid #ef4b55",
        "color": "#ffffff",
        "padding": "0.4rem 0.8rem",
        "box_shadow": "none",
    },
    ".stock-card": {
        "padding": "1.25rem 1.75rem",
        "border_radius": "1.35rem",
    },
    ".stock-table-head, .stock-table-row": {
        "display": "grid",
        "grid_template_columns": "1.55fr 1.1fr 0.65fr 0.65fr 0.75fr",
        "gap": "1rem",
        "align_items": "center",
        "min_width": "52rem",
    },
    ".stock-table-head": {
        "padding": "1rem 0 0.75rem",
        "border_bottom": "1px solid #17332f",
    },
    ".stock-table-row": {
        "padding": "0.8rem 0",
        "border_bottom": "1px solid #17332f",
    },
    ".stock-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.78rem",
        "font_weight": "700",
        "text_align": "center",
    },
    ".stock-table-cell": {
        "color": "#ffffff",
        "font_size": "0.82rem",
        "text_align": "center",
    },
    ".stock-product": {"font_weight": "500", "text_align": "center"},
    ".stock-value": {"font_weight": "700", "text_align": "center"},
    ".stock-critical": {
        "color": "#ff5a63",
        "font_weight": "700",
    },
    ".stock-status": {
        "justify_self": "center",
        "display": "inline-flex",
        "padding": "0.3rem 0.75rem",
        "border_radius": "999px",
        "font_size": "0.75rem",
        "font_weight": "700",
    },
    ".stock-status-success": {
        "color": "#34d399",
        "background": "rgba(16,185,129,0.12)",
        "border": "1px solid rgba(16,185,129,0.65)",
    },
    ".stock-status-danger": {
        "color": "#ff5a63",
        "background": "rgba(239,68,68,0.12)",
        "border": "1px solid rgba(239,68,68,0.65)",
    },
    ".strong": {"font_weight": "700", "color": "#ffffff"},
    ".status-badge": {
        "display": "inline-block",
        "padding": "0.2rem 0.65rem",
        "border_radius": "999px",
        "font_size": "0.72rem",
        "font_weight": "700",
        "white_space": "nowrap",
    },
    ".status-badge-success": {"background": "#d9f3e8", "color": "#0a6b4d"},
    ".status-badge-info": {"background": "#e4f0f8", "color": "#28607f"},
    ".status-badge-warning": {"background": "#fff0d6", "color": "#8a5a12"},
    ".status-badge-danger": {"background": "#fcebea", "color": "#a32d2d"},
    ".channel-badge": {
        "border": "1px solid",
        "padding": "0.35rem 0.75rem",
    },
    ".channel-badge-presencial": {
        "background": "rgba(143,176,171,0.12)",
        "border_color": "rgba(143,176,171,0.55)",
        "color": "#a9c5c0",
    },
    ".channel-badge-online": {
        "background": "rgba(34,211,238,0.12)",
        "border_color": "rgba(34,211,238,0.7)",
        "color": "#22d3ee",
    },
    ".supplier-table-head, .supplier-table-row": {
        "display": "grid",
        "grid_template_columns": "1.4fr 1fr 1.15fr 0.8fr 10rem",
        "gap": "0.8rem",
        "align_items": "center",
        "width": "100%",
        "box_sizing": "border-box",
        "min_width": "48rem",
    },
    ".supplier-table-head": {
        "padding": "0.6rem 0.5rem",
        "border_bottom": "1px solid #17332f",
    },
    ".supplier-table-row": {
        "padding": "0.8rem 0.5rem",
        "border_bottom": "1px solid #17332f",
    },
    ".supplier-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.75rem",
        "font_weight": "700",
    },
    ".supplier-deadline": {
        "color": "#e3e4d4",
        "font_size": "0.78rem",
        "white_space": "nowrap",
    },
    ".supplier-table-head > :nth-child(4), .supplier-table-row > :nth-child(4)": {
        "justify_self": "center",
        "text_align": "center",
    },
    ".supplier-table-head > :nth-child(5), .supplier-table-row > :nth-child(5)": {
        "justify_self": "center",
        "text_align": "center",
        "width": "100%",
        "justify_content": "center",
    },
    ".supplier-action-button": {
        "padding": "0.35rem 0.65rem",
        "font_size": "0.72rem",
        "white_space": "nowrap",
    },
    ".new-supplier-button": {
        "display": "inline-flex",
        "align_items": "center",
        "justify_content": "center",
        "padding": "0.7rem 1.25rem",
        "border_radius": "0.75rem",
        "background": "#0b8277",
        "color": "#ffffff",
        "font_size": "0.9rem",
        "font_weight": "700",
        "white_space": "nowrap",
        "box_shadow": "0 0 18px rgba(20,184,166,0.3)",
    },
    ".customer-table-head, .customer-table-row": {
        "display": "grid",
        "grid_template_columns": "1.35fr 1fr 1.1fr 1.4fr 1.35fr 1.7fr",
        "gap": "1rem",
        "align_items": "center",
        "width": "100%",
        "box_sizing": "border-box",
        "min_width": "62rem",
    },
    ".customer-table-head": {
        "padding": "1rem 0 0.75rem",
        "border_bottom": "1px solid #17332f",
    },
    ".customer-table-row": {
        "padding": "0.75rem 0",
        "border_bottom": "1px solid #17332f",
    },
    ".customer-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.78rem",
        "font_weight": "700",
        "text_align": "left",
    },
    ".customer-table-cell": {
        "color": "#ffffff",
        "font_size": "0.82rem",
        "text_align": "left",
    },
    ".customer-name": {"font_weight": "500"},
    ".customer-edit-button": {
        "background": "transparent",
        "border": "1px solid #14b8a6",
        "color": "#ffffff",
        "padding": "0.4rem 0.8rem",
        "box_shadow": "none",
    },
    ".customer-remove-button": {
        "background": "#ef4b55",
        "border": "1px solid #ef4b55",
        "color": "#ffffff",
        "padding": "0.4rem 0.8rem",
        "box_shadow": "none",
    },
    ".stock-card": {
        "padding": "1.25rem 1.75rem",
        "border_radius": "1.35rem",
    },
    ".stock-table-head, .stock-table-row": {
        "display": "grid",
        "grid_template_columns": "1.55fr 1.1fr 0.65fr 0.65fr 0.75fr",
        "gap": "1rem",
        "align_items": "center",
        "min_width": "52rem",
    },
    ".stock-table-head": {
        "padding": "1rem 0 0.75rem",
        "border_bottom": "1px solid #17332f",
    },
    ".stock-table-row": {
        "padding": "0.8rem 0",
        "border_bottom": "1px solid #17332f",
    },
    ".stock-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.78rem",
        "font_weight": "700",
        "text_align": "center",
    },
    ".stock-table-cell": {
        "color": "#ffffff",
        "font_size": "0.82rem",
        "text_align": "center",
    },
    ".stock-product": {"font_weight": "500", "text_align": "center"},
    ".stock-value": {"font_weight": "700", "text_align": "center"},
    ".stock-critical": {
        "color": "#ff5a63",
        "font_weight": "700",
    },
    ".stock-status": {
        "justify_self": "center",
        "display": "inline-flex",
        "padding": "0.3rem 0.75rem",
        "border_radius": "999px",
        "font_size": "0.75rem",
        "font_weight": "700",
    },
    ".stock-status-success": {
        "color": "#34d399",
        "background": "rgba(16,185,129,0.12)",
        "border": "1px solid rgba(16,185,129,0.65)",
    },
    ".stock-status-danger": {
        "color": "#ff5a63",
        "background": "rgba(239,68,68,0.12)",
        "border": "1px solid rgba(239,68,68,0.65)",
    },
    ".strong": {"font_weight": "700", "color": "#ffffff"},
    ".status-badge": {
        "display": "inline-block",
        "padding": "0.2rem 0.65rem",
        "border_radius": "999px",
        "font_size": "0.72rem",
        "font_weight": "700",
        "white_space": "nowrap",
    },
    ".status-badge-success": {"background": "#d9f3e8", "color": "#0a6b4d"},
    ".status-badge-info": {"background": "#e4f0f8", "color": "#28607f"},
    ".status-badge-warning": {"background": "#fff0d6", "color": "#8a5a12"},
    ".status-badge-danger": {"background": "#fcebea", "color": "#a32d2d"},
    ".channel-badge": {
        "border": "1px solid",
        "padding": "0.35rem 0.75rem",
    },
    ".channel-badge-presencial": {
        "background": "rgba(143,176,171,0.12)",
        "border_color": "rgba(143,176,171,0.55)",
        "color": "#a9c5c0",
    },
    ".channel-badge-online": {
        "background": "rgba(34,211,238,0.12)",
        "border_color": "rgba(34,211,238,0.7)",
        "color": "#22d3ee",
    },
    ".supplier-table-head, .supplier-table-row": {
        "display": "grid",
        "grid_template_columns": "1.4fr 1fr 1.15fr 0.8fr 10rem",
        "gap": "0.8rem",
        "align_items": "center",
        "width": "100%",
        "box_sizing": "border-box",
        "min_width": "48rem",
    },
    ".supplier-table-head": {
        "padding": "0.6rem 0.5rem",
        "border_bottom": "1px solid #17332f",
    },
    ".supplier-table-row": {
        "padding": "0.8rem 0.5rem",
        "border_bottom": "1px solid #17332f",
    },
    ".supplier-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.75rem",
        "font_weight": "700",
    },
    ".supplier-deadline": {
        "color": "#e3e4d4",
        "font_size": "0.78rem",
        "white_space": "nowrap",
    },
    ".supplier-table-head > :nth-child(4), .supplier-table-row > :nth-child(4)": {
        "justify_self": "center",
        "text_align": "center",
    },
    ".supplier-table-head > :nth-child(5), .supplier-table-row > :nth-child(5)": {
        "justify_self": "center",
        "text_align": "center",
        "width": "100%",
        "justify_content": "center",
    },
    ".supplier-action-button": {
        "padding": "0.35rem 0.65rem",
        "font_size": "0.72rem",
        "white_space": "nowrap",
    },
    ".new-supplier-button": {
        "display": "inline-flex",
        "align_items": "center",
        "justify_content": "center",
        "padding": "0.7rem 1.25rem",
        "border_radius": "0.75rem",
        "background": "#0b8277",
        "color": "#ffffff",
        "font_size": "0.9rem",
        "font_weight": "700",
        "white_space": "nowrap",
        "box_shadow": "0 0 18px rgba(20,184,166,0.3)",
    },
    ".customer-table-head, .customer-table-row": {
        "display": "grid",
        "grid_template_columns": "1.35fr 1fr 1.1fr 1.4fr 1.35fr 1.7fr",
        "gap": "1rem",
        "align_items": "center",
        "width": "100%",
        "box_sizing": "border-box",
        "min_width": "62rem",
    },
    ".customer-table-head": {
        "padding": "1rem 0 0.75rem",
        "border_bottom": "1px solid #17332f",
    },
    ".customer-table-row": {
        "padding": "0.75rem 0",
        "border_bottom": "1px solid #17332f",
    },
    ".customer-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.78rem",
        "font_weight": "700",
        "text_align": "left",
    },
    ".customer-table-cell": {
        "color": "#ffffff",
        "font_size": "0.82rem",
        "text_align": "left",
    },
    ".customer-name": {"font_weight": "500"},
    ".customer-edit-button": {
        "background": "transparent",
        "border": "1px solid #14b8a6",
        "color": "#ffffff",
        "padding": "0.4rem 0.8rem",
        "box_shadow": "none",
    },
    ".customer-remove-button": {
        "background": "#ef4b55",
        "border": "1px solid #ef4b55",
        "color": "#ffffff",
        "padding": "0.4rem 0.8rem",
        "box_shadow": "none",
    },
    ".stock-card": {
        "padding": "1.25rem 1.75rem",
        "border_radius": "1.35rem",
    },
    ".stock-table-head, .stock-table-row": {
        "display": "grid",
        "grid_template_columns": "1.55fr 1.1fr 0.65fr 0.65fr 0.75fr",
        "gap": "1rem",
        "align_items": "center",
        "min_width": "52rem",
    },
    ".stock-table-head": {
        "padding": "1rem 0 0.75rem",
        "border_bottom": "1px solid #17332f",
    },
    ".stock-table-row": {
        "padding": "0.8rem 0",
        "border_bottom": "1px solid #17332f",
    },
    ".stock-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.78rem",
        "font_weight": "700",
        "text_align": "center",
    },
    ".stock-table-cell": {
        "color": "#ffffff",
        "font_size": "0.82rem",
        "text_align": "center",
    },
    ".stock-product": {"font_weight": "500", "text_align": "center"},
    ".stock-value": {"font_weight": "700", "text_align": "center"},
    ".stock-critical": {
        "color": "#ff5a63",
        "font_weight": "700",
    },
    ".stock-status": {
        "justify_self": "center",
        "display": "inline-flex",
        "padding": "0.3rem 0.75rem",
        "border_radius": "999px",
        "font_size": "0.75rem",
        "font_weight": "700",
    },
    ".stock-status-success": {
        "color": "#34d399",
        "background": "rgba(16,185,129,0.12)",
        "border": "1px solid rgba(16,185,129,0.65)",
    },
    ".stock-status-danger": {
        "color": "#ff5a63",
        "background": "rgba(239,68,68,0.12)",
        "border": "1px solid rgba(239,68,68,0.65)",
    },
    ".strong": {"font_weight": "700", "color": "#ffffff"},
    ".status-badge": {
        "display": "inline-block",
        "padding": "0.2rem 0.65rem",
        "border_radius": "999px",
        "font_size": "0.72rem",
        "font_weight": "700",
        "white_space": "nowrap",
    },
    ".status-badge-success": {"background": "#d9f3e8", "color": "#0a6b4d"},
    ".status-badge-info": {"background": "#e4f0f8", "color": "#28607f"},
    ".status-badge-warning": {"background": "#fff0d6", "color": "#8a5a12"},
    ".status-badge-danger": {"background": "#fcebea", "color": "#a32d2d"},
    ".channel-badge": {
        "border": "1px solid",
        "padding": "0.35rem 0.75rem",
    },
    ".channel-badge-presencial": {
        "background": "rgba(143,176,171,0.12)",
        "border_color": "rgba(143,176,171,0.55)",
        "color": "#a9c5c0",
    },
    ".channel-badge-online": {
        "background": "rgba(34,211,238,0.12)",
        "border_color": "rgba(34,211,238,0.7)",
        "color": "#22d3ee",
    },
    ".supplier-table-head, .supplier-table-row": {
        "display": "grid",
        "grid_template_columns": "1.4fr 1fr 1.15fr 0.8fr 10rem",
        "gap": "0.8rem",
        "align_items": "center",
        "width": "100%",
        "box_sizing": "border-box",
        "min_width": "48rem",
    },
    ".supplier-table-head": {
        "padding": "0.6rem 0.5rem",
        "border_bottom": "1px solid #17332f",
    },
    ".supplier-table-row": {
        "padding": "0.8rem 0.5rem",
        "border_bottom": "1px solid #17332f",
    },
    ".supplier-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.75rem",
        "font_weight": "700",
    },
    ".supplier-deadline": {
        "color": "#e3e4d4",
        "font_size": "0.78rem",
        "white_space": "nowrap",
    },
    ".supplier-table-head > :nth-child(4), .supplier-table-row > :nth-child(4)": {
        "justify_self": "center",
        "text_align": "center",
    },
    ".supplier-table-head > :nth-child(5), .supplier-table-row > :nth-child(5)": {
        "justify_self": "center",
        "text_align": "center",
        "width": "100%",
        "justify_content": "center",
    },
    ".supplier-action-button": {
        "padding": "0.35rem 0.65rem",
        "font_size": "0.72rem",
        "white_space": "nowrap",
    },
    ".new-supplier-button": {
        "display": "inline-flex",
        "align_items": "center",
        "justify_content": "center",
        "padding": "0.7rem 1.25rem",
        "border_radius": "0.75rem",
        "background": "#0b8277",
        "color": "#ffffff",
        "font_size": "0.9rem",
        "font_weight": "700",
        "white_space": "nowrap",
        "box_shadow": "0 0 18px rgba(20,184,166,0.3)",
    },
    ".customer-table-head, .customer-table-row": {
        "display": "grid",
        "grid_template_columns": "1.35fr 1fr 1.1fr 1.4fr 1.35fr 1.7fr",
        "gap": "1rem",
        "align_items": "center",
        "width": "100%",
        "box_sizing": "border-box",
        "min_width": "62rem",
    },
    ".customer-table-head": {
        "padding": "1rem 0 0.75rem",
        "border_bottom": "1px solid #17332f",
    },
    ".customer-table-row": {
        "padding": "0.75rem 0",
        "border_bottom": "1px solid #17332f",
    },
    ".customer-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.78rem",
        "font_weight": "700",
        "text_align": "left",
    },
    ".customer-table-cell": {
        "color": "#ffffff",
        "font_size": "0.82rem",
        "text_align": "left",
    },
    ".customer-name": {"font_weight": "500"},
    ".customer-edit-button": {
        "background": "transparent",
        "border": "1px solid #14b8a6",
        "color": "#ffffff",
        "padding": "0.4rem 0.8rem",
        "box_shadow": "none",
    },
    ".customer-remove-button": {
        "background": "#ef4b55",
        "border": "1px solid #ef4b55",
        "color": "#ffffff",
        "padding": "0.4rem 0.8rem",
        "box_shadow": "none",
    },
    ".stock-card": {
        "padding": "1.25rem 1.75rem",
        "border_radius": "1.35rem",
    },
    ".stock-table-head, .stock-table-row": {
        "display": "grid",
        "grid_template_columns": "1.55fr 1.1fr 0.65fr 0.65fr 0.75fr",
        "gap": "1rem",
        "align_items": "center",
        "min_width": "52rem",
    },
    ".stock-table-head": {
        "padding": "1rem 0 0.75rem",
        "border_bottom": "1px solid #17332f",
    },
    ".stock-table-row": {
        "padding": "0.8rem 0",
        "border_bottom": "1px solid #17332f",
    },
    ".stock-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.78rem",
        "font_weight": "700",
        "text_align": "center",
    },
    ".stock-table-cell": {
        "color": "#ffffff",
        "font_size": "0.82rem",
        "text_align": "center",
    },
    ".stock-product": {"font_weight": "500", "text_align": "center"},
    ".stock-value": {"font_weight": "700", "text_align": "center"},
    ".stock-critical": {
        "color": "#ff5a63",
        "font_weight": "700",
    },
    ".stock-status": {
        "justify_self": "center",
        "display": "inline-flex",
        "padding": "0.3rem 0.75rem",
        "border_radius": "999px",
        "font_size": "0.75rem",
        "font_weight": "700",
    },
    ".stock-status-success": {
        "color": "#34d399",
        "background": "rgba(16,185,129,0.12)",
        "border": "1px solid rgba(16,185,129,0.65)",
    },
    ".stock-status-danger": {
        "color": "#ff5a63",
        "background": "rgba(239,68,68,0.12)",
        "border": "1px solid rgba(239,68,68,0.65)",
    },
    ".strong": {"font_weight": "700", "color": "#ffffff"},
    ".status-badge": {
        "display": "inline-block",
        "padding": "0.2rem 0.65rem",
        "border_radius": "999px",
        "font_size": "0.72rem",
        "font_weight": "700",
        "white_space": "nowrap",
    },
    ".status-badge-success": {"background": "#d9f3e8", "color": "#0a6b4d"},
    ".status-badge-info": {"background": "#e4f0f8", "color": "#28607f"},
    ".status-badge-warning": {"background": "#fff0d6", "color": "#8a5a12"},
    ".status-badge-danger": {"background": "#fcebea", "color": "#a32d2d"},
    ".channel-badge": {
        "border": "1px solid",
        "padding": "0.35rem 0.75rem",
    },
    ".channel-badge-presencial": {
        "background": "rgba(143,176,171,0.12)",
        "border_color": "rgba(143,176,171,0.55)",
        "color": "#a9c5c0",
    },
    ".channel-badge-online": {
        "background": "rgba(34,211,238,0.12)",
        "border_color": "rgba(34,211,238,0.7)",
        "color": "#22d3ee",
    },
    ".supplier-table-head, .supplier-table-row": {
        "display": "grid",
        "grid_template_columns": "1.4fr 1fr 1.15fr 0.8fr 10rem",
        "gap": "0.8rem",
        "align_items": "center",
        "width": "100%",
        "box_sizing": "border-box",
        "min_width": "48rem",
    },
    ".supplier-table-head": {
        "padding": "0.6rem 0.5rem",
        "border_bottom": "1px solid #17332f",
    },
    ".supplier-table-row": {
        "padding": "0.8rem 0.5rem",
        "border_bottom": "1px solid #17332f",
    },
    ".supplier-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.75rem",
        "font_weight": "700",
    },
    ".supplier-deadline": {
        "color": "#e3e4d4",
        "font_size": "0.78rem",
        "white_space": "nowrap",
    },
    ".supplier-table-head > :nth-child(4), .supplier-table-row > :nth-child(4)": {
        "justify_self": "center",
        "text_align": "center",
    },
    ".supplier-table-head > :nth-child(5), .supplier-table-row > :nth-child(5)": {
        "justify_self": "center",
        "text_align": "center",
        "width": "100%",
        "justify_content": "center",
    },
    ".supplier-action-button": {
        "padding": "0.35rem 0.65rem",
        "font_size": "0.72rem",
        "white_space": "nowrap",
    },
    ".new-supplier-button": {
        "display": "inline-flex",
        "align_items": "center",
        "justify_content": "center",
        "padding": "0.7rem 1.25rem",
        "border_radius": "0.75rem",
        "background": "#0b8277",
        "color": "#ffffff",
        "font_size": "0.9rem",
        "font_weight": "700",
        "white_space": "nowrap",
        "box_shadow": "0 0 18px rgba(20,184,166,0.3)",
    },
    ".customer-table-head, .customer-table-row": {
        "display": "grid",
        "grid_template_columns": "1.35fr 1fr 1.1fr 1.4fr 1.35fr 1.7fr",
        "gap": "1rem",
        "align_items": "center",
        "width": "100%",
        "box_sizing": "border-box",
        "min_width": "62rem",
    },
    ".customer-table-head": {
        "padding": "1rem 0 0.75rem",
        "border_bottom": "1px solid #17332f",
    },
    ".customer-table-row": {
        "padding": "0.75rem 0",
        "border_bottom": "1px solid #17332f",
    },
    ".customer-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.78rem",
        "font_weight": "700",
        "text_align": "left",
    },
    ".customer-table-cell": {
        "color": "#ffffff",
        "font_size": "0.82rem",
        "text_align": "left",
    },
    ".customer-name": {"font_weight": "500"},
    ".customer-edit-button": {
        "background": "transparent",
        "border": "1px solid #14b8a6",
        "color": "#ffffff",
        "padding": "0.4rem 0.8rem",
        "box_shadow": "none",
    },
    ".customer-remove-button": {
        "background": "#ef4b55",
        "border": "1px solid #ef4b55",
        "color": "#ffffff",
        "padding": "0.4rem 0.8rem",
        "box_shadow": "none",
    },
    ".stock-card": {
        "padding": "1.25rem 1.75rem",
        "border_radius": "1.35rem",
    },
    ".stock-table-head, .stock-table-row": {
        "display": "grid",
        "grid_template_columns": "1.55fr 1.1fr 0.65fr 0.65fr 0.75fr",
        "gap": "1rem",
        "align_items": "center",
        "min_width": "52rem",
    },
    ".stock-table-head": {
        "padding": "1rem 0 0.75rem",
        "border_bottom": "1px solid #17332f",
    },
    ".stock-table-row": {
        "padding": "0.8rem 0",
        "border_bottom": "1px solid #17332f",
    },
    ".stock-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.78rem",
        "font_weight": "700",
        "text_align": "center",
    },
    ".stock-table-cell": {
        "color": "#ffffff",
        "font_size": "0.82rem",
        "text_align": "center",
    },
    ".stock-product": {"font_weight": "500", "text_align": "center"},
    ".stock-value": {"font_weight": "700", "text_align": "center"},
    ".stock-critical": {
        "color": "#ff5a63",
        "font_weight": "700",
    },
    ".stock-status": {
        "justify_self": "center",
        "display": "inline-flex",
        "padding": "0.3rem 0.75rem",
        "border_radius": "999px",
        "font_size": "0.75rem",
        "font_weight": "700",
    },
    ".stock-status-success": {
        "color": "#34d399",
        "background": "rgba(16,185,129,0.12)",
        "border": "1px solid rgba(16,185,129,0.65)",
    },
    ".stock-status-danger": {
        "color": "#ff5a63",
        "background": "rgba(239,68,68,0.12)",
        "border": "1px solid rgba(239,68,68,0.65)",
    },
    ".strong": {"font_weight": "700", "color": "#ffffff"},
    ".status-badge": {
        "display": "inline-block",
        "padding": "0.2rem 0.65rem",
        "border_radius": "999px",
        "font_size": "0.72rem",
        "font_weight": "700",
        "white_space": "nowrap",
    },
    ".status-badge-success": {"background": "#d9f3e8", "color": "#0a6b4d"},
    ".status-badge-info": {"background": "#e4f0f8", "color": "#28607f"},
    ".status-badge-warning": {"background": "#fff0d6", "color": "#8a5a12"},
    ".status-badge-danger": {"background": "#fcebea", "color": "#a32d2d"},
    ".channel-badge": {
        "border": "1px solid",
        "padding": "0.35rem 0.75rem",
    },
    ".channel-badge-presencial": {
        "background": "rgba(143,176,171,0.12)",
        "border_color": "rgba(143,176,171,0.55)",
        "color": "#a9c5c0",
    },
    ".channel-badge-online": {
        "background": "rgba(34,211,238,0.12)",
        "border_color": "rgba(34,211,238,0.7)",
        "color": "#22d3ee",
    },
    ".supplier-table-head, .supplier-table-row": {
        "display": "grid",
        "grid_template_columns": "1.4fr 1fr 1.15fr 0.8fr 10rem",
        "gap": "0.8rem",
        "align_items": "center",
        "width": "100%",
        "box_sizing": "border-box",
        "min_width": "48rem",
    },
    ".supplier-table-head": {
        "padding": "0.6rem 0.5rem",
        "border_bottom": "1px solid #17332f",
    },
    ".supplier-table-row": {
        "padding": "0.8rem 0.5rem",
        "border_bottom": "1px solid #17332f",
    },
    ".supplier-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.75rem",
        "font_weight": "700",
    },
    ".supplier-deadline": {
        "color": "#e3e4d4",
        "font_size": "0.78rem",
        "white_space": "nowrap",
    },
    ".supplier-table-head > :nth-child(4), .supplier-table-row > :nth-child(4)": {
        "justify_self": "center",
        "text_align": "center",
    },
    ".supplier-table-head > :nth-child(5), .supplier-table-row > :nth-child(5)": {
        "justify_self": "center",
        "text_align": "center",
        "width": "100%",
        "justify_content": "center",
    },
    ".supplier-action-button": {
        "padding": "0.35rem 0.65rem",
        "font_size": "0.72rem",
        "white_space": "nowrap",
    },
    ".new-supplier-button": {
        "display": "inline-flex",
        "align_items": "center",
        "justify_content": "center",
        "padding": "0.7rem 1.25rem",
        "border_radius": "0.75rem",
        "background": "#0b8277",
        "color": "#ffffff",
        "font_size": "0.9rem",
        "font_weight": "700",
        "white_space": "nowrap",
        "box_shadow": "0 0 18px rgba(20,184,166,0.3)",
    },
    ".customer-table-head, .customer-table-row": {
        "display": "grid",
        "grid_template_columns": "1.35fr 1fr 1.1fr 1.4fr 1.35fr 1.7fr",
        "gap": "1rem",
        "align_items": "center",
        "width": "100%",
        "box_sizing": "border-box",
        "min_width": "62rem",
    },
    ".customer-table-head": {
        "padding": "1rem 0 0.75rem",
        "border_bottom": "1px solid #17332f",
    },
    ".customer-table-row": {
        "padding": "0.75rem 0",
        "border_bottom": "1px solid #17332f",
    },
    ".customer-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.78rem",
        "font_weight": "700",
        "text_align": "left",
    },
    ".customer-table-cell": {
        "color": "#ffffff",
        "font_size": "0.82rem",
        "text_align": "left",
    },
    ".customer-name": {"font_weight": "500"},
    ".customer-edit-button": {
        "background": "transparent",
        "border": "1px solid #14b8a6",
        "color": "#ffffff",
        "padding": "0.4rem 0.8rem",
        "box_shadow": "none",
    },
    ".customer-remove-button": {
        "background": "#ef4b55",
        "border": "1px solid #ef4b55",
        "color": "#ffffff",
        "padding": "0.4rem 0.8rem",
        "box_shadow": "none",
    },
    ".stock-card": {
        "padding": "1.25rem 1.75rem",
        "border_radius": "1.35rem",
    },
    ".stock-table-head, .stock-table-row": {
        "display": "grid",
        "grid_template_columns": "1.55fr 1.1fr 0.65fr 0.65fr 0.75fr",
        "gap": "1rem",
        "align_items": "center",
        "min_width": "52rem",
    },
    ".stock-table-head": {
        "padding": "1rem 0 0.75rem",
        "border_bottom": "1px solid #17332f",
    },
    ".stock-table-row": {
        "padding": "0.8rem 0",
        "border_bottom": "1px solid #17332f",
    },
    ".stock-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.78rem",
        "font_weight": "700",
        "text_align": "center",
    },
    ".stock-table-cell": {
        "color": "#ffffff",
        "font_size": "0.82rem",
        "text_align": "center",
    },
    ".stock-product": {"font_weight": "500", "text_align": "center"},
    ".stock-value": {"font_weight": "700", "text_align": "center"},
    ".stock-critical": {
        "color": "#ff5a63",
        "font_weight": "700",
    },
    ".stock-status": {
        "justify_self": "center",
        "display": "inline-flex",
        "padding": "0.3rem 0.75rem",
        "border_radius": "999px",
        "font_size": "0.75rem",
        "font_weight": "700",
    },
    ".stock-status-success": {
        "color": "#34d399",
        "background": "rgba(16,185,129,0.12)",
        "border": "1px solid rgba(16,185,129,0.65)",
    },
    ".stock-status-danger": {
        "color": "#ff5a63",
        "background": "rgba(239,68,68,0.12)",
        "border": "1px solid rgba(239,68,68,0.65)",
    },
    ".strong": {"font_weight": "700", "color": "#ffffff"},
    ".status-badge": {
        "display": "inline-block",
        "padding": "0.2rem 0.65rem",
        "border_radius": "999px",
        "font_size": "0.72rem",
        "font_weight": "700",
        "white_space": "nowrap",
    },
    ".status-badge-success": {"background": "#d9f3e8", "color": "#0a6b4d"},
    ".status-badge-info": {"background": "#e4f0f8", "color": "#28607f"},
    ".status-badge-warning": {"background": "#fff0d6", "color": "#8a5a12"},
    ".status-badge-danger": {"background": "#fcebea", "color": "#a32d2d"},
    ".channel-badge": {
        "border": "1px solid",
        "padding": "0.35rem 0.75rem",
    },
    ".channel-badge-presencial": {
        "background": "rgba(143,176,171,0.12)",
        "border_color": "rgba(143,176,171,0.55)",
        "color": "#a9c5c0",
    },
    ".channel-badge-online": {
        "background": "rgba(34,211,238,0.12)",
        "border_color": "rgba(34,211,238,0.7)",
        "color": "#22d3ee",
    },
    ".supplier-table-head, .supplier-table-row": {
        "display": "grid",
        "grid_template_columns": "1.4fr 1fr 1.15fr 0.8fr 10rem",
        "gap": "0.8rem",
        "align_items": "center",
        "width": "100%",
        "box_sizing": "border-box",
        "min_width": "48rem",
    },
    ".supplier-table-head": {
        "padding": "0.6rem 0.5rem",
        "border_bottom": "1px solid #17332f",
    },
    ".supplier-table-row": {
        "padding": "0.8rem 0.5rem",
        "border_bottom": "1px solid #17332f",
    },
    ".supplier-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.75rem",
        "font_weight": "700",
    },
    ".supplier-deadline": {
        "color": "#e3e4d4",
        "font_size": "0.78rem",
        "white_space": "nowrap",
    },
    ".supplier-table-head > :nth-child(4), .supplier-table-row > :nth-child(4)": {
        "justify_self": "center",
        "text_align": "center",
    },
    ".supplier-table-head > :nth-child(5), .supplier-table-row > :nth-child(5)": {
        "justify_self": "center",
        "text_align": "center",
        "width": "100%",
        "justify_content": "center",
    },
    ".supplier-action-button": {
        "padding": "0.35rem 0.65rem",
        "font_size": "0.72rem",
        "white_space": "nowrap",
    },
    ".new-supplier-button": {
        "display": "inline-flex",
        "align_items": "center",
        "justify_content": "center",
        "padding": "0.7rem 1.25rem",
        "border_radius": "0.75rem",
        "background": "#0b8277",
        "color": "#ffffff",
        "font_size": "0.9rem",
        "font_weight": "700",
        "white_space": "nowrap",
        "box_shadow": "0 0 18px rgba(20,184,166,0.3)",
    },
    ".customer-table-head, .customer-table-row": {
        "display": "grid",
        "grid_template_columns": "1.35fr 1fr 1.1fr 1.4fr 1.35fr 1.7fr",
        "gap": "1rem",
        "align_items": "center",
        "width": "100%",
        "box_sizing": "border-box",
        "min_width": "62rem",
    },
    ".customer-table-head": {
        "padding": "1rem 0 0.75rem",
        "border_bottom": "1px solid #17332f",
    },
    ".customer-table-row": {
        "padding": "0.75rem 0",
        "border_bottom": "1px solid #17332f",
    },
    ".customer-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.78rem",
        "font_weight": "700",
        "text_align": "left",
    },
    ".customer-table-cell": {
        "color": "#ffffff",
        "font_size": "0.82rem",
        "text_align": "left",
    },
    ".customer-name": {"font_weight": "500"},
    ".customer-edit-button": {
        "background": "transparent",
        "border": "1px solid #14b8a6",
        "color": "#ffffff",
        "padding": "0.4rem 0.8rem",
        "box_shadow": "none",
    },
    ".customer-remove-button": {
        "background": "#ef4b55",
        "border": "1px solid #ef4b55",
        "color": "#ffffff",
        "padding": "0.4rem 0.8rem",
        "box_shadow": "none",
    },
    ".stock-card": {
        "padding": "1.25rem 1.75rem",
        "border_radius": "1.35rem",
    },
    ".stock-table-head, .stock-table-row": {
        "display": "grid",
        "grid_template_columns": "1.55fr 1.1fr 0.65fr 0.65fr 0.75fr",
        "gap": "1rem",
        "align_items": "center",
        "min_width": "52rem",
    },
    ".stock-table-head": {
        "padding": "1rem 0 0.75rem",
        "border_bottom": "1px solid #17332f",
    },
    ".stock-table-row": {
        "padding": "0.8rem 0",
        "border_bottom": "1px solid #17332f",
    },
    ".stock-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.78rem",
        "font_weight": "700",
        "text_align": "center",
    },
    ".stock-table-cell": {
        "color": "#ffffff",
        "font_size": "0.82rem",
        "text_align": "center",
    },
    ".stock-product": {"font_weight": "500", "text_align": "center"},
    ".stock-value": {"font_weight": "700", "text_align": "center"},
    ".stock-critical": {
        "color": "#ff5a63",
        "font_weight": "700",
    },
    ".stock-status": {
        "justify_self": "center",
        "display": "inline-flex",
        "padding": "0.3rem 0.75rem",
        "border_radius": "999px",
        "font_size": "0.75rem",
        "font_weight": "700",
    },
    ".stock-status-success": {
        "color": "#34d399",
        "background": "rgba(16,185,129,0.12)",
        "border": "1px solid rgba(16,185,129,0.65)",
    },
    ".stock-status-danger": {
        "color": "#ff5a63",
        "background": "rgba(239,68,68,0.12)",
        "border": "1px solid rgba(239,68,68,0.65)",
    },
    ".strong": {"font_weight": "700", "color": "#ffffff"},
    ".status-badge": {
        "display": "inline-block",
        "padding": "0.2rem 0.65rem",
        "border_radius": "999px",
        "font_size": "0.72rem",
        "font_weight": "700",
        "white_space": "nowrap",
    },
    ".status-badge-success": {"background": "#d9f3e8", "color": "#0a6b4d"},
    ".status-badge-info": {"background": "#e4f0f8", "color": "#28607f"},
    ".status-badge-warning": {"background": "#fff0d6", "color": "#8a5a12"},
    ".status-badge-danger": {"background": "#fcebea", "color": "#a32d2d"},
    ".channel-badge": {
        "border": "1px solid",
        "padding": "0.35rem 0.75rem",
    },
    ".channel-badge-presencial": {
        "background": "rgba(143,176,171,0.12)",
        "border_color": "rgba(143,176,171,0.55)",
        "color": "#a9c5c0",
    },
    ".channel-badge-online": {
        "background": "rgba(34,211,238,0.12)",
        "border_color": "rgba(34,211,238,0.7)",
        "color": "#22d3ee",
    },
    ".supplier-table-head, .supplier-table-row": {
        "display": "grid",
        "grid_template_columns": "1.4fr 1fr 1.15fr 0.8fr 10rem",
        "gap": "0.8rem",
        "align_items": "center",
        "width": "100%",
        "box_sizing": "border-box",
        "min_width": "48rem",
    },
    ".supplier-table-head": {
        "padding": "0.6rem 0.5rem",
        "border_bottom": "1px solid #17332f",
    },
    ".supplier-table-row": {
        "padding": "0.8rem 0.5rem",
        "border_bottom": "1px solid #17332f",
    },
    ".supplier-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.75rem",
        "font_weight": "700",
    },
    ".supplier-deadline": {
        "color": "#e3e4d4",
        "font_size": "0.78rem",
        "white_space": "nowrap",
    },
    ".supplier-table-head > :nth-child(4), .supplier-table-row > :nth-child(4)": {
        "justify_self": "center",
        "text_align": "center",
    },
    ".customer-table-heading": {
        "color": "#8fb0ab",
        "font_size": "0.78rem",
        "font_weight": "700",
        "text_align": "center",
    },
    ".customer-table-cell": {
        "color": "#ffffff",
        "font_size": "0.82rem",
        "text_align": "center",
    },
    ".customer-table-head > *, .customer-table-row > *": {
        "justify_self": "center",
        "text_align": "center",
    },
    ".customer-table-head-readonly, .customer-table-row-readonly": {
        "grid_template_columns": "1.35fr 1fr 1.1fr 1.4fr 1.35fr",
    },
}

app = rx.App(style=GLOBAL_STYLE)
app.add_page(login_page, route="/", title="FarmaGestão")
app.add_page(login_page, route="/login", title="Entrar | FarmaGestão")
app.add_page(
    dashboard_page,
    route="/dashboard",
    title="Visão geral | FarmaGestão",
    on_load=State.load_dashboard,
)
app.add_page(
    sales_page,
    route="/vendas",
    title="Vendas | FarmaGestão",
    on_load=State.load_sales,
)
app.add_page(
    stock_page,
    route="/estoque",
    title="Estoque | FarmaGestão",
    on_load=State.load_products,
)
app.add_page(
    products_page,
    route="/produtos",
    title="Produtos | FarmaGestão",
    on_load=State.load_products,
)
app.add_page(
    customers_page,
    route="/clientes",
    title="Clientes | FarmaGestão",
    on_load=State.load_customers,
)
app.add_page(
    employees_page,
    route="/equipe",
    title="Equipe | FarmaGestão",
    on_load=State.load_employees,
)
app.add_page(
    suppliers_page,
    route="/fornecedores",
    title="Fornecedores | FarmaGestão",
    on_load=State.load_suppliers,
)
app.add_page(
    account_page,
    route="/minha-conta",
    title="Minha conta | FarmaGestão",
    on_load=State.load_session,
)
app.add_page(
    attendance_page,
    route="/atendimento",
    title="Atendimento | FarmaGestão",
    on_load=State.load_products,
)
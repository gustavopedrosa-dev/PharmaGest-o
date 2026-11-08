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
    dashboard_funcionarios_ativos: int = 0
    dashboard_estoque_critico: list[dict[str, object]] = []
    dashboard_mais_vendidos: list[dict[str, object]] = []
    dashboard_carregado: bool = False
    acesso_inicial: dict[str, str] = {}
    confirmando_inativacao: bool = False
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
    categoria_nome: str = ""
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
    cliente_data_nascimento: str = "1990-01-01"
    cliente_telefone: str = ""
    cliente_email: str = ""
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
    funcionario_cargo: str = ""
    funcionario_salario: str = ""
    funcionario_login: str = ""
    fornecedor_id: str = ""
    fornecedor_nome: str = ""
    fornecedor_cnpj: str = ""
    fornecedor_telefone: str = ""
    fornecedor_email: str = ""
    fornecedor_endereco: str = ""
    fornecedor_prazo_entrega: str = ""

    @rx.var
    def is_gestor(self) -> bool:
        return self.perfil_acesso == "gestor"

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

    def set_product_id(self, value: str) -> None:
        self.produto_id = value

    def set_categoria_id(self, value: str) -> None:
        self.categoria_id = value

    def set_categoria_nome(self, value: str) -> None:
        self.categoria_nome = value

    def set_sale_field(self, field: str, value: str) -> None:
        setattr(self, field, value)

    def set_customer_field(self, field: str, value: str) -> None:
        setattr(self, field, value)

    def set_address_field(self, field: str, value: str) -> None:
        setattr(self, field, value)

    def set_employee_field(self, field: str, value: str) -> None:
        setattr(self, field, value)

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
        self.venda_itens = [
            *self.venda_itens,
            {
                "id_produto": str(product_id),
                "quantidade": str(quantity),
            },
        ]
        self.venda_produto_id = ""
        self.venda_quantidade = "1"
        self.mensagem = ""

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
            self._clear_dashboard()
            self.mensagem = FORBIDDEN_MESSAGE
            return rx.redirect("/minha-conta")
        self.dashboard_carregado = False
        self.mensagem = ""
        try:
            agora = datetime.now().astimezone()
            data_inicio = agora.replace(hour=0, minute=0, second=0, microsecond=0)
            data_fim = data_inicio + timedelta(days=1)
            summary = XanoClient().dashboard_summary(
                self._token,
                data_inicio=data_inicio,
                data_fim=data_fim,
            )
            self.dashboard_total_vendas = int(summary.get("total_vendas", 0) or 0)
            self.dashboard_valor_total = float(summary.get("valor_total", 0) or 0)
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
    def load_products(self) -> rx.event.EventSpec | None:
        redirect = self.load_session()
        if redirect is not None:
            return redirect
        try:
            client = XanoClient()
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
        redirect = self.load_session()
        if redirect is not None:
            return redirect
        if not self.is_gestor:
            self.mensagem = FORBIDDEN_MESSAGE
            return rx.redirect("/minha-conta")
        try:
            self._set_suppliers(XanoClient().list_suppliers(self._token))
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
        redirect = self.load_session()
        if redirect is not None:
            return redirect
        try:
            self._set_customers(XanoClient().list_customers(self._token))
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
    def load_employees(self) -> rx.event.EventSpec | None:
        redirect = self.load_session()
        if redirect is not None:
            return redirect
        if not self.is_gestor:
            self.mensagem = FORBIDDEN_MESSAGE
            return rx.redirect("/minha-conta")
        try:
            self._set_employees(XanoClient().list_employees(self._token))
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
        try:
            employee, access = XanoClient().create_employee(
                self._token,
                self._employee_payload(include_login=True),
            )
            self.funcionarios = [*self.funcionarios, self._employee_view(employee)]
            self.acesso_inicial = access
            self.mensagem = "Funcionário cadastrado. Guarde a senha inicial exibida."
            self._clear_employee_form()
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
        try:
            employee_id = int(self.funcionario_id)
            employee = XanoClient().update_employee(
                self._token,
                employee_id,
                self._employee_payload(include_login=False),
            )
            self.funcionarios = [
                self._employee_view(employee)
                if item["id"] == str(employee_id)
                else item
                for item in self.funcionarios
            ]
            self.mensagem = "Funcionário atualizado."
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
            employee = XanoClient().deactivate_employee(self._token, employee_id)
            self.funcionarios = [
                self._employee_view(employee)
                if item["id"] == str(employee_id)
                else item
                for item in self.funcionarios
            ]
            self.mensagem = "Funcionário inativado."
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
        try:
            customer = XanoClient().create_customer(
                self._token,
                self._customer_payload(),
            )
            self.clientes = [*self.clientes, self._customer_view(customer)]
            self.cliente_id = str(customer.id)
            self.mensagem = "Cliente cadastrado."
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
    def update_customer(self) -> None:
        if self.is_gestor:
            self.mensagem = FORBIDDEN_MESSAGE
            return
        try:
            customer_id = int(self.cliente_id)
            customer = XanoClient().update_customer(
                self._token,
                customer_id,
                self._customer_payload(),
            )
            self.clientes = [
                self._customer_view(customer)
                if item["id"] == str(customer_id)
                else item
                for item in self.clientes
            ]
            self.mensagem = "Cliente atualizado."
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

    @rx.event
    def deactivate_customer(self) -> None:
        if self.is_gestor:
            self.mensagem = FORBIDDEN_MESSAGE
            return
        try:
            customer_id = int(self.cliente_id)
            customer = XanoClient().deactivate_customer(self._token, customer_id)
            self.clientes = [
                self._customer_view(customer)
                if item["id"] == str(customer_id)
                else item
                for item in self.clientes
            ]
            self.mensagem = "Cliente inativado."
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
        redirect = self.load_session()
        if redirect is not None:
            return redirect
        try:
            client = XanoClient()
            sales, payments = client.list_sale_history(
                self._token,
                is_gestor=self.is_gestor,
            )
            orders, items = client.list_orders(self._token, is_gestor=self.is_gestor)
            orders_by_id = {order.id: order for order in orders}
            items_by_order: dict[int, list[str]] = {}
            for item in items:
                items_by_order.setdefault(int(item["id_pedido"]), []).append(
                    f'{item["quantidade"]}x Produto {item["id_produto"]}'
                )
            payments_by_sale = {
                int(payment["id_venda"]): str(payment.get("forma_pagamento") or "")
                for payment in payments
            }
            self.vendas = [
                {
                    "id": str(sale.id),
                    "pedido": str(sale.id_pedido),
                    "total": f"{sale.valor_total:.2f}",
                    "status": sale.status,
                    "data": sale.data_venda,
                    "cliente": str(
                        orders_by_id.get(sale.id_pedido).id_cliente
                        or "balcão"
                    )
                    if sale.id_pedido in orders_by_id
                    else "balcão",
                    "produtos": ", ".join(
                        items_by_order.get(sale.id_pedido, [])
                    )
                    or "—",
                    "canal": orders_by_id.get(sale.id_pedido).canal
                    if sale.id_pedido in orders_by_id
                    else "",
                    "atendente": str(orders_by_id.get(sale.id_pedido).id_funcionario)
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
    def update_product(self) -> None:
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
            "cpf": self.cliente_cpf or None,
            "data_nascimento": self.cliente_data_nascimento,
            "telefone": self.cliente_telefone or None,
            "email": self.cliente_email or None,
        }

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
            "salario": float(self.funcionario_salario)
            if self.funcionario_salario.strip()
            else None,
        }
        if include_login:
            payload["login"] = self.funcionario_login
        return payload

    def _clear_employee_form(self) -> None:
        self.funcionario_id = ""
        self.funcionario_nome = ""
        self.funcionario_cpf = ""
        self.funcionario_data_nascimento = ""
        self.funcionario_telefone = ""
        self.funcionario_email = ""
        self.funcionario_cargo = ""
        self.funcionario_salario = ""
        self.funcionario_login = ""

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

    def _set_customers(self, customers: list[Customer]) -> None:
        self.clientes = [self._customer_view(customer) for customer in customers]

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
    def _employee_view(employee: Employee) -> dict[str, str]:
        return {
            "id": str(employee.id),
            "nome": employee.nome,
            "cpf": employee.cpf,
            "cargo": employee.cargo,
            "salario": (
                f"R$ {employee.salario:.2f}"
                if employee.salario is not None
                else ""
            ),
            "email": employee.email,
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
            "categoria": str(product.id_categoria),
            "estoque": str(product.quantidade_estoque),
            "minimo": str(product.estoque_minimo),
            "preco": f"R$ {product.preco_venda:.2f}",
            "situacao": (
                "repor"
                if product.quantidade_estoque < product.estoque_minimo
                else "regular"
            ),
        }

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
        rx.box(rx.text(State.mensagem), class_name="feedback feedback-error"),
        rx.fragment(),
    )


def page_header(title: str, description: str = "") -> rx.Component:
    return rx.vstack(
        rx.heading(title, size="7", class_name="page-title"),
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


def section_heading(title: str, description: str = "") -> rx.Component:
    return rx.vstack(
        rx.heading(title, size="5"),
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
                    navigation_tab("Atendimento", "/atendimento"),
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
                                    rx.text("Faturamento hoje", class_name="muted"),
                                    rx.text(
                                        f"R$ {State.dashboard_valor_total:.2f}",
                                        class_name="stat-card-number",
                                    ),
                                ),
                                class_name="stat-card",
                            ),
                            rx.box(
                                rx.vstack(
                                    rx.text("Vendas hoje", class_name="muted"),
                                    rx.text(
                                        State.dashboard_total_vendas,
                                        class_name="stat-card-number",
                                    ),
                                ),
                                class_name="stat-card",
                            ),
                            rx.box(
                                rx.vstack(
                                    rx.text(
                                        "Produtos abaixo do mínimo",
                                        class_name="muted",
                                    ),
                                    rx.text(
                                        State.dashboard_estoque_critico.length(),
                                        class_name="stat-card-number",
                                    ),
                                ),
                                class_name="stat-card",
                            ),
                            rx.box(
                                rx.vstack(
                                    rx.text("Funcionários ativos", class_name="muted"),
                                    rx.text(
                                        State.dashboard_funcionarios_ativos,
                                        class_name="stat-card-number",
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
                                rx.heading("Estoque em atenção", size="5"),
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
                                            rx.text(produto["estoque"], class_name="table-cell"),
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
        rx.hstack(
            rx.heading("Clientes", size="7", class_name="customers-page-title"),
            rx.link(
                "Novo cliente",
                href="#cliente-form",
                class_name="new-customer-button",
            ),
            justify="between",
            align_items="center",
            width="100%",
        ),
        rx.box(
            rx.text("Nome", class_name="customer-table-heading"),
            rx.text("CPF", class_name="customer-table-heading"),
            rx.text("Telefone", class_name="customer-table-heading"),
            rx.text("E-mail", class_name="customer-table-heading"),
            rx.text("Endereço", class_name="customer-table-heading"),
            rx.text("", class_name="customer-table-heading"),
            class_name="customer-table-head",
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
                rx.text("—", class_name="customer-table-cell"),
                rx.hstack(
                    rx.button(
                        "Editar",
                        on_click=State.set_customer_field(
                            "cliente_id", customer["id"]
                        ),
                        class_name="customer-edit-button",
                    ),
                    rx.button(
                        "Remover",
                        on_click=State.set_customer_field(
                            "cliente_id", customer["id"]
                        ),
                        class_name="customer-remove-button",
                    ),
                    spacing="2",
                ),
                class_name="customer-table-row",
            ),
        ),
        width="100%",
        class_name="content-card customers-card",
    )


def customer_form() -> rx.Component:
    return rx.vstack(
        rx.heading("Manter cliente", size="5"),
        rx.input(
            placeholder="ID do cliente para editar ou inativar",
            value=State.cliente_id,
            on_change=lambda value: State.set_customer_field("cliente_id", value),
        ),
        rx.input(
            placeholder="Nome",
            value=State.cliente_nome,
            on_change=lambda value: State.set_customer_field("cliente_nome", value),
        ),
        rx.input(
            placeholder="CPF",
            value=State.cliente_cpf,
            on_change=lambda value: State.set_customer_field("cliente_cpf", value),
        ),
        rx.input(
            placeholder="Data de nascimento (AAAA-MM-DD)",
            value=State.cliente_data_nascimento,
            on_change=lambda value: State.set_customer_field(
                "cliente_data_nascimento", value
            ),
        ),
        rx.input(
            placeholder="Telefone",
            value=State.cliente_telefone,
            on_change=lambda value: State.set_customer_field(
                "cliente_telefone", value
            ),
        ),
        rx.input(
            placeholder="E-mail",
            value=State.cliente_email,
            on_change=lambda value: State.set_customer_field("cliente_email", value),
        ),
        rx.hstack(
            rx.button("Cadastrar", on_click=State.create_customer),
            rx.button("Atualizar", on_click=State.update_customer),
            rx.button("Inativar", on_click=State.deactivate_customer),
        ),
        id="cliente-form",
        width="100%",
        class_name="content-card",
        max_width="32rem",
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
            page_header("Clientes", "Consulte e mantenha os cadastros autorizados."),
            customer_list(),
            rx.cond(State.is_gestor, rx.fragment(), customer_form()),
            feedback_message(),
            width="100%",
            spacing="4",
        )
    )


def employee_list() -> rx.Component:
    return rx.vstack(
        rx.heading("Equipe", size="5"),
        rx.foreach(
            State.funcionarios,
            lambda employee: rx.hstack(
                rx.text(employee["id"], width="3rem"),
                rx.text(employee["nome"], width="16rem"),
                rx.text(employee["cargo"], width="12rem"),
                rx.text(employee["salario"], width="10rem"),
                rx.text(employee["cpf"]),
                rx.text(employee["situacao"], width="8rem"),
                class_name="content-card",
                width="100%",
            ),
        ),
        width="100%",
    )


def employee_form() -> rx.Component:
    return rx.vstack(
        rx.heading("Manter funcionário", size="5"),
        rx.input(
            placeholder="ID para editar ou inativar",
            value=State.funcionario_id,
            on_change=lambda value: State.set_employee_field(
                "funcionario_id", value
            ),
        ),
        rx.input(
            placeholder="Nome",
            value=State.funcionario_nome,
            on_change=lambda value: State.set_employee_field(
                "funcionario_nome", value
            ),
        ),
        rx.input(
            placeholder="CPF",
            value=State.funcionario_cpf,
            on_change=lambda value: State.set_employee_field(
                "funcionario_cpf", value
            ),
        ),
        rx.input(
            placeholder="Data de nascimento (AAAA-MM-DD)",
            value=State.funcionario_data_nascimento,
            on_change=lambda value: State.set_employee_field(
                "funcionario_data_nascimento", value
            ),
        ),
        rx.input(
            placeholder="Telefone",
            value=State.funcionario_telefone,
            on_change=lambda value: State.set_employee_field(
                "funcionario_telefone", value
            ),
        ),
        rx.input(
            placeholder="E-mail",
            value=State.funcionario_email,
            on_change=lambda value: State.set_employee_field(
                "funcionario_email", value
            ),
        ),
        rx.input(
            placeholder="Cargo",
            value=State.funcionario_cargo,
            on_change=lambda value: State.set_employee_field(
                "funcionario_cargo", value
            ),
        ),
        rx.input(
            placeholder="Salário",
            value=State.funcionario_salario,
            on_change=lambda value: State.set_employee_field(
                "funcionario_salario", value
            ),
        ),
        rx.input(
            placeholder="Login inicial (somente cadastro)",
            value=State.funcionario_login,
            on_change=lambda value: State.set_employee_field(
                "funcionario_login", value
            ),
        ),
        rx.hstack(
            rx.button("Cadastrar", on_click=State.create_employee),
            rx.button("Atualizar", on_click=State.update_employee),
            rx.button(
                "Inativar",
                on_click=State.request_deactivate_employee,
            ),
        ),
        rx.cond(
            State.confirmando_inativacao,
            rx.vstack(
                rx.text("Confirma a inativação deste funcionário?"),
                rx.hstack(
                    rx.button("Cancelar", on_click=State.cancel_deactivate_employee),
                    rx.button("Confirmar inativação", on_click=State.deactivate_employee),
                ),
            ),
            rx.fragment(),
        ),
        rx.cond(
            State.acesso_inicial != {},
            rx.vstack(
                rx.text("Login inicial: ", State.acesso_inicial["login"]),
                rx.text(
                    "Senha inicial: ", State.acesso_inicial["senha_inicial"]
                ),
            ),
            rx.fragment(),
        ),
        width="100%",
        class_name="content-card",
        max_width="32rem",
    )


def employees_page() -> rx.Component:
    return protected_layout(
        rx.vstack(
            page_header("Equipe", "Gerencie os funcionários e seus acessos."),
            employee_list(),
            employee_form(),
            feedback_message(),
            width="100%",
            spacing="4",
        )
    )


def supplier_list() -> rx.Component:
    return rx.vstack(
        section_heading("Fornecedores", "Parceiros cadastrados e prazo de entrega."),
        rx.foreach(
            State.fornecedores,
            lambda supplier: rx.box(
                rx.vstack(
                    rx.text(supplier["nome"], class_name="table-cell strong"),
                    rx.text(supplier["cnpj"], class_name="muted"),
                    align_items="start",
                    spacing="0",
                ),
                rx.text(supplier["telefone"], class_name="table-cell"),
                rx.text(supplier["email"], class_name="table-cell"),
                rx.text(
                    "Prazo ",
                    supplier["prazo_entrega"],
                    class_name="status-badge status-badge-info",
                ),
                rx.button(
                    "Selecionar",
                    on_click=lambda: State.select_supplier(supplier["id"]),
                    class_name="secondary-button",
                ),
                class_name="supplier-row",
                width="100%",
            ),
        ),
        class_name="content-card",
        width="100%",
    )


def supplier_form() -> rx.Component:
    return rx.vstack(
        rx.heading("Manter fornecedor", size="5"),
        rx.cond(
            State.fornecedor_id != "",
            rx.text("Fornecedor selecionado: ", State.fornecedor_id),
        ),
        rx.input(
            placeholder="Nome",
            value=State.fornecedor_nome,
            on_change=lambda value: State.set_supplier_field("fornecedor_nome", value),
        ),
        rx.input(
            placeholder="CNPJ",
            value=State.fornecedor_cnpj,
            on_change=lambda value: State.set_supplier_field("fornecedor_cnpj", value),
        ),
        rx.input(
            placeholder="Telefone",
            value=State.fornecedor_telefone,
            on_change=lambda value: State.set_supplier_field(
                "fornecedor_telefone", value
            ),
        ),
        rx.input(
            placeholder="E-mail",
            type="email",
            value=State.fornecedor_email,
            on_change=lambda value: State.set_supplier_field(
                "fornecedor_email", value
            ),
        ),
        rx.input(
            placeholder="Endereço",
            value=State.fornecedor_endereco,
            on_change=lambda value: State.set_supplier_field(
                "fornecedor_endereco", value
            ),
        ),
        rx.input(
            placeholder="Prazo de entrega (opcional)",
            value=State.fornecedor_prazo_entrega,
            on_change=lambda value: State.set_supplier_field(
                "fornecedor_prazo_entrega", value
            ),
        ),
        rx.hstack(
            rx.button("Cadastrar", on_click=State.create_supplier),
            rx.button("Atualizar", on_click=State.update_supplier),
            rx.button("Remover", on_click=State.request_delete_supplier),
        ),
        rx.cond(
            State.confirmando_remocao_fornecedor,
            rx.vstack(
                rx.text("Confirma a remoção deste fornecedor?"),
                rx.hstack(
                    rx.button(
                        "Cancelar",
                        on_click=State.cancel_delete_supplier,
                        class_name="secondary-button",
                    ),
                    rx.button(
                        "Confirmar remoção",
                        on_click=State.delete_supplier,
                        class_name="danger-button",
                    ),
                ),
                class_name="confirm-modal",
            ),
        ),
        width="100%",
        class_name="content-card",
        max_width="36rem",
    )


def suppliers_page() -> rx.Component:
    return protected_layout(
        rx.cond(
            State.is_gestor,
            rx.vstack(
                page_header(
                    "Fornecedores",
                    "Mantenha o catálogo de parceiros da farmácia.",
                ),
                supplier_list(),
                supplier_form(),
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
            rx.vstack(
                page_header("Minha conta", "Atualize suas credenciais de acesso."),
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
                feedback_message(),
                class_name="content-card",
                width="100%",
            ),
        ),
    )


def product_list() -> rx.Component:
    return rx.vstack(
        rx.heading("Produtos ativos"),
        rx.foreach(
            State.produtos,
            lambda product: rx.hstack(
                rx.text(product["id"], width="3rem"),
                rx.text(product["nome"], width="14rem"),
                rx.text("Estoque: ", product["estoque"]),
                rx.text("Mínimo: ", product["minimo"]),
                rx.text(product["situacao"]),
                rx.text(product["preco"]),
                class_name="content-card",
                width="100%",
            ),
        ),
        width="100%",
    )


def product_form() -> rx.Component:
    return rx.vstack(
            rx.heading("Cadastrar produto", size="5"),
            rx.input(
                placeholder="ID da categoria",
                value=State.produto_categoria_id,
                on_change=lambda value: State.set_product_field(
                    "produto_categoria_id", value
                ),
            ),
            rx.select.root(
                rx.select.trigger(
                    placeholder="Selecione um fornecedor",
                    width="100%",
                ),
                rx.select.content(
                    rx.select.group(
                        rx.foreach(
                            State.fornecedores,
                            lambda supplier: rx.select.item(
                                supplier["nome"] + " (" + supplier["cnpj"] + ")",
                                value=supplier["id"],
                            ),
                        ),
                    ),
                ),
                value=State.produto_fornecedor_id,
                on_change=State.set_product_supplier,
                disabled=State.fornecedores.length() == 0,
                width="100%",
            ),
            rx.cond(
                State.fornecedores.length() == 0,
                rx.text("Nenhum fornecedor disponível. Cadastre um fornecedor primeiro."),
            ),
            rx.input(
                placeholder="Nome",
                value=State.produto_nome,
                on_change=lambda value: State.set_product_field("produto_nome", value),
            ),
            rx.input(
                placeholder="Descrição",
                value=State.produto_descricao,
                on_change=lambda value: State.set_product_field(
                    "produto_descricao", value
                ),
            ),
            rx.input(
                placeholder="Código de barras",
                value=State.produto_codigo_barras,
                on_change=lambda value: State.set_product_field(
                    "produto_codigo_barras", value
                ),
            ),
            rx.input(
                placeholder="Preço de venda",
                value=State.produto_preco,
                on_change=lambda value: State.set_product_field(
                    "produto_preco", value
                ),
            ),
            rx.input(
                placeholder="Quantidade em estoque",
                value=State.produto_quantidade,
                on_change=lambda value: State.set_product_field(
                    "produto_quantidade", value
                ),
            ),
            rx.input(
                placeholder="Estoque mínimo",
                value=State.produto_estoque_minimo,
                on_change=lambda value: State.set_product_field(
                    "produto_estoque_minimo", value
                ),
            ),
            rx.checkbox(
                "Produto controlado",
                checked=State.produto_controlado,
                on_change=State.set_product_controlled,
            ),
            rx.button("Cadastrar", on_click=State.create_product),
            width="100%",
            class_name="content-card",
            max_width="32rem",
    )


def products_page() -> rx.Component:
    return protected_layout(
        rx.vstack(
            page_header("Produtos", "Cadastre produtos e acompanhe o catálogo ativo."),
            rx.cond(State.is_gestor, product_form(), rx.text(FORBIDDEN_MESSAGE)),
            rx.input(
                placeholder="ID do produto para inativar",
                value=State.produto_id,
                on_change=State.set_product_id,
            ),
            rx.cond(
                State.is_gestor,
                rx.hstack(
                    rx.button("Atualizar produto", on_click=State.update_product),
                    rx.button("Inativar produto", on_click=State.deactivate_product),
                ),
            ),
            rx.cond(
                State.is_gestor,
                rx.vstack(
                    rx.heading("Categorias", size="5"),
                    rx.foreach(
                        State.categorias,
                        lambda category: rx.text(
                            category["id"], " - ", category["nome"]
                        ),
                    ),
                    rx.input(
                        placeholder="ID da categoria para editar",
                        value=State.categoria_id,
                        on_change=State.set_categoria_id,
                    ),
                    rx.hstack(
                        rx.button(
                            "Atualizar categoria",
                            on_click=State.update_category,
                        ),
                        rx.button(
                            "Inativar categoria",
                            on_click=State.deactivate_category,
                        ),
                    ),
                    rx.input(
                        placeholder="Nova categoria",
                        value=State.categoria_nome,
                        on_change=State.set_categoria_nome,
                    ),
                    rx.button("Cadastrar categoria", on_click=State.create_category),
                ),
            ),
            product_list(),
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
                            "stock-table-cell stock-value",
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
            placeholder="ID do produto",
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
                "Produto ",
                item["id_produto"],
                " - Quantidade: ",
                item["quantidade"],
            ),
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
        rx.button("Confirmar venda", on_click=State.create_sale),
        width="100%",
        class_name="content-card",
        max_width="32rem",
    )


def sales_history() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading("Vendas", size="7", class_name="sales-page-title"),
            rx.link(
                "Nova venda",
                href="/atendimento",
                class_name="new-sale-button",
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
        "color": "#ffffff",
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
    },
    ".feedback-error": {
        "background": "#fcebea",
        "color": "#a32d2d",
        "border": "1px solid #f2b8b5",
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
    ".dashboard-page": {
        "padding_top": "1rem",
    },
    ".content-card": {
        "padding": "1.25rem",
        "border": "1px solid #17332f",
        "border_radius": "18px",
        "background": "#081312",
        "box_shadow": "0 10px 30px -12px rgba(0,0,0,0.8), inset 0 1px 0 rgba(120,230,215,0.1)",
        "overflow_x": "auto",
    },
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
        "grid_template_columns": "0.75fr 0.65fr 1.05fr 1.65fr 0.85fr 0.9fr 0.8fr",
        "gap": "1rem",
        "align_items": "center",
        "min_width": "68rem",
    },
    ".sales-table-head": {
        "padding": "1rem 0 0.75rem",
        "border_bottom": "1px solid #17332f",
    },
    ".sales-table-row": {
        "padding": "0.85rem 0",
        "border_bottom": "1px solid #17332f",
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
    ".customers-page-title": {
        "color": "#ffffff",
        "font_size": "1.25rem",
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
        "box_shadow": "0 0 18px rgba(20,184,166,0.3)",
    },
    ".customer-table-head, .customer-table-row": {
        "display": "grid",
        "grid_template_columns": "1.2fr 1fr 1.1fr 1.45fr 1.35fr 1.2fr",
        "gap": "1rem",
        "align_items": "center",
        "min_width": "68rem",
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
    ".supplier-row": {
        "display": "grid",
        "grid_template_columns": "1.3fr 1fr 1.4fr auto auto",
        "gap": "0.8rem",
        "align_items": "center",
        "padding": "0.8rem 0",
        "border_bottom": "1px solid #edf3ef",
        "min_width": "42rem",
    },
    ".secondary-button": {
        "background": "transparent",
        "color": "#0f6e56",
        "border": "1px solid #0f6e56",
    },
    ".danger-button": {
        "background": "#a32d2d",
        "color": "#ffffff",
        "border_color": "#a32d2d",
    },
    ".confirm-modal": {
        "margin_top": "1rem",
        "padding": "1rem",
        "border": "1px solid #f2b8b5",
        "border_radius": "14px",
        "background": "#fff7f6",
    },
    ".stat-card": {
        "width": "100%",
        "min_width": "0",
        "height": "7rem",
        "padding": "1rem",
        "border": "1px solid #17332f",
        "border_radius": "14px",
        "background": "#081312",
        "box_sizing": "border-box",
        "display": "flex",
        "align_items": "center",
        "overflow": "hidden",
    },
    ".dashboard-stats": {
        "display": "grid",
        "grid_template_columns": "repeat(4, minmax(0, 1fr))",
        "gap": "0.9rem",
        "margin_bottom": "1.25rem",
    },
    ".stat-card-number": {
        "color": "#5eead4",
        "font_size": "1.65rem",
        "font_weight": "800",
    },
    ".stat-caption": {
        "color": "#5c7568",
        "font_size": "0.75rem",
    },
    ".role-label": {
        "font_size": "0.68rem",
        "font_weight": "700",
    },
    ".stock-alert-head, .stock-alert-row": {
        "display": "grid",
        "grid_template_columns": "2fr 1fr 1fr 1fr",
        "gap": "0.65rem",
        "align_items": "center",
        "min_width": "34rem",
        "text_align": "center",
    },
    ".stock-alert-head": {
        "padding": "0.9rem 0.5rem 0.65rem",
        "border_bottom": "1px solid #d6e6dc",
    },
    ".stock-alert-row": {
        "padding": "0.75rem 0.5rem",
        "border_bottom": "1px solid #edf3ef",
    },
    ".stock-alert-head > :first-child, .stock-alert-row > :first-child": {
        "text_align": "left",
    },
    "@media (max-width: 700px)": {
        ".login-page": {"padding": "1.25rem"},
        ".login-hero-copy": {"gap": "0.75rem", "flex_basis": "100%"},
        ".login-hero-title": {"font_size": "2.3rem"},
        ".login-hero-description": {"font_size": "0.95rem"},
        ".login-panel": {
            "max_width": "none",
            "padding": "2rem 1.5rem",
            "flex_basis": "100%",
        },
        ".nav-links": {"gap": "0.6rem"},
        ".app-shell": {"padding_left": "0"},
        ".topbar": {
            "position": "relative",
            "width": "100%",
            "padding": "1rem",
            "border_right": "0",
            "border_bottom": "1px solid #d6e6dc",
        },
        ".nav-brand": {"width": "100%"},
        ".nav-tabs": {"width": "100%", "overflow_x": "auto", "padding_bottom": "0.2rem"},
        ".page-content": {"padding": "1rem 0.75rem"},
        ".content-card": {"padding": "1rem", "max_width": "100%"},
        ".dashboard-stats": {"grid_template_columns": "repeat(2, minmax(0, 1fr))"},
    },
    "@media (max-width: 480px)": {
        ".dashboard-stats": {"grid_template_columns": "1fr"},
    },
}

app = rx.App(style=GLOBAL_STYLE)
app.add_page(login_page, route="/login")
app.add_page(dashboard_page, route="/dashboard", on_load=State.load_dashboard)
app.add_page(account_page, route="/minha-conta", on_load=State.load_session)
app.add_page(products_page, route="/produtos", on_load=State.load_products)
app.add_page(stock_page, route="/estoque", on_load=State.load_products)
app.add_page(customers_page, route="/clientes", on_load=State.load_customers)
app.add_page(employees_page, route="/equipe", on_load=State.load_employees)
app.add_page(suppliers_page, route="/fornecedores", on_load=State.load_suppliers)
app.add_page(attendance_page, route="/atendimento", on_load=State.load_session)
app.add_page(sales_page, route="/vendas", on_load=State.load_sales)
app.add_page(login_page, route="/")

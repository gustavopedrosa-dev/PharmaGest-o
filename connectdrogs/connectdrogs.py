"""Frontend do FarmaGestão para autenticação e navegação por perfil."""

from __future__ import annotations

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
    acesso_inicial: dict[str, str] = {}
    confirmando_inativacao: bool = False
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

    @rx.event
    def load_products(self) -> rx.event.EventSpec | None:
        redirect = self.load_session()
        if redirect is not None:
            return redirect
        try:
            client = XanoClient()
            self._set_products(client.list_products(self._token))
            self._set_categories(client.list_categories(self._token))
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

    def _set_customers(self, customers: list[Customer]) -> None:
        self.clientes = [self._customer_view(customer) for customer in customers]

    def _set_addresses(self, addresses: list[Address]) -> None:
        self.enderecos = [self._address_view(address) for address in addresses]

    def _set_employees(self, employees: list[Employee]) -> None:
        self.funcionarios = [self._employee_view(employee) for employee in employees]

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
    def _product_view(product: object) -> dict[str, str]:
        return {
            "id": str(product.id),
            "nome": product.nome,
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
            rx.hstack(
                rx.link("Painel", href="/dashboard"),
                rx.link("Produtos", href="/produtos"),
                rx.link("Vendas", href="/vendas"),
                rx.link("Equipe", href="/equipe"),
            ),
            rx.hstack(
                rx.link("Atendimento", href="/atendimento"),
                rx.link("Minhas vendas", href="/vendas"),
            ),
        ),
        rx.link("Clientes", href="/clientes"),
        rx.link("Estoque", href="/estoque"),
        rx.cond(
            State.is_gestor,
            rx.fragment(),
            rx.link("Minha conta", href="/minha-conta"),
        ),
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


def customer_list() -> rx.Component:
    return rx.vstack(
        rx.heading("Clientes", size="5"),
        rx.foreach(
            State.clientes,
            lambda customer: rx.hstack(
                rx.text(customer["id"], width="3rem"),
                rx.text(customer["nome"], width="14rem"),
                rx.text("CPF: ", customer["cpf"]),
                rx.text("Situacao: ", customer["situacao"]),
                width="100%",
            ),
        ),
        width="100%",
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
        width="100%",
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
                width="100%",
                max_width="32rem",
            ),
        ),
        width="100%",
    )


def customers_page() -> rx.Component:
    return protected_layout(
        rx.vstack(
            rx.heading("Gestao de clientes"),
            customer_list(),
            rx.cond(State.is_gestor, rx.fragment(), customer_form()),
            address_section(),
            rx.cond(State.mensagem != "", rx.text(State.mensagem)),
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
        max_width="32rem",
    )


def employees_page() -> rx.Component:
    return protected_layout(
        rx.vstack(
            rx.heading("Gestão da equipe"),
            employee_list(),
            employee_form(),
            rx.cond(State.mensagem != "", rx.text(State.mensagem)),
        )
    )


def account_page() -> rx.Component:
    return protected_layout(
        rx.cond(
            State.is_gestor,
            rx.text(FORBIDDEN_MESSAGE),
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
            rx.input(
                placeholder="ID do fornecedor",
                value=State.produto_fornecedor_id,
                on_change=lambda value: State.set_product_field(
                    "produto_fornecedor_id", value
                ),
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
            max_width="32rem",
    )


def products_page() -> rx.Component:
    return protected_layout(
        rx.vstack(
            rx.heading("Gestão de produtos"),
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
            rx.cond(State.mensagem != "", rx.text(State.mensagem)),
        )
    )


def stock_page() -> rx.Component:
    return protected_layout(
        rx.vstack(
            rx.heading("Consulta de estoque"),
            product_list(),
            rx.cond(State.mensagem != "", rx.text(State.mensagem)),
        )
    )


def sale_form() -> rx.Component:
    return rx.vstack(
        rx.heading("Registrar atendimento"),
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
        max_width="32rem",
    )


def sales_history() -> rx.Component:
    return rx.vstack(
        rx.heading("Histórico de vendas"),
        rx.foreach(
            State.vendas,
            lambda sale: rx.hstack(
                rx.text("Venda ", sale["id"]),
                rx.text("Pedido ", sale["pedido"]),
                rx.text("Total: R$ ", sale["total"]),
                rx.text("Canal: ", sale["canal"]),
                rx.text("Atendente: ", sale["atendente"]),
                rx.text("Pagamento: ", sale["pagamento"]),
                rx.text(sale["status"]),
                rx.text(sale["data"]),
                width="100%",
            ),
        ),
        rx.heading("Pedidos e itens", size="5"),
        rx.foreach(
            State.pedidos,
            lambda order: rx.vstack(
                rx.text(
                    "Pedido ",
                    order["id"],
                    " - Cliente: ",
                    order["cliente"],
                    " - ",
                    order["status"],
                    " - ",
                    order["canal"],
                ),
                rx.foreach(
                    State.itens_pedido,
                    lambda item: rx.cond(
                        item["pedido"] == order["id"],
                        rx.text(
                            "Produto ",
                            item["produto"],
                            " - Quantidade: ",
                            item["quantidade"],
                        ),
                        rx.fragment(),
                    ),
                ),
                width="100%",
            ),
        ),
        rx.cond(State.mensagem != "", rx.text(State.mensagem)),
        width="100%",
    )


def attendance_page() -> rx.Component:
    return protected_layout(
        rx.cond(
            State.is_gestor,
            rx.text(FORBIDDEN_MESSAGE),
            sale_form(),
        )
    )


def sales_page() -> rx.Component:
    return protected_layout(sales_history())


app = rx.App()
app.add_page(login_page, route="/login")
app.add_page(dashboard_page, route="/dashboard", on_load=State.load_dashboard)
app.add_page(account_page, route="/minha-conta", on_load=State.load_session)
app.add_page(products_page, route="/produtos", on_load=State.load_products)
app.add_page(stock_page, route="/estoque", on_load=State.load_products)
app.add_page(customers_page, route="/clientes", on_load=State.load_customers)
app.add_page(employees_page, route="/equipe", on_load=State.load_employees)
app.add_page(attendance_page, route="/atendimento", on_load=State.load_session)
app.add_page(sales_page, route="/vendas", on_load=State.load_sales)
app.add_page(login_page, route="/")

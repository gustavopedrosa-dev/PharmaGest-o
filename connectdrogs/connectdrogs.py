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
    produtos: list[dict[str, str]] = []
    categorias: list[dict[str, str]] = []
    vendas: list[dict[str, str]] = []
    pedidos: list[dict[str, str]] = []
    itens_pedido: list[dict[str, str]] = []
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
            ),
            rx.hstack(
                rx.link("Atendimento", href="/atendimento"),
                rx.link("Minhas vendas", href="/vendas"),
            ),
        ),
        rx.link("Estoque", href="/estoque"),
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
app.add_page(attendance_page, route="/atendimento", on_load=State.load_session)
app.add_page(sales_page, route="/vendas", on_load=State.load_sales)
app.add_page(login_page, route="/")

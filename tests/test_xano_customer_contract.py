from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]


def read_xano(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


class CustomerXanoContractTests(unittest.TestCase):
    def test_customer_write_endpoints_require_collaborator_and_preserve_status_rules(self) -> None:
        create_script = read_xano("xano/api/clientes/cliente_POST.xs")
        update_script = read_xano("xano/api/clientes/cliente_PATCH.xs")
        deactivate_script = read_xano("xano/api/clientes/cliente_inativar_POST.xs")

        for script in (create_script, update_script, deactivate_script):
            self.assertIn('required_role: "colaborador"', script)
        self.assertIn('field_name = "cpf"', create_script)
        self.assertIn('$cliente_com_cpf == null', create_script)
        self.assertIn('$cliente_com_cpf.id == $input.id', update_script)
        self.assertIn("data = {ativo: false}", deactivate_script)

    def test_address_endpoints_require_existing_customer(self) -> None:
        create_script = read_xano("xano/api/clientes/endereco_POST.xs")
        list_script = read_xano("xano/api/clientes/enderecos_GET.xs")

        self.assertIn('field_value = $input.id', create_script)
        self.assertIn('precondition ($cliente != null)', create_script)
        self.assertIn('id_cliente: $input.id', create_script)
        self.assertIn('precondition ($cliente != null)', list_script)
        self.assertIn("$db.endereco.id_cliente == $input.id", list_script)

    def test_order_creation_rejects_inactive_customer(self) -> None:
        script = read_xano("xano/api/vendas/pedido_POST.xs")

        self.assertIn('output = ["id", "ativo"]', script)
        self.assertIn('$cliente.ativo == true', script)
        self.assertIn('error = "O cliente não está ativo."', script)

    def test_employee_provisioning_uses_generated_password_and_role_guards(self) -> None:
        create_script = read_xano("xano/api/equipe/funcionario_POST.xs")
        list_script = read_xano("xano/api/equipe/funcionarios_GET.xs")
        deactivate_script = read_xano("xano/api/equipe/funcionario_inativar_POST.xs")
        account_login_script = read_xano(
            "xano/api/identidade/minha_conta_login_PATCH.xs"
        )
        account_password_script = read_xano(
            "xano/api/identidade/minha_conta_senha_PATCH.xs"
        )

        self.assertIn("security.create_password", create_script)
        self.assertIn('perfil_acesso: "colaborador"', create_script)
        self.assertIn("db.transaction", create_script)
        self.assertIn('required_role: "gestor"', create_script)
        self.assertIn('required_role: "gestor"', list_script)
        self.assertIn('required_role: "gestor"', deactivate_script)
        self.assertIn('required_role: "colaborador"', account_login_script)
        self.assertIn('required_role: "colaborador"', account_password_script)
        self.assertIn("security.check_password", account_password_script)


if __name__ == "__main__":
    unittest.main()
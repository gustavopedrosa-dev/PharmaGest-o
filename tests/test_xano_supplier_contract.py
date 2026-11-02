import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


def read_xano(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


class SupplierXanoContractTests(unittest.TestCase):
    def test_supplier_read_and_write_endpoints_require_manager(self) -> None:
        scripts = (
            "xano/api/produtos/fornecedores_GET.xs",
            "xano/api/produtos/fornecedor_POST.xs",
            "xano/api/produtos/fornecedor_PATCH.xs",
            "xano/api/produtos/fornecedor_DELETE.xs",
        )

        for path in scripts:
            with self.subTest(path=path):
                self.assertIn(
                    'input = {required_role: "gestor"}',
                    read_xano(path),
                )

    def test_supplier_schema_adds_optional_delivery_lead_time(self) -> None:
        table = read_xano("xano/table/fornecedor.xs")

        self.assertIn("text? prazo_entrega", table)

    def test_create_and_update_enforce_unique_cnpj(self) -> None:
        create_script = read_xano("xano/api/produtos/fornecedor_POST.xs")
        update_script = read_xano("xano/api/produtos/fornecedor_PATCH.xs")

        for script in (create_script, update_script):
            self.assertIn('db.query "fornecedor"', script)
            self.assertIn('error = "Já existe um fornecedor com este CNPJ."', script)
        self.assertIn("$db.fornecedor.id != $input.id", update_script)
        self.assertIn("text? prazo_entrega?", create_script)
        self.assertIn("text? prazo_entrega?", update_script)
        self.assertIn("prazo_entrega: $input.prazo_entrega", create_script)
        self.assertIn("prazo_entrega: $input.prazo_entrega", update_script)

    def test_delete_rejects_supplier_referenced_by_products(self) -> None:
        delete_script = read_xano("xano/api/produtos/fornecedor_DELETE.xs")

        self.assertIn('db.query "produto"', delete_script)
        self.assertIn("$db.produto.id_fornecedor == $input.id", delete_script)
        self.assertIn("precondition (!$produtos_vinculados)", delete_script)
        self.assertIn('db.del "fornecedor"', delete_script)

    def test_product_validation_still_requires_existing_supplier(self) -> None:
        script = read_xano("xano/function/produtos/require_product_input.xs")

        self.assertIn('db.get "fornecedor"', script)
        self.assertIn("precondition ($fornecedor != null)", script)
        self.assertIn('error = "O fornecedor informado não existe."', script)


if __name__ == "__main__":
    unittest.main()
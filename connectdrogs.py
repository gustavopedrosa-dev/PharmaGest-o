    saved_addresses = [dict(address) for address in addresses]
    for address in saved_addresses:
        address_fields = (
            address.get("logradouro", ""),
            address.get("numero", ""),
            address.get("bairro", ""),
            address.get("cidade", ""),
            address.get("estado", ""),
            address.get("cep", ""),
            address.get("complemento", ""),
        )
        if not any(str(value).strip() for value in address_fields):
            continue

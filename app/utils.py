from itertools import cycle

def validar_rut(rut_completo):
    rut = rut_completo.upper().replace("-", "").replace(".", "")
    cuerpo = rut[:-1]
    verificador = rut[-1]

    reverso = map(int, reversed(cuerpo))
    factores = cycle(range(2, 8))
    s = sum(d * f for d, f in zip(reverso, factores))
    res = (-s) % 11

    if res == 10:
        dv = 'K'
    else:
        dv = str(res)

    is_valid = dv == verificador

    # Mostrar resultado en consola
    print(f"Validando RUT: {rut_completo} - {'Válido' if is_valid else 'Inválido'}")

    return is_valid


def validar_rut_persona_natural(rut_completo):
    return validar_rut(rut_completo)


def validar_rut_empresa(rut_completo):
    return validar_rut(rut_completo)


# Pruebas de ejemplo
if __name__ == "__main__":
    # RUT de persona natural
    rut_natural = "19918561-6"
    validar_rut_persona_natural(rut_natural)

    # RUT de empresa
    rut_empresa = "77645122-3"
    validar_rut_empresa(rut_empresa)

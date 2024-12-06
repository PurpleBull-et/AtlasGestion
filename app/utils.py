from itertools import cycle
import random
import string

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


def gen_password():
    letras = ''.join(random.choices(string.ascii_letters, k=5))  # 5 letras
    numeros = ''.join(random.choices(string.digits, k=3))  # 3 números
    mayuscula = random.choice(string.ascii_uppercase)  # 1 mayúscula
    punto = random.choice(['.', '.'])  # Punto al inicio o al final
    passw = punto + mayuscula + letras + numeros if random.choice([True, False]) else mayuscula + letras + numeros + punto
    return passw

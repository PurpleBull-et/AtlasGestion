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

import requests
from bs4 import BeautifulSoup
from datetime import datetime

def obtener_hora_oficial():
    try:
        # Realiza la solicitud al sitio de hora oficial
        url = "https://www.horaoficial.cl/"
        response = requests.get(url)
        response.raise_for_status()
        
        # Analiza el contenido de la página
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Encuentra el elemento que contiene la hora
        hora_html = soup.find('span', {'id': 'reloj'}).text.strip()
        fecha_html = soup.find('span', {'id': 'fecha'}).text.strip()
        
        # Convierte la hora y fecha en un objeto datetime
        hora_completa = f"{fecha_html} {hora_html}"
        hora_oficial = datetime.strptime(hora_completa, '%d-%m-%Y %H:%M:%S')
        
        return hora_oficial
    except Exception as e:
        print(f"Error al obtener la hora oficial: {e}")
        return None

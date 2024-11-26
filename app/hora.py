import requests

# URL de la API para la hora actual en Santiago, Chile
url = "https://www.timeapi.io/api/Time/current/zone?timeZone=America/Santiago"

try:
    # Realizar la solicitud GET
    response = requests.get(url)
    response.raise_for_status()  # Lanza una excepción si el código de estado no es 200
    data = response.json()

    # Extraer la hora actual
    hora_actual = data['time']
    print(f"La hora actual en Santiago, Chile (TimeAPI) es: {hora_actual}")
except requests.exceptions.RequestException as e:
    print(f"Error al obtener la hora desde TimeAPI: {e}")


import requests

# Datos de regiones, provincias y comunas (simulación local para el ejemplo)
chile_data = {
    "Región Metropolitana": {
        "Cordillera": ["Puente Alto", "San José de Maipo", "Pirque"],
        "Santiago": ["Santiago", "Providencia", "Las Condes"]
    },
    "Región de Valparaíso": {
        "Valparaíso": ["Valparaíso", "Viña del Mar", "Concón"],
        "Quillota": ["Quillota", "La Calera", "Hijuelas"]
    }
}

def validar_direccion(region, provincia, comuna, direccion):
    """
    Valida si la dirección ingresada existe dentro de la jerarquía de Región, Provincia y Comuna.
    """
    if region in chile_data:
        if provincia in chile_data[region]:
            if comuna in chile_data[region][provincia]:
                # Aquí se podría agregar validación más específica de la dirección exacta
                print(f"Dirección válida: {region} - {provincia} - {comuna} -> {direccion}")
                return True
            else:
                print(f"Comuna '{comuna}' no encontrada en provincia '{provincia}'.")
        else:
            print(f"Provincia '{provincia}' no encontrada en región '{region}'.")
    else:
        print(f"Región '{region}' no encontrada.")
    return False

def ejecutar_prueba():
    """
    Ejecuta pruebas para validar direcciones.
    """
    print("\nPrueba 1: Dirección válida")
    validar_direccion("Región Metropolitana", "Cordillera", "Puente Alto", "Puntilla 0813")
    
    print("\nPrueba 2: Región inválida")
    validar_direccion("Región Inventada", "Cordillera", "Puente Alto", "Puntilla 0893")
    
    print("\nPrueba 3: Provincia inválida")
    validar_direccion("Región Metropolitana", "Inventada", "Puente Alto", "Puntilla 0893")
    
    print("\nPrueba 4: Comuna inválida")
    validar_direccion("Región Metropolitana", "Cordillera", "Inventada", "Puntilla 0893")

if __name__ == "__main__":
    ejecutar_prueba()

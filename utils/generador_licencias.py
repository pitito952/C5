# generador_licencias.py (Solo para tu uso)
import hashlib

# ¡¡¡ESTA SEMILLA ES EL SECRETO DE TU NEGOCIO!!! Guárdala bien.
SEMILLA_SECRETA = "C5-Antigravity-Solutions-2026-XYZ"


def generar_licencia(huella_mac):
    """Genera una clave de licencia a partir de la MAC y la semilla secreta."""
    texto_a_hashear = f"{huella_mac.upper()}-{SEMILLA_SECRETA}"
    # Usamos SHA256 para seguridad y tomamos una parte para que no sea tan larga
    hash_completo = hashlib.sha256(texto_a_hashear.encode()).hexdigest()
    # Formateamos en bloques de 4 caracteres para legibilidad: XXXX-XXXX-XXXX-XXXX
    licencia = "-".join(hash_completo[:16].upper()[i:i + 4] for i in range(0, 16, 4))
    return licencia


if __name__ == "__main__":
    # Simulación del proceso
    mac_del_cliente = input("Introduce la dirección MAC del cliente: ")
    if mac_del_cliente:
        licencia_generada = generar_licencia(mac_del_cliente)
        print(f"\nLicencia generada para {mac_del_cliente}:")
        print(licencia_generada)
        print("\nInstrucciones:")
        print("1. Envía esta licencia al cliente.")
        print("2. Pídele que la guarde en un lugar seguro.")

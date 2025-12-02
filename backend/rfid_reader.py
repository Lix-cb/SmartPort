from mfrc522 import SimpleMFRC522
import time


def leer_rfid(reintentos=3, pausa=1):
    """Lee el RFID con reintentos.

    Siempre regresa el ID numérico de la tarjeta como string.
    Si después de `reintentos` intentos no se logra leer, devuelve None.
    """
    reader = SimpleMFRC522()
    print("Acerca la tarjeta RFID...")

    for intento in range(reintentos):
        try:
            id, text = reader.read()
            # Mensaje de depuración para ver exactamente qué llega del lector
            print(f"[DEBUG] id crudo: {id}, text crudo: {repr(text)}")

            # Usamos SIEMPRE el ID numérico
            resultado = str(id).strip()
            if resultado:
                print(f"✓ RFID leído correctamente: {resultado}")
                return resultado

            print("⚠ Se leyó la tarjeta pero el ID vino vacío, reintentando...")

        except Exception as e:
            print(f"✗ Intento {intento + 1}/{reintentos} falló: {e}")

        if intento < reintentos - 1:
            print(f"  Reintentando en {pausa}s...")
            time.sleep(pausa)

    # Si todos los intentos fallaron
    print("✗ No se pudo leer el RFID después de varios intentos.")
    return None
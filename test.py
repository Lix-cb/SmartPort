#!/usr/bin/env python3
"""
test_rfid.py - Script de prueba para depurar lectura RFID
Prueba independiente que NO afecta el backend
"""

import sys
import time

print("="*60)
print("TEST RFID - SmartPort v2.0")
print("="*60)
print()

# Intentar importar SimpleMFRC522
try:
    from mfrc522 import SimpleMFRC522
    print("[OK] Librería SimpleMFRC522 importada correctamente")
except ImportError as e:
    print(f"[ERROR] No se pudo importar SimpleMFRC522: {e}")
    print("[INFO] Instala con: sudo pip3 install mfrc522")
    sys.exit(1)

# Intentar importar MFRC522 base
try:
    from mfrc522 import MFRC522
    print("[OK] Librería MFRC522 (base) importada correctamente")
    MFRC522_DISPONIBLE = True
except ImportError:
    print("[WARNING] MFRC522 base no disponible")
    MFRC522_DISPONIBLE = False

print()
print("="*60)
print("INICIALIZANDO LECTOR...")
print("="*60)

# Crear instancia del lector
try:
    reader = SimpleMFRC522()
    print("[OK] SimpleMFRC522 inicializado correctamente")
except Exception as e:
    print(f"[ERROR] No se pudo inicializar el lector: {e}")
    sys.exit(1)

print()
print("="*60)
print("ESPERANDO TARJETA RFID...")
print("Acerca una tarjeta al lector")
print("="*60)
print()

# Leer tarjeta
try:
    print("[INFO] Ejecutando reader.read()...")
    print("[INFO] (Esto se bloqueará hasta que detecte una tarjeta)")
    print()
    
    id, text = reader.read()
    
    print()
    print("="*60)
    print("TARJETA DETECTADA")
    print("="*60)
    print()
    
    # Mostrar ID original
    print(f"[DATO 1] ID original (SimpleMFRC522):")
    print(f"         Valor: {id}")
    print(f"         Tipo: {type(id)}")
    print(f"         Longitud: {len(str(id))} dígitos")
    print()
    
    # Mostrar texto (si hay)
    print(f"[DATO 2] Texto almacenado en tarjeta:")
    if text and text.strip():
        print(f"         \"{text. strip()}\"")
    else:
        print(f"         (vacío)")
    print()
    
    # Método 1: Extraer últimos 32 bits
    print(f"[MÉTODO 1] Extraer últimos 32 bits (4 bytes):")
    uid_32bits = id & 0xFFFFFFFF
    print(f"           Valor: {uid_32bits}")
    print(f"           Hex: 0x{uid_32bits:08X}")
    print()
    
    # Método 2: Acceder al UID directo
    print(f"[MÉTODO 2] Acceder al UID directo (reader.READER.uid):")
    try:
        uid_bytes = reader.READER.uid
        print(f"           Disponible: SÍ")
        print(f"           Tamaño: {len(uid_bytes)} bytes")
        print(f"           Bytes (HEX): ", end="")
        for b in uid_bytes:
            print(f"{b:02X} ", end="")
        print()
        print(f"           Bytes (DEC): ", end="")
        for b in uid_bytes:
            print(f"{b:3d} ", end="")
        print()
        
        # Convertir a decimal (igual que ESP8266)
        if len(uid_bytes) >= 4:
            uid_decimal = (uid_bytes[0] << 24) | (uid_bytes[1] << 16) | (uid_bytes[2] << 8) | uid_bytes[3]
            print(f"           Convertido a decimal: {uid_decimal}")
            print(f"           Convertido a hex: 0x{uid_decimal:08X}")
        else:
            print(f"           [WARNING] Menos de 4 bytes disponibles")
            uid_decimal = None
    except Exception as e:
        print(f"           Disponible: NO")
        print(f"           Error: {e}")
        uid_decimal = None
    print()
    
    # Método 3: Convertir ID completo a HEX
    print(f"[MÉTODO 3] ID completo en hexadecimal:")
    id_hex = format(id, 'X')
    print(f"           Hex: 0x{id_hex}")
    print(f"           Longitud: {len(id_hex)} caracteres hex")
    print()
    
    # Comparación
    print("="*60)
    print("COMPARACIÓN DE MÉTODOS")
    print("="*60)
    print()
    print(f"SimpleMFRC522 ID original: {id}")
    print(f"Método 1 (32 bits):        {uid_32bits}")
    if uid_decimal:
        print(f"Método 2 (UID directo):    {uid_decimal}")
        print()
        if uid_32bits == uid_decimal:
            print("✅ Método 1 y Método 2 COINCIDEN")
        else:
            print("⚠️  Método 1 y Método 2 NO COINCIDEN")
    print()
    
    # Recomendación
    print("="*60)
    print("RECOMENDACIÓN PARA ESP8266")
    print("="*60)
    print()
    if uid_decimal:
        print(f"Usar este valor en BD: {uid_decimal}")
        print(f"Este es el formato de 4 bytes (32 bits) que usa el ESP8266")
    else:
        print(f"Usar este valor en BD: {uid_32bits}")
        print(f"Calculado con máscara de 32 bits")
    print()
    
except KeyboardInterrupt:
    print()
    print("[INFO] Lectura cancelada por usuario")
    sys.exit(0)
except Exception as e:
    print()
    print(f"[ERROR] Error durante lectura: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("="*60)
print("TEST COMPLETADO")
print("="*60)

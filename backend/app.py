"""
app.py - API REST para SmartPort v2. 0
Sistema de registro y acceso con RFID + Reconocimiento facial

MODULO 1: Registro y validacion biometrica con Raspberry Pi
MODULO 2: Recepcion de datos de peso via MQTT desde ESP8266
MODULO 3: Control de puerta fisica via MQTT con ESP8266

VERSIÓN FINAL:
- Registro atómico (RFID + Rostro juntos)
- Integración completa con ESP8266 (Módulo 2 y 3)
- Check-in automático al completar registro
- Verificación de acceso con apertura de puerta
- FORMATO RFID: HEXADECIMAL 8 caracteres (compatible ESP8266)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import paho.mqtt.client as mqtt
import os
import cv2
import face_recognition
import numpy as np
import time
import threading

# Importar funciones de base de datos
from db import (
    verificar_admin, registrar_admin, listar_admins,
    crear_pasajero, registrar_rfid_pasajero, registrar_rostro_pasajero,
    buscar_pasajero_por_rfid, registrar_acceso, calcular_similitud_facial,
    get_db_connection
)

# Intentar importar MFRC522 (puede fallar si no esta conectado)
try:
    from mfrc522 import SimpleMFRC522
    reader = SimpleMFRC522()
    RFID_DISPONIBLE = True
    # CRITICO: Lock para evitar lecturas simultaneas del RFID
    rfid_lock = threading.Lock()
    print("[OK] MFRC522 inicializado con lock de threading")
except:
    print("[WARNING] MFRC522 no disponible - Usando modo simulacion")
    RFID_DISPONIBLE = False
    rfid_lock = None

app = Flask(__name__)
CORS(app)

# ========================================
# CONFIGURACION MQTT
# ========================================

MQTT_BROKER = os.environ.get("MQTT_BROKER", "broker.mqtt.cool")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_TOPIC_VERIFICAR_RFID = "aeropuerto/verificar_rfid"  # ESP8266 Puerta envia RFID
MQTT_TOPIC_PUERTA_RESPUESTA = "aeropuerto/puerta/respuesta"  # Raspberry responde ABRIR/DENEGAR
MQTT_TOPIC_PESO = "aeropuerto/peso"  # ESP8266 Bascula envia peso

# ========================================
# FIX para Python 3.13: Usar CallbackAPIVersion
# ========================================
try:
    # Python 3.13+ requiere especificar la version del API
    mqtt_client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
        client_id="RaspberryPi_SmartPort"
    )
except AttributeError:
    # Fallback para versiones antiguas de paho-mqtt
    mqtt_client = mqtt.Client(client_id="RaspberryPi_SmartPort")

mqtt_conectado = False

def on_connect(client, userdata, flags, rc):
    global mqtt_conectado
    if rc == 0:
        mqtt_conectado = True
        print("[OK] Conectado al broker MQTT")
        
        # Suscribirse a topics necesarios
        client.subscribe(MQTT_TOPIC_VERIFICAR_RFID)
        client.subscribe(MQTT_TOPIC_PESO)
        print(f"[OK] Suscrito a: {MQTT_TOPIC_VERIFICAR_RFID}")
        print(f"[OK] Suscrito a: {MQTT_TOPIC_PESO}")
    else:
        mqtt_conectado = False
        print(f"[ERROR] Error conectando a MQTT: codigo {rc}")

def on_disconnect(client, userdata, rc):
    global mqtt_conectado
    mqtt_conectado = False
    print("[INFO] Desconectado del broker MQTT")

def on_message(client, userdata, msg):
    """
    Callback para mensajes MQTT recibidos
    Modulo 2: Recibe pesos de bascula (ya en kg)
    Modulo 3: Recibe solicitudes de verificacion de RFID desde ESP8266 Puerta
    """
    topic = msg.topic
    payload = msg.payload. decode('utf-8'). strip()  # ✅ Eliminar espacios
    
    if topic == MQTT_TOPIC_VERIFICAR_RFID:
        # MODULO 3: ESP8266 Puerta solicita verificar RFID
        print(f"\n[INFO] MODULO 3: ESP8266 Puerta solicita verificar RFID: {payload}")
        verificar_rfid_para_puerta(payload)
    
    elif topic == MQTT_TOPIC_PESO:
        # MODULO 2: ESP8266 Bascula envia peso en kg (como string)
        print(f"\n[DEBUG] MODULO 2: Payload recibido (raw): '{payload}' (tipo: {type(payload)})")
        
        try:
            # ✅ FIX 1: Reemplazar coma por punto (por si acaso)
            payload_limpio = payload.replace(',', '.')
            
            # ✅ FIX 2: Convertir a float
            peso = float(payload_limpio)
            
            print(f"[INFO] MODULO 2: Peso convertido: {peso:.3f} kg")
            
            # ✅ FIX 3: Validar rango mínimo (0.100 kg en lugar de 0.5)
            if peso < 0.0:
                print(f"[WARNING] Peso negativo: {peso:.3f} kg - Ajustando a 0.0")
                peso = 0.0
            elif peso < 0.100:
                print(f"[WARNING] Peso muy bajo: {peso:.3f} kg (mínimo: 0.100 kg)")
            elif peso > 50.0:
                print(f"[WARNING] Peso muy alto: {peso:.2f} kg")
            
            # ✅ FIX 4: SIEMPRE guardar en BD, sin importar el valor
            registrar_peso_equipaje(peso)
            print(f"[OK] Peso {peso:.3f} kg procesado correctamente")
            
        except ValueError as e:
            # ✅ FIX 5: Si falla conversión, guardar 0.0 como marca de error
            print(f"[ERROR] MODULO 2: No se pudo convertir a float: '{payload}'")
            print(f"[ERROR] Tipo de dato: {type(payload)}, Longitud: {len(payload)}")
            print(f"[ERROR] Bytes (hex): {payload.encode('utf-8').hex()}")
            print(f"[ERROR] Detalle: {e}")
            print(f"[INFO] Guardando peso 0.0 como registro de error...")
            registrar_peso_equipaje(0.0)
        except Exception as e:
            # ✅ FIX 6: Capturar cualquier otro error
            print(f"[ERROR] MODULO 2: Error inesperado procesando peso")
            print(f"[ERROR] Payload: '{payload}'")
            print(f"[ERROR] Error: {e}")
            import traceback
            traceback.print_exc()
            print(f"[INFO] Guardando peso 0.0 como registro de error...")
            registrar_peso_equipaje(0. 0)

def verificar_rfid_para_puerta(rfid_uid):
    """
    MODULO 3: Verificar si un RFID puede abrir la puerta fisica
    
    Si todo OK:
    1. Envía "ABRIR" al ESP8266
    2. Actualiza accesos_puerta. puerta_abierta = 1
    3. Actualiza pasajeros.estado = 'COMPLETO'
    4. Guarda con COMMIT
    """
    conn = get_db_connection()
    if not conn:
        print("[ERROR] No se pudo conectar a la base de datos")
        mqtt_client.publish(MQTT_TOPIC_PUERTA_RESPUESTA, "DENEGAR")
        return
    
    cursor = None
    
    try:
        cursor = conn.cursor()
        
        # ============================================
        # PASO 1: BUSCAR PASAJERO POR RFID
        # ============================================
        cursor.execute("""
            SELECT p.id_pasajero, p.nombre_normalizado, p.estado,
                   a.id_acceso, a.puerta_abierta
            FROM pasajeros p
            LEFT JOIN accesos_puerta a ON p.id_pasajero = a.id_pasajero
            WHERE p.rfid_uid = %s
        """, (rfid_uid,))
        
        resultado = cursor.fetchone()
        
        if not resultado:
            print(f"[ERROR] RFID {rfid_uid} no encontrado en sistema")
            mqtt_client.publish(MQTT_TOPIC_PUERTA_RESPUESTA, "DENEGAR")
            return
        
        id_pasajero = resultado['id_pasajero']
        id_acceso = resultado['id_acceso']
        nombre = resultado['nombre_normalizado']
        estado_actual = resultado['estado']
        puerta_usada = resultado['puerta_abierta']
        
        print(f"\n[INFO] Pasajero encontrado: {nombre}")
        print(f"[INFO] ID Pasajero: {id_pasajero}")
        print(f"[INFO] ID Acceso: {id_acceso}")
        print(f"[INFO] Estado actual: {estado_actual}")
        print(f"[INFO] Puerta usada: {puerta_usada}")
        
        # ============================================
        # PASO 2: VALIDACIONES
        # ============================================
        
        # Validación 1: Tiene check-in completado?  
        if not id_acceso:
            print(f"[ERROR] Sin check-in facial completado")
            print(f"[INFO] Debe pasar primero por Módulo 1")
            mqtt_client.publish(MQTT_TOPIC_PUERTA_RESPUESTA, "DENEGAR")
            return
        
        # Validación 2: Estado es ABORDADO?
        if estado_actual != 'ABORDADO':
            print(f"[ERROR] Estado inválido: {estado_actual} (se requiere ABORDADO)")
            mqtt_client.publish(MQTT_TOPIC_PUERTA_RESPUESTA, "DENEGAR")
            return
        
        # Validación 3: NO ha usado la puerta antes?
        if puerta_usada:
            print(f"[ERROR] Esta tarjeta ya fue usada para abrir la puerta")
            print(f"[INFO] Solo se permite un acceso por pasajero")
            mqtt_client.publish(MQTT_TOPIC_PUERTA_RESPUESTA, "DENEGAR")
            return
        
        # ============================================
        # PASO 3: AUTORIZAR ACCESO
        # ============================================
        print("\n" + "="*60)
        print(f"[OK] ✓✓✓ ACCESO AUTORIZADO ✓✓✓")
        print(f"[OK] Pasajero: {nombre}")
        print(f"[OK] RFID: {rfid_uid}")
        print("="*60)
        
        # Enviar señal ABRIR al ESP8266
        mqtt_client.publish(MQTT_TOPIC_PUERTA_RESPUESTA, "ABRIR")
        print("[MQTT] ✓ Señal ABRIR enviada al ESP8266")
        
        # ============================================
        # PASO 4: ACTUALIZAR BASE DE DATOS
        # ============================================
        print("\n[INFO] === ACTUALIZANDO BASE DE DATOS ===")
        
        # UPDATE 1: Marcar puerta como usada
        print(f"[INFO] 1/2: Actualizando accesos_puerta (id_acceso={id_acceso})...")
        cursor.execute("""
            UPDATE accesos_puerta 
            SET puerta_abierta = 1,
                fecha_hora = NOW()
            WHERE id_acceso = %s
        """, (id_acceso,))
        
        filas_1 = cursor.rowcount
        print(f"[DEBUG] Filas afectadas: {filas_1}")
        
        if filas_1 > 0:
            print(f"[OK] ✓ accesos_puerta actualizado (puerta_abierta = 1)")
        else:
            print(f"[WARNING] No se actualizó ninguna fila en accesos_puerta")
        
        # UPDATE 2: Cambiar estado del pasajero a COMPLETO
        print(f"[INFO] 2/2: Actualizando pasajeros (id_pasajero={id_pasajero})...")
        cursor.execute("""
            UPDATE pasajeros 
            SET estado = 'COMPLETO'
            WHERE id_pasajero = %s
        """, (id_pasajero,))
        
        filas_2 = cursor.rowcount
        print(f"[DEBUG] Filas afectadas: {filas_2}")
        
        if filas_2 > 0:
            print(f"[OK] ✓ Estado actualizado (ABORDADO → COMPLETO)")
        else:
            print(f"[WARNING] No se actualizó ninguna fila en pasajeros")
        
        # COMMIT: Guardar cambios permanentemente
        print("\n[INFO] Ejecutando COMMIT para guardar cambios...")
        conn.commit()
        print("[OK] ✓✓✓ COMMIT EXITOSO - Cambios guardados en BD")
        
        # ============================================
        # PASO 5: VERIFICAR QUE SE GUARDARON LOS CAMBIOS
        # ============================================
        print("\n[INFO] === VERIFICANDO CAMBIOS EN BD ===")
        cursor.execute("""
            SELECT p.estado, a.puerta_abierta, a.fecha_hora
            FROM pasajeros p
            LEFT JOIN accesos_puerta a ON p.id_pasajero = a.id_pasajero
            WHERE p. id_pasajero = %s
        """, (id_pasajero,))
        
        verificacion = cursor.fetchone()
        
        print(f"[VERIFICACIÓN] Estado del pasajero: {verificacion['estado']}")
        print(f"[VERIFICACIÓN] puerta_abierta: {verificacion['puerta_abierta']}")
        print(f"[VERIFICACIÓN] fecha_hora: {verificacion['fecha_hora']}")
        
        # Validar que TODO se guardó correctamente
        if verificacion['estado'] == 'COMPLETO' and verificacion['puerta_abierta'] == 1:
            print("\n[OK] ✓✓✓ VERIFICACIÓN EXITOSA ✓✓✓")
            print("[OK] Base de datos actualizada correctamente")
        else:
            print("\n[WARNING] ⚠ VERIFICACIÓN FALLIDA ⚠")
            print("[WARNING] Los cambios NO se guardaron correctamente")
            print(f"[DEBUG] Esperado: estado='COMPLETO', puerta_abierta=1")
            print(f"[DEBUG] Obtenido: estado='{verificacion['estado']}', puerta_abierta={verificacion['puerta_abierta']}")
        
        print("="*60)
        print(f"[RESUMEN] Pasajero {nombre} - Proceso COMPLETO")
        print("="*60 + "\n")
        
    except Exception as e:
        print("\n" + "="*60)
        print("[ERROR] ✗✗✗ ERROR EN VERIFICACIÓN ✗✗✗")
        print(f"[ERROR] {e}")
        print("="*60)
        
        import traceback
        traceback.print_exc()
        
        # Hacer rollback para deshacer cambios parciales
        try:
            conn.rollback()
            print("[INFO] Rollback ejecutado - Cambios revertidos")
        except:
            pass
        
        # Denegar acceso si hay error
        mqtt_client.publish(MQTT_TOPIC_PUERTA_RESPUESTA, "DENEGAR")
        
    finally:
        # Cerrar cursor y conexión
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            print("[DEBUG] Conexión a BD cerrada\n")

def registrar_peso_equipaje(peso_kg):
    """
    MODULO 2: Registrar peso recibido de ESP8266 Bascula
    """
    conn = get_db_connection()
    if not conn:
        print("[ERROR] No se pudo conectar a la base de datos")
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO pesos_equipaje (peso_kg, fecha_registro)
            VALUES (%s, NOW())
        """, (peso_kg,))
        
        conn.commit()
        print(f"[OK] Peso {peso_kg:.2f} kg registrado en BD")
        
        # Mostrar advertencia si hay sobrepeso
        if peso_kg > 2.0:
            print(f"[WARNING] SOBREPESO detectado: {peso_kg:.2f} kg (límite: 23 kg)")
        
    except Exception as e:
        print(f"[ERROR] Error registrando peso: {e}")
    finally:
        cursor.close()
        conn.close()

mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.on_message = on_message

# ========================================
# INICIAR MQTT CON MANEJO DE ERRORES
# ========================================
try:
    print(f"[INFO] Conectando a MQTT: {MQTT_BROKER}:{MQTT_PORT}")
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
    print("[OK] MQTT habilitado para Modulos 2 y 3")
except Exception as e:
    print(f"[WARNING] MQTT no disponible: {e}")
    print("[INFO] Solo Modulo 1 estara operativo")
    mqtt_conectado = False

# ========================================
# FUNCIONES AUXILIARES
# ========================================

def leer_rfid(timeout=30):
    """
    Leer tarjeta RFID y retornar UID en formato HEXADECIMAL
    RECORTA A 8 CARACTERES (4 bytes) para compatibilidad con ESP8266
    """
    if not RFID_DISPONIBLE:
        # Modo simulación
        simulated_id = format(int(time.time() * 1000) % 0xFFFFFFFF, '08X')
        print(f"[SIMULACION] RFID generado: {simulated_id}")
        return simulated_id
    
    # ADQUIRIR LOCK - Solo un thread puede leer RFID a la vez
    if not rfid_lock.acquire(blocking=True, timeout=5):
        print("[ERROR] No se pudo adquirir lock para leer RFID (otro proceso leyendo)")
        return None
    
    try:
        print(f"[INFO] Esperando tarjeta RFID (timeout {timeout}s)...")
        print("[DEBUG] Lock adquirido - iniciando lectura...")
        
        # Variables compartidas entre threads
        resultado = {'rfid': None, 'error': None, 'completado': False}
        
        def leer_bloqueante():
            """Thread interno que ejecuta reader.read() bloqueante"""
            try:
                id, text = reader.read()  # BLOQUEANTE
                
                # Convertir ID a HEXADECIMAL (formato estándar)
                rfid_hex_completo = format(id, 'X').upper()
                
                # RECORTAR A 8 CARACTERES (primeros 4 bytes)
                # Esto hace que coincida con lo que lee el ESP8266
                if len(rfid_hex_completo) > 8:
                    rfid_hex = rfid_hex_completo[:8]  # Solo primeros 8 caracteres
                    print(f"[INFO] RFID completo: {rfid_hex_completo}")
                    print(f"[INFO] RFID recortado (8 chars): {rfid_hex}")
                else:
                    rfid_hex = rfid_hex_completo.zfill(8)  # Rellenar con ceros si es corto
                
                resultado['rfid'] = rfid_hex
                resultado['completado'] = True
                
                print(f"[OK] RFID leído: {rfid_hex}")
                print(f"[DEBUG] ID decimal original: {id}")
                
            except Exception as e:
                resultado['error'] = str(e)
                resultado['completado'] = True
                print(f"[ERROR] Error leyendo RFID: {e}")
        
        # Crear thread de lectura
        thread_lectura = threading.Thread(target=leer_bloqueante, daemon=True)
        thread_lectura.start()
        
        # Esperar con timeout
        thread_lectura.join(timeout=timeout)
        
        # Verificar si terminó
        if not resultado['completado']:
            print(f"[TIMEOUT] No se detectó tarjeta en {timeout}s")
            return None
        
        if resultado['error']:
            print(f"[ERROR] Error durante lectura: {resultado['error']}")
            return None
        
        return resultado['rfid']
        
    finally:
        # LIBERAR LOCK - Permitir que otro thread lea
        rfid_lock.release()
        print("[DEBUG] Lock liberado")

def capturar_rostro():
    """Capturar rostro con la camara y extraer embedding"""
    cap = None
    try:
        print("[INFO] Iniciando captura de rostro...")
        
        # Usar explícitamente /dev/video0 con backend V4L2
        print("[DEBUG] Abriendo /dev/video0 con V4L2...")
        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        
        if not cap.isOpened():
            print("[ERROR] No se pudo acceder a /dev/video0")
            return None
        
        print("[OK] Cámara abierta correctamente")
        
        # Configurar resolución óptima
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        # Dar tiempo a la camara para inicializar
        print("[INFO] Inicializando cámara (2s)...")
        time.sleep(2)
        
        # Descartar primeros 5 frames (pueden estar en negro o mal expuestos)
        print("[DEBUG] Descartando frames de calentamiento...")
        for i in range(5):
            cap.read()
        
        intentos = 0
        max_intentos = 30  # 30 frames = ~10 segundos
        
        print("[INFO] Buscando rostro en el frame...")
        
        while intentos < max_intentos:
            ret, frame = cap.read()
            
            if not ret or frame is None or frame.size == 0:
                print(f"[WARNING] Intento {intentos+1}/{max_intentos}: Frame inválido")
                intentos += 1
                time.sleep(0.3)
                continue
            
            print(f"[DEBUG] Frame {intentos+1}: {frame.shape} - Analizando...")
            
            # Convertir BGR (OpenCV) a RGB (face_recognition)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detectar rostros
            face_locations = face_recognition.face_locations(rgb_frame)
            
            if len(face_locations) > 0:
                print(f"[OK] ✓ Rostro detectado en intento {intentos+1}")
                print(f"[DEBUG] Ubicaciones: {face_locations}")
                
                # Extraer encoding del primer rostro
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                
                if len(face_encodings) > 0:
                    embedding = face_encodings[0]
                    cap.release()
                    print(f"[OK] ✓ Embedding facial extraído correctamente - Shape: {embedding.shape}")
                    return embedding
                else:
                    print("[WARNING] Rostro detectado pero no se pudo extraer encoding")
            else:
                print(f"[DEBUG] No se detectó rostro en frame {intentos+1}")
            
            intentos += 1
            time.sleep(0.3)
        
        cap.release()
        print(f"[ERROR] ✗ No se detectó ningún rostro después de {max_intentos} intentos (~10s)")
        return None
        
    except Exception as e:
        print(f"[ERROR] ✗ Error capturando rostro: {e}")
        import traceback
        traceback.print_exc()
        if cap:
            cap.release()
        return None

# ========================================
# ENDPOINTS - SISTEMA
# ========================================

@app. route('/api/health', methods=['GET'])
def health_check():
    """Verificar estado del sistema"""
    return jsonify({
        'status': 'ok',
        'modulo': 'SmartPort v2.0',
        'mqtt': 'conectado' if mqtt_conectado else 'desconectado',
        'rfid': 'disponible' if RFID_DISPONIBLE else 'simulado',
        'broker': MQTT_BROKER,
        'formato_rfid': 'HEXADECIMAL (8 caracteres)'
    })

# ========================================
# ENDPOINTS - ADMINISTRADOR
# ========================================

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """Verificar acceso de administrador por RFID"""
    try:
        print("\n=== INICIO LOGIN ADMIN ===")
        
        # Leer RFID
        rfid_uid = leer_rfid(timeout=15)
        
        if not rfid_uid:
            print("[ERROR] No se detecto tarjeta RFID")
            return jsonify({
                'status': 'error',
                'error': 'No se detecto tarjeta RFID'
            }), 400
        
        print(f"[INFO] RFID detectado: {rfid_uid}")
        
        # Verificar si es admin
        admin = verificar_admin(rfid_uid)
        
        if admin:
            print(f"[OK] Admin verificado: {admin['nombre']}")
            return jsonify({
                'status': 'ok',
                'admin': {
                    'id': admin['id_admin'],
                    'nombre': admin['nombre'],
                    'rfid': admin['rfid_uid']
                }
            })
        else:
            print("[ERROR] RFID no autorizado")
            return jsonify({
                'status': 'error',
                'error': 'Acceso denegado - RFID no autorizado'
            }), 403
            
    except Exception as e:
        print(f"[ERROR] Error en login admin: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/admin/registrar-admin', methods=['POST'])
def registrar_nuevo_admin():
    """Registrar un nuevo administrador"""
    try:
        data = request.json
        nombre = data.get('nombre', '').strip()
        
        if not nombre:
            return jsonify({
                'status': 'error',
                'error': 'El nombre es requerido'
            }), 400
        
        print(f"\n=== REGISTRAR NUEVO ADMIN: {nombre} ===")
        
        # Leer RFID
        rfid_uid = leer_rfid(timeout=15)
        
        if not rfid_uid:
            print("[ERROR] No se detecto tarjeta RFID")
            return jsonify({
                'status': 'error',
                'error': 'No se detecto tarjeta RFID'
            }), 400
        
        # Registrar admin
        if registrar_admin(rfid_uid, nombre):
            print(f"[OK] Admin registrado: {nombre} - RFID: {rfid_uid}")
            return jsonify({
                'status': 'ok',
                'mensaje': f'Administrador {nombre} registrado correctamente',
                'rfid_uid': rfid_uid
            })
        else:
            print("[ERROR] Error al registrar (posible RFID duplicado)")
            return jsonify({
                'status': 'error',
                'error': 'Error al registrar administrador (posible RFID duplicado)'
            }), 400
            
    except Exception as e:
        print(f"[ERROR] Error registrando admin: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/admin/listar-admins', methods=['GET'])
def obtener_admins():
    """Listar todos los administradores"""
    try:
        admins = listar_admins()
        return jsonify({
            'status': 'ok',
            'admins': admins
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/admin/crear-pasajero', methods=['POST'])
def admin_crear_pasajero():
    """Crear un nuevo pasajero (solo nombre y vuelo)"""
    try:
        data = request.json
        nombre = data.get('nombre', '').strip()
        numero_vuelo = data.get('numero_vuelo')
        
        if not nombre or not numero_vuelo:
            return jsonify({
                'status': 'error',
                'error': 'Nombre y numero de vuelo son requeridos'
            }), 400
        
        print(f"\n=== CREAR PASAJERO ===")
        print(f"Nombre: {nombre}")
        print(f"Vuelo: {numero_vuelo}")
        
        # Crear pasajero
        pasajero = crear_pasajero(nombre, numero_vuelo)
        
        if pasajero:
            print(f"[OK] Pasajero creado - ID: {pasajero['id_pasajero']}")
            return jsonify({
                'status': 'ok',
                'pasajero': {
                    'id_pasajero': pasajero['id_pasajero'],
                    'nombre': pasajero['nombre_normalizado'],
                    'numero_vuelo': pasajero['numero_vuelo'],
                    'destino': pasajero['destino']
                }
            })
        else:
            print("[ERROR] Error al crear pasajero")
            return jsonify({
                'status': 'error',
                'error': 'Error al crear pasajero'
            }), 500
            
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/admin/registrar-rfid', methods=['POST'])
def admin_registrar_rfid():
    """
    Leer RFID del pasajero (NO guardar en BD todavía)
    Solo retornar el UID leído para guardarlo temporalmente en frontend
    REGISTRO ATÓMICO: Se guardará junto con el rostro en completar-registro
    """
    try:
        data = request.json
        id_pasajero = data.get('id_pasajero')
        
        if not id_pasajero:
            return jsonify({
                'status': 'error',
                'error': 'ID de pasajero requerido'
            }), 400
        
        print(f"\n=== LEER RFID (TEMPORAL) - Pasajero ID: {id_pasajero} ===")
        print("[INFO] SOLO lectura, NO se guardará en BD todavía")
        
        # Leer RFID
        rfid_uid = leer_rfid(timeout=15)
        
        if not rfid_uid:
            print("[ERROR] No se detecto tarjeta RFID")
            return jsonify({
                'status': 'error',
                'error': 'No se detecto tarjeta RFID'
            }), 400
        
        print(f"[OK] RFID leído: {rfid_uid}")
        print("[INFO] RFID guardado temporalmente en frontend")
        print("[INFO] Se registrará en BD junto con el rostro en el siguiente paso")
        
        # NO GUARDAR EN BD, solo retornar
        return jsonify({
            'status': 'ok',
            'rfid_uid': rfid_uid,
            'mensaje': 'RFID leído correctamente (pendiente de registro completo)'
        })
            
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/admin/completar-registro', methods=['POST'])
def admin_completar_registro():
    """
    Completar registro: Guardar RFID + rostro juntos en la BD
    También crea el registro de check-in en accesos_puerta (necesario para Módulo 3)
    REGISTRO ATÓMICO: Todo o nada
    """
    try:
        data = request.json
        id_pasajero = data.get('id_pasajero')
        rfid_uid = data.get('rfid_uid')
        
        if not id_pasajero or not rfid_uid:
            return jsonify({
                'status': 'error',
                'error': 'ID de pasajero y RFID son requeridos'
            }), 400
        
        print(f"\n{'='*60}")
        print(f"=== COMPLETAR REGISTRO ATÓMICO - Pasajero ID: {id_pasajero} ===")
        print(f"RFID: {rfid_uid}")
        print(f"{'='*60}")
        
        # PASO 1: Registrar RFID en BD
        print("[INFO] Paso 1/3: Registrando RFID en BD...")
        if not registrar_rfid_pasajero(id_pasajero, rfid_uid):
            print("[ERROR] Error al registrar RFID")
            return jsonify({
                'status': 'error',
                'error': 'Error al registrar RFID (posible RFID duplicado)'
            }), 400
        
        print("[OK] ✓ RFID registrado correctamente en BD")
        
        # PASO 2: Capturar y registrar rostro
        print("[INFO] Paso 2/3: Capturando rostro...")
        embedding = capturar_rostro()
        
        if embedding is None:
            # Si falla el rostro, REVERTIR el RFID (eliminar de BD)
            print("[ERROR] No se pudo capturar rostro - REVIRTIENDO registro de RFID")
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE pasajeros 
                        SET rfid_uid = NULL 
                        WHERE id_pasajero = %s
                    """, (id_pasajero,))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    print("[INFO] ✓ RFID eliminado de BD por fallo en captura de rostro")
                    print("[INFO] Transacción revertida - BD mantiene consistencia")
                except Exception as e:
                    print(f"[ERROR] Error al revertir RFID: {e}")
            
            return jsonify({
                'status': 'error',
                'error': 'No se pudo capturar el rostro.  Intente nuevamente.'
            }), 400
        
        print(f"[OK] ✓ Rostro capturado - Shape: {embedding.shape}")
        
        # PASO 3: Guardar rostro en BD Y crear check-in
        print("[INFO] Paso 3/3: Guardando rostro y creando check-in...")
        if not registrar_rostro_pasajero(id_pasajero, embedding):
            print("[ERROR] Error al guardar rostro")
            # Intentar revertir RFID también
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE pasajeros 
                        SET rfid_uid = NULL 
                        WHERE id_pasajero = %s
                    """, (id_pasajero,))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    print("[INFO] RFID eliminado de BD por fallo al guardar rostro")
                except:
                    pass
            
            return jsonify({
                'status': 'error',
                'error': 'Error al guardar el rostro'
            }), 500
        
        print("[OK] ✓ Rostro registrado correctamente en BD")
        print("[OK] ✓ Check-in creado en accesos_puerta (Módulo 3 habilitado)")
        print(f"{'='*60}")
        print("[OK] ✓✓✓ REGISTRO COMPLETO EXITOSO ✓✓✓")
        print(f"[OK] Pasajero ID {id_pasajero} registrado con:")
        print(f"[OK]   - RFID: {rfid_uid}")
        print(f"[OK]   - Rostro: Embedding de {embedding.shape[0]} dimensiones")
        print(f"[OK]   - Estado: VALIDADO")
        print(f"[OK]   - Check-in: Completado (puede usar Módulo 3)")
        print(f"{'='*60}\n")
        
        return jsonify({
            'status': 'ok',
            'mensaje': 'Registro completado exitosamente',
            'rfid': rfid_uid
        })
        
    except Exception as e:
        print(f"[ERROR] Excepción en completar_registro: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# ========================================
# ENDPOINTS - USUARIO (ACCESO) - MODULO 1
# ========================================

@app.route('/api/usuario/validar-rfid', methods=['POST'])
def usuario_validar_rfid():
    """
    PASO 1: Solo validar que el RFID existe en BD
    NO cambia el estado del pasajero
    NO captura rostro todavía
    """
    try:
        print("\n" + "="*60)
        print("=== PASO 1: VALIDACIÓN DE RFID ===")
        print("="*60)
        
        rfid_uid = leer_rfid(timeout=15)
        
        if not rfid_uid:
            print("[ERROR] No se detectó tarjeta RFID")
            return jsonify({
                'status': 'error',
                'error': 'No se detectó tarjeta RFID'
            }), 400
        
        print(f"[OK] RFID detectado: {rfid_uid}")
        
        # Buscar pasajero con ese RFID
        pasajero = buscar_pasajero_por_rfid(rfid_uid)
        
        if not pasajero:
            print("[ERROR] RFID no encontrado en la base de datos")
            return jsonify({
                'status': 'error',
                'error': 'RFID no registrado'
            }), 404
        
        print(f"[OK] Pasajero encontrado: {pasajero['nombre_normalizado']}")
        print(f"[INFO] Vuelo: {pasajero['numero_vuelo']} - Destino: {pasajero['destino']}")
        print(f"[INFO] Estado actual: {pasajero['estado']}")
        
        # VALIDACIÓN 1: Si ya completó el proceso (ABORDADO o COMPLETO), no puede volver a verificar
        if pasajero['estado'] in ['ABORDADO', 'COMPLETO']:
            print(f"[INFO] Pasajero ya completó el proceso - Estado: {pasajero['estado']}")
            return jsonify({
                'status': 'error',
                'error': 'Ya completó el proceso de abordaje',
                'estado_actual': pasajero['estado']
            }), 403
        
        # VALIDACIÓN 2: Verificar que tenga rostro registrado
        if pasajero['rostro_embedding'] is None:
            print("[ERROR] Pasajero sin rostro registrado")
            return jsonify({
                'status': 'error',
                'error': 'Pasajero sin biometria registrada'
            }), 400
        
        # TODO OK - RFID válido, retornar datos del pasajero
        print("[OK] RFID válido - Listo para captura de rostro")
        print("="*60 + "\n")
        
        return jsonify({
            'status': 'ok',
            'pasajero': {
                'id_pasajero': pasajero['id_pasajero'],
                'nombre': pasajero['nombre_normalizado'],
                'vuelo': pasajero['numero_vuelo'],
                'destino': pasajero['destino']
            }
        })
        
    except Exception as e:
        print(f"[ERROR] Error en validación de RFID: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/usuario/verificar-rostro', methods=['POST'])
def usuario_verificar_rostro():
    """
    PASO 2: Capturar y verificar rostro
    SOLO si la verificación es exitosa, cambia el estado a ABORDADO
    """
    try:
        data = request.json
        id_pasajero = data.get('id_pasajero')
        
        if not id_pasajero:
            return jsonify({
                'status': 'error',
                'error': 'ID de pasajero requerido'
            }), 400
        
        print("\n" + "="*60)
        print("=== PASO 2: VERIFICACIÓN DE ROSTRO ===")
        print(f"ID Pasajero: {id_pasajero}")
        print("="*60)
        
        # Buscar pasajero por ID (necesitamos crear esta función o usar buscar_pasajero_por_rfid)
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'status': 'error',
                'error': 'Error de conexión a BD'
            }), 500
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id_pasajero, nombre_normalizado, numero_vuelo, destino, 
                   rostro_embedding, estado
            FROM pasajeros
            WHERE id_pasajero = %s
        """, (id_pasajero,))
        
        pasajero = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not pasajero:
            print("[ERROR] Pasajero no encontrado")
            return jsonify({
                'status': 'error',
                'error': 'Pasajero no encontrado'
            }), 404
        
        print(f"[INFO] Pasajero: {pasajero['nombre_normalizado']}")
        
        # Capturar rostro actual
        print("[INFO] Capturando rostro actual...")
        embedding_actual = capturar_rostro()
        
        if embedding_actual is None:
            print("[ERROR] No se pudo capturar rostro")
            # NO cambiar estado
            return jsonify({
                'status': 'error',
                'error': 'No se detectó rostro'
            }), 400
        
        print("[OK] Rostro capturado correctamente")
        
        # Comparar rostros
        print("[INFO] Comparando rostros...")
        porcentaje_similitud = calcular_similitud_facial(
            pasajero['rostro_embedding'],
            embedding_actual
        )
        
        print(f"[OK] Similitud facial: {porcentaje_similitud:.2f}%")
        
        # Decidir si permitir acceso (umbral 60%)
        if porcentaje_similitud >= 60.0:
            print("="*60)
            print("[OK] ✓✓✓ ACCESO CONCEDIDO ✓✓✓")
            print("="*60)
            
            # AQUÍ SÍ: Registrar acceso en BD (cambia estado a ABORDADO)
            print("[INFO] Registrando acceso y cambiando estado a ABORDADO...")
            registrar_acceso(pasajero['id_pasajero'], porcentaje_similitud)
            print("[OK] Estado actualizado a ABORDADO")
            print("[INFO] Pasajero ahora puede usar Módulo 3 (puerta física)")
            
            print("="*60)
            print(f"BIENVENIDO: {pasajero['nombre_normalizado']}")
            print(f"VUELO: {pasajero['numero_vuelo']} -> {pasajero['destino']}")
            print("="*60 + "\n")
            
            return jsonify({
                'status': 'ok',
                'acceso': 'concedido',
                'pasajero': {
                    'nombre': pasajero['nombre_normalizado'],
                    'vuelo': pasajero['numero_vuelo'],
                    'destino': pasajero['destino']
                },
                'similitud': round(porcentaje_similitud, 2),
                'mensaje': f'Bienvenido {pasajero["nombre_normalizado"]}'
            })
        else:
            print("="*60)
            print("[ERROR] ACCESO DENEGADO")
            print(f"[INFO] Similitud insuficiente: {porcentaje_similitud:.2f}% (mínimo: 60%)")
            print("="*60 + "\n")
            
            # NO cambiar estado
            return jsonify({
                'status': 'error',
                'acceso': 'denegado',
                'error': 'Biometria no coincide',
                'similitud': round(porcentaje_similitud, 2)
            }), 403
            
    except Exception as e:
        print("="*60)
        print("[ERROR] ERROR EN VERIFICACIÓN")
        print(f"[ERROR] Error: {e}")
        print("="*60 + "\n")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# ========================================
# ENDPOINTS - DASHBOARD
# ========================================

@app.route('/api/admin/dashboard-pesos', methods=['GET'])
def dashboard_pesos():
    """
    Obtener los últimos pesos registrados
    Límite de sobrepeso: 2 kg
    """
    try:
        # Parámetros opcionales
        limite = request.args.get('limite', 50, type=int)  # Default: últimos 50
        
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'status': 'error',
                'error': 'Error de conexión a BD'
            }), 500
        
        cursor = conn.cursor()
        
        # ✅ CORREGIDO: Quitar espacio en 1.5
        cursor.execute("""
            SELECT 
                id_peso,
                peso_kg,
                fecha_hora,
                CASE 
                    WHEN peso_kg > 2.0 THEN 'SOBREPESO'
                    WHEN peso_kg > 1.5 THEN 'ADVERTENCIA'
                    ELSE 'NORMAL'
                END as estado
            FROM pesos_equipaje
            ORDER BY fecha_hora DESC
            LIMIT %s
        """, (limite,))
        
        pesos = cursor.fetchall()
        
        # Estadísticas (AJUSTADO: límite 2kg)
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                AVG(peso_kg) as promedio,
                MAX(peso_kg) as maximo,
                MIN(peso_kg) as minimo,
                SUM(CASE WHEN peso_kg > 2.0 THEN 1 ELSE 0 END) as sobrepesos
            FROM pesos_equipaje
            WHERE DATE(fecha_hora) = CURDATE()
        """)
        
        stats = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'pesos': pesos,
            'estadisticas': {
                'total_hoy': stats['total'] or 0,
                'promedio': round(stats['promedio'], 2) if stats['promedio'] else 0,
                'maximo': round(stats['maximo'], 2) if stats['maximo'] else 0,
                'minimo': round(stats['minimo'], 2) if stats['minimo'] else 0,
                'sobrepesos': stats['sobrepesos'] or 0
            }
        })
        
    except Exception as e:
        print(f"[ERROR] Error en dashboard-pesos: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


# ========================================
# INICIAR SERVIDOR
# ========================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("SMARTPORT v2.0 - SISTEMA COMPLETO")
    print("Sistema Inteligente de Control Aeroportuario")
    print("="*60)
    print("MÓDULOS OPERATIVOS:")
    print("  • Módulo 1: Registro biométrico (Raspberry Pi)")
    if mqtt_conectado:
        print("  • Módulo 2: Báscula inteligente (ESP8266)")
        print("  • Módulo 3: Control de puerta (ESP8266)")
    else:
        print("  • Módulo 2: No disponible (MQTT desconectado)")
        print("  • Módulo 3: No disponible (MQTT desconectado)")
    print("="*60)
    print(f"RFID Local: {'Conectado' if RFID_DISPONIBLE else 'Modo simulación'}")
    print(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"Estado MQTT: {'Conectado ✓' if mqtt_conectado else 'Desconectado ✗'}")
    print(f"Formato RFID: HEXADECIMAL (8 caracteres/4 bytes)")
    print("="*60)
    print("CARACTERÍSTICAS:")
    print("  ✓ Registro atómico (RFID + Rostro juntos)")
    print("  ✓ Check-in automático al completar registro")
    print("  ✓ Integración completa con ESP8266")
    print("  ✓ Verificación biométrica facial")
    print("  ✓ Control de acceso con apertura de puerta")
    print("  ✓ Registro de pesos de equipaje")
    print("  ✓ Formato RFID 8 chars (compatible ESP8266)")
    print("  ✓ NUEVO: Validación RFID separada del rostro")
    print("="*60)
    print("Flask Server: http://0.0.0.0:5000")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

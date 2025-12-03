"""
app.py - API REST para SmartPort v2.0
Sistema de registro y acceso con RFID + Reconocimiento facial

MODULO 1: Registro y validacion biometrica (NO abre puertas fisicas)
MODULO 2: Recepcion de datos de peso via MQTT (preparado para futuro)
MODULO 3: Control de puerta fisica via MQTT (preparado para futuro)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import paho.mqtt.client as mqtt
import os
import cv2
import face_recognition
import numpy as np
import time

# Importar funciones de base de datos
from db import (
    verificar_admin, registrar_admin, listar_admins,
    crear_pasajero, registrar_rfid_pasajero, registrar_rostro_pasajero,
    buscar_pasajero_por_rfid, registrar_acceso, calcular_similitud_facial
)

# Intentar importar MFRC522 (puede fallar si no esta conectado)
try:
    from mfrc522 import SimpleMFRC522
    reader = SimpleMFRC522()
    RFID_DISPONIBLE = True
except:
    print("[WARNING] MFRC522 no disponible - Usando modo simulacion")
    RFID_DISPONIBLE = False

app = Flask(__name__)
CORS(app)

# ========================================
# CONFIGURACION MQTT
# ========================================

MQTT_BROKER = os.environ.get("MQTT_BROKER", "broker.mqtt. cool")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_TOPIC_VERIFICAR_RFID = "aeropuerto/verificar_rfid"  # ESP32 Puerta envia RFID
MQTT_TOPIC_PUERTA_RESPUESTA = "aeropuerto/puerta/respuesta"  # Raspberry responde
MQTT_TOPIC_PESO = "aeropuerto/peso"  # ESP32 Bascula envia peso

# ========================================
# FIX para Python 3.13: Usar CallbackAPIVersion
# ========================================
try:
    # Python 3.13+ requiere especificar la version del API
    mqtt_client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
        client_id="RaspberryPi_Aeropuerto"
    )
except AttributeError:
    # Fallback para versiones antiguas de paho-mqtt
    mqtt_client = mqtt.Client(client_id="RaspberryPi_Aeropuerto")

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
    Modulo 2: Recibe pesos de bascula
    Modulo 3: Recibe solicitudes de verificacion de RFID desde ESP32 Puerta
    """
    topic = msg.topic
    payload = msg.payload.decode('utf-8')
    
    if topic == MQTT_TOPIC_VERIFICAR_RFID:
        # MODULO 3: ESP32 Puerta solicita verificar RFID
        print(f"\n[INFO] MODULO 3: ESP32 Puerta solicita verificar RFID: {payload}")
        verificar_rfid_para_puerta(payload)
    
    elif topic == MQTT_TOPIC_PESO:
        # MODULO 2: ESP32 Bascula envia peso
        print(f"\n[INFO] MODULO 2: Peso recibido: {payload} kg")
        registrar_peso_equipaje(float(payload))

def verificar_rfid_para_puerta(rfid_uid):
    """
    MODULO 3: Verificar si un RFID puede abrir la puerta fisica
    Valida que:
    1.  Tenga registro en accesos_puerta (paso check-in en Modulo 1)
    2. Estado = ABORDADO
    3. NO haya abierto la puerta antes (puerta_abierta = FALSE)
    """
    from db import get_db_connection
    
    conn = get_db_connection()
    if not conn:
        print("[ERROR] No se pudo conectar a la base de datos")
        mqtt_client.publish(MQTT_TOPIC_PUERTA_RESPUESTA, "DENEGAR")
        return
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Buscar pasajero por RFID
        cursor.execute("""
            SELECT p.id_pasajero, p.nombre_normalizado, p. estado,
                   a.id_acceso, a.puerta_abierta
            FROM pasajeros p
            LEFT JOIN accesos_puerta a ON p. id_pasajero = a. id_pasajero
            WHERE p.rfid_uid = %s
        """, (rfid_uid,))
        
        resultado = cursor.fetchone()
        
        if not resultado:
            print(f"[ERROR] RFID {rfid_uid} no encontrado en sistema")
            mqtt_client.publish(MQTT_TOPIC_PUERTA_RESPUESTA, "DENEGAR")
            return
        
        # Verificar que tenga check-in completado
        if not resultado['id_acceso']:
            print(f"[ERROR] RFID {rfid_uid} sin check-in completado (sin registro en accesos_puerta)")
            mqtt_client.publish(MQTT_TOPIC_PUERTA_RESPUESTA, "DENEGAR")
            return
        
        # Verificar que NO haya usado la puerta antes
        if resultado['puerta_abierta']:
            print(f"[ERROR] RFID {rfid_uid} ya fue usado anteriormente para abrir puerta")
            mqtt_client.publish(MQTT_TOPIC_PUERTA_RESPUESTA, "DENEGAR")
            return
        
        # TODO OK: Autorizar apertura
        print(f"[OK] Acceso autorizado para: {resultado['nombre_normalizado']}")
        print(f"[OK] Enviando señal ABRIR a ESP32 Puerta")
        mqtt_client.publish(MQTT_TOPIC_PUERTA_RESPUESTA, "ABRIR")
        
        # Marcar como usado en BD
        cursor.execute("""
            UPDATE accesos_puerta 
            SET puerta_abierta = TRUE 
            WHERE id_acceso = %s
        """, (resultado['id_acceso'],))
        
        conn.commit()
        print(f"[OK] Puerta marcada como usada en BD para pasajero ID: {resultado['id_pasajero']}")
        
    except Exception as e:
        print(f"[ERROR] Error verificando RFID para puerta: {e}")
        mqtt_client.publish(MQTT_TOPIC_PUERTA_RESPUESTA, "DENEGAR")
    finally:
        cursor.close()
        conn.close()

def registrar_peso_equipaje(peso_kg):
    """
    MODULO 2: Registrar peso recibido de ESP32 Bascula
    """
    from db import get_db_connection
    
    conn = get_db_connection()
    if not conn:
        print("[ERROR] No se pudo conectar a la base de datos")
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO pesos_equipaje (peso_kg)
            VALUES (%s)
        """, (peso_kg,))
        
        conn.commit()
        print(f"[OK] Peso {peso_kg} kg registrado en BD")
    except Exception as e:
        print(f"[ERROR] Error registrando peso: {e}")
    finally:
        cursor.close()
        conn.close()

mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.on_message = on_message

# ========================================
# MODULO 1: MQTT con manejo de errores mejorado
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
    """Leer tarjeta RFID con timeout usando SimpleMFRC522. read() bloqueante
    
    Compatible con multithreading (Flask debug mode)
    """
    if not RFID_DISPONIBLE:
        # Modo simulación
        simulated_id = "SIM" + str(int(time.time() * 1000))[-8:]
        print(f"[SIMULACION] RFID generado: {simulated_id}")
        return simulated_id
    
    import threading
    
    resultado = {'rfid': None, 'error': None}
    
    def leer_con_timeout():
        """Thread que ejecuta la lectura bloqueante"""
        try:
            print(f"[INFO] Esperando tarjeta RFID (timeout {timeout}s)...")
            id, text = reader.read()  # Bloqueante - espera hasta leer
            resultado['rfid'] = str(id). strip()
            print(f"[OK] RFID leído: {resultado['rfid']}")
        except Exception as e:
            resultado['error'] = str(e)
            print(f"[ERROR] Error leyendo RFID: {e}")
    
    # Crear y arrancar thread de lectura
    thread_lectura = threading.Thread(target=leer_con_timeout)
    thread_lectura.daemon = True
    thread_lectura. start()
    
    # Esperar con timeout
    thread_lectura.join(timeout=timeout)
    
    # Verificar resultado
    if thread_lectura.is_alive():
        # Timeout alcanzado
        print(f"[TIMEOUT] No se detectó tarjeta en {timeout}s")
        # Nota: El thread queda esperando, pero al ser daemon se limpia automáticamente
        return None
    
    if resultado['error']:
        print(f"[ERROR] Error durante la lectura: {resultado['error']}")
        return None
    
    return resultado['rfid']
    
def capturar_rostro():
    """Capturar rostro con la camara y extraer embedding"""
    try:
        print("[INFO] Iniciando captura de rostro...")
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("[ERROR] No se pudo acceder a la camara")
            return None
        
        # Dar tiempo a la camara para inicializar
        time.sleep(1)
        
        intentos = 0
        max_intentos = 30  # 30 frames = ~10 segundos
        
        while intentos < max_intentos:
            ret, frame = cap. read()
            
            if not ret:
                intentos += 1
                continue
            
            # Convertir BGR (OpenCV) a RGB (face_recognition)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detectar rostros
            face_locations = face_recognition.face_locations(rgb_frame)
            
            if len(face_locations) > 0:
                print(f"[OK] Rostro detectado (intento {intentos+1})")
                
                # Extraer encoding del primer rostro
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                
                if len(face_encodings) > 0:
                    embedding = face_encodings[0]
                    cap.release()
                    print("[OK] Embedding facial extraido correctamente")
                    return embedding
            
            intentos += 1
            time. sleep(0.3)
        
        cap.release()
        print("[ERROR] No se detecto ningun rostro")
        return None
        
    except Exception as e:
        print(f"[ERROR] Error capturando rostro: {e}")
        return None

# ========================================
# ENDPOINTS - SISTEMA
# ========================================

@app. route('/api/health', methods=['GET'])
def health_check():
    """Verificar estado del sistema"""
    return jsonify({
        'status': 'ok',
        'modulo': 1,
        'mqtt': 'conectado' if mqtt_conectado else 'desconectado (no requerido en Modulo 1)',
        'rfid': 'disponible' if RFID_DISPONIBLE else 'simulado',
        'broker': MQTT_BROKER
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
    """Registrar RFID de un pasajero"""
    try:
        data = request.json
        id_pasajero = data.get('id_pasajero')
        
        if not id_pasajero:
            return jsonify({
                'status': 'error',
                'error': 'ID de pasajero requerido'
            }), 400
        
        print(f"\n=== REGISTRAR RFID - Pasajero ID: {id_pasajero} ===")
        
        # Leer RFID
        rfid_uid = leer_rfid(timeout=15)
        
        if not rfid_uid:
            print("[ERROR] No se detecto tarjeta RFID")
            return jsonify({
                'status': 'error',
                'error': 'No se detecto tarjeta RFID'
            }), 400
        
        # Registrar RFID
        if registrar_rfid_pasajero(id_pasajero, rfid_uid):
            print(f"[OK] RFID registrado: {rfid_uid}")
            return jsonify({
                'status': 'ok',
                'rfid_uid': rfid_uid
            })
        else:
            print("[ERROR] Error al registrar RFID (posible duplicado)")
            return jsonify({
                'status': 'error',
                'error': 'Error al registrar RFID (posible RFID duplicado)'
            }), 400
            
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/admin/registrar-rostro', methods=['POST'])
def admin_registrar_rostro():
    """Capturar y registrar rostro de un pasajero"""
    try:
        data = request.json
        id_pasajero = data.get('id_pasajero')
        
        if not id_pasajero:
            return jsonify({
                'status': 'error',
                'error': 'ID de pasajero requerido'
            }), 400
        
        print(f"\n=== REGISTRAR ROSTRO - Pasajero ID: {id_pasajero} ===")
        
        # Capturar rostro
        embedding = capturar_rostro()
        
        if embedding is None:
            print("[ERROR] No se pudo capturar el rostro")
            return jsonify({
                'status': 'error',
                'error': 'No se pudo capturar el rostro'
            }), 400
        
        # Guardar en BD
        if registrar_rostro_pasajero(id_pasajero, embedding):
            print("[OK] Rostro registrado correctamente")
            return jsonify({
                'status': 'ok',
                'mensaje': 'Rostro registrado correctamente'
            })
        else:
            print("[ERROR] Error al guardar el rostro")
            return jsonify({
                'status': 'error',
                'error': 'Error al guardar el rostro'
            }), 500
            
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# ========================================
# ENDPOINTS - USUARIO (ACCESO) - MODULO 1
# ========================================

@app.route('/api/usuario/verificar-acceso', methods=['POST'])
def usuario_verificar_acceso():
    """
    Verificar acceso con RFID + rostro
    MODULO 1: Solo registra validacion en BD (NO abre puerta fisica)
    """
    try:
        # PASO 1: Leer RFID
        print("\n" + "="*60)
        print("=== INICIO VERIFICACION ACCESO - MODULO 1 ===")
        print("="*60)
        
        rfid_uid = leer_rfid(timeout=15)
        
        if not rfid_uid:
            print("[ERROR] PASO 1 FALLIDO: No se detecto tarjeta RFID")
            return jsonify({
                'status': 'error',
                'error': 'No se detecto tarjeta RFID'
            }), 400
        
        print(f"[OK] PASO 1: RFID detectado: {rfid_uid}")
        
        # PASO 2: Buscar pasajero con ese RFID
        pasajero = buscar_pasajero_por_rfid(rfid_uid)
        
        if not pasajero:
            print("[ERROR] PASO 2 FALLIDO: RFID no encontrado en la base de datos")
            return jsonify({
                'status': 'error',
                'error': 'RFID no registrado'
            }), 404
        
        print(f"[OK] PASO 2: Pasajero encontrado: {pasajero['nombre_normalizado']}")
        print(f"[INFO] Vuelo: {pasajero['numero_vuelo']} - Destino: {pasajero['destino']}")
        
        # Verificar que tenga rostro registrado
        if pasajero['rostro_embedding'] is None:
            print("[ERROR] PASO 2 FALLIDO: Pasajero sin rostro registrado")
            return jsonify({
                'status': 'error',
                'error': 'Pasajero sin biometria registrada'
            }), 400
        
        # PASO 3: Capturar rostro actual
        print("[INFO] PASO 3: Capturando rostro actual...")
        embedding_actual = capturar_rostro()
        
        if embedding_actual is None:
            print("[ERROR] PASO 3 FALLIDO: No se pudo capturar rostro")
            return jsonify({
                'status': 'error',
                'error': 'No se detecto rostro'
            }), 400
        
        print("[OK] PASO 3: Rostro capturado correctamente")
        
        # PASO 4: Comparar rostros
        print("[INFO] PASO 4: Comparando rostros...")
        porcentaje_similitud = calcular_similitud_facial(
            pasajero['rostro_embedding'],
            embedding_actual
        )
        
        print(f"[OK] PASO 4: Similitud facial: {porcentaje_similitud:.2f}%")
        
        # PASO 5: Decidir si permitir acceso (umbral 60%)
        if porcentaje_similitud >= 60.0:
            print("="*60)
            print("[OK] ACCESO CONCEDIDO")
            print("="*60)
            
            # Registrar acceso en BD (activa bandera para Modulo 3)
            print("[INFO] PASO 5: Registrando acceso en base de datos...")
            registrar_acceso(pasajero['id_pasajero'], porcentaje_similitud)
            print("[OK] PASO 5: Acceso registrado en BD")
            
            # ========================================
            # MODULO 1: NO ENVIAR SEÑAL MQTT
            # Esta funcionalidad se activara en Modulo 3
            # ========================================
            
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
            print(f"[INFO] Similitud insuficiente: {porcentaje_similitud:.2f}% (minimo: 60%)")
            print("="*60 + "\n")
            
            return jsonify({
                'status': 'error',
                'acceso': 'denegado',
                'error': 'Biometria no coincide',
                'similitud': round(porcentaje_similitud, 2)
            }), 403
            
    except Exception as e:
        print("="*60)
        print("[ERROR] ERROR EN VERIFICACION")
        print(f"[ERROR] Error: {e}")
        print("="*60 + "\n")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# ========================================
# INICIAR SERVIDOR
# ========================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("SMARTPORT v2.0 - MODULO 1")
    print("SISTEMA DE REGISTRO Y VALIDACION BIOMETRICA")
    print("="*60)
    print("Modulo: 1 (Registro RFID + Rostro)")
    print("MQTT: Deshabilitado (no requerido en Modulo 1)")
    print(f"RFID: {'Conectado' if RFID_DISPONIBLE else 'Modo simulacion'}")
    print("Flask Server: http://0.0.0.0:5000")
    print("="*60)
    print("[INFO] En Modulo 1 NO se abren puertas fisicas")
    print("[INFO] Solo se registran validaciones en la base de datos")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

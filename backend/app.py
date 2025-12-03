"""
app.py - API REST para SmartPort v2. 0 - MÓDULO 1
Sistema de registro y acceso con RFID + Reconocimiento facial
MÓDULO 1: Solo registro y validación (NO abre puertas físicas)
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

# Intentar importar MFRC522 (puede fallar si no está conectado)
try:
    from mfrc522 import SimpleMFRC522
    reader = SimpleMFRC522()
    RFID_DISPONIBLE = True
except:
    print("⚠️  MFRC522 no disponible - Usando modo simulación")
    RFID_DISPONIBLE = False

app = Flask(__name__)
CORS(app)

# ========================================
# CONFIGURACIÓN MQTT
# ========================================

MQTT_BROKER = os. environ.get("MQTT_BROKER", "broker.mqtt.cool")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_TOPIC_PUERTA = "aeropuerto/puerta/abrir"

mqtt_client = mqtt.Client(client_id="RaspberryPi_Aeropuerto")
mqtt_conectado = False

def on_connect(client, userdata, flags, rc):
    global mqtt_conectado
    if rc == 0:
        mqtt_conectado = True
        print("✓ Conectado al broker MQTT")
    else:
        mqtt_conectado = False
        print(f"✗ Error conectando a MQTT: código {rc}")

def on_disconnect(client, userdata, rc):
    global mqtt_conectado
    mqtt_conectado = False
    print("✗ Desconectado del broker MQTT")

mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect

# ========================================
# MÓDULO 1: MQTT deshabilitado (no requerido)
# Se habilitará en Módulo 2 (recibir pesos) y Módulo 3 (abrir puerta)
# ========================================
try:
    print("⚠️  MQTT deshabilitado en Módulo 1 (no requerido para registro)")
    mqtt_conectado = False
    # Descomentar las siguientes líneas en Módulo 2/3:
    # mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    # mqtt_client.loop_start()
except Exception as e:
    print(f"⚠️  MQTT no disponible: {e}")
    mqtt_conectado = False

# ========================================
# FUNCIONES AUXILIARES
# ========================================

def leer_rfid(timeout=10):
    """Leer tarjeta RFID (timeout en segundos)"""
    if not RFID_DISPONIBLE:
        # Modo simulación
        return "SIM" + str(int(time.time() * 1000))[-8:]
    
    try:
        print("Esperando tarjeta RFID...")
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            try:
                uid, _ = reader.read_no_block()
                if uid:
                    rfid_str = str(uid). strip()
                    print(f"✓ RFID leído: {rfid_str}")
                    return rfid_str
            except:
                pass
            time.sleep(0. 1)
        
        print("⏱️  Timeout leyendo RFID")
        return None
    except Exception as e:
        print(f"Error leyendo RFID: {e}")
        return None

def capturar_rostro():
    """Capturar rostro con la cámara y extraer embedding"""
    try:
        print("Iniciando captura de rostro...")
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("✗ No se pudo acceder a la cámara")
            return None
        
        # Dar tiempo a la cámara para inicializar
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
                print(f"✓ Rostro detectado (intento {intentos+1})")
                
                # Extraer encoding del primer rostro
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                
                if len(face_encodings) > 0:
                    embedding = face_encodings[0]
                    cap.release()
                    print("✓ Embedding facial extraído correctamente")
                    return embedding
            
            intentos += 1
            time. sleep(0.3)
        
        cap.release()
        print("✗ No se detectó ningún rostro")
        return None
        
    except Exception as e:
        print(f"Error capturando rostro: {e}")
        return None

def enviar_mqtt_abrir_puerta():
    """
    Enviar señal MQTT para abrir la puerta
    NOTA: Esta función se usará en MÓDULO 3, no en Módulo 1
    """
    global mqtt_conectado
    
    if mqtt_conectado:
        try:
            mqtt_client.publish(MQTT_TOPIC_PUERTA, "ABRIR")
            print("✓ Señal MQTT enviada: ABRIR PUERTA")
            return True
        except Exception as e:
            print(f"Error enviando MQTT: {e}")
            return False
    else:
        print("⚠️  MQTT no conectado - puerta no abierta")
        return False

# ========================================
# ENDPOINTS - SISTEMA
# ========================================

@app. route('/api/health', methods=['GET'])
def health_check():
    """Verificar estado del sistema"""
    return jsonify({
        'status': 'ok',
        'modulo': 1,
        'mqtt': 'conectado' if mqtt_conectado else 'desconectado (no requerido en Módulo 1)',
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
            print("✗ No se detectó tarjeta RFID")
            return jsonify({
                'status': 'error',
                'error': 'No se detectó tarjeta RFID'
            }), 400
        
        print(f"RFID detectado: {rfid_uid}")
        
        # Verificar si es admin
        admin = verificar_admin(rfid_uid)
        
        if admin:
            print(f"✓ Admin verificado: {admin['nombre']}")
            return jsonify({
                'status': 'ok',
                'admin': {
                    'id': admin['id_admin'],
                    'nombre': admin['nombre'],
                    'rfid': admin['rfid_uid']
                }
            })
        else:
            print("✗ RFID no autorizado")
            return jsonify({
                'status': 'error',
                'error': 'Acceso denegado - RFID no autorizado'
            }), 403
            
    except Exception as e:
        print(f"✗ Error en login admin: {e}")
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
            print("✗ No se detectó tarjeta RFID")
            return jsonify({
                'status': 'error',
                'error': 'No se detectó tarjeta RFID'
            }), 400
        
        # Registrar admin
        if registrar_admin(rfid_uid, nombre):
            print(f"✓ Admin registrado: {nombre} - RFID: {rfid_uid}")
            return jsonify({
                'status': 'ok',
                'mensaje': f'Administrador {nombre} registrado correctamente',
                'rfid_uid': rfid_uid
            })
        else:
            print("✗ Error al registrar (posible RFID duplicado)")
            return jsonify({
                'status': 'error',
                'error': 'Error al registrar administrador (posible RFID duplicado)'
            }), 400
            
    except Exception as e:
        print(f"✗ Error registrando admin: {e}")
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
                'error': 'Nombre y número de vuelo son requeridos'
            }), 400
        
        print(f"\n=== CREAR PASAJERO ===")
        print(f"Nombre: {nombre}")
        print(f"Vuelo: {numero_vuelo}")
        
        # Crear pasajero
        pasajero = crear_pasajero(nombre, numero_vuelo)
        
        if pasajero:
            print(f"✓ Pasajero creado - ID: {pasajero['id_pasajero']}")
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
            print("✗ Error al crear pasajero")
            return jsonify({
                'status': 'error',
                'error': 'Error al crear pasajero'
            }), 500
            
    except Exception as e:
        print(f"✗ Error: {e}")
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
            print("✗ No se detectó tarjeta RFID")
            return jsonify({
                'status': 'error',
                'error': 'No se detectó tarjeta RFID'
            }), 400
        
        # Registrar RFID
        if registrar_rfid_pasajero(id_pasajero, rfid_uid):
            print(f"✓ RFID registrado: {rfid_uid}")
            return jsonify({
                'status': 'ok',
                'rfid_uid': rfid_uid
            })
        else:
            print("✗ Error al registrar RFID (posible duplicado)")
            return jsonify({
                'status': 'error',
                'error': 'Error al registrar RFID (posible RFID duplicado)'
            }), 400
            
    except Exception as e:
        print(f"✗ Error: {e}")
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
            print("✗ No se pudo capturar el rostro")
            return jsonify({
                'status': 'error',
                'error': 'No se pudo capturar el rostro'
            }), 400
        
        # Guardar en BD
        if registrar_rostro_pasajero(id_pasajero, embedding):
            print("✓ Rostro registrado correctamente")
            return jsonify({
                'status': 'ok',
                'mensaje': 'Rostro registrado correctamente'
            })
        else:
            print("✗ Error al guardar el rostro")
            return jsonify({
                'status': 'error',
                'error': 'Error al guardar el rostro'
            }), 500
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# ========================================
# ENDPOINTS - USUARIO (ACCESO) - MÓDULO 1
# ========================================

@app.route('/api/usuario/verificar-acceso', methods=['POST'])
def usuario_verificar_acceso():
    """
    Verificar acceso con RFID + rostro
    MÓDULO 1: Solo registra validación en BD (NO abre puerta física)
    """
    try:
        # PASO 1: Leer RFID
        print("\n" + "="*60)
        print("=== INICIO VERIFICACIÓN ACCESO - MÓDULO 1 ===")
        print("="*60)
        
        rfid_uid = leer_rfid(timeout=15)
        
        if not rfid_uid:
            print("✗ PASO 1 FALLIDO: No se detectó tarjeta RFID")
            return jsonify({
                'status': 'error',
                'error': 'No se detectó tarjeta RFID'
            }), 400
        
        print(f"✓ PASO 1: RFID detectado: {rfid_uid}")
        
        # PASO 2: Buscar pasajero con ese RFID
        pasajero = buscar_pasajero_por_rfid(rfid_uid)
        
        if not pasajero:
            print("✗ PASO 2 FALLIDO: RFID no encontrado en la base de datos")
            return jsonify({
                'status': 'error',
                'error': 'RFID no registrado'
            }), 404
        
        print(f"✓ PASO 2: Pasajero encontrado: {pasajero['nombre_normalizado']}")
        print(f"         Vuelo: {pasajero['numero_vuelo']} - Destino: {pasajero['destino']}")
        
        # Verificar que tenga rostro registrado
        if pasajero['rostro_embedding'] is None:
            print("✗ PASO 2 FALLIDO: Pasajero sin rostro registrado")
            return jsonify({
                'status': 'error',
                'error': 'Pasajero sin biometría registrada'
            }), 400
        
        # PASO 3: Capturar rostro actual
        print("⏳ PASO 3: Capturando rostro actual...")
        embedding_actual = capturar_rostro()
        
        if embedding_actual is None:
            print("✗ PASO 3 FALLIDO: No se pudo capturar rostro")
            return jsonify({
                'status': 'error',
                'error': 'No se detectó rostro'
            }), 400
        
        print("✓ PASO 3: Rostro capturado correctamente")
        
        # PASO 4: Comparar rostros
        print("⏳ PASO 4: Comparando rostros...")
        porcentaje_similitud = calcular_similitud_facial(
            pasajero['rostro_embedding'],
            embedding_actual
        )
        
        print(f"✓ PASO 4: Similitud facial: {porcentaje_similitud:.2f}%")
        
        # PASO 5: Decidir si permitir acceso (umbral 60%)
        if porcentaje_similitud >= 60. 0:
            print("="*60)
            print("✓✓✓ ACCESO CONCEDIDO ✓✓✓")
            print("="*60)
            
            # Registrar acceso en BD (activa bandera para Módulo 3)
            print("⏳ PASO 5: Registrando acceso en base de datos...")
            registrar_acceso(pasajero['id_pasajero'], porcentaje_similitud)
            print("✓ PASO 5: Acceso registrado en BD")
            
            # ========================================
            # MÓDULO 1: NO ENVIAR SEÑAL MQTT
            # Esta función se habilitará en Módulo 3
            # ========================================
            # enviar_mqtt_abrir_puerta()  # <-- COMENTADO para Módulo 1
            
            print("="*60)
            print(f"BIENVENIDO: {pasajero['nombre_normalizado']}")
            print(f"VUELO: {pasajero['numero_vuelo']} → {pasajero['destino']}")
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
            print("✗✗✗ ACCESO DENEGADO ✗✗✗")
            print(f"Similitud insuficiente: {porcentaje_similitud:. 2f}% (mínimo: 60%)")
            print("="*60 + "\n")
            
            return jsonify({
                'status': 'error',
                'acceso': 'denegado',
                'error': 'Biometría no coincide',
                'similitud': round(porcentaje_similitud, 2)
            }), 403
            
    except Exception as e:
        print("="*60)
        print(f"✗✗✗ ERROR EN VERIFICACIÓN ✗✗✗")
        print(f"Error: {e}")
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
    print("🛫 SMARTPORT v2.0 - MÓDULO 1")
    print("   SISTEMA DE REGISTRO Y VALIDACIÓN BIOMÉTRICA")
    print("="*60)
    print(f"📍 Módulo: 1 (Registro RFID + Rostro)")
    print(f"📡 MQTT: Deshabilitado (no requerido en Módulo 1)")
    print(f"🔌 RFID: {'Conectado' if RFID_DISPONIBLE else 'Modo simulación'}")
    print(f"🌐 Flask Server: http://0.0.0.0:5000")
    print("="*60)
    print("ℹ️  En Módulo 1 NO se abren puertas físicas")
    print("ℹ️  Solo se registran validaciones en la base de datos")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

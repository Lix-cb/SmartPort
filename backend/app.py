"""
app.py - API REST para SmartPort v2. 0
Sistema de registro y acceso con RFID + Reconocimiento facial
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

MQTT_BROKER = os.environ.get("MQTT_BROKER", "broker.mqtt. cool")
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

try:
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
except:
    print(f"⚠️  No se pudo conectar al broker MQTT: {MQTT_BROKER}")

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
            time.sleep(0.1)
        
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
    """Enviar señal MQTT para abrir la puerta"""
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
        'mqtt': 'conectado' if mqtt_conectado else 'desconectado',
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
        # Leer RFID
        rfid_uid = leer_rfid(timeout=15)
        
        if not rfid_uid:
            return jsonify({
                'status': 'error',
                'error': 'No se detectó tarjeta RFID'
            }), 400
        
        # Verificar si es admin
        admin = verificar_admin(rfid_uid)
        
        if admin:
            return jsonify({
                'status': 'ok',
                'admin': {
                    'id': admin['id_admin'],
                    'nombre': admin['nombre'],
                    'rfid': admin['rfid_uid']
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'error': 'Acceso denegado - RFID no autorizado'
            }), 403
            
    except Exception as e:
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
        
        # Leer RFID
        rfid_uid = leer_rfid(timeout=15)
        
        if not rfid_uid:
            return jsonify({
                'status': 'error',
                'error': 'No se detectó tarjeta RFID'
            }), 400
        
        # Registrar admin
        if registrar_admin(rfid_uid, nombre):
            return jsonify({
                'status': 'ok',
                'mensaje': f'Administrador {nombre} registrado correctamente',
                'rfid_uid': rfid_uid
            })
        else:
            return jsonify({
                'status': 'error',
                'error': 'Error al registrar administrador (posible RFID duplicado)'
            }), 400
            
    except Exception as e:
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
        
        # Crear pasajero
        pasajero = crear_pasajero(nombre, numero_vuelo)
        
        if pasajero:
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
            return jsonify({
                'status': 'error',
                'error': 'Error al crear pasajero'
            }), 500
            
    except Exception as e:
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
        
        # Leer RFID
        rfid_uid = leer_rfid(timeout=15)
        
        if not rfid_uid:
            return jsonify({
                'status': 'error',
                'error': 'No se detectó tarjeta RFID'
            }), 400
        
        # Registrar RFID
        if registrar_rfid_pasajero(id_pasajero, rfid_uid):
            return jsonify({
                'status': 'ok',
                'rfid_uid': rfid_uid
            })
        else:
            return jsonify({
                'status': 'error',
                'error': 'Error al registrar RFID (posible RFID duplicado)'
            }), 400
            
    except Exception as e:
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
        
        # Capturar rostro
        embedding = capturar_rostro()
        
        if embedding is None:
            return jsonify({
                'status': 'error',
                'error': 'No se pudo capturar el rostro'
            }), 400
        
        # Guardar en BD
        if registrar_rostro_pasajero(id_pasajero, embedding):
            return jsonify({
                'status': 'ok',
                'mensaje': 'Rostro registrado correctamente'
            })
        else:
            return jsonify({
                'status': 'error',
                'error': 'Error al guardar el rostro'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# ========================================
# ENDPOINTS - USUARIO (ACCESO)
# ========================================

@app.route('/api/usuario/verificar-acceso', methods=['POST'])
def usuario_verificar_acceso():
    """Verificar acceso con RFID + rostro"""
    try:
        # PASO 1: Leer RFID
        print("\n=== INICIO VERIFICACIÓN ACCESO ===")
        rfid_uid = leer_rfid(timeout=15)
        
        if not rfid_uid:
            return jsonify({
                'status': 'error',
                'error': 'No se detectó tarjeta RFID'
            }), 400
        
        print(f"RFID detectado: {rfid_uid}")
        
        # PASO 2: Buscar pasajero con ese RFID
        pasajero = buscar_pasajero_por_rfid(rfid_uid)
        
        if not pasajero:
            print("✗ RFID no encontrado en la base de datos")
            return jsonify({
                'status': 'error',
                'error': 'RFID no registrado'
            }), 404
        
        print(f"Pasajero encontrado: {pasajero['nombre_normalizado']}")
        
        # Verificar que tenga rostro registrado
        if pasajero['rostro_embedding'] is None:
            print("✗ Pasajero sin rostro registrado")
            return jsonify({
                'status': 'error',
                'error': 'Pasajero sin biometría registrada'
            }), 400
        
        # PASO 3: Capturar rostro actual
        print("Capturando rostro actual...")
        embedding_actual = capturar_rostro()
        
        if embedding_actual is None:
            print("✗ No se pudo capturar rostro")
            return jsonify({
                'status': 'error',
                'error': 'No se detectó rostro'
            }), 400
        
        # PASO 4: Comparar rostros
        print("Comparando rostros...")
        porcentaje_similitud = calcular_similitud_facial(
            pasajero['rostro_embedding'],
            embedding_actual
        )
        
        print(f"Similitud facial: {porcentaje_similitud:. 2f}%")
        
        # PASO 5: Decidir si permitir acceso (umbral 60%)
        if porcentaje_similitud >= 60. 0:
            print("✓ ACCESO CONCEDIDO")
            
            # Registrar acceso en BD
            registrar_acceso(pasajero['id_pasajero'], porcentaje_similitud)
            
            # Enviar señal MQTT para abrir puerta
            enviar_mqtt_abrir_puerta()
            
            return jsonify({
                'status': 'ok',
                'acceso': 'concedido',
                'pasajero': {
                    'nombre': pasajero['nombre_normalizado'],
                    'vuelo': pasajero['numero_vuelo'],
                    'destino': pasajero['destino'],
                    'puerta': pasajero['puerta_asignada'] or 'P1'
                },
                'similitud': round(porcentaje_similitud, 2)
            })
        else:
            print("✗ ACCESO DENEGADO - Similitud insuficiente")
            return jsonify({
                'status': 'error',
                'acceso': 'denegado',
                'error': 'Biometría no coincide',
                'similitud': round(porcentaje_similitud, 2)
            }), 403
            
    except Exception as e:
        print(f"✗ Error en verificación: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# ========================================
# INICIAR SERVIDOR
# ========================================

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🛫 SMARTPORT v2.0 - SISTEMA AEROPUERTO INTELIGENTE")
    print("="*50)
    print(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"RFID: {'Conectado' if RFID_DISPONIBLE else 'Modo simulación'}")
    print(f"Flask Server: 0.0.0.0:5000")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

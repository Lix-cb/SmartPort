from flask import Flask, request, jsonify
from flask_cors import CORS
import paho.mqtt.client as mqtt
import json
import threading
import time
from rfid_reader import leer_rfid
from camera_recognition import (
    verificar_persona,
    obtener_embedding_camara_headless,
)
from db import (
    buscar_pasajero_por_nombre_y_vuelo,
    guardar_rfid_en_pasajero,
    guardar_embedding_en_pasajero,
    obtener_embedding_pasajero,
    buscar_por_rfid,
    obtener_vuelo_por_rfid,
    registrar_acceso_puerta,
    conectar,
)
import os

app = Flask(__name__)
CORS(app)  # Permitir peticiones desde React

# ============================
# CONFIGURACIÓN MQTT
# ============================
MQTT_BROKER = os.environ. get("MQTT_BROKER", "broker.mqtt. cool")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_TOPIC_ACCESO = "aeropuerto/rfid/acceso"
MQTT_TOPIC_RESPUESTA = "aeropuerto/rfid/respuesta"

mqtt_client = None

def on_connect(client, userdata, flags, rc):
    """Callback cuando se conecta al broker MQTT"""
    if rc == 0:
        print("✓ Conectado al broker MQTT")
        client.subscribe(MQTT_TOPIC_ACCESO)
        print(f"✓ Suscrito a: {MQTT_TOPIC_ACCESO}")
    else:
        print(f"✗ Error de conexión MQTT: {rc}")

def on_message(client, userdata, msg):
    """Callback cuando llega un mensaje MQTT del ESP32"""
    try:
        payload = msg.payload.decode()
        print(f"\n📨 Mensaje MQTT recibido: {payload}")
        
        data = json.loads(payload)
        rfid_uid = data.get("serial")
        
        if not rfid_uid:
            print("⚠ No se recibió serial en el mensaje")
            return
        
        print(f"🔍 Verificando RFID: {rfid_uid}")
        
        # Buscar pasajero por RFID
        pasajero = buscar_por_rfid(rfid_uid)
        
        if not pasajero:
            print(f"✗ RFID no registrado: {rfid_uid}")
            client.publish(MQTT_TOPIC_RESPUESTA, "no pass")
            return
        
        # Verificar que tenga estado VALIDADO (check-in completo)
        if pasajero. get("estado") != "VALIDADO":
            print(f"✗ Pasajero sin check-in completo: {pasajero['nombre_normalizado']}")
            client.publish(MQTT_TOPIC_RESPUESTA, "no pass")
            return
        
        # Obtener información del vuelo
        vuelo_info = obtener_vuelo_por_rfid(rfid_uid)
        
        if not vuelo_info:
            print("✗ No se encontró información del vuelo")
            client. publish(MQTT_TOPIC_RESPUESTA, "no pass")
            return
        
        # Registrar acceso en la base de datos
        try:
            registrar_acceso_puerta(
                pasajero["id_pasajero"], 
                1  # ID de puerta predeterminado
            )
        except Exception as e:
            print(f"⚠ Error al registrar acceso: {e}")
        
        # ACCESO AUTORIZADO
        print(f"✓ ACCESO AUTORIZADO para {pasajero['nombre_normalizado']}")
        print(f"  Vuelo: {vuelo_info['numero_vuelo']} → {vuelo_info['destino']}")
        print(f"  Puerta asignada: {vuelo_info. get('puerta_asignada', 'N/A')}")
        
        client.publish(MQTT_TOPIC_RESPUESTA, "pass")
        
    except json.JSONDecodeError:
        print("✗ Error al decodificar JSON")
    except Exception as e:
        print(f"✗ Error procesando mensaje MQTT: {e}")

def iniciar_mqtt():
    """Inicializa el cliente MQTT en un thread separado"""
    global mqtt_client
    
    mqtt_client = mqtt.Client(client_id="RaspberryPi_Aeropuerto")
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        print(f"✓ Cliente MQTT iniciado - Broker: {MQTT_BROKER}:{MQTT_PORT}")
    except Exception as e:
        print(f"✗ Error conectando a MQTT: {e}")

# Iniciar MQTT al arrancar Flask
threading.Thread(target=iniciar_mqtt, daemon=True).start()

# ============================
# MÓDULO 1 - Buscar pasajero
# ============================

@app.route("/api/buscar-pasajero", methods=["POST"])
def api_buscar_pasajero():
    """
    Busca un pasajero por nombre y número de vuelo
    """
    data = request.get_json(silent=True) or {}
    nombre = data.get("nombre", ""). strip()
    numero_vuelo = data.get("numero_vuelo")

    if not nombre or numero_vuelo is None:
        return jsonify({"error": "Faltan campos nombre o numero_vuelo"}), 400

    try:
        numero_vuelo = int(numero_vuelo)
    except ValueError:
        return jsonify({"error": "numero_vuelo debe ser entero"}), 400

    pasajero = buscar_pasajero_por_nombre_y_vuelo(nombre, numero_vuelo)
    
    if not pasajero:
        return jsonify({
            "status": "not_found",
            "msg": "No se encontró pasajero con ese nombre y vuelo"
        }), 404

    return jsonify({
        "status": "ok",
        "id_pasajero": pasajero["id_pasajero"],
        "nombre_normalizado": pasajero["nombre_normalizado"],
        "numero_vuelo": pasajero["numero_vuelo"],
        "destino": pasajero["destino"],
        "estado": pasajero. get("estado", "REGISTRADO")
    })

# ============================
# MÓDULO 1 - Registrar RFID
# ============================

@app.route("/api/registrar-rfid", methods=["POST"])
def api_registrar_rfid():
    """
    Registra solo el RFID para un pasajero
    """
    data = request.get_json(silent=True) or {}
    id_pasajero = data.get("id_pasajero")
    rfid_manual = data.get("rfid_manual")

    if id_pasajero is None:
        return jsonify({"error": "Falta id_pasajero"}), 400

    try:
        id_pasajero = int(id_pasajero)
    except ValueError:
        return jsonify({"error": "id_pasajero debe ser entero"}), 400

    # Obtener RFID
    if rfid_manual and str(rfid_manual).strip():
        rfid_uid = str(rfid_manual).strip()
        print(f"[DEBUG] Usando RFID manual: {rfid_uid}")
    else:
        print("⏳ Esperando tarjeta RFID...")
        rfid_uid = leer_rfid()
        if rfid_uid is None:
            return jsonify({"error": "No se pudo leer el RFID"}), 500

    print(f"✓ RFID detectado: {rfid_uid}")

    # Guardar en BD
    try:
        guardar_rfid_en_pasajero(id_pasajero, rfid_uid)
        print(f"✓ RFID registrado exitosamente")
    except Exception as e:
        return jsonify({"error": f"Error al guardar RFID: {e}"}), 500

    return jsonify({
        "status": "ok",
        "msg": "RFID registrado exitosamente",
        "id_pasajero": id_pasajero,
        "rfid_uid": rfid_uid,
    })

# ============================
# MÓDULO 1 - Registrar rostro
# ============================

@app.route("/api/registrar-rostro", methods=["POST"])
def api_registrar_rostro():
    """
    Captura y registra el embedding facial para un pasajero
    """
    data = request.get_json(silent=True) or {}
    id_pasajero = data.get("id_pasajero")

    if id_pasajero is None:
        return jsonify({"error": "Falta id_pasajero"}), 400

    try:
        id_pasajero = int(id_pasajero)
    except ValueError:
        return jsonify({"error": "id_pasajero debe ser entero"}), 400

    # Capturar embedding facial
    print("📸 Capturando embedding facial desde cámara...")
    emb = obtener_embedding_camara_headless(headless=True)
    
    if emb is None:
        return jsonify({"error": "No se pudo obtener un embedding facial válido"}), 500

    # Guardar en BD
    try:
        guardar_embedding_en_pasajero(id_pasajero, emb)
        print(f"✓ Rostro registrado y pasajero validado exitosamente")
    except Exception as e:
        return jsonify({"error": f"Error al guardar embedding: {e}"}), 500

    return jsonify({
        "status": "ok",
        "msg": "Rostro registrado exitosamente.  Check-in completo.",
        "id_pasajero": id_pasajero,
    })

# ============================
# MÓDULO 3 - Verificación (Opcional - para testing)
# ============================

@app.route("/api/verificar-manual", methods=["POST"])
def verificar_manual():
    """
    Endpoint para verificar manualmente sin MQTT
    """
    rfid_uid = leer_rfid()
    
    if rfid_uid is None:
        return jsonify({"status": "error", "msg": "No se pudo leer el RFID"}), 500

    print(f"🔍 RFID detectado para verificación: {rfid_uid}")

    pasajero = buscar_por_rfid(rfid_uid)
    
    if not pasajero:
        return jsonify({"status": "error", "msg": "RFID no registrado"}), 404

    id_pasajero = pasajero["id_pasajero"]

    # Obtener embedding guardado en BD
    emb_bd = obtener_embedding_pasajero(id_pasajero)
    
    if emb_bd is None:
        return jsonify({
            "status": "error",
            "msg": "No hay embedding registrado para este pasajero"
        }), 500

    # Capturar rostro actual y comparar
    ok = verificar_persona(emb_bd)

    if ok:
        return jsonify({
            "status": "ok",
            "msg": f"Identidad verificada para {pasajero['nombre_normalizado']}"
        })
    else:
        return jsonify({
            "status": "fail",
            "msg": "El rostro no coincide con el registro"
        })

# ============================
# HEALTH CHECK
# ============================

@app.route("/api/health", methods=["GET"])
def health():
    """Endpoint para verificar que el servidor está funcionando"""
    mqtt_status = "conectado" if mqtt_client and mqtt_client.is_connected() else "desconectado"
    
    return jsonify({
        "status": "ok",
        "mqtt": mqtt_status,
        "broker": MQTT_BROKER
    })

# ============================
# MAIN
# ============================

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🛫 SISTEMA AEROPUERTO SMART")
    print("="*50)
    print(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"Flask Server: 0.0.0.0:5000")
    print("="*50 + "\n")
    
    # Escucha en todas las interfaces, puerto 5000
    app.run(host="0.0.0.0", port=5000, debug=False)

"""
db.py - Modulo de conexion y operaciones con la base de datos
SmartPort v2.0 - OPTIMIZADO

MODULO 1: Funciones de registro y validacion biometrica
MODULO 2: Funciones de registro de peso
MODULO 3: Funciones de verificacion de puerta fisica
"""

import mysql.connector
from mysql.connector import Error
import pickle
import numpy as np

DB_CONFIG = {
    'host': 'localhost',
    'user': 'aero_user',
    'password': 'aero123',
    'database': 'aeropuerto'
}

def get_db_connection():
    """Crear conexion a la base de datos"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"[ERROR] Error conectando a la base de datos: {e}")
        return None

# ========================================
# FUNCIONES PARA ADMINS
# ========================================

def verificar_admin(rfid_uid):
    """Verificar si un RFID pertenece a un admin"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id_admin, nombre, rfid_uid 
            FROM admins 
            WHERE rfid_uid = %s
        """, (rfid_uid,))
        
        admin = cursor.fetchone()
        return admin
    except Error as e:
        print(f"[ERROR] Error verificando admin: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def registrar_admin(rfid_uid, nombre):
    """Registrar un nuevo administrador"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO admins (rfid_uid, nombre)
            VALUES (%s, %s)
        """, (rfid_uid, nombre. upper(). strip())) 
        
        conn.commit()
        return True
    except Error as e:
        print(f"[ERROR] Error registrando admin: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def listar_admins():
    """Obtener lista de todos los admins"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn. cursor(dictionary=True)
        cursor.execute("""
            SELECT id_admin, nombre, rfid_uid, fecha_registro 
            FROM admins 
            ORDER BY fecha_registro DESC
        """)
        
        admins = cursor.fetchall()
        return admins
    except Error as e:
        print(f"[ERROR] Error listando admins: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# ========================================
# FUNCIONES PARA VUELOS
# ========================================

def buscar_o_crear_vuelo(numero_vuelo, destino="DESTINO"):
    """
    Buscar vuelo o crearlo si no existe
    numero_vuelo ES la clave primaria (no auto_increment)
    """
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Buscar vuelo existente
        cursor.execute("""
            SELECT numero_vuelo, destino 
            FROM vuelos 
            WHERE numero_vuelo = %s
        """, (numero_vuelo,))
        
        vuelo = cursor.fetchone()
        
        if vuelo:
            return vuelo
        
        # Si no existe, crear uno nuevo
        cursor.execute("""
            INSERT INTO vuelos (numero_vuelo, destino)
            VALUES (%s, %s)
        """, (numero_vuelo, destino))
        
        conn.commit()
        
        # Retornar el vuelo creado
        return {
            'numero_vuelo': numero_vuelo,
            'destino': destino
        }
        
    except Error as e:
        print(f"[ERROR] Error en buscar_o_crear_vuelo: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

# ========================================
# FUNCIONES PARA PASAJEROS (MODO ADMIN)
# ========================================

def crear_pasajero(nombre, numero_vuelo):
    """Crear un nuevo pasajero (sin RFID ni rostro aun)"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Buscar o crear vuelo
        vuelo = buscar_o_crear_vuelo(numero_vuelo)
        if not vuelo:
            return None
        
        # Crear pasajero
        nombre_norm = nombre.upper(). strip()
        cursor.execute("""
            INSERT INTO pasajeros (nombre_normalizado, numero_vuelo)
            VALUES (%s, %s)
        """, (nombre_norm, vuelo['numero_vuelo']))
        
        conn.commit()
        id_pasajero = cursor.lastrowid
        
        # Obtener datos completos
        cursor.execute("""
            SELECT p.id_pasajero, p.nombre_normalizado, p. rfid_uid, p.estado,
                   v.numero_vuelo, v.destino
            FROM pasajeros p
            JOIN vuelos v ON p.numero_vuelo = v.numero_vuelo
            WHERE p.id_pasajero = %s
        """, (id_pasajero,))
        
        return cursor.fetchone()
    except Error as e:
        print(f"[ERROR] Error creando pasajero: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def registrar_rfid_pasajero(id_pasajero, rfid_uid):
    """Asociar RFID a un pasajero existente"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor. execute("""
            UPDATE pasajeros 
            SET rfid_uid = %s 
            WHERE id_pasajero = %s
        """, (rfid_uid, id_pasajero))
        
        conn. commit()
        return cursor.rowcount > 0
    except Error as e:
        print(f"[ERROR] Error registrando RFID: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def registrar_rostro_pasajero(id_pasajero, embedding):
    """Guardar embedding facial de un pasajero"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Serializar el embedding (numpy array) a bytes
        embedding_bytes = pickle. dumps(embedding)
        
        cursor.execute("""
            UPDATE pasajeros 
            SET rostro_embedding = %s, estado = 'VALIDADO'
            WHERE id_pasajero = %s
        """, (embedding_bytes, id_pasajero))
        
        conn.commit()
        return cursor.rowcount > 0
    except Error as e:
        print(f"[ERROR] Error registrando rostro: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

# ========================================
# FUNCIONES PARA ACCESO (MODO USUARIO)
# ========================================

def buscar_pasajero_por_rfid(rfid_uid):
    """Buscar pasajero por su RFID"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.id_pasajero, p.nombre_normalizado, p.rfid_uid, 
                   p.rostro_embedding, p.estado,
                   v.numero_vuelo, v.destino
            FROM pasajeros p
            JOIN vuelos v ON p.numero_vuelo = v.numero_vuelo
            WHERE p.rfid_uid = %s
        """, (rfid_uid,))
        
        pasajero = cursor.fetchone()
        
        if pasajero and pasajero['rostro_embedding']:
            # Deserializar el embedding
            pasajero['rostro_embedding'] = pickle.loads(pasajero['rostro_embedding'])
        
        return pasajero
    except Error as e:
        print(f"[ERROR] Error buscando pasajero por RFID: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def registrar_acceso(id_pasajero, porcentaje_similitud):
    """
    MODULO 1: Registrar validacion exitosa en BD
    Activa bandera que sera verificada en Modulo 3 para abrir puerta fisica
    
    Args:
        id_pasajero: ID del pasajero validado
        porcentaje_similitud: Porcentaje de coincidencia facial
    
    Returns:
        bool: True si se registro correctamente, False en caso contrario
    """
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Verificar si ya tiene acceso registrado
        cursor.execute("""
            SELECT id_acceso FROM accesos_puerta 
            WHERE id_pasajero = %s
        """, (id_pasajero,))
        
        if cursor.fetchone():
            # Ya tiene acceso registrado (evita duplicados)
            print("[INFO] Pasajero ya tiene acceso registrado previamente")
            return True
        
        # Registrar nuevo acceso
        cursor.execute("""
            INSERT INTO accesos_puerta (id_pasajero, porcentaje_similitud, puerta_abierta)
            VALUES (%s, %s, FALSE)
        """, (id_pasajero, porcentaje_similitud))
        
        # Actualizar estado del pasajero (bandera para Modulo 3)
        cursor.execute("""
            UPDATE pasajeros 
            SET estado = 'ABORDADO'
            WHERE id_pasajero = %s
        """, (id_pasajero,))
        
        conn.commit()
        print(f"[OK] Acceso registrado - ID Pasajero: {id_pasajero}, Similitud: {porcentaje_similitud:. 2f}%")
        return True
    except Error as e:
        print(f"[ERROR] Error registrando acceso: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def verificar_acceso_puerta(rfid_uid):
    """
    MODULO 3: Verificar si un RFID puede abrir la puerta fisica
    
    Valida:
    1. Que exista registro en accesos_puerta (check-in completado en Modulo 1)
    2. Que el estado sea ABORDADO
    3. Que NO haya usado la puerta antes (puerta_abierta = FALSE)
    
    Args:
        rfid_uid: UID de la tarjeta RFID
    
    Returns:
        dict: Informacion del acceso si es valido, None si no
    """
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT p.id_pasajero, p.nombre_normalizado, p. estado,
                   a.id_acceso, a.puerta_abierta, a.porcentaje_similitud
            FROM pasajeros p
            LEFT JOIN accesos_puerta a ON p.id_pasajero = a.id_pasajero
            WHERE p.rfid_uid = %s
        """, (rfid_uid,))
        
        resultado = cursor.fetchone()
        
        if not resultado:
            print(f"[ERROR] RFID {rfid_uid} no encontrado")
            return None
        
        if not resultado['id_acceso']:
            print(f"[ERROR] RFID {rfid_uid} sin check-in completado")
            return None
        
        if resultado['puerta_abierta']:
            print(f"[ERROR] RFID {rfid_uid} ya fue usado para abrir puerta")
            return None
        
        if resultado['estado'] != 'ABORDADO':
            print(f"[ERROR] RFID {rfid_uid} estado incorrecto: {resultado['estado']}")
            return None
        
        return resultado
        
    except Error as e:
        print(f"[ERROR] Error verificando acceso puerta: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def marcar_puerta_usada(id_acceso):
    """
    MODULO 3: Marcar que el pasajero ya uso la puerta fisica
    Evita que pueda abrir la puerta una segunda vez
    
    Args:
        id_acceso: ID del registro en accesos_puerta
    
    Returns:
        bool: True si se marco correctamente, False en caso contrario
    """
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE accesos_puerta 
            SET puerta_abierta = TRUE 
            WHERE id_acceso = %s
        """, (id_acceso,))
        
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"[OK] Puerta marcada como usada - ID Acceso: {id_acceso}")
            return True
        else:
            print(f"[ERROR] No se encontro registro con ID Acceso: {id_acceso}")
            return False
            
    except Error as e:
        print(f"[ERROR] Error marcando puerta usada: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def registrar_peso(peso_kg):
    """
    MODULO 2: Registrar peso recibido de ESP32 Bascula
    
    Args:
        peso_kg: Peso en kilogramos
    
    Returns:
        bool: True si se registro correctamente, False en caso contrario
    """
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn. cursor()
        
        cursor.execute("""
            INSERT INTO pesos_equipaje (peso_kg)
            VALUES (%s)
        """, (peso_kg,))
        
        conn.commit()
        print(f"[OK] Peso registrado: {peso_kg} kg")
        return True
        
    except Error as e:
        print(f"[ERROR] Error registrando peso: {e}")
        return False
    finally:
        cursor.close()
        conn. close()

# ========================================
# FUNCION AUXILIAR
# ========================================

def calcular_similitud_facial(embedding1, embedding2):
    """
    Calcular similitud entre dos embeddings faciales
    Usa distancia euclidiana y la convierte a porcentaje
    
    Args:
        embedding1: Primer embedding (numpy array o lista)
        embedding2: Segundo embedding (numpy array o lista)
    
    Returns:
        float: Porcentaje de similitud (0-100)
    """
    try:
        # Convertir a numpy arrays si no lo son
        emb1 = np.array(embedding1)
        emb2 = np.array(embedding2)
        
        # Calcular distancia euclidiana
        distancia = np.linalg.norm(emb1 - emb2)
        
        # Convertir a porcentaje de similitud
        # Distancia menor = mayor similitud
        # 0. 6 es el umbral tipico de face_recognition
        porcentaje = max(0, min(100, (1 - distancia) * 100))
        
        return porcentaje
    except Exception as e:
        print(f"[ERROR] Error calculando similitud: {e}")
        return 0

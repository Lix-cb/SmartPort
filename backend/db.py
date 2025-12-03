"""
db.py - Módulo de conexión y operaciones con la base de datos
SmartPort v2.0
"""

import mysql.connector
from mysql. connector import Error
import pickle
import numpy as np

DB_CONFIG = {
    'host': 'localhost',
    'user': 'aero_user',
    'password': 'aero123',
    'database': 'aeropuerto'
}

def get_db_connection():
    """Crear conexión a la base de datos"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Error conectando a la base de datos: {e}")
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
        print(f"Error verificando admin: {e}")
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
        """, (rfid_uid, nombre. upper()))
        
        conn.commit()
        return True
    except Error as e:
        print(f"Error registrando admin: {e}")
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
        print(f"Error listando admins: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# ========================================
# FUNCIONES PARA VUELOS
# ========================================

def buscar_o_crear_vuelo(numero_vuelo, destino="DESTINO", hora_salida=None):
    """Buscar vuelo o crearlo si no existe"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Buscar vuelo existente
        cursor.execute("""
            SELECT id_vuelo, numero_vuelo, destino, hora_salida 
            FROM vuelos 
            WHERE numero_vuelo = %s
        """, (numero_vuelo,))
        
        vuelo = cursor. fetchone()
        
        if vuelo:
            return vuelo
        
        # Si no existe, crear uno nuevo
        if not hora_salida:
            hora_salida = "DATE_ADD(NOW(), INTERVAL 2 HOUR)"
            cursor.execute(f"""
                INSERT INTO vuelos (numero_vuelo, destino, hora_salida)
                VALUES (%s, %s, {hora_salida})
            """, (numero_vuelo, destino))
        else:
            cursor.execute("""
                INSERT INTO vuelos (numero_vuelo, destino, hora_salida)
                VALUES (%s, %s, %s)
            """, (numero_vuelo, destino, hora_salida))
        
        conn.commit()
        id_vuelo = cursor.lastrowid
        
        # Obtener el vuelo creado
        cursor.execute("""
            SELECT id_vuelo, numero_vuelo, destino, hora_salida 
            FROM vuelos 
            WHERE id_vuelo = %s
        """, (id_vuelo,))
        
        return cursor.fetchone()
    except Error as e:
        print(f"Error en buscar_o_crear_vuelo: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

# ========================================
# FUNCIONES PARA PASAJEROS (MODO ADMIN)
# ========================================

def crear_pasajero(nombre, numero_vuelo):
    """Crear un nuevo pasajero (sin RFID ni rostro aún)"""
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
            INSERT INTO pasajeros (nombre_normalizado, id_vuelo)
            VALUES (%s, %s)
        """, (nombre_norm, vuelo['id_vuelo']))
        
        conn.commit()
        id_pasajero = cursor.lastrowid
        
        # Obtener datos completos
        cursor.execute("""
            SELECT p.id_pasajero, p.nombre_normalizado, p. rfid_uid, p.estado,
                   v.numero_vuelo, v.destino, v.hora_salida
            FROM pasajeros p
            JOIN vuelos v ON p.id_vuelo = v.id_vuelo
            WHERE p.id_pasajero = %s
        """, (id_pasajero,))
        
        return cursor.fetchone()
    except Error as e:
        print(f"Error creando pasajero: {e}")
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
        print(f"Error registrando RFID: {e}")
        return False
    finally:
        cursor.close()
        conn. close()

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
        print(f"Error registrando rostro: {e}")
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
            SELECT p.id_pasajero, p.nombre_normalizado, p. rfid_uid, 
                   p.rostro_embedding, p.estado,
                   v.numero_vuelo, v.destino, v.hora_salida, v.puerta_asignada
            FROM pasajeros p
            JOIN vuelos v ON p. id_vuelo = v.id_vuelo
            WHERE p. rfid_uid = %s
        """, (rfid_uid,))
        
        pasajero = cursor.fetchone()
        
        if pasajero and pasajero['rostro_embedding']:
            # Deserializar el embedding
            pasajero['rostro_embedding'] = pickle.loads(pasajero['rostro_embedding'])
        
        return pasajero
    except Error as e:
        print(f"Error buscando pasajero por RFID: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def registrar_acceso(id_pasajero, porcentaje_similitud, id_puerta=1):
    """Registrar un acceso exitoso a la puerta"""
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
            # Ya tiene acceso registrado
            return True
        
        # Registrar nuevo acceso
        cursor.execute("""
            INSERT INTO accesos_puerta (id_pasajero, id_puerta, porcentaje_similitud)
            VALUES (%s, %s, %s)
        """, (id_pasajero, id_puerta, porcentaje_similitud))
        
        # Actualizar estado del pasajero
        cursor.execute("""
            UPDATE pasajeros 
            SET estado = 'ABORDADO'
            WHERE id_pasajero = %s
        """, (id_pasajero,))
        
        conn.commit()
        return True
    except Error as e:
        print(f"Error registrando acceso: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

# ========================================
# FUNCIÓN AUXILIAR
# ========================================

def calcular_similitud_facial(embedding1, embedding2):
    """Calcular similitud entre dos embeddings faciales (distancia euclidiana)"""
    try:
        # Convertir a numpy arrays si no lo son
        emb1 = np.array(embedding1)
        emb2 = np.array(embedding2)
        
        # Calcular distancia euclidiana
        distancia = np.linalg.norm(emb1 - emb2)
        
        # Convertir a porcentaje de similitud (0. 6 = umbral típico de face_recognition)
        # Distancia menor = mayor similitud
        porcentaje = max(0, min(100, (1 - distancia) * 100))
        
        return porcentaje
    except Exception as e:
        print(f"Error calculando similitud: {e}")
        return 0

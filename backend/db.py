import mysql.connector
import numpy as np
import os
from datetime import datetime

# ---------------------------
# CONEXIÓN A MARIADB
# ---------------------------
def conectar():
    host = os.environ.get("DB_HOST", "localhost")
    user = os.environ.get("DB_USER", "aero_user")
    password = os. environ.get("DB_PASS", "aero123")
    database = os.environ.get("DB_NAME", "aeropuerto")

    return mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        ssl_disabled=True
    )

# -------------------------------------------
# NORMALIZACIÓN DE NOMBRE PARA COINCIDENCIA
# -------------------------------------------
def normalizar(nombre):
    """Normaliza nombres eliminando acentos y convirtiendo a mayúsculas"""
    if not nombre:
        return None

    nombre = nombre.upper()
    nombre = (
        nombre.replace("Á","A"). replace("É","E").replace("Í","I")
              .replace("Ó","O").replace("Ú","U").replace("Ñ","N")
    )
    return nombre. strip()

# -------------------------------------------
# BÚSQUEDA DE PASAJERO POR NOMBRE + VUELO
# -------------------------------------------
def buscar_pasajero_por_nombre_y_vuelo(nombre, numero_vuelo):
    """
    Busca un pasajero por su nombre normalizado y número de vuelo
    """
    nombre_norm = normalizar(nombre)

    db = conectar()
    cursor = db.cursor(dictionary=True)

    sql = """
        SELECT p.*, v.numero_vuelo, v.destino, v.hora_salida, v.puerta_asignada
        FROM pasajeros p
        JOIN vuelos v ON p.id_vuelo = v.id_vuelo
        WHERE p.nombre_normalizado = %s
        AND v.numero_vuelo = %s;
    """

    cursor.execute(sql, (nombre_norm, numero_vuelo))
    resultado = cursor.fetchone()

    cursor.close()
    db.close()

    return resultado

# -------------------------------------------
# GUARDAR SOLO EL RFID DEL PASAJERO
# -------------------------------------------
def guardar_rfid_en_pasajero(id_pasajero, rfid_uid):
    """
    Guarda solo el RFID del pasajero
    """
    db = conectar()
    cursor = db.cursor()

    sql = """
        UPDATE pasajeros
        SET rfid_uid = %s
        WHERE id_pasajero = %s;
    """

    cursor.execute(sql, (rfid_uid, id_pasajero))
    db.commit()

    cursor.close()
    db.close()

# -------------------------------------------
# GUARDAR SOLO EL EMBEDDING FACIAL
# -------------------------------------------
def guardar_embedding_en_pasajero(id_pasajero, embedding):
    """
    Guarda el embedding facial y cambia estado a VALIDADO
    """
    if embedding is not None:
        embedding_bytes = embedding.tobytes()
    else:
        embedding_bytes = None

    db = conectar()
    cursor = db.cursor()

    sql = """
        UPDATE pasajeros
        SET rostro_id = %s,
            estado = 'VALIDADO'
        WHERE id_pasajero = %s;
    """

    cursor.execute(sql, (embedding_bytes, id_pasajero))
    db.commit()

    cursor.close()
    db.close()

# -------------------------------------------
# OBTENER EMBEDDING ALMACENADO PARA VERIFICAR
# -------------------------------------------
def obtener_embedding_pasajero(id_pasajero):
    """
    Obtiene el embedding facial almacenado de un pasajero
    """
    db = conectar()
    cursor = db.cursor()

    sql = "SELECT rostro_id FROM pasajeros WHERE id_pasajero = %s;"
    cursor.execute(sql, (id_pasajero,))
    row = cursor.fetchone()

    cursor.close()
    db. close()

    if not row or row[0] is None:
        return None

    emb_bytes = row[0]
    return np.frombuffer(emb_bytes, dtype=np.float64)

# -------------------------------------------
# BUSCAR PASAJERO POR RFID (PARA VERIFICACIÓN)
# -------------------------------------------
def buscar_por_rfid(rfid_uid):
    """
    Busca un pasajero por su RFID
    """
    db = conectar()
    cursor = db.cursor(dictionary=True)

    sql = """
        SELECT id_pasajero, nombre_normalizado, estado, id_vuelo
        FROM pasajeros
        WHERE rfid_uid = %s;
    """

    cursor.execute(sql, (rfid_uid,))
    res = cursor.fetchone()

    cursor.close()
    db. close()

    return res

# -------------------------------------------
# OBTENER INFORMACIÓN DEL VUELO POR RFID
# -------------------------------------------
def obtener_vuelo_por_rfid(rfid_uid):
    """
    Obtiene información completa del vuelo asociado al pasajero
    mediante su RFID
    """
    db = conectar()
    cursor = db.cursor(dictionary=True)

    sql = """
        SELECT v.id_vuelo, v.numero_vuelo, v.destino, 
               v.hora_salida, v.puerta_asignada
        FROM vuelos v
        JOIN pasajeros p ON p.id_vuelo = v. id_vuelo
        WHERE p.rfid_uid = %s;
    """

    cursor. execute(sql, (rfid_uid,))
    vuelo = cursor.fetchone()

    cursor.close()
    db.close()

    return vuelo

# -------------------------------------------
# REGISTRAR ACCESO A PUERTA (MÓDULO 3)
# -------------------------------------------
def registrar_acceso_puerta(id_pasajero, id_puerta):
    """
    Registra el acceso de un pasajero a una puerta específica
    Solo permite UN acceso por pasajero (por la restricción UNIQUE en la BD)
    """
    db = conectar()
    cursor = db.cursor()

    sql = """
        INSERT INTO accesos_puerta (id_pasajero, id_puerta, fecha_hora)
        VALUES (%s, %s, NOW());
    """

    try:
        cursor.execute(sql, (id_pasajero, id_puerta))
        db.commit()
        print(f"✓ Acceso registrado para pasajero {id_pasajero} en puerta {id_puerta}")
    except mysql.connector.IntegrityError:
        print(f"⚠ El pasajero {id_pasajero} ya tiene un acceso registrado")
    finally:
        cursor.close()
        db.close()

# -------------------------------------------
# VERIFICAR SI PASAJERO YA ACCEDIÓ
# -------------------------------------------
def verificar_acceso_previo(id_pasajero):
    """
    Verifica si un pasajero ya registró su acceso a alguna puerta
    """
    db = conectar()
    cursor = db.cursor(dictionary=True)

    sql = """
        SELECT * FROM accesos_puerta
        WHERE id_pasajero = %s;
    """

    cursor.execute(sql, (id_pasajero,))
    acceso = cursor.fetchone()

    cursor.close()
    db. close()

    return acceso is not None

# -------------------------------------------
# OBTENER ESTADÍSTICAS (OPCIONAL - PARA DASHBOARD)
# -------------------------------------------
def obtener_estadisticas():
    """
    Obtiene estadísticas generales del sistema
    """
    db = conectar()
    cursor = db.cursor(dictionary=True)

    stats = {}

    # Total de pasajeros
    cursor.execute("SELECT COUNT(*) as total FROM pasajeros")
    stats['total_pasajeros'] = cursor.fetchone()['total']

    # Pasajeros validados (con check-in completo)
    cursor.execute("SELECT COUNT(*) as total FROM pasajeros WHERE estado = 'VALIDADO'")
    stats['pasajeros_validados'] = cursor.fetchone()['total']

    # Pasajeros que han abordado
    cursor.execute("SELECT COUNT(*) as total FROM pasajeros WHERE estado = 'ABORDADO'")
    stats['pasajeros_abordados'] = cursor.fetchone()['total']

    # Total de accesos registrados
    cursor.execute("SELECT COUNT(*) as total FROM accesos_puerta")
    stats['total_accesos'] = cursor.fetchone()['total']

    cursor.close()
    db.close()

    return stats

# -------------------------------------------
# LISTAR VUELOS ACTIVOS
# -------------------------------------------
def listar_vuelos_activos():
    """
    Lista todos los vuelos con hora de salida futura
    """
    db = conectar()
    cursor = db.cursor(dictionary=True)

    sql = """
        SELECT v.*, COUNT(p.id_pasajero) as total_pasajeros
        FROM vuelos v
        LEFT JOIN pasajeros p ON p.id_vuelo = v. id_vuelo
        WHERE v.hora_salida > NOW()
        GROUP BY v.id_vuelo
        ORDER BY v.hora_salida ASC;
    """

    cursor.execute(sql)
    vuelos = cursor.fetchall()

    cursor.close()
    db.close()

    return vuelos

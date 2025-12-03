---- -----------------------------------------------------
-- SCRIPT COMPLETO: BASE DE DATOS AEROPUERTO IOT v2.0
-- SISTEMA DE REGISTRO Y ACCESO CON RFID + BIOMETRIA
-- MODULO 1: Registro biometrico
-- MODULO 2: Control de peso equipaje
-- MODULO 3: Control de puerta fisica
-- -----------------------------------------------------

-- -----------------------------------------------------
-- 1. CREAR BASE DE DATOS
-- -----------------------------------------------------
DROP DATABASE IF EXISTS aeropuerto;
CREATE DATABASE aeropuerto;
USE aeropuerto;

-- -----------------------------------------------------
-- 2. TABLA: admins
-- RFID de administradores autorizados
-- -----------------------------------------------------
CREATE TABLE admins (
    id_admin INT AUTO_INCREMENT PRIMARY KEY,
    rfid_uid VARCHAR(100) UNIQUE NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Insertar admin por defecto
INSERT INTO admins (rfid_uid, nombre) 
VALUES ('47600058058', 'ADMINISTRADOR PRINCIPAL');

-- -----------------------------------------------------
-- 3. TABLA: vuelos
-- -----------------------------------------------------
CREATE TABLE vuelos (
    id_vuelo INT AUTO_INCREMENT PRIMARY KEY,
    numero_vuelo INT NOT NULL,
    destino VARCHAR(50),
    hora_salida DATETIME NOT NULL,
    puerta_asignada VARCHAR(10) DEFAULT NULL,
    
    CONSTRAINT uq_numero_vuelo UNIQUE (numero_vuelo),
    CONSTRAINT chk_numero_vuelo_4dig CHECK (numero_vuelo BETWEEN 0 AND 9999)
);

CREATE INDEX idx_hora_salida ON vuelos (hora_salida);

-- -----------------------------------------------------
-- 4. TABLA: pasajeros
-- Registro completo: nombre, vuelo, RFID, rostro
-- -----------------------------------------------------
CREATE TABLE pasajeros (
    id_pasajero INT AUTO_INCREMENT PRIMARY KEY,
    nombre_normalizado VARCHAR(150) NOT NULL,
    id_vuelo INT NOT NULL,
    
    rfid_uid VARCHAR(100) UNIQUE DEFAULT NULL,
    rostro_embedding BLOB DEFAULT NULL,  -- Embedding facial (128 dimensiones)
    
    estado ENUM('REGISTRADO','VALIDADO','ABORDADO') DEFAULT 'REGISTRADO',
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_pasajero_vuelo
        FOREIGN KEY (id_vuelo)
        REFERENCES vuelos(id_vuelo)
        ON DELETE CASCADE
);

CREATE INDEX idx_pasajero_rfid ON pasajeros (rfid_uid);
CREATE INDEX idx_pasajero_nombre_vuelo ON pasajeros (nombre_normalizado, id_vuelo);

-- -----------------------------------------------------
-- 5. TABLA: accesos_puerta
-- Registro de cada acceso exitoso (RFID + rostro validado)
-- -----------------------------------------------------
CREATE TABLE accesos_puerta (
    id_acceso INT AUTO_INCREMENT PRIMARY KEY,
    id_pasajero INT NOT NULL,
    id_puerta INT NOT NULL,
    fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    porcentaje_similitud DECIMAL(5,2) DEFAULT NULL,  -- % de coincidencia facial
    puerta_abierta BOOLEAN DEFAULT FALSE,  -- Modulo 3: Marca si ya uso la puerta fisica

    CONSTRAINT fk_acceso_pasajero
        FOREIGN KEY (id_pasajero)
        REFERENCES pasajeros(id_pasajero)
        ON DELETE CASCADE,
        
    CONSTRAINT uq_acceso_por_pasajero UNIQUE (id_pasajero)
);

CREATE INDEX idx_puerta_abierta ON accesos_puerta (puerta_abierta);

-- -----------------------------------------------------
-- 6. TABLA: pesos_equipaje
-- -----------------------------------------------------
CREATE TABLE pesos_equipaje (
    id_peso INT AUTO_INCREMENT PRIMARY KEY,
    peso_kg DECIMAL(6,2) NOT NULL,
    fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_peso_positivo CHECK (peso_kg >= 0)
);

CREATE INDEX idx_fecha_hora ON pesos_equipaje (fecha_hora);

-- -----------------------------------------------------
-- 7. TABLA: puertas
-- -----------------------------------------------------
CREATE TABLE puertas (
    id_puerta INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(20) NOT NULL,
    id_vuelo INT DEFAULT NULL,

    CONSTRAINT fk_puerta_vuelo
        FOREIGN KEY (id_vuelo)
        REFERENCES vuelos(id_vuelo)
        ON DELETE SET NULL
);

-- Crear puerta por defecto
INSERT INTO puertas (nombre) VALUES ('P1');

-- -----------------------------------------------------
-- 8. DATOS DE PRUEBA
-- -----------------------------------------------------

-- Crear vuelo de prueba
INSERT INTO vuelos (numero_vuelo, destino, hora_salida)
VALUES (1234, 'CDMX', DATE_ADD(NOW(), INTERVAL 2 HOUR));

-- Pasajeros de prueba (sin RFID ni rostro aun - se registran desde admin)
INSERT INTO pasajeros (nombre_normalizado, id_vuelo)
VALUES
 ('JORGE CARDENAS BLANCO', 1),
 ('FRANCISCO CALDERON OROZCO', 1);

-- -----------------------------------------------------
-- 9. CREAR USUARIO Y DAR PERMISOS
-- -----------------------------------------------------

DROP USER IF EXISTS 'aero_user'@'localhost';
CREATE USER 'aero_user'@'localhost' IDENTIFIED BY 'aero123';
GRANT ALL PRIVILEGES ON aeropuerto.* TO 'aero_user'@'localhost';
FLUSH PRIVILEGES;

-- -----------------------------------------------------
-- 10. VERIFICACION
-- -----------------------------------------------------
SELECT 'Base de datos v2.0 creada exitosamente' AS status;
SELECT COUNT(*) AS total_admins FROM admins;
SELECT COUNT(*) AS total_vuelos FROM vuelos;
SELECT COUNT(*) AS total_pasajeros FROM pasajeros;

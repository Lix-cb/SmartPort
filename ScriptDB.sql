-- -----------------------------------------------------
-- SCRIPT OPTIMIZADO: BASE DE DATOS AEROPUERTO IOT v2.0
-- SISTEMA DE REGISTRO Y ACCESO CON RFID + BIOMETRIA
-- Solo campos necesarios para el proyecto
-- -----------------------------------------------------

DROP DATABASE IF EXISTS aeropuerto;
CREATE DATABASE aeropuerto;
USE aeropuerto;

-- -----------------------------------------------------
-- TABLA: admins
-- Administradores autorizados (acceso con RFID)
-- -----------------------------------------------------
CREATE TABLE admins (
    id_admin INT AUTO_INCREMENT PRIMARY KEY,
    rfid_uid VARCHAR(100) UNIQUE NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO admins (rfid_uid, nombre) 
VALUES ('476600058058', 'ADMINISTRADOR PRINCIPAL');

-- -----------------------------------------------------
-- TABLA: vuelos
-- numero_vuelo ES la clave primaria (no auto_increment)
-- -----------------------------------------------------
CREATE TABLE vuelos (
    numero_vuelo INT PRIMARY KEY,
    destino VARCHAR(50) NOT NULL DEFAULT 'DESTINO',
    
    CONSTRAINT chk_numero_vuelo_4dig CHECK (numero_vuelo BETWEEN 0 AND 9999)
);

-- -----------------------------------------------------
-- TABLA: pasajeros
-- Registro completo: nombre, vuelo, RFID, rostro
-- -----------------------------------------------------
CREATE TABLE pasajeros (
    id_pasajero INT AUTO_INCREMENT PRIMARY KEY,
    nombre_normalizado VARCHAR(150) NOT NULL,
    numero_vuelo INT NOT NULL,
    
    rfid_uid VARCHAR(100) UNIQUE DEFAULT NULL,
    rostro_embedding BLOB DEFAULT NULL,
    
    estado ENUM('REGISTRADO','VALIDADO','ABORDADO') DEFAULT 'REGISTRADO',
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_pasajero_vuelo
        FOREIGN KEY (numero_vuelo)
        REFERENCES vuelos(numero_vuelo)
        ON DELETE CASCADE
);

CREATE INDEX idx_pasajero_rfid ON pasajeros (rfid_uid);
CREATE INDEX idx_pasajero_nombre_vuelo ON pasajeros (nombre_normalizado, numero_vuelo);

-- -----------------------------------------------------
-- TABLA: accesos_puerta
-- Registro de validacion biometrica exitosa
-- -----------------------------------------------------
CREATE TABLE accesos_puerta (
    id_acceso INT AUTO_INCREMENT PRIMARY KEY,
    id_pasajero INT NOT NULL,
    fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    porcentaje_similitud DECIMAL(5,2) DEFAULT NULL,
    puerta_abierta BOOLEAN DEFAULT FALSE,

    CONSTRAINT fk_acceso_pasajero
        FOREIGN KEY (id_pasajero)
        REFERENCES pasajeros(id_pasajero)
        ON DELETE CASCADE,
        
    CONSTRAINT uq_acceso_por_pasajero UNIQUE (id_pasajero)
);

CREATE INDEX idx_puerta_abierta ON accesos_puerta (puerta_abierta);

-- -----------------------------------------------------
-- TABLA: pesos_equipaje
-- Registro de pesos recibidos de ESP32 Bascula
-- -----------------------------------------------------
CREATE TABLE pesos_equipaje (
    id_peso INT AUTO_INCREMENT PRIMARY KEY,
    peso_kg DECIMAL(6,2) NOT NULL,
    fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_peso_positivo CHECK (peso_kg >= 0)
);

CREATE INDEX idx_fecha_hora ON pesos_equipaje (fecha_hora);

-- -----------------------------------------------------
-- DATOS DE PRUEBA
-- -----------------------------------------------------

-- -----------------------------------------------------
-- USUARIO Y PERMISOS
-- -----------------------------------------------------
DROP USER IF EXISTS 'aero_user'@'localhost';
CREATE USER 'aero_user'@'localhost' IDENTIFIED BY 'aero123';
GRANT ALL PRIVILEGES ON aeropuerto.* TO 'aero_user'@'localhost';
FLUSH PRIVILEGES;

-- -----------------------------------------------------
-- VERIFICACION
-- -----------------------------------------------------
SELECT 'Base de datos v2. 0 optimizada creada exitosamente' AS status;
SELECT COUNT(*) AS total_admins FROM admins;
SELECT COUNT(*) AS total_vuelos FROM vuelos;
SELECT COUNT(*) AS total_pasajeros FROM pasajeros;




-- -----------------------------------------------------
-- SCRIPT COMPLETO: BASE DE DATOS AEROPUERTO IOT
-- -----------------------------------------------------

-- -----------------------------------------------------
-- 1. CREAR BASE DE DATOS
-- -----------------------------------------------------
DROP DATABASE IF EXISTS aeropuerto;
CREATE DATABASE aeropuerto;
USE aeropuerto;

-- -----------------------------------------------------
-- 2. TABLA: vuelos
-- numero_vuelo: int(4) ingresado por el usuario
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
-- 3. TABLA: pasajeros
-- nombre_normalizado: un solo campo, todo en mayúsculas
-- Pasajero SIEMPRE está ligado a un vuelo
-- RFID y rostro se registran DESPUÉS
-- -----------------------------------------------------
CREATE TABLE pasajeros (
    id_pasajero INT AUTO_INCREMENT PRIMARY KEY,
    nombre_normalizado VARCHAR(150) NOT NULL,
    id_vuelo INT NOT NULL,
    
    rfid_uid VARCHAR(100) UNIQUE DEFAULT NULL,
    rostro_id BLOB DEFAULT NULL,  -- BLOB para guardar embeddings (bytes)
    
    estado ENUM('REGISTRADO','VALIDADO','ABORDADO') DEFAULT 'REGISTRADO',

    CONSTRAINT fk_pasajero_vuelo
        FOREIGN KEY (id_vuelo)
        REFERENCES vuelos(id_vuelo)
        ON DELETE CASCADE
);

CREATE INDEX idx_pasajero_nombre_vuelo 
    ON pasajeros (nombre_normalizado, id_vuelo);

-- -----------------------------------------------------
-- 4.  TABLA: accesos_puerta
-- Un pasajero solo puede registrar UN acceso
-- -----------------------------------------------------
CREATE TABLE accesos_puerta (
    id_acceso INT AUTO_INCREMENT PRIMARY KEY,
    id_pasajero INT NOT NULL,
    id_puerta INT NOT NULL,
    fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_acceso_pasajero
        FOREIGN KEY (id_pasajero)
        REFERENCES pasajeros(id_pasajero)
        ON DELETE CASCADE
);

CREATE UNIQUE INDEX uq_acceso_por_pasajero 
    ON accesos_puerta (id_pasajero);

-- -----------------------------------------------------
-- 5. TABLA: pesos_equipaje
-- Peso estable de la báscula, SIN vincular a pasajero
-- Una sola báscula en todo el sistema
-- -----------------------------------------------------
CREATE TABLE pesos_equipaje (
    id_peso INT AUTO_INCREMENT PRIMARY KEY,
    peso_kg DECIMAL(6,2) NOT NULL,
    fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_peso_positivo CHECK (peso_kg >= 0)
);

CREATE INDEX idx_fecha_hora ON pesos_equipaje (fecha_hora);

-- -----------------------------------------------------
-- 6. TABLA: puertas
-- Manejo de puertas físicas / lógicas del aeropuerto
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

-- Crear una puerta por defecto
INSERT INTO puertas (nombre) VALUES ('P1');

-- -----------------------------------------------------
-- 7.  DATOS DE PRUEBA
-- -----------------------------------------------------

-- Crear vuelo 1234
INSERT INTO vuelos (numero_vuelo, destino, hora_salida)
VALUES (1234, 'CDMX', DATE_ADD(NOW(), INTERVAL 45 MINUTE));

-- Insertar pasajeros de prueba (usando id_vuelo = 1, que es el AUTO_INCREMENT)
INSERT INTO pasajeros (nombre_normalizado, id_vuelo)
VALUES
 ('JORGE CARDENAS BLANCO', 1),      -- id_vuelo = 1 (vuelo 1234)
 ('FRANCISCO CALDERON OROZCO', 1);  -- id_vuelo = 1 (vuelo 1234)

-- -----------------------------------------------------
-- 8.  CREAR USUARIO Y DAR PERMISOS
-- -----------------------------------------------------

-- Eliminar el usuario si ya existe (para evitar errores)
DROP USER IF EXISTS 'aero_user'@'localhost';

-- Crear el usuario
CREATE USER 'aero_user'@'localhost' IDENTIFIED BY 'aero123';

-- Dar todos los permisos sobre la base de datos aeropuerto
GRANT ALL PRIVILEGES ON aeropuerto.* TO 'aero_user'@'localhost';

-- Aplicar los cambios
FLUSH PRIVILEGES;

-- -----------------------------------------------------
-- 9.  VERIFICACIÓN
-- -----------------------------------------------------
SELECT 'Base de datos creada exitosamente' AS status;
SELECT COUNT(*) AS total_vuelos FROM vuelos;
SELECT COUNT(*) AS total_pasajeros FROM pasajeros;
SELECT User, Host FROM mysql.user WHERE User = 'aero_user';

-- Mostrar datos insertados
SELECT * FROM vuelos;
SELECT * FROM pasajeros;

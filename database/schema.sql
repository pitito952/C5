-- ==========================================================
-- SCRIPT DE BASE DE DATOS: Módulo de Caja Chica / Petty Cash
-- Motor: MySQL 8+
-- ==========================================================

CREATE DATABASE IF NOT EXISTS caja_chica_db
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE caja_chica_db;

-- --------------------------------------------------------
-- 1. Tabla: usuarios
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol ENUM('Cajero', 'Administrador') NOT NULL DEFAULT 'Cajero',
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso DATETIME NULL DEFAULT NULL
) ENGINE=InnoDB;

-- Usuario administrador por defecto (password = admin123 hash simulado)
INSERT IGNORE INTO usuarios (username, password_hash, rol) 
VALUES ('admin', 'admin123', 'Administrador');

-- --------------------------------------------------------
-- 2. Tabla: configuracion_caja
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS configuracion_caja (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    fondo_fijo DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    saldo_inicial DECIMAL(10,2) NULL DEFAULT NULL, -- Nueva columna para el saldo del cierre anterior
    estado ENUM('Activa', 'Inactiva') NOT NULL DEFAULT 'Activa',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Crear una caja de ejemplo
INSERT IGNORE INTO configuracion_caja (nombre, fondo_fijo) 
VALUES ('Caja Chica', 10000.00);

-- --------------------------------------------------------
-- 3. Tabla: categorias_movimiento
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS categorias_movimiento (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    tipo ENUM('Ingreso', 'Egreso') NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB;

-- Categorías por defecto
INSERT IGNORE INTO categorias_movimiento (nombre, tipo) VALUES 
('Venta Menor', 'Ingreso'),
('Reposición de Caja', 'Ingreso'),
('Papelería y Útiles', 'Egreso'),
('Movilización y Taxis', 'Egreso'),
('Alimentación', 'Egreso'),
('Aseo y Limpieza', 'Egreso');

-- --------------------------------------------------------
-- 4. Tabla: sesiones_caja
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS sesiones_caja (
    id INT AUTO_INCREMENT PRIMARY KEY,
    caja_id INT NOT NULL,
    usuario_id INT NOT NULL,
    fecha_apertura DATETIME NOT NULL,
    monto_inicial DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    -- Campos que se llenarán al cerrar:
    fecha_cierre DATETIME NULL,
    monto_final_sistema DECIMAL(10,2) NULL,
    monto_final_fisico DECIMAL(10,2) NULL,
    diferencia DECIMAL(10,2) NULL,
    estado ENUM('Abierta', 'Cerrada') NOT NULL DEFAULT 'Abierta',
    observaciones_cierre TEXT NULL,
    FOREIGN KEY (caja_id) REFERENCES configuracion_caja(id) ON DELETE RESTRICT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- --------------------------------------------------------
-- 5. Tabla: movimientos_caja
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS movimientos_caja (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sesion_id INT NOT NULL,
    usuario_id INT NOT NULL,
    caja_id INT NOT NULL,
    categoria_id INT NOT NULL,
    fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tipo ENUM('Ingreso', 'Egreso') NOT NULL,
    concepto VARCHAR(255) NOT NULL,
    comprobante_tipo VARCHAR(1) NULL, -- 'F', 'V', 'R', etc.
    comprobante_numero VARCHAR(8) NULL,
    monto DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    anulado BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (sesion_id) REFERENCES sesiones_caja(id) ON DELETE RESTRICT,
    FOREIGN KEY (caja_id) REFERENCES configuracion_caja(id) ON DELETE RESTRICT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE RESTRICT,
    FOREIGN KEY (categoria_id) REFERENCES categorias_movimiento(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Índices útiles para rendimiento
CREATE INDEX idx_movimientos_sesion ON movimientos_caja(sesion_id);

-- --------------------------------------------------------
-- 6. Tabla: parametros_control
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS parametros_control (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo_empresa VARCHAR(3) NOT NULL,
    nombre_empresa VARCHAR(50) NOT NULL,
    ruta_logo VARCHAR(255) NULL,
    simbolo_moneda VARCHAR(5),
    nombre_moneda VARCHAR(50),
    tasa_cambio DECIMAL(10, 4)
) ENGINE=InnoDB;

-- Valores por defecto
INSERT IGNORE INTO parametros_control (id, codigo_empresa, nombre_empresa, ruta_logo, simbolo_moneda, nombre_moneda, tasa_cambio)
VALUES (1, 'A01', 'Mi Empresa', 'C:/Users/pitito/aida/assets/logotipo/logo_coninfo.png', '', '', '1.0000');

-- Índices útiles para rendimiento
CREATE INDEX idx_sesion_activa ON sesiones_caja(estado);

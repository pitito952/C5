-- Archivo de migración V5.1 para agregar columnas faltantes requeridas por los CRUDs

USE caja_chica_db;

-- 1. Agregar 'ultimo_acceso' a 'usuarios' si no existe
ALTER TABLE usuarios ADD COLUMN ultimo_acceso DATETIME NULL;

-- 2. Agregar 'descripcion' a 'configuracion_caja' si no existe
ALTER TABLE configuracion_caja ADD COLUMN descripcion VARCHAR(255) NULL;

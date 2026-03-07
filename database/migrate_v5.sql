-- Archivo de migración V5 para agregar caja_id y usuario_id a movimientos_caja

USE caja_chica_db;

-- 1. Agregar columnas si no existen
-- MySQL 8 soporta IF NOT EXISTS en ADD COLUMN, pero para mayor compatibilidad usamos una aproximación directa
-- Si la columna ya existe, esto tirará un error que ignoraremos o controlaremos en Python.

ALTER TABLE movimientos_caja 
ADD COLUMN usuario_id INT NULL AFTER sesion_id,
ADD COLUMN caja_id INT NULL AFTER usuario_id;

-- 2. Retro-alimentar registros existentes basándonos en la tabla sesiones_caja
-- Como cada movimiento pertenecía a una sesión, podemos inferir la caja y el usuario creador de la sesión original.
UPDATE movimientos_caja m
JOIN sesiones_caja s ON m.sesion_id = s.id
SET m.usuario_id = s.usuario_id, 
    m.caja_id = s.caja_id
WHERE m.usuario_id IS NULL;

-- 3. Hacer las nuevas columnas NO NULL (ahora que tienen datos)
ALTER TABLE movimientos_caja MODIFY COLUMN usuario_id INT NOT NULL;
ALTER TABLE movimientos_caja MODIFY COLUMN caja_id INT NOT NULL;

-- 4. Crear llaves foráneas para mantener integridad referencial
ALTER TABLE movimientos_caja
ADD CONSTRAINT fk_mov_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE RESTRICT,
ADD CONSTRAINT fk_mov_caja FOREIGN KEY (caja_id) REFERENCES configuracion_caja(id) ON DELETE RESTRICT;

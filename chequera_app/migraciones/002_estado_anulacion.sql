-- Migracion 2: estado_anulacion
-- Generada automaticamente


-- Migración 002: Agregar campo de estado para anulación de cheques

-- Agregar columna estado (default: 'activo')
ALTER TABLE cheques ADD COLUMN estado TEXT DEFAULT 'activo';

-- Índice en estado para filtrar cheques activos/anulados
CREATE INDEX IF NOT EXISTS idx_estado ON cheques(estado);

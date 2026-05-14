-- Migración 1: indices_rendimiento
-- Generada automáticamente


-- Migración 001: Agregar índices para mejorar rendimiento

-- Índice en serie y numero para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_serie_numero ON cheques(serie, numero);

-- Índice en fecha de emisión
CREATE INDEX IF NOT EXISTS idx_fecha_emision ON cheques(fecha_emision);

-- Índice en beneficiario para búsquedas parciales
CREATE INDEX IF NOT EXISTS idx_beneficiario ON cheques(beneficiario);

-- ============================================
-- AJUSTES PARA SOL Y DASHBOARD
-- ============================================

ALTER TABLE macmetric.archivos_cargados
ADD COLUMN IF NOT EXISTS fecha_operativa DATE,
ADD COLUMN IF NOT EXISTS registros_insertados INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS nombre_reporte_generado TEXT;

ALTER TABLE macmetric.tramites
ADD COLUMN IF NOT EXISTS archivo_cargado_id INTEGER,
ADD COLUMN IF NOT EXISTS terminal VARCHAR(50),
ADD COLUMN IF NOT EXISTS domicilio_visible VARCHAR(20),
ADD COLUMN IF NOT EXISTS tipo_tramite_categoria VARCHAR(100);

ALTER TABLE macmetric.tiempos_atencion
ADD COLUMN IF NOT EXISTS archivo_cargado_id INTEGER;

-- Opcional: llaves foráneas si quieres dejarlo consistente
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_tramites_archivo_cargado'
          AND table_schema = 'macmetric'
          AND table_name = 'tramites'
    ) THEN
        ALTER TABLE macmetric.tramites
        ADD CONSTRAINT fk_tramites_archivo_cargado
        FOREIGN KEY (archivo_cargado_id)
        REFERENCES macmetric.archivos_cargados(id)
        ON DELETE SET NULL;
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_tiempos_archivo_cargado'
          AND table_schema = 'macmetric'
          AND table_name = 'tiempos_atencion'
    ) THEN
        ALTER TABLE macmetric.tiempos_atencion
        ADD CONSTRAINT fk_tiempos_archivo_cargado
        FOREIGN KEY (archivo_cargado_id)
        REFERENCES macmetric.archivos_cargados(id)
        ON DELETE SET NULL;
    END IF;
END$$;

-- ============================================
-- NUEVA TABLA PARA CR
-- ============================================

CREATE TABLE IF NOT EXISTS macmetric.entregas_cr (
    id SERIAL PRIMARY KEY,
    archivo_cargado_id INTEGER REFERENCES macmetric.archivos_cargados(id) ON DELETE SET NULL,
    mac_modulo VARCHAR(6) NOT NULL,
    fecha_entrega DATE NOT NULL,
    solicitud VARCHAR(50),
    folio_nec VARCHAR(50),
    terminal VARCHAR(50),
    hora_inicio TIMESTAMP,
    hora_fin TIMESTAMP,
    minutos_atencion NUMERIC(10,2),
    dentro_norma BOOLEAN,
    origen_archivo VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_entregas_cr_mac
        CHECK (mac_modulo IN ('090852', '090853'))
);

CREATE INDEX IF NOT EXISTS idx_entregas_cr_archivo
    ON macmetric.entregas_cr(archivo_cargado_id);

CREATE INDEX IF NOT EXISTS idx_entregas_cr_mac_fecha
    ON macmetric.entregas_cr(mac_modulo, fecha_entrega);

CREATE INDEX IF NOT EXISTS idx_entregas_cr_solicitud
    ON macmetric.entregas_cr(solicitud);
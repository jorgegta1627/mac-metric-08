-- ============================================
-- ESQUEMA BASE
-- ============================================
CREATE SCHEMA IF NOT EXISTS macmetric;

-- ============================================
-- ROLES
-- ============================================
CREATE TABLE IF NOT EXISTS macmetric.roles (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- USUARIOS
-- ============================================
CREATE TABLE IF NOT EXISTS macmetric.usuarios (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    nombre_completo VARCHAR(150) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id INTEGER NOT NULL REFERENCES macmetric.roles(id),
    mac_modulo VARCHAR(6),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_usuarios_mac
        CHECK (mac_modulo IS NULL OR mac_modulo IN ('090852', '090853'))
);

-- ============================================
-- TIPOS DE ARCHIVO (LOS 15 TIPOS)
-- ============================================
CREATE TABLE IF NOT EXISTS macmetric.tipos_archivo (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) NOT NULL UNIQUE,
    nombre VARCHAR(150) NOT NULL,
    descripcion VARCHAR(255),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- CARGAS DE ARCHIVOS (BITÁCORA)
-- ============================================
CREATE TABLE IF NOT EXISTS macmetric.cargas_archivo (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES macmetric.usuarios(id),
    mac_modulo VARCHAR(6) NOT NULL,
    tipo_archivo_id INTEGER NOT NULL REFERENCES macmetric.tipos_archivo(id),
    nombre_original VARCHAR(255) NOT NULL,
    nombre_guardado VARCHAR(255) NOT NULL,
    ruta_archivo VARCHAR(500) NOT NULL,
    estatus_procesamiento VARCHAR(50) NOT NULL DEFAULT 'PENDIENTE',
    fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_procesamiento TIMESTAMP,
    observaciones TEXT,
    CONSTRAINT chk_cargas_mac
        CHECK (mac_modulo IN ('090852', '090853'))
);

-- ============================================
-- TRÁMITES
-- ============================================
CREATE TABLE IF NOT EXISTS macmetric.tramites (
    id SERIAL PRIMARY KEY,
    carga_archivo_id INTEGER REFERENCES macmetric.cargas_archivo(id) ON DELETE SET NULL,
    mac_modulo VARCHAR(6) NOT NULL,
    fecha_tramite DATE NOT NULL,
    folio_tramite VARCHAR(50),
    tipo_tramite VARCHAR(100),
    funcionario_nombre VARCHAR(150),
    funcionario_puesto VARCHAR(100),
    ciudadano_clave VARCHAR(50),
    estatus_tramite VARCHAR(50),
    origen_archivo VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_tramites_mac
        CHECK (mac_modulo IN ('090852', '090853'))
);

-- ============================================
-- TIEMPOS DE ATENCIÓN
-- ============================================
CREATE TABLE IF NOT EXISTS macmetric.tiempos_atencion (
    id SERIAL PRIMARY KEY,
    carga_archivo_id INTEGER REFERENCES macmetric.cargas_archivo(id) ON DELETE SET NULL,
    tramite_id INTEGER REFERENCES macmetric.tramites(id) ON DELETE CASCADE,
    mac_modulo VARCHAR(6) NOT NULL,
    fecha_atencion DATE NOT NULL,
    hora_inicio TIMESTAMP,
    hora_fin TIMESTAMP,
    minutos_atencion NUMERIC(10,2),
    dentro_norma BOOLEAN,
    observaciones TEXT,
    origen_archivo VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_tiempos_mac
        CHECK (mac_modulo IN ('090852', '090853'))
);

-- ============================================
-- INVENTARIO
-- ============================================
CREATE TABLE IF NOT EXISTS macmetric.inventario (
    id SERIAL PRIMARY KEY,
    carga_archivo_id INTEGER REFERENCES macmetric.cargas_archivo(id) ON DELETE SET NULL,
    mac_modulo VARCHAR(6) NOT NULL,
    fecha_corte DATE NOT NULL,
    tipo_movimiento VARCHAR(100),
    cantidad INTEGER NOT NULL DEFAULT 0,
    credencial_folio VARCHAR(100),
    estatus_conciliacion VARCHAR(50),
    observaciones TEXT,
    origen_archivo VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_inventario_mac
        CHECK (mac_modulo IN ('090852', '090853'))
);

CREATE TABLE macmetric.archivos_cargados (
    id SERIAL PRIMARY KEY,

    nombre_archivo TEXT NOT NULL,
    ruta_archivo TEXT NOT NULL,

    mac VARCHAR(10),              -- 090852, 090853
    tipo VARCHAR(20),             -- TIEMPOS, TRAMITES, etc.

    fecha_carga TIMESTAMP DEFAULT NOW(),
    usuario_carga TEXT,

    estatus VARCHAR(20) DEFAULT 'PENDIENTE',  -- PENDIENTE / PROCESADO / ERROR
    mensaje_error TEXT,

    activo BOOLEAN DEFAULT TRUE
);
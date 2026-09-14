CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_completo TEXT NOT NULL,
    usuario TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    rol TEXT CHECK(rol IN ('ADMIN', 'PROFESOR')) NOT NULL DEFAULT 'PROFESOR'
);

CREATE TABLE IF NOT EXISTS estudiantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paterno TEXT NOT NULL,
    materno TEXT NOT NULL,
    nombres TEXT NOT NULL,
    nivel TEXT CHECK(nivel IN ('Primaria', 'Secundaria')) NOT NULL,
    curso INTEGER CHECK(curso BETWEEN 1 AND 6) NOT NULL,
    nombre_padre TEXT NOT NULL,
    celular_padre TEXT NOT NULL,
    domicilio TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS seguimiento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estudiante_id INTEGER,
    materia TEXT NOT NULL,
    tipo_registro TEXT CHECK(tipo_registro IN ('asistio', 'falta', 'no_tarea', 'falto_respeto', 'mal_comportamiento', 'sin_uniforme')),
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (estudiante_id) REFERENCES estudiantes (id)
);

-- Usuario Administrador por defecto (Credenciales: admin / admin123)
INSERT OR IGNORE INTO usuarios (id, nombre_completo, usuario, password, rol) 
VALUES (1, 'Administrador General', 'admin', 'admin123', 'ADMIN');
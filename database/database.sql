CREATE TABLE usuarios (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    huella_id  INT UNIQUE NOT NULL,
    nombre     VARCHAR(50) NOT NULL,
    rut        VARCHAR(12) UNIQUE,                              -- RUT chileno (texto, incluye dígito verificador)
    pin        VARCHAR(5) NOT NULL,                             -- PIN de 5 dígitos
    rol        ENUM('empleado', 'admin')   DEFAULT 'empleado', -- Tipo de usuario
    estado     ENUM('activo', 'inactivo')  DEFAULT 'activo',   -- Estado del usuario
    creado_en  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

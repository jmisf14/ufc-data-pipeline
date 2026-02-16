-- Tabla EXTERNA complementaria - NO interfiere con pipeline de Scrapy
-- Almacena "Tale of the Tape" - datos específicos de cada pelea
-- Contiene datos únicos: peso por pelea, edad al momento de la pelea, etc.
-- Se puede relacionar mediante JOINs usando fighter_id/fight_id, pero SIN foreign keys

CREATE TABLE IF NOT EXISTS external_fighter_tott (
    id SERIAL PRIMARY KEY,
    fighter_id VARCHAR(255),
    fight_id VARCHAR(255),
    fighter_name VARCHAR(255),
    age INTEGER,  -- Edad al momento de la pelea
    height VARCHAR(50),  -- Puede incluir unidades
    weight VARCHAR(50),  -- Peso en la pelea (importante, puede variar por pelea)
    reach VARCHAR(50),
    stance VARCHAR(50),
    dob DATE,  -- Date of birth
    sig_str_landed_per_min DECIMAL(10,2),
    sig_str_accuracy INTEGER,
    sig_str_absorbed_per_min DECIMAL(10,2),
    sig_str_defense INTEGER,
    takedown_avg DECIMAL(10,2),
    takedown_accuracy INTEGER,
    takedown_defense INTEGER,
    submission_avg DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices únicos para UPSERT
-- 1) Si hay fighter_id (lo extraemos desde URL), usarlo como clave única
CREATE UNIQUE INDEX IF NOT EXISTS idx_external_fighter_tott_unique_fighter_id
    ON external_fighter_tott(fighter_id)
    WHERE fighter_id IS NOT NULL;

-- 2) Si NO hay fighter_id, usar fighter_name como fallback
CREATE UNIQUE INDEX IF NOT EXISTS idx_external_fighter_tott_unique_name 
    ON external_fighter_tott(fighter_name) 
    WHERE fighter_id IS NULL;

-- Índices para mejorar performance (sin foreign keys)
CREATE INDEX IF NOT EXISTS idx_external_fighter_tott_fighter_id ON external_fighter_tott(fighter_id);
CREATE INDEX IF NOT EXISTS idx_external_fighter_tott_fight_id ON external_fighter_tott(fight_id);
CREATE INDEX IF NOT EXISTS idx_external_fighter_tott_fighter_fight ON external_fighter_tott(fighter_id, fight_id);

-- Comentarios para documentación
COMMENT ON TABLE external_fighter_tott IS 'Tabla EXTERNA complementaria - Tale of the Tape. Datos específicos por pelea. NO interfiere con pipeline de Scrapy';
COMMENT ON COLUMN external_fighter_tott.weight IS 'Peso del fighter en esta pelea específica (puede variar entre peleas) - DATO ÚNICO';
COMMENT ON COLUMN external_fighter_tott.age IS 'Edad del fighter al momento de esta pelea específica - DATO ÚNICO';
COMMENT ON COLUMN external_fighter_tott.fighter_id IS 'Se puede relacionar con tabla fighters.id mediante JOINs, pero SIN foreign key';

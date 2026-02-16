-- Tabla EXTERNA complementaria - NO interfiere con pipeline de Scrapy
-- Almacena estadísticas DETALLADAS POR ROUND de cada fighter
-- Diferente a la tabla 'fights' que tiene totales de la pelea
-- Se puede relacionar mediante JOINs usando fight_id y fighter_id, pero SIN foreign keys

CREATE TABLE IF NOT EXISTS external_fight_stats (
    id SERIAL PRIMARY KEY,
    event_name VARCHAR(255),
    bout VARCHAR(255),
    round_number INTEGER,  -- 1, 2, 3, 4, 5
    round_label VARCHAR(50),  -- "Round 1", "Round 2", etc.
    fighter_name VARCHAR(255),
    knockdowns DECIMAL(5,1),
    sig_str_landed INTEGER,
    sig_str_attempted INTEGER,
    sig_str_percentage INTEGER,  -- Sin el símbolo %
    total_str_landed INTEGER,
    total_str_attempted INTEGER,
    takedown_landed INTEGER,
    takedown_attempted INTEGER,
    takedown_percentage INTEGER,  -- Sin el símbolo %, puede ser NULL si es "---"
    submission_attempts DECIMAL(5,1),
    reversals DECIMAL(5,1),
    control_time VARCHAR(20),  -- Formato "M:SS" o "--"
    head_landed INTEGER,
    head_attempted INTEGER,
    body_landed INTEGER,
    body_attempted INTEGER,
    leg_landed INTEGER,
    leg_attempted INTEGER,
    distance_landed INTEGER,
    distance_attempted INTEGER,
    clinch_landed INTEGER,
    clinch_attempted INTEGER,
    ground_landed INTEGER,
    ground_attempted INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_name, bout, round_number, fighter_name)  -- Un fighter solo puede tener un registro por round
);

-- Índices para mejorar performance (sin foreign keys)
CREATE INDEX IF NOT EXISTS idx_external_fight_stats_event ON external_fight_stats(event_name);
CREATE INDEX IF NOT EXISTS idx_external_fight_stats_bout ON external_fight_stats(bout);
CREATE INDEX IF NOT EXISTS idx_external_fight_stats_fighter ON external_fight_stats(fighter_name);
CREATE INDEX IF NOT EXISTS idx_external_fight_stats_round ON external_fight_stats(round_number);

-- Comentarios para documentación
COMMENT ON TABLE external_fight_stats IS 'Tabla EXTERNA complementaria - Estadísticas detalladas POR ROUND de cada fighter. NO interfiere con pipeline de Scrapy';
COMMENT ON COLUMN external_fight_stats.round_number IS 'Número del round (1-5). Diferente a fights que tiene totales de la pelea';
COMMENT ON COLUMN external_fight_stats.fighter_name IS 'Nombre del fighter. Se puede relacionar con fighters mediante JOINs, pero SIN foreign key';

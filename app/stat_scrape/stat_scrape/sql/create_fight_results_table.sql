-- Tabla EXTERNA complementaria - NO interfiere con pipeline de Scrapy
-- Complementa la tabla 'fights' existente con datos adicionales estructurados
-- Se puede relacionar mediante JOINs usando fight_id, pero SIN foreign keys

CREATE TABLE IF NOT EXISTS external_fight_results (
    id SERIAL PRIMARY KEY,
    event_name VARCHAR(255),
    bout VARCHAR(255),
    outcome VARCHAR(10),  -- W/L indica ganador/perdedor
    weightclass VARCHAR(255),
    method VARCHAR(255),
    round INTEGER,
    time VARCHAR(50),
    time_format VARCHAR(100),
    referee VARCHAR(255),
    details TEXT,
    url VARCHAR(500) UNIQUE,
    fight_id VARCHAR(255),  -- ID extraído de la URL para relacionar con tabla fights
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para mejorar performance de queries (sin foreign keys)
CREATE INDEX IF NOT EXISTS idx_external_fight_results_fight_id ON external_fight_results(fight_id);
CREATE INDEX IF NOT EXISTS idx_external_fight_results_url ON external_fight_results(url);
CREATE INDEX IF NOT EXISTS idx_external_fight_results_event_name ON external_fight_results(event_name);

-- Comentarios para documentación
COMMENT ON TABLE external_fight_results IS 'Tabla EXTERNA complementaria - Resultados de peleas desde repositorio externo. NO interfiere con pipeline de Scrapy';
COMMENT ON COLUMN external_fight_results.fight_id IS 'ID de la pelea extraído de la URL. Se puede relacionar con tabla fights.id mediante JOINs, pero SIN foreign key';

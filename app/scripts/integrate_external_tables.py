"""
Script INDEPENDIENTE para cargar tablas complementarias desde repositorio externo.
NO modifica ni interfiere con el pipeline de Scrapy existente.

Tablas creadas (complementarias, NO integradas):
- external_fight_results (complementa fights)
- external_fighter_tott (complementa fighters)
- external_fight_stats (complementa fights, si se decide cargar)

Estas tablas son completamente separadas y se pueden complementar mediante JOINs
usando IDs comunes, pero sin foreign keys que puedan interferir.
"""

import pandas as pd
import psycopg2
import os
import requests
from io import StringIO
from dotenv import load_dotenv
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URLs de los CSVs
CSV_URLS = {
    'fight_results': 'https://raw.githubusercontent.com/Greco1899/scrape_ufc_stats/main/ufc_fight_results.csv',
    'fight_stats': 'https://raw.githubusercontent.com/Greco1899/scrape_ufc_stats/main/ufc_fight_stats.csv',
    'fighter_tott': 'https://raw.githubusercontent.com/Greco1899/scrape_ufc_stats/main/ufc_fighter_tott.csv'
}


def connect_to_db():
    """Conecta a la base de datos Supabase"""
    load_dotenv()
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST"),
        user=os.environ.get("POSTGRES_USER"),
        password=os.environ.get("POSTGRES_PASSWORD"),
        dbname=os.environ.get("POSTGRES_DB"),
        port=os.environ.get("POSTGRES_PORT"),
    )


def download_csv(url, name):
    """Descarga un CSV desde GitHub"""
    logger.info(f"Descargando {name}...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text))
        logger.info(f"✅ {name} descargado: {len(df)} filas, {len(df.columns)} columnas")
        return df
    except Exception as e:
        logger.error(f"❌ Error descargando {name}: {e}")
        return None


def analyze_fight_results(df_results):
    """Analiza ufc_fight_results.csv y compara con tabla fights"""
    logger.info("\n=== Analizando ufc_fight_results.csv ===")
    logger.info(f"Columnas: {list(df_results.columns)}")
    logger.info(f"Primeras filas:\n{df_results.head(3)}")
    
    # Extraer ID de la URL
    if 'URL' in df_results.columns:
        df_results['fight_id'] = df_results['URL'].str.extract(r'/([^/]+)$')
    
    return df_results


def analyze_fight_stats(df_stats):
    """Analiza ufc_fight_stats.csv"""
    logger.info("\n=== Analizando ufc_fight_stats.csv ===")
    logger.info(f"Columnas: {list(df_stats.columns)}")
    logger.info(f"Primeras filas:\n{df_stats.head(3)}")
    
    return df_stats


def analyze_fighter_tott(df_tott):
    """Analiza ufc_fighter_tott.csv"""
    logger.info("\n=== Analizando ufc_fighter_tott.csv ===")
    logger.info(f"Columnas: {list(df_tott.columns)}")
    logger.info(f"Primeras filas:\n{df_tott.head(3)}")
    
    return df_tott


def create_fight_results_table(conn):
    """Crea tabla EXTERNA para fight_results (complementaria, no integrada)"""
    cursor = conn.cursor()
    
    create_table_sql = """
    -- Tabla complementaria externa - NO interfiere con pipeline de Scrapy
    CREATE TABLE IF NOT EXISTS external_fight_results (
        id SERIAL PRIMARY KEY,
        event_name VARCHAR(255),
        bout VARCHAR(255),
        outcome VARCHAR(10),
        weightclass VARCHAR(255),
        method VARCHAR(255),
        round INTEGER,
        time VARCHAR(50),
        time_format VARCHAR(100),
        referee VARCHAR(255),
        details TEXT,
        url VARCHAR(500) UNIQUE,
        fight_id VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_fight_results_fight_id ON fight_results(fight_id);
    CREATE INDEX IF NOT EXISTS idx_fight_results_url ON fight_results(url);
    """
    
    cursor.execute(create_table_sql)
    conn.commit()
    logger.info("✅ Tabla external_fight_results creada/verificada (complementaria, independiente)")


def create_fighter_tott_table(conn):
    """Crea tabla EXTERNA para fighter_tott (complementaria, no integrada)"""
    cursor = conn.cursor()
    
    create_table_sql = """
    -- Tabla complementaria externa - NO interfiere con pipeline de Scrapy
    CREATE TABLE IF NOT EXISTS external_fighter_tott (
        id SERIAL PRIMARY KEY,
        fighter_id VARCHAR(255),
        fight_id VARCHAR(255),
        fighter_name VARCHAR(255),
        age INTEGER,
        height VARCHAR(50),
        weight VARCHAR(50),
        reach VARCHAR(50),
        stance VARCHAR(50),
        dob DATE,
        sig_str_landed_per_min DECIMAL(10,2),
        sig_str_accuracy INTEGER,
        sig_str_absorbed_per_min DECIMAL(10,2),
        sig_str_defense INTEGER,
        takedown_avg DECIMAL(10,2),
        takedown_accuracy INTEGER,
        takedown_defense INTEGER,
        submission_avg DECIMAL(10,2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(fighter_id, fight_id)
    );
    
    CREATE INDEX IF NOT EXISTS idx_fighter_tott_fighter_id ON fighter_tott(fighter_id);
    CREATE INDEX IF NOT EXISTS idx_fighter_tott_fight_id ON fighter_tott(fight_id);
    """
    
    cursor.execute(create_table_sql)
    conn.commit()
    logger.info("✅ Tabla external_fighter_tott creada/verificada (complementaria, independiente)")


def load_fight_results(df_results, conn):
    """Carga fight_results a la base de datos"""
    if df_results is None or df_results.empty:
        logger.warning("⚠️  No hay datos de fight_results para cargar")
        return
    
    cursor = conn.cursor()
    
    # Preparar datos
    df_results['fight_id'] = df_results['URL'].str.extract(r'/([^/]+)$') if 'URL' in df_results.columns else None
    
    insert_sql = """
    INSERT INTO external_fight_results 
    (event_name, bout, outcome, weightclass, method, round, time, time_format, 
     referee, details, url, fight_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (url) DO UPDATE SET
        event_name = EXCLUDED.event_name,
        bout = EXCLUDED.bout,
        outcome = EXCLUDED.outcome,
        weightclass = EXCLUDED.weightclass,
        method = EXCLUDED.method,
        round = EXCLUDED.round,
        time = EXCLUDED.time,
        time_format = EXCLUDED.time_format,
        referee = EXCLUDED.referee,
        details = EXCLUDED.details,
        fight_id = EXCLUDED.fight_id,
        updated_at = CURRENT_TIMESTAMP
    """
    
    records = []
    for _, row in df_results.iterrows():
        records.append((
            row.get('EVENT', None),
            row.get('BOUT', None),
            row.get('OUTCOME', None),
            row.get('WEIGHTCLASS', None),
            row.get('METHOD', None),
            int(row.get('ROUND', 0)) if pd.notna(row.get('ROUND')) else None,
            row.get('TIME', None),
            row.get('TIME FORMAT', None),
            row.get('REFEREE', None),
            row.get('DETAILS', None),
            row.get('URL', None),
            row.get('fight_id', None)
        ))
    
    try:
        cursor.executemany(insert_sql, records)
        conn.commit()
        logger.info(f"✅ {len(records)} registros cargados/actualizados en external_fight_results")
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Error cargando fight_results: {e}")
        raise


def load_fighter_tott(df_tott, conn):
    """Carga fighter_tott a la base de datos"""
    if df_tott is None or df_tott.empty:
        logger.warning("⚠️  No hay datos de fighter_tott para cargar")
        return
    
    cursor = conn.cursor()
    
    # Mapeo flexible de columnas (normalizar nombres)
    column_mapping = {
        'fighter_id': ['fighter_id', 'fighterid', 'id'],
        'fight_id': ['fight_id', 'fightid', 'fight_id'],
        'fighter_name': ['fighter_name', 'name', 'fighter', 'fighter_name'],
        'age': ['age', 'age_at_fight'],
        'height': ['height', 'ht'],
        'weight': ['weight', 'wt', 'weight_at_fight'],
        'reach': ['reach'],
        'stance': ['stance'],
        'dob': ['dob', 'date_of_birth', 'birthdate'],
        'sig_str_landed_per_min': ['sig_str_landed_per_min', 'sig_str_landed', 'ss_landed_per_min'],
        'sig_str_accuracy': ['sig_str_accuracy', 'ss_accuracy', 'striking_accuracy'],
        'sig_str_absorbed_per_min': ['sig_str_absorbed_per_min', 'sig_str_absorbed', 'ss_absorbed_per_min'],
        'sig_str_defense': ['sig_str_defense', 'ss_defense', 'striking_defense'],
        'takedown_avg': ['takedown_avg', 'td_avg', 'takedown_average'],
        'takedown_accuracy': ['takedown_accuracy', 'td_accuracy'],
        'takedown_defense': ['takedown_defense', 'td_defense'],
        'submission_avg': ['submission_avg', 'sub_avg', 'submission_average']
    }
    
    def find_column(df, possible_names):
        """Encuentra una columna por posibles nombres"""
        for name in possible_names:
            if name in df.columns:
                return name
        return None
    
    # Construir mapeo real
    actual_mapping = {}
    for target_col, possible_names in column_mapping.items():
        found_col = find_column(df_tott, possible_names)
        if found_col:
            actual_mapping[target_col] = found_col
        else:
            logger.warning(f"⚠️  No se encontró columna para {target_col}")
    
    logger.info(f"📋 Mapeo de columnas: {actual_mapping}")
    
    insert_sql = """
    INSERT INTO external_fighter_tott 
    (fighter_id, fight_id, fighter_name, age, height, weight, reach, stance, dob,
     sig_str_landed_per_min, sig_str_accuracy, sig_str_absorbed_per_min, 
     sig_str_defense, takedown_avg, takedown_accuracy, takedown_defense, submission_avg)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (fighter_id, fight_id) DO UPDATE SET
        fighter_name = EXCLUDED.fighter_name,
        age = EXCLUDED.age,
        height = EXCLUDED.height,
        weight = EXCLUDED.weight,
        reach = EXCLUDED.reach,
        stance = EXCLUDED.stance,
        dob = EXCLUDED.dob,
        sig_str_landed_per_min = EXCLUDED.sig_str_landed_per_min,
        sig_str_accuracy = EXCLUDED.sig_str_accuracy,
        sig_str_absorbed_per_min = EXCLUDED.sig_str_absorbed_per_min,
        sig_str_defense = EXCLUDED.sig_str_defense,
        takedown_avg = EXCLUDED.takedown_avg,
        takedown_accuracy = EXCLUDED.takedown_accuracy,
        takedown_defense = EXCLUDED.takedown_defense,
        submission_avg = EXCLUDED.submission_avg,
        updated_at = CURRENT_TIMESTAMP
    """
    
    records = []
    for _, row in df_tott.iterrows():
        def get_value(col_name):
            source_col = actual_mapping.get(col_name)
            if source_col and source_col in df_tott.columns:
                val = row[source_col]
                # Convertir tipos apropiados
                if col_name in ['age', 'sig_str_accuracy', 'sig_str_defense', 
                               'takedown_accuracy', 'takedown_defense']:
                    try:
                        return int(val) if pd.notna(val) else None
                    except:
                        return None
                elif col_name in ['sig_str_landed_per_min', 'sig_str_absorbed_per_min',
                                 'takedown_avg', 'submission_avg']:
                    try:
                        return float(val) if pd.notna(val) else None
                    except:
                        return None
                return val if pd.notna(val) else None
            return None
        
        records.append((
            get_value('fighter_id'),
            get_value('fight_id'),
            get_value('fighter_name'),
            get_value('age'),
            get_value('height'),
            get_value('weight'),
            get_value('reach'),
            get_value('stance'),
            get_value('dob'),
            get_value('sig_str_landed_per_min'),
            get_value('sig_str_accuracy'),
            get_value('sig_str_absorbed_per_min'),
            get_value('sig_str_defense'),
            get_value('takedown_avg'),
            get_value('takedown_accuracy'),
            get_value('takedown_defense'),
            get_value('submission_avg')
        ))
    
    try:
        cursor.executemany(insert_sql, records)
        conn.commit()
        logger.info(f"✅ {len(records)} registros cargados/actualizados en external_fighter_tott")
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Error cargando fighter_tott: {e}")
        logger.error(f"   Columnas disponibles: {list(df_tott.columns)}")
        raise


def main():
    """Función principal"""
    logger.info("🚀 Iniciando integración de tablas externas...")
    
    # Descargar CSVs
    df_results = download_csv(CSV_URLS['fight_results'], 'ufc_fight_results.csv')
    df_stats = download_csv(CSV_URLS['fight_stats'], 'ufc_fight_stats.csv')
    df_tott = download_csv(CSV_URLS['fighter_tott'], 'ufc_fighter_tott.csv')
    
    # Analizar estructura
    if df_results is not None:
        df_results = analyze_fight_results(df_results)
    
    if df_stats is not None:
        df_stats = analyze_fight_stats(df_stats)
    
    if df_tott is not None:
        df_tott = analyze_fighter_tott(df_tott)
    
    # Conectar a BD
    conn = connect_to_db()
    
    try:
        # Crear tablas
        if df_results is not None:
            create_fight_results_table(conn)
            load_fight_results(df_results, conn)
        
        if df_tott is not None:
            create_fighter_tott_table(conn)
            load_fighter_tott(df_tott, conn)
        
        # Nota: fight_stats puede ser similar a tu tabla fights existente
        # Por ahora, solo analizamos su estructura
        if df_stats is not None:
            logger.info("\n📊 fight_stats analizado - revisa si necesita tabla separada")
            logger.info("   Compara con tu tabla 'fights' existente para decidir")
        
        logger.info("\n✅ Carga de tablas complementarias completada!")
        logger.info("\n📊 Tablas creadas (INDEPENDIENTES del pipeline de Scrapy):")
        logger.info("   - external_fight_results (complementa fights)")
        logger.info("   - external_fighter_tott (complementa fighters)")
        logger.info("\n💡 Estas tablas son complementarias pero separadas:")
        logger.info("   - Puedes hacer JOINs usando IDs comunes (fight_id, fighter_id)")
        logger.info("   - NO tienen foreign keys que interfieran con tu pipeline")
        logger.info("   - NO modifican las tablas existentes (events, fights, fighters)")
        logger.info("\n🔍 Próximos pasos:")
        logger.info("   1. Revisa las tablas en Supabase")
        logger.info("   2. Usa JOINs para complementar datos cuando necesites")
        logger.info("   3. Ejemplo: SELECT * FROM fights f JOIN external_fight_results efr ON f.id = efr.fight_id")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()

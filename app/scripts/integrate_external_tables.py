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
    
    # Buscar el archivo SQL (funciona desde app/ o desde raíz)
    sql_paths = [
        "stat_scrape/sql/create_fight_results_table.sql",
        "app/stat_scrape/stat_scrape/sql/create_fight_results_table.sql",
        "../stat_scrape/stat_scrape/sql/create_fight_results_table.sql"
    ]
    
    sql_content = None
    for path in sql_paths:
        if os.path.exists(path):
            sql_content = open(path, "r").read()
            break
    
    if not sql_content:
        raise FileNotFoundError(f"No se encontró create_fight_results_table.sql en: {sql_paths}")
    
    cursor.execute(sql_content)
    conn.commit()
    logger.info("✅ Tabla external_fight_results creada/verificada (complementaria, independiente)")


def create_fighter_tott_table(conn):
    """Crea tabla EXTERNA para fighter_tott (complementaria, no integrada)"""
    cursor = conn.cursor()
    
    # Buscar el archivo SQL (funciona desde app/ o desde raíz)
    sql_paths = [
        "stat_scrape/sql/create_fighter_tott_table.sql",
        "app/stat_scrape/stat_scrape/sql/create_fighter_tott_table.sql",
        "../stat_scrape/stat_scrape/sql/create_fighter_tott_table.sql"
    ]
    
    sql_content = None
    for path in sql_paths:
        if os.path.exists(path):
            sql_content = open(path, "r").read()
            break
    
    if not sql_content:
        raise FileNotFoundError(f"No se encontró create_fighter_tott_table.sql en: {sql_paths}")
    
    create_table_sql = sql_content
    
    cursor.execute(create_table_sql)
    conn.commit()
    logger.info("✅ Tabla external_fighter_tott creada/verificada (complementaria, independiente)")


def create_fight_stats_table(conn):
    """Crea tabla EXTERNA para fight_stats (complementaria, no integrada)"""
    cursor = conn.cursor()
    
    # Buscar el archivo SQL (funciona desde app/ o desde raíz)
    sql_paths = [
        "stat_scrape/sql/create_fight_stats_table.sql",
        "app/stat_scrape/stat_scrape/sql/create_fight_stats_table.sql",
        "../stat_scrape/stat_scrape/sql/create_fight_stats_table.sql"
    ]
    
    sql_content = None
    for path in sql_paths:
        if os.path.exists(path):
            sql_content = open(path, "r").read()
            break
    
    if not sql_content:
        raise FileNotFoundError(f"No se encontró create_fight_stats_table.sql en: {sql_paths}")
    
    create_table_sql = sql_content
    
    cursor.execute(create_table_sql)
    conn.commit()
    logger.info("✅ Tabla external_fight_stats creada/verificada (complementaria, independiente)")


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


def parse_fraction(value):
    """Parsea valores en formato 'X of Y' o 'X/Y'"""
    if pd.isna(value) or value == '---' or value == '':
        return None, None
    value_str = str(value).strip()
    if ' of ' in value_str:
        parts = value_str.split(' of ')
        try:
            landed = int(parts[0]) if parts[0] else None
            attempted = int(parts[1]) if len(parts) > 1 and parts[1] else None
            return landed, attempted
        except:
            return None, None
    return None, None


def parse_percentage(value):
    """Parsea porcentajes, maneja '---' y valores nulos"""
    if pd.isna(value) or value == '---' or value == '':
        return None
    value_str = str(value).strip().replace('%', '')
    try:
        return int(float(value_str))
    except:
        return None


def parse_time(value):
    """Parsea tiempo en formato 'M:SS' o '--'"""
    if pd.isna(value) or value == '--' or value == '':
        return None
    value_str = str(value).strip()
    if ':' in value_str:
        return value_str
    return None


def extract_round_number(round_str):
    """Extrae el número del round de strings como 'Round 1', 'Round 2', etc."""
    if pd.isna(round_str):
        return None, None
    round_str = str(round_str).strip()
    if 'Round' in round_str:
        try:
            num = int(round_str.replace('Round', '').strip())
            return num, round_str
        except:
            return None, round_str
    return None, round_str


def load_fight_stats(df_stats, conn):
    """Carga fight_stats a la base de datos (estadísticas por round)"""
    if df_stats is None or df_stats.empty:
        logger.warning("⚠️  No hay datos de fight_stats para cargar")
        return
    
    cursor = conn.cursor()
    
    insert_sql = """
    INSERT INTO external_fight_stats 
    (event_name, bout, round_number, round_label, fighter_name, knockdowns,
     sig_str_landed, sig_str_attempted, sig_str_percentage,
     total_str_landed, total_str_attempted,
     takedown_landed, takedown_attempted, takedown_percentage,
     submission_attempts, reversals, control_time,
     head_landed, head_attempted,
     body_landed, body_attempted,
     leg_landed, leg_attempted,
     distance_landed, distance_attempted,
     clinch_landed, clinch_attempted,
     ground_landed, ground_attempted)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (event_name, bout, round_number, fighter_name) DO UPDATE SET
        round_label = EXCLUDED.round_label,
        knockdowns = EXCLUDED.knockdowns,
        sig_str_landed = EXCLUDED.sig_str_landed,
        sig_str_attempted = EXCLUDED.sig_str_attempted,
        sig_str_percentage = EXCLUDED.sig_str_percentage,
        total_str_landed = EXCLUDED.total_str_landed,
        total_str_attempted = EXCLUDED.total_str_attempted,
        takedown_landed = EXCLUDED.takedown_landed,
        takedown_attempted = EXCLUDED.takedown_attempted,
        takedown_percentage = EXCLUDED.takedown_percentage,
        submission_attempts = EXCLUDED.submission_attempts,
        reversals = EXCLUDED.reversals,
        control_time = EXCLUDED.control_time,
        head_landed = EXCLUDED.head_landed,
        head_attempted = EXCLUDED.head_attempted,
        body_landed = EXCLUDED.body_landed,
        body_attempted = EXCLUDED.body_attempted,
        leg_landed = EXCLUDED.leg_landed,
        leg_attempted = EXCLUDED.leg_attempted,
        distance_landed = EXCLUDED.distance_landed,
        distance_attempted = EXCLUDED.distance_attempted,
        clinch_landed = EXCLUDED.clinch_landed,
        clinch_attempted = EXCLUDED.clinch_attempted,
        ground_landed = EXCLUDED.ground_landed,
        ground_attempted = EXCLUDED.ground_attempted,
        updated_at = CURRENT_TIMESTAMP
    """
    
    records = []
    for _, row in df_stats.iterrows():
        # Parsear round
        round_num, round_label = extract_round_number(row.get('ROUND', None))
        
        # Parsear sig strikes
        sig_str_landed, sig_str_attempted = parse_fraction(row.get('SIG.STR.', None))
        sig_str_pct = parse_percentage(row.get('SIG.STR. %', None))
        
        # Parsear total strikes
        total_str_landed, total_str_attempted = parse_fraction(row.get('TOTAL STR.', None))
        
        # Parsear takedowns
        td_landed, td_attempted = parse_fraction(row.get('TD', None))
        td_pct = parse_percentage(row.get('TD %', None))
        
        # Parsear otros campos
        kd = None
        if pd.notna(row.get('KD', None)):
            try:
                kd = float(row.get('KD', 0))
            except:
                kd = None
        
        sub_att = None
        if pd.notna(row.get('SUB.ATT', None)):
            try:
                sub_att = float(row.get('SUB.ATT', 0))
            except:
                sub_att = None
        
        rev = None
        if pd.notna(row.get('REV.', None)):
            try:
                rev = float(row.get('REV.', 0))
            except:
                rev = None
        
        # Parsear control time
        ctrl = parse_time(row.get('CTRL', None))
        
        # Parsear HEAD, BODY, LEG, DISTANCE, CLINCH, GROUND
        head_landed, head_attempted = parse_fraction(row.get('HEAD', None))
        body_landed, body_attempted = parse_fraction(row.get('BODY', None))
        leg_landed, leg_attempted = parse_fraction(row.get('LEG', None))
        dist_landed, dist_attempted = parse_fraction(row.get('DISTANCE', None))
        clinch_landed, clinch_attempted = parse_fraction(row.get('CLINCH', None))
        ground_landed, ground_attempted = parse_fraction(row.get('GROUND', None))
        
        records.append((
            row.get('EVENT', None),
            row.get('BOUT', None),
            round_num,
            round_label,
            row.get('FIGHTER', None),
            kd,
            sig_str_landed,
            sig_str_attempted,
            sig_str_pct,
            total_str_landed,
            total_str_attempted,
            td_landed,
            td_attempted,
            td_pct,
            sub_att,
            rev,
            ctrl,
            head_landed,
            head_attempted,
            body_landed,
            body_attempted,
            leg_landed,
            leg_attempted,
            dist_landed,
            dist_attempted,
            clinch_landed,
            clinch_attempted,
            ground_landed,
            ground_attempted
        ))
    
    try:
        cursor.executemany(insert_sql, records)
        conn.commit()
        logger.info(f"✅ {len(records)} registros cargados en external_fight_stats")
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Error cargando fight_stats: {e}")
        logger.error(f"   Columnas disponibles: {list(df_stats.columns)}")
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
        
        # Cargar fight_stats (estadísticas por round)
        if df_stats is not None:
            create_fight_stats_table(conn)
            load_fight_stats(df_stats, conn)
        
        logger.info("\n✅ Carga de tablas complementarias completada!")
        logger.info("\n📊 Tablas creadas (INDEPENDIENTES del pipeline de Scrapy):")
        logger.info("   - external_fight_results (complementa fights)")
        logger.info("   - external_fighter_tott (complementa fighters)")
        logger.info("   - external_fight_stats (estadísticas por round, complementa fights)")
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

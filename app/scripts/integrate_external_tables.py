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
import psycopg2.errors
import psycopg2.extras
import os
import requests
from io import StringIO
from dotenv import load_dotenv
from pathlib import Path
import logging
from datetime import date, datetime

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


def download_csv(url, name, max_retries=3, timeout=120):
    """Descarga un CSV desde GitHub con reintentos y timeout aumentado"""
    logger.info(f"Descargando {name}...")
    
    for attempt in range(max_retries):
        try:
            # Timeout aumentado para archivos grandes como fighter_tott.csv
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            df = pd.read_csv(StringIO(response.text))
            logger.info(f"✅ {name} descargado: {len(df)} filas, {len(df.columns)} columnas")
            return df
        except requests.exceptions.Timeout as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10
                logger.warning(f"⏳ Timeout descargando {name} (intento {attempt + 1}/{max_retries}). Reintentando en {wait_time}s...")
                import time
                time.sleep(wait_time)
            else:
                logger.error(f"❌ Error descargando {name} después de {max_retries} intentos: {e}")
                return None
        except Exception as e:
            logger.error(f"❌ Error descargando {name}: {e}")
            return None
    
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
    
    # Buscar el archivo SQL usando rutas relativas desde el script
    script_dir = os.path.dirname(os.path.abspath(__file__))  # .../app/scripts
    app_dir = os.path.dirname(script_dir)  # .../app
    repo_dir = os.path.dirname(app_dir)  # repo root
    
    sql_paths = [
        os.path.join(app_dir, "stat_scrape", "stat_scrape", "sql", "create_fight_results_table.sql"),
        os.path.join(repo_dir, "app", "stat_scrape", "stat_scrape", "sql", "create_fight_results_table.sql"),
        "stat_scrape/stat_scrape/sql/create_fight_results_table.sql",
        "../stat_scrape/stat_scrape/sql/create_fight_results_table.sql"
    ]
    
    sql_content = None
    for path in sql_paths:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            sql_content = open(abs_path, "r").read()
            logger.debug(f"✅ Archivo SQL encontrado en: {abs_path}")
            break
    
    if not sql_content:
        raise FileNotFoundError(f"No se encontró create_fight_results_table.sql. Buscado en: {sql_paths}")
    
    cursor.execute(sql_content)
    conn.commit()
    logger.info("✅ Tabla external_fight_results creada/verificada (complementaria, independiente)")


def create_fighter_tott_table(conn):
    """Crea tabla EXTERNA para fighter_tott (complementaria, no integrada)"""
    cursor = conn.cursor()
    
    # Buscar el archivo SQL usando rutas relativas desde el script
    script_dir = os.path.dirname(os.path.abspath(__file__))  # .../app/scripts
    app_dir = os.path.dirname(script_dir)  # .../app
    repo_dir = os.path.dirname(app_dir)  # repo root
    
    sql_paths = [
        os.path.join(app_dir, "stat_scrape", "stat_scrape", "sql", "create_fighter_tott_table.sql"),
        os.path.join(repo_dir, "app", "stat_scrape", "stat_scrape", "sql", "create_fighter_tott_table.sql"),
        "stat_scrape/stat_scrape/sql/create_fighter_tott_table.sql",
        "../stat_scrape/stat_scrape/sql/create_fighter_tott_table.sql"
    ]
    
    sql_content = None
    for path in sql_paths:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            sql_content = open(abs_path, "r").read()
            logger.debug(f"✅ Archivo SQL encontrado en: {abs_path}")
            break
    
    if not sql_content:
        raise FileNotFoundError(f"No se encontró create_fighter_tott_table.sql. Buscado en: {sql_paths}")
    
    cursor.execute(sql_content)
    conn.commit()
    logger.info("✅ Tabla external_fighter_tott creada/verificada (complementaria, independiente)")


def create_fight_stats_table(conn):
    """Crea tabla EXTERNA para fight_stats (complementaria, no integrada)"""
    cursor = conn.cursor()
    
    # Buscar el archivo SQL usando rutas relativas desde el script
    script_dir = os.path.dirname(os.path.abspath(__file__))  # .../app/scripts
    app_dir = os.path.dirname(script_dir)  # .../app
    repo_dir = os.path.dirname(app_dir)  # repo root
    
    sql_paths = [
        os.path.join(app_dir, "stat_scrape", "stat_scrape", "sql", "create_fight_stats_table.sql"),
        os.path.join(repo_dir, "app", "stat_scrape", "stat_scrape", "sql", "create_fight_stats_table.sql"),
        "stat_scrape/stat_scrape/sql/create_fight_stats_table.sql",
        "../stat_scrape/stat_scrape/sql/create_fight_stats_table.sql"
    ]
    
    sql_content = None
    for path in sql_paths:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            sql_content = open(abs_path, "r").read()
            logger.debug(f"✅ Archivo SQL encontrado en: {abs_path}")
            break
    
    if not sql_content:
        raise FileNotFoundError(f"No se encontró create_fight_stats_table.sql. Buscado en: {sql_paths}")
    
    cursor.execute(sql_content)
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
    
    logger.info(f"📋 Columnas disponibles en CSV: {list(df_tott.columns)}")
    
    # Mapeo según las columnas reales del CSV
    # El CSV tiene: FIGHTER, HEIGHT, WEIGHT, REACH, STANCE, DOB, URL
    def find_column(df, possible_names):
        """Encuentra una columna por posibles nombres"""
        for name in possible_names:
            if name in df.columns:
                return name
        return None
    
    # Mapear columnas disponibles
    fighter_name_col = find_column(df_tott, ['FIGHTER', 'fighter_name', 'name', 'fighter'])
    height_col = find_column(df_tott, ['HEIGHT', 'height', 'ht'])
    weight_col = find_column(df_tott, ['WEIGHT', 'weight', 'wt'])
    reach_col = find_column(df_tott, ['REACH', 'reach'])
    stance_col = find_column(df_tott, ['STANCE', 'stance'])
    dob_col = find_column(df_tott, ['DOB', 'dob', 'date_of_birth', 'birthdate'])
    url_col = find_column(df_tott, ['URL', 'url', 'link'])
    
    logger.info(f"📋 Mapeo de columnas encontradas:")
    logger.info(f"   fighter_name: {fighter_name_col}")
    logger.info(f"   height: {height_col}")
    logger.info(f"   weight: {weight_col}")
    logger.info(f"   reach: {reach_col}")
    logger.info(f"   stance: {stance_col}")
    logger.info(f"   dob: {dob_col}")
    logger.info(f"   url: {url_col}")
    
    # Nota importante:
    # `ufc_fighter_tott.csv` (en este repo externo) NO trae `age`.
    # Para cubrir tu caso de uso, calculamos `age` desde `DOB` (edad actual aprox en años).
    
    insert_sql = """
    INSERT INTO external_fighter_tott 
    (fighter_id, fight_id, fighter_name, age, height, weight, reach, stance, dob,
     sig_str_landed_per_min, sig_str_accuracy, sig_str_absorbed_per_min, 
     sig_str_defense, takedown_avg, takedown_accuracy, takedown_defense, submission_avg)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
        # Extraer fighter_id de la URL si existe (este CSV suele tener fighter-details/ID)
        fighter_id = None
        if url_col and pd.notna(row.get(url_col)):
            url = str(row[url_col])
            # Intentar extraer ID de la URL (formato: .../fighter-details/ID o .../fight-details/ID)
            if 'fighter-details' in url:
                fighter_id = url.split('/')[-1] if url.endswith('/') else url.split('/')[-1]
        
        # Obtener valores de las columnas disponibles
        fighter_name = row.get(fighter_name_col) if fighter_name_col else None
        height = row.get(height_col) if height_col else None
        weight = row.get(weight_col) if weight_col else None
        reach = row.get(reach_col) if reach_col else None
        stance = row.get(stance_col) if stance_col else None
        
        # Parsear DOB si existe (DOB suele venir como "Jan 01, 1990")
        dob = None
        if dob_col and pd.notna(row.get(dob_col)):
            dob_str = str(row[dob_col]).strip()
            if dob_str and dob_str != '--' and dob_str != '':
                try:
                    # Intentar parsear diferentes formatos de fecha
                    for fmt in ['%b %d, %Y', '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                        try:
                            dob = datetime.strptime(dob_str, fmt).date()
                            break
                        except:
                            continue
                except:
                    dob = None

        age = None
        if dob:
            try:
                age = int((date.today() - dob).days / 365.25)
            except:
                age = None
        
        # Limpiar valores None y strings vacíos
        def clean_value(val):
            if pd.isna(val) or val == '--' or val == '':
                return None
            return str(val).strip() if val else None
        
        records.append((
            fighter_id,  # Puede ser None si no se puede extraer de URL
            None,        # fight_id - este CSV no es por pelea, lo dejamos NULL
            clean_value(fighter_name),
            age,   # age - calculada desde DOB
            clean_value(height),
            clean_value(weight),
            clean_value(reach),
            clean_value(stance),
            dob,
            None,  # sig_str_landed_per_min - no disponible
            None,  # sig_str_accuracy - no disponible
            None,  # sig_str_absorbed_per_min - no disponible
            None,  # sig_str_defense - no disponible
            None,  # takedown_avg - no disponible
            None,  # takedown_accuracy - no disponible
            None,  # takedown_defense - no disponible
            None   # submission_avg - no disponible
        ))
    
    try:
        # Hacemos UPSERT por fighter_id cuando existe; si no, por fighter_name.
        with_id = [r for r in records if r[0] and r[2]]
        without_id = [r for r in records if (not r[0]) and r[2]]

        insert_sql_by_id = """
        INSERT INTO external_fighter_tott
        (fighter_id, fight_id, fighter_name, age, height, weight, reach, stance, dob,
         sig_str_landed_per_min, sig_str_accuracy, sig_str_absorbed_per_min,
         sig_str_defense, takedown_avg, takedown_accuracy, takedown_defense, submission_avg)
        VALUES %s
        ON CONFLICT (fighter_id) WHERE fighter_id IS NOT NULL
        DO UPDATE SET
            fighter_name = EXCLUDED.fighter_name,
            age = EXCLUDED.age,
            height = EXCLUDED.height,
            weight = EXCLUDED.weight,
            reach = EXCLUDED.reach,
            stance = EXCLUDED.stance,
            dob = EXCLUDED.dob,
            updated_at = CURRENT_TIMESTAMP
        """

        insert_sql_by_name = """
        INSERT INTO external_fighter_tott
        (fighter_id, fight_id, fighter_name, age, height, weight, reach, stance, dob,
         sig_str_landed_per_min, sig_str_accuracy, sig_str_absorbed_per_min,
         sig_str_defense, takedown_avg, takedown_accuracy, takedown_defense, submission_avg)
        VALUES %s
        ON CONFLICT (fighter_name) WHERE fighter_id IS NULL
        DO UPDATE SET
            age = EXCLUDED.age,
            height = EXCLUDED.height,
            weight = EXCLUDED.weight,
            reach = EXCLUDED.reach,
            stance = EXCLUDED.stance,
            dob = EXCLUDED.dob,
            updated_at = CURRENT_TIMESTAMP
        """

        if with_id:
            psycopg2.extras.execute_values(cursor, insert_sql_by_id, with_id, page_size=1000)
        if without_id:
            psycopg2.extras.execute_values(cursor, insert_sql_by_name, without_id, page_size=1000)

        conn.commit()
        logger.info(f"✅ external_fighter_tott: {len(with_id)} upserts por fighter_id, {len(without_id)} upserts por fighter_name")
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Error cargando fighter_tott: {e}")
        logger.error(f"   Columnas disponibles: {list(df_tott.columns)}")
        import traceback
        logger.error(traceback.format_exc())
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
    
    # Vectorizamos parsing para que sea MUCHO más rápido (evita iterrows).
    df = df_stats.copy()

    # Round number + label
    df["round_label"] = df["ROUND"].astype(str)
    df["round_number"] = pd.to_numeric(df["ROUND"].astype(str).str.extract(r"(\d+)")[0], errors="coerce").astype("Int64")

    def split_of(series: pd.Series):
        s = series.astype(str).replace({"nan": pd.NA, "---": pd.NA, "": pd.NA})
        parts = s.str.split(" of ", n=1, expand=True)
        landed = pd.to_numeric(parts[0], errors="coerce").astype("Int64")
        attempted = pd.to_numeric(parts[1], errors="coerce").astype("Int64") if parts.shape[1] > 1 else pd.Series([pd.NA] * len(series), dtype="Int64")
        return landed, attempted

    def pct(series: pd.Series):
        s = series.astype(str).replace({"nan": pd.NA, "---": pd.NA, "": pd.NA})
        s = s.str.replace("%", "", regex=False)
        return pd.to_numeric(s, errors="coerce").astype("Int64")

    kd = pd.to_numeric(df["KD"], errors="coerce")
    sub_att = pd.to_numeric(df["SUB.ATT"], errors="coerce")
    rev = pd.to_numeric(df["REV."], errors="coerce")
    ctrl = df["CTRL"].astype(str).replace({"nan": pd.NA, "--": pd.NA, "": pd.NA})

    sig_l, sig_a = split_of(df["SIG.STR."])
    tot_l, tot_a = split_of(df["TOTAL STR."])
    td_l, td_a = split_of(df["TD"])
    head_l, head_a = split_of(df["HEAD"])
    body_l, body_a = split_of(df["BODY"])
    leg_l, leg_a = split_of(df["LEG"])
    dist_l, dist_a = split_of(df["DISTANCE"])
    clinch_l, clinch_a = split_of(df["CLINCH"])
    ground_l, ground_a = split_of(df["GROUND"])

    sig_pct = pct(df["SIG.STR. %"])
    td_pct = pct(df["TD %"])

    out = pd.DataFrame(
        {
            "event_name": df["EVENT"],
            "bout": df["BOUT"],
            "round_number": df["round_number"],
            "round_label": df["round_label"],
            "fighter_name": df["FIGHTER"],
            "knockdowns": kd,
            "sig_str_landed": sig_l,
            "sig_str_attempted": sig_a,
            "sig_str_percentage": sig_pct,
            "total_str_landed": tot_l,
            "total_str_attempted": tot_a,
            "takedown_landed": td_l,
            "takedown_attempted": td_a,
            "takedown_percentage": td_pct,
            "submission_attempts": sub_att,
            "reversals": rev,
            "control_time": ctrl,
            "head_landed": head_l,
            "head_attempted": head_a,
            "body_landed": body_l,
            "body_attempted": body_a,
            "leg_landed": leg_l,
            "leg_attempted": leg_a,
            "distance_landed": dist_l,
            "distance_attempted": dist_a,
            "clinch_landed": clinch_l,
            "clinch_attempted": clinch_a,
            "ground_landed": ground_l,
            "ground_attempted": ground_a,
        }
    )

    # Convertimos a tuplas
    records = list(out.itertuples(index=False, name=None))
    
    try:
        # execute_values es MUCHO más rápido que executemany para volumen grande
        psycopg2.extras.execute_values(cursor, insert_sql.replace("VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, \n            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", "VALUES %s"), records, page_size=2000)
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
        # Crear tablas (siempre intentar crear, incluso si algunos CSVs fallaron)
        try:
            create_fight_results_table(conn)
            if df_results is not None:
                load_fight_results(df_results, conn)
            else:
                logger.warning("⚠️  No se cargaron datos de fight_results (CSV no descargado)")
        except Exception as e:
            logger.error(f"❌ Error procesando fight_results: {e}")
        
        try:
            create_fighter_tott_table(conn)
            if df_tott is not None:
                load_fighter_tott(df_tott, conn)
            else:
                logger.warning("⚠️  No se cargaron datos de fighter_tott (CSV no descargado)")
        except Exception as e:
            logger.error(f"❌ Error procesando fighter_tott: {e}")
        
        try:
            create_fight_stats_table(conn)
            if df_stats is not None:
                load_fight_stats(df_stats, conn)
            else:
                logger.warning("⚠️  No se cargaron datos de fight_stats (CSV no descargado)")
        except Exception as e:
            logger.error(f"❌ Error procesando fight_stats: {e}")
        
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

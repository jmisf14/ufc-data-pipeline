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
    """
    Carga `ufc_fight_results.csv` en la tabla `external_fight_results`
    haciendo un snapshot completo (TRUNCATE + INSERT).
    No se inventan columnas ni se hace parsing complejo: se respeta el CSV.
    """
    if df_results is None or df_results.empty:
        logger.warning("⚠️  No hay datos de fight_results para cargar")
        return

    required_cols = [
        "EVENT",
        "BOUT",
        "OUTCOME",
        "WEIGHTCLASS",
        "METHOD",
        "ROUND",
        "TIME",
        "TIME FORMAT",
        "REFEREE",
        "DETAILS",
        "URL",
    ]
    missing = [c for c in required_cols if c not in df_results.columns]
    if missing:
        logger.error(f"❌ Columnas faltantes en fight_results CSV: {missing}")
        return

    cursor = conn.cursor()

    # Extraemos columnas en el mismo orden que la tabla
    df = df_results[required_cols].copy()
    df = df.where(pd.notna(df), None)

    # Snapshot completo
    cursor.execute("TRUNCATE TABLE public.external_fight_results;")

    insert_sql = """
        INSERT INTO public.external_fight_results
        (event, bout, outcome, weightclass, method,
         round, time, time_format, referee, details, url)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    records = list(df.itertuples(index=False, name=None))

    try:
        cursor.executemany(insert_sql, records)
        conn.commit()
        logger.info(f"✅ {len(records)} filas cargadas en external_fight_results")
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Error cargando fight_results: {e}")
        raise


def load_fighter_tott(df_tott, conn):
    """
    Carga `ufc_fighter_tott.csv` en la tabla `external_fighter_tott`
    haciendo un snapshot completo (TRUNCATE + INSERT).
    Solo usa las columnas que existen realmente en el CSV.
    """
    if df_tott is None or df_tott.empty:
        logger.warning("⚠️  No hay datos de fighter_tott para cargar")
        return

    cursor = conn.cursor()

    required_cols = ["FIGHTER", "HEIGHT", "WEIGHT", "REACH", "STANCE", "DOB", "URL"]
    missing = [c for c in required_cols if c not in df_tott.columns]
    if missing:
        logger.error(f"❌ Columnas faltantes en fighter_tott CSV: {missing}")
        return

    logger.info(f"📋 Columnas disponibles en CSV fighter_tott: {list(df_tott.columns)}")

    df = df_tott[required_cols].copy()
    df = df.where(pd.notna(df), None)

    # Snapshot completo
    cursor.execute("TRUNCATE TABLE public.external_fighter_tott;")

    insert_sql = """
        INSERT INTO public.external_fighter_tott
        (fighter, height, weight, reach, stance, dob, url)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """

    records = list(df.itertuples(index=False, name=None))

    try:
        cursor.executemany(insert_sql, records)
        conn.commit()
        logger.info(f"✅ {len(records)} filas cargadas en external_fighter_tott")
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Error cargando fighter_tott: {e}")
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
    """
    Carga `ufc_fight_stats.csv` en la tabla `external_fight_stats`
    haciendo un snapshot completo (TRUNCATE + INSERT).
    No se parsean porcentajes ni fracciones; se guarda el texto tal cual.
    """
    if df_stats is None or df_stats.empty:
        logger.warning("⚠️  No hay datos de fight_stats para cargar")
        return

    required_cols = [
        "EVENT",
        "BOUT",
        "ROUND",
        "FIGHTER",
        "KD",
        "SIG.STR.",
        "SIG.STR. %",
        "TOTAL STR.",
        "TD",
        "TD %",
        "SUB.ATT",
        "REV.",
        "CTRL",
        "HEAD",
        "BODY",
        "LEG",
        "DISTANCE",
        "CLINCH",
        "GROUND",
    ]
    missing = [c for c in required_cols if c not in df_stats.columns]
    if missing:
        logger.error(f"❌ Columnas faltantes en fight_stats CSV: {missing}")
        return

    cursor = conn.cursor()

    df = df_stats[required_cols].copy()
    df = df.where(pd.notna(df), None)

    # Snapshot completo
    cursor.execute("TRUNCATE TABLE public.external_fight_stats;")

    insert_sql = """
        INSERT INTO public.external_fight_stats
        (event, bout, round, fighter, kd,
         sig_str, sig_str_pct, total_str, td, td_pct,
         sub_att, rev, ctrl, head, body, leg, distance, clinch, ground)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    records = list(df.itertuples(index=False, name=None))

    try:
        cursor.executemany(insert_sql, records)
        conn.commit()
        logger.info(f"✅ {len(records)} filas cargadas en external_fight_stats")
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Error cargando fight_stats: {e}")
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
    
    # Asegura que el loader encuentre las tablas en el esquema `public`.
    # En Supabase, el search_path puede no incluir `public` dependiendo del rol.
    with conn.cursor() as cur:
        cur.execute("SET search_path TO public;")
    conn.commit()
    
    try:
        # IMPORTANTE: asumimos que las tablas ya existen en Supabase.
        # NO tocamos el esquema de la base de datos, solo hacemos snapshot de los CSV.

        if df_results is not None:
            load_fight_results(df_results, conn)
        else:
            logger.warning("⚠️  No se cargaron datos de fight_results (CSV no descargado)")

        if df_tott is not None:
            load_fighter_tott(df_tott, conn)
        else:
            logger.warning("⚠️  No se cargaron datos de fighter_tott (CSV no descargado)")

        if df_stats is not None:
            load_fight_stats(df_stats, conn)
        else:
            logger.warning("⚠️  No se cargaron datos de fight_stats (CSV no descargado)")
        
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

"""
Script simplificado para analizar la estructura de los CSVs.
Usa requests directamente sin pandas para evitar problemas de dependencias.
"""

import requests
import csv
from io import StringIO

CSV_URLS = {
    'fight_results': 'https://raw.githubusercontent.com/Greco1899/scrape_ufc_stats/main/ufc_fight_results.csv',
    'fight_stats': 'https://raw.githubusercontent.com/Greco1899/scrape_ufc_stats/main/ufc_fight_stats.csv',
    'fighter_tott': 'https://raw.githubusercontent.com/Greco1899/scrape_ufc_stats/main/ufc_fighter_tott.csv'
}


def analyze_csv(url, name):
    """Analiza un CSV y muestra su estructura"""
    print(f"\n{'='*70}")
    print(f"📊 Analizando: {name}")
    print(f"{'='*70}")
    
    try:
        print(f"🔗 Descargando desde: {url}")
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        # Leer CSV
        csv_content = response.text
        reader = csv.DictReader(StringIO(csv_content))
        
        # Obtener columnas
        columns = reader.fieldnames
        print(f"\n📋 Columnas encontradas ({len(columns)}):")
        for i, col in enumerate(columns, 1):
            print(f"   {i:2d}. {col}")
        
        # Leer primeras filas
        rows = list(reader)
        total_rows = len(rows)
        print(f"\n📊 Total de filas: {total_rows:,}")
        
        print(f"\n📝 Primeras 3 filas (muestra):")
        for i, row in enumerate(rows[:3], 1):
            print(f"\n   --- Fila {i} ---")
            for col in columns[:10]:  # Mostrar primeras 10 columnas
                value = row.get(col, '')
                if len(str(value)) > 50:
                    value = str(value)[:47] + "..."
                print(f"   {col}: {value}")
            if len(columns) > 10:
                print(f"   ... ({len(columns) - 10} columnas más)")
        
        # Analizar valores únicos en algunas columnas clave
        print(f"\n🔍 Análisis de datos:")
        
        # Buscar columnas con URLs
        url_cols = [col for col in columns if 'url' in col.lower() or 'link' in col.lower()]
        if url_cols:
            print(f"   🔗 Columnas con URLs: {url_cols}")
            for url_col in url_cols:
                sample_url = rows[0].get(url_col, '') if rows else ''
                if sample_url and 'fight-details' in sample_url:
                    fight_id = sample_url.split('/')[-1]
                    print(f"      Ejemplo ID de {url_col}: {fight_id}")
        
        # Buscar columnas con ROUND
        round_cols = [col for col in columns if 'round' in col.lower()]
        if round_cols:
            print(f"   🔄 Columnas con ROUND: {round_cols}")
            unique_rounds = set(row.get(round_cols[0], '') for row in rows[:100])
            print(f"      Valores únicos (primeros 100): {sorted(unique_rounds)}")
        
        # Buscar columnas con FIGHTER
        fighter_cols = [col for col in columns if 'fighter' in col.lower()]
        if fighter_cols:
            print(f"   👤 Columnas con FIGHTER: {fighter_cols}")
        
        # Buscar columnas con formato "X of Y"
        print(f"   📈 Columnas con formato 'X of Y' (primeras 5 filas):")
        for col in columns[:15]:  # Revisar primeras 15 columnas
            sample_values = [row.get(col, '') for row in rows[:5]]
            has_fraction = any(' of ' in str(v) for v in sample_values if v)
            if has_fraction:
                print(f"      {col}: {sample_values[0]}")
        
        return {
            'columns': columns,
            'total_rows': total_rows,
            'sample_rows': rows[:5]
        }
        
    except Exception as e:
        print(f"❌ Error analizando {name}: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Analiza todos los CSVs"""
    print("🔍 Analizando estructura de CSVs del repositorio externo...")
    print("   Esto puede tomar unos momentos...\n")
    
    results = {}
    
    for key, url in CSV_URLS.items():
        result = analyze_csv(url, key)
        results[key] = result
    
    # Resumen final
    print(f"\n{'='*70}")
    print("📝 RESUMEN FINAL")
    print(f"{'='*70}")
    
    for key, result in results.items():
        if result:
            print(f"\n✅ {key}:")
            print(f"   - Columnas: {len(result['columns'])}")
            print(f"   - Filas: {result['total_rows']:,}")
            print(f"   - Columnas: {', '.join(result['columns'][:10])}{'...' if len(result['columns']) > 10 else ''}")
        else:
            print(f"\n❌ {key}: Error al cargar")
    
    print("\n💡 Usa esta información para verificar el mapeo en el script de integración")
    print("   Revisa especialmente:")
    print("   - Nombres exactos de columnas")
    print("   - Formatos de datos (X of Y, porcentajes, tiempos)")
    print("   - Valores nulos o especiales (---, --, etc.)")


if __name__ == "__main__":
    main()

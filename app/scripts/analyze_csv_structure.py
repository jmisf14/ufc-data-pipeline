"""
Script para analizar la estructura de los CSVs antes de integrarlos.
Útil para entender qué columnas tienen y cómo mapearlas.
"""

import pandas as pd
import requests
from io import StringIO
import json

CSV_URLS = {
    'fight_results': 'https://raw.githubusercontent.com/Greco1899/scrape_ufc_stats/main/ufc_fight_results.csv',
    'fight_stats': 'https://raw.githubusercontent.com/Greco1899/scrape_ufc_stats/main/ufc_fight_stats.csv',
    'fighter_tott': 'https://raw.githubusercontent.com/Greco1899/scrape_ufc_stats/main/ufc_fighter_tott.csv'
}


def analyze_csv(url, name):
    """Analiza un CSV y muestra su estructura"""
    print(f"\n{'='*60}")
    print(f"Analizando: {name}")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text))
        
        print(f"\n📊 Dimensiones: {df.shape[0]} filas × {df.shape[1]} columnas")
        print(f"\n📋 Columnas ({len(df.columns)}):")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i}. {col}")
        
        print(f"\n📝 Primeras 3 filas:")
        print(df.head(3).to_string())
        
        print(f"\n🔍 Información de tipos:")
        print(df.dtypes)
        
        print(f"\n📈 Valores nulos por columna:")
        nulls = df.isnull().sum()
        for col, count in nulls.items():
            if count > 0:
                print(f"   {col}: {count} ({count/len(df)*100:.1f}%)")
        
        # Extraer IDs de URLs si existen
        url_cols = [col for col in df.columns if 'url' in col.lower() or 'link' in col.lower()]
        if url_cols:
            print(f"\n🔗 Columnas con URLs encontradas: {url_cols}")
            for url_col in url_cols:
                sample_url = df[url_col].dropna().iloc[0] if not df[url_col].dropna().empty else None
                if sample_url:
                    # Intentar extraer ID
                    if 'fight-details' in sample_url:
                        fight_id = sample_url.split('/')[-1]
                        print(f"   Ejemplo ID de {url_col}: {fight_id}")
        
        return df
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def main():
    """Analiza todos los CSVs"""
    print("🔍 Analizando estructura de CSVs del repositorio externo...")
    
    results = {}
    
    for key, url in CSV_URLS.items():
        df = analyze_csv(url, key)
        results[key] = df
    
    # Guardar resumen
    print(f"\n{'='*60}")
    print("📝 RESUMEN")
    print(f"{'='*60}")
    
    for key, df in results.items():
        if df is not None:
            print(f"\n✅ {key}: {df.shape[0]} filas, {len(df.columns)} columnas")
        else:
            print(f"\n❌ {key}: Error al cargar")
    
    print("\n💡 Usa esta información para ajustar el script de integración")


if __name__ == "__main__":
    main()

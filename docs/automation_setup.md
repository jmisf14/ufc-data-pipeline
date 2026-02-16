# Configuración de Automatización Semanal

## 🚀 Automatización Implementada

Se ha creado un workflow de GitHub Actions que carga automáticamente las tablas externas semanalmente en Supabase.

### Workflow: `.github/workflows/load_external_tables.yml`

**Características:**
- ✅ Ejecución automática cada lunes a las 21:00 UTC
- ✅ Ejecución manual disponible (workflow_dispatch)
- ✅ Independiente del pipeline de Scrapy
- ✅ Timeout de 30 minutos (suficiente para descargar y cargar CSVs)

### Horario de Ejecución

```
Pipeline de Scrapy:    Lunes 20:00 UTC
Tablas Externas:       Lunes 21:00 UTC (1 hora después)
```

Esto asegura que:
1. Primero se actualicen los datos del scraper principal
2. Luego se carguen las tablas complementarias externas

## 📋 Tablas que se Cargarán

1. **external_fight_results** - Resultados estructurados de peleas
2. **external_fighter_tott** - Tale of the Tape (peso y edad por pelea)
3. **external_fight_stats** - Estadísticas detalladas por round

## ⚙️ Configuración Requerida

### Secrets de GitHub

Asegúrate de que estos secrets estén configurados en tu repositorio:

1. Ve a: **Settings → Secrets and variables → Actions**
2. Verifica que existan estos secrets:
   - `SUPABASE_DB_HOST`
   - `SUPABASE_DB_PORT`
   - `SUPABASE_DB_NAME`
   - `SUPABASE_DB_USER`
   - `SUPABASE_DB_PASSWORD`

**Nota:** Estos son los mismos secrets que usa tu workflow de Scrapy, así que ya deberían estar configurados.

## 🔍 Verificación

### Verificar que el Workflow Funciona

1. **Ejecución Manual (Primera vez)**:
   - Ve a: **Actions → Load External UFC Tables to Supabase**
   - Click en **Run workflow**
   - Selecciona la rama (main/master)
   - Click en **Run workflow**

2. **Verificar Ejecución**:
   - Revisa los logs del workflow
   - Deberías ver mensajes como:
     ```
     ✅ Tabla external_fight_results creada/verificada
     ✅ Tabla external_fighter_tott creada/verificada
     ✅ Tabla external_fight_stats creada/verificada
     ✅ X registros cargados/actualizados
     ```

3. **Verificar en Supabase**:
   ```sql
   -- Verificar que las tablas existen y tienen datos
   SELECT 
       'external_fight_results' as tabla,
       COUNT(*) as registros
   FROM external_fight_results
   UNION ALL
   SELECT 
       'external_fighter_tott' as tabla,
       COUNT(*) as registros
   FROM external_fighter_tott
   UNION ALL
   SELECT 
       'external_fight_stats' as tabla,
       COUNT(*) as registros
   FROM external_fight_stats;
   ```

## 📅 Programación

### Cambiar el Horario

Si quieres cambiar cuándo se ejecuta, edita `.github/workflows/load_external_tables.yml`:

```yaml
schedule:
  # Formato cron: minuto hora día mes día-semana
  # Ejemplos:
  - cron: "0 21 * * 1"    # Lunes 21:00 UTC (actual)
  - cron: "0 12 * * 0"    # Domingo 12:00 UTC
  - cron: "0 0 * * *"     # Todos los días a medianoche UTC
```

### Ejecución Manual

Puedes ejecutar el workflow manualmente en cualquier momento:
1. Ve a **Actions**
2. Selecciona **Load External UFC Tables to Supabase**
3. Click en **Run workflow**

## 🔄 Proceso Automático

Cada semana, el workflow:

1. **Descarga los CSVs** desde GitHub:
   - `ufc_fight_results.csv`
   - `ufc_fight_stats.csv`
   - `ufc_fighter_tott.csv`

2. **Crea las tablas** si no existen:
   - Ejecuta los scripts SQL de creación
   - Crea índices para optimización

3. **Carga los datos**:
   - Parsea los datos correctamente
   - Usa `ON CONFLICT DO UPDATE` para evitar duplicados
   - Actualiza registros existentes

4. **Reporta el resultado**:
   - Muestra cuántos registros se cargaron
   - Indica si hubo errores

## 🛡️ Seguridad

- ✅ Usa secrets de GitHub (no expone credenciales)
- ✅ Conexión SSL requerida (`PGSSLMODE: require`)
- ✅ Timeout configurado (evita ejecuciones infinitas)
- ✅ Proceso idempotente (puede ejecutarse múltiples veces sin problemas)

## 📊 Monitoreo

### Ver Historial de Ejecuciones

1. Ve a **Actions** en GitHub
2. Selecciona **Load External UFC Tables to Supabase**
3. Verás todas las ejecuciones (automáticas y manuales)

### Logs de Ejecución

Cada ejecución muestra:
- ✅ Descarga de CSVs
- ✅ Creación/verificación de tablas
- ✅ Carga de datos
- ✅ Resumen final

## 🐛 Troubleshooting

### Error: "No se encontró create_*_table.sql"

**Solución:** Verifica que los archivos SQL estén en:
- `app/stat_scrape/stat_scrape/sql/`

El script busca automáticamente en múltiples rutas.

### Error: "Connection timeout"

**Solución:** 
- Verifica que los secrets de Supabase estén correctos
- Verifica que tu IP esté en la whitelist de Supabase (si aplica)
- El workflow tiene timeout de 30 minutos, debería ser suficiente

### Error: "No module named 'pandas'"

**Solución:** 
- Verifica que `requirements.txt` incluya `pandas==2.1.4`
- El workflow instala dependencias automáticamente

### Los datos no se actualizan

**Solución:**
- Verifica que el repositorio externo tenga datos actualizados
- Revisa los logs del workflow para ver errores
- Ejecuta manualmente para ver mensajes detallados

## ✅ Checklist de Configuración

- [ ] Secrets de GitHub configurados
- [ ] Workflow creado en `.github/workflows/load_external_tables.yml`
- [ ] Primera ejecución manual exitosa
- [ ] Tablas verificadas en Supabase
- [ ] Datos cargados correctamente
- [ ] Programación semanal activa

## 📝 Notas

- El workflow es **independiente** del pipeline de Scrapy
- No interfiere con las tablas existentes (`events`, `fights`, `fighters`)
- Las tablas externas se actualizan automáticamente cada semana
- Puedes ejecutar manualmente cuando necesites actualizaciones inmediatas

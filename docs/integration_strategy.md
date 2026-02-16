# Estrategia de Tablas Complementarias Externas

> ⚠️ **IMPORTANTE**: Estas tablas son **complementarias pero completamente separadas**. 
> NO interfieren con tu pipeline de Scrapy existente.

## Tablas a Integrar

Desde el repositorio [scrape_ufc_stats](https://github.com/Greco1899/scrape_ufc_stats):

1. **ufc_fight_results.csv** - Resultados estructurados de peleas
2. **ufc_fight_stats.csv** - Estadísticas detalladas de peleas  
3. **ufc_fighter_tott.csv** - Tale of the Tape (datos por pelea)

## Análisis de Datos

### 1. ufc_fight_results.csv
**Columnas identificadas:**
- EVENT, BOUT, OUTCOME, WEIGHTCLASS, METHOD, ROUND, TIME, TIME FORMAT, REFEREE, DETAILS, URL

**Relación con tabla existente `fights`:**
- ✅ Muchos datos ya están en `fights`
- ⚠️ Estructura diferente (más legible, menos normalizada)
- 💡 Útil para: validación, queries más simples, datos históricos completos

**Decisión:** Crear tabla `fight_results` como complemento

### 2. ufc_fight_stats.csv
**Análisis pendiente:**
- Necesita revisión de columnas específicas
- Probablemente similar a tu tabla `fights` existente
- Puede tener estadísticas adicionales o formato diferente

**Decisión:** Evaluar si necesita tabla separada o se integra en `fights`

### 3. ufc_fighter_tott.csv (Tale of the Tape)
**Datos únicos:**
- ⭐ **Peso por pelea** (varía entre peleas del mismo fighter)
- ⭐ **Edad al momento de la pelea** (más preciso que DOB)
- Estadísticas específicas de esa pelea

**Relación con tabla existente `fighters`:**
- `fighters` tiene datos generales del fighter
- `fighter_tott` tiene datos específicos por pelea
- Son complementarios, no duplicados

**Decisión:** Crear tabla `fighter_tott` (datos únicos y valiosos)

## Estrategia: Tablas Complementarias Separadas

### Principio: Separación Total

**Tablas completamente independientes con prefijo `external_`:**

1. **external_fight_results** → Tabla complementaria para datos estructurados de resultados
2. **external_fighter_tott** → Tabla complementaria para datos por pelea (peso, edad específica)
3. **external_fight_stats** → (Opcional, evaluar después)

### Características Clave:
- ✅ **Nombres diferentes**: Prefijo `external_` para claridad
- ✅ **Sin foreign keys**: No hay restricciones que puedan interferir
- ✅ **Proceso independiente**: Script separado, no parte del pipeline de Scrapy
- ✅ **Sin interferencia**: El pipeline de Scrapy nunca toca estas tablas

### Ventajas:
- ✅ No duplica datos existentes
- ✅ Mantiene estructura normalizada
- ✅ Permite queries más flexibles
- ✅ Datos históricos completos
- ✅ Relaciones claras con tablas existentes

### Arquitectura de Separación:

```
PIPELINE DE SCRAPY (Existente - NO TOCAR)
├── events
├── fights
└── fighters

TABLAS EXTERNAS (Nuevas - Independientes)
├── external_fight_results (complementa fights)
└── external_fighter_tott (complementa fighters)

RELACIONES: Solo mediante JOINs lógicos (sin foreign keys)
- external_fight_results.fight_id ←→ fights.id (JOIN)
- external_fighter_tott.fighter_id ←→ fighters.id (JOIN)
- external_fighter_tott.fight_id ←→ fights.id (JOIN)
```

## Implementación

### Paso 1: Crear Tablas (Automático)
Las tablas se crean automáticamente al ejecutar el script, pero puedes crearlas manualmente:
- `create_fight_results_table.sql` → Crea `external_fight_results`
- `create_fighter_tott_table.sql` → Crea `external_fighter_tott`

### Paso 2: Cargar Datos
Ejecutar script Python:
```bash
python app/scripts/integrate_external_tables.py
```

### Paso 3: Validar
- Verificar que no hay duplicados
- Confirmar relaciones entre tablas
- Revisar integridad de datos

## Uso de las Nuevas Tablas

### Ejemplo: Query con external_fight_results
```sql
-- Combinar datos de fights con external_fight_results (JOIN lógico)
SELECT 
    f.id,
    f.division,
    f.red_sig_strikes,
    f.blue_sig_strikes,
    efr.event_name,
    efr.bout,
    efr.outcome,
    efr.method
FROM fights f
LEFT JOIN external_fight_results efr ON f.id = efr.fight_id
WHERE efr.event_name LIKE '%UFC 325%';
```

### Ejemplo: Query con external_fighter_tott
```sql
-- Obtener peso y edad específicos de una pelea (JOIN lógico)
SELECT 
    f.first_name || ' ' || f.last_name as fighter_name,
    f.height as general_height,  -- De tabla fighters
    et.weight as weight_in_fight,  -- ⭐ De external_fighter_tott (específico de pelea)
    et.age as age_in_fight,        -- ⭐ De external_fighter_tott (específico de pelea)
    et.stance
FROM fighters f
JOIN external_fighter_tott et ON f.id = et.fighter_id
WHERE et.fight_id = 'fight_id_here';
```

## Mantenimiento

### Actualización Periódica
El script `integrate_external_tables.py` se ejecuta **INDEPENDIENTEMENTE**:
- ✅ Manualmente cuando necesites actualizar
- ✅ Automáticamente vía cron job
- ❌ **NO** como parte del pipeline de Scrapy (son procesos separados)

### Detección de Duplicados
El script usa `ON CONFLICT` para evitar duplicados:
- `fight_results`: único por `url`
- `fighter_tott`: único por `(fighter_id, fight_id)`

## Próximos Pasos

1. ✅ Ejecutar script de carga independiente: `python app/scripts/integrate_external_tables.py`
2. ⏳ Revisar estructura de `ufc_fight_stats.csv` (si decides cargarlo)
3. ⏳ Crear vistas SQL si es necesario para simplificar queries comunes
4. ⏳ Documentar relaciones lógicas en diagrama ER (sin foreign keys)

## ⚠️ Recordatorio Importante

- **NO modifiques** las tablas del pipeline de Scrapy (`events`, `fights`, `fighters`)
- **NO agregues foreign keys** entre tablas externas y existentes
- **SÍ puedes** hacer JOINs cuando necesites combinar datos
- **SÍ puedes** ejecutar el script independientemente cuando quieras

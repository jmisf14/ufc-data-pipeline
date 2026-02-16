# Estrategia de Tablas Complementarias Externas

## 🎯 Objetivo

Crear tablas **complementarias pero completamente separadas** que NO interfieran con tu pipeline de Scrapy existente.

## 📊 Arquitectura

### Tablas del Pipeline de Scrapy (EXISTENTES - NO TOCAR)
- `events` - Creada y mantenida por Scrapy
- `fights` - Creada y mantenida por Scrapy  
- `fighters` - Creada y mantenida por Scrapy

### Tablas Complementarias Externas (NUEVAS - INDEPENDIENTES)
- `external_fight_results` - Complementa `fights` (resultados estructurados)
- `external_fighter_tott` - Complementa `fighters` (peso y edad por pelea)
- `external_fight_stats` - Complementa `fights` (estadísticas por round)

## 🔑 Principios de Diseño

### ✅ Separación Total
- **Nombres diferentes**: Prefijo `external_` para claridad
- **Sin foreign keys**: No hay restricciones de integridad referencial
- **Proceso independiente**: Script separado, no parte del pipeline de Scrapy
- **Sin interferencia**: El pipeline de Scrapy nunca toca estas tablas

### ✅ Complementariedad
- **JOINs permitidos**: Puedes relacionar usando IDs comunes
- **Datos únicos**: Cada tabla aporta información diferente
- **Queries flexibles**: Combina datos cuando necesites

## 📋 Estructura de Tablas

### `external_fight_results`
**Propósito**: Resultados estructurados y legibles de peleas

**Relación con `fights`**:
- `external_fight_results.fight_id` puede hacer JOIN con `fights.id`
- **SIN foreign key** - relación lógica, no física

**Datos únicos**:
- Formato más legible (EVENT, BOUT, OUTCOME)
- Detalles estructurados (WEIGHTCLASS, METHOD, REFEREE)
- Historial completo desde repositorio externo

### `external_fighter_tott`
**Propósito**: Tale of the Tape - datos específicos por pelea

**Relación con `fighters`**:
- `external_fighter_tott.fighter_id` puede hacer JOIN con `fighters.id`
- `external_fighter_tott.fight_id` puede hacer JOIN con `fights.id`
- **SIN foreign keys** - relaciones lógicas

**Datos únicos**:
- ⭐ **Peso por pelea** (varía entre peleas del mismo fighter)
- ⭐ **Edad al momento de la pelea** (más preciso que DOB)
- Estadísticas específicas de esa pelea

### `external_fight_stats`
**Propósito**: Estadísticas detalladas POR ROUND de cada fighter

**Relación con `fights`**:
- Puede hacer JOIN usando `bout` o `event_name` + `fighter_name`
- **SIN foreign keys** - relaciones lógicas

**Datos únicos**:
- ⭐ **Estadísticas por round** (Round 1, 2, 3, etc.) - NO en tabla `fights`
- ⭐ **Estadísticas por fighter individual** (no solo red/blue)
- ⭐ **Control time por round** (tiempo de control en cada round)
- ⭐ **Desglose detallado** de strikes por posición y distancia por round

## 🔄 Proceso de Carga

### Script Independiente
```bash
python app/scripts/integrate_external_tables.py
```

**Características**:
- ✅ Descarga CSVs desde GitHub
- ✅ Crea tablas si no existen
- ✅ Carga datos con detección de duplicados
- ✅ **NO modifica** tablas existentes (events, fights, fighters)
- ✅ **NO interfiere** con pipeline de Scrapy

### Ejecución
- **Manual**: Cuando necesites actualizar
- **Cron job**: Periódicamente (semanal, mensual)
- **Independiente**: No afecta el pipeline de Scrapy

## 💡 Ejemplos de Uso

### Query Complementaria Simple
```sql
-- Combinar datos de fights con external_fight_results
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
WHERE f.id = 'fight_id_here';
```

### Query con Tale of the Tape
```sql
-- Obtener peso y edad específicos de una pelea
SELECT 
    f.first_name || ' ' || f.last_name as fighter_name,
    f.height as general_height,
    f.reach as general_reach,
    et.weight as weight_in_fight,  -- ⭐ Peso específico de esta pelea
    et.age as age_in_fight,         -- ⭐ Edad específica de esta pelea
    et.stance
FROM fighters f
JOIN external_fighter_tott et ON f.id = et.fighter_id
WHERE et.fight_id = 'fight_id_here';
```

### Query Completa Complementaria
```sql
-- Combinar todas las fuentes de datos
SELECT 
    e.name as event_name,
    e.date as event_date,
    f.division,
    f.red_sig_strikes,
    f.blue_sig_strikes,
    efr.bout,
    efr.outcome,
    efr.method,
    et_red.weight as red_weight,
    et_blue.weight as blue_weight
FROM events e
JOIN fights f ON e.id = f.event_id
LEFT JOIN external_fight_results efr ON f.id = efr.fight_id
LEFT JOIN external_fighter_tott et_red ON f.red_id = et_red.fighter_id AND f.id = et_red.fight_id
LEFT JOIN external_fighter_tott et_blue ON f.blue_id = et_blue.fighter_id AND f.id = et_blue.fight_id
WHERE e.date >= '2024-01-01';
```

### Query con Estadísticas por Round
```sql
-- Ver estadísticas por round de una pelea específica
SELECT 
    efs.round_number,
    efs.fighter_name,
    efs.sig_str_landed,
    efs.sig_str_percentage,
    efs.control_time,
    efs.takedown_landed,
    efs.head_landed,
    efs.body_landed,
    efs.leg_landed
FROM external_fight_stats efs
WHERE efs.bout = 'Alexander Volkanovski vs. Diego Lopes'
ORDER BY efs.round_number, efs.fighter_name;
```

## 🛡️ Garantías de Separación

### El Pipeline de Scrapy:
- ✅ Solo toca: `events`, `fights`, `fighters`
- ✅ Nunca toca: `external_*` tables
- ✅ No se ve afectado por estas tablas

### Las Tablas Externas:
- ✅ Solo se cargan mediante script independiente
- ✅ No tienen foreign keys que puedan fallar
- ✅ No dependen de las tablas del pipeline
- ✅ Pueden existir independientemente

## 📝 Mantenimiento

### Actualización de Datos Externos
```bash
# Ejecutar cuando necesites actualizar
python app/scripts/integrate_external_tables.py
```

### Verificación
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
FROM external_fighter_tott;
```

## ⚠️ Importante

1. **NO modifiques** las tablas del pipeline de Scrapy
2. **NO agregues foreign keys** entre tablas externas y existentes
3. **NO ejecutes** el script de carga durante el pipeline de Scrapy
4. **SÍ puedes** hacer JOINs cuando necesites combinar datos
5. **SÍ puedes** ejecutar el script independientemente cuando quieras

## 🎯 Resultado Final

- ✅ Tablas complementarias funcionando
- ✅ Pipeline de Scrapy intacto y sin interferencias
- ✅ Datos únicos disponibles (peso por pelea, edad específica)
- ✅ Flexibilidad para combinar datos cuando necesites
- ✅ Separación clara y mantenible

# Tabla external_fight_stats

## 📊 Descripción

Tabla complementaria que almacena **estadísticas detalladas POR ROUND** de cada fighter en cada pelea.

### Diferencia con tabla `fights` existente:

- **`fights`**: Tiene totales de la pelea completa (red vs blue)
- **`external_fight_stats`**: Tiene estadísticas desglosadas por round y por fighter individual

## 🎯 Datos Únicos

Esta tabla proporciona información que NO está en tu tabla `fights`:

1. **Estadísticas por round** (Round 1, Round 2, Round 3, etc.)
2. **Estadísticas por fighter individual** (no solo red/blue)
3. **Control time por round** (tiempo de control en cada round)
4. **Desglose detallado** de strikes por posición (head, body, leg) por round
5. **Desglose por distancia** (distance, clinch, ground) por round

## 📋 Estructura

### Campos Principales:
- `event_name`, `bout` - Identificación del evento y pelea
- `round_number`, `round_label` - Round (1-5)
- `fighter_name` - Nombre del fighter
- `knockdowns` - Knockdowns en ese round
- `sig_str_landed`, `sig_str_attempted`, `sig_str_percentage` - Significant strikes
- `total_str_landed`, `total_str_attempted` - Total strikes
- `takedown_landed`, `takedown_attempted`, `takedown_percentage` - Takedowns
- `submission_attempts`, `reversals` - Submission attempts y reversals
- `control_time` - Tiempo de control (formato "M:SS")
- `head_landed`, `head_attempted` - Strikes a la cabeza
- `body_landed`, `body_attempted` - Strikes al cuerpo
- `leg_landed`, `leg_attempted` - Strikes a las piernas
- `distance_landed`, `distance_attempted` - Strikes a distancia
- `clinch_landed`, `clinch_attempted` - Strikes en clinch
- `ground_landed`, `ground_attempted` - Strikes en el suelo

## 🔗 Relaciones

### Con tabla `fights`:
- Puedes hacer JOIN usando `bout` o `event_name` + `fighter_name`
- **SIN foreign key** - relación lógica

### Con tabla `fighters`:
- Puedes hacer JOIN usando `fighter_name`
- **SIN foreign key** - relación lógica

## 💡 Ejemplos de Uso

### Ver estadísticas por round de una pelea
```sql
SELECT 
    round_number,
    fighter_name,
    sig_str_landed,
    sig_str_attempted,
    sig_str_percentage,
    control_time,
    takedown_landed,
    takedown_attempted
FROM external_fight_stats
WHERE bout = 'Mario Bautista vs. Vinicius Oliveira'
ORDER BY round_number, fighter_name;
```

### Comparar performance por round
```sql
SELECT 
    round_number,
    fighter_name,
    sig_str_landed,
    sig_str_percentage,
    control_time,
    head_landed,
    body_landed,
    leg_landed
FROM external_fight_stats
WHERE bout = 'Alexander Volkanovski vs. Diego Lopes'
ORDER BY round_number, fighter_name;
```

### Combinar con tabla fights
```sql
SELECT 
    f.id as fight_id,
    f.division,
    efs.round_number,
    efs.fighter_name,
    efs.sig_str_landed as round_sig_strikes,
    efs.control_time,
    f.red_sig_strikes as total_red_sig_strikes,
    f.blue_sig_strikes as total_blue_sig_strikes
FROM fights f
JOIN external_fight_stats efs ON f.id = (
    SELECT fight_id 
    FROM external_fight_results 
    WHERE bout = efs.bout 
    LIMIT 1
)
WHERE f.id = 'fight_id_here'
ORDER BY efs.round_number;
```

### Análisis de tendencias por round
```sql
-- Ver cómo cambia el performance de un fighter por round
SELECT 
    round_number,
    AVG(sig_str_landed) as avg_sig_strikes,
    AVG(sig_str_percentage) as avg_accuracy,
    AVG(CAST(control_time AS INTERVAL)) as avg_control_time
FROM external_fight_stats
WHERE fighter_name = 'Alexander Volkanovski'
GROUP BY round_number
ORDER BY round_number;
```

## ⚠️ Notas Importantes

1. **Formato de datos**:
   - `control_time` está en formato string "M:SS" o NULL
   - Los porcentajes están sin el símbolo %
   - Los valores "---" se convierten a NULL

2. **Unicidad**:
   - Un fighter solo puede tener un registro por round en cada pelea
   - Constraint: `UNIQUE(event_name, bout, round_number, fighter_name)`

3. **Relaciones**:
   - **NO tiene foreign keys** - relaciones solo mediante JOINs lógicos
   - **NO interfiere** con el pipeline de Scrapy

4. **Actualización**:
   - Se carga mediante script independiente
   - Usa `ON CONFLICT DO UPDATE` para actualizar registros existentes

## 🎯 Casos de Uso

- ✅ Análisis de performance por round
- ✅ Identificar en qué round un fighter es más efectivo
- ✅ Comparar estrategias entre rounds
- ✅ Análisis de fatiga (cómo cambia el performance en rounds posteriores)
- ✅ Análisis de control time por round
- ✅ Desglose detallado de strikes por posición y distancia

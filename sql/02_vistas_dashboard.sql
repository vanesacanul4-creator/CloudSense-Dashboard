-- ============================================================================
-- C.L.O.U.D. Sense · Vistas de solo lectura para el dashboard (BD de la app)
-- Ejecutar en la base `cloudsense` como usuario postgres:
--   sudo -u postgres psql -d cloudsense -f 02_vistas_dashboard.sql
-- No modifica ni borra datos de la app: solo crea el esquema `dash` con vistas.
-- Cada vista imita una hoja de Plantilla_CloudSense.xlsx.
-- Los ids llevan prefijo APP- para no chocar con los del Excel (T01, T02...).
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS dash;

-- Hoja "Tanques": uno por tanque registrado en la app (con su ubicación)
CREATE OR REPLACE VIEW dash.tanques AS
SELECT 'APP-' || lpad(t.id::text, 3, '0')                              AS id_tanque,
       CASE WHEN t.nominal_capacity_g > 100000 THEN 'estacionario' ELSE 'cilindro' END AS tipo,
       (t.nominal_capacity_g / 1000.0)::float8                         AS capacidad_kg,
       COALESCE(u.name, 'Sin cliente') || COALESCE(' · ' || t.alias, '') AS cliente,
       CASE WHEN t.nominal_capacity_g <= 45000  THEN 'Doméstico'
            WHEN t.nominal_capacity_g <= 150000 THEN 'Comercial'
            ELSE 'Industrial' END                                       AS tipo_cliente,
       COALESCE(NULLIF(a.label, ''), NULLIF(a.city, ''), 'Sin zona')    AS zona,
       COALESCE(NULLIF(a.state, ''), 'Yucatán')                         AS estado,
       COALESCE(NULLIF(a.city, ''), 'Tizimín')                          AS municipio,
       COALESCE(t.latitude,  a.lat)::float8                             AS latitud,
       COALESCE(t.longitude, a.lng)::float8                             AS longitud
FROM tanks t
LEFT JOIN users u          ON u.id = t.user_id
LEFT JOIN user_addresses a ON a.id = t.address_id
WHERE t.deleted_at IS NULL;

-- Hoja "Lecturas_Bascula": peso de gas y nivel por lectura (últimos 180 días)
CREATE OR REPLACE VIEW dash.lecturas_bascula AS
SELECT 'APP-' || lpad(t.id::text, 3, '0')                                   AS id_tanque,
       (sr.recorded_at AT TIME ZONE 'America/Merida')                        AS fecha_hora,
       (rp.gas_estimated_g / 1000.0)::float8                                 AS peso_kg,
       LEAST(GREATEST(100.0 * rp.gas_estimated_g / NULLIF(t.nominal_capacity_g, 0), 0), 100)::float8 AS nivel_pct
FROM reading_processing rp
JOIN sensor_readings sr ON sr.id = rp.sensor_reading_id
JOIN tanks t            ON t.id  = rp.tank_id
WHERE rp.is_current
  AND rp.gas_estimated_g IS NOT NULL
  AND t.deleted_at IS NULL
  AND sr.recorded_at >= now() - interval '180 days';

-- Hoja "Fugas": alertas de la app (los mapas de alertas salen de aquí)
CREATE OR REPLACE VIEW dash.fugas AS
SELECT al.id::text                                                           AS id_alerta,
       'APP-' || lpad(al.tank_id::text, 3, '0')                              AS id_tanque,
       (al.triggered_at AT TIME ZONE 'America/Merida')                       AS fecha_hora,
       sr.mq6_analog::float8                                                 AS nivel_mq6,
       NULL::float8                                                          AS caida_peso_pct,
       (EXTRACT(EPOCH FROM (COALESCE(al.resolved_at, al.attended_at, al.dismissed_at) - al.triggered_at)) / 60.0)::float8 AS duracion_min,
       NULL::float8                                                          AS kg_perdidos_estimados,
       (EXTRACT(EPOCH FROM (COALESCE(al.attended_at, al.resolved_at, al.dismissed_at) - al.triggered_at)) / 60.0)::float8 AS tiempo_respuesta_min,
       CASE WHEN al.attended_at IS NOT NULL OR al.resolved_at IS NOT NULL OR al.dismissed_at IS NOT NULL OR lower(al.status) IN ('resolved','dismissed','attended','closed','cerrada','resuelta') THEN 1 ELSE 0 END AS atendida,
       CASE WHEN lower(al.severity) IN ('low','leve','info','baja')                    THEN 'Leve'
            WHEN lower(al.severity) IN ('medium','media','warning','moderate','moderada') THEN 'Media'
            WHEN lower(al.severity) IN ('high','alta','critical','critica','crítica','severe') THEN 'Alta'
            ELSE 'Media' END                                                 AS gravedad,
       COALESCE(al.type, 'alerta')                                           AS origen
FROM alerts al
LEFT JOIN sensor_readings sr ON sr.id = al.source_reading_id
WHERE al.tank_id IS NOT NULL;

-- Hoja "Reabastecimientos": recargas detectadas por la app (consumption_records)
CREATE OR REPLACE VIEW dash.reabastecimientos AS
SELECT 'APP-R' || lpad(cr.id::text, 4, '0')                                  AS id_recarga,
       'APP-' || lpad(cr.tank_id::text, 3, '0')                              AS id_tanque,
       (cr.period_start AT TIME ZONE 'America/Merida')                       AS fecha,
       (GREATEST(cr.gas_end_g - cr.gas_start_g, 0) / 1000.0)::float8         AS kg_cargados,
       LEAST(100.0 * cr.gas_start_g / NULLIF(t.nominal_capacity_g, 0), 100)::float8 AS nivel_antes_pct,
       LEAST(100.0 * cr.gas_end_g   / NULLIF(t.nominal_capacity_g, 0), 100)::float8 AS nivel_despues_pct,
       NULL::float8                                                          AS precio_kg,
       NULL::float8                                                          AS monto,
       (EXTRACT(EPOCH FROM (cr.period_start - lag(cr.period_start) OVER (PARTITION BY cr.tank_id ORDER BY cr.period_start))) / 86400.0)::float8 AS dias_desde_ultima_recarga,
       NULL::text                                                            AS proveedor
FROM consumption_records cr
JOIN tanks t ON t.id = cr.tank_id
WHERE cr.refill_detected AND t.deleted_at IS NULL;

-- Permisos: el dashboard (dash_ro) solo puede LEER estas cuatro vistas
GRANT USAGE ON SCHEMA dash TO dash_ro;
GRANT SELECT ON dash.tanques, dash.lecturas_bascula, dash.fugas, dash.reabastecimientos TO dash_ro;

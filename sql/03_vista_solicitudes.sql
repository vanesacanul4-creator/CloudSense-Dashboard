-- ============================================================================
-- C.L.O.U.D. Sense · Vista de solicitudes de gas para el dashboard
-- Ejecutar en la base `cloudsense` (como postgres):
--   sudo -u postgres psql -d cloudsense -f 03_vista_solicitudes.sql
-- Solo lee delivery_requests; no modifica ninguna tabla de la app.
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS dash;

CREATE OR REPLACE VIEW dash.solicitudes AS
SELECT 'SOL-' || lpad(d.id::text, 3, '0')                                   AS id_solicitud,
       'APP-' || lpad(d.tank_id::text, 3, '0')                              AS id_tanque,
       COALESCE(u.name, 'Sin cliente') || COALESCE(' · ' || t.alias, '')    AS cliente,
       CASE WHEN d.status IN ('requested', 'received')                               THEN 'Pendiente'
            WHEN d.status IN ('accepted', 'scheduled', 'assigned', 'en_route')       THEN 'En proceso'
            WHEN d.status IN ('delivered', 'completed')                              THEN 'Entregada'
            ELSE 'Cancelada' END                                            AS estado,
       d.status::text                                                       AS estado_app,
       (d.requested_at AT TIME ZONE 'America/Merida')                       AS fecha_solicitud,
       (d.updated_at   AT TIME ZONE 'America/Merida')                       AS fecha_actualizacion,
       CASE WHEN d.status IN ('delivered', 'completed')
            THEN (EXTRACT(EPOCH FROM (d.updated_at - d.requested_at)) / 3600.0)::float8 END AS horas_entrega,
       d.percent_snapshot::float8                                           AS nivel_pct,
       (d.gas_snapshot_g / 1000.0)::float8                                  AS gas_kg,
       d.delivery_address_text                                              AS direccion,
       COALESCE(NULLIF(a.label, ''), NULLIF(a.city, ''), 'Sin zona')        AS zona,
       COALESCE(d.delivery_lat, t.latitude,  a.lat)::float8                 AS latitud,
       COALESCE(d.delivery_lng, t.longitude, a.lng)::float8                 AS longitud,
       d.provider_id                                                        AS id_proveedor,
       d.cancel_reason                                                      AS motivo_cancelacion
FROM delivery_requests d
JOIN tanks t               ON t.id = d.tank_id
LEFT JOIN users u          ON u.id = d.user_id
LEFT JOIN user_addresses a ON a.id = t.address_id
WHERE t.deleted_at IS NULL;

GRANT USAGE ON SCHEMA dash TO dash_ro;
GRANT SELECT ON dash.solicitudes TO dash_ro;

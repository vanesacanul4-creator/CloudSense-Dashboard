"""Exporta el data warehouse (PostgreSQL local) a data/lecturas_dw.csv para el dashboard.
Uso:  pip install psycopg2-binary pandas   y luego   python exportar_dw.py"""
import pandas as pd, psycopg2
Q = """SELECT f.fecha_hora, f.mq2, f.mq3, f.mq5, f.mq6, f.mq7, f.mq8, f.mq135,
       c.clase, h.turno, m.anio_mes, m.nombre_mes, m.trimestre, s.anio, s.nombre_semestre
FROM fact_lectura_sensor f
JOIN dim_clase_gas c ON c.clase_key=f.clase_key
JOIN dim_hora h ON h.hora_key=f.hora_key
JOIN dim_fecha d ON d.fecha_key=f.fecha_key
JOIN dim_mes m ON m.mes_key=d.mes_key
JOIN dim_semestre s ON s.semestre_key=m.semestre_key"""
con = psycopg2.connect(host="localhost", dbname="dw_cloud_sense", user="dw_user", password=input("Contraseña de dw_user: "))
df = pd.read_sql(Q, con); df.to_csv("data/lecturas_dw.csv", index=False); print(len(df), "filas exportadas")

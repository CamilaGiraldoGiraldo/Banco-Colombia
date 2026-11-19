# Simulación de cajas – Banco de Colombia (M/M/1)

Simulación de eventos discretos de un día de operación (8 h) de un banco con tres cajas, para decidir
si se necesita una cuarta caja y cuántas cajas dedicar a retiros y a pagos.

## Contenido
| Archivo | Descripción |
|---|---|
| `simulacion_banco.py` | Código comentado: generación de usuarios, cajas M/M/1, réplicas y estadísticas |
| `requirements.txt` | Dependencias (numpy, pandas, scipy, matplotlib) |
| `resultados/` | CSV con los resultados de cada punto del enunciado |
| Informe (documento entregado) | Introducción, metodología, resultados y conclusiones |

## Ejecución
```bash
pip install -r requirements.txt
python simulacion_banco.py
```
Genera en `resultados/`:
- `p1_tiempos_por_cajero.csv` – cajero con menor y mayor tiempo promedio
- `p3_usuarios_por_tipo_y_replica.csv` – usuarios por tipo en cada réplica (y promedio)
- `p4_p5_comparacion_escenarios.csv` – A (3 mixtas), B (1R+2P), C (2R+1P), D (4 mixtas)
- `verificacion_200_replicas.csv` – verificación con 200 réplicas (IC 95 %, P90, espera máxima)
- `prueba_pareada_B_vs_C.csv` – prueba t pareada entre las configuraciones B y C
- `grafico_wq_10_replicas.png` y `grafico_wq_200_replicas.png` – espera por escenario con IC 95 %

## Modelo
- Acción: retiro 70 % / pago 30 %; tipo de usuario con las probabilidades de la Tabla 2 (condicionales a la acción).
- Tiempo entre llegadas y de servicio: exponenciales con las medias de la Tabla 1 según el tipo.
- Cada caja es un M/M/1 independiente con fila FIFO; el usuario se asigna al azar entre las cajas habilitadas.
- Mejora: escenarios extra con política "fila más corta" (A2, C2) y "fila única" (A3, M/M/3).
- Semillas fijas: los resultados son reproducibles. Los 4 escenarios usan los mismos usuarios en cada réplica.

## Resultados principales (10 réplicas)
- Menor tiempo en el sistema: caja 2 (5,83 min); mayor: caja 1 (6,47 min).
- ≈ 191 usuarios/día (69 % retiros, 31 % pagos). Réplicas con menos usuarios: 7 y 9 (175).
- Nueva caja: no indispensable (Wq 3,06 → 2,09 min con 4 cajas; utilización 41 %).
- Cajas exclusivas: 2 de retiros + 1 de pagos (Wq global 3,83 min vs 4,64 de 1R+2P).
- Réplicas: el piloto de 10 da IC95 % ±0,64 min; para ±0,5 min bastan 13 réplicas (aprox. normal).
- Mejora: con fila única, 3 cajas dan Wq = 0,43 min, mejor que 4 cajas con asignación aleatoria (2,07 min).
- B vs C (prueba pareada, 200 réplicas): diferencia 1,65 min ±0,43, p < 0,001 a favor de C.
# Guion del video de sustentación (≈ 6–7 min)

**0:00 – Problema (45 s).** El banco tiene 3 cajas, sin cajeros electrónicos. 70 % retiros, 30 % pagos, cuatro tipos de usuario.
Decisión: ¿cuarta caja? ¿1 de retiros + 2 de pagos o 2 de retiros + 1 de pagos?

**0:45 – Modelo (1 min 30 s).** Mostrar `simulacion_banco.py`: tablas de parámetros, `generar_usuarios` (acción, tipo, llegadas
y servicio exponenciales) y `simular_cajas` (M/M/1 independientes, fila FIFO, asignación aleatoria entre cajas habilitadas).
Supuestos: probabilidades condicionales a la acción, día que inicia vacío, 480 min.

**2:15 – Réplicas (45 s).** Piloto de 10 réplicas: Wq = 3,06 min, s = 0,89, IC95 % ±0,55. Con e = 0,5 min se requieren 13
réplicas; se usaron 10 (requisito del enunciado) y se verificó con 200.

**3:00 – Resultados (2 min 30 s).** Ejecutar el script en vivo.
1. Caja 2 menor (5,83 min), caja 1 mayor (6,47 min).
2. Promedios por tipo: ≈ 191 usuarios/día; retiro normal es el más frecuente (53,4).
3. Tabla por réplica; réplicas 7 y 9 con 175 usuarios.
4. Cuarta caja: Wq 3,06 → 2,09 min, pero la espera máxima (~28 min) no cambia → no es indispensable.
5. Exclusivas: 2R+1P (Wq 3,83) mejor que 1R+2P (4,64); aun así, las 3 mixtas (3,06) son lo más eficiente.

**5:30 – Conclusiones y limitaciones (1 min).** Recomendación, supuestos (asignación aleatoria; fila más corta
mejoraría) y trabajo futuro (llegadas por franja horaria, costos de personal).

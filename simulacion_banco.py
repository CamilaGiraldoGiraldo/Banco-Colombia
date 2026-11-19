"""
Simulación de las cajas del Banco de Colombia (modelos M/M/1 independientes).

Simula un día de 8 horas (480 min) con N réplicas y compara escenarios:
  A: 3 mixtas | B: 1 retiros + 2 pagos | C: 2 retiros + 1 pago | D: 4 mixtas   (asignación aleatoria, M/M/1)
  A2: 3 mixtas con "fila más corta" | A3: 3 mixtas con fila única | C2: 2R + 1P con "fila más corta"

Uso:   python simulacion_banco.py            (10 réplicas; genera CSV y gráficos en ./resultados)
Requiere: numpy, pandas, scipy, matplotlib
"""
import os
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

T = 480.0          # duración de la jornada (minutos)
REPLICAS = 10      # réplicas del experimento principal
P_RETIRO = 0.70    # 70 % de los usuarios hace retiros

# (acción, tipo, media de servicio, media entre llegadas, prob. condicional a la acción)  -> Tablas 1 y 2
TIPOS = [
    ("Retiro", "Rápido",    1, 1, .23), ("Retiro", "Normal",    2, 2, .40),
    ("Retiro", "Lento",     3, 3, .17), ("Retiro", "Muy lento", 4, 3, .20),
    ("Pago",   "Rápido",    3, 1, .10), ("Pago",   "Normal",    3, 2, .20),
    ("Pago",   "Lento",     5, 3, .30), ("Pago",   "Muy lento", 7, 4, .40),
]
# nombre: (cajas, política). M = mixta, R = solo retiros, P = solo pagos.
# Políticas: "aleatoria" (M/M/1 independientes, la del enunciado), "fila_corta" (va a la caja con menos
# usuarios), "fila_unica" (una sola fila; atiende la primera caja libre -> M/M/c).
ESCENARIOS = {
    "A: 3 mixtas": (list("MMM"), "aleatoria"),
    "B: 1 retiros + 2 pagos": (list("RPP"), "aleatoria"),
    "C: 2 retiros + 1 pago": (list("RRP"), "aleatoria"),
    "D: 4 mixtas": (list("MMMM"), "aleatoria"),
    "A2: 3 mixtas, fila más corta": (list("MMM"), "fila_corta"),
    "A3: 3 mixtas, fila única": (list("MMM"), "fila_unica"),
    "C2: 2R + 1P, fila más corta": (list("RRP"), "fila_corta"),
}


def generar_usuarios(rng: np.random.Generator) -> list:
    """Genera las llegadas del día: (instante, tipo, acción, tiempo de servicio)."""
    t, usuarios = 0.0, []
    while True:
        accion = 0 if rng.random() < P_RETIRO else 1               # 0 = retiro, 1 = pago
        probs = [x[4] for x in TIPOS[accion * 4: accion * 4 + 4]]
        k = accion * 4 + rng.choice(4, p=probs)                     # tipo de usuario
        t += rng.exponential(TIPOS[k][3])                           # tiempo entre llegadas
        if t > T:
            break
        usuarios.append((t, k, accion, rng.exponential(TIPOS[k][2])))  # tiempo de servicio
    return usuarios


def simular_cajas(usuarios: list, cajas: list, politica: str, rng: np.random.Generator) -> pd.DataFrame:
    """Cada caja atiende en orden de llegada (FIFO). La política decide a qué caja va cada usuario
    entre las habilitadas para su operación. Devuelve un DataFrame con una fila por usuario."""
    libre = [0.0] * len(cajas)                  # instante en que cada caja queda libre
    salidas = [[] for _ in cajas]               # instantes de salida de los usuarios de cada caja
    filas = []
    for t, k, a, s in usuarios:
        hab = [i for i, c in enumerate(cajas) if c == "M" or (c == "R" and a == 0) or (c == "P" and a == 1)]
        if politica == "aleatoria":             # reparto uniforme: cada caja es un M/M/1 independiente
            i = hab[rng.integers(len(hab))]
        elif politica == "fila_corta":          # caja con menos usuarios presentes (desempate al azar)
            carga = {j: sum(1 for d in salidas[j] if d > t) for j in hab}
            menor = min(carga.values())
            empate = [j for j in hab if carga[j] == menor]
            i = empate[rng.integers(len(empate))]
        else:                                   # fila única: la caja que se desocupa primero
            i = min(hab, key=lambda j: libre[j])
        inicio = max(t, libre[i])
        libre[i] = inicio + s
        salidas[i].append(libre[i])
        filas.append((i + 1, k, a, inicio - t, inicio + s - t, s))
    return pd.DataFrame(filas, columns=["caja", "tipo", "accion", "espera", "sistema", "servicio"])


def experimento(n_rep: int, semilla_llegadas: int = 100,
                semilla_asignacion: int = 5000) -> tuple[pd.DataFrame, np.ndarray]:
    """Corre n_rep réplicas; en cada una todos los escenarios usan los mismos usuarios."""
    datos, conteos = [], []
    for r in range(n_rep):
        usuarios = generar_usuarios(np.random.default_rng(semilla_llegadas + r))
        conteos.append(np.bincount([u[1] for u in usuarios], minlength=8))
        for nombre, (cajas, politica) in ESCENARIOS.items():
            df = simular_cajas(usuarios, cajas, politica, np.random.default_rng(semilla_asignacion + r))
            df["replica"], df["escenario"], df["n_cajas"] = r + 1, nombre, len(cajas)
            datos.append(df)
    return pd.concat(datos, ignore_index=True), np.array(conteos)


def resumen_escenarios(df: pd.DataFrame) -> pd.DataFrame:
    """Indicadores por réplica: W, Wq, Lq, utilización, esperas por acción, P90 y espera máxima."""
    filas = []
    for (esc, rep), g in df.groupby(["escenario", "replica"]):
        n = g["n_cajas"].iloc[0]
        filas.append(dict(escenario=esc, replica=rep, W=g.sistema.mean(), Wq=g.espera.mean(),
                          Lq=g.espera.sum() / T, utilizacion=g.servicio.sum() / (T * n),
                          Wq_retiros=g[g.accion == 0].espera.mean(), Wq_pagos=g[g.accion == 1].espera.mean(),
                          W_retiros=g[g.accion == 0].sistema.mean(), W_pagos=g[g.accion == 1].sistema.mean(),
                          P90_espera=g.espera.quantile(0.9), espera_max=g.espera.max()))
    return pd.DataFrame(filas)


def media_ic(x, conf=0.95):
    """Media e intervalo de confianza (t de Student) entre réplicas."""
    x = np.asarray(x, float)
    h = stats.t.ppf((1 + conf) / 2, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))
    return x.mean(), h


def replicas_necesarias(wq_piloto, error=0.5, z=1.96):
    """n = (z*s/e)^2 con la desviación estándar de la corrida piloto; e = semiancho deseado (min)."""
    s = np.std(wq_piloto, ddof=1)
    return int(np.ceil((z * s / error) ** 2)), s


def grafico_wq(res: pd.DataFrame, ruta: str, titulo: str):
    """Barras de Wq (retiros, pagos y global) por escenario, con IC 95 %."""
    esc = list(ESCENARIOS)
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ancho = 0.26
    for j, (col, nombre) in enumerate([("Wq_retiros", "Retiros"), ("Wq_pagos", "Pagos"), ("Wq", "Global")]):
        m, h = zip(*[media_ic(res[res.escenario == e][col]) for e in esc])
        ax.bar(np.arange(len(esc)) + (j - 1) * ancho, m, ancho, yerr=h, capsize=3, label=nombre)
    ax.set_xticks(range(len(esc)))
    ax.set_xticklabels([e.replace(", ", ",\n").replace(": ", ":\n") for e in esc], fontsize=8)
    ax.set_ylabel("Espera en fila Wq (min)")
    ax.set_title(titulo)
    ax.legend()
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs("resultados", exist_ok=True)
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)
    df, conteos = experimento(REPLICAS)

    # Punto 1: tiempo promedio por cajero (escenario A, sin segregar usuarios)
    a = df[df.escenario == "A: 3 mixtas"]
    caja = a.groupby(["replica", "caja"])[["sistema", "espera", "servicio"]].mean().groupby("caja").mean()
    caja["usuarios_dia"] = a.groupby(["replica", "caja"]).size().groupby("caja").mean()
    caja.round(2).to_csv("resultados/p1_tiempos_por_cajero.csv")
    print("\n[1] Tiempos promedio por cajero (min)\n", caja.round(2))
    print("   Menor tiempo en el sistema: caja", caja.sistema.idxmin(), "| Mayor: caja", caja.sistema.idxmax())

    # Puntos 2 y 3: usuarios por tipo
    nombres = [f"{t[0]}-{t[1]}" for t in TIPOS]
    por_rep = pd.DataFrame(conteos, columns=nombres, index=range(1, REPLICAS + 1))
    por_rep["Total"] = por_rep.sum(axis=1)
    por_rep.to_csv("resultados/p3_usuarios_por_tipo_y_replica.csv", index_label="replica")
    print("\n[2] Promedio de usuarios por tipo\n", por_rep.mean().round(1))
    print("\n[3] Usuarios por tipo en cada réplica\n", por_rep)
    print("   Réplica(s) con menos usuarios:", list(por_rep.index[por_rep.Total == por_rep.Total.min()]))

    # Puntos 4 y 5 + mejoras: comparación de escenarios con IC 95 %
    res = resumen_escenarios(df)
    comp = res.groupby("escenario").mean(numeric_only=True).drop(columns="replica").round(2)
    comp.to_csv("resultados/p4_p5_comparacion_escenarios.csv")
    print("\n[4-5] Comparación de escenarios (promedio de 10 réplicas)\n", comp[["W", "Wq", "Lq", "utilizacion",
          "Wq_retiros", "Wq_pagos", "P90_espera", "espera_max"]])
    grafico_wq(res, "resultados/grafico_wq_10_replicas.png", "Espera en fila por escenario (10 réplicas, IC 95 %)")

    # Número de réplicas: corrida piloto de 10
    wq = res[res.escenario == "A: 3 mixtas"].Wq.to_numpy(dtype=float)
    n_req, s = replicas_necesarias(wq)
    print(f"\n[Réplicas] Piloto n=10: Wq(A)={wq.mean():.2f}, s={s:.2f}, IC95%±{media_ic(wq)[1]:.2f}; "
          f"réplicas para ±0,5 min: {n_req}")

    # Verificación con 200 réplicas: medias, IC, percentil 90 y prueba pareada B vs C
    big, _ = experimento(200, 1000, 6000)
    r2 = resumen_escenarios(big)
    filas = []
    for e in ESCENARIOS:
        g = r2[r2.escenario == e]
        wq_m, wq_h = media_ic(g.Wq)
        filas.append(dict(escenario=e, W=g.W.mean(), Wq=wq_m, Wq_IC95=wq_h, Wq_retiros=g.Wq_retiros.mean(),
                          Wq_pagos=g.Wq_pagos.mean(), P90_espera=g.P90_espera.mean(), espera_max=g.espera_max.mean(),
                          utilizacion=g.utilizacion.mean()))
    t200 = pd.DataFrame(filas).set_index("escenario").round(2)
    t200.to_csv("resultados/verificacion_200_replicas.csv")
    print("\nVerificación con 200 réplicas\n", t200)
    grafico_wq(r2, "resultados/grafico_wq_200_replicas.png", "Espera en fila por escenario (200 réplicas, IC 95 %)")
    wq_b = r2[r2.escenario.str.startswith("B")].Wq.to_numpy(dtype=float)
    wq_c = r2[r2.escenario.str.startswith("C:")].Wq.to_numpy(dtype=float)
    dif = wq_b - wq_c
    m, h = media_ic(dif)
    t_est, p = stats.ttest_1samp(dif, 0)
    print(f"\nPrueba pareada Wq(B) - Wq(C): diferencia {m:.2f} min, IC95% ±{h:.2f}, p = {p:.2g}")
    pd.DataFrame([dict(diferencia_B_menos_C=m, IC95=h, p_valor=p)]).round(4).to_csv("resultados/prueba_pareada_B_vs_C.csv", index=False)
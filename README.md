# FoodRush · Lakehouse de pedidos a domicilio en Azure Databricks

![Azure Databricks](https://img.shields.io/badge/Azure%20Databricks-FF3621?logo=databricks&logoColor=white)
![Delta Lake](https://img.shields.io/badge/Delta%20Lake-00ADD4?logo=delta&logoColor=white)
![Unity Catalog](https://img.shields.io/badge/Unity%20Catalog-1B3139)
![PySpark](https://img.shields.io/badge/PySpark-E25A1C?logo=apachespark&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-4479A1?logo=databricks&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)

Pipeline de ingeniería de datos de extremo a extremo: ficheros sucios de una app de comida a domicilio se convierten en **tablas fiables y gobernadas**. Incluye arquitectura Medallion, cargas incrementales con `MERGE`, histórico SCD tipo 2, reglas de calidad con tabla de rechazos, permisos en Unity Catalog y orquestación con Lakeflow Jobs.

Es el proyecto final de la certificación **DP-750: Azure Databricks Data Engineer Associate**, dentro del Máster en Big Data e IA.

> Estado: 🚧 en desarrollo

## 1. Descripción

**FoodRush** es una app ficticia de comida a domicilio que conecta clientes, restaurantes y repartidores. Cada día recibe ficheros con los pedidos y los cambios de clientes, y esos datos llegan con errores: importes negativos, pedidos duplicados, clientes sin informar, fechas imposibles y estados mal escritos.

**Problema:** el equipo de negocio no se fía de los datos y no puede responder preguntas sencillas como qué restaurante factura más, quiénes son los mejores clientes o en qué zonas se tarda más en entregar.

**Solución:** un pipeline en Azure Databricks que ingiere los ficheros, los limpia y valida, mantiene el histórico con cargas incrementales y publica tres data marts gobernados en Unity Catalog. Todo el flujo está orquestado con Lakeflow Jobs.

**Resultado esperado:**
- Tablas fiables, sin duplicados.
- Los registros erróneos quedan apartados y explicados.
- Hay tres data marts listos para análisis.

## 2. Arquitectura

```text
 Ficheros CSV / JSON (carga_1, carga_2)
                │
                ▼
   Volumen UC: foodrush.bronze.landing
                │
                ▼
 ┌──────────────────────── Azure Databricks ────────────────────────┐
 │  BRONZE   pedidos_raw, clientes_raw, restaurantes_raw, ...       │
 │     │     (datos originales + fecha y fichero de carga)          │
 │     ▼                                                            │
 │  SILVER   pedidos  ── reglas de calidad ──► pedidos_rechazados   │
 │     │     clientes (SCD Tipo 2), restaurantes, repartidores      │
 │     ▼     MERGE INTO para cargas incrementales                   │
 │  GOLD     fact_pedidos + dim_cliente / dim_restaurante / ...     │
 │           mart_ventas_restaurante · mart_clientes · mart_entregas│
 └──────────────────────────────────────────────────────────────────┘
                │                          ▲
                ▼                          │
      Consultas / dashboard       Lakeflow Job (orquestación)
                                  Unity Catalog (permisos, máscaras, linaje)
```

<!-- TODO: sustituir por docs/arquitectura.png -->

## 3. Tecnologías

- Azure Databricks · Unity Catalog
- Delta Lake (`MERGE INTO`, historial de versiones, `OPTIMIZE`)
- PySpark y SQL
- Lakeflow Jobs
- Python + pytest (tests de las reglas de calidad)
- Git / GitHub

## 4. Instalación y configuración

### Requisitos
- Workspace de Azure Databricks Premium (o Databricks Free Edition).
- Permiso para crear catálogos en Unity Catalog. Si no lo tienes, usa un catálogo existente y pásalo en el parámetro `catalogo` de los notebooks.
- Cómputo serverless o un SQL warehouse.

### Pasos
0. **Clonar el repositorio:**
   ```powershell
   git clone https://github.com/Metrex29/foodrush-databricks-lakehouse.git
   ```
1. **Generar los datos de ejemplo** (opcional, ya vienen en `data/sample/`):
   ```powershell
   python scripts/generar_datos.py
   ```
2. **Crear el catálogo, los esquemas y el volumen:** ejecuta `sql/01_catalogo_y_esquemas.sql`.
3. **Subir los ficheros** de `data/sample/carga_1/` al volumen `/Volumes/foodrush/bronze/landing/carga_1/`. Haz lo mismo con `carga_2`.
4. **Ejecutar los notebooks** en orden. Para hacerlo automáticamente, crea el job descrito en `jobs/configuracion.md`.

### Tests locales
```powershell
pip install -r requirements.txt
python -m pytest -q
```

## 5. Datos y modelo

Los datos son **sintéticos**: los genera `scripts/generar_datos.py` con una semilla fija, así que salen siempre iguales. Los emails usan `example.com` y los teléfonos son ficticios.

| Fichero | Formato | Carga 1 | Carga 2 |
|---|---|---|---|
| restaurantes | CSV | 20 | — |
| repartidores | CSV | 25 | — |
| clientes | CSV | 150 | 20 nuevos + 12 que cambian de zona |
| pedidos | JSON Lines | 608 (8 duplicados) | 80 nuevos + 10 repetidos + 8 modificados |

**Errores introducidos a propósito** (≈2-3 %): importe negativo, `cliente_id` nulo, fecha de entrega anterior al pedido y estados mal escritos (`"ENTREGADO "`, `"En Reparto"`).

**Reglas de calidad** (`src/foodrush/calidad.py`):

| Regla | Condición |
|---|---|
| `importe_positivo` | `importe > 0` |
| `cliente_informado` | `cliente_id IS NOT NULL` |
| `entrega_posterior_al_pedido` | `fecha_entrega IS NULL OR fecha_entrega >= fecha_pedido` |
| `estado_valido` | estado en `entregado`, `cancelado`, `en_reparto` (tras normalizar) |

<!-- TODO: esquema de tablas silver y gold -->

## 6. Ejemplos de ejecución

<!-- TODO: capturas de cada fase, carga 1 vs carga 2, job y permisos -->

## 7. Conclusiones

<!-- TODO -->

---

## Estructura del repositorio

```text
foodrush-databricks-lakehouse/
├── README.md
├── docs/                 # Informe (proyecto.md → PDF), arquitectura y capturas
├── data/sample/          # Datos sintéticos: carga_1 y carga_2
├── scripts/              # Generador de datos
├── notebooks/            # Notebooks de Databricks (.py exportados)
├── sql/                  # Catálogo, seguridad y consultas
├── src/foodrush/         # Funciones reutilizables (calidad y limpieza)
├── tests/                # Tests con pytest
├── jobs/                 # Configuración del Lakeflow Job
├── presentation/         # PowerPoint de la exposición
└── requirements.txt
```

## Bloques DP-750 implementados

| Bloque | Qué se demuestra | Estado |
|---|---|---|
| A · Entorno y Unity Catalog | Catálogo `foodrush`, esquemas por capa, volumen, convención de nombres | 🟡 |
| B · Seguridad y gobierno | `GRANT` por grupo, máscara de columna en el teléfono, comentarios, linaje | ⬜ |
| C · Ingesta y transformación | CSV/JSON → Delta, nulos, duplicados, joins y columnas derivadas | ⬜ |
| D · Delta e incremental | `MERGE INTO` de la carga 2, SCD Tipo 2 en clientes, modelo estrella | ⬜ |
| E · Calidad | 4 reglas, tabla de rechazados con motivo y métricas | 🟡 |
| F · Orquestación | Lakeflow Job con dependencias, ejecución completa y un fallo controlado | ⬜ |
| G · Optimización | Consulta antes/después de `OPTIMIZE` y clustering | ⬜ |
| H · SDLC | Git, código reutilizable en `src/`, tests con pytest | 🟡 |

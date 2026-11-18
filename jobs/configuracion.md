# Lakeflow Job · `foodrush_pipeline_diario`

<!-- Se completará al crear el job en el workspace. -->

| Orden | Tarea | Notebook | Depende de |
|---|---|---|---|
| 1 | ingesta_bronze | `notebooks/01_ingesta_bronze` | — |
| 2 | limpieza_silver | `notebooks/02_silver_calidad` | 1 |
| 3 | incremental_merge | `notebooks/03_silver_merge_scd2` | 2 |
| 4 | publicar_gold | `notebooks/04_gold_marts` | 3 |
| 5 | validacion | `notebooks/05_validacion` | 4 |

**Parámetros:** `carga` (`carga_1` / `carga_2`), `catalogo` (por defecto `foodrush`).

**Cómputo:** serverless para jobs.

**Reintentos, programación y notificaciones:** pendiente.

"""
Reglas de calidad y limpieza de FoodRush.

Cada regla se define una sola vez y se usa de dos formas:
  - REGLAS_SQL: expresiones SQL que los notebooks aplican sobre DataFrames
    de Spark (F.expr) o en Lakeflow Declarative Pipelines (expectations).
  - Funciones Python puras: las mismas reglas sobre un diccionario, para
    poder probarlas con pytest sin necesidad de un clúster.
"""

from datetime import datetime

ESTADOS_VALIDOS = {"entregado", "cancelado", "en_reparto"}

# Nombre de la regla -> condición que debe cumplir un pedido válido
REGLAS_SQL = {
    "importe_positivo": "importe > 0",
    "cliente_informado": "cliente_id IS NOT NULL",
    "entrega_posterior_al_pedido": "fecha_entrega IS NULL OR fecha_entrega >= fecha_pedido",
    "estado_valido": "estado IN ('entregado', 'cancelado', 'en_reparto')",
}


def normalizar_estado(estado: str | None) -> str | None:
    """'  En Reparto ' -> 'en_reparto'. Devuelve None si viene vacío."""
    if estado is None:
        return None
    limpio = estado.strip().lower().replace(" ", "_")
    return limpio or None


def _fecha(valor: str | None) -> datetime | None:
    return datetime.fromisoformat(valor) if valor else None


def reglas_incumplidas(pedido: dict) -> list[str]:
    """Devuelve la lista de reglas que incumple un pedido (vacía si es válido).

    Se espera que el estado ya esté normalizado.
    """
    fallos = []
    importe = pedido.get("importe")
    if importe is None or importe <= 0:
        fallos.append("importe_positivo")
    if pedido.get("cliente_id") is None:
        fallos.append("cliente_informado")
    fp, fe = _fecha(pedido.get("fecha_pedido")), _fecha(pedido.get("fecha_entrega"))
    if fe is not None and fp is not None and fe < fp:
        fallos.append("entrega_posterior_al_pedido")
    if pedido.get("estado") not in ESTADOS_VALIDOS:
        fallos.append("estado_valido")
    return fallos


def separar_validos(pedidos: list[dict]) -> tuple[list[dict], list[dict]]:
    """Normaliza el estado y separa pedidos válidos de rechazados.

    Los rechazados llevan una columna 'motivos' con las reglas incumplidas.
    """
    validos, rechazados = [], []
    for p in pedidos:
        p = {**p, "estado": normalizar_estado(p.get("estado"))}
        fallos = reglas_incumplidas(p)
        if fallos:
            rechazados.append({**p, "motivos": fallos})
        else:
            validos.append(p)
    return validos, rechazados


def deduplicar(pedidos: list[dict], clave: str = "pedido_id") -> list[dict]:
    """Se queda con la última aparición de cada clave de negocio."""
    por_clave = {}
    for p in pedidos:
        por_clave[p[clave]] = p
    return list(por_clave.values())

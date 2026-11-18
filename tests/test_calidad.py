import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from foodrush.calidad import (  # noqa: E402
    deduplicar,
    normalizar_estado,
    reglas_incumplidas,
    separar_validos,
)

PEDIDO_OK = {
    "pedido_id": "P00001",
    "cliente_id": "C0001",
    "fecha_pedido": "2026-09-10T20:00:00",
    "fecha_entrega": "2026-09-10T20:35:00",
    "importe": 24.5,
    "estado": "entregado",
}


def test_pedido_correcto_no_incumple_reglas():
    assert reglas_incumplidas(PEDIDO_OK) == []


def test_importe_negativo_se_rechaza():
    assert "importe_positivo" in reglas_incumplidas({**PEDIDO_OK, "importe": -3})


def test_cliente_nulo_se_rechaza():
    assert "cliente_informado" in reglas_incumplidas({**PEDIDO_OK, "cliente_id": None})


def test_entrega_anterior_al_pedido_se_rechaza():
    p = {**PEDIDO_OK, "fecha_entrega": "2026-09-10T19:30:00"}
    assert "entrega_posterior_al_pedido" in reglas_incumplidas(p)


def test_pedido_sin_entregar_puede_no_tener_fecha_entrega():
    p = {**PEDIDO_OK, "estado": "en_reparto", "fecha_entrega": None}
    assert reglas_incumplidas(p) == []


def test_normalizar_estado():
    assert normalizar_estado("  En Reparto ") == "en_reparto"
    assert normalizar_estado("ENTREGADO ") == "entregado"
    assert normalizar_estado("   ") is None
    assert normalizar_estado(None) is None


def test_un_pedido_puede_incumplir_varias_reglas():
    p = {**PEDIDO_OK, "importe": 0, "cliente_id": None}
    assert set(reglas_incumplidas(p)) == {"importe_positivo", "cliente_informado"}


def test_deduplicar_se_queda_con_la_ultima_version():
    v1 = {**PEDIDO_OK, "estado": "en_reparto"}
    v2 = {**PEDIDO_OK, "estado": "entregado"}
    resultado = deduplicar([v1, v2])
    assert len(resultado) == 1
    assert resultado[0]["estado"] == "entregado"


def test_datos_de_ejemplo_contienen_rechazos():
    """Los datos sintéticos de la carga 1 deben producir rechazos de todos los tipos."""
    ruta = RAIZ / "data" / "sample" / "carga_1" / "pedidos.json"
    pedidos = [json.loads(linea) for linea in ruta.read_text(encoding="utf-8").splitlines()]
    validos, rechazados = separar_validos(deduplicar(pedidos))

    motivos = {m for r in rechazados for m in r["motivos"]}
    assert {"importe_positivo", "cliente_informado", "entrega_posterior_al_pedido"} <= motivos
    # Tras normalizar, ningún estado sucio debe llegar a rechazarse
    assert "estado_valido" not in motivos
    assert len(validos) + len(rechazados) == len({p["pedido_id"] for p in pedidos})

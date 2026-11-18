"""
Generador de datos sintéticos para FoodRush.

Crea dos cargas en data/sample/:
  - carga_1/: carga inicial (restaurantes, repartidores, clientes y pedidos).
  - carga_2/: carga incremental (pedidos nuevos, repetidos y modificados,
              clientes nuevos y clientes que cambian de zona).

Los datos incluyen errores introducidos a propósito para demostrar las
reglas de calidad: importes negativos, cliente nulo, pedidos duplicados,
fechas de entrega anteriores al pedido y estados mal escritos.

Uso:
    python scripts/generar_datos.py
"""

import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

SEMILLA = 750
random.seed(SEMILLA)

RAIZ = Path(__file__).resolve().parent.parent / "data" / "sample"

ZONAS = ["Centro", "Norte", "Sur", "Este", "Oeste", "Universidad"]
COCINAS = ["Italiana", "Japonesa", "Mexicana", "Hamburguesas", "India",
           "Mediterránea", "China", "Vegana", "Pizzería", "Tapas"]
NOMBRES_REST = ["Trattoria Bella", "Sushi Koi", "El Taco Loco", "Burger Rush",
                "Curry House", "Mar y Huerta", "Dragón Rojo", "Green Bowl",
                "Pizza Nostra", "La Tasca", "Ramen Ya", "Don Burrito",
                "Smash Bros Burger", "Tandoori Star", "Olivo", "Wok Express",
                "Veggie Lab", "Forno Napoli", "Bodega 33", "Poke Point"]
NOMBRES = ["Ana", "Luis", "Marta", "Javier", "Lucía", "Pablo", "Sara", "Diego",
           "Elena", "Hugo", "Carmen", "Álvaro", "Nerea", "Iván", "Paula", "Raúl",
           "Irene", "Sergio", "Laura", "Dani"]
APELLIDOS = ["García", "López", "Martín", "Sánchez", "Pérez", "Gómez", "Ruiz",
             "Díaz", "Moreno", "Muñoz", "Romero", "Navarro", "Torres", "Gil"]
VEHICULOS = ["Bici", "Moto", "Patinete"]
METODOS_PAGO = ["tarjeta", "efectivo", "bizum"]
ESTADOS = ["entregado"] * 8 + ["cancelado", "en_reparto"]
# Variantes mal escritas que la capa silver debe normalizar
ESTADOS_SUCIOS = ["Entregado", "ENTREGADO ", " cancelado", "En Reparto"]

INICIO = datetime(2026, 9, 1)


def escribir_csv(ruta: Path, filas: list[dict]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)


def escribir_jsonl(ruta: Path, filas: list[dict]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8") as f:
        for fila in filas:
            f.write(json.dumps(fila, ensure_ascii=False) + "\n")


def telefono_ficticio() -> str:
    # Prefijo 600 000 xxx: no corresponde a números reales asignados
    return f"600000{random.randint(100, 999)}"


def generar_restaurantes() -> list[dict]:
    return [
        {
            "restaurante_id": f"R{i:03d}",
            "nombre": nombre,
            "tipo_cocina": COCINAS[i % len(COCINAS)],
            "zona": random.choice(ZONAS),
            "valoracion": round(random.uniform(3.2, 4.9), 1),
        }
        for i, nombre in enumerate(NOMBRES_REST, start=1)
    ]


def generar_repartidores(n: int = 25) -> list[dict]:
    return [
        {
            "repartidor_id": f"D{i:03d}",
            "nombre": f"{random.choice(NOMBRES)} {random.choice(APELLIDOS)}",
            "vehiculo": random.choice(VEHICULOS),
            "zona": random.choice(ZONAS),
        }
        for i in range(1, n + 1)
    ]


def generar_clientes(desde: int, hasta: int) -> list[dict]:
    clientes = []
    for i in range(desde, hasta + 1):
        nombre = random.choice(NOMBRES)
        apellido = random.choice(APELLIDOS)
        clientes.append({
            "cliente_id": f"C{i:04d}",
            "nombre": f"{nombre} {apellido}",
            "email": f"cliente{i:04d}@example.com",
            "telefono": telefono_ficticio(),
            "zona": random.choice(ZONAS),
            "fecha_registro": (INICIO - timedelta(days=random.randint(1, 400))).date().isoformat(),
        })
    return clientes


def generar_pedido(num: int, clientes, restaurantes, repartidores, dia_max: int) -> dict:
    fecha = INICIO + timedelta(days=random.randint(0, dia_max),
                               hours=random.randint(12, 23),
                               minutes=random.randint(0, 59))
    estado = random.choice(ESTADOS)
    minutos = random.randint(15, 60)
    importe = round(random.uniform(8, 65), 2)
    return {
        "pedido_id": f"P{num:05d}",
        "cliente_id": random.choice(clientes)["cliente_id"],
        "restaurante_id": random.choice(restaurantes)["restaurante_id"],
        "repartidor_id": random.choice(repartidores)["repartidor_id"],
        "fecha_pedido": fecha.isoformat(timespec="seconds"),
        "fecha_entrega": (fecha + timedelta(minutes=minutos)).isoformat(timespec="seconds")
        if estado == "entregado" else None,
        "importe": importe,
        "propina": round(random.choice([0, 0, 0, 1, 1.5, 2, 3]), 2),
        "estado": estado,
        "metodo_pago": random.choice(METODOS_PAGO),
    }


def ensuciar(pedidos: list[dict], proporcion: float) -> dict:
    """Introduce errores controlados y devuelve cuántos de cada tipo."""
    n = max(1, int(len(pedidos) * proporcion))
    errores = {"importe_negativo": 0, "cliente_nulo": 0,
               "entrega_antes_pedido": 0, "estado_sucio": 0}

    for p in random.sample(pedidos, n):
        p["importe"] = -abs(p["importe"])
        errores["importe_negativo"] += 1
    for p in random.sample(pedidos, n):
        p["cliente_id"] = None
        errores["cliente_nulo"] += 1
    entregados = [p for p in pedidos if p["fecha_entrega"]]
    for p in random.sample(entregados, n):
        fp = datetime.fromisoformat(p["fecha_pedido"])
        p["fecha_entrega"] = (fp - timedelta(minutes=random.randint(5, 90))).isoformat(timespec="seconds")
        errores["entrega_antes_pedido"] += 1
    for p in random.sample(pedidos, n * 2):
        p["estado"] = random.choice(ESTADOS_SUCIOS)
        errores["estado_sucio"] += 1
    return errores


def main() -> None:
    restaurantes = generar_restaurantes()
    repartidores = generar_repartidores()

    # ---------- CARGA 1 ----------
    clientes_1 = generar_clientes(1, 150)
    pedidos_1 = [generar_pedido(i, clientes_1, restaurantes, repartidores, 45)
                 for i in range(1, 601)]
    errores_1 = ensuciar(pedidos_1, 0.02)
    # Duplicados exactos dentro de la misma carga
    duplicados_1 = [dict(p) for p in random.sample(pedidos_1, 8)]
    pedidos_1 += duplicados_1
    random.shuffle(pedidos_1)

    c1 = RAIZ / "carga_1"
    escribir_csv(c1 / "restaurantes.csv", restaurantes)
    escribir_csv(c1 / "repartidores.csv", repartidores)
    escribir_csv(c1 / "clientes.csv", clientes_1)
    escribir_jsonl(c1 / "pedidos.json", pedidos_1)

    # ---------- CARGA 2 ----------
    # Clientes: 20 nuevos + 12 que cambian de zona (para SCD2)
    clientes_nuevos = generar_clientes(151, 170)
    cambian = [dict(c) for c in random.sample(clientes_1, 12)]
    for c in cambian:
        c["zona"] = random.choice([z for z in ZONAS if z != c["zona"]])
    clientes_2 = cambian + clientes_nuevos

    todos_clientes = clientes_1 + clientes_nuevos
    validos_1 = [p for p in pedidos_1 if p["estado"] in ("en_reparto",)]
    # Pedidos que pasan de en_reparto a entregado
    modificados = []
    for p in validos_1[:8]:
        q = dict(p)
        fp = datetime.fromisoformat(q["fecha_pedido"])
        q["estado"] = "entregado"
        q["fecha_entrega"] = (fp + timedelta(minutes=random.randint(20, 50))).isoformat(timespec="seconds")
        modificados.append(q)
    # Pedidos repetidos sin cambios (ya llegaron en la carga 1)
    repetidos = [dict(p) for p in random.sample(
        [p for p in pedidos_1 if p["estado"] == "entregado"], 10)]
    nuevos = [generar_pedido(i, todos_clientes, restaurantes, repartidores, 60)
              for i in range(601, 681)]
    errores_2 = ensuciar(nuevos, 0.03)
    pedidos_2 = nuevos + repetidos + modificados
    random.shuffle(pedidos_2)

    c2 = RAIZ / "carga_2"
    escribir_csv(c2 / "clientes.csv", clientes_2)
    escribir_jsonl(c2 / "pedidos.json", pedidos_2)

    print("Carga 1:")
    print(f"  restaurantes={len(restaurantes)} repartidores={len(repartidores)} "
          f"clientes={len(clientes_1)} pedidos={len(pedidos_1)} (duplicados={len(duplicados_1)})")
    print(f"  errores introducidos: {errores_1}")
    print("Carga 2:")
    print(f"  clientes={len(clientes_2)} (nuevos={len(clientes_nuevos)}, cambian_zona={len(cambian)})")
    print(f"  pedidos={len(pedidos_2)} (nuevos={len(nuevos)}, repetidos={len(repetidos)}, "
          f"modificados={len(modificados)})")
    print(f"  errores introducidos: {errores_2}")


if __name__ == "__main__":
    main()

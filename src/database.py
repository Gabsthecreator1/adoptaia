import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

MASCOTAS_PATH = BASE_DIR / "data" / "mascotas" / "mascotas.json"


def cargar_mascotas():
    """Carga las mascotas disponibles desde el archivo JSON."""

    with open(MASCOTAS_PATH, "r", encoding="utf-8") as archivo:
        mascotas = json.load(archivo)

    return mascotas


if __name__ == "__main__":

    mascotas = cargar_mascotas()

    print("\n--- MASCOTAS DISPONIBLES ---\n")
    print(f"Total de mascotas: {len(mascotas)}")

    for mascota in mascotas:
        print(
            f"- {mascota['nombre']} | "
            f"{mascota['especie']} | "
            f"Energía: {mascota['energia']}"
        )
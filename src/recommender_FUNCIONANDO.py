from src.database import cargar_mascotas


def recomendar_mascotas(
    especie=None,
    energia=None,
    apto_departamento=None,
    convive_perros=None,
    convive_gatos=None,
    convive_ninos=None,
    tiempo_paseo=None,
):
    """
    Busca mascotas compatibles con las características
    y condiciones reales del hogar.

    IMPORTANTE:
    - Si en el hogar HAY perros, la mascota debe convivir con perros.
    - Si en el hogar HAY gatos, la mascota debe convivir con gatos.
    - Si en el hogar HAY niños, la mascota debe convivir con niños.
    - Si NO hay perros, gatos o niños, esa característica no restringe
      la recomendación.
    """

    mascotas = cargar_mascotas()
    resultados = []

    for mascota in mascotas:

        # -------------------------------------------------
        # ESPECIE
        # -------------------------------------------------

        if especie is not None:
            if mascota["especie"].lower() != especie.lower():
                continue

        # -------------------------------------------------
        # ENERGÍA
        # -------------------------------------------------

        if energia is not None:
            if mascota["energia"].lower() != energia.lower():
                continue

        # -------------------------------------------------
        # DEPARTAMENTO
        # -------------------------------------------------

        # Solo necesitamos exigir aptitud para departamento
        # cuando la persona realmente vive en departamento.
        if apto_departamento is True:
            if mascota["apto_departamento"] is not True:
                continue

        # -------------------------------------------------
        # CONVIVENCIA CON PERROS
        # -------------------------------------------------

        # Si HAY perros en casa, la mascota debe poder
        # convivir con perros.
        #
        # Si NO hay perros, no necesitamos filtrar este campo.
        if convive_perros is True:
            if mascota["convive_perros"] is not True:
                continue

        # -------------------------------------------------
        # CONVIVENCIA CON GATOS
        # -------------------------------------------------

        # Si HAY gatos en casa, la mascota debe poder
        # convivir con gatos.
        if convive_gatos is True:
            if mascota["convive_gatos"] is not True:
                continue

        # -------------------------------------------------
        # CONVIVENCIA CON NIÑOS
        # -------------------------------------------------

        # Si HAY niños en casa, la mascota debe poder
        # convivir con niños.
        if convive_ninos is True:
            if mascota["convive_ninos"] is not True:
                continue

        # -------------------------------------------------
        # TIEMPO DE PASEO
        # -------------------------------------------------

        # Actualmente mascotas.json no contiene un campo
        # específico de minutos de paseo.
        #
        # Por ahora utilizamos el nivel de energía como
        # aproximación responsable.
        #
        # Una disponibilidad menor a 30 minutos no es
        # recomendable para perros de energía alta.

        if (
            tiempo_paseo is not None
            and mascota["especie"].lower() == "perro"
        ):
            if tiempo_paseo < 30 and mascota["energia"].lower() == "alta":
                continue

        # -------------------------------------------------
        # MASCOTA COMPATIBLE
        # -------------------------------------------------

        resultados.append(mascota)

    return resultados


# =========================================================
# PRUEBA LOCAL
# =========================================================

if __name__ == "__main__":

    print("\n--- PRUEBA DEL RECOMENDADOR ---\n")

    resultados = recomendar_mascotas(
        especie="perro",
        energia="baja",
        apto_departamento=True,
        convive_perros=False,
        convive_gatos=True,
        convive_ninos=False,
        tiempo_paseo=60,
    )

    print(f"Mascotas encontradas: {len(resultados)}\n")

    for mascota in resultados:
        print(f"Nombre: {mascota['nombre']}")
        print(f"Especie: {mascota['especie']}")
        print(f"Edad: {mascota['edad']}")
        print(f"Energía: {mascota['energia']}")
        print(
            f"Apto departamento: "
            f"{mascota['apto_departamento']}"
        )
        print(
            f"Convive con gatos: "
            f"{mascota['convive_gatos']}"
        )
        print(f"Descripción: {mascota['descripcion']}")
        print("-" * 40)
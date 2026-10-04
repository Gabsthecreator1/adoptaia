import re
import streamlit as st

from src.agent import preparar_rag, responder_pregunta
from src.recommender import recomendar_mascotas


# ============================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================

st.set_page_config(
    page_title="AdoptaIA",
    page_icon="🐾",
    layout="centered",
)


# ============================================================
# FORMULARIO DE ADOPCIÓN
# ============================================================

FORMULARIO_ADOPCION = (
    "https://docs.google.com/forms/d/1Qn0jfzArUM6hcrw3n3Elz2TK6JhFq6Y4ukjcQmfWAl4/preview"
)


# ============================================================
# AUTENTICACIÓN SIMPLE
# ============================================================

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🐾 AdoptaIA")
    st.subheader("Acceso al sistema")

    with st.form("login_form"):
        usuario = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        ingresar = st.form_submit_button("Iniciar sesión")

    if ingresar:
        usuario_correcto = st.secrets["auth"]["usuario"]
        password_correcto = st.secrets["auth"]["password"]

        if usuario == usuario_correcto and password == password_correcto:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")

    st.stop()

# Botón de cierre de sesión para usuarios autenticados
if st.sidebar.button("Cerrar sesión"):
    st.session_state.autenticado = False
    st.session_state.pop("messages", None)
    st.session_state.pop("preferencias", None)
    st.rerun()


# ============================================================
# CARGAR RAG
# ============================================================

@st.cache_resource
def cargar_adoptaia():
    return preparar_rag()


vectorstore = cargar_adoptaia()


# ============================================================
# DETECTAR PREFERENCIAS
# ============================================================

def detectar_preferencias(texto):
    texto = texto.lower().strip()
    preferencias = {}

    # --------------------------------------------------------
    # ESPECIE QUE DESEA ADOPTAR
    # Evitamos confundir "tengo gatos" con "quiero adoptar gato".
    # --------------------------------------------------------
    especie_actual = st.session_state.preferencias.get("especie")

    patrones_perro = [
        "busco un perro", "busco perro", "quiero un perro", "quiero perro",
        "adoptar un perro", "adoptar perro", "prefiero un perro", "prefiero perro",
        "me interesa un perro", "me interesa perro", "una perrita", "un perrito",
    ]
    patrones_gato = [
        "busco un gato", "busco gato", "quiero un gato", "quiero gato",
        "adoptar un gato", "adoptar gato", "prefiero un gato", "prefiero gato",
        "me interesa un gato", "me interesa gato", "una gatita", "un gatito",
    ]

    if any(frase in texto for frase in patrones_perro):
        preferencias["especie"] = "perro"
    elif any(frase in texto for frase in patrones_gato):
        preferencias["especie"] = "gato"
    elif especie_actual is None:
        # Solo usamos menciones simples cuando todavía no sabemos qué busca.
        if any(p in texto for p in ["perro", "perrita", "perrito", "perra"]):
            preferencias["especie"] = "perro"
        elif any(p in texto for p in ["gato", "gata", "gatito", "gatita"]):
            preferencias["especie"] = "gato"

    # --------------------------------------------------------
    # ENERGÍA
    # --------------------------------------------------------
    if any(palabra in texto for palabra in [
        "tranquilo", "tranquila", "poca energía", "poca energia",
        "energía baja", "energia baja", "sedentario", "sedentaria",
        "energía bajo", "energia bajo",
    ]):
        preferencias["energia"] = "baja"
    elif any(palabra in texto for palabra in [
        "energía media", "energia media", "actividad media",
        "moderado", "moderada", "energía medio", "energia medio",
    ]):
        preferencias["energia"] = "media"
    elif any(palabra in texto for palabra in [
        "activo", "activa", "mucha energía", "mucha energia",
        "energía alta", "energia alta", "energía alto", "energia alto",
    ]):
        preferencias["energia"] = "alta"

    # --------------------------------------------------------
    # TIPO DE VIVIENDA
    # --------------------------------------------------------
    if any(palabra in texto for palabra in [
        "departamento", "depa", "espacio pequeño", "espacio reducido",
    ]):
        preferencias["apto_departamento"] = True
    elif any(palabra in texto for palabra in [
        "casa", "patio", "jardín", "jardin",
    ]):
        preferencias["apto_departamento"] = False

    # --------------------------------------------------------
    # CONVIVENCIA CON PERROS
    # Primero las negaciones para evitar falsos positivos.
    # --------------------------------------------------------
    if any(frase in texto for frase in [
        "no tengo perro", "no tengo perros", "sin perro", "sin perros",
        "ni perro", "ni perros", "no hay perro", "no hay perros",
    ]):
        preferencias["convive_perros"] = False
    elif any(frase in texto for frase in [
        "tengo perro", "tengo perros", "otro perro", "otros perros",
        "con perros", "hay perro", "hay perros",
    ]):
        preferencias["convive_perros"] = True

    # --------------------------------------------------------
    # CONVIVENCIA CON GATOS
    # --------------------------------------------------------
    if any(frase in texto for frase in [
        "no tengo gato", "no tengo gatos", "sin gato", "sin gatos",
        "ni gato", "ni gatos", "no hay gato", "no hay gatos",
    ]):
        preferencias["convive_gatos"] = False
    elif any(frase in texto for frase in [
        "tengo gato", "tengo gatos", "otro gato", "otros gatos",
        "con gatos", "hay gato", "hay gatos",
    ]):
        preferencias["convive_gatos"] = True

    # --------------------------------------------------------
    # CONVIVENCIA CON NIÑOS
    # --------------------------------------------------------
    if any(frase in texto for frase in [
        "no tengo niños", "no tengo hijos", "sin niños", "sin hijos",
        "no hay niños", "ni niños", "ni hijos", "no hay hijos",
    ]):
        preferencias["convive_ninos"] = False
    elif any(frase in texto for frase in [
        "tengo niños", "tengo hijos", "hay niños", "con niños", "con hijos",
    ]):
        preferencias["convive_ninos"] = True

    # --------------------------------------------------------
    # TIEMPO / DISPONIBILIDAD PARA PASEOS
    # Este dato completa el perfil, aunque el recomendador actual todavía
    # no lo usa como filtro directo.
    # --------------------------------------------------------
    menciona_paseo = any(p in texto for p in [
        "paseo", "pasear", "sacarlo", "sacarla", "caminar", "ejercicio",
        "hora", "horas", "minuto", "minutos", "tiempo", "veces al día",
        "veces al dia",
    ])

    if menciona_paseo:
        if any(frase in texto for frase in [
            "no tengo tiempo", "casi no tengo tiempo", "muy poco tiempo",
            "poco tiempo", "menos de 30 minutos", "menos de media hora",
        ]):
            preferencias["tiempo_paseos"] = "bajo"
        elif any(frase in texto for frase in [
            "mucho tiempo", "bastante tiempo", "dos horas", "2 horas",
            "tres horas", "3 horas", "más de una hora", "mas de una hora",
            "varias horas", "tres veces", "3 veces", "cuatro veces", "4 veces",
        ]):
            preferencias["tiempo_paseos"] = "alto"
        elif re.search(r"\b(1|una)\s*hora\b", texto):
            preferencias["tiempo_paseos"] = "medio"
        elif re.search(r"\b([3-9][0-9]|[1-9][0-9]{2,})\s*minutos?\b", texto):
            minutos = int(re.search(r"\b([3-9][0-9]|[1-9][0-9]{2,})\s*minutos?\b", texto).group(1))
            if minutos < 45:
                preferencias["tiempo_paseos"] = "bajo"
            elif minutos <= 90:
                preferencias["tiempo_paseos"] = "medio"
            else:
                preferencias["tiempo_paseos"] = "alto"
        elif any(frase in texto for frase in [
            "media hora", "30 minutos", "una vez", "1 vez",
        ]):
            preferencias["tiempo_paseos"] = "bajo"
        elif any(frase in texto for frase in [
            "dos veces", "2 veces", "tiempo suficiente", "tiempo moderado",
        ]):
            preferencias["tiempo_paseos"] = "medio"

    return preferencias


# ============================================================
# ACTUALIZAR MEMORIA DE PREFERENCIAS
# ============================================================

def actualizar_preferencias(nuevas_preferencias):
    for clave, valor in nuevas_preferencias.items():
        st.session_state.preferencias[clave] = valor


# ============================================================
# VERIFICAR DATOS FALTANTES
# ============================================================

def obtener_datos_faltantes():
    preferencias = st.session_state.preferencias
    faltantes = []

    for campo in [
        "especie",
        "energia",
        "apto_departamento",
        "convive_perros",
        "convive_gatos",
        "convive_ninos",
        "tiempo_paseos",
    ]:
        if preferencias.get(campo) is None:
            faltantes.append(campo)

    return faltantes


# ============================================================
# CREAR PREGUNTA PARA COMPLETAR PERFIL
# ============================================================

def crear_pregunta_faltante(faltantes):
    if "especie" in faltantes:
        return "Para ayudarte a encontrar una mascota compatible, ¿prefieres adoptar un perro o un gato?"

    if "energia" in faltantes:
        return "¿Qué nivel de energía buscas en la mascota: bajo, medio o alto?"

    if "apto_departamento" in faltantes:
        return "¿La mascota vivirá en un departamento o en una casa?"

    convivencia = []
    if "convive_perros" in faltantes:
        convivencia.append("perros")
    if "convive_gatos" in faltantes:
        convivencia.append("gatos")
    if "convive_ninos" in faltantes:
        convivencia.append("niños")

    if convivencia:
        texto = ", ".join(convivencia)
        return (
            "Para completar el perfil, necesito saber un poco más sobre su futuro hogar. "
            f"¿La mascota convivirá con {texto}? "
            "Puedes indicarme cuáles sí y cuáles no."
        )

    if "tiempo_paseos" in faltantes:
        return (
            "Ya casi terminamos el perfil. ¿Cuánto tiempo puedes dedicar diariamente "
            "a los paseos o actividad de la mascota? Por ejemplo: 30 minutos, "
            "1 hora o 2 horas al día."
        )

    return None


# ============================================================
# OBTENER RECOMENDACIONES
# ============================================================

def obtener_recomendaciones():
    p = st.session_state.preferencias

    # El perfil guarda el tiempo de paseo como bajo/medio/alto.
    # El recomendador trabaja con minutos, así que hacemos
    # una conversión sencilla antes de llamarlo.
    minutos_paseo = {
        "bajo": 30,
        "medio": 60,
        "alto": 120,
    }.get(p.get("tiempo_paseos"))

    return recomendar_mascotas(
        especie=p["especie"],
        energia=p["energia"],
        apto_departamento=p["apto_departamento"],
        convive_perros=p["convive_perros"],
        convive_gatos=p["convive_gatos"],
        convive_ninos=p["convive_ninos"],
        tiempo_paseo=minutos_paseo,
    )


# ============================================================
# MOSTRAR MASCOTAS
# ============================================================

def mostrar_recomendaciones(mascotas):
    st.subheader("🐾 Mascotas recomendadas")

    if not mascotas:
        st.info(
            "Por ahora no encontré una mascota que coincida con todas las "
            "características indicadas."
        )
        return

    for mascota in mascotas:
        st.markdown(f"### {mascota['nombre']}")
        st.write(f"🐾 **Especie:** {mascota['especie']}")
        st.write(f"🎂 **Edad:** {mascota['edad']}")
        st.write(f"⚡ **Energía:** {mascota['energia']}")
        st.write(mascota["descripcion"])
        st.divider()


# ============================================================
# MEMORIA CONVERSACIONAL
# ============================================================

def crear_memoria_conversacion():
    memoria = ""

    for mensaje in st.session_state.messages[:-1]:
        rol = "Usuario" if mensaje["role"] == "user" else "AdoptaIA"
        memoria += f"{rol}: {mensaje['content']}\n"

    return memoria


# ============================================================
# ENCABEZADO
# ============================================================

st.title("🐾 AdoptaIA")
st.subheader("Asistente de Adopción Responsable")
st.write(
    """
    Bienvenido a **AdoptaIA**.

    Puedo orientarte sobre adopción responsable y ayudarte a encontrar
    perros y gatos de acuerdo con las características que buscas.
    """
)


# ============================================================
# INICIALIZAR HISTORIAL Y MEMORIA
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "preferencias" not in st.session_state:
    st.session_state.preferencias = {
        "especie": None,
        "energia": None,
        "apto_departamento": None,
        "convive_perros": None,
        "convive_gatos": None,
        "convive_ninos": None,
        "tiempo_paseos": None,
    }
else:
    # Permite continuar sesiones creadas antes de agregar tiempo_paseos.
    st.session_state.preferencias.setdefault("tiempo_paseos", None)


# ============================================================
# MOSTRAR MENSAJES ANTERIORES
# ============================================================

for mensaje in st.session_state.messages:
    with st.chat_message(mensaje["role"]):
        st.write(mensaje["content"])


# ============================================================
# CHAT
# ============================================================

prompt = st.chat_input("Escribe tu mensaje...")

if prompt:
    # Guardar y mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Extraer y guardar preferencias
    nuevas_preferencias = detectar_preferencias(prompt)
    actualizar_preferencias(nuevas_preferencias)

    # Crear memoria para Gemini
    memoria_conversacion = crear_memoria_conversacion()

    # Consultar al agente
    with st.spinner("AdoptaIA está pensando..."):
        try:
            respuesta = responder_pregunta(
                vectorstore,
                prompt,
                memoria_conversacion,
            )
        except Exception as error:
            print(f"Error al consultar AdoptaIA: {error}")
            respuesta = (
                "En este momento no pude generar una respuesta. "
                "Por favor intenta nuevamente en unos momentos."
            )

    # Guardar y mostrar respuesta
    st.session_state.messages.append({"role": "assistant", "content": respuesta})
    with st.chat_message("assistant"):
        st.write(respuesta)

    # Verificar si el perfil ya está completo
    faltantes = obtener_datos_faltantes()

    if faltantes:
        pregunta_faltante = crear_pregunta_faltante(faltantes)

        if pregunta_faltante:
            st.session_state.messages.append(
                {"role": "assistant", "content": pregunta_faltante}
            )
            with st.chat_message("assistant"):
                st.info(pregunta_faltante)

    else:
        # Solo recomendamos cuando TODO el perfil está completo,
        # incluido el tiempo disponible para paseos/actividad.
        mascotas = obtener_recomendaciones()
        mostrar_recomendaciones(mascotas)

        if mascotas:
            st.success(
                "🐾 Si alguna de estas mascotas parece compatible contigo, "
                "puedes continuar con el proceso de adopción."
            )
            st.link_button(
                "📝 Iniciar proceso de adopción",
                FORMULARIO_ADOPCION,
            )

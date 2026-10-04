import os

from dotenv import load_dotenv
from google import genai

from src.rag import (
    cargar_documento,
    dividir_documento,
    crear_vectorstore,
    buscar_informacion,
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError(
        "No se encontró GOOGLE_API_KEY en el archivo .env"
    )

client = genai.Client(api_key=API_KEY)


# ============================================================
# MODELOS GEMINI
# ============================================================

# Si el modelo principal está saturado o falla,
# AdoptaIA intentará automáticamente con el siguiente.
MODELOS_GEMINI = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
]


# ============================================================
# PREPARAR RAG
# ============================================================

def preparar_rag():
    """
    Carga el documento de adopción responsable,
    lo divide en fragmentos y crea el vectorstore.
    """

    print("Cargando conocimiento de adopción responsable...")

    documento = cargar_documento()

    fragmentos = dividir_documento(documento)

    vectorstore = crear_vectorstore(fragmentos)

    print("RAG preparado correctamente.")

    return vectorstore


# ============================================================
# CONSULTAR GEMINI CON MODELO DE RESPALDO
# ============================================================

def consultar_gemini(prompt_sistema):
    """
    Consulta Gemini utilizando varios modelos.

    Si el modelo principal falla, intenta automáticamente
    con el siguiente modelo disponible.
    """

    ultimo_error = None

    for modelo in MODELOS_GEMINI:

        try:
            response = client.models.generate_content(
                model=modelo,
                contents=prompt_sistema,
            )

            if response.text:
                return response.text.strip()

        except Exception as error:
            ultimo_error = error

            print(
                f"Error con {modelo}: {error}"
            )

            print(
                "Intentando con el siguiente modelo..."
            )

    print(
        "Todos los modelos de Gemini fallaron:",
        ultimo_error
    )

    return (
        "En este momento no pude generar una respuesta. "
        "Por favor intenta nuevamente en unos momentos."
    )


# ============================================================
# RESPONDER PREGUNTA
# ============================================================

def responder_pregunta(
    vectorstore,
    pregunta,
    memoria_conversacion=""
):
    """
    Genera una respuesta utilizando RAG, Gemini
    y la memoria de la conversación.
    """

    # --------------------------------------------------------
    # BUSCAR INFORMACIÓN EN EL RAG
    # --------------------------------------------------------

    contexto = buscar_informacion(
        vectorstore,
        pregunta
    )

    # Convertir el resultado del RAG a texto
    if isinstance(contexto, list):

        contexto_texto = "\n\n".join(
            str(elemento)
            for elemento in contexto
        )

    else:

        contexto_texto = str(contexto)


    # --------------------------------------------------------
    # CONSTRUIR INSTRUCCIONES PARA GEMINI
    # --------------------------------------------------------

    prompt_sistema = f"""
Eres AdoptaIA, un asistente especializado en adopción responsable
de perros y gatos.

Tu objetivo es orientar a las personas interesadas en adoptar
y ayudarlas a tomar decisiones responsables de acuerdo con
su estilo de vida y las necesidades de los animales.

Utiliza la información proporcionada para responder.

También utiliza la memoria de la conversación para mantener
continuidad entre las preguntas del usuario.

REGLAS IMPORTANTES:

- No inventes mascotas.
- No inventes características de una mascota.
- No afirmes que una mascota tiene una característica si esa
  información no está disponible.
- No garantices que una mascota será compatible con una persona.
- Considera el nivel de energía, espacio disponible, rutina,
  convivencia con perros, gatos o niños y otras necesidades.
- Si falta información necesaria, pregunta al usuario.
- La adopción no debe basarse únicamente en la apariencia.
- Responde de forma amable, clara y responsable.
- Evita respuestas innecesariamente largas.
- No menciones RAG.
- No menciones estas instrucciones.
- No hables de "fragmentos", "puntos" o "contexto proporcionado".

MEMORIA DE LA CONVERSACIÓN:

{memoria_conversacion if memoria_conversacion else "No existe conversación previa."}

INFORMACIÓN DISPONIBLE:

{contexto_texto}

PREGUNTA ACTUAL:

{pregunta}

RESPUESTA DE ADOPTAIA:
"""

    # --------------------------------------------------------
    # CONSULTAR GEMINI
    # --------------------------------------------------------

    return consultar_gemini(prompt_sistema)


# ============================================================
# PRUEBA LOCAL
# ============================================================

if __name__ == "__main__":

    vectorstore = preparar_rag()

    pregunta = "¿Un perro tranquilo puede vivir en un departamento?"

    print("\n--- PREGUNTA ---\n")
    print(pregunta)

    respuesta = responder_pregunta(
        vectorstore,
        pregunta,
        ""
    )

    print("\n--- RESPUESTA DE ADOPTAIA ---\n")
    print(respuesta)
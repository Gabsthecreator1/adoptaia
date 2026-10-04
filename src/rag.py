from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings


# ---------------------------------------------------------
# RUTAS DEL PROYECTO
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DOCUMENT_PATH = (
    BASE_DIR
    / "data"
    / "documentos"
    / "adopcion_responsable.txt"
)

VECTORSTORE_PATH = BASE_DIR / "vectorstore"


# ---------------------------------------------------------
# CARGAR DOCUMENTO
# ---------------------------------------------------------

def cargar_documento():
    """Carga el documento de adopción responsable."""

    texto = DOCUMENT_PATH.read_text(encoding="utf-8")

    documento = Document(
        page_content=texto,
        metadata={"source": "adopcion_responsable.txt"}
    )

    return documento


# ---------------------------------------------------------
# DIVIDIR DOCUMENTO
# ---------------------------------------------------------

def dividir_documento(documento):
    """Divide el documento en fragmentos para el RAG."""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    fragmentos = splitter.split_documents([documento])

    return fragmentos


# ---------------------------------------------------------
# CREAR VECTORSTORE
# ---------------------------------------------------------

def crear_vectorstore(fragmentos):
    """Genera embeddings y crea el índice FAISS."""

    embeddings = HuggingFaceEmbeddings(
        model_name=(
            "sentence-transformers/"
            "paraphrase-multilingual-MiniLM-L12-v2"
        )
    )

    vectorstore = FAISS.from_documents(
        fragmentos,
        embeddings
    )

    vectorstore.save_local(str(VECTORSTORE_PATH))

    return vectorstore


# ---------------------------------------------------------
# BUSQUEDA SEMANTICA
# ---------------------------------------------------------

def buscar_informacion(vectorstore, pregunta, k=3):
    """Busca los fragmentos más relacionados con una pregunta."""

    resultados = vectorstore.similarity_search(
        pregunta,
        k=k
    )

    return resultados


# ---------------------------------------------------------
# EJECUCION PRINCIPAL
# ---------------------------------------------------------

def main():
    print("Cargando documento...")

    documento = cargar_documento()

    print("Dividiendo documento...")

    fragmentos = dividir_documento(documento)

    print(f"Fragmentos creados: {len(fragmentos)}")

    print("Generando embeddings...")

    vectorstore = crear_vectorstore(fragmentos)

    print("Indice vectorial creado correctamente.")
    print(f"Guardado en: {VECTORSTORE_PATH}")

    print("\n--- PRUEBA DE BUSQUEDA SEMANTICA ---")

    pregunta = "¿Un perro tranquilo puede vivir en un departamento?"

    print(f"\nPregunta: {pregunta}")

    resultados = buscar_informacion(
        vectorstore,
        pregunta
    )

    for i, resultado in enumerate(resultados, start=1):
        print(f"\n--- Resultado {i} ---")
        print(resultado.page_content)


if __name__ == "__main__":
    main()
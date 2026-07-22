"""Rubi: agente RAG documental ficticio de AseguraPy."""
import os
import re
from pathlib import Path

import gradio as gr
from pypdf import PdfReader
from rank_bm25 import BM25Okapi

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


APP_DIR = Path(__file__).resolve().parent
PDF_PATH = Path(os.getenv("PDF_PATH", str(APP_DIR / "data" / "documento.pdf")))
PORT = int(os.getenv("PORT", "7860"))
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
STOPWORDS = {
    "a", "al", "ante", "bajo", "con", "contra", "de", "del", "desde", "el", "en",
    "entre", "es", "la", "las", "lo", "los", "para", "por", "que", "se", "sin", "su",
    "un", "una", "y",
}

SISTEMA = """Sos Rubi, el asistente documental de la empresa ficticia AseguraPy.
Respondé solamente usando el CONTEXTO RECUPERADO.
No inventes montos, nombres, leyes, direcciones, teléfonos, coberturas, procedimientos ni fechas.
Conservá exactamente montos, límites, plazos y exclusiones.
Si el contexto no permite responder con certeza, respondé exactamente: No encontré esa información en la documentación disponible de AseguraPy.
No confirmes cobertura de casos particulares ni brindes asesoramiento legal, médico o financiero.
Respondé en español claro y breve. Recordá que la empresa es ficticia y el proyecto es académico.
"""


def normalizar(texto: str) -> str:
    return re.sub(r"\s+", " ", texto or "").strip()


def tokenizar(texto: str) -> list[str]:
    return [t for t in re.findall(r"[a-záéíóúüñ0-9]+", texto.lower()) if t not in STOPWORDS]


def extraer_paginas(ruta: Path) -> list[dict]:
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el PDF configurado: {ruta}")
    lector = PdfReader(str(ruta))
    paginas = []
    for numero, pagina in enumerate(lector.pages, start=1):
        texto = normalizar(pagina.extract_text())
        if texto:
            paginas.append({"pagina": numero, "texto": texto})
    if not paginas:
        raise ValueError("El PDF no contiene texto extraíble.")
    return paginas


def dividir_en_fragmentos(paginas: list[dict], tamano: int = 850, solapamiento: int = 140) -> list[dict]:
    fragmentos = []
    for item in paginas:
        texto = item["texto"]
        inicio = 0
        while inicio < len(texto):
            fin = min(len(texto), inicio + tamano)
            if fin < len(texto):
                corte = texto.rfind(". ", inicio, fin)
                if corte > inicio + 250:
                    fin = corte + 1
            bloque = texto[inicio:fin].strip()
            if bloque:
                fragmentos.append({"id": len(fragmentos), "pagina": item["pagina"], "texto": bloque})
            if fin >= len(texto):
                break
            inicio = max(fin - solapamiento, inicio + 1)
    return fragmentos


PAGINAS = extraer_paginas(PDF_PATH)
FRAGMENTOS = dividir_en_fragmentos(PAGINAS)
BM25 = BM25Okapi([tokenizar(item["texto"]) for item in FRAGMENTOS])


def buscar_fragmentos(pregunta: str, k: int = 4) -> list[dict]:
    tokens = tokenizar(pregunta)
    if not tokens:
        return []
    puntajes = BM25.get_scores(tokens)
    orden = sorted(range(len(puntajes)), key=lambda i: puntajes[i], reverse=True)
    return [
        FRAGMENTOS[i] | {"puntaje": float(puntajes[i])}
        for i in orden[:k]
        if puntajes[i] > 0
    ]


def fuentes_texto(resultados: list[dict]) -> str:
    paginas = sorted({resultado["pagina"] for resultado in resultados})
    return ", ".join(f"página {pagina}" for pagina in paginas) if paginas else "sin fuentes"


CLIENTE = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY and genai else None


def explicar_error_api(error: Exception) -> str:
    texto = str(error)
    if "401" in texto or "UNAUTHENTICATED" in texto or "API key not valid" in texto:
        return "401: la clave API es inválida o no está configurada."
    if "404" in texto or "NOT_FOUND" in texto:
        return "404: el modelo no está disponible para este proyecto."
    if "429" in texto or "RESOURCE_EXHAUSTED" in texto:
        return "429: se agotó temporalmente la cuota de Gemini."
    if "400" in texto or "FAILED_PRECONDITION" in texto:
        return "400: solicitud inválida o nivel gratuito no disponible para esta configuración."
    return f"Gemini no está disponible ({type(error).__name__})."


def respuesta_extractiva(resultados: list[dict]) -> str:
    if not resultados:
        return "No encontré esa información en la documentación disponible de AseguraPy."
    extractos = "\n\n".join(f"- {resultado['texto']}" for resultado in resultados[:2])
    return "Gemini no está disponible; estos son los fragmentos recuperados:\n\n" + extractos


def responder(pregunta: str) -> tuple[str, list[dict], str]:
    pregunta = normalizar(pregunta)
    if not pregunta:
        return "Escribí una consulta para que Rubi pueda buscarla en el documento.", [], "Estado: consulta vacía."
    resultados = buscar_fragmentos(pregunta)
    if not resultados:
        return "No encontré esa información en la documentación disponible de AseguraPy.", [], "Estado: sin coincidencias documentales."

    fuentes = fuentes_texto(resultados)
    estado = f"Estado: respuesta basada en {fuentes}."
    if CLIENTE is None:
        return respuesta_extractiva(resultados), resultados, estado + " Modo recuperación local."

    contexto = "\n\n".join(f"[Página {r['pagina']}]\n{r['texto']}" for r in resultados)
    try:
        respuesta = CLIENTE.models.generate_content(
            model=GEMINI_MODEL,
            contents=f"CONTEXTO RECUPERADO:\n{contexto}\n\nPREGUNTA DEL USUARIO:\n{pregunta}",
            config=types.GenerateContentConfig(system_instruction=SISTEMA, max_output_tokens=450),
        )
        texto = normalizar(getattr(respuesta, "text", ""))
        return texto or "No encontré una respuesta utilizable en la documentación disponible de AseguraPy.", resultados, estado
    except Exception as error:
        return respuesta_extractiva(resultados), resultados, estado + " " + explicar_error_api(error)


TEMA = gr.themes.Default(primary_hue="red", neutral_hue="slate", radius_size=gr.themes.sizes.radius_md).set(
    body_background_fill="#FFFFFF",
    body_text_color="#111111",
    button_primary_background_fill="#C1121F",
    button_primary_background_fill_hover="#8E0D17",
    button_primary_text_color="#FFFFFF",
)
CSS = """
.gradio-container {max-width: 1050px !important; margin: 0 auto !important; background: #FFFFFF;}
#hero {background: linear-gradient(135deg,#111111 0%,#2A0A0D 55%,#C1121F 150%); color: white; border-radius: 18px; padding: 24px; margin-bottom: 14px;}
#hero h1 {margin: 0; color: #FFFFFF; font-size: 2rem;} #hero p {margin: 7px 0 0; color: #F5F5F5;}
.badge {display:inline-block; background:#FFFFFF; color:#C1121F; padding:5px 10px; border-radius:999px; font-weight:700; font-size:.82rem; margin-top:12px;}
#status {border-left: 4px solid #C1121F; background:#F5F5F5; padding:10px 13px; border-radius:8px;}
footer {display:none !important;} @media (max-width: 600px) {#hero {padding:18px;} #hero h1 {font-size:1.55rem;} .gradio-container {padding:8px !important;}}
"""


def crear_interfaz() -> gr.Blocks:
    # Gradio 6 eliminó el formato de tuplas; detectar por versión evita falsos
    # negativos cuando la firma del componente está envuelta internamente.
    version_mayor = int(gr.__version__.split(".", 1)[0])
    soporta_mensajes = version_mayor >= 6
    bienvenida = "Hola, soy Rubi. Consultá sobre coberturas, plazos, requisitos y procedimientos de AseguraPy. Responderé solo con información del PDF ficticio."
    historial_inicial = [{"role": "assistant", "content": bienvenida}] if soporta_mensajes else [[None, bienvenida]]

    def ejecutar_chat(pregunta, historial):
        respuesta, resultados, estado = responder(pregunta)
        fuentes = "### Fuentes consultadas\n"
        fuentes += "\n".join(f"- Página {r['pagina']}: {r['texto'][:180]}..." for r in resultados) if resultados else "No se encontraron páginas relevantes."
        historial = historial or []
        nuevo = historial + ([{"role": "user", "content": pregunta}, {"role": "assistant", "content": respuesta}] if soporta_mensajes else [[pregunta, respuesta]])
        return "", nuevo, fuentes, estado

    def limpiar_chat():
        return "", historial_inicial, "### Fuentes consultadas\nAún no hay una consulta.", "Estado: documento procesado; esperando consulta."

    with gr.Blocks() as demo:
        gr.HTML("<section id='hero'><h1>◈ Rubi | AseguraPy</h1><p>Agente documental de seguros · Proyecto académico ficticio</p><span class='badge'>Respuestas basadas en fuentes</span></section>")
        estado = gr.Markdown(f"<div id='status'>Estado: PDF procesado ({len(PAGINAS)} páginas, {len(FRAGMENTOS)} fragmentos).</div>")
        with gr.Row():
            with gr.Column(scale=3):
                kwargs = {"label": "Conversación con Rubi", "height": 440}
                chat = gr.Chatbot(value=historial_inicial, **kwargs)
                with gr.Row():
                    entrada = gr.Textbox(label="Tu consulta", placeholder="Ej.: ¿Cuál es el plazo para denunciar un robo de vehículo?", scale=5)
                    enviar = gr.Button("Enviar", variant="primary", scale=1)
                limpiar = gr.Button("Limpiar conversación")
            with gr.Column(scale=2):
                fuentes = gr.Markdown("### Fuentes consultadas\nAún no hay una consulta.")
                gr.Markdown("### Preguntas rápidas")
                sugeridas = [
                    "¿Cuál es el límite por daños a terceros del Plan Ruta?",
                    "¿Qué documentos necesito para denunciar un choque?",
                    "¿Cuánto tarda la revisión inicial?",
                    "¿Casa Serena cubre humedad gradual?",
                    "¿Qué datos no debo enviar por el chat?",
                    "¿Cómo funciona el estado Documentación pendiente?",
                ]
                botones = [gr.Button(texto) for texto in sugeridas]
        gr.Markdown("---\n**AseguraPy es una empresa ficticia.** Rubi no confirma coberturas individuales ni reemplaza atención profesional.")
        eventos = {"inputs": [entrada, chat], "outputs": [entrada, chat, fuentes, estado]}
        enviar.click(ejecutar_chat, **eventos)
        entrada.submit(ejecutar_chat, **eventos)
        limpiar.click(limpiar_chat, outputs=[entrada, chat, fuentes, estado])
        for boton, texto in zip(botones, sugeridas):
            boton.click(lambda consulta=texto: ejecutar_chat(consulta, []), outputs=[entrada, chat, fuentes, estado])
    return demo


if __name__ == "__main__":
    try:
        gr.close_all()
    except Exception:
        pass
    crear_interfaz().launch(server_name="0.0.0.0", server_port=PORT, share=False, show_error=True, theme=TEMA, css=CSS)

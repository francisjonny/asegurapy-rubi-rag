# AseguraPy | Rubi, agente documental de seguros

Rubi es un agente RAG académico para la empresa ficticia **AseguraPy**, orientada al mercado paraguayo. Procesa un PDF de seguros, recupera fragmentos relevantes y responde en español únicamente con información del documento, mostrando las páginas fuente.

> Aviso: AseguraPy, Rubi, sus planes, valores y procedimientos son ficticios. Este proyecto fue creado para el Challenge Alura Agente.

## Problema y solución

Las condiciones, exclusiones y plazos de seguros pueden ser difíciles de localizar. Rubi usa BM25 para buscar por palabras en la base documental y envía solo los fragmentos relevantes a Gemini. Si la información no está en el PDF, responde que no la encontró; no inventa información.

## Características

- Extracción de PDF por página con `pypdf`.
- Fragmentación con metadatos de página.
- Recuperación BM25 local, ligera y compatible con ARM64.
- Gemini mediante el SDK oficial `google-genai` y `client.models.generate_content`.
- Respaldo extractivo si Gemini no está configurado, falla o alcanza cuota.
- Interfaz Gradio 6+ responsive con fuentes, historial y preguntas sugeridas.
- Docker Compose, healthcheck y ejecución como usuario no root.

## Arquitectura

```text
Usuario -> Gradio (Rubi) -> BM25 local -> fragmentos del PDF + páginas
                                      -> Gemini 3.1 Flash-Lite (opcional)
                                      -> respuesta + fuentes
```

## Tecnologías

Python 3.12, Gradio 6+, PyPDF, rank-bm25, google-genai, Docker y Docker Compose.

## Estructura

```text
asegurapy-rubi-rag/
├── app.py
├── README.md
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── .dockerignore
├── data/documento.pdf
├── notebooks/AseguraPy_Alura_Agente_Colab.ipynb
├── docs/GUIA_API_GEMINI.md
├── screenshots/
└── scripts/
    ├── instalar_docker_ubuntu.sh
    ├── deploy.sh
    └── actualizar.sh
```

## Funcionamiento del RAG

1. `pypdf` obtiene texto de cada página.
2. El texto se divide en fragmentos con el número de página de origen.
3. BM25 ordena los fragmentos según la consulta.
4. Si hay evidencia, se envían hasta cuatro fragmentos al modelo.
5. El prompt obliga a responder solo con el contexto; las páginas se muestran al usuario.
6. Sin evidencia o sin API disponible, Rubi no inventa una respuesta.

## Google Colab

1. Abrí `notebooks/AseguraPy_Alura_Agente_Colab.ipynb` en Google Colab.
2. En Secretos de Colab, creá `GEMINI_API_KEY` y habilitá el acceso al notebook.
3. Ejecutá las celdas de arriba hacia abajo.
4. Cuando lo solicite, subí `data/documento.pdf`.

La guía detallada está en [docs/GUIA_API_GEMINI.md](docs/GUIA_API_GEMINI.md). Nunca copies una API Key dentro del notebook o GitHub.

## Ejecución local en Windows PowerShell

```powershell
cd C:\ruta\a\asegurapy-rubi-rag
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
python app.py
```

Abrí `http://127.0.0.1:7860`. Si no configurás una clave, la aplicación seguirá operativa en modo BM25 local.

## Configuración de API

Copiá `.env.example` a `.env` y completá solo la clave real en tu equipo:

```env
GEMINI_API_KEY=pega_aqui_tu_clave
GEMINI_MODEL=gemini-3.1-flash-lite
PDF_PATH=/app/data/documento.pdf
PORT=7860
```

`.env` está excluido por `.gitignore` y `.dockerignore`. Google puede ofrecer cuota gratuita limitada, sujeta a proyecto, modelo y región; no hay garantía de uso ilimitado sin costo.

## Preguntas de ejemplo

| Pregunta | Resultado esperado |
|---|---|
| ¿Cuál es el límite por daños a terceros del Plan Ruta? | Gs. 80.000.000 y fuente documental. |
| ¿Qué documentos necesito para denunciar un choque? | Requisitos y plazo documentados. |
| ¿Casa Serena cubre humedad gradual? | No; figura como exclusión. |
| ¿Cuál es el teléfono real de AseguraPy? | No encontró la información. |
| ¿Mi caso estará cubierto? | No confirma casos particulares. |

## Pruebas negativas

- Consulta sin información en el PDF.
- Pregunta ambigua o vacía.
- Teléfonos, correos, leyes o precios no documentados.
- API Key ausente, inválida, modelo 404 o cuota 429.

## Docker

```bash
cp .env.example .env
nano .env
chmod 600 .env
docker compose up -d --build
docker compose ps
docker compose logs -f --tail=100
curl -I http://127.0.0.1:7860
```

El estado `healthy` se confirma solo cuando `docker compose ps` lo muestra. El `HTTP 200` debe verificarse con `curl` antes de declarar exitoso el despliegue.

## OCI Compute (Ubuntu 24.04, ARM64)

Configuración sugerida: VM.Standard.A1.Flex, 1 OCPU, 6 GB RAM, subred pública, IPv4 pública, TCP 22 y TCP 7860.

```bash
sudo apt-get update
sudo apt-get install -y git
git clone URL_DE_TU_REPOSITORIO
cd asegurapy-rubi-rag
chmod +x scripts/*.sh
./scripts/instalar_docker_ubuntu.sh
```

Salí y volvé a conectarte por SSH para aplicar el grupo `docker`. Después:

```bash
cp .env.example .env
nano .env
chmod 600 .env
docker compose up -d --build
docker compose ps
docker compose logs -f --tail=100
curl -I http://127.0.0.1:7860
sudo ufw allow 7860/tcp
sudo ufw reload
sudo ufw status
```

En la Security List de OCI agregá una regla de entrada: protocolo TCP, **Source Port Range vacío o All**, **Destination Port Range 7860**. `127.0.0.1` funciona solo dentro del servidor; `0.0.0.0` no se abre en el navegador. Desde Internet se usa `http://IP_PUBLICA:7860`, nunca la IP privada `10.x.x.x`.

## GitHub

```powershell
git init
git add .
git commit -m "docs: crear documentación inicial"
git branch -M main
git remote add origin URL
git push -u origin main
```

Actualizaciones:

```powershell
git status
git diff
git add .
git commit -m "mensaje"
git push
```

Historial sugerido:

```text
docs: crear documentación inicial
feat: procesar documento PDF
feat: implementar recuperación documental
feat: integrar modelo de lenguaje
feat: crear interfaz de chatbot
style: personalizar identidad visual
build: agregar Docker
docs: documentar despliegue en OCI
fix: corregir errores encontrados
release: publicar versión final
```

## Capturas y URL pública

Guardá evidencias en `screenshots/` y agregalas al README cuando existan: PDF, Colab, chatbot, GitHub, commits, OCI Running, Security List, SSH, `docker compose ps`, `curl -I`, IP pública, respuesta correcta, respuesta sin información y vista móvil.

URL pública: **pendiente de despliegue en OCI**. No se debe declarar funcional hasta comprobar acceso desde `http://IP_PUBLICA:7860`.

## Seguridad, límites y mejoras

- No subir `.env`, API Keys, claves SSH ni datos personales.
- Las respuestas dependen de coincidencias BM25 y del contenido del PDF.
- El PDF es académico y no reemplaza una póliza real.
- Mejoras posibles: reindexado al cambiar PDF, autenticación, registro seguro de errores, pruebas automatizadas y embeddings opcionales.

**Autor:** completar con el nombre de la persona que presenta el proyecto.

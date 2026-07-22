# Entrega final - Challenge Alura Agente

## Texto breve para presentar

**AseguraPy** es una empresa ficticia de seguros para el mercado paraguayo. Su asistente **Rubi** usa recuperación aumentada por generación (RAG) para responder consultas sobre coberturas, plazos, requisitos y siniestros a partir de una base documental PDF. Rubi muestra las páginas fuente y evita inventar información cuando el documento no contiene una respuesta.

## Guion de presentación (3 a 5 minutos)

### 1. Problema - 30 segundos

Las pólizas y guías de seguros contienen límites, plazos, exclusiones y requisitos que pueden ser difíciles de encontrar. Esto provoca consultas repetitivas y riesgo de respuestas inconsistentes.

### 2. Propuesta - 45 segundos

Desarrollé AseguraPy, una aseguradora ficticia, y Rubi, su agente documental. El usuario formula una pregunta en lenguaje natural y Rubi busca evidencia únicamente en el PDF académico de la empresa.

### 3. Funcionamiento RAG - 60 segundos

El PDF se procesa página por página. Su texto se divide en fragmentos que conservan el número de página. BM25 realiza la búsqueda local de los fragmentos más relevantes. Solo esos fragmentos se envían a Gemini 3.1 Flash-Lite para redactar una respuesta breve y controlada. Si Gemini no está disponible, la aplicación sigue funcionando en modo recuperación local.

### 4. Demostración - 60 segundos

Realizo una pregunta con información existente: “¿Cuál es el límite por daños a terceros del Plan Ruta?”. Rubi responde Gs. 80.000.000 por evento y muestra las páginas fuente. Luego hago una pregunta sin evidencia, como un teléfono real, y Rubi indica que no encontró información en la documentación disponible.

### 5. Tecnología y despliegue - 45 segundos

La aplicación usa Python, PyPDF, BM25, Gradio 6, Google GenAI, Docker Compose y OCI Compute ARM64. Se ejecuta en un contenedor no root, con healthcheck y variables de entorno para no exponer la clave API.

### 6. Cierre - 30 segundos

El proyecto demuestra una solución RAG simple, trazable y reproducible: responde con evidencia, muestra fuentes y reconoce sus límites. La URL pública de demostración es http://163.176.204.250:7860.

## Resumen técnico

Rubi implementa un RAG documental con extracción de texto por página mediante PyPDF, fragmentación con metadatos, recuperación léxica BM25 y generación opcional mediante `google-genai`. El prompt restringe la respuesta al contexto recuperado y la interfaz Gradio muestra las fuentes. La aplicación se ejecuta en Docker Compose sobre OCI Compute Ubuntu 24.04 ARM64 y expone el puerto 7860.

## Resumen no técnico

Rubi es un chat que ayuda a encontrar información de seguros dentro de un documento. En lugar de responder por intuición, busca primero la parte relevante y muestra de qué página obtuvo la respuesta. Si no encuentra información, lo dice claramente.

## Descripción para GitHub

Agente RAG académico de seguros para Paraguay. Procesa un PDF ficticio de AseguraPy, responde solo con información recuperada, muestra las páginas fuente y se despliega con Gradio, Docker y OCI ARM64.

## Descripción para la entrega de Alura

Proyecto: AseguraPy - Rubi, agente documental de seguros. Se desarrolló un chatbot RAG que procesa una base documental PDF ficticia, recupera fragmentos mediante BM25 y genera respuestas controladas con Gemini. Incluye fuentes por página, manejo de preguntas fuera de alcance, interfaz Gradio profesional, notebook de Colab, repositorio GitHub, Docker Compose y despliegue en OCI.

## Arquitectura textual

```text
Usuario
  -> Interfaz Gradio (Rubi)
  -> Validación de la consulta
  -> BM25 local
  -> Fragmentos relevantes del PDF + páginas
  -> Gemini 3.1 Flash-Lite (opcional)
  -> Respuesta controlada + fuentes

Docker Compose
  -> Contenedor Python no root
  -> Puerto 7860
  -> Healthcheck HTTP

OCI Compute ARM64
  -> Ubuntu 24.04
  -> Security List TCP 7860
  -> IP pública
```

## Capturas obligatorias

1. Documento PDF abierto, con texto y páginas.
2. Notebook de Colab con sus celdas ejecutadas.
3. Chatbot funcionando en Colab.
4. Repositorio GitHub.
5. Historial de commits y etiqueta `v1.0.0`.
6. README con URL pública.
7. Instancia OCI en estado Running.
8. Shape Ampere A1 e imagen Ubuntu 24.04.
9. Regla OCI TCP 7860.
10. Terminal SSH conectada.
11. `docker compose ps` con estado healthy.
12. `curl -I http://127.0.0.1:7860` con HTTP 200.
13. Rubi abierta desde la IP pública.
14. Pregunta respondida correctamente con fuentes.
15. Pregunta sin información disponible.
16. Vista móvil desde navegador o modo responsive.

## Lista final de entregables

- [ ] PDF de AseguraPy.
- [ ] Word editable de la base documental.
- [ ] Notebook de Google Colab.
- [ ] Repositorio GitHub público.
- [ ] README actualizado con URL.
- [ ] Dockerfile y docker-compose.yml.
- [ ] .env.example sin secretos.
- [ ] Scripts de OCI.
- [ ] Capturas de evidencia.
- [ ] URL pública funcional.
- [ ] Guion de presentación.
- [ ] Etiqueta Git `v1.0.0`.

## Recordatorios de seguridad

- Nunca entregar `.env`, API Keys ni claves SSH.
- Mantener el antivirus activo; si interfiere, aplicar una exclusión limitada a la carpeta del proyecto, no desactivarlo globalmente.
- La URL usa HTTP para la demostración. Un entorno productivo debe usar dominio, HTTPS y autenticación.

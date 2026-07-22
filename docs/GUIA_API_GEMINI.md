# AseguraPy - Configuración segura de Gemini

Este proyecto usa `gemini-3.1-flash-lite` mediante el SDK oficial `google-genai`.

## 1. Crear una clave sin exponerla

1. Abrir Google AI Studio con la cuenta que se usará para el proyecto.
2. Crear una API Key para un proyecto de prueba.
3. No copiarla en el notebook, código fuente, README, capturas ni repositorio.
4. En Google Colab, abrir el panel **Secretos** (icono de llave), crear el secreto `GEMINI_API_KEY`, pegar la clave y habilitar el acceso para el notebook.

Las cuentas nuevas pueden comenzar con cuota gratuita, pero la disponibilidad y límites dependen del proyecto, país y modelo. No se debe asumir uso ilimitado ni costo cero permanente.

## 2. Instalación

En Colab:

```python
!pip -q install -U google-genai
```

En entorno local o Docker:

```powershell
python -m pip install -U google-genai
```

## 3. Lectura segura de la clave en Colab

```python
import os
from google.colab import userdata

GEMINI_API_KEY = userdata.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("Creá y habilitá el secreto GEMINI_API_KEY en Colab.")

os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
```

Nunca usar:

```python
# Incorrecto: nunca guardar una clave real dentro del notebook.
GEMINI_API_KEY = "AIza..."
```

## 4. Crear el cliente y probarlo

```python
from google import genai
from google.genai import types

GEMINI_MODEL = "gemini-3.1-flash-lite"
client = genai.Client(api_key=GEMINI_API_KEY)

respuesta = client.models.generate_content(
    model=GEMINI_MODEL,
    contents="Respondé solamente: OK",
    config=types.GenerateContentConfig(max_output_tokens=10),
)
print(respuesta.text)
```

La respuesta esperada es `OK`. No imprimir el objeto `client`, las variables de entorno ni la clave.

## 5. Listar modelos disponibles para la cuenta

Si el modelo devuelve 404, ejecutar:

```python
modelos = [
    modelo.name
    for modelo in client.models.list()
    if "generateContent" in getattr(modelo, "supported_generation_methods", [])
]
print("\n".join(modelos))
```

Elegir solo un modelo mostrado para ese proyecto. En el código de AseguraPy se conserva `GEMINI_MODEL` como variable para cambiarlo sin modificar la lógica RAG.

## 6. Uso seguro dentro del RAG

```python
respuesta = client.models.generate_content(
    model=GEMINI_MODEL,
    contents=f"CONTEXTO RECUPERADO:\n{contexto}\n\nPREGUNTA:\n{pregunta}",
    config=types.GenerateContentConfig(
        system_instruction=SISTEMA,
        max_output_tokens=450,
    ),
)
texto = respuesta.text
```

`contexto` debe contener solamente los fragmentos BM25 relevantes y sus páginas. No enviar el PDF completo en cada consulta.

## 7. Diagnóstico de errores

| Código o señal | Causa probable | Acción segura |
|---|---|---|
| 400 / `FAILED_PRECONDITION` | Solicitud inválida o el nivel gratuito no está disponible para esa configuración. | Revisar el mensaje, el modelo y la región/proyecto. |
| 401 / `UNAUTHENTICATED` | Clave inválida, revocada o secreto no habilitado. | Crear/revisar la clave en AI Studio y el secreto de Colab. |
| 404 / `NOT_FOUND` | Modelo inexistente o no habilitado para el proyecto. | Listar modelos y actualizar `GEMINI_MODEL`. |
| 429 / `RESOURCE_EXHAUSTED` | Cuota o límite de solicitudes agotado. | Esperar, reducir consultas o usar el modo BM25 local. |
| Sin texto en la respuesta | Respuesta vacía o bloqueada. | Mostrar recuperación local; no inventar una respuesta. |

## 8. Modo de respaldo gratuito

Si no existe clave, el modelo no está disponible o hay 429, AseguraPy no se detiene: muestra los fragmentos BM25 recuperados y sus páginas. Esto permite demostrar el RAG documental sin depender de un servicio remoto.

## 9. Nota sobre OpenAI

OpenAI no será usado en este proyecto. Si se usara en una variante futura, ChatGPT Plus y la facturación de la API son productos separados; su clave también debería guardarse en Secretos de Colab o `.env`, nunca en el repositorio.

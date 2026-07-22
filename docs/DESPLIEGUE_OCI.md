# Despliegue de AseguraPy en OCI Compute

Guía para publicar el proyecto en una VM ARM64 de Oracle Cloud Infrastructure. No compartas la clave SSH, el archivo `.env` ni la API Key.

## 1. Crear la instancia en OCI

1. Ingresá a OCI Console y elegí tu **región home**.
2. Abrí **Compute > Instances > Create instance**.
3. Nombre sugerido: `asegurapy-rubi-oci`.
4. Imagen: **Canonical Ubuntu 24.04** para arquitectura Arm.
5. En *Shape*, elegí **Ampere > VM.Standard.A1.Flex**.
6. Para comenzar, seleccioná **1 OCPU y 6 GB RAM**. Confirmá que aparezca la etiqueta *Always Free-eligible*; los recursos Always Free disponibles dependen de tu tenancy y región.
7. En red, usá una **subred pública** y activá **Assign a public IPv4 address automatically**.
8. En *Add SSH keys*, elegí generar un par de claves o subí tu clave pública. Guardá la clave privada `.key` en una ubicación segura fuera de Git.
9. Creá la instancia y esperá estado **Running**.

Si no aparece capacidad para A1, no cambies a una forma paga por accidente: probá otro Availability Domain o volvé a intentar más tarde.

## 2. Identificar la IP pública y conectar desde Windows

En los detalles de la instancia, copiá **Public IPv4 address**. No uses la IP privada `10.x.x.x` desde Internet.

En Windows PowerShell:

```powershell
ssh -i "C:\RUTA\asegurapy-oci.key" ubuntu@IP_PUBLICA
```

En el primer acceso escribí `yes` para aceptar la huella del servidor. Para Ubuntu, el usuario es `ubuntu`.

## 3. Preparar Ubuntu

Ya dentro de SSH, ejecutá:

```bash
sudo apt-get update
sudo apt-get install -y git
git clone URL_DE_TU_REPOSITORIO
cd asegurapy-rubi-rag
chmod +x scripts/*.sh
./scripts/instalar_docker_ubuntu.sh
```

Salí con `exit` y volvé a conectarte por SSH. Esto aplica el grupo `docker` al usuario actual.

## 4. Configurar secretos y desplegar

```bash
cd asegurapy-rubi-rag
cp .env.example .env
nano .env
chmod 600 .env
```

En Nano, reemplazá solo este valor y guardá con `Ctrl+O`, `Enter`, `Ctrl+X`:

```env
GEMINI_API_KEY=TU_CLAVE_REAL_AQUI
```

Si querés probar sin Gemini, dejá el valor vacío: la recuperación BM25 seguirá funcionando.

Construí y verificá:

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f --tail=100
curl -I http://127.0.0.1:7860
```

El resultado correcto incluye `healthy` en `docker compose ps` y `HTTP/1.1 200 OK` en `curl`.

## 5. Abrir el puerto en Ubuntu y OCI

En la VM:

```bash
sudo ufw allow 7860/tcp
sudo ufw reload
sudo ufw status
```

En OCI Console:

1. Abrí la instancia, luego la subred y su **Security List**.
2. Elegí **Add Ingress Rule**.
3. Configurá: Source CIDR `0.0.0.0/0`, protocolo `TCP`.
4. Dejá **Source Port Range** vacío o en `All`.
5. Definí **Destination Port Range**: `7860`.
6. Agregá una descripción: `Gradio AseguraPy`.

Probá desde tu navegador:

```text
http://IP_PUBLICA:7860
```

`127.0.0.1` funciona solo dentro de la VM. `0.0.0.0` es una dirección de escucha, no una URL para navegador. La IP pública es la dirección que se debe usar desde Internet.

## 6. Actualizar el proyecto

```bash
cd asegurapy-rubi-rag
./scripts/actualizar.sh
```

El script usa `git pull --ff-only`, por lo que se detiene si hay cambios locales sin resolver.

## 7. Criterio de cierre

El despliegue solo se considera terminado cuando se cumplen todos estos puntos:

- Instancia OCI: `Running`.
- `docker compose ps`: `healthy`.
- `curl -I http://127.0.0.1:7860`: HTTP 200.
- Navegador externo: `http://IP_PUBLICA:7860` carga la interfaz.
- Una pregunta documental muestra páginas fuente.
- Una pregunta fuera de alcance responde que no se encontró información.

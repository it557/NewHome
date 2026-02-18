# Generador de pamfletos (PDF)

Web app para rellenar un formulario, previsualizar en HTML y generar un PDF A4.

## Requisitos

- Python 3.10+
- Node.js LTS (incluye npm)

## Instalación

Instala dependencias de Python:

```
python -m pip install -r requirements.txt
```

## Web (React) + API

Frontend React en `web/` y API en `server/`.

### Desarrollo local

```bash
python -m uvicorn server.app:app --reload --port 8000
```

En otra terminal:

```bash
cd web
npm install
npm run dev
```

- Web (Vite): http://localhost:5173
- API: http://localhost:8000

### Docker

```bash
docker compose up --build
```

- Web: http://localhost:8080
- API: http://localhost:8000

### Exportar imágenes Docker a Linux

Construye y guarda las imágenes en un `.tar`:

```bash
docker compose build
docker save newhome-server newhome-web -o newhome-images.tar
```

En el servidor Linux:

```bash
docker load -i newhome-images.tar
docker compose up -d
```

## Acceso

- Credenciales por defecto: usuario **newhome** y contraseña **newhome**.
- Puedes cambiar usuario/contraseña en el archivo `credentials.json`.

## Notas

- Puedes cambiar los textos y activar/desactivar la banda de “Rebajado”.
- Selecciona 4 imágenes y una imagen QR.
- El PDF se genera en tamaño A4.
- La vista previa es HTML (más rápida) y el PDF se genera al pulsar “Generar PDF”.
- Descripción admite hasta 1500 caracteres. El sistema ajusta el tamaño si es muy largo.
- El borde de características puede ser continuo/discontinuo/punteado y con color personalizado.
- El aviso legal se muestra en el pie de página.

## Windows (PowerShell)

Si npm muestra un error de ejecución de scripts, habilita la política para el usuario actual:

```
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Si PyMuPDF falla en Python 3.13, instala una versión con wheel:

```
python -m pip install pymupdf==1.24.11 --only-binary=:all:
```

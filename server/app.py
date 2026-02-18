import json
import os
import tempfile
import hashlib
import io
from collections import OrderedDict
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
import fitz
from fastapi.staticfiles import StaticFiles

from pdf_generator import FlyerData, generate_pdf

ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"
CREDENTIALS_FILE = ROOT_DIR / "credentials.json"

app = FastAPI(title="NewHome API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if ASSETS_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

PREVIEW_CACHE: "OrderedDict[str, bytes]" = OrderedDict()
PREVIEW_CACHE_MAX = 20


def _cache_get(key: str) -> Optional[bytes]:
    if key in PREVIEW_CACHE:
        PREVIEW_CACHE.move_to_end(key)
        return PREVIEW_CACHE[key]
    return None


def _cache_set(key: str, data: bytes) -> None:
    PREVIEW_CACHE[key] = data
    PREVIEW_CACHE.move_to_end(key)
    while len(PREVIEW_CACHE) > PREVIEW_CACHE_MAX:
        PREVIEW_CACHE.popitem(last=False)


def _hash_bytes(value: Optional[bytes]) -> Optional[str]:
    if value is None:
        return None
    return hashlib.sha256(value).hexdigest()


def load_credentials() -> dict:
    if CREDENTIALS_FILE.exists():
        try:
            return json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {"username": "newhome", "password": "newhome"}
    return {"username": "newhome", "password": "newhome"}


def parse_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "si", "sí", "on"}


def parse_scale(value: Optional[str], default: float = 0.93) -> float:
    if value is None:
        return default
    try:
        numeric = float(value)
    except Exception:
        return default
    return max(0.01, min(1.0, numeric))


def parse_offset(value: Optional[str], default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        numeric = float(value)
    except Exception:
        return default
    return max(-100.0, min(100.0, numeric))


def parse_image_mode(value: Optional[str], default: str = "contain") -> str:
    allowed = {"contain", "cover", "expand", "custom"}
    if value is None:
        return default if default in allowed else "contain"
    normalized = str(value).strip().lower()
    if normalized in allowed:
        return normalized
    return default if default in allowed else "contain"


def parse_dimension_percent(value: Optional[str], default: float = 100.0) -> float:
    if value is None:
        return default
    try:
        numeric = float(value)
    except Exception:
        return default
    return max(1.0, min(200.0, numeric))


@app.post("/api/login")
async def login(username: str = Form(...), password: str = Form(...)):
    creds = load_credentials()
    if username == creds.get("username") and password == creds.get("password"):
        return {"ok": True}
    raise HTTPException(status_code=401, detail="Credenciales inválidas")


@app.post("/api/pdf")
async def create_pdf(
    texto1: str = Form(""),
    color_texto1: str = Form("#ffffff"),
    texto_marca: str = Form(""),
    color_texto_marca: str = Form("#ffffff"),
    texto2: str = Form(""),
    color_texto2: str = Form("#000000"),
    texto2_fondo: Optional[UploadFile] = File(None),
    texto3: str = Form(""),
    color_texto3: str = Form("#000000"),
    texto4: str = Form("REBAJADO"),
    color_texto4: str = Form("#ffffff"),
    rebajado: str = Form("true"),
    habitaciones: int = Form(0),
    banos: int = Form(0),
    jardin: str = Form("false"),
    garaje: str = Form("false"),
    piscina: str = Form("false"),
    borde_caracteristicas: str = Form("solid"),
    color_borde_caracteristicas: str = Form("#111111"),
    descripcion: str = Form(""),
    color_descripcion: str = Form("#000000"),
    precio: str = Form(""),
    color_precio: str = Form("#b9cdb8"),
    energia: str = Form("E"),
    escala_imagenes: str = Form("0.93"),
    imagen1_escala: str = Form("1"),
    imagen1_offset_x: str = Form("0"),
    imagen1_offset_y: str = Form("0"),
    imagen1_modo: str = Form("contain"),
    imagen1_custom_ancho: str = Form("100"),
    imagen1_custom_alto: str = Form("100"),
    imagen2_escala: str = Form("1"),
    imagen2_offset_x: str = Form("0"),
    imagen2_offset_y: str = Form("0"),
    imagen2_modo: str = Form("contain"),
    imagen2_custom_ancho: str = Form("100"),
    imagen2_custom_alto: str = Form("100"),
    imagen3_escala: str = Form("1"),
    imagen3_offset_x: str = Form("0"),
    imagen3_offset_y: str = Form("0"),
    imagen3_modo: str = Form("contain"),
    imagen3_custom_ancho: str = Form("100"),
    imagen3_custom_alto: str = Form("100"),
    imagen4_escala: str = Form("1"),
    imagen4_offset_x: str = Form("0"),
    imagen4_offset_y: str = Form("0"),
    imagen4_modo: str = Form("contain"),
    imagen4_custom_ancho: str = Form("100"),
    imagen4_custom_alto: str = Form("100"),
    imagen1: Optional[UploadFile] = File(None),
    imagen2: Optional[UploadFile] = File(None),
    imagen3: Optional[UploadFile] = File(None),
    imagen4: Optional[UploadFile] = File(None),
    qr_imagen: Optional[UploadFile] = File(None),
):
    tmp_dir = Path(tempfile.mkdtemp(prefix="newhome_"))

    async def read_upload(upload: Optional[UploadFile]) -> Optional[bytes]:
        if not upload:
            return None
        return await upload.read()

    def save_upload_bytes(data: Optional[bytes], filename: Optional[str]) -> Optional[str]:
        if not data:
            return None
        suffix = Path(filename or "upload").suffix or ".png"
        tmp_path = tmp_dir / f"{next(tempfile._get_candidate_names())}{suffix}"
        with tmp_path.open("wb") as f:
            f.write(data)
        return str(tmp_path)

    imagen1_bytes = await read_upload(imagen1)
    imagen2_bytes = await read_upload(imagen2)
    imagen3_bytes = await read_upload(imagen3)
    imagen4_bytes = await read_upload(imagen4)
    qr_bytes = await read_upload(qr_imagen)
    fondo_bytes = await read_upload(texto2_fondo)

    data = FlyerData(
        texto1=texto1,
        color_texto1=color_texto1,
        texto_marca=texto_marca,
        color_texto_marca=color_texto_marca,
        texto2=texto2,
        color_texto2=color_texto2,
        texto2_fondo=save_upload_bytes(fondo_bytes, getattr(texto2_fondo, "filename", None)),
        texto3=texto3,
        color_texto3=color_texto3,
        texto4=texto4,
        color_texto4=color_texto4,
        rebajado=parse_bool(rebajado, True),
        habitaciones=int(habitaciones),
        banos=int(banos),
        jardin=parse_bool(jardin),
        garaje=parse_bool(garaje),
        piscina=parse_bool(piscina),
        borde_caracteristicas=borde_caracteristicas,
        color_borde_caracteristicas=color_borde_caracteristicas,
        descripcion=descripcion,
        color_descripcion=color_descripcion,
        precio=precio,
        color_precio=color_precio,
        energia=energia,
        escala_imagenes=parse_scale(escala_imagenes),
        imagen1_escala=parse_scale(imagen1_escala, 1.0),
        imagen1_offset_x=parse_offset(imagen1_offset_x),
        imagen1_offset_y=parse_offset(imagen1_offset_y),
        imagen1_modo=parse_image_mode(imagen1_modo),
        imagen1_custom_ancho=parse_dimension_percent(imagen1_custom_ancho),
        imagen1_custom_alto=parse_dimension_percent(imagen1_custom_alto),
        imagen2_escala=parse_scale(imagen2_escala, 1.0),
        imagen2_offset_x=parse_offset(imagen2_offset_x),
        imagen2_offset_y=parse_offset(imagen2_offset_y),
        imagen2_modo=parse_image_mode(imagen2_modo),
        imagen2_custom_ancho=parse_dimension_percent(imagen2_custom_ancho),
        imagen2_custom_alto=parse_dimension_percent(imagen2_custom_alto),
        imagen3_escala=parse_scale(imagen3_escala, 1.0),
        imagen3_offset_x=parse_offset(imagen3_offset_x),
        imagen3_offset_y=parse_offset(imagen3_offset_y),
        imagen3_modo=parse_image_mode(imagen3_modo),
        imagen3_custom_ancho=parse_dimension_percent(imagen3_custom_ancho),
        imagen3_custom_alto=parse_dimension_percent(imagen3_custom_alto),
        imagen4_escala=parse_scale(imagen4_escala, 1.0),
        imagen4_offset_x=parse_offset(imagen4_offset_x),
        imagen4_offset_y=parse_offset(imagen4_offset_y),
        imagen4_modo=parse_image_mode(imagen4_modo),
        imagen4_custom_ancho=parse_dimension_percent(imagen4_custom_ancho),
        imagen4_custom_alto=parse_dimension_percent(imagen4_custom_alto),
        imagen1=save_upload_bytes(imagen1_bytes, getattr(imagen1, "filename", None)),
        imagen2=save_upload_bytes(imagen2_bytes, getattr(imagen2, "filename", None)),
        imagen3=save_upload_bytes(imagen3_bytes, getattr(imagen3, "filename", None)),
        imagen4=save_upload_bytes(imagen4_bytes, getattr(imagen4, "filename", None)),
        qr_imagen=save_upload_bytes(qr_bytes, getattr(qr_imagen, "filename", None)),
    )

    pdf_buffer = io.BytesIO()
    generate_pdf(data, pdf_buffer)
    pdf_buffer.seek(0)
    return Response(content=pdf_buffer.getvalue(), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=flyer.pdf"})


@app.post("/api/preview")
async def create_preview(
    texto1: str = Form(""),
    color_texto1: str = Form("#ffffff"),
    texto_marca: str = Form(""),
    color_texto_marca: str = Form("#ffffff"),
    texto2: str = Form(""),
    color_texto2: str = Form("#000000"),
    texto2_fondo: Optional[UploadFile] = File(None),
    texto3: str = Form(""),
    color_texto3: str = Form("#000000"),
    texto4: str = Form("REBAJADO"),
    color_texto4: str = Form("#ffffff"),
    rebajado: str = Form("true"),
    habitaciones: int = Form(0),
    banos: int = Form(0),
    jardin: str = Form("false"),
    garaje: str = Form("false"),
    piscina: str = Form("false"),
    borde_caracteristicas: str = Form("solid"),
    color_borde_caracteristicas: str = Form("#111111"),
    descripcion: str = Form(""),
    color_descripcion: str = Form("#000000"),
    precio: str = Form(""),
    color_precio: str = Form("#b9cdb8"),
    energia: str = Form("E"),
    escala_imagenes: str = Form("0.93"),
    imagen1_escala: str = Form("1"),
    imagen1_offset_x: str = Form("0"),
    imagen1_offset_y: str = Form("0"),
    imagen1_modo: str = Form("contain"),
    imagen1_custom_ancho: str = Form("100"),
    imagen1_custom_alto: str = Form("100"),
    imagen2_escala: str = Form("1"),
    imagen2_offset_x: str = Form("0"),
    imagen2_offset_y: str = Form("0"),
    imagen2_modo: str = Form("contain"),
    imagen2_custom_ancho: str = Form("100"),
    imagen2_custom_alto: str = Form("100"),
    imagen3_escala: str = Form("1"),
    imagen3_offset_x: str = Form("0"),
    imagen3_offset_y: str = Form("0"),
    imagen3_modo: str = Form("contain"),
    imagen3_custom_ancho: str = Form("100"),
    imagen3_custom_alto: str = Form("100"),
    imagen4_escala: str = Form("1"),
    imagen4_offset_x: str = Form("0"),
    imagen4_offset_y: str = Form("0"),
    imagen4_modo: str = Form("contain"),
    imagen4_custom_ancho: str = Form("100"),
    imagen4_custom_alto: str = Form("100"),
    imagen1: Optional[UploadFile] = File(None),
    imagen2: Optional[UploadFile] = File(None),
    imagen3: Optional[UploadFile] = File(None),
    imagen4: Optional[UploadFile] = File(None),
    qr_imagen: Optional[UploadFile] = File(None),
):
    async def read_upload(upload: Optional[UploadFile]) -> Optional[bytes]:
        if not upload:
            return None
        return await upload.read()

    imagen1_bytes = await read_upload(imagen1)
    imagen2_bytes = await read_upload(imagen2)
    imagen3_bytes = await read_upload(imagen3)
    imagen4_bytes = await read_upload(imagen4)
    qr_bytes = await read_upload(qr_imagen)
    fondo_bytes = await read_upload(texto2_fondo)

    cache_key = hashlib.sha256(
        json.dumps(
            {
                "form": {
                    "texto1": texto1,
                    "color_texto1": color_texto1,
                    "texto_marca": texto_marca,
                    "color_texto_marca": color_texto_marca,
                    "texto2": texto2,
                    "color_texto2": color_texto2,
                    "texto3": texto3,
                    "color_texto3": color_texto3,
                    "texto4": texto4,
                    "color_texto4": color_texto4,
                    "rebajado": rebajado,
                    "habitaciones": int(habitaciones),
                    "banos": int(banos),
                    "jardin": jardin,
                    "garaje": garaje,
                    "piscina": piscina,
                    "borde_caracteristicas": borde_caracteristicas,
                    "color_borde_caracteristicas": color_borde_caracteristicas,
                    "descripcion": descripcion,
                    "color_descripcion": color_descripcion,
                    "precio": precio,
                    "color_precio": color_precio,
                    "energia": energia,
                    "escala_imagenes": parse_scale(escala_imagenes),
                    "imagen1_escala": parse_scale(imagen1_escala, 1.0),
                    "imagen1_offset_x": parse_offset(imagen1_offset_x),
                    "imagen1_offset_y": parse_offset(imagen1_offset_y),
                    "imagen1_modo": parse_image_mode(imagen1_modo),
                    "imagen1_custom_ancho": parse_dimension_percent(imagen1_custom_ancho),
                    "imagen1_custom_alto": parse_dimension_percent(imagen1_custom_alto),
                    "imagen2_escala": parse_scale(imagen2_escala, 1.0),
                    "imagen2_offset_x": parse_offset(imagen2_offset_x),
                    "imagen2_offset_y": parse_offset(imagen2_offset_y),
                    "imagen2_modo": parse_image_mode(imagen2_modo),
                    "imagen2_custom_ancho": parse_dimension_percent(imagen2_custom_ancho),
                    "imagen2_custom_alto": parse_dimension_percent(imagen2_custom_alto),
                    "imagen3_escala": parse_scale(imagen3_escala, 1.0),
                    "imagen3_offset_x": parse_offset(imagen3_offset_x),
                    "imagen3_offset_y": parse_offset(imagen3_offset_y),
                    "imagen3_modo": parse_image_mode(imagen3_modo),
                    "imagen3_custom_ancho": parse_dimension_percent(imagen3_custom_ancho),
                    "imagen3_custom_alto": parse_dimension_percent(imagen3_custom_alto),
                    "imagen4_escala": parse_scale(imagen4_escala, 1.0),
                    "imagen4_offset_x": parse_offset(imagen4_offset_x),
                    "imagen4_offset_y": parse_offset(imagen4_offset_y),
                    "imagen4_modo": parse_image_mode(imagen4_modo),
                    "imagen4_custom_ancho": parse_dimension_percent(imagen4_custom_ancho),
                    "imagen4_custom_alto": parse_dimension_percent(imagen4_custom_alto),
                },
                "files": {
                    "imagen1": _hash_bytes(imagen1_bytes),
                    "imagen2": _hash_bytes(imagen2_bytes),
                    "imagen3": _hash_bytes(imagen3_bytes),
                    "imagen4": _hash_bytes(imagen4_bytes),
                    "qr_imagen": _hash_bytes(qr_bytes),
                    "texto2_fondo": _hash_bytes(fondo_bytes),
                },
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()

    cached = _cache_get(cache_key)
    if cached is not None:
        return Response(content=cached, media_type="image/png")

    tmp_dir = Path(tempfile.mkdtemp(prefix="newhome_preview_"))

    def save_upload_bytes(data: Optional[bytes], filename: Optional[str]) -> Optional[str]:
        if not data:
            return None
        suffix = Path(filename or "upload").suffix or ".png"
        tmp_path = tmp_dir / f"{next(tempfile._get_candidate_names())}{suffix}"
        with tmp_path.open("wb") as f:
            f.write(data)
        return str(tmp_path)

    data = FlyerData(
        texto1=texto1,
        color_texto1=color_texto1,
        texto_marca=texto_marca,
        color_texto_marca=color_texto_marca,
        texto2=texto2,
        color_texto2=color_texto2,
        texto2_fondo=save_upload_bytes(fondo_bytes, getattr(texto2_fondo, "filename", None)),
        texto3=texto3,
        color_texto3=color_texto3,
        texto4=texto4,
        color_texto4=color_texto4,
        rebajado=parse_bool(rebajado, True),
        habitaciones=int(habitaciones),
        banos=int(banos),
        jardin=parse_bool(jardin),
        garaje=parse_bool(garaje),
        piscina=parse_bool(piscina),
        borde_caracteristicas=borde_caracteristicas,
        color_borde_caracteristicas=color_borde_caracteristicas,
        descripcion=descripcion,
        color_descripcion=color_descripcion,
        precio=precio,
        color_precio=color_precio,
        energia=energia,
        escala_imagenes=parse_scale(escala_imagenes),
        imagen1_escala=parse_scale(imagen1_escala, 1.0),
        imagen1_offset_x=parse_offset(imagen1_offset_x),
        imagen1_offset_y=parse_offset(imagen1_offset_y),
        imagen1_modo=parse_image_mode(imagen1_modo),
        imagen1_custom_ancho=parse_dimension_percent(imagen1_custom_ancho),
        imagen1_custom_alto=parse_dimension_percent(imagen1_custom_alto),
        imagen2_escala=parse_scale(imagen2_escala, 1.0),
        imagen2_offset_x=parse_offset(imagen2_offset_x),
        imagen2_offset_y=parse_offset(imagen2_offset_y),
        imagen2_modo=parse_image_mode(imagen2_modo),
        imagen2_custom_ancho=parse_dimension_percent(imagen2_custom_ancho),
        imagen2_custom_alto=parse_dimension_percent(imagen2_custom_alto),
        imagen3_escala=parse_scale(imagen3_escala, 1.0),
        imagen3_offset_x=parse_offset(imagen3_offset_x),
        imagen3_offset_y=parse_offset(imagen3_offset_y),
        imagen3_modo=parse_image_mode(imagen3_modo),
        imagen3_custom_ancho=parse_dimension_percent(imagen3_custom_ancho),
        imagen3_custom_alto=parse_dimension_percent(imagen3_custom_alto),
        imagen4_escala=parse_scale(imagen4_escala, 1.0),
        imagen4_offset_x=parse_offset(imagen4_offset_x),
        imagen4_offset_y=parse_offset(imagen4_offset_y),
        imagen4_modo=parse_image_mode(imagen4_modo),
        imagen4_custom_ancho=parse_dimension_percent(imagen4_custom_ancho),
        imagen4_custom_alto=parse_dimension_percent(imagen4_custom_alto),
        imagen1=save_upload_bytes(imagen1_bytes, getattr(imagen1, "filename", None)),
        imagen2=save_upload_bytes(imagen2_bytes, getattr(imagen2, "filename", None)),
        imagen3=save_upload_bytes(imagen3_bytes, getattr(imagen3, "filename", None)),
        imagen4=save_upload_bytes(imagen4_bytes, getattr(imagen4, "filename", None)),
        qr_imagen=save_upload_bytes(qr_bytes, getattr(qr_imagen, "filename", None)),
    )

    pdf_buffer = io.BytesIO()
    generate_pdf(data, pdf_buffer)
    pdf_buffer.seek(0)

    doc = fitz.open(stream=pdf_buffer.getvalue(), filetype="pdf")
    try:
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=120, alpha=False)
        png_bytes = pix.tobytes("png")
    finally:
        doc.close()

    _cache_set(cache_key, png_bytes)
    return Response(content=png_bytes, media_type="image/png")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))

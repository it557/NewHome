from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union, BinaryIO
import textwrap
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from PIL import Image


@dataclass
class FlyerData:
    texto1: str
    color_texto1: str
    texto_marca: str
    color_texto_marca: str
    texto2: str
    color_texto2: str
    texto2_fondo: Optional[str]
    texto3: str
    color_texto3: str
    texto4: str
    color_texto4: str
    rebajado: bool
    habitaciones: int
    banos: int
    jardin: bool
    garaje: bool
    piscina: bool
    borde_caracteristicas: str
    color_borde_caracteristicas: str
    descripcion: str
    color_descripcion: str
    precio: str
    color_precio: str
    energia: str
    escala_imagenes: float
    imagen1_escala: float
    imagen1_offset_x: float
    imagen1_offset_y: float
    imagen1_modo: str
    imagen1_custom_ancho: float
    imagen1_custom_alto: float
    imagen2_escala: float
    imagen2_offset_x: float
    imagen2_offset_y: float
    imagen2_modo: str
    imagen2_custom_ancho: float
    imagen2_custom_alto: float
    imagen3_escala: float
    imagen3_offset_x: float
    imagen3_offset_y: float
    imagen3_modo: str
    imagen3_custom_ancho: float
    imagen3_custom_alto: float
    imagen4_escala: float
    imagen4_offset_x: float
    imagen4_offset_y: float
    imagen4_modo: str
    imagen4_custom_ancho: float
    imagen4_custom_alto: float
    imagen1: Optional[str]
    imagen2: Optional[str]
    imagen3: Optional[str]
    imagen4: Optional[str]
    qr_imagen: Optional[str]


PAGE_W, PAGE_H = A4
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
LEGAL_TEXT = (
    "En cumplimiento del decreto de la Junta de Andalucía 218/2005 del 11 de octubre, "
    "se informa al cliente que los gastos notariales, registrales, ITP y otros gastos "
    "inherentes a la compraventa no están incluidos en la venta."
)


def _draw_image_fit(
    c: canvas.Canvas,
    path: str,
    x: float,
    y: float,
    w: float,
    h: float,
    scale: float = 1.0,
    offset_x: float = 0.0,
    offset_y: float = 0.0,
) -> None:
    with Image.open(path) as img:
        img_w, img_h = img.size
        img_ratio = img_w / img_h
        box_ratio = w / h

        if img_ratio > box_ratio:
            draw_w = w
            draw_h = w / img_ratio
        else:
            draw_h = h
            draw_w = h * img_ratio

    scale = max(0.01, min(scale, 1.0))
    draw_w *= scale
    draw_h *= scale

    extra_w = max(0.0, w - draw_w)
    extra_h = max(0.0, h - draw_h)
    offset_x = _safe_offset(offset_x)
    offset_y = _safe_offset(offset_y)

    draw_x = x + (w - draw_w) / 2 + (extra_w / 2) * (offset_x / 100)
    draw_y = y + (h - draw_h) / 2 + (extra_h / 2) * (offset_y / 100)
    c.drawImage(path, draw_x, draw_y, draw_w, draw_h, preserveAspectRatio=True, mask='auto')


def _draw_image_cover(
    c: canvas.Canvas,
    path: str,
    x: float,
    y: float,
    w: float,
    h: float,
    scale: float = 1.0,
) -> None:
    with Image.open(path) as img:
        img_w, img_h = img.size
        img_ratio = img_w / img_h
        box_ratio = w / h

        if img_ratio > box_ratio:
            draw_h = h
            draw_w = h * img_ratio
        else:
        
            draw_w = w
            draw_h = w / img_ratio

    scale = max(0.1, min(scale, 1.0))
    draw_w *= scale
    draw_h *= scale

    draw_x = x + (w - draw_w) / 2
    draw_y = y + (h - draw_h) / 2
    clip = c.beginPath()
    clip.rect(x, y, w, h)
    c.saveState()
    # Clip to the target box so oversize images are cropped to fit.
    c.clipPath(clip, stroke=0, fill=0)
    c.drawImage(path, draw_x, draw_y, draw_w, draw_h, preserveAspectRatio=True, mask='auto')
    c.restoreState()


def _draw_image_by_mode(
    c: canvas.Canvas,
    path: str,
    x: float,
    y: float,
    w: float,
    h: float,
    mode: str,
    scale: float,
    offset_x: float,
    offset_y: float,
    custom_w_pct: float,
    custom_h_pct: float,
) -> None:
    mode = _safe_image_mode(mode)
    with Image.open(path) as img:
        img_w, img_h = img.size
        img_ratio = img_w / img_h
        box_ratio = w / h

        if mode == "cover":
            if img_ratio > box_ratio:
                draw_h = h
                draw_w = h * img_ratio
            else:
                draw_w = w
                draw_h = w / img_ratio
        elif mode == "contain":
            if img_ratio > box_ratio:
                draw_w = w
                draw_h = w / img_ratio
            else:
                draw_h = h
                draw_w = h * img_ratio
        else:
            draw_w = w
            draw_h = h

    if mode == "custom":
        draw_w *= _safe_dimension_percent(custom_w_pct) / 100.0
        draw_h *= _safe_dimension_percent(custom_h_pct) / 100.0
    else:
        draw_scale = _safe_scale(scale)
        draw_w *= draw_scale
        draw_h *= draw_scale

    base_x = x + (w - draw_w) / 2
    base_y = y + (h - draw_h) / 2
    shift_x = abs(w - draw_w) / 2 * (_safe_offset(offset_x) / 100.0)
    shift_y = abs(h - draw_h) / 2 * (_safe_offset(offset_y) / 100.0)
    draw_x = base_x + shift_x
    draw_y = base_y + shift_y

    clip = c.beginPath()
    clip.rect(x, y, w, h)
    c.saveState()
    c.clipPath(clip, stroke=0, fill=0)
    c.drawImage(
        path,
        draw_x,
        draw_y,
        draw_w,
        draw_h,
        preserveAspectRatio=mode in {"contain", "cover"},
        mask='auto',
    )
    c.restoreState()


def generate_pdf(data: FlyerData, output_path: Union[str, BinaryIO]) -> None:
    c = canvas.Canvas(output_path, pagesize=A4)

    # Background
    c.setFillColor(colors.white)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # Top header bar
    header_h = 20 * mm
    c.setFillColor(colors.HexColor("#213502"))
    c.rect(0, PAGE_H - header_h, PAGE_W, header_h, fill=1, stroke=0)

    c.setFillColor(_safe_color(data.color_texto1, colors.white))
    c.setFont("Helvetica-Bold", 22)
    header_y = PAGE_H - header_h / 2 - 8
    c.drawString(12 * mm, header_y, data.texto1.upper() or "TEXTO 1")

    logo_path = ASSETS_DIR / "logo_new_home.png"
    if logo_path.exists():
        _draw_image_fit(c, str(logo_path), PAGE_W - 60 * mm, PAGE_H - header_h + 2 * mm, 48 * mm, header_h - 4 * mm)
    else:
        c.setFont("Helvetica-Bold", 20)
        c.setFillColor(_safe_color(data.color_texto_marca, colors.white))
        c.drawRightString(PAGE_W - 12 * mm, header_y, data.texto_marca or "TEXTO MARCA")

    # Subheader
    sub_h = 12 * mm
    if data.texto2_fondo:
        _draw_image_cover(c, data.texto2_fondo, 0, PAGE_H - header_h - sub_h, PAGE_W, sub_h)
    else:
        c.setFillColor(colors.HexColor("#c9e0cb"))
        c.rect(0, PAGE_H - header_h - sub_h, PAGE_W, sub_h, fill=1, stroke=0)

    c.setFillColor(_safe_color(data.color_texto2, colors.black))
    c.setFont("Helvetica-Bold", 14)
    sub_y = PAGE_H - header_h - sub_h / 2 - 6
    c.drawString(12 * mm, sub_y, data.texto2 or "TEXTO 2")

    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(_safe_color(data.color_texto3, colors.black))
    texto3 = _format_superscripts(data.texto3 or "TEXTO 3")
    c.drawRightString(PAGE_W - 12 * mm, sub_y, texto3)

    # Image grid area
    grid_top = PAGE_H - header_h - sub_h - 6 * mm
    grid_left = 10 * mm
    grid_w = PAGE_W - 20 * mm
    grid_h = 110 * mm
    gap = 4 * mm
    cell_w = (grid_w - gap) / 2
    cell_h = (grid_h - gap) / 2

    images = [data.imagen1, data.imagen2, data.imagen3, data.imagen4]
    image_configs = [
        (data.imagen1_escala, data.imagen1_offset_x, data.imagen1_offset_y, data.imagen1_modo, data.imagen1_custom_ancho, data.imagen1_custom_alto),
        (data.imagen2_escala, data.imagen2_offset_x, data.imagen2_offset_y, data.imagen2_modo, data.imagen2_custom_ancho, data.imagen2_custom_alto),
        (data.imagen3_escala, data.imagen3_offset_x, data.imagen3_offset_y, data.imagen3_modo, data.imagen3_custom_ancho, data.imagen3_custom_alto),
        (data.imagen4_escala, data.imagen4_offset_x, data.imagen4_offset_y, data.imagen4_modo, data.imagen4_custom_ancho, data.imagen4_custom_alto),
    ]
    for idx, img in enumerate(images):
        col = idx % 2
        row = idx // 2
        x = grid_left + col * (cell_w + gap)
        y = grid_top - (row + 1) * cell_h - row * gap
        c.setFillColor(colors.HexColor("#f1f1f1"))
        c.rect(x, y, cell_w, cell_h, fill=1, stroke=0)
        if img:
            individual_scale, offset_x, offset_y, mode, custom_w, custom_h = image_configs[idx]
            final_scale = _safe_scale(_safe_scale(data.escala_imagenes) * _safe_scale(individual_scale))
            _draw_image_by_mode(
                c,
                img,
                x,
                y,
                cell_w,
                cell_h,
                mode=mode,
                scale=final_scale,
                offset_x=offset_x,
                offset_y=offset_y,
                custom_w_pct=custom_w,
                custom_h_pct=custom_h,
            )

    # Rebajado band
    if data.rebajado:
        band_h = 14 * mm
        band_y = grid_top - grid_h / 2 - band_h / 2
        c.setFillColor(colors.Color(1, 0.7, 0.7, alpha=0.6))
        c.rect(0, band_y, PAGE_W, band_h, fill=1, stroke=0)
        c.setFillColor(_safe_color(data.color_texto4, colors.white))
        c.setFont("Helvetica-Bold", 30)
        c.drawCentredString(PAGE_W / 2, band_y + 4 * mm, data.texto4.upper() or "REBAJADO")

    # Icon row
    icon_row_y = grid_top - grid_h - 12 * mm
    c.setStrokeColor(_safe_color(data.color_borde_caracteristicas, colors.black))
    c.setLineWidth(1)
    if data.borde_caracteristicas == "dashed":
        c.setDash(4, 2)
    elif data.borde_caracteristicas == "dotted":
        c.setDash(1, 2)
    elif data.borde_caracteristicas == "double":
        c.setDash(2, 2)
    else:
        c.setDash()
    icon_row_h = 14 * mm
    c.setFillColor(colors.white)
    c.rect(10 * mm, icon_row_y, PAGE_W - 20 * mm, icon_row_h, fill=1, stroke=1)
    c.setDash()

    c.setFont("Helvetica", 9)
    icons = [
        ("Habitaciones", str(data.habitaciones), ASSETS_DIR / "dormitorio.png", colors.black),
        ("Baños", str(data.banos), ASSETS_DIR / "aseo.png", colors.black),
        ("Jardín", "✓" if data.jardin else "✗", ASSETS_DIR / "jardin.png", colors.HexColor("#16a34a") if data.jardin else colors.HexColor("#dc2626")),
        ("Garaje", "✓" if data.garaje else "✗", ASSETS_DIR / "garaje.png", colors.HexColor("#16a34a") if data.garaje else colors.HexColor("#dc2626")),
        ("Piscina", "✓" if data.piscina else "✗", ASSETS_DIR / "piscina.png", colors.HexColor("#16a34a") if data.piscina else colors.HexColor("#dc2626")),
    ]
    step = (PAGE_W - 20 * mm) / len(icons)
    for i, (label, value, icon_path, value_color) in enumerate(icons):
        cx = 10 * mm + step * (i + 0.5)
        icon_w = 9 * mm
        icon_h = 7 * mm
        icon_x = cx - icon_w / 2 - 4 * mm
        icon_y = icon_row_y + (icon_row_h - icon_h) / 2
        _draw_feature_icon(c, icon_path, icon_x, icon_y, icon_w, icon_h)
        c.setFillColor(value_color)
        c.setFont("Helvetica-Bold", 11)
        text_x = cx + 4 * mm
        text_y = icon_row_y + icon_row_h / 2 - 3
        c.drawString(text_x, text_y, value)

    # QR + description
    desc_top = icon_row_y - 10 * mm
    qr_size = 30 * mm
    qr_x = 10 * mm
    qr_y = desc_top - qr_size
    c.setFillColor(colors.HexColor("#f1f1f1"))
    c.rect(qr_x, qr_y, qr_size, qr_size, fill=1, stroke=0)
    if data.qr_imagen:
        _draw_image_fit(c, data.qr_imagen, qr_x, qr_y, qr_size, qr_size)

    desc_x = qr_x + qr_size + 6 * mm
    desc_w = PAGE_W - desc_x - 10 * mm
    desc_h = qr_size
    footer_top = 18 * mm
    footer_max_h = 18 * mm
    price_y = footer_top - 2 * mm
    desc_start_y = qr_y + desc_h - 2 * mm
    desc_max_h = max(0, desc_start_y - (price_y + 12 * mm))
    c.setFillColor(_safe_color(data.color_descripcion, colors.black))
    desc_font_size = 9 if len(data.descripcion or "") <= 1000 else 8
    line_h = 4.2 * mm if desc_font_size == 9 else 3.8 * mm
    c.setFont("Helvetica", desc_font_size)
    _draw_wrapped_text(c, data.descripcion, desc_x, desc_start_y, desc_w, line_h, desc_max_h)

    # Energy rating + price
    energy_x = 10 * mm
    energy_img_w = 30 * mm
    energy_img_h = 30 * mm

    energy_img_y = price_y + 10 * mm
    _draw_energy_image(c, energy_x, energy_img_y, energy_img_w, energy_img_h, data.energia)

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#3fa63f"))
    c.drawCentredString(energy_x + energy_img_w / 2, price_y + 8 * mm, "Precio")

    c.setFont("Helvetica-Bold", 80)
    c.setFillColor(_safe_color(data.color_precio, colors.HexColor("#b9cdb8")))
    c.drawRightString(PAGE_W - 12 * mm, price_y + 8 * mm, data.precio or "0€")

    c.setFont("Helvetica", 9)
    c.setFillColor(colors.black)
    _draw_wrapped_text(c, LEGAL_TEXT, desc_x, footer_top, desc_w, 4.2 * mm, footer_max_h)

    c.showPage()
    c.save()


def _draw_wrapped_text(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    w: float,
    line_h: float,
    max_h: float,
) -> None:
    if not text:
        return
    wrapped_lines = textwrap.wrap(
        text,
        width=87,
        break_long_words=True,
        break_on_hyphens=False,
        replace_whitespace=False,
        drop_whitespace=False,
    )
    curr_y = y
    max_lines = max(1, int(max_h // line_h))
    lines_used = 0
    for line in wrapped_lines:
        c.drawString(x, curr_y, line)
        curr_y -= line_h
        lines_used += 1
        if lines_used >= max_lines:
            return


def _draw_energy_label(c: canvas.Canvas, x: float, y: float, w: float, h: float, energia: str) -> None:
    levels = ["A", "B", "C", "D", "E", "F", "G"]
    bar_h = h / len(levels)
    colors_list = ["#3fa63f", "#69b83f", "#b2d13f", "#f2da3a", "#f5a43a", "#f0713a", "#e0453a"]

    for i, level in enumerate(levels):
        y0 = y + h - (i + 1) * bar_h
        c.setFillColor(colors.HexColor(colors_list[i]))
        c.rect(x, y0, w, bar_h, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x + 3, y0 + bar_h / 2 - 3, level)

    # Arrow indicator
    if energia and energia.upper() in levels:
        idx = levels.index(energia.upper())
        arrow_y = y + h - (idx + 0.5) * bar_h
        c.setFillColor(colors.red)
        c.setStrokeColor(colors.red)
        c.line(x + w, arrow_y, x + w + 10, arrow_y)
        c.line(x + w + 10, arrow_y, x + w + 6, arrow_y + 3)
        c.line(x + w + 10, arrow_y, x + w + 6, arrow_y - 3)


def _draw_energy_image(c: canvas.Canvas, x: float, y: float, w: float, h: float, energia: str) -> None:
    image_path = ASSETS_DIR / "certificado.png"
    if image_path.exists():
        _draw_image_fit(c, str(image_path), x, y, w, h)

    levels = ["A", "B", "C", "D", "E", "F", "G"]
    if energia and energia.upper() in levels:
        idx = levels.index(energia.upper())
        arrow_y = y + h - (idx + 0.5) * (h / len(levels))
        offsets = {
            "A": -2.2 * mm,
            "B": -1.4 * mm,
            "C": -1.4 * mm,
            "D": -1.0 * mm,
            "E": 0,
            "F": 1.2 * mm,
            "G": 1.8 * mm,
        }
        arrow_y += offsets.get(energia.upper(), 0)
        c.setFillColor(colors.red)
        c.setStrokeColor(colors.red)
        c.setLineWidth(2)
        # Arrow on the right, pointing left toward the image (closer + thicker)
        x_shift = 0
        if energia.upper() == "G":
            x_shift = 7
        head_right = x + w + 1 + x_shift
        arrow_left = x + w - 14 + x_shift
        tail_right = head_right + 6
        c.line(tail_right, arrow_y, arrow_left, arrow_y)
        c.line(arrow_left, arrow_y, head_right - 2, arrow_y + 3)
        c.line(arrow_left, arrow_y, head_right - 2, arrow_y - 3)
        c.setLineWidth(1)


def _safe_color(value: str, fallback) -> colors.Color:
    try:
        if isinstance(value, str) and value:
            return colors.HexColor(value)
    except Exception:
        return fallback
    return fallback


def _safe_scale(value: float) -> float:
    try:
        numeric = float(value)
    except Exception:
        return 0.93
    return max(0.01, min(1.0, numeric))


def _safe_offset(value: float) -> float:
    try:
        numeric = float(value)
    except Exception:
        return 0.0
    return max(-100.0, min(100.0, numeric))


def _safe_image_mode(value: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"contain", "cover", "expand", "custom"}:
        return normalized
    return "contain"


def _safe_dimension_percent(value: float) -> float:
    try:
        numeric = float(value)
    except Exception:
        return 100.0
    return max(1.0, min(200.0, numeric))


def _format_superscripts(value: str) -> str:
    if not value:
        return value
    return re.sub(r"m\s*\^?\s*2", "m²", value, flags=re.IGNORECASE)


def _draw_feature_icon(c: canvas.Canvas, path: Path, x: float, y: float, w: float, h: float) -> None:
    if path.exists():
        _draw_image_fit(c, str(path), x, y, w, h)


def _draw_house_icon(c: canvas.Canvas, x: float, y: float) -> None:
    c.setStrokeColor(colors.HexColor("#3fa63f"))
    c.setFillColor(colors.HexColor("#3fa63f"))
    c.setLineWidth(1)
    # Roof
    c.line(x + 2, y + 12, x + 10, y + 20)
    c.line(x + 18, y + 12, x + 10, y + 20)
    # Body
    c.rect(x + 4, y + 2, 12, 10, fill=0, stroke=1)

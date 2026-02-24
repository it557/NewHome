from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union, BinaryIO
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
    descripcion_tamano: float
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

    top_area_bottom_y = PAGE_H - header_h - sub_h

    footer_top = 18 * mm
    footer_max_h = 18 * mm
    price_y = footer_top - 2 * mm

    energy_x = 10 * mm
    energy_img_w = 30 * mm
    energy_img_h = 30 * mm
    energy_img_y = price_y + 10 * mm

    min_margin = 3 * mm
    bottom_area_top_y = energy_img_y + energy_img_h + 2 * mm
    available_height = top_area_bottom_y - bottom_area_top_y

    min_block_scale = 0.90
    max_block_scale = 1.08
    scale_step = 0.01
    desc_font_min = 8.0

    desc_font_size = _safe_description_font_size(data.descripcion_tamano)
    if len(data.descripcion or "") > 1000:
        desc_font_size = max(desc_font_min, desc_font_size - 1.0)

    def compute_layout(scale: float, spacing_ratio: float, font_size: float) -> dict:
        top_gap = 6 * mm * spacing_ratio
        grid_h = 110 * mm * scale
        grid_w = PAGE_W - 20 * mm
        grid_gap = 4 * mm
        icon_row_h = 14 * mm * scale
        grid_to_icons_gap = 12 * mm * spacing_ratio
        icons_to_desc_gap = 10 * mm * spacing_ratio
        qr_size = 30 * mm * scale
        desc_x = 10 * mm + qr_size + 6 * mm
        desc_w = PAGE_W - desc_x - 10 * mm
        line_h = max(3.2 * mm, font_size * 1.3)
        desc_lines = _wrap_text_to_width(c, data.descripcion or "", "Helvetica", font_size, desc_w)
        desc_h = len(desc_lines) * line_h
        desc_row_h = max(qr_size, desc_h + 2 * mm)
        block_h = top_gap + grid_h + grid_to_icons_gap + icon_row_h + icons_to_desc_gap + desc_row_h
        remaining = available_height - block_h
        return {
            "scale": scale,
            "top_gap": top_gap,
            "grid_h": grid_h,
            "grid_w": grid_w,
            "grid_gap": grid_gap,
            "icon_row_h": icon_row_h,
            "grid_to_icons_gap": grid_to_icons_gap,
            "icons_to_desc_gap": icons_to_desc_gap,
            "qr_size": qr_size,
            "desc_x": desc_x,
            "desc_w": desc_w,
            "desc_font_size": font_size,
            "line_h": line_h,
            "desc_lines": desc_lines,
            "desc_h": desc_h,
            "desc_row_h": desc_row_h,
            "block_h": block_h,
            "remaining": remaining,
        }

    def scale_range(start: float, end: float, step: float) -> list[float]:
        values = []
        current = start
        while current >= end - 1e-9:
            values.append(round(current, 2))
            current -= step
        return values

    base_layout = compute_layout(1.0, 1.0, desc_font_size)
    prefer_scale_up = base_layout["remaining"] > 20 * mm
    candidate_scales = scale_range(max_block_scale if prefer_scale_up else 1.0, min_block_scale, scale_step)

    layout = None
    for scale in candidate_scales:
        candidate = compute_layout(scale, 1.0, desc_font_size)
        if candidate["remaining"] >= 2 * min_margin:
            layout = candidate
            break

    if layout is None:
        for scale in scale_range(1.0, min_block_scale, scale_step):
            candidate = compute_layout(scale, 0.88, desc_font_size)
            if candidate["remaining"] >= 2 * min_margin:
                layout = candidate
                break

    if layout is None:
        font_size = desc_font_size
        while font_size >= desc_font_min:
            candidate = compute_layout(min_block_scale, 0.82, font_size)
            if candidate["remaining"] >= 2 * min_margin:
                layout = candidate
                break
            font_size -= 0.5

    if layout is None:
        layout = compute_layout(min_block_scale, 0.80, desc_font_min)
        fixed_part_h = (
            layout["top_gap"]
            + layout["grid_h"]
            + layout["grid_to_icons_gap"]
            + layout["icon_row_h"]
            + layout["icons_to_desc_gap"]
        )
        max_desc_row_h = max(layout["qr_size"], available_height - fixed_part_h - 2 * min_margin)
        max_desc_h = max(0.0, max_desc_row_h - 2 * mm)
        max_lines = max(1, int(max_desc_h // layout["line_h"]))
        truncated = _truncate_lines_to_count(
            c,
            layout["desc_lines"],
            max_lines,
            "Helvetica",
            layout["desc_font_size"],
            layout["desc_w"],
        )
        used_desc_h = len(truncated) * layout["line_h"]
        layout["desc_lines"] = truncated
        layout["desc_h"] = used_desc_h
        layout["desc_row_h"] = max(layout["qr_size"], used_desc_h + 2 * mm)
        layout["block_h"] = fixed_part_h + layout["desc_row_h"]
        layout["remaining"] = available_height - layout["block_h"]

    remaining = max(0.0, layout["remaining"])
    if remaining >= 2 * min_margin:
        margin_top = remaining / 2
    else:
        margin_top = max(0.0, remaining / 2)

    grid_top = top_area_bottom_y - margin_top - layout["top_gap"]
    block_bottom_y = grid_top - (
        layout["grid_h"]
        + layout["grid_to_icons_gap"]
        + layout["icon_row_h"]
        + layout["icons_to_desc_gap"]
        + layout["desc_row_h"]
    )
    min_bottom_limit = bottom_area_top_y + min_margin
    if block_bottom_y < min_bottom_limit:
        grid_top += min_bottom_limit - block_bottom_y

    # Image grid area
    grid_left = 10 * mm
    grid_w = layout["grid_w"]
    grid_h = layout["grid_h"]
    gap = layout["grid_gap"]
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
        band_h = 14 * mm * layout["scale"]
        band_y = grid_top - grid_h / 2 - band_h / 2
        c.setFillColor(colors.Color(1, 0.7, 0.7, alpha=0.6))
        c.rect(0, band_y, PAGE_W, band_h, fill=1, stroke=0)
        c.setFillColor(_safe_color(data.color_texto4, colors.white))
        c.setFont("Helvetica-Bold", max(24, 30 * layout["scale"]))
        c.drawCentredString(PAGE_W / 2, band_y + 3.6 * mm * layout["scale"], data.texto4.upper() or "REBAJADO")

    # Icon row
    icon_row_y = grid_top - grid_h - layout["grid_to_icons_gap"]
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
    icon_row_h = layout["icon_row_h"]
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
        icon_w = 9 * mm * layout["scale"]
        icon_h = 7 * mm * layout["scale"]
        icon_x = cx - icon_w / 2 - 4 * mm
        icon_y = icon_row_y + (icon_row_h - icon_h) / 2
        _draw_feature_icon(c, icon_path, icon_x, icon_y, icon_w, icon_h)
        c.setFillColor(value_color)
        c.setFont("Helvetica-Bold", max(9, 11 * layout["scale"]))
        text_x = cx + 4 * mm
        text_y = icon_row_y + icon_row_h / 2 - 2.5 * layout["scale"]
        c.drawString(text_x, text_y, value)

    # QR + description
    desc_top = icon_row_y - layout["icons_to_desc_gap"]
    qr_size = layout["qr_size"]
    qr_x = 10 * mm
    qr_y = desc_top - qr_size
    c.setFillColor(colors.HexColor("#f1f1f1"))
    c.rect(qr_x, qr_y, qr_size, qr_size, fill=1, stroke=0)
    if data.qr_imagen:
        _draw_image_fit(c, data.qr_imagen, qr_x, qr_y, qr_size, qr_size)

    desc_x = layout["desc_x"]
    desc_w = layout["desc_w"]
    desc_start_y = desc_top - 2 * mm
    desc_max_h = max(0, layout["desc_row_h"] - 2 * mm)
    c.setFillColor(_safe_color(data.color_descripcion, colors.black))
    c.setFont("Helvetica", layout["desc_font_size"])
    _draw_wrapped_lines(c, layout["desc_lines"], desc_x, desc_start_y, layout["line_h"], desc_max_h)

    # Energy rating + price
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
    font_name = c._fontname
    font_size = c._fontsize
    lines = _wrap_text_to_width(c, text, font_name, font_size, w)
    _draw_wrapped_lines(c, lines, x, y, line_h, max_h)


def _draw_wrapped_lines(
    c: canvas.Canvas,
    lines: list[str],
    x: float,
    y: float,
    line_h: float,
    max_h: float,
) -> None:
    if not lines:
        return
    curr_y = y
    max_lines = max(1, int(max_h // line_h))
    for index, line in enumerate(lines):
        if index >= max_lines:
            break
        c.drawString(x, curr_y, line)
        curr_y -= line_h


def _measure_wrapped_text_height(
    c: canvas.Canvas,
    text: str,
    font_name: str,
    font_size: float,
    max_width: float,
    line_height: float,
) -> float:
    lines = _wrap_text_to_width(c, text, font_name, font_size, max_width)
    return len(lines) * line_height


def _wrap_text_to_width(
    c: canvas.Canvas,
    text: str,
    font_name: str,
    font_size: float,
    max_width: float,
) -> list[str]:
    if not text:
        return []

    def split_long_word(word: str) -> list[str]:
        chunks: list[str] = []
        current = ""
        for char in word:
            probe = current + char
            if c.stringWidth(probe, font_name, font_size) <= max_width or not current:
                current = probe
            else:
                chunks.append(current)
                current = char
        if current:
            chunks.append(current)
        return chunks

    lines: list[str] = []
    paragraphs = str(text).replace("\r", "").split("\n")
    for paragraph in paragraphs:
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = ""
        for word in words:
            probe = word if not current else f"{current} {word}"
            if c.stringWidth(probe, font_name, font_size) <= max_width:
                current = probe
                continue

            if current:
                lines.append(current)
                current = ""

            if c.stringWidth(word, font_name, font_size) <= max_width:
                current = word
            else:
                chunks = split_long_word(word)
                if chunks:
                    lines.extend(chunks[:-1])
                    current = chunks[-1]

        if current:
            lines.append(current)

    return lines


def _truncate_lines_to_count(
    c: canvas.Canvas,
    lines: list[str],
    max_lines: int,
    font_name: str,
    font_size: float,
    max_width: float,
) -> list[str]:
    if max_lines <= 0:
        return []
    if len(lines) <= max_lines:
        return lines

    clipped = lines[:max_lines]
    last = clipped[-1].rstrip()
    ellipsis = "…"
    while last and c.stringWidth(f"{last}{ellipsis}", font_name, font_size) > max_width:
        last = last[:-1]
    clipped[-1] = f"{last}{ellipsis}" if last else ellipsis
    return clipped


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


def _safe_description_font_size(value: float) -> float:
    try:
        numeric = float(value)
    except Exception:
        return 9.0
    return max(8.0, min(14.0, numeric))


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

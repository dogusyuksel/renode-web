#!/usr/bin/env python3
"""
generate_full_report.py

Usage:
  python3 generate_full_report.py \
      --connections connections.json \
      --diagram structure.png \
      --log log.txt \
      --out report.pdf

Dependencies:
  pip install reportlab matplotlib pillow
"""

import argparse, os, json, re
from io import BytesIO
from datetime import datetime
from PIL import Image as PILImage
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image,
    Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

# Font
try:
    pdfmetrics.registerFont(TTFont("DejaVuSansMono", "DejaVuSansMono.ttf"))
    MONO_FONT = "DejaVuSansMono"
except Exception:
    MONO_FONT = "Courier"

PAGE_WIDTH, PAGE_HEIGHT = A4
LEFT_MARGIN = RIGHT_MARGIN = TOP_MARGIN = BOTTOM_MARGIN = 2 * cm
USABLE_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
USABLE_HEIGHT = PAGE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def ensure_list(x):
    if isinstance(x, list): return x
    if x is None: return []
    return [x]

def peripheral_family(name: str):
    if not name: return ""
    s = name.strip().lower()
    m = re.match(r"([a-zA-Z_]+)", s)
    return m.group(1) if m else s

def make_table(title, headers, rows):
    """Generic table generator."""
    data = [headers] + rows
    col_widths = [max(2, len(h)) * 4 for h in headers]
    table = Table(data, colWidths=[3*cm, 5*cm, 4*cm, 3*cm, 3*cm][:len(headers)])
    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("BOX", (0, 0), (-1, -1), 0.25, colors.grey),
    ])
    table.setStyle(style)
    return table

def make_centered_image(img_path, max_w=USABLE_WIDTH, max_h=USABLE_HEIGHT*0.6):
    """Centers image, resizes only if too big."""
    img = PILImage.open(img_path)
    w_px, h_px = img.size
    dpi = img.info.get("dpi", (96, 96))[0] or 96
    w_pt, h_pt = w_px * 72.0 / dpi, h_px * 72.0 / dpi
    scale = min(1.0, max_w / w_pt, max_h / h_pt)
    w, h = w_pt * scale, h_pt * scale
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    rl_img = Image(buf, width=w, height=h)
    rl_img.hAlign = "CENTER"
    return rl_img


# ----------------------------------------------------------------------
# Log parsing and styling
# ----------------------------------------------------------------------
LOG_RE = re.compile(r"^(\d{1,2}:\d{2}:\d{2}\.\d+)\s*\[([^\]]+)\]\s*(.*)$")

def parse_logs(text):
    parsed = []
    for line in text.splitlines():
        m = LOG_RE.match(line)
        if m:
            ts, lvl, msg = m.groups()
            parsed.append((ts, lvl.upper(), msg))
        else:
            parsed.append((None, None, line))
    return parsed

def level_color(level):
    level = (level or "").upper()
    return {
        "INFO": "#2E7D32",
        "WARNING": "#ff4d94",
        "NOISY": "#1565C0",
        "ERROR": "#C62828",
        "DEBUG": "#616161",
        "FATAL": "#8B0000",
    }.get(level, "#424242")

# ----------------------------------------------------------------------
# Main PDF builder
# ----------------------------------------------------------------------
def build_pdf(connections_path, diagram_path, log_path, out_pdf):
    connections = load_json(connections_path).get("connections", [])
    mcu = load_json(connections_path).get("mcu", "unknown")

    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        log_text = f.read()
    logs = parse_logs(log_text)

    # PDF setup
    doc = SimpleDocTemplate(out_pdf, pagesize=A4,
                            rightMargin=RIGHT_MARGIN, leftMargin=LEFT_MARGIN,
                            topMargin=TOP_MARGIN, bottomMargin=BOTTOM_MARGIN)
    styles = getSampleStyleSheet()
    story = []

    # Cover page
    title_style = ParagraphStyle("Title", parent=styles["Title"], fontSize=28,
                                 alignment=1, textColor=colors.HexColor("#003366"))
    
    print(mcu)
    story += [
        Spacer(1, 3*cm),
        Paragraph("FW Test Report", title_style),
        Spacer(1, 0.5*cm),
        Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]),
        Spacer(1, 0.2*cm),
        Paragraph(f"MCU: <b>{mcu}</b>", styles["Normal"]),
        Spacer(1, 2*cm),
    ]

    # 2. Tested peripherals
    story.append(Paragraph("Tested Peripherals", styles["Heading2"]))
    rows = [[str(i+1), c.get("peripheral",""), c.get("sensor",""),
             c.get("port",""), str(c.get("pin",""))] for i,c in enumerate(connections)]
    story.append(make_table("Tested", ["#", "Peripheral", "Sensor", "Port", "Pin"], rows))
    story.append(PageBreak())

    # 4. System Diagram
    story.append(Paragraph("System Diagram", styles["Heading2"]))
    try:
        story.append(make_centered_image(diagram_path))
    except Exception as e:
        story.append(Paragraph(f"⚠️ Diagram could not be loaded: {e}", styles["Normal"]))
    story.append(PageBreak())

    # 5. Logs
    story.append(Paragraph("Logs", styles["Heading2"]))
    story.append(Spacer(1, 0.3*cm))
    for ts, lvl, msg in logs:
        if lvl and lvl.upper() in ("RENODE"):  # skip renode related things
            continue
        ts_html = f"<font color='#888888'>{ts or ''}</font>"
        lvl_html = f"<font color='{level_color(lvl)}'><b>[{lvl or ''}]</b></font>"
        esc_msg = (msg or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        html = f"{ts_html} {lvl_html} <font face='{MONO_FONT}' size='8'>{esc_msg}</font>"
        story.append(Paragraph(html, ParagraphStyle("LogLine", fontSize=9, leading=11)))
    # done

    doc.build(story)
    print(f"PDF generated: {out_pdf}")

# ----------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--connections", required=True)
    p.add_argument("--diagram", required=True)
    p.add_argument("--log", required=True)
    p.add_argument("--out", default="report.pdf")
    args = p.parse_args()

    build_pdf(args.connections, args.diagram, args.log, args.out)

if __name__ == "__main__":
    main()

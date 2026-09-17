import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_JUSTIFY

from app.core.config import settings

REPORTS_DIR = Path(settings.reports_dir)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
FONT_DIR = Path(__file__).resolve().parents[1] / 'assets' / 'fonts'
pdfmetrics.registerFont(TTFont('DejaVuSans', str(FONT_DIR / 'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', str(FONT_DIR / 'DejaVuSans-Bold.ttf')))

def _build_chart(data: list[dict[str, Any]], chart_type: Literal['bar', 'line', 'none']) -> io.BytesIO | None:
    if not data or chart_type == 'none':
        return None

    keys = list(data[0].keys())
    numeric_keys = [k for k in keys if all(isinstance(row.get(k), (int, float)) for row in data)]
    label_keys = [k for k in keys if k not in numeric_keys]
    if not numeric_keys or not label_keys:
        return None

    label_key, value_key = label_keys[0], numeric_keys[0]
    labels = [str(row[label_key]) for row in data]
    values = [row[value_key] for row in data]

    fig, ax = plt.subplots(figsize=(6, 3.5))
    if chart_type == 'line':
        ax.plot(labels, values, marker='o')
    else:
        ax.bar(labels, values)
    ax.set_ylabel(value_key)
    plt.xticks(rotation=45, ha='right')
    ax.set_axisbelow(True)
    ax.grid(True, axis='y', linestyle='--', alpha=0.5)
    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=150)
    plt.close(fig)
    buffer.seek(0)
    return buffer

def generate_report(title: str, data: list[dict[str, Any]], summary: str, chart_type: Literal['bar', 'line', 'none'] = 'bar') -> str:
    filename = f"report_{datetime.now(timezone.utc):%Y-%m-%d_%H-%M-%S}.pdf"
    file_path = REPORTS_DIR / filename

    styles = getSampleStyleSheet()
    styles['Title'].fontName = 'DejaVuSans-Bold'
    styles['Heading2'].fontName = 'DejaVuSans-Bold'
    styles['BodyText'].fontName = 'DejaVuSans'
    styles['BodyText'].alignment = TA_JUSTIFY
    doc = SimpleDocTemplate(str(file_path), pagesize=A4)
    story = [Paragraph(title, styles['Title']), Spacer(1, 0.5 * cm)]

    chart_buffer = _build_chart(data, chart_type)
    if chart_buffer is not None:
        story.append(Image(chart_buffer, width=15 * cm, height=8.5 * cm))
        story.append(Spacer(1, 0.5 * cm))

    if data:
        headers = list(data[0].keys())
        table_data = [headers] + [[str(row.get(h, '')) for h in headers] for row in data]
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSans-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'DejaVuSans'),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph('Висновки', styles['Heading2']))
    story.append(Paragraph(summary, styles['BodyText']))

    doc.build(story)

    return str(file_path)

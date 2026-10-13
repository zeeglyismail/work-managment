"""Monthly work report rendered with reportlab."""

import io
from collections import defaultdict
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from xml.sax.saxutils import escape

from .models import Entry
from .queries import fmt_minutes

INK = colors.HexColor("#111827")
MUTED = colors.HexColor("#6b7280")
ACCENT = colors.HexColor("#4f46e5")
RULE = colors.HexColor("#e5e7eb")
ZEBRA = colors.HexColor("#f9fafb")

_styles = getSampleStyleSheet()
H1 = ParagraphStyle("h1", parent=_styles["Title"], alignment=0, fontSize=20, leading=24, textColor=INK, spaceAfter=4)
H2 = ParagraphStyle("h2", parent=_styles["Heading2"], fontSize=12, textColor=INK, spaceBefore=10, spaceAfter=6)
SUB = ParagraphStyle("sub", parent=_styles["Normal"], fontSize=9, textColor=MUTED)
CELL = ParagraphStyle("cell", parent=_styles["Normal"], fontSize=8.5, leading=11, textColor=INK)
CELL_MUTED = ParagraphStyle("cellm", parent=CELL, textColor=MUTED, fontSize=7.5, leading=9.5)
CELL_R = ParagraphStyle("cellr", parent=CELL, alignment=TA_RIGHT)
KPI_VAL = ParagraphStyle("kpiv", parent=_styles["Normal"], fontSize=16, leading=19, textColor=INK, fontName="Helvetica-Bold")
KPI_LBL = ParagraphStyle("kpil", parent=_styles["Normal"], fontSize=8, textColor=MUTED)


def _table(rows, col_widths, header=True, align_right_cols=()):
    t = Table(rows, colWidths=col_widths, repeatRows=1 if header else 0)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE),
    ]
    if header:
        style += [
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("TEXTCOLOR", (0, 0), (-1, 0), MUTED),
            ("LINEBELOW", (0, 0), (-1, 0), 0.8, INK),
        ]
        for i in range(1, len(rows)):
            if i % 2 == 0:
                style.append(("BACKGROUND", (0, i), (-1, i), ZEBRA))
    for c in align_right_cols:
        style.append(("ALIGN", (c, 0), (c, -1), "RIGHT"))
    t.setStyle(TableStyle(style))
    return t


def render_month_report(
    month: str, entries: list[Entry], owner_name: str, generated_at: datetime
) -> bytes:
    month_label = datetime.strptime(month, "%Y-%m").strftime("%B %Y")
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"Work report - {month_label}",
        author=owner_name or "Worklog",
    )
    width = doc.width

    finished = [e for e in entries if e.ended_at is not None]
    total = sum(e.minutes() for e in finished)
    days: dict = defaultdict(list)
    for e in finished:
        days[e.started_at.date()].append(e)
    by_project: dict[str, int] = defaultdict(int)
    for e in finished:
        by_project[e.project.name if e.project else "No project"] += e.minutes()
    avg = total // len(days) if days else 0

    story = []
    who = f"{escape(owner_name)} &middot; " if owner_name else ""
    story.append(Paragraph(f"Work report &mdash; {month_label}", H1))
    story.append(Paragraph(
        f"{who}Generated {generated_at.strftime('%d %b %Y, %H:%M')}", SUB
    ))
    story.append(Spacer(1, 8 * mm))

    kpis = [
        (fmt_minutes(total), "Total time"),
        (str(len(days)), "Days worked"),
        (str(len(finished)), "Entries"),
        (fmt_minutes(avg), "Average per working day"),
    ]
    kpi_table = Table(
        [[Paragraph(v, KPI_VAL) for v, _ in kpis], [Paragraph(lbl, KPI_LBL) for _, lbl in kpis]],
        colWidths=[width / 4] * 4,
    )
    kpi_table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 2, ACCENT),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(kpi_table)

    if not finished:
        story.append(Spacer(1, 10 * mm))
        story.append(Paragraph("No completed work was logged this month.", CELL))
        doc.build(story)
        return buf.getvalue()

    # Time per project
    rows = [["Project", "Time", "Share"]]
    for name, mins in sorted(by_project.items(), key=lambda kv: -kv[1]):
        rows.append([Paragraph(escape(name), CELL), fmt_minutes(mins), f"{mins * 100 / total:.0f}%"])
    story.append(KeepTogether([
        Paragraph("Time by project", H2),
        _table(rows, [width * 0.6, width * 0.2, width * 0.2], align_right_cols=(1, 2)),
    ]))

    # Daily summary
    rows = [["Date", "First start", "Last end", "Entries", "Time"]]
    for day in sorted(days):
        items = days[day]
        rows.append([
            day.strftime("%a %d %b"),
            min(e.started_at for e in items).strftime("%H:%M"),
            max(e.ended_at for e in items).strftime("%H:%M"),
            str(len(items)),
            fmt_minutes(sum(e.minutes() for e in items)),
        ])
    rows.append(["", "", "", "Total", fmt_minutes(total)])
    daily = _table(rows, [width * 0.28, width * 0.18, width * 0.18, width * 0.16, width * 0.2],
                   align_right_cols=(3, 4))
    daily.setStyle(TableStyle([
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("LINEABOVE", (0, -1), (-1, -1), 0.8, INK),
    ]))
    story.append(Paragraph("Daily summary", H2))
    story.append(daily)

    # Detailed log
    rows = [["Date", "Time", "Project", "Work done", "Duration"]]
    for e in finished:
        work = [Paragraph(escape(e.title), CELL)]
        if e.notes.strip():
            work.append(Paragraph(escape(e.notes.strip()).replace("\n", "<br/>"), CELL_MUTED))
        rows.append([
            e.started_at.strftime("%d %b"),
            f"{e.started_at:%H:%M}-{e.ended_at:%H:%M}",
            Paragraph(escape(e.project.name) if e.project else "&mdash;", CELL),
            work,
            Paragraph(fmt_minutes(e.minutes()), CELL_R),
        ])
    story.append(Paragraph("Detailed log", H2))
    story.append(_table(
        rows,
        [width * 0.1, width * 0.15, width * 0.18, width * 0.43, width * 0.14],
        align_right_cols=(4,),
    ))

    def _footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(doc_.leftMargin, 9 * mm, f"Work report - {month_label}")
        canvas.drawRightString(A4[0] - doc_.rightMargin, 9 * mm, f"Page {doc_.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()

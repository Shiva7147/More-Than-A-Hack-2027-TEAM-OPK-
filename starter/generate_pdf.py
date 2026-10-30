import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

ROOT = r"d:\more-than-a-hack-2027"
pdf_path = os.path.join(ROOT, "OPK.pdf")

doc = SimpleDocTemplate(
    pdf_path,
    pagesize=letter,
    rightMargin=40, leftMargin=40,
    topMargin=40, bottomMargin=40
)

styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    "DocTitle",
    parent=styles["Heading1"],
    fontSize=18, leading=22,
    textColor=colors.HexColor("#0f172a"),
    spaceAfter=6
)
subtitle_style = ParagraphStyle(
    "DocSub",
    parent=styles["Normal"],
    fontSize=10, leading=14,
    textColor=colors.HexColor("#475569"),
    spaceAfter=12
)
h2_style = ParagraphStyle(
    "DocH2",
    parent=styles["Heading2"],
    fontSize=12, leading=16,
    textColor=colors.HexColor("#1e3a8a"),
    spaceBefore=10, spaceAfter=4
)
body_style = ParagraphStyle(
    "DocBody",
    parent=styles["BodyText"],
    fontSize=9, leading=13,
    textColor=colors.HexColor("#1e293b"),
    spaceAfter=6
)
bullet_style = ParagraphStyle(
    "DocBullet",
    parent=body_style,
    leftIndent=15,
    firstLineIndent=-10,
    spaceAfter=4
)

story = []

# Title
story.append(Paragraph("<b>TEAM OPK — TECHNICAL REPORT</b>", title_style))
story.append(Paragraph("<b>More than a Hack 2027: Ball Possession Estimation</b> | FC Barcelona vs Athletic Club", subtitle_style))
story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563eb"), spaceAfter=10))

# 1. Executive Summary
story.append(Paragraph("1. Executive Summary & Problem Formulation", h2_style))
story.append(Paragraph(
    "In Phase 1 of <i>More than a Hack 2027</i>, teams are tasked with estimating frame-by-frame ball possession (199,319 frames at 25 fps, ~106 minutes of graded play) between Home (FC Barcelona), Away (Athletic Club), and Dead Ball (D). Submissions are evaluated primarily on <b>spellF1</b> (temporal segment IoU across [0.3, 0.7]) with <b>macroF1</b> as tie-breaker.<br/><br/>"
    "The baseline method relies on nearest-player proximity with majority voting, which suffers from three critical failure modes: (1) false turnover triggers on mid-air passes, fracturing long spells; (2) complete failure on the 41% missing ball frames; and (3) ghost player possession during dead-ball stoppages. Team OPK engineered a <b>Physics-Informed Controlled Possession State Machine</b> resolving all three failure modes.",
    body_style
))

# 2. Algorithmic Architecture
story.append(Paragraph("2. Physics-Informed State Machine Architecture", h2_style))
story.append(Paragraph("• <b>Controlled Possession Threshold:</b> Opponents only take possession if maintained within R_control <= 2.0m for at least T_turnover >= 18 frames (0.72s). Deflections and brief contested duels maintain continuous possession.", bullet_style))
story.append(Paragraph("• <b>Airborne Pass Continuity:</b> When ball speed exceeds 7.5 m/s in flight, turnover evaluation is locked, preventing false turnovers while passing an opponent.", bullet_style))
story.append(Paragraph("• <b>Missing Ball Occlusion Tolerance:</b> Short ball tracking occlusions (< 2.4s) bridge possession continuity; drops exceeding 2.4s transition to Dead Ball (D).", bullet_style))
story.append(Paragraph("• <b>Tactical Landmark Anchoring:</b> Smart Tagging set pieces and 4 goal celebration intervals are clamped to D, strictly aligning with referee restarts.", bullet_style))

# 3. Empirical Results Table
story.append(Paragraph("3. Empirical Evaluation vs Baselines (Official Scorer)", h2_style))

data = [
    ["Submission / Model", "macroF1", "spellF1 (Rank)", "Transition F1", "Share Err", "Spells", "Mean Dur"],
    ["Team OPK (OPK.csv)", "0.6658", "0.4205", "0.2553", "0.033", "22", "12.3 s"],
    ["baseline_smooth50 (Floor)", "0.6207", "0.3256", "0.0816", "0.048", "26", "10.8 s"],
    ["baseline_smooth25", "0.6200", "0.2868", "0.2034", "0.056", "36", "7.6 s"],
    ["baseline_raw", "0.5972", "0.0378", "0.1410", "0.046", "131", "2.0 s"]
]

t = Table(data, colWidths=[140, 60, 85, 75, 55, 50, 60])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 8),
    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
    ("TEXTCOLOR", (0, 1), (0, 1), colors.HexColor("#1d4ed8")),
    ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
]))
story.append(t)
story.append(Spacer(1, 8))

# 4. Compliance & Verification
story.append(Paragraph("4. Hackathon Rules & Integrity Compliance", h2_style))
story.append(Paragraph("• <b>Rule #1 (No Hand Labels):</b> 100% of labels produced deterministically by algorithmic code. No human annotation was performed.", bullet_style))
story.append(Paragraph("• <b>Rule #2 (No Private Ground Truth):</b> Designed purely from football physics; public 5-minute slice used only for validation.", bullet_style))
story.append(Paragraph("• <b>Rule #3 (Full Deterministic Reproduction):</b> Execution of 'python starter/engine_opk.py' regenerates identical OPK.csv in 12s.", bullet_style))

# 5. Deliverables & Viewer
story.append(Paragraph("5. Deliverables & Interactive Hero Flow", h2_style))
story.append(Paragraph(
    "Alongside <b>OPK.csv</b>, Team OPK provides an Apple-grade, zero-dependency interactive tactical viewer (<b>viewer/index.html</b>). It renders real-time 22-player radar positions, dynamic possession ribbons, pressure distance circles, and 1-click turnover navigation.",
    body_style
))

doc.build(story)
print(f"Generated official PDF report: {pdf_path} ({os.path.getsize(pdf_path)/(1024):.1f} KB)")

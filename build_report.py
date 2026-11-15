from pathlib import Path
from html.parser import HTMLParser
import re

import markdown
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Preformatted, Image, PageBreak
)

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "REPORT_DRAFT.md"
OUTPUT = ROOT / "23BCS209_Prudhvi_Raj_Kumar_Pipelines.pdf"
EVIDENCE = ROOT / "evidence"

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="ReportTitle", parent=styles["Title"],
    fontSize=17, leading=21, alignment=TA_CENTER, spaceAfter=12
))
styles.add(ParagraphStyle(
    name="H1x", parent=styles["Heading1"],
    fontSize=13, leading=16, spaceBefore=9, spaceAfter=5
))
styles.add(ParagraphStyle(
    name="H2x", parent=styles["Heading2"],
    fontSize=10.5, leading=13, spaceBefore=7, spaceAfter=4
))
styles.add(ParagraphStyle(
    name="Bodyx", parent=styles["BodyText"],
    fontSize=8.5, leading=11, spaceAfter=5
))
styles.add(ParagraphStyle(
    name="Smallx", parent=styles["BodyText"],
    fontSize=7.5, leading=9
))
styles.add(ParagraphStyle(
    name="Codex", fontName="Courier",
    fontSize=7, leading=8.5, leftIndent=5,
    rightIndent=5, spaceBefore=3, spaceAfter=6
))

class Node:
    def __init__(self, tag, attrs=None):
        self.tag = tag
        self.attrs = dict(attrs or [])
        self.children = []

class TreeParser(HTMLParser):
    void = {"br", "hr", "img"}
    def __init__(self):
        super().__init__()
        self.root = Node("root")
        self.stack = [self.root]
    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in self.void:
            self.stack.append(node)
    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, 0, -1):
            if self.stack[i].tag == tag:
                self.stack = self.stack[:i]
                break
    def handle_data(self, data):
        self.stack[-1].children.append(data)

def inline(nodes):
    out = ""
    for n in nodes:
        if isinstance(n, str):
            out += (n.replace("&", "&amp;")
                     .replace("<", "&lt;").replace(">", "&gt;"))
        elif n.tag in ("strong", "b"):
            out += "<b>" + inline(n.children) + "</b>"
        elif n.tag in ("em", "i"):
            out += "<i>" + inline(n.children) + "</i>"
        elif n.tag == "code":
            out += '<font name="Courier">' + inline(n.children) + "</font>"
        elif n.tag == "a":
            out += inline(n.children)
        elif n.tag == "br":
            out += "<br/>"
        else:
            out += inline(n.children)
    return out

def build_blocks(nodes, story):
    for n in nodes:
        if isinstance(n, str):
            if n.strip():
                story.append(Paragraph(inline([n]), styles["Bodyx"]))
            continue

        tag = n.tag
        if tag in ("h1", "h2", "h3", "h4"):
            style = styles["ReportTitle"] if tag == "h1" else (
                styles["H1x"] if tag == "h2" else styles["H2x"])
            story.append(Paragraph(inline(n.children), style))
        elif tag == "p":
            story.append(Paragraph(inline(n.children), styles["Bodyx"]))
        elif tag == "pre":
            code = "".join(
                x if isinstance(x, str) else inline(x.children)
                for x in n.children
            )
            story.append(Preformatted(code.strip(), styles["Codex"]))
        elif tag in ("ul", "ol"):
            for item in n.children:
                if isinstance(item, Node) and item.tag == "li":
                    bullet = "â€¢ " if tag == "ul" else "â€“ "
                    story.append(Paragraph(
                        bullet + inline(item.children), styles["Bodyx"]))
        elif tag == "table":
            rows = []
            for tr in n.children:
                if isinstance(tr, Node) and tr.tag == "tbody":
                    trs = tr.children
                else:
                    trs = [tr]
                for row in trs:
                    if isinstance(row, Node) and row.tag == "tr":
                        cells = []
                        for cell in row.children:
                            if isinstance(cell, Node) and cell.tag in ("td", "th"):
                                cells.append(Paragraph(
                                    inline(cell.children), styles["Smallx"]))
                        if cells:
                            rows.append(cells)
            if rows:
                count = max(len(r) for r in rows)
                widths = [None] * count
                tbl = Table(rows, colWidths=widths, repeatRows=1,
                            hAlign="LEFT")
                tbl.setStyle(TableStyle([
                    ("GRID", (0,0), (-1,-1), 0.35, colors.grey),
                    ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
                    ("VALIGN", (0,0), (-1,-1), "TOP"),
                    ("LEFTPADDING", (0,0), (-1,-1), 4),
                    ("RIGHTPADDING", (0,0), (-1,-1), 4),
                    ("TOPPADDING", (0,0), (-1,-1), 3),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 3),
                ]))
                story.append(tbl)
                story.append(Spacer(1, 5))
        elif tag == "blockquote":
            story.append(Paragraph(inline(n.children), styles["Bodyx"]))
        elif tag == "hr":
            story.append(Spacer(1, 5))
        else:
            build_blocks(n.children, story)

class CountDoc(SimpleDocTemplate):
    main_pages = None
    def afterFlowable(self, flowable):
        if (self.main_pages is None and isinstance(flowable, Paragraph)
                and "Evidence Appendix" in flowable.getPlainText()):
            self.main_pages = self.canv.getPageNumber() - 1

text = SOURCE.read_text(encoding="utf-8-sig")
html = markdown.markdown(
    text, extensions=["tables", "fenced_code", "sane_lists"]
)
parser = TreeParser()
parser.feed(html)

story = []
build_blocks(parser.root.children, story)

story.append(PageBreak())
story.append(Paragraph("Evidence Appendix", styles["H1x"]))
story.append(Paragraph(
    "Screenshots supporting the CI, Mage and RabbitMQ implementation.",
    styles["Bodyx"]
))

images = [
    ("A_github_actions_pass.png", "A3 — Successful GitHub Actions run"),
    ("B3_ORD1006_validation.png", "B3 — ORD-1006 validation results"),
    ("B3_gold_exclusion.png", "B3 — Quarantined order excluded from Gold"),
    ("B3_quarantine_duplicates.png", "B3 — Quarantine duplicate investigation"),
    ("B3_quarantine_json_case_mismatch.png", "B3 — Quarantine JSON key-case investigation"),
    ("B4_CUST02_SCD2_history.png", "B4 — CUST-02 SCD Type 2 history"),
    ("B4_gold_merge_history.png", "B4 — Gold MERGE query history"),
    ("B4_gold_row_counts.png", "B4 — Gold fact table row counts"),
    ("B4_ORD1002_gold_current.png", "B4 — ORD-1002 current Gold record"),
    ("B4_ORD1002_gold_publication.png", "B4 — ORD-1002 publication evidence"),
    ("C1_mage_pipeline_graph.png", "C1 — Mage pipeline graph"),
    ("D1_rabbitmq_overview.png", "D1 — RabbitMQ management overview"),
    ("D2_rabbitmq_queues.png", "D2 — RabbitMQ queues"),
    ("D3_rabbitmq_exchange_bindings.png", "D3 — RabbitMQ exchange bindings"),
]

for filename, caption in images:
    path = EVIDENCE / filename
    if not path.exists():
        print("Missing evidence image:", path)
        continue
    story.append(PageBreak())
    story.append(Paragraph(caption, styles["H2x"]))
    img = Image(str(path))
    max_w, max_h = 175 * mm, 225 * mm
    scale = min(max_w / img.imageWidth, max_h / img.imageHeight)
    img.drawWidth = img.imageWidth * scale
    img.drawHeight = img.imageHeight * scale
    story.append(img)

doc = CountDoc(
    str(OUTPUT), pagesize=A4,
    rightMargin=17*mm, leftMargin=17*mm,
    topMargin=15*mm, bottomMargin=15*mm,
    title="Data Engineering Pipeline Orchestration Report",
    author="Prudhvi Raj Kumar"
)
doc.build(story)

print("PDF created:", OUTPUT.name)
print("Total pages:", doc.page)
print("Main report pages:", doc.main_pages)
print("Evidence appendix pages:", doc.page - (doc.main_pages or 0))
print("Main report limit:", "PASS" if doc.main_pages and doc.main_pages <= 8 else "CHECK â€” exceeds 8 pages or count unavailable")

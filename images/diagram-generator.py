"""Generates the two diagrams for the model collapse article as SVG, then PNG with rsvg-convert.

1. training-loops: what each round's training data contains when you replace, accumulate,
   or mix real data, and what the research found for each setup.
2. collapse-safe-pipeline: how the seven steps of the tutorial connect.

Same style as the LlamaIndex article's diagram. Usage: python3 diagram-generator.py
"""

import subprocess
from pathlib import Path

FONT = "'Helvetica Neue', Helvetica, Arial, sans-serif"
INK = "#1f1f1f"
MUTED = "#5c5f66"
BODY = "#343a40"
GREEN, GREEN_FILL = "#2b8a3e", "#ebfbee"
PURPLE, PURPLE_FILL = "#6741d9", "#f3f0ff"
REAL, REAL_FILL = "#1c64c2", "#dbe8fb"
OUT, OUT_FILL = "#c4541c", "#fde7da"
RED = "#c92a2a"


class Canvas:
    def __init__(self, w, h):
        self.w, self.h, self.parts = w, h, []

    def text(self, x, y, s, size=18, weight=400, fill=INK, anchor="middle", spacing=0):
        ls = f' letter-spacing="{spacing}"' if spacing else ""
        self.parts.append(
            f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}"{ls}>{s}</text>'
        )

    def rect(self, x, y, w, h, stroke, fill, rx=12, width=2.5, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{width}"{d}/>'
        )

    def badge(self, cx, cy, n, fill=INK):
        self.parts.append(f'<circle cx="{cx}" cy="{cy}" r="16" fill="{fill}"/>')
        self.text(cx, cy + 6, n, 17, 700, "#ffffff")

    def arrow(self, d, dash=None):
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="2.5" '
            f'stroke-linecap="round" marker-end="url(#head)"{da}/>'
        )

    def box(self, x, y, w, h, title, lines=(), kind="code", number=None):
        stroke, fill, ink = {
            "apify": (GREEN, GREEN_FILL, GREEN),
            "store": (PURPLE, PURPLE_FILL, PURPLE),
            "code": (INK, "#ffffff", INK),
        }[kind]
        self.rect(x, y, w, h, stroke, fill, 14)
        titles = title if isinstance(title, tuple) else (title,)
        block = 26 * len(titles) + 23 * len(lines) + (40 if number else 0)
        top = y + (h - block) / 2
        if number:
            self.badge(x + w / 2, top + 16, number, stroke if kind != "code" else INK)
            top += 40
        for t in titles:
            self.text(x + w / 2, top + 20, t, 20, 700, ink)
            top += 26
        for line in lines:
            self.text(x + w / 2, top + 19, line, 16, 400, ink if kind != "code" else BODY)
            top += 23

    def swatch(self, x, y, stroke, fill, s):
        self.rect(x, y, 30, 20, stroke, fill, 5, 2)
        self.text(x + 42, y + 16, s, 16, 400, BODY, "start")

    def save(self, name):
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}" font-family="{FONT}">'
            '<defs><marker id="head" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="12" '
            'markerHeight="12" markerUnits="userSpaceOnUse" orient="auto">'
            f'<path d="M 1 1 L 10 6 L 1 11" fill="none" stroke="{INK}" stroke-width="2.2" '
            'stroke-linecap="round" stroke-linejoin="round"/></marker></defs>'
            f'<rect width="{self.w}" height="{self.h}" fill="#fafafa"/>' + "".join(self.parts) + "</svg>"
        )
        here = Path(__file__).resolve().parent
        svg_path, png_path = here / f"{name}.svg", here / f"{name}.png"
        svg_path.write_text(svg)
        subprocess.run(["rsvg-convert", "-z", "2", "-o", str(png_path), str(svg_path)], check=True)
        print("written", svg_path.name, png_path.name)


def training_loops():
    c = Canvas(1290, 730)
    cells_x, cell_w = (350, 560, 770), 190
    for i, x in enumerate(cells_x):
        c.text(x + cell_w / 2, 52, f"ROUND {i + 1} TRAINS ON", 15, 700, MUTED, spacing=1.2)
    c.text(1120, 52, "RESULT IN THE RESEARCH", 15, 700, MUTED, spacing=1.2)

    rows = [
        ("Replace", ("Each round trains only on", "the last model's output"),
         [["O0"], ["O1"], ["O2"]], ("Collapse",), ("Shumailov et al.,", "Nature 2024"), RED),
        ("Accumulate", ("Keep all real data and", "add each round's output"),
         [["R", "O0"], ["R", "O0", "O1"], ["R", "O0", "O1", "O2"]],
         ("Error stays", "bounded"), ("Gerstgrasser et al.,", "COLM 2024"), GREEN),
        ("Mix", ("A share of real data", "in every round"),
         [["R|O0"], ["R|O1"], ["R|O2"]],
         ("Stable if the real", "share is large enough"), ("Bertrand et al., ICLR 2024.", "Nature 2024: 10% was enough"), INK),
    ]
    for r, (name, desc, cells, result, source, color) in enumerate(rows):
        y = 80 + r * 200
        c.rect(30, y, 1230, 180, "#dee2e6", "#ffffff", 16, 1.5)
        c.text(56, y + 66, name, 24, 700, INK, "start")
        for k, line in enumerate(desc):
            c.text(56, y + 98 + 24 * k, line, 16, 400, BODY, "start")
        for x, blocks in zip(cells_x, cells):
            bar_h = 30
            top = y + (180 - (len(blocks) * (bar_h + 6) - 6)) / 2
            for b in blocks:
                if b == "R":
                    c.rect(x, top, cell_w, bar_h, REAL, REAL_FILL, 7, 2)
                    c.text(x + cell_w / 2, top + 21, "Real data", 15, 700, REAL)
                elif b.startswith("R|"):
                    real_w = 64
                    c.rect(x, top, real_w, bar_h, REAL, REAL_FILL, 7, 2)
                    c.text(x + real_w / 2, top + 21, "Real", 15, 700, REAL)
                    c.rect(x + real_w + 4, top, cell_w - real_w - 4, bar_h, OUT, OUT_FILL, 7, 2)
                    c.text(x + real_w + 4 + (cell_w - real_w - 4) / 2, top + 21,
                           f"Output {b[-1]}", 15, 700, OUT)
                else:
                    c.rect(x, top, cell_w, bar_h, OUT, OUT_FILL, 7, 2)
                    c.text(x + cell_w / 2, top + 21, f"Output {b[-1]}", 15, 700, OUT)
                top += bar_h + 6
        for k, line in enumerate(result):
            c.text(1120, y + 70 + 26 * k, line, 20, 700, color)
        for k, line in enumerate(source):
            c.text(1120, y + 70 + 26 * len(result) + 6 + 21 * k, line, 15, 400, MUTED)
    c.swatch(40, 688, REAL, REAL_FILL, "Real, human-written data")
    c.swatch(330, 688, OUT, OUT_FILL, "Output of the model from the round before")
    c.save("training-loops")


def pipeline():
    c = Canvas(1290, 850)
    c.text(40, 60, "COLLECT", 15, 700, MUTED, "start", 1.5)
    c.box(40, 80, 330, 170, "Check AI-use signals",
          ("signals.py skips sites that say", "no or can't be read"), "code", "2")
    c.box(430, 80, 360, 170, "Website Content Crawler",
          ("collect.py crawls the allowed", "pages and saves provenance"), "apify", "2")
    c.box(850, 80, 400, 170, ("Archive copies", "from before ChatGPT"),
          ("baseline.py finds the last capture", "and saves its existed_by date"), "apify", "3")
    c.arrow("M 370 165 L 422 165")
    c.arrow("M 790 165 L 842 165")

    c.box(430, 315, 820, 130, "Named dataset and rows.jsonl",
          ("every row is kept, new crawls are added,", "nothing is replaced"), "store", "1")
    c.arrow("M 610 250 L 610 307")
    c.arrow("M 1050 250 L 1050 307")
    c.box(40, 315, 330, 130, "Monitor diversity",
          ("monitor.py compares each", "crawl_id with the baseline"), "code", "7")
    c.arrow("M 430 380 L 378 380")

    c.text(40, 512, "PREPARE A TRAINING ROUND", 15, 700, MUTED, "start", 1.5)
    c.box(40, 532, 330, 170, "Deduplicate",
          ("dedup.py keeps archive rows first,", "then the newest live copy"), "code", "4")
    c.box(430, 532, 360, 170, "Checked synthetic rows",
          ("rephrase.py rejects new numbers", "and tags each row's source"), "code", "5")
    c.box(850, 532, 400, 170, "Training round",
          ("build_round.py keeps every real row,", "caps synthetic rows, holds out pages"), "code", "6")
    # lands right of the "PREPARE A TRAINING ROUND" label, so the arrow doesn't cross it
    c.arrow("M 610 445 L 610 470 Q 610 482 598 482 L 342 482 Q 330 482 330 494 L 330 524")
    c.arrow("M 370 617 L 422 617")
    c.arrow("M 790 617 L 842 617")

    # next round: a scheduled crawl starts the loop again at the signal check
    c.arrow("M 1050 702 L 1050 752 L 20 752 L 20 165 L 32 165", dash="8 7")
    c.text(40, 742, "Next round: refresh on a schedule (cron)", 16, 700, BODY, "start")

    c.swatch(40, 800, GREEN, GREEN_FILL, "Runs on Apify")
    c.swatch(230, 800, INK, "#ffffff", "Your Python code")
    c.swatch(450, 800, PURPLE, PURPLE_FILL, "Storage")
    c.save("collapse-safe-pipeline")


if __name__ == "__main__":
    training_loops()
    pipeline()

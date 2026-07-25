#!/usr/bin/env python3
"""Kahani — Zero to One pitch deck (16:9), condensed for judges.

Target: 8 slides. Dense but readable. Text inside cards. Fixed grid.
"""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
OUT = ROOT / "Kahani_ZeroToOne_Pitch.pptx"

BG = RGBColor(0x0F, 0x0F, 0x12)
SURFACE = RGBColor(0x18, 0x18, 0x1F)
SURFACE_2 = RGBColor(0x22, 0x22, 0x2C)
ACCENT = RGBColor(0xE6, 0x19, 0x4D)
MUTED = RGBColor(0xA1, 0xA1, 0xAA)
DIM = RGBColor(0x71, 0x71, 0x7A)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LINE = RGBColor(0x2E, 0x2E, 0x38)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)
MX = Inches(0.70)
CONTENT_TOP = Inches(1.85)
FOOTER_Y = Inches(7.08)
CONTENT_W = Inches(11.93)
GAP = Inches(0.22)
TOTAL_PAGES = 8
FONT = "Calibri"


def _font(run, size, *, bold=False, color=WHITE):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    for tag in ("latin", "ea", "cs"):
        el = rPr.find(qn(f"a:{tag}"))
        if el is None:
            el = rPr.makeelement(qn(f"a:{tag}"), {})
            rPr.append(el)
        el.set("typeface", FONT)


def _bg(slide):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = BG


def _rect(slide, l, t, w, h, *, fill=SURFACE, line=None, rounded=False):
    kind = MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE if rounded else MSO_AUTO_SHAPE_TYPE.RECTANGLE
    sh = slide.shapes.add_shape(kind, l, t, w, h)
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if rounded:
        sh.adjustments[0] = 0.05
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(1.0)
    return sh


def _write(
    shape,
    blocks,
    *,
    align=PP_ALIGN.LEFT,
    valign=MSO_ANCHOR.TOP,
    ml=0.16,
    mr=0.14,
    mt=0.12,
    mb=0.10,
):
    tf = shape.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.auto_size = None
    tf.vertical_anchor = valign
    tf.margin_left = Inches(ml)
    tf.margin_right = Inches(mr)
    tf.margin_top = Inches(mt)
    tf.margin_bottom = Inches(mb)
    for i, (text, size, bold, color, space_after) in enumerate(blocks):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_before = Pt(0)
        p.space_after = Pt(space_after)
        p.line_spacing = 1.12
        run = p.add_run()
        run.text = text
        _font(run, size, bold=bold, color=color)


def _label(slide, l, t, w, h, blocks, *, align=PP_ALIGN.LEFT):
    box = slide.shapes.add_textbox(l, t, w, h)
    _write(box, blocks, align=align, ml=0, mr=0, mt=0, mb=0)
    return box


def _card(slide, l, t, w, h, blocks, *, fill=SURFACE, line=LINE, accent=False, center=False):
    align = PP_ALIGN.CENTER if center else PP_ALIGN.LEFT
    valign = MSO_ANCHOR.MIDDLE if center else MSO_ANCHOR.TOP
    if accent:
        strip = Inches(0.08)
        _rect(slide, l, t, strip, h, fill=ACCENT)
        card = _rect(slide, l + strip, t, w - strip, h, fill=fill, line=line, rounded=True)
        _write(card, blocks, align=align, valign=valign, ml=0.14)
    else:
        card = _rect(slide, l, t, w, h, fill=fill, line=line, rounded=True)
        _write(card, blocks, align=align, valign=valign)
    return card


def _header(slide, section: str, title: str, subtitle: str | None = None):
    _rect(slide, MX, Inches(0.38), Inches(0.38), Inches(0.06), fill=ACCENT)
    _label(slide, MX, Inches(0.52), CONTENT_W, Inches(0.24), [(section.upper(), 11, True, ACCENT, 0)])
    _label(slide, MX, Inches(0.80), CONTENT_W, Inches(0.40), [(title, 22, True, WHITE, 0)])
    if subtitle:
        _label(slide, MX, Inches(1.26), CONTENT_W, Inches(0.40), [(subtitle, 13, False, MUTED, 0)])


def _footer(slide, page: int):
    _label(
        slide,
        MX,
        FOOTER_Y,
        Inches(9.2),
        Inches(0.24),
        [("Kahani  ·  Zero to One × Pocket FM  ·  IIM Bangalore", 10, False, DIM, 0)],
    )
    _label(
        slide,
        Inches(11.15),
        FOOTER_Y,
        Inches(1.5),
        Inches(0.24),
        [(f"{page:02d} / {TOTAL_PAGES:02d}", 10, False, DIM, 0)],
        align=PP_ALIGN.RIGHT,
    )


def _picture_in_box(slide, path: Path, l, t, w, h):
    _rect(slide, l, t, w, h, fill=SURFACE_2, line=LINE, rounded=True)
    inset = Inches(0.08)
    inner_l, inner_t = l + inset, t + inset
    inner_w, inner_h = w - 2 * inset, h - 2 * inset
    if not path.exists():
        ph = _rect(slide, inner_l, inner_t, inner_w, inner_h, fill=SURFACE_2)
        _write(
            ph,
            [("Screenshot placeholder", 12, True, MUTED, 4), (path.name, 10, False, DIM, 0)],
            align=PP_ALIGN.CENTER,
            valign=MSO_ANCHOR.MIDDLE,
        )
        return
    from PIL import Image

    with Image.open(path) as im:
        iw, ih = im.size
    scale = min(inner_w / iw, inner_h / ih)
    pw, ph = int(iw * scale), int(ih * scale)
    pl = int(inner_l + (inner_w - pw) / 2)
    pt = int(inner_t + (inner_h - ph) / 2)
    slide.shapes.add_picture(str(path), pl, pt, width=pw, height=ph)


def blank(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s)
    return s


def bullets(title: str, items: list[str], *, title_size=13, item_size=11):
    blocks = [(title, title_size, True, WHITE, 8)]
    for i, item in enumerate(items):
        gap = 5 if i < len(items) - 1 else 0
        blocks.append((f"•  {item}", item_size, False, MUTED, gap))
    return blocks


# ── 8 slides ────────────────────────────────────────────────────────────────


def slide_01_cover(prs):
    s = blank(prs)
    _rect(s, Inches(0), Inches(0), Inches(0.12), SLIDE_H, fill=ACCENT)

    _label(
        s,
        MX,
        Inches(0.70),
        CONTENT_W,
        Inches(0.28),
        [("ZERO TO ONE  ·  POCKET FM × OPENAI × LIGHTSPEED  ·  IIM BANGALORE", 11, True, ACCENT, 0)],
    )
    _label(s, MX, Inches(2.10), CONTENT_W, Inches(0.80), [("Kahani", 52, True, WHITE, 0)])
    _label(
        s,
        MX,
        Inches(3.00),
        Inches(11.2),
        Inches(0.50),
        [("Agentic production studio for serialized audio entertainment.", 18, False, MUTED, 0)],
    )
    _label(
        s,
        MX,
        Inches(3.55),
        Inches(11.0),
        Inches(0.40),
        [
            (
                "Discovery → multi-part serial package → audience simulation → human publish.",
                13,
                False,
                DIM,
                0,
            )
        ],
    )

    chips = [
        ("Theme", "T-04 Creator Tools  ·  also T-01 / T-02"),
        ("Bet", "Wow audio first — agents are the how"),
        ("Gate", "Auto-run pipeline · never auto-publish"),
    ]
    chip_w = Inches(3.80)
    for i, (a, b) in enumerate(chips):
        _card(
            s,
            MX + i * (chip_w + GAP),
            Inches(5.10),
            chip_w,
            Inches(1.20),
            [(a.upper(), 10, True, ACCENT, 6), (b, 12, True, WHITE, 0)],
        )
    return s


def slide_02_problem_insight(prs):
    s = blank(prs)
    _header(
        s,
        "01  Problem & insight",
        "Retention is part-to-part. Production still runs in fragments.",
        "Orchestrate a studio with agents — keep humans at the quality cliffs.",
    )

    pains = [
        ("Slow idea → script", "Generic LLM drafts lack regional authenticity."),
        ("Weak chaining", "Cliffhangers fail → drop-off after part one."),
        ("Manual assembly", "Voice, SFX, visuals aligned by hand across tools."),
        ("No pre-publish signal", "Teams guess which cohorts will continue."),
    ]
    card_w, card_h = Inches(2.80), Inches(1.70)
    for i, (t, d) in enumerate(pains):
        _card(
            s,
            MX + i * (card_w + GAP),
            CONTENT_TOP,
            card_w,
            card_h,
            [(t, 13, True, WHITE, 6), (d, 11, False, MUTED, 0)],
            accent=True,
        )

    bets = [
        (
            "Audio is the product",
            ["Visuals are companion, not spine", "Narration-led by default", "Demo: one undeniable listen"],
        ),
        (
            "Serials over one-shots",
            ["Multi-part arcs (90–180s)", "Cliffhangers as a first-class stage", "One shared timeline clock"],
        ),
        (
            "Simulate before publish",
            ["Structural audit + personas", "Concrete rewrite patches", "Human approve — always"],
        ),
    ]
    y = CONTENT_TOP + card_h + GAP
    bet_w = Inches(3.80)
    for i, (title, items) in enumerate(bets):
        _card(
            s,
            MX + i * (bet_w + GAP),
            y,
            bet_w,
            Inches(2.55),
            bullets(title, items),
            fill=SURFACE_2,
        )
    _footer(s, 2)
    return s


def slide_03_solution(prs):
    s = blank(prs)
    _header(
        s,
        "02  Solution",
        "Kahani — discovery signal to human-approved serial package",
        "One project. One multi-agent pipeline. One editor-ready output.",
    )

    _card(
        s,
        MX,
        CONTENT_TOP,
        CONTENT_W,
        Inches(0.95),
        [
            (
                "Hook → multi-part serial (script, cliffhangers, narration/dialogue audio, SFX, companion visuals) → simulated listeners → patches → human publish.",
                13,
                False,
                WHITE,
                0,
            )
        ],
        line=ACCENT,
    )

    stages = ["Discovery", "Script", "Cliff", "Narration", "Voice", "SFX", "Visuals", "Editor", "Sim"]
    stage_w = Inches(1.18)
    y1 = CONTENT_TOP + Inches(1.15)
    for i, name in enumerate(stages):
        _card(
            s,
            MX + i * (stage_w + Inches(0.12)),
            y1,
            stage_w,
            Inches(1.15),
            [(str(i + 1), 12, True, ACCENT, 2), (name, 10, True, WHITE, 0)],
            center=True,
        )

    outcomes = [
        ("< 4 hrs", "Target for a 5-part package with ≤ 2 human gates"),
        ("24+ personas", "Age × gender × city-tier × intent cohorts"),
        ("1 timeline", "Script, VO, SFX, shots share one clock"),
        ("Closed loop", "Sim patches re-enter Script / Cliff / Narration"),
    ]
    y2 = y1 + Inches(1.35)
    ow = Inches(2.80)
    for i, (n, d) in enumerate(outcomes):
        _card(
            s,
            MX + i * (ow + GAP),
            y2,
            ow,
            Inches(1.75),
            [(n, 16, True, ACCENT, 6), (d, 11, False, MUTED, 0)],
        )
    _footer(s, 3)
    return s


def slide_04_product(prs):
    s = blank(prs)
    _header(
        s,
        "03  Product",
        "What judges can click, listen to, and stress-test",
        "Built for T-04 Creator Tools — with storytelling and voice AI in the loop.",
    )

    # Left: feature list
    features = [
        "Agent chat with live pipeline + approvals",
        "Script package review (structured, not a wall of text)",
        "Narration Director → performance map before TTS",
        "Web timeline editor (stems, markers, listen)",
        "Companion visuals aligned to story beats",
        "Audience Sim: audit, personas, diff-style patches",
        "Hindi + English · Docker Compose runtime",
    ]
    _card(
        s,
        MX,
        CONTENT_TOP,
        Inches(5.40),
        Inches(4.55),
        bullets("Shipped for demo", features, title_size=14, item_size=12),
        accent=True,
    )

    # Right: primary screenshot
    path = ASSETS / "02-agent-chat.png"
    if not path.exists() or path.stat().st_size < 40_000:
        alt = ASSETS / "01-chat-or-missing.png"
        if alt.exists():
            path = alt
    _picture_in_box(s, path, MX + Inches(5.40) + GAP, CONTENT_TOP, Inches(6.30), Inches(4.55))
    _footer(s, 4)
    return s


def slide_05_surfaces(prs):
    s = blank(prs)
    _header(
        s,
        "04  Product surfaces",
        "End-to-end loop in four screens",
        "Replace placeholders in docs/pitch/assets/ before final presentation.",
    )
    cells = [
        ("Projects", "03-projects-home.png"),
        ("Timeline editor", "04-timeline-editor.png"),
        ("Audience Sim", "05-audience-sim.png"),
        ("Visuals", "06-visuals.png"),
    ]
    cell_w, cell_h = Inches(5.85), Inches(2.15)
    title_h = Inches(0.34)
    for i, (title, fname) in enumerate(cells):
        col, row = i % 2, i // 2
        x = MX + col * (cell_w + GAP)
        y = CONTENT_TOP + row * (cell_h + GAP)
        title_card = _rect(s, x, y, cell_w, title_h, fill=SURFACE, line=LINE, rounded=True)
        _write(
            title_card,
            [(title, 11, True, WHITE, 0)],
            valign=MSO_ANCHOR.MIDDLE,
            mt=0.02,
            mb=0.02,
            ml=0.12,
        )
        _picture_in_box(
            s,
            ASSETS / fname,
            x,
            y + title_h + Inches(0.06),
            cell_w,
            cell_h - title_h - Inches(0.06),
        )
    _footer(s, 5)
    return s


def slide_06_differentiator_demo(prs):
    s = blank(prs)
    _header(
        s,
        "05  Differentiator & demo",
        "Audience simulation before publish — then prove it with a listen",
        "Simulation informs; it does not dictate. Scores labeled uncalibrated until listen logs exist.",
    )

    _card(
        s,
        MX,
        CONTENT_TOP,
        Inches(5.85),
        Inches(4.55),
        bullets(
            "Why this is different",
            [
                "Structural audit + persona drop-off risk",
                "Concrete patches, not vague feedback",
                "Signal before VO / mix spend",
                "Complements ranking — does not claim to replace it",
                "Creator stays final decision-maker",
                "Data flywheel: preview listens → calibrate",
            ],
            title_size=14,
            item_size=12,
        ),
        accent=True,
    )

    steps = [
        ("1 Brief", "Regional hook + context"),
        ("2 Generate", "Discovery → script → cliff → narration"),
        ("3 Approve", "Human gate before costly audio"),
        ("4 Listen", "Wow-audio moment in the editor"),
        ("5 Simulate", "Persona risk + accept a patch"),
        ("6 Decide", "Human publish intent"),
    ]
    x = MX + Inches(5.85) + GAP
    step_h = Inches(0.68)
    for i, (t, d) in enumerate(steps):
        _card(
            s,
            x,
            CONTENT_TOP + i * (step_h + Inches(0.08)),
            Inches(5.85),
            step_h,
            [(t, 12, True, WHITE, 2), (d, 11, False, MUTED, 0)],
        )
    _footer(s, 6)
    return s


def slide_07_tech_future(prs):
    s = blank(prs)
    _header(
        s,
        "06  Execution & roadmap",
        "Production-shaped stack — clear path beyond the hackathon",
        "Judged on innovation, technical execution, use of AI, real-world impact, and a working demo.",
    )

    cols = [
        (
            "Stack",
            [
                "React / TypeScript web studio",
                "FastAPI + ARQ workers",
                "LangGraph multi-agent pipeline",
                "LLM · TTS · SFX · visuals",
                "Postgres · Redis · object storage",
            ],
        ),
        (
            "Now (36h)",
            [
                "E2E agent pipeline + editor",
                "Wow-audio demo path",
                "Structural audit + persona sim",
                "Human approval gates",
                "Hindi + English series support",
            ],
        ),
        (
            "Next",
            [
                "Calibrate sims on preview listens",
                "Richer dialect packs for Bharat",
                "Deeper SFX / mix automation",
                "Multilingual adaptation / dubbing",
                "Distribution handoff APIs",
            ],
        ),
    ]
    card_w = Inches(3.80)
    for i, (title, items) in enumerate(cols):
        _card(
            s,
            MX + i * (card_w + GAP),
            CONTENT_TOP,
            card_w,
            Inches(4.55),
            bullets(title, items, title_size=14, item_size=12),
            accent=True,
        )
    _footer(s, 7)
    return s


def slide_08_close(prs):
    s = blank(prs)
    _rect(s, Inches(0), Inches(0), Inches(0.12), SLIDE_H, fill=ACCENT)

    _label(s, MX, Inches(1.60), CONTENT_W, Inches(0.28), [("THANK YOU", 12, True, ACCENT, 0)])
    _label(s, MX, Inches(2.10), CONTENT_W, Inches(0.70), [("Kahani", 46, True, WHITE, 0)])
    _label(
        s,
        MX,
        Inches(2.90),
        Inches(11.0),
        Inches(0.45),
        [("Agentic production for serialized audio — discovery to human publish.", 16, False, MUTED, 0)],
    )

    asks = [
        ("Ask", "Pilot with a Pocket FM–style content pod"),
        ("Proof", "Live demo: listen → simulate → patch"),
        ("Contact", "Add team names and emails here"),
    ]
    card_w = Inches(3.80)
    for i, (a, b) in enumerate(asks):
        _card(
            s,
            MX + i * (card_w + GAP),
            Inches(4.00),
            card_w,
            Inches(1.40),
            [(a.upper(), 11, True, ACCENT, 6), (b, 13, True, WHITE, 0)],
        )

    _label(
        s,
        MX,
        Inches(6.10),
        CONTENT_W,
        Inches(0.28),
        [("Zero to One  ·  Pocket FM × OpenAI × Lightspeed  ·  IIM Bangalore  ·  July 2026", 11, False, DIM, 0)],
    )
    _footer(s, 8)
    return s


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    slide_01_cover(prs)
    slide_02_problem_insight(prs)
    slide_03_solution(prs)
    slide_04_product(prs)
    slide_05_surfaces(prs)
    slide_06_differentiator_demo(prs)
    slide_07_tech_future(prs)
    slide_08_close(prs)

    try:
        prs.save(OUT)
        print(f"Wrote {OUT} ({len(prs.slides)} slides)")
    except PermissionError:
        alt = ROOT / "Kahani_ZeroToOne_Pitch_v2.pptx"
        prs.save(alt)
        print(f"Original locked; wrote {alt} ({len(prs.slides)} slides)")
        print("Close PowerPoint and re-run to overwrite the main file.")


if __name__ == "__main__":
    main()

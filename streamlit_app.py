
import math
from pathlib import Path
import streamlit as st
from PIL import Image

# ============================================================
# Streamlit side-oppsett
# ============================================================
st.set_page_config(
    page_title="Byggmatte",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      .block-container { padding-top: 3.5rem; padding-bottom: 1.0rem; }
      div[data-testid="stVerticalBlock"] { gap: 0.35rem; }
      div[data-testid="stImage"] { margin-top: 0rem !important; margin-bottom: 0rem !important; }
      div[data-testid="stImage"] > img { display:block; }

      .bk-title-row { display:flex; align-items: baseline; gap: 10px; line-height: 1; margin: 0; padding: 0; }
      .bk-title { font-size: 34px; font-weight: 900; color: #ff7a00; line-height: 1; }
      .bk-sub { font-size: 15px; color: #9aa4ad; line-height: 1; white-space: nowrap; }
      .bk-header-tight { margin-bottom: 8px; }

      /* "kort" følelse uten for mye luft */
      .bk-card p { margin: 0.25rem 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# Tilstand
# ============================================================
if "language" not in st.session_state:
    st.session_state.language = "NO"  # NO / EN

if "view" not in st.session_state:
    st.session_state.view = "Forside"

if "show_calculators" not in st.session_state:
    st.session_state.show_calculators = False


def lang() -> str:
    return st.session_state.get("language", "NO")


def tt(no: str, en: str) -> str:
    return en if lang() == "EN" else no


# ============================================================
# Logo + header
# ============================================================
LOGO_PATH = Path(__file__).parent / "byggmattev2.png"
if not LOGO_PATH.exists():
    alt1 = Path(__file__).parent / "logo.png"
    alt2 = Path(__file__).parent / "byggmatte.png"
    LOGO_PATH = alt1 if alt1.exists() else (alt2 if alt2.exists() else LOGO_PATH)

header_left, header_right = st.columns([1.1, 5], gap="small")
with header_left:
    try:
        img = Image.open(LOGO_PATH)
        st.image(img, width=260)
    except Exception:
        st.write("")

with header_right:
    st.markdown(
        f"""
        <div class="bk-header-tight">
          <div class="bk-title-row">
            <div class="bk-title">Byggmatte</div>
            <div class="bk-sub" style="margin-top:10px;">
              {tt("Fra skole til yrke – matematikk tilpasset yrkeslivet!",
                  "From school to trade – practical math for the workplace!")}
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='margin-top:-10px;'></div>", unsafe_allow_html=True)

# ============================================================
# Topmeny (didaktisk først)
# ============================================================
b1, b2, b3, b4 = st.columns([1.2, 1.6, 1.8, 2.0])

with b1:
    if st.button("🏠 " + tt("Forside", "Front page"), use_container_width=True):
        st.session_state.view = "Forside"
        st.rerun()

with b2:
    if st.button("📚 " + tt("Læringssoner", "Learning zones"), use_container_width=True):
        st.session_state.view = "Læringssoner"
        st.rerun()

with b3:
    if st.button("🧮 " + tt("Kalkulatorer", "Calculators"), use_container_width=True):
        st.session_state.view = "Kalkulatorer"
        st.rerun()

with b4:
    with st.popover("⚙️ " + tt("Innstillinger", "Settings"), use_container_width=True):
        st.subheader(tt("Innstillinger", "Settings"))
        st.markdown("**" + tt("Språk", "Language") + "**")
        st.session_state.language = st.radio(
            tt("Velg språk", "Select language"),
            ["NO", "EN"],
            horizontal=True,
            index=0 if lang() == "NO" else 1,
        )
        st.divider()
        st.session_state.show_calculators = st.toggle(
            tt("Aktiver kalkulatorer i læringssonene", "Enable calculators inside learning zones"),
            value=st.session_state.show_calculators,
        )
        st.caption(tt(
            "Når denne er på, kan elevene åpne en enkel kalkulator nederst i hver sone for å kontrollere svaret.",
            "When enabled, students can open a simple calculator at the bottom of each zone to verify answers."
        ))

st.divider()


# ============================================================
# Små hjelpefunksjoner
# ============================================================
def to_mm(value: float, unit: str) -> float:
    if unit == "mm":
        return value
    if unit == "cm":
        return value * 10.0
    if unit == "m":
        return value * 1000.0
    return value


def mm_to_all(mm: float):
    return {"mm": mm, "cm": mm / 10.0, "m": mm / 1000.0}


def render_asset_image(filename: str):
    """Vis bilde hvis det finnes i ./assets."""
    assets_dir = Path(__file__).parent / "assets"
    p = assets_dir / filename
    if p.exists() and p.is_file() and p.stat().st_size > 0:
        st.image(str(p), use_container_width=True)


# ============================================================
# FORSIDE (ferdig formulert)
# ============================================================
def show_front_page():
    left, right = st.columns([1.25, 1], gap="large")

    with left:
        st.markdown("## " + tt("Matematikk i byggfaget – før du bruker kalkulator", "Math in construction – before you use a calculator"))
        st.markdown(
            tt(
                """
**Byggmatte** er laget som et *undervisningsopplegg* – ikke bare et verktøy.  
Målet er at du skal **forstå**, **vurdere** og **kontrollere** regningene du gjør i verkstedet og på byggeplass.

### Hvorfor trenger vi matematikk i bygg?
Du bruker matematikk for å:
- bestille riktig mengde materialer (og redusere svinn)  
- sikre at konstruksjoner blir rette, stabile og trygge  
- lese og bruke arbeidstegninger og målestokk  
- dokumentere eget arbeid og gjøre egenkontroll  

> **Fagarbeiderlogikk:** Først forstår jeg oppgaven → så velger jeg formel → så regner jeg → så kontrollerer jeg.

### Slik bruker du appen i undervisning
1. **Les forsiden** (hva er målet og hva betyr begrepene?)  
2. Gå til **Læringssoner** og finn riktig tema (areal, omkrets, volum …)  
3. Prøv å regne **med mellomregning** før du sjekker svaret  
4. Bruk kalkulatoren *kun som kontroll* når du er usikker

""",
                """
**Byggmatte** is designed as a *learning sequence* — not just a tool.  
The goal is that you can **understand**, **judge** and **verify** the math you use in the workshop and on site.

### Why do we need math in construction?
You use math to:
- order the right quantity of materials (and reduce waste)  
- ensure structures are straight, stable and safe  
- read drawings and work with scale  
- document your work and perform self-checks  

> **Craft logic:** Understand the task → choose a formula → calculate → verify.

### How to use this app in class
1. **Read the front page** (goal + key concepts)  
2. Go to **Learning zones** and find the right topic (area, perimeter, volume …)  
3. Try to calculate **with working** before checking  
4. Use the calculator *only for verification* when needed
"""
            )
        )

        with st.container(border=True):
            st.markdown("### " + tt("Mini-økt (2×45 min) – forslag", "Mini-lesson (2×45 min) – suggestion"))
            st.markdown(
                tt(
                    """
**Økt 1 (45 min):** Felles gjennomgang av forsiden + én læringssone. Elevene forklarer *hvilken formel* de velger og *hvorfor*.  
**Økt 2 (45 min):** Elevene jobber med en praktisk case (gulv, vegg, list, betong). De leverer:  
- valgt formel  
- inndata (med enheter)  
- mellomregning  
- kontroll (kalkulator / grovsjekk)
                    """,
                    """
**Session 1 (45 min):** Whole-class walkthrough of the front page + one learning zone. Students explain *which formula* they choose and *why*.  
**Session 2 (45 min):** Students work on a practical case (floor, wall, trim, concrete). They submit:  
- chosen formula  
- inputs (with units)  
- working  
- verification (calculator / sanity check)
                    """
                )
            )

    with right:
        with st.container(border=True):
            st.markdown("### " + tt("Start her", "Start here"))
            st.write(tt("Velg hva du vil gjøre nå:", "Choose what you want to do now:"))

            c1, c2 = st.columns(2)
            with c1:
                if st.button("📚 " + tt("Gå til læringssoner", "Go to learning zones"), use_container_width=True):
                    st.session_state.view = "Læringssoner"
                    st.rerun()
            with c2:
                if st.button("🧮 " + tt("Gå til kalkulatorer", "Go to calculators"), use_container_width=True):
                    st.session_state.view = "Kalkulatorer"
                    st.rerun()

            st.divider()
            st.markdown("**" + tt("Huskeliste før du regner", "Checklist before you calculate") + "**")
            st.markdown(
                tt(
                    "- Har jeg riktige mål?\n- Har jeg samme enhet på alle mål (mm/cm/m)?\n- Vet jeg hvilken formel som passer?\n- Kan jeg grovsjekke om svaret virker realistisk?",
                    "- Do I have correct measurements?\n- Are all units consistent (mm/cm/m)?\n- Do I know which formula fits?\n- Can I sanity-check if the answer is realistic?",
                )
            )

        st.caption(tt("Illustrasjoner kan ligge i mappen **assets/** (valgfritt).", "Illustrations can be placed in the **assets/** folder (optional)."))
        render_asset_image("areal.png")


# ============================================================
# LÆRINGSSONER (full sone med alle vanlige formler i appen)
# ============================================================
def formula_block(title: str, formulas: list[str], notes: list[str] | None = None):
    with st.container(border=True):
        st.markdown(f"### {title}")
        st.markdown("**" + tt("Formler", "Formulas") + "**")
        for f in formulas:
            st.markdown(f"- `{f}`")
        if notes:
            st.markdown("**" + tt("Husk", "Remember") + "**")
            for n in notes:
                st.markdown(f"- {n}")


def calculator_block(kind: str):
    """Enkle kontrollkalkulatorer knyttet til sonene."""
    if not st.session_state.show_calculators:
        st.info(tt("Ønsker du kalkulator her? Slå på i ⚙️ Innstillinger.", "Want the calculator here? Enable it in ⚙️ Settings."))
        return

    st.markdown("#### " + tt("Kontrollkalkulator", "Verification calculator"))

    if kind == "unit":
        v = st.number_input(tt("Verdi", "Value"), min_value=0.0, value=1000.0, step=1.0)
        u = st.selectbox(tt("Enhet", "Unit"), ["mm", "cm", "m"], index=0)
        mm = to_mm(float(v), str(u))
        out = mm_to_all(mm)
        c1, c2, c3 = st.columns(3)
        c1.metric("mm", f"{out['mm']:.2f}")
        c2.metric("cm", f"{out['cm']:.2f}")
        c3.metric("m", f"{out['m']:.3f}")

    if kind == "area_rect":
        a = st.number_input(tt("Lengde (m)", "Length (m)"), min_value=0.0, value=6.0, step=0.1)
        b = st.number_input(tt("Bredde (m)", "Width (m)"), min_value=0.0, value=2.0, step=0.1)
        if st.button(tt("Beregn areal", "Calculate area")):
            st.success(f"{a*b:.2f} m²")

    if kind == "perimeter_rect":
        a = st.number_input(tt("Lengde (m)", "Length (m)"), min_value=0.0, value=2.0, step=0.1, key="p_a")
        b = st.number_input(tt("Bredde (m)", "Width (m)"), min_value=0.0, value=2.0, step=0.1, key="p_b")
        if st.button(tt("Beregn omkrets", "Calculate perimeter")):
            st.success(f"{2*(a+b):.2f} m")

    if kind == "volume_box":
        l = st.number_input(tt("Lengde (m)", "Length (m)"), min_value=0.0, value=6.0, step=0.1, key="v_l")
        b = st.number_input(tt("Bredde (m)", "Width (m)"), min_value=0.0, value=2.0, step=0.1, key="v_b")
        h = st.number_input(tt("Høyde/tykkelse (m)", "Height/thickness (m)"), min_value=0.0, value=0.10, step=0.01, key="v_h")
        if st.button(tt("Beregn volum", "Calculate volume")):
            st.success(f"{l*b*h:.3f} m³")

    if kind == "diagonal":
        a = st.number_input(tt("Side A (m)", "Side A (m)"), min_value=0.0, value=3.0, step=0.1, key="d_a")
        b = st.number_input(tt("Side B (m)", "Side B (m)"), min_value=0.0, value=4.0, step=0.1, key="d_b")
        if st.button(tt("Beregn diagonal", "Calculate diagonal")):
            st.success(f"{math.sqrt(a*a + b*b):.3f} m")

    if kind == "percent_of":
        p = st.number_input(tt("Prosent (%)", "Percent (%)"), min_value=0.0, value=25.0, step=1.0, key="pc_p")
        v = st.number_input(tt("Av (verdi)", "Of (value)"), min_value=0.0, value=800.0, step=1.0, key="pc_v")
        if st.button(tt("Beregn", "Calculate")):
            st.success(f"{(p/100.0)*v:.2f}")

    if kind == "slope":
        fall = st.number_input(tt("Fall (m)", "Fall (m)"), min_value=0.0, value=0.08, step=0.01, key="sl_f")
        lengde = st.number_input(tt("Lengde (m)", "Length (m)"), min_value=0.0, value=4.0, step=0.1, key="sl_l")
        if st.button(tt("Beregn fall (%)", "Calculate slope (%)")):
            if lengde == 0:
                st.warning(tt("Lengde kan ikke være 0.", "Length cannot be 0."))
            else:
                st.success(f"{(fall/lengde)*100.0:.2f} %")


def show_learning_zones():
    st.markdown("## " + tt("Læringssoner", "Learning zones"))
    st.caption(tt(
        "Her finner du forklaringer og formler. Målet er at elevene skal kunne velge riktig formel og vise mellomregning.",
        "Here you will find explanations and formulas. The goal is that students can choose the correct formula and show working."
    ))

    # 1) Enheter
    with st.expander("📏 " + tt("Enheter og omregning", "Units and conversion"), expanded=True):
        st.markdown(tt(
            """
**Hvorfor:** I bygg oppstår feil ofte fordi vi blander mm, cm og m.  
**Regel:** Gjør om til *samme enhet* før du regner.

- `mm → cm`: ÷ 10  
- `cm → m`: ÷ 100  
- `mm → m`: ÷ 1000  
- `m → cm`: × 100  
- `m → mm`: × 1000
            """,
            """
**Why:** In construction, mistakes often happen because mm, cm and m get mixed.  
**Rule:** Convert to the *same unit* before calculating.

- `mm → cm`: ÷ 10  
- `cm → m`: ÷ 100  
- `mm → m`: ÷ 1000  
- `m → cm`: × 100  
- `m → mm`: × 1000
            """
        ))
        render_asset_image("enhetsomregner.png")
        calculator_block("unit")

    # 2) Areal
    with st.expander("⬛ " + tt("Areal (flate)", "Area (surface)"), expanded=False):
        formula_block(
            tt("Areal – vanlige formler", "Area – common formulas"),
            formulas=[
                "Rektangel = lengde × bredde",
                "Trekant = (grunnlinje × høyde) / 2",
                "Sirkel = π × r²",
                "Trapes = ((a + b) / 2) × h",
            ],
            notes=[
                tt("Svar i m² når målene er i meter.", "Answer is in m² when measurements are in meters."),
                tt("Trekk fra åpninger (dør/vindu) for nettoareal.", "Subtract openings (door/window) for net area."),
                tt("Legg til svinn ved bestilling (ofte 10–15 %).", "Add waste when ordering (often 10–15%)."),
            ],
        )
        st.markdown(tt(
            "**Eksempel (rektangel):** Gulv 6,0 m × 2,0 m → `A = 12,0 m²`.",
            "**Example (rectangle):** Floor 6.0 m × 2.0 m → `A = 12.0 m²`.",
        ))
        render_asset_image("areal.png")
        calculator_block("area_rect")

    # 3) Omkrets
    with st.expander("🧵 " + tt("Omkrets (lengde rundt)", "Perimeter (length around)"), expanded=False):
        formula_block(
            tt("Omkrets – vanlige formler", "Perimeter – common formulas"),
            formulas=[
                "Rektangel = 2 × (lengde + bredde)",
                "Trekant = a + b + c",
                "Sirkel = 2 × π × r  (eller π × d)",
            ],
            notes=[
                tt("Svar i meter (m) når målene er i meter.", "Answer is in meters (m) when measurements are in meters."),
                tt("Brukes mye til lister, sviller, rammer og løpemeter.", "Often used for trim, sills, frames and running meters."),
            ],
        )
        render_asset_image("omkrets.png")
        calculator_block("perimeter_rect")

    # 4) Volum
    with st.expander("🧱 " + tt("Volum (mengde)", "Volume (quantity)"), expanded=False):
        formula_block(
            tt("Volum – vanlige formler", "Volume – common formulas"),
            formulas=[
                "Boks = lengde × bredde × høyde",
                "Plate = lengde × bredde × tykkelse",
                "Sylinder = π × r² × h",
            ],
            notes=[
                tt("Tykkelse står ofte i mm – gjør om til meter først.", "Thickness is often given in mm — convert to meters first."),
                tt("Svar i m³.", "Answer is in m³."),
            ],
        )
        st.markdown(tt(
            "**Eksempel (plate):** 100 mm = 0,10 m → `V = 6,0 × 2,0 × 0,10 = 1,2 m³`.",
            "**Example (slab):** 100 mm = 0.10 m → `V = 6.0 × 2.0 × 0.10 = 1.2 m³`.",
        ))
        render_asset_image("volum.png")
        calculator_block("volume_box")

    # 5) Diagonal og kontroll av rett vinkel
    with st.expander("📐 " + tt("Diagonal og rett vinkel (Pytagoras)", "Diagonal and right angle (Pythagoras)"), expanded=False):
        formula_block(
            tt("Diagonal – formel", "Diagonal – formula"),
            formulas=[
                "c = √(a² + b²)",
                "a = √(c² − b²)",
                "b = √(c² − a²)",
            ],
            notes=[
                tt("Brukes for å kontrollere om en ramme er i vinkel.", "Used to check if a frame is square."),
                tt("Klassiker: 3–4–5 (m) gir rett vinkel.", "Classic: 3–4–5 (m) gives a right angle."),
            ],
        )
        render_asset_image("diagonal.png")
        calculator_block("diagonal")

    # 6) Vinkler (grunnleggende trig)
    with st.expander("📐 " + tt("Vinkler (grunnleggende)", "Angles (basics)"), expanded=False):
        formula_block(
            tt("Vinkler – vanlige formler", "Angles – common formulas"),
            formulas=[
                "sin A (θ) = motstående / hypotenus",
                "cos B (θ) = hosliggende / hypotenus",
                "tan C (θ) = motstående / hosliggende",
                "θ = arctan(motstående / hosliggende)",
            ],
            notes=[
                tt("Bruk A, B, C som sider dersom det er enklere å huske.", "Use A, B, C as sides if that is easier to remember."),
                tt("Vær konsekvent: samme enhet på alle lengder.", "Be consistent: same unit for all lengths."),
            ],
        )
        render_asset_image("vinkler.png")
        st.info(tt(
            "Tips i undervisning: La elevene tegne en rettvinklet trekant og merke sider før de bruker kalkulator.",
            "Class tip: Let students sketch a right triangle and label sides before using a calculator."
        ))

    # 7) Målestokk
    with st.expander("📐 " + tt("Målestokk", "Scale"), expanded=False):
        formula_block(
            tt("Målestokk – formler", "Scale – formulas"),
            formulas=[
                "Målestokk = tegning / virkelighet",
                "Tegning = virkelighet × målestokk",
                "Virkelighet = tegning / målestokk",
                "Ved 1:n → målestokk = 1/n",
            ],
            notes=[
                tt("Pass på enheter (mm på tegning, m i virkelighet).", "Watch units (mm on drawing, m in reality)."),
                tt("Skriv alltid målestokk som 1:n.", "Always write scale as 1:n."),
            ],
        )
        render_asset_image("malestokk.png")

    # 8) Fall
    with st.expander("📉 " + tt("Fall (gulv / sluk)", "Slope (floors / drains)"), expanded=False):
        formula_block(
            tt("Fall – formler", "Slope – formulas"),
            formulas=[
                "Fall (%) = (fall / lengde) × 100",
                "Fall (m) = (fall% / 100) × lengde",
            ],
            notes=[
                tt("Fall måles ofte i mm per meter: 1:50 = 20 mm per meter.", "Slope is often expressed as mm per meter: 1:50 = 20 mm per meter."),
                tt("Bruk grovsjekk: virker fallet rimelig på lengden?", "Sanity-check: does the slope make sense for the length?"),
            ],
        )
        render_asset_image("fall.png")
        calculator_block("slope")

    # 9) Prosent
    with st.expander("🧮 " + tt("Prosent (svinn, rabatt, påslag)", "Percent (waste, discount, markup)"), expanded=False):
        formula_block(
            tt("Prosent – formler", "Percent – formulas"),
            formulas=[
                "Prosentandel = (del / hel) × 100",
                "Del = (prosent / 100) × hel",
                "Hel = del / (prosent / 100)",
                "Ny verdi = gammel verdi × (1 ± prosent/100)",
            ],
            notes=[
                tt("Svinn: bestillingsmengde = mengde × (1 + svinn%).", "Waste: order quantity = quantity × (1 + waste%)."),
                tt("Rabatt: pris etter rabatt = pris × (1 − rabatt%).", "Discount: price after discount = price × (1 − discount%)."),
            ],
        )
        render_asset_image("prosent.png")
        calculator_block("percent_of")

    # 10) Økonomi (enkel)
    with st.expander("💰 " + tt("Økonomi (enkel overslagsregning)", "Economy (simple estimating)"), expanded=False):
        formula_block(
            tt("Økonomi – formler", "Economy – formulas"),
            formulas=[
                "Sum = materialkost + timekost",
                "Timekost = timer × pris_per_time",
                "Pris inkl. MVA = pris eks. MVA × (1 + mva/100)",
            ],
            notes=[
                tt("Poenget er å kunne forklare regnegangen, ikke bare få et tall.", "The goal is to explain your working, not just get a number."),
            ],
        )
        render_asset_image("okonomi.png")

    st.divider()
    with st.container(border=True):
        st.markdown("### " + tt("Refleksjon (kan leveres)", "Reflection (can be submitted)"))
        st.markdown(
            tt(
                "- Hvilken formel valgte du – og hvorfor?\n"
                "- Hvilke enheter brukte du – og hvordan kontrollerte du dem?\n"
                "- Hvordan kan du grovsjekke om svaret er realistisk?\n"
                "- Hva kan gå galt i praksis hvis du regner feil?",
                "- Which formula did you choose — and why?\n"
                "- Which units did you use — and how did you verify them?\n"
                "- How can you sanity-check if the answer is realistic?\n"
                "- What can go wrong in practice if the calculation is wrong?",
            )
        )


# ============================================================
# KALKULATORER (valgfritt)
# ============================================================
def show_calculators():
    st.markdown("## " + tt("Kalkulatorer", "Calculators"))
    st.caption(tt(
        "Bruk disse som kontroll etter at du har jobbet i læringssonene.",
        "Use these for verification after you have worked in the learning zones."
    ))

    tabs = st.tabs(
        [
            "📏 " + tt("Enhetsomregning", "Unit conversion"),
            "⬛ " + tt("Areal", "Area"),
            "🧵 " + tt("Omkrets", "Perimeter"),
            "🧱 " + tt("Volum", "Volume"),
            "📐 " + tt("Diagonal", "Diagonal"),
            "📉 " + tt("Fall", "Slope"),
            "🧮 " + tt("Prosent", "Percent"),
        ]
    )

    with tabs[0]:
        calculator_block("unit")

    with tabs[1]:
        calculator_block("area_rect")

    with tabs[2]:
        calculator_block("perimeter_rect")

    with tabs[3]:
        calculator_block("volume_box")

    with tabs[4]:
        calculator_block("diagonal")

    with tabs[5]:
        calculator_block("slope")

    with tabs[6]:
        calculator_block("percent_of")


# ============================================================
# Router
# ============================================================
if st.session_state.view == "Forside":
    show_front_page()
elif st.session_state.view == "Læringssoner":
    show_learning_zones()
else:
    show_calculators()

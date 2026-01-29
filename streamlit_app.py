
import math
from pathlib import Path
import random
import streamlit as st
from PIL import Image

# ==========================
# Pro-konfig (enkelt å endre)
# ==========================
PRO_PRICE_MONTH = 29  # kr per måned (pilot)
PRO_PRICE_YEAR = 299  # kr per år (pilot)
TEACHER_CODE = "2150"

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
      .block-container { padding-top: 3.2rem; padding-bottom: 1.0rem; }
      div[data-testid="stVerticalBlock"] { gap: 0.35rem; }
      div[data-testid="stImage"] { margin-top: 0rem !important; margin-bottom: 0rem !important; }
      div[data-testid="stImage"] > img { display:block; }

      .bk-title-row { display:flex; align-items: baseline; gap: 10px; line-height: 1; margin: 0; padding: 0; }
      .bk-title { font-size: 34px; font-weight: 900; color: #ff7a00; line-height: 1; }
      .bk-sub { font-size: 15px; color: #9aa4ad; line-height: 1; white-space: nowrap; }
      .bk-header-tight { margin-bottom: 8px; }

      .bk-muted { color:#6b7680; }
      .bk-card p { margin: 0.25rem 0; }
      .bk-chip { display:inline-block; padding:4px 10px; border-radius:999px; font-size:12px; border:1px solid #e6eaee; color:#6b7680; }
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

if "is_pro_user" not in st.session_state:
    st.session_state.is_pro_user = False

if "pro_teacher_mode" not in st.session_state:
    st.session_state.pro_teacher_mode = False

# Læringsarena-progress
if "arena_level" not in st.session_state:
    st.session_state.arena_level = 1  # 1..3
if "arena_score" not in st.session_state:
    st.session_state.arena_score = {1: 0, 2: 0, 3: 0}
if "arena_taskset" not in st.session_state:
    st.session_state.arena_taskset = {}  # level -> list[task]


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
# Topmeny
# ============================================================
b1, b2, b3, b4, b5 = st.columns([1.2, 1.7, 1.6, 1.6, 2.2])

with b1:
    if st.button("🏠 " + tt("Forside", "Front page"), use_container_width=True, key="nav_home"):
        st.session_state.view = "Forside"
        st.rerun()

with b2:
    if st.button("📚 " + tt("Læringsarena", "Learning arena"), use_container_width=True, key="nav_arena"):
        st.session_state.view = "Læringsarena"
        st.rerun()

with b3:
    if st.button("🧾 " + tt("Beregning", "Working"), use_container_width=True, key="nav_working"):
        st.session_state.view = "Beregning"
        st.rerun()

with b4:
    if st.button("🧮 " + tt("Kalkulatorer", "Calculators"), use_container_width=True, key="nav_calcs"):
        st.session_state.view = "Kalkulatorer"
        st.rerun()

with b5:
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
            tt("Aktiver kontrollkalkulatorer i læringsarena", "Enable verification calculators in learning arena"),
            value=st.session_state.show_calculators,
        )
        st.caption(tt(
            "Når denne er på, kan elevene åpne en enkel kalkulator nederst i temaene for å kontrollere svaret.",
            "When enabled, students can open simple calculators at the bottom of topics to verify answers."
        ))

        st.divider()
        st.markdown("**" + tt("Oppgradering", "Upgrade") + "**")
        st.caption(tt("Pro gir ekstra øving, dokumentasjon og vurderingsstøtte.",
                      "Pro adds extra practice, documentation and assessment support."))
        if st.button("⭐ " + tt("Oppgrader til Pro (BETA)", "Upgrade to Pro (BETA)"), use_container_width=True):
            st.session_state.view = "Pro"
            st.rerun()

st.divider()

# ============================================================
# Navigasjon (fallback i sidepanel)
# ============================================================
with st.sidebar:
    st.markdown("### " + tt("Navigasjon", "Navigation"))
    nav_options = [
        ("Forside", tt("Forside", "Front page")),
        ("Læringsarena", tt("Læringsarena", "Learning arena")),
        ("Beregning", tt("Beregning", "Working")),
        ("Kalkulatorer", tt("Kalkulatorer", "Calculators")),
        ("Pro", tt("Pro (info)", "Pro (info)")),
        ("ProInnhold", tt("Pro-innhold", "Pro content")),
    ]
    view_to_index = {key: i for i, (key, _) in enumerate(nav_options)}
    current_index = view_to_index.get(st.session_state.view, 0)

    nav_label = st.radio(
        tt("Gå til", "Go to"),
        options=[label for _, label in nav_options],
        index=current_index,
    )
    label_to_view = {label: key for key, label in nav_options}
    chosen_view = label_to_view.get(nav_label, "Forside")

    if chosen_view != st.session_state.view:
        st.session_state.view = chosen_view
        st.rerun()

# ============================================================
# Hjelpefunksjoner (enheter)
# ============================================================
LENGTH_UNITS = ["mm", "cm", "m"]

def to_m(value: float, unit: str) -> float:
    if unit == "mm":
        return value / 1000.0
    if unit == "cm":
        return value / 100.0
    return value

def from_m(value_m: float, unit: str) -> float:
    if unit == "mm":
        return value_m * 1000.0
    if unit == "cm":
        return value_m * 100.0
    return value_m

def area_from_m2(value_m2: float, unit: str) -> float:
    if unit == "mm":
        return value_m2 * (1000.0 ** 2)
    if unit == "cm":
        return value_m2 * (100.0 ** 2)
    return value_m2

def volume_from_m3(value_m3: float, unit: str) -> float:
    if unit == "mm":
        return value_m3 * (1000.0 ** 3)
    if unit == "cm":
        return value_m3 * (100.0 ** 3)
    return value_m3

def render_asset_image(filename: str):
    assets_dir = Path(__file__).parent / "assets"
    p = assets_dir / filename
    if p.exists() and p.is_file() and p.stat().st_size > 0:
        st.image(str(p), use_container_width=True)

def fmt(x: float) -> str:
    if abs(x) >= 1000:
        return f"{x:,.2f}".replace(",", " ")
    return f"{x:.4g}"

# ============================================================
# FORSIDE
# ============================================================
def show_front_page():
    left, right = st.columns([1.25, 1], gap="large")

    with left:
        st.markdown("## " + tt("Matematikk i byggfaget – hvorfor trenger vi det?", "Math in construction – why do we need it?"))
        st.markdown(
            tt(
                """
**Byggmatte** er laget som et *undervisningsopplegg*, men også et verktøy for å kontrollere om det vi har gjort, er riktig.  
Målet er at du skal **forstå**, **vurdere** og **kontrollere** regningene du gjør i verkstedet og på byggeplass.

### Hvorfor trenger vi matematikk i bygg?
Du bruker matematikk for å:
- Bestille riktig mengde materialer (og redusere svinn)  
- Sikre at konstruksjoner blir rette, stabile og trygge  
- Lese og bruke arbeidstegninger og målestokk  
- Dokumentere eget arbeid og gjøre egenkontroll  

> **Fagarbeiderlogikk:** Først forstår jeg oppgaven → så velger jeg formel → så regner jeg → så kontrollerer jeg.

### Slik bruker du appen i undervisning
1. **Les forsiden**  
2. Bruk **Læringsarena** (formler + oppgaver)  
3. Vis **mellomregning** før du sjekker svaret  
4. Bruk kalkulatoren *kun som kontroll* når du er usikker
""",
                """
**Byggmatte** is designed as a learning sequence and a verification tool.  
Goal: **understand**, **judge** and **verify** the math you use in the workshop and on site.

### Why do we need math in construction?
You use math to:
- order correct material quantities (reduce waste)  
- keep structures straight, stable and safe  
- read drawings and scale  
- document your work and self-check  

> Craft logic: Understand → choose formula → calculate → verify.

### How to use the app in class
1. Read the front page  
2. Use the Learning arena (formulas + tasks)  
3. Show working before checking  
4. Use calculators only for verification
"""
            )
        )

    with right:
        with st.container(border=True):
            st.markdown("### " + tt("Start her", "Start here"))
            st.write(tt("Velg hva du vil gjøre nå:", "Choose what you want to do now:"))
            c1, c2 = st.columns(2)
            with c1:
                if st.button("📚 " + tt("Læringsarena", "Learning arena"), use_container_width=True, key="nav_arena"):
                    st.session_state.view = "Læringsarena"
                    st.rerun()
            with c2:
                if st.button("🧮 " + tt("Kalkulatorer", "Calculators"), use_container_width=True, key="nav_calcs"):
                    st.session_state.view = "Kalkulatorer"
                    st.rerun()

            st.divider()
            st.markdown("**" + tt("Huskeliste før du regner", "Checklist before you calculate") + "**")
            st.markdown(
                tt(
                    "- Riktige mål?\n- Samme enhet (mm/cm/m)?\n- Riktig formel?\n- Grovsjekk: virker svaret realistisk?",
                    "- Correct measurements?\n- Same unit (mm/cm/m)?\n- Correct formula?\n- Sanity-check: is the result realistic?",
                )
            )

# ============================================================
# FORMELBANK (tidligere læringssone)
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

def verification_calculator(kind: str, key_prefix: str | None = None):
    """Enkle kontrollkalkulatorer knyttet til tema.

    Viktig: Streamlit krever unike widget-keys når samme type widget kan dukke opp flere steder
    (forside + faner + læringsarena). Derfor bruker vi key_prefix.
    """
    if not st.session_state.show_calculators:
        st.info(tt("Ønsker du kontrollkalkulator her? Slå på i ⚙️ Innstillinger.", "Enable verification calculators in ⚙️ Settings."))
        return

    kp = key_prefix or f"vc_{kind}"
    st.markdown("#### " + tt("Kontrollkalkulator", "Verification calculator"))

    if kind == "unit":
        v = st.number_input(tt("Verdi", "Value"), min_value=0.0, value=1000.0, step=1.0, key=f"{kp}_val")
        u = st.selectbox(tt("Enhet", "Unit"), ["mm", "cm", "m"], index=0, key=f"{kp}_unit")
        mm = to_mm(float(v), str(u))
        out = mm_to_all(mm)
        c1, c2, c3 = st.columns(3)
        c1.metric("mm", f"{out['mm']:.2f}")
        c2.metric("cm", f"{out['cm']:.2f}")
        c3.metric("m", f"{out['m']:.3f}")

    elif kind == "area_rect":
        a = st.number_input(tt("Lengde", "Length"), min_value=0.0, value=6.0, step=0.1, key=f"{kp}_a")
        b = st.number_input(tt("Bredde", "Width"), min_value=0.0, value=2.0, step=0.1, key=f"{kp}_b")
        u = st.selectbox(tt("Enhet", "Unit"), ["mm", "cm", "m"], index=2, key=f"{kp}_unit")
        a_m = to_mm(a, u) / 1000.0
        b_m = to_mm(b, u) / 1000.0
        if st.button(tt("Beregn areal", "Calculate area"), key=f"{kp}_btn"):
            st.success(f"{a_m*b_m:.3f} m²")

    elif kind == "perimeter_rect":
        a = st.number_input(tt("Lengde", "Length"), min_value=0.0, value=2.0, step=0.1, key=f"{kp}_a")
        b = st.number_input(tt("Bredde", "Width"), min_value=0.0, value=2.0, step=0.1, key=f"{kp}_b")
        u = st.selectbox(tt("Enhet", "Unit"), ["mm", "cm", "m"], index=2, key=f"{kp}_unit")
        a_m = to_mm(a, u) / 1000.0
        b_m = to_mm(b, u) / 1000.0
        if st.button(tt("Beregn omkrets", "Calculate perimeter"), key=f"{kp}_btn"):
            st.success(f"{2*(a_m+b_m):.3f} m")

    elif kind == "volume_box":
        l = st.number_input(tt("Lengde", "Length"), min_value=0.0, value=6.0, step=0.1, key=f"{kp}_l")
        b = st.number_input(tt("Bredde", "Width"), min_value=0.0, value=2.0, step=0.1, key=f"{kp}_b")
        h = st.number_input(tt("Høyde/tykkelse", "Height/thickness"), min_value=0.0, value=0.10, step=0.01, key=f"{kp}_h")
        u = st.selectbox(tt("Enhet", "Unit"), ["mm", "cm", "m"], index=2, key=f"{kp}_unit")
        l_m = to_mm(l, u) / 1000.0
        b_m = to_mm(b, u) / 1000.0
        h_m = to_mm(h, u) / 1000.0
        if st.button(tt("Beregn volum", "Calculate volume"), key=f"{kp}_btn"):
            st.success(f"{l_m*b_m*h_m:.4f} m³")

    elif kind == "diagonal":
        a = st.number_input(tt("Side A", "Side A"), min_value=0.0, value=3.0, step=0.1, key=f"{kp}_a")
        b = st.number_input(tt("Side B", "Side B"), min_value=0.0, value=4.0, step=0.1, key=f"{kp}_b")
        u = st.selectbox(tt("Enhet", "Unit"), ["mm", "cm", "m"], index=2, key=f"{kp}_unit")
        a_m = to_mm(a, u) / 1000.0
        b_m = to_mm(b, u) / 1000.0
        if st.button(tt("Beregn diagonal", "Calculate diagonal"), key=f"{kp}_btn"):
            st.success(f"{math.sqrt(a_m*a_m + b_m*b_m):.4f} m")

    elif kind == "slope":
        fall = st.number_input(tt("Fall", "Drop"), min_value=0.0, value=0.08, step=0.01, key=f"{kp}_fall")
        lengde = st.number_input(tt("Lengde", "Length"), min_value=0.0, value=4.0, step=0.1, key=f"{kp}_len")
        u = st.selectbox(tt("Enhet", "Unit"), ["mm", "cm", "m"], index=2, key=f"{kp}_unit")
        fall_m = to_mm(fall, u) / 1000.0
        lengde_m = to_mm(lengde, u) / 1000.0
        if st.button(tt("Beregn fall (%)", "Calculate slope (%)"), key=f"{kp}_btn"):
            if lengde_m == 0:
                st.warning(tt("Lengde kan ikke være 0.", "Length cannot be 0."))
            else:
                st.success(f"{(fall_m/lengde_m)*100.0:.2f} %")

    elif kind == "percent_of":
        p = st.number_input(tt("Prosent (%)", "Percent (%)"), min_value=0.0, value=25.0, step=1.0, key=f"{kp}_p")
        v = st.number_input(tt("Av (verdi)", "Of (value)"), min_value=0.0, value=800.0, step=1.0, key=f"{kp}_v")
        if st.button(tt("Beregn", "Calculate"), key=f"{kp}_btn"):
            st.success(f"{(p/100.0)*v:.2f}")



def angle_calculator():
    st.markdown("### " + tt("Vinkelkalkulator (rettvinklet trekant)", "Angle calculator (right triangle)"))
    st.caption(tt(
        "Bruk A (hosliggende) og B (motstående). Du kan regne ut vinkel, eller finne en side fra vinkel.",
        "Use A (adjacent) and B (opposite). Calculate the angle, or find a side from an angle."
    ))

    mode = st.radio(
        tt("Velg hva du vil finne", "Choose what to find"),
        [
            tt("Finn vinkel (grader) fra A og B", "Find angle (degrees) from A and B"),
            tt("Finn B fra A og vinkel", "Find B from A and angle"),
            tt("Finn A fra B og vinkel", "Find A from B and angle"),
        ],
        horizontal=False
    )

    unit = st.selectbox(tt("Enhet for lengder", "Unit for lengths"), LENGTH_UNITS, index=2, key="ang_u")

    if tt("Finn vinkel", "Find angle") in mode:
        A = st.number_input(tt(f"A ({unit})", f"A ({unit})"), min_value=0.0, value=3.0, step=0.1, key="ang_A1")
        B = st.number_input(tt(f"B ({unit})", f"B ({unit})"), min_value=0.0, value=4.0, step=0.1, key="ang_B1")
        if st.button(tt("Beregn vinkel", "Calculate angle"), key="ang_btn1"):
            if A == 0:
                st.warning(tt("A kan ikke være 0.", "A cannot be 0."))
            else:
                theta = math.degrees(math.atan(to_m(B, unit) / to_m(A, unit)))
                C = math.sqrt(to_m(A, unit)**2 + to_m(B, unit)**2)
                st.success(f"θ = {theta:.2f}°")
                st.caption(tt(f"Hypotenus C = {fmt(from_m(C, unit))} {unit}", f"Hypotenuse C = {fmt(from_m(C, unit))} {unit}"))

    elif tt("Finn B", "Find B") in mode:
        A = st.number_input(tt(f"A ({unit})", f"A ({unit})"), min_value=0.0, value=3.0, step=0.1, key="ang_A2")
        theta = st.number_input(tt("Vinkel θ (grader)", "Angle θ (degrees)"), min_value=0.0, max_value=89.999, value=35.0, step=0.1, key="ang_t2")
        if st.button(tt("Beregn B", "Calculate B"), key="ang_btn2"):
            B_m = to_m(A, unit) * math.tan(math.radians(theta))
            st.success(f"B = {fmt(from_m(B_m, unit))} {unit}")

    else:
        B = st.number_input(tt(f"B ({unit})", f"B ({unit})"), min_value=0.0, value=4.0, step=0.1, key="ang_B3")
        theta = st.number_input(tt("Vinkel θ (grader)", "Angle θ (degrees)"), min_value=0.0, max_value=89.999, value=35.0, step=0.1, key="ang_t3")
        if st.button(tt("Beregn A", "Calculate A"), key="ang_btn3"):
            t = math.tan(math.radians(theta))
            if t == 0:
                st.warning(tt("Vinkel kan ikke være 0°.", "Angle cannot be 0°."))
            else:
                A_m = to_m(B, unit) / t
                st.success(f"A = {fmt(from_m(A_m, unit))} {unit}")

# ============================================================
# ØVINGSOPPGAVER (nivåbasert)
# ============================================================
def make_tasks(level: int):
    rnd = random.Random(1000 + level)  # stabilt sett per nivå

    tasks = []
    # nivå 1: enkle rektangel (areal/omkrets)
    if level == 1:
        for _ in range(5):
            L = rnd.choice([2, 3, 4, 5, 6, 7])
            B = rnd.choice([1, 1.5, 2, 2.5, 3])
            task_type = rnd.choice(["area", "perimeter"])
            if task_type == "area":
                tasks.append({
                    "topic": "Areal",
                    "prompt": f"Et gulv er {L} m langt og {B} m bredt. Finn arealet i m².",
                    "answer": L * B,
                    "unit": "m²",
                    "tolerance": 0.01,
                })
            else:
                tasks.append({
                    "topic": "Omkrets",
                    "prompt": f"En ramme er {L} m × {B} m. Finn omkretsen i meter.",
                    "answer": 2 * (L + B),
                    "unit": "m",
                    "tolerance": 0.01,
                })

    # nivå 2: volum + prosent (svinn)
    elif level == 2:
        for _ in range(5):
            t = rnd.choice(["volume", "waste"])
            if t == "volume":
                L = rnd.choice([2, 3, 4, 5])
                B = rnd.choice([1.5, 2, 2.5, 3])
                H = rnd.choice([0.05, 0.08, 0.1, 0.12, 0.15])
                tasks.append({
                    "topic": "Volum",
                    "prompt": f"En plate/flate er {L} m × {B} m med tykkelse {H} m. Finn volumet i m³.",
                    "answer": L * B * H,
                    "unit": "m³",
                    "tolerance": 0.001,
                })
            else:
                qty = rnd.choice([20, 25, 30, 40, 50])
                waste = rnd.choice([10, 12, 15])
                tasks.append({
                    "topic": "Prosent",
                    "prompt": f"Du trenger {qty} stk. Legg til {waste}% svinn. Hvor mange bør du bestille? (avrund opp til helt tall)",
                    "answer": math.ceil(qty * (1 + waste/100)),
                    "unit": "stk",
                    "tolerance": 0.0,
                    "integer": True
                })

    # nivå 3: diagonal + fall
    else:
        for _ in range(5):
            t = rnd.choice(["diag", "slope"])
            if t == "diag":
                a = rnd.choice([1.2, 1.5, 2.0, 2.5, 3.0])
                b = rnd.choice([1.6, 2.0, 2.4, 3.2, 4.0])
                tasks.append({
                    "topic": "Diagonal",
                    "prompt": f"En rektangulær ramme har sider a={a} m og b={b} m. Finn diagonal c i meter (2 desimaler).",
                    "answer": math.sqrt(a*a + b*b),
                    "unit": "m",
                    "tolerance": 0.02,
                })
            else:
                fall_m = rnd.choice([0.04, 0.06, 0.08, 0.1])
                lengde_m = rnd.choice([2.0, 3.0, 4.0, 5.0])
                tasks.append({
                    "topic": "Fall",
                    "prompt": f"Det er fall {fall_m} m over lengde {lengde_m} m. Finn fall i % (2 desimaler).",
                    "answer": (fall_m/lengde_m)*100,
                    "unit": "%",
                    "tolerance": 0.05,
                })

    return tasks

def arena_tasks_ui():
    st.markdown("### " + tt("Øvingsoppgaver (nivå)", "Practice tasks (levels)"))
    st.caption(tt(
        "Jobb deg gjennom nivåene. Du går videre når du har minst 4 av 5 riktige i nivået.",
        "Work through the levels. Advance when you have at least 4 out of 5 correct."
    ))

    level = st.session_state.arena_level
    st.markdown(f"<span class='bk-chip'>{tt('Nivå', 'Level')} {level}</span>", unsafe_allow_html=True)

    if level not in st.session_state.arena_taskset:
        st.session_state.arena_taskset[level] = make_tasks(level)

    tasks = st.session_state.arena_taskset[level]
    correct = st.session_state.arena_score.get(level, 0)

    st.write(tt("Svar med riktig enhet der det er relevant.", "Answer with correct unit where relevant."))
    st.divider()

    for i, t in enumerate(tasks, start=1):
        with st.container(border=True):
            st.markdown(f"**{tt('Oppgave', 'Task')} {i} – {t['topic']}**")
            st.write(t["prompt"])

            key_in = f"arena_{level}_{i}_ans"
            ans = st.text_input(tt("Ditt svar", "Your answer"), key=key_in, placeholder=t["unit"])

            colA, colB = st.columns([1.2, 2.8])
            with colA:
                if st.button(tt("Sjekk", "Check"), key=f"arena_{level}_{i}_check", use_container_width=True):
                    try:
                        if t.get("integer"):
                            user_val = int(float(ans.replace(",", ".")))
                        else:
                            user_val = float(ans.replace(",", "."))
                        ok = abs(user_val - t["answer"]) <= t["tolerance"]
                    except Exception:
                        ok = False

                    res_key = f"arena_{level}_{i}_ok"
                    if ok:
                        if not st.session_state.get(res_key, False):
                            st.session_state[res_key] = True
                            st.session_state.arena_score[level] = st.session_state.arena_score.get(level, 0) + 1
                            st.rerun()
                        else:
                            st.success(tt("Riktig ✔️", "Correct ✔️"))
                    else:
                        st.error(tt("Ikke helt. Prøv igjen.", "Not quite. Try again."))

            with colB:
                if st.toggle(tt("Vis fasit", "Show answer"), key=f"arena_{level}_{i}_show"):
                    st.info(f"{tt('Fasit', 'Answer')}: {fmt(t['answer'])} {t['unit']}")

    st.divider()
    score = st.session_state.arena_score.get(level, 0)
    st.metric(tt("Riktige i nivået", "Correct in level"), f"{score} / {len(tasks)}")

    if score >= 4:
        st.success(tt("Du kan gå videre til neste nivå!", "You can advance to the next level!"))
        if level < 3 and st.button(tt("➡️ Neste nivå", "➡️ Next level"), use_container_width=True):
            st.session_state.arena_level = level + 1
            st.rerun()
    else:
        st.info(tt("Tips: Sjekk formelbanken og bruk mellomregning.", "Tip: Use the formula bank and show working."))

    if st.button(tt("🔁 Start nivået på nytt", "🔁 Restart level"), use_container_width=True):
        # Nullstill nivå
        for i in range(1, 6):
            st.session_state.pop(f"arena_{level}_{i}_ans", None)
            st.session_state.pop(f"arena_{level}_{i}_ok", None)
            st.session_state.pop(f"arena_{level}_{i}_show", None)
        st.session_state.arena_score[level] = 0
        st.session_state.arena_taskset[level] = make_tasks(level)
        st.rerun()

def formula_bank_ui():
    st.markdown("### " + tt("Formelbank", "Formula bank"))
    st.caption(tt(
        "Forklaringer og formler (tilpasset byggfaget).",
        "Explanations and formulas (construction-focused)."
    ))

    with st.expander("📏 " + tt("Enheter og omregning", "Units and conversion"), expanded=True):
        st.markdown(tt(
            """
**Regel:** Gjør om til *samme enhet* før du regner.

- `mm → cm`: ÷ 10  
- `cm → m`: ÷ 100  
- `mm → m`: ÷ 1000  
- `m → cm`: × 100  
- `m → mm`: × 1000
            """,
            """
**Rule:** Convert to the *same unit* before calculating.

- `mm → cm`: ÷ 10  
- `cm → m`: ÷ 100  
- `mm → m`: ÷ 1000  
- `m → cm`: × 100  
- `m → mm`: × 1000
            """
        ))
        render_asset_image("enhetsomregner.png")
        verification_calculator("unit", key_prefix="arena_unit")

    with st.expander("⬛ " + tt("Areal (flate)", "Area (surface)"), expanded=False):
        formula_block(
            tt("Areal – vanlige formler", "Area – common formulas"),
            [
                "A_rektangel = lengde × bredde",
                "A_trekant = (grunnlinje × høyde) / 2",
                "A_sirkel = π × r²",
                "A_trapes = ((a + b) / 2) × h",
            ],
            [
                tt("Svar i m² når målene er i meter.", "Answer in m² when measurements are in meters."),
                tt("Trekk fra åpninger (dør/vindu) for nettoareal.", "Subtract openings for net area."),
            ],
        )
        render_asset_image("areal.png")
        verification_calculator("area_rect", key_prefix="arena_area_rect")

    with st.expander("🧵 " + tt("Omkrets (lengde rundt)", "Perimeter (length around)"), expanded=False):
        formula_block(
            tt("Omkrets – vanlige formler", "Perimeter – common formulas"),
            [
                "O_rektangel = 2 × (lengde + bredde)",
                "O_trekant = a + b + c",
                "O_sirkel = 2 × π × r  (eller π × d)",
            ],
            [
                tt("Brukes mye til lister, sviller, rammer og løpemeter.", "Often used for trim, sills and running meters."),
            ],
        )
        render_asset_image("omkrets.png")
        verification_calculator("perimeter_rect", key_prefix="arena_perimeter_rect")

    with st.expander("🧱 " + tt("Volum (mengde)", "Volume (quantity)"), expanded=False):
        formula_block(
            tt("Volum – vanlige formler", "Volume – common formulas"),
            [
                "V_boks = lengde × bredde × høyde",
                "V_plate = lengde × bredde × tykkelse",
                "V_sylinder = π × r² × h",
            ],
            [
                tt("Tykkelse står ofte i mm – gjør om til meter først.", "Thickness is often in mm — convert to meters first."),
                tt("Svar i m³.", "Answer in m³."),
            ],
        )
        render_asset_image("volum.png")
        verification_calculator("volume_box", key_prefix="arena_volume_box")

    with st.expander("📐 " + tt("Diagonal og rett vinkel (Pytagoras)", "Diagonal and right angle (Pythagoras)"), expanded=False):
        formula_block(
            tt("Pytagoras", "Pythagoras"),
            [
                "c = √(a² + b²)",
                "a = √(c² − b²)",
                "b = √(c² − a²)",
            ],
            [
                tt("Klassiker: 3–4–5 gir rett vinkel.", "Classic: 3–4–5 gives a right angle."),
            ],
        )
        render_asset_image("diagonal.png")
        verification_calculator("diagonal", key_prefix="arena_diagonal")

    with st.expander("📐 " + tt("Vinkler (trigonometri)", "Angles (trigonometry)"), expanded=False):
        formula_block(
            tt("Trig – grunnformler", "Trig – basic formulas"),
            [
                "tan(θ) = B / A",
                "θ = arctan(B / A)",
                "B = A × tan(θ)",
                "A = B / tan(θ)",
            ],
            [
                tt("Her bruker vi A=hosliggende, B=motstående.", "Here A=adjacent, B=opposite."),
            ],
        )
        angle_calculator()

    with st.expander("📐 " + tt("Målestokk", "Scale"), expanded=False):
        formula_block(
            tt("Målestokk – formler", "Scale – formulas"),
            [
                "Målestokk = tegning / virkelighet",
                "Tegning = virkelighet × målestokk",
                "Virkelighet = tegning / målestokk",
                "Ved 1:n → målestokk = 1/n",
            ],
            [
                tt("Pass på enheter (mm på tegning, m i virkelighet).", "Watch units (mm on drawing, m in reality)."),
            ],
        )

    with st.expander("📉 " + tt("Fall (gulv / sluk)", "Slope (floors / drains)"), expanded=False):
        formula_block(
            tt("Fall – formler", "Slope – formulas"),
            [
                "Fall (%) = (fall / lengde) × 100",
                "Fall (m) = (fall% / 100) × lengde",
            ],
            [
                tt("Ofte uttrykt som 1:50 (≈2%).", "Often expressed as 1:50 (≈2%)."),
            ],
        )
        render_asset_image("fall.png")
        verification_calculator("slope", key_prefix="arena_slope")

    with st.expander("🧮 " + tt("Prosent (svinn, rabatt, påslag)", "Percent (waste, discount, markup)"), expanded=False):
        formula_block(
            tt("Prosent – formler", "Percent – formulas"),
            [
                "Prosentandel = (del / hel) × 100",
                "Del = (prosent / 100) × hel",
                "Hel = del / (prosent / 100)",
                "Ny verdi = gammel verdi × (1 ± prosent/100)",
            ],
            [
                tt("Svinn: bestillingsmengde = mengde × (1 + svinn%).", "Waste: order = qty × (1 + waste%)."),
            ],
        )
        verification_calculator("percent_of", key_prefix="arena_percent_of")

# ============================================================
# LÆRINGSARENA (nytt navn + oppgaver)
# ============================================================
def show_learning_arena():
    st.markdown("## " + tt("Læringsarena", "Learning arena"))
    tab1, tab2 = st.tabs([tt("Formelbank", "Formula bank"), tt("Øvingsoppgaver", "Practice tasks")])

    with tab1:
        formula_bank_ui()

    with tab2:
        arena_tasks_ui()

# ============================================================
# BEREGNING (tilbake som egen fane)
# ============================================================
def show_working_page():
    st.markdown("## " + tt("Beregning", "Working"))
    st.caption(tt(
        "Her får eleven en struktur for mellomregning – slik man forventer i yrkesfag og vurdering.",
        "A structure for showing working — useful for assessment."
    ))

    topic = st.selectbox(
        tt("Velg tema", "Choose topic"),
        [
            tt("Areal (rektangel)", "Area (rectangle)"),
            tt("Omkrets (rektangel)", "Perimeter (rectangle)"),
            tt("Volum (boks/plate)", "Volume (box/slab)"),
            tt("Diagonal (Pytagoras)", "Diagonal (Pythagoras)"),
            tt("Fall (%)", "Slope (%)"),
            tt("Prosent (svinn)", "Percent (waste)"),
            tt("Vinkel (grader)", "Angle (degrees)"),
        ],
    )

    st.divider()

    if topic.startswith(tt("Areal", "Area")):
        unit = st.selectbox(tt("Enhet", "Unit"), LENGTH_UNITS, index=2, key="wk_a_u")
        L = st.number_input(tt(f"Lengde ({unit})", f"Length ({unit})"), min_value=0.0, value=6.0, step=0.1, key="wk_a_L")
        B = st.number_input(tt(f"Bredde ({unit})", f"Width ({unit})"), min_value=0.0, value=2.0, step=0.1, key="wk_a_B")
        st.markdown("**Formel:** `A = L × B`")
        if st.button(tt("Vis mellomregning", "Show working"), key="wk_a_btn"):
            Lm = to_m(L, unit); Bm = to_m(B, unit)
            A = Lm * Bm
            st.code(
                f"L = {L} {unit} = {fmt(Lm)} m\n"
                f"B = {B} {unit} = {fmt(Bm)} m\n"
                f"A = L × B = {fmt(Lm)} × {fmt(Bm)} = {fmt(A)} m²",
                language="text"
            )
            st.success(f"{fmt(area_from_m2(A, unit))} {unit}²  |  {fmt(A)} m²")

    elif topic.startswith(tt("Omkrets", "Perimeter")):
        unit = st.selectbox(tt("Enhet", "Unit"), LENGTH_UNITS, index=2, key="wk_o_u")
        L = st.number_input(tt(f"Lengde ({unit})", f"Length ({unit})"), min_value=0.0, value=6.0, step=0.1, key="wk_o_L")
        B = st.number_input(tt(f"Bredde ({unit})", f"Width ({unit})"), min_value=0.0, value=2.0, step=0.1, key="wk_o_B")
        st.markdown("**Formel:** `O = 2 × (L + B)`")
        if st.button(tt("Vis mellomregning", "Show working"), key="wk_o_btn"):
            Lm = to_m(L, unit); Bm = to_m(B, unit)
            O = 2 * (Lm + Bm)
            st.code(
                f"L = {L} {unit} = {fmt(Lm)} m\n"
                f"B = {B} {unit} = {fmt(Bm)} m\n"
                f"O = 2 × (L + B) = 2 × ({fmt(Lm)} + {fmt(Bm)}) = {fmt(O)} m",
                language="text"
            )
            st.success(f"{fmt(from_m(O, unit))} {unit}  |  {fmt(O)} m")

    elif topic.startswith(tt("Volum", "Volume")):
        unit = st.selectbox(tt("Enhet", "Unit"), LENGTH_UNITS, index=2, key="wk_v_u")
        L = st.number_input(tt(f"Lengde ({unit})", f"Length ({unit})"), min_value=0.0, value=6.0, step=0.1, key="wk_v_L")
        B = st.number_input(tt(f"Bredde ({unit})", f"Width ({unit})"), min_value=0.0, value=2.0, step=0.1, key="wk_v_B")
        H = st.number_input(tt(f"Høyde/tykkelse ({unit})", f"Height/thickness ({unit})"), min_value=0.0, value=0.1, step=0.01, key="wk_v_H")
        st.markdown("**Formel:** `V = L × B × H`")
        if st.button(tt("Vis mellomregning", "Show working"), key="wk_v_btn"):
            Lm = to_m(L, unit); Bm = to_m(B, unit); Hm = to_m(H, unit)
            V = Lm * Bm * Hm
            st.code(
                f"L = {L} {unit} = {fmt(Lm)} m\n"
                f"B = {B} {unit} = {fmt(Bm)} m\n"
                f"H = {H} {unit} = {fmt(Hm)} m\n"
                f"V = L × B × H = {fmt(Lm)} × {fmt(Bm)} × {fmt(Hm)} = {fmt(V)} m³",
                language="text"
            )
            st.success(f"{fmt(volume_from_m3(V, unit))} {unit}³  |  {fmt(V)} m³")

    elif topic.startswith(tt("Diagonal", "Diagonal")):
        unit = st.selectbox(tt("Enhet", "Unit"), LENGTH_UNITS, index=2, key="wk_d_u")
        a = st.number_input(tt(f"A ({unit})", f"A ({unit})"), min_value=0.0, value=3.0, step=0.1, key="wk_d_a")
        b = st.number_input(tt(f"B ({unit})", f"B ({unit})"), min_value=0.0, value=4.0, step=0.1, key="wk_d_b")
        st.markdown("**Formel:** `c = √(a² + b²)`")
        if st.button(tt("Vis mellomregning", "Show working"), key="wk_d_btn"):
            am = to_m(a, unit); bm = to_m(b, unit)
            c = math.sqrt(am*am + bm*bm)
            st.code(
                f"a = {a} {unit} = {fmt(am)} m\n"
                f"b = {b} {unit} = {fmt(bm)} m\n"
                f"c = √(a² + b²) = √({fmt(am)}² + {fmt(bm)}²) = {fmt(c)} m",
                language="text"
            )
            st.success(f"{fmt(from_m(c, unit))} {unit}  |  {fmt(c)} m")

    elif topic.startswith(tt("Fall", "Slope")):
        unit = st.selectbox(tt("Enhet", "Unit"), LENGTH_UNITS, index=2, key="wk_f_u")
        fall = st.number_input(tt(f"Fall ({unit})", f"Drop ({unit})"), min_value=0.0, value=0.08, step=0.01, key="wk_f_f")
        lengde = st.number_input(tt(f"Lengde ({unit})", f"Length ({unit})"), min_value=0.0, value=4.0, step=0.1, key="wk_f_L")
        st.markdown("**Formel:** `Fall(%) = (fall / lengde) × 100`")
        if st.button(tt("Vis mellomregning", "Show working"), key="wk_f_btn"):
            fm = to_m(fall, unit); lm = to_m(lengde, unit)
            if lm == 0:
                st.warning(tt("Lengde kan ikke være 0.", "Length cannot be 0."))
            else:
                pct = (fm/lm)*100
                st.code(
                    f"fall = {fall} {unit} = {fmt(fm)} m\n"
                    f"lengde = {lengde} {unit} = {fmt(lm)} m\n"
                    f"Fall(%) = ({fmt(fm)} / {fmt(lm)}) × 100 = {pct:.2f} %",
                    language="text"
                )
                st.success(f"{pct:.2f} %")

    elif topic.startswith(tt("Prosent", "Percent")):
        qty = st.number_input(tt("Mengde uten svinn (stk)", "Quantity without waste (pcs)"), min_value=0.0, value=40.0, step=1.0, key="wk_p_q")
        waste = st.number_input(tt("Svinn (%)", "Waste (%)"), min_value=0.0, value=10.0, step=1.0, key="wk_p_w")
        st.markdown("**Formel:** `bestilling = mengde × (1 + svinn/100)`")
        if st.button(tt("Vis mellomregning", "Show working"), key="wk_p_btn"):
            order = qty * (1 + waste/100)
            st.code(
                f"bestilling = {qty} × (1 + {waste}/100)\n"
                f"= {qty} × (1 + {waste/100:.2f})\n"
                f"= {order:.2f} → (avrund opp) {math.ceil(order)}",
                language="text"
            )
            st.success(f"{math.ceil(order)} {tt('stk', 'pcs')}")

    else:
        # vinkel
        angle_calculator()

# ============================================================
# KALKULATORER (med enhetsvalg)
# ============================================================
def show_calculators():
    st.markdown("## " + tt("Kalkulatorer", "Calculators"))
    st.caption(tt(
        "Her kan du kontrollregne. Velg enhet (mm/cm/m) der det er relevant.",
        "Verify your results. Choose unit (mm/cm/m) where relevant."
    ))

    tabs = st.tabs(
        [
            "📏 " + tt("Enhetsomregning", "Unit conversion"),
            "⬛ " + tt("Areal", "Area"),
            "🧵 " + tt("Omkrets", "Perimeter"),
            "🧱 " + tt("Volum", "Volume"),
            "📐 " + tt("Diagonal", "Diagonal"),
            "📐 " + tt("Vinkler", "Angles"),
            "📉 " + tt("Fall", "Slope"),
            "🧮 " + tt("Prosent", "Percent"),
        ]
    )

    with tabs[0]:
        verification_calculator("unit", key_prefix="tab_unit")

    with tabs[1]:
        verification_calculator("area_rect", key_prefix="tab_area_rect")

    with tabs[2]:
        verification_calculator("perimeter_rect", key_prefix="tab_perimeter_rect")

    with tabs[3]:
        verification_calculator("volume_box", key_prefix="tab_volume_box")

    with tabs[4]:
        verification_calculator("diagonal", key_prefix="tab_diagonal")

    with tabs[5]:
        angle_calculator()

    with tabs[6]:
        verification_calculator("slope", key_prefix="tab_slope")

    with tabs[7]:
        verification_calculator("percent_of", key_prefix="tab_percent_of")

# ============================================================
# PRO (info + lås)
# ============================================================
def pro_paywall():
    st.warning(
        tt(
            f"«Alt dere trenger for å forstå og bestå faget ligger i gratisdelen.\n"
            f"I denne versjonen er for dere som vil øve mer, bli tryggere og dokumentere bedre.\n"
            f"Denne koster {PRO_PRICE_MONTH} kr/mnd (eller {PRO_PRICE_YEAR} kr/år) for å komme videre.»",
            f"“Everything you need to understand and pass is in the free version.\n"
            f"This version is for those who want more practice, confidence and better documentation.\n"
            f"This costs {PRO_PRICE_MONTH} NOK/month (or {PRO_PRICE_YEAR} NOK/year) to continue.”",
        )
    )
    st.caption(tt(
        "Dette er en betalingslås. Når du ønsker det, kan vi koble dette til Stripe/Vipps.",
        "This is a paywall. When you’re ready, we can connect this to Stripe/Vipps."
    ))

def show_pro_page():
    st.markdown("## 🔒 " + tt("Ønsker du å utvikle deg enda mere?", "Want to develop even more?"))
    st.markdown(
        tt(
            f"""
I Pro-versjonen finner du **utvidet innhold**, for eksempel:
- Nivåbaserte øvingsoppgaver (med tydelig progresjon)
- Mer vurderingsrettet støtte (egenkontroll, dokumentasjon)
- Flere praktiske case knyttet til verksted og byggeplass
- TEK-kravene i byggebransjen
- Hvorfor er HMS så viktig?
- Verktøyopplæring og tegneforståelse

> «Alt dere trenger for å forstå og bestå fagene ligger i gratisdelen.  
> I denne versjonen er for dere som vil øve mer, bli tryggere og dokumentere bedre.  
> Denne koster **{PRO_PRICE_MONTH} kr/mnd** (eller **{PRO_PRICE_YEAR} kr/år**) for å komme videre»
            """,
            f"""
In the Pro version you get extended content:
- Level-based practice tasks
- Assessment-oriented support
- Practical cases linked to workshop/site
- Regulations (TEK), HSE, tool training, drawings

> “Everything you need to pass is in the free version.  
> Pro is for extra practice, confidence and documentation.  
> This costs **{PRO_PRICE_MONTH} NOK/month** (or **{PRO_PRICE_YEAR} NOK/year**) to continue.”
            """
        )
    )

    st.divider()
    c1, c2, c3 = st.columns([1.2, 1.6, 2.2])

    with c1:
        if st.button("💳 " + tt(f"{PRO_PRICE_MONTH} kr / mnd (pilot)", f"{PRO_PRICE_MONTH} NOK / month (pilot)"), use_container_width=True):
            pro_paywall()
            st.stop()

    with c2:
        code = st.text_input(tt("Lærerkode (lærer)", "Teacher code"), type="password", key="teacher_code_pro_page")
        if code == TEACHER_CODE:
            st.session_state.is_pro_user = True
            st.session_state.pro_teacher_mode = True
            st.success(tt("Lærertilgang aktiv.", "Teacher access enabled."))

    with c3:
        st.caption(tt(
            "Lærerkode gir tilgang i pilotperioden (for lærere/klasserom).",
            "Teacher code grants access during the pilot (teachers/classroom)."
        ))

    st.divider()

    can_open = bool(st.session_state.get("is_pro_user", False))
    if st.button("📦 " + tt("Gå til Pro-innhold", "Go to Pro content"), use_container_width=True, disabled=not can_open):
        st.session_state.view = "ProInnhold"
        st.rerun()

    st.caption(tt(
        "Elever trenger ikke Pro for å bestå: gratisdelen er laget som et komplett undervisningsopplegg.",
        "Students don't need Pro to pass: the free part is designed as a complete learning sequence."
    ))

def show_pro_content():
    st.markdown("## 🔓 " + tt("Pro-innhold", "Pro content"))
    st.caption(tt(
        "Her ligger utvidet innhold. Gratisversjonen er fullt brukbar som undervisningsopplegg.",
        "Extended content lives here. The free version is fully usable as a learning sequence."
    ))

    with st.container(border=True):
        st.markdown("**" + tt("Lærertilgang (pilot)", "Teacher access (pilot)") + "**")
        teacher_code = st.text_input(tt("Lærerkode", "Teacher code"), type="password", key="teacher_code_pro_content")
        cta1, cta2 = st.columns([1.2, 2.8])
        with cta1:
            if st.button("🔑 " + tt("Lås opp", "Unlock"), use_container_width=True):
                if teacher_code == TEACHER_CODE:
                    st.session_state.is_pro_user = True
                    st.session_state.pro_teacher_mode = True
                    st.success(tt("Lærertilgang aktiv.", "Teacher access enabled."))
                    st.rerun()
                else:
                    st.error(tt("Feil kode.", "Wrong code."))
        with cta2:
            st.caption(tt("Koden gir tilgang i pilotperioden.", "Code grants access during the pilot."))

    sections = [
        ("🧩 " + tt("Oppgaver (nivå og progresjon)", "Tasks (levels and progression)"), "oppgaver"),
        ("🦺 " + tt("HMS – Hvorfor er HMS viktig?", "HSE – Why HSE matters"), "hms"),
        ("🏗️ " + tt("TEK-krav i praksis (enkel oversikt)", "Building regulations (TEK) in practice"), "tek"),
        ("🪚 " + tt("Verktøyopplæring", "Tool training"), "verktoy"),
        ("📝 " + tt("Dokumentasjon av eget arbeid", "Documentation of your work"), "dokumentasjon"),
    ]
    labels = [s[0] for s in sections]
    keys = {s[0]: s[1] for s in sections}
    pick = st.radio(tt("Velg Pro-del", "Choose Pro section"), labels, horizontal=False)
    key = keys[pick]
    st.divider()

    if not st.session_state.is_pro_user:
        st.markdown("### " + pick)
        st.markdown(tt("Dette er Pro. For å komme videre må du ha tilgang.", "This is Pro. Access is required."))
        pro_paywall()
        return

    st.success(tt("Pro er aktiv ✔️", "Pro is active ✔️"))
    st.markdown("### " + pick)

    if key == "oppgaver":
        st.markdown(tt(
            """
**Struktur (slik Pro-oppgavene er bygget):**
- Nivå 1: velg formel + enheter
- Nivå 2: mellomregning
- Nivå 3: egenkontroll + refleksjon

Her kan vi legge inn samme oppgavebank som i tidligere versjon (ordrett), delt per tema.
            """,
            """
**Structure:**
Level 1 formula+units, Level 2 working, Level 3 self-check+reflection.
            """
        ))
    elif key == "hms":
        st.markdown(tt(
            """
**Kort HMS-oppsett til BA verksted/byggeplass**
- Før: plan + PVU + rydd/orden
- Under: rutiner + stopp ved endring
- Etter: rydd + avvik + logg

**Mini SJA (3 spørsmål):**
1) Hva kan gå galt?  
2) Hvordan forebygger vi?  
3) Hva gjør vi hvis det skjer?
            """,
            "HSE plan–do–check with a mini risk assessment."
        ))
    elif key == "tek":
        st.markdown(tt(
            """
**TEK i praksis (elevnivå)**
- Sikkerhet (rekkverk, orden, fallfare)
- Fukt (tetting, overganger, lufting)
- Brann (materialvalg, gjennomføringer – begrepsnivå)
- Universell utforming (terskler, bredder – begrepsnivå)

Pro kan gi korte “TEK-kort” til oppgaver (5 min lesing) som elever bruker i dokumentasjon.
            """,
            "Simple TEK overview + TEK-cards for tasks."
        ))
    elif key == "verktoy":
        st.markdown(tt(
            """
**Verktøyopplæring (struktur)**
1) Før: kontroll + PVU + innstillinger  
2) Under: håndplassering + sikring av emne  
3) Etter: stopp + rengjøring + vedlikehold

**Dokumentasjon:** 3 bilder + 5–8 setninger (rutine/risiko/tiltak).
            """,
            "Tool training structure + documentation."
        ))
    else:
        st.markdown(tt(
            """
**Dokumentasjon av eget arbeid**
- Mål og kontrollmålinger (før/etter)
- Materialvalg (dimensjoner/impregnert)
- Avvik og tiltak
- HMS: risikovurdering + PVU

**Mal (elev):**
Oppgave – Mål/enheter – Formelvalg – Mellomregning – Kontroll – Avvik – Refleksjon.
            """,
            "Documentation template."
        ))

# ============================================================
# Router
# ============================================================
if st.session_state.view == "Forside":
    show_front_page()
elif st.session_state.view == "Læringsarena":
    show_learning_arena()
elif st.session_state.view == "Beregning":
    show_working_page()
elif st.session_state.view == "Kalkulatorer":
    show_calculators()
elif st.session_state.view == "Pro":
    show_pro_page()
elif st.session_state.view == "ProInnhold":
    show_pro_content()
else:
    show_front_page()


import math
from pathlib import Path
import random
import time
import json
import os
import streamlit as st
from PIL import Image

try:
    import pandas as pd
except Exception:
    pd = None

# ==========================
# Pro-konfig (enkelt å endre)
# ==========================
PRO_PRICE_MONTH = 29  # kr per måned (pilot)
PRO_PRICE_YEAR = 299  # kr per år (pilot)
TEACHER_CODE = "2150"

# ==========================
# Lokal lagring (progresjon)
# ==========================
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
PROGRESS_FILE = DATA_DIR / "progress.json"


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

# Veien til yrkeslivet (BETA) tilgang
if "vty_access" not in st.session_state:
    st.session_state.vty_access = False
if "vty_teacher_mode" not in st.session_state:
    st.session_state.vty_teacher_mode = False

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
            <div class="bk-title"></div>
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
    if st.button("📚 " + tt("Læringsarena", "Learning arena"), use_container_width=True, key="top_nav_arena"):
        st.session_state.view = "Læringsarena"
        st.rerun()

with b3:
    if st.button("🧾 " + tt("Beregning", "Working"), use_container_width=True, key="nav_working"):
        st.session_state.view = "Beregning"
        st.rerun()

with b4:
    if st.button("🧮 " + tt("Kalkulatorer", "Calculators"), use_container_width=True, key="top_nav_calcs"):
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
        st.caption(tt("Veien til yrkeslivet gir ekstra øving, dokumentasjon og vurderingsstøtte.",
                      "Pro adds extra practice, documentation and assessment support."))
        if st.button("📜" + tt("Veien til yrkeslivet (BETA)", "The path to professional life (BETA)"), use_container_width=True):
            st.session_state.view = "VeienTilYrkeslivet_Lås"
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
        ("VeienTilYrkeslivet_Lås", tt("Veien til yrkeslivet (BETA)", "Path to professional life (BETA)")),
        ("VeienTilYrkeslivet_Innhold", tt("Yrkeslivet: oppgaver", "Workplace: tasks")),
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


def to_mm(value: float, unit: str) -> float:
    """Konverter lengde til millimeter."""
    return to_m(value, unit) * 1000.0


def mm_to_all(mm: float) -> dict:
    """Hjelpevisning: mm -> mm/cm/m."""
    return {"mm": mm, "cm": mm / 10.0, "m": mm / 1000.0}


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
# Progresjon: lagre/hente per elev-ID (lokal JSON-fil)
# ============================================================
def load_progress_db() -> dict:
    if PROGRESS_FILE.exists():
        try:
            return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_progress_db(db: dict) -> None:
    try:
        PROGRESS_FILE.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

def get_student_record(db: dict, student_id: str) -> dict:
    return db.get(student_id, {
        "student_id": student_id,
        "class_name": "",
        "global_level": 1,
        "completed_topics": {},
        "topics": {},
        "updated_at": time.time()
    })

def put_student_record(db: dict, record: dict) -> None:
    record["updated_at"] = time.time()
    db[record["student_id"]] = record

LEVELS = [
    (1, "7. trinn", "Grade 7"),
    (2, "8. trinn", "Grade 8"),
    (3, "9. trinn", "Grade 9"),
    (4, "10. trinn", "Grade 10"),
    (5, "VG1 (grunnnivå)", "VG1 (foundation)"),
    (6, "VG2 (videre)", "VG2 (intermediate)"),
    (7, "VG3 (lærling-nivå)", "VG3 (apprentice level)"),
]

REQUIRED_TOPICS_PER_LEVEL = 3  # må bestå 3 tema i nivået for å låse opp neste

TOPICS = [
    ("areal", "Areal", "Area"),
    ("omkrets", "Omkrets", "Perimeter"),
    ("vinkler", "Vinkler", "Angles"),
    ("enheter", "Enhetsomregning", "Unit conversion"),
    ("volum", "Volum", "Volume"),
    ("diagonal", "Diagonal", "Diagonal"),
    ("fall", "Fall", "Slope"),
    ("prosent", "Prosent", "Percent"),
]

def topic_label(topic_key: str) -> str:
    for k, no, en in TOPICS:
        if k == topic_key:
            return tt(no, en)
    return topic_key

def level_label(level: int) -> str:
    for lv, no, en in LEVELS:
        if lv == level:
            return tt(no, en)
    return str(level)

def ensure_topic_level_state(record: dict, topic_key: str, level: int) -> None:
    """
    Lagrer progresjon per tema per globalt nivå:
    record["topics"][topic_key]["levels"][str(level)] = stats
    """
    topics = record.setdefault("topics", {})
    t = topics.setdefault(topic_key, {"levels": {}})
    levels = t.setdefault("levels", {})
    key = str(level)
    if key not in levels:
        levels[key] = {
            "q_index": 0,
            "correct": 0,
            "answered": 0,
            "total_correct": 0,
            "total_answered": 0,
            "passed": False,
        }

def deterministic_rng(student_id: str, topic_key: str, level: int):
    seed = abs(hash(f"{student_id}:{topic_key}:{level}")) % (2**32)
    return random.Random(seed)

def generate_question(student_id: str, topic_key: str, level: int, qn: int) -> dict:
    """
    10 spørsmål per tema per nivå (qn=0..9).
    Vokser fra 7. trinn -> VG3 lærling.
    """
    rnd = deterministic_rng(student_id, topic_key, level)
    # deterministisk "shuffle" frem til index
    for _ in range(qn + 5):
        rnd.random()

    # Hjelpere for nivåtilpassede tall
    def pick_len_small():  # barneskole
        return rnd.choice([2, 3, 4, 5, 6, 7, 8])

    def pick_len_med():  # ungdomsskole
        return rnd.choice([2.4, 3.0, 3.6, 4.2, 4.8, 5.4, 6.0])

    def pick_len_large():  # vgs/lærling
        return rnd.choice([6.0, 7.2, 8.4, 9.6, 10.8, 12.0])

    def with_opening(area, level):
        # VG1+ trekker fra åpning 0.9x2.1
        if level >= 5 and rnd.random() < 0.5:
            return max(0.0, area - (0.9 * 2.1)), True
        return area, False

    if topic_key == "areal":
        if level <= 2:
            L = pick_len_small()
            B = rnd.choice([1, 2, 3, 4, 5])
            return {"prompt": f"Finn arealet av et rektangel: L={L} m og B={B} m. (m²)",
                    "answer": L * B, "unit": "m²", "tol": 0.01}
        if level <= 4:
            L = pick_len_med()
            B = rnd.choice([2.0, 2.5, 3.0, 3.5, 4.0])
            return {"prompt": f"Et rom er {L} m langt og {B} m bredt. Finn gulvarealet (m²).",
                    "answer": L * B, "unit": "m²", "tol": 0.02}
        # VG1-VG3: vegg/gulv med åpning og svinn
        H = rnd.choice([2.4, 2.7, 3.0])
        L = pick_len_large()
        area = H * L
        area2, opening = with_opening(area, level)
        if opening:
            return {"prompt": f"En vegg er {L} m lang og {H} m høy. Trekk fra én dør (0,9×2,1 m). Finn nettoareal (m²).",
                    "answer": area2, "unit": "m²", "tol": 0.05}
        return {"prompt": f"En vegg er {L} m lang og {H} m høy. Finn arealet (m²).",
                "answer": area2, "unit": "m²", "tol": 0.05}

    if topic_key == "omkrets":
        if level <= 2:
            L = pick_len_small()
            B = rnd.choice([1, 2, 3, 4, 5])
            return {"prompt": f"Finn omkretsen av et rektangel: L={L} m og B={B} m. (m)",
                    "answer": 2 * (L + B), "unit": "m", "tol": 0.01}
        if level <= 4:
            L = pick_len_med()
            B = rnd.choice([2.0, 2.5, 3.0, 3.5])
            return {"prompt": f"Du skal sette gulvlister rundt et rom {L} m × {B} m. Finn omkrets (m).",
                    "answer": 2 * (L + B), "unit": "m", "tol": 0.02}
        # VG1+: løpemeter + svinn
        L = pick_len_large()
        B = rnd.choice([3.6, 4.2, 4.8, 5.4])
        base = 2 * (L + B)
        if level >= 6:
            waste = rnd.choice([5, 8, 10])
            return {"prompt": f"Du skal ha lister rundt et rom {L} m × {B} m. Legg til {waste}% svinn. Hvor mange meter bestiller du?",
                    "answer": base * (1 + waste/100), "unit": "m", "tol": 0.2}
        return {"prompt": f"Du skal ha lister rundt et rom {L} m × {B} m. Finn løpemeter (m).",
                "answer": base, "unit": "m", "tol": 0.05}

    if topic_key == "enheter":
        # nivåøkning: mer realistiske byggmål og flere steg
        if level <= 2:
            val = rnd.choice([10, 25, 50, 120, 250, 500, 1000])
            return {"prompt": f"Gjør om {val} mm til cm.", "answer": val/10, "unit": "cm", "tol": 0.001}
        if level <= 4:
            val = rnd.choice([30, 45, 60, 90, 120, 150, 240])
            return {"prompt": f"Gjør om {val} cm til meter (m).", "answer": val/100, "unit": "m", "tol": 0.0005}
        # VG1+: blandede enheter slik elevene møter i verksted
        choice = rnd.choice([
            ("mm", "m", rnd.choice([18, 22, 48, 70, 98, 148])),
            ("m", "mm", rnd.choice([0.6, 1.2, 2.4, 3.6])),
            ("cm", "mm", rnd.choice([7.3, 9.8, 14.8])),
            ("mm", "cm", rnd.choice([600, 1200, 2400, 3600])),
        ])
        frm, to, val = choice
        if frm == "mm" and to == "m":
            ans = val/1000
        elif frm == "m" and to == "mm":
            ans = val*1000
        elif frm == "cm" and to == "mm":
            ans = val*10
        else:
            ans = val/10
        return {"prompt": f"Gjør om {val} {frm} til {to}.", "answer": ans, "unit": to, "tol": 0.01 if to=="mm" else 0.001}

    if topic_key == "vinkler":
        # rettvinklet trekant med A (hosliggende) og B (motstående): A, B = C og vinkler
        if level <= 3:
            A = rnd.choice([2,3,4,5,6])
            B = rnd.choice([1,2,3,4])
            theta = math.degrees(math.atan(B/A))
            return {"prompt": f"Rettvinklet trekant: A={A} og B={B}. Finn vinkelen θ (grader).",
                    "answer": theta, "unit": "°", "tol": 0.6}
        if level <= 5:
            A = rnd.choice([2.4, 3.0, 3.6, 4.2])
            theta = rnd.choice([15, 20, 25, 30, 35, 40, 45])
            B = A * math.tan(math.radians(theta))
            return {"prompt": f"Du skal lage skråavstivning. A={A} m og θ={theta}°. Finn B (m).",
                    "answer": B, "unit": "m", "tol": 0.05}
        # VG2/VG3: takvinkel/utstikk (mer realistiske tall)
        run = rnd.choice([3.6, 4.2, 4.8, 5.4])
        rise = rnd.choice([1.2, 1.5, 1.8, 2.1])
        theta = math.degrees(math.atan(rise/run))
        return {"prompt": f"Tak: horisontal lengde (A)={run} m og høyde (B)={rise} m. Finn takvinkel θ (grader).",
                "answer": theta, "unit": "°", "tol": 0.6}

    if topic_key == "diagonal":
        if level <= 3:
            a = rnd.choice([3,4,5,6])
            b = rnd.choice([4,5,6,7,8])
            return {"prompt": f"Finn diagonal C når A={a} og B={b}. (C = √(A²+B²))",
                    "answer": math.sqrt(a*a+b*b), "unit": "", "tol": 0.1}
        if level <= 5:
            a = rnd.choice([1.2, 2.4, 3.6, 4.8])
            b = rnd.choice([1.6, 2.0, 3.2, 4.0])
            return {"prompt": f"Ramme: A={a} m og B={b} m. Finn diagonal C (m) for å sjekke vinkel.",
                    "answer": math.sqrt(a*a+b*b), "unit": "m", "tol": 0.03}
        # VG2/VG3: 3-4-5 skalert
        k = rnd.choice([1.0, 1.5, 2.0, 2.5])
        a = 3*k; b = 4*k; c = 5*k
        ask = rnd.choice(["c", "a", "b"])
        if ask == "c":
            return {"prompt": f"Kontrollmål: A={a} m og B={b} m. Hva skal C være (m) for rett vinkel?",
                    "answer": c, "unit": "m", "tol": 0.05}
        if ask == "a":
            return {"prompt": f"Kontrollmål: C={c} m og B={b} m. Hva skal A være (m)?",
                    "answer": a, "unit": "m", "tol": 0.05}
        return {"prompt": f"Kontrollmål: C={c} m og A={a} m. Hva skal B være (m)?",
                "answer": b, "unit": "m", "tol": 0.05}

    if topic_key == "volum":
        if level <= 3:
            L = rnd.choice([2,3,4,5])
            B = rnd.choice([1,2,3])
            H = rnd.choice([1,2,3])
            return {"prompt": f"Finn volum: L={L}, B={B}, H={H}. (V=L×B×H)",
                    "answer": L*B*H, "unit": "", "tol": 0.01}
        if level <= 5:
            L = rnd.choice([2.4, 3.6, 4.8, 6.0])
            B = rnd.choice([1.2, 2.4, 3.0])
            t = rnd.choice([0.05, 0.08, 0.10])
            return {"prompt": f"Betongplate: {L} m × {B} m × {t} m. Finn volum (m³).",
                    "answer": L*B*t, "unit": "m³", "tol": 0.01}
        # VG2/VG3: tykkelse i mm
        L = rnd.choice([6.0, 7.2, 8.4])
        B = rnd.choice([2.4, 3.0, 3.6])
        tmm = rnd.choice([80, 100, 120, 150])
        return {"prompt": f"Plate: {L} m × {B} m × {tmm} mm. Finn volum (m³).",
                "answer": L*B*(tmm/1000), "unit": "m³", "tol": 0.02}

    if topic_key == "fall":
        if level <= 3:
            fall_cm = rnd.choice([2,3,4,5,6])
            lengde_m = rnd.choice([2,3,4,5])
            fall_m = fall_cm/100
            return {"prompt": f"Fall er {fall_cm} cm over {lengde_m} m. Finn fall i %.",
                    "answer": (fall_m/lengde_m)*100, "unit": "%", "tol": 0.2}
        if level <= 5:
            fall_mm_per_m = rnd.choice([10, 15, 20, 25])
            lengde_m = rnd.choice([2.0, 3.0, 4.0, 5.0])
            fall_mm = fall_mm_per_m*lengde_m
            return {"prompt": f"Du har fall {fall_mm_per_m} mm per meter over {lengde_m} m. Hvor mange mm fall totalt?",
                    "answer": fall_mm, "unit": "mm", "tol": 1.0}
        # VG2/VG3: fall i % -> mm
        pct = rnd.choice([1.0, 1.5, 2.0, 2.5])
        lengde_m = rnd.choice([3.0, 4.0, 5.0, 6.0])
        fall_mm = (pct/100)*lengde_m*1000
        return {"prompt": f"Prosjekt: Fall {pct}% over {lengde_m} m. Hvor mange mm fall blir det?",
                "answer": fall_mm, "unit": "mm", "tol": 2.0}

    if topic_key == "prosent":
        if level <= 3:
            base = rnd.choice([50, 80, 100, 120, 200])
            p = rnd.choice([10, 20, 25, 50])
            return {"prompt": f"Hva er {p}% av {base}?",
                    "answer": (p/100)*base, "unit": "", "tol": 0.2}
        if level <= 5:
            qty = rnd.choice([20, 25, 30, 40, 50])
            waste = rnd.choice([5, 10, 12, 15])
            return {"prompt": f"Du trenger {qty} stk. Legg til {waste}% svinn. Hvor mange bestiller du? (avrund opp)",
                    "answer": math.ceil(qty*(1+waste/100)), "unit": "stk", "tol": 0.0, "integer": True}
        # VG2/VG3: prisendring
        old = rnd.choice([1200, 1500, 2000, 2500, 3200])
        change = rnd.choice([8, 10, 12, 15, 20])
        direction = rnd.choice(["opp", "ned"])
        if direction == "opp":
            return {"prompt": f"En vare koster {old} kr. Prisøkning {change}%. Hva er ny pris?",
                    "answer": old*(1+change/100), "unit": "kr", "tol": 1.0}
        return {"prompt": f"En vare koster {old} kr. Rabatt {change}%. Hva er ny pris?",
                "answer": old*(1-change/100), "unit": "kr", "tol": 1.0}

    return {"prompt": "(mangler)", "answer": 0.0, "unit": "", "tol": 0.0}

def check_answer(user_text: str, q: dict):
    try:
        s = (user_text or "").strip().replace(",", ".")
        if s == "":
            return False, None
        if q.get("integer"):
            v = int(float(s))
        else:
            v = float(s)
        ok = abs(v - float(q["answer"])) <= float(q.get("tol", 0.0))
        return ok, v
    except Exception:
        return False, None

# ============================================================
# FORSIDE
# ============================================================
def show_front_page():
    left, right = st.columns([1.25, 1], gap="large")

    with left:
        st.markdown("## " + tt("Lær praktisk matematikk som brukes i yrkeslivet!", "Learn practical mathematics in your professional life!"))
        st.markdown(
            tt(
                """
I denne appen lærer du ikke bare å regne.
Du lærer å forstå oppgaven, velge riktig formel, regne selv og kontrollere svaret ditt – akkurat slik en fagarbeider gjør.

Her jobber vi med praktiske oppgaver hentet fra byggfaget.
Du øver på å tenke som en yrkesutøver, ikke som en kalkulator.

I **Læringsarenaen** finner du:
Formler, eksempler og oppgaver i ulike nivåer.
Regn for hånd først – bruk kalkulatoren kun som kontroll.

Målet er at du skal bli trygg på regningene du gjør,
slik at du kan stole på dem i verkstedet – og senere i yrket ditt.

### Hvorfor trenger vi matematikk når vi bygger?
Du bruker matematikk for å:
- Bestille riktig mengde materialer
- Kostnader på både produksjon og ulike materialer vi bruker
- Velge riktig materialer til riktig bruk  
- Forståelse av å lese og bruke arbeidstegninger og målestokk 
- Dokumentere eget arbeid og gjøre egenkontroll  


### Dette finner du i appen:
1. **Læringsarena** - Formelbank, øvingsoppgaver, gjett formelen.
2. **Beregninger** - Struktur for mellomregning – slik man forventer i yrkesfag og vurdering.
3. **Kalkulator** - Kontrollsjekk at din regning er riktig
4. **Veien til yrkeslivet** - Denne betalte versjonen gir deg ekstra øving, dokumentasjon, vurderingsstøtte og forståelse for et VG3 nivå.
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
                if st.button("📚 " + tt("Læringsarena", "Learning arena"), use_container_width=True, key="front_nav_arena"):
                    st.session_state.view = "Læringsarena"
                    st.rerun()
            with c2:
                if st.button("🧮 " + tt("Kalkulatorer", "Calculators"), use_container_width=True, key="front_nav_calcs"):
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
    # Unique instance prefix to avoid StreamlitDuplicateElementKey when the same
    # calculator UI is rendered in multiple tabs/containers.
    _uid = st.session_state.get('_vc_uid', 0)
    st.session_state['_vc_uid'] = _uid + 1
    kp = f"{key_prefix}_{_uid}" if key_prefix else f"vc_{_uid}"
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
    st.markdown("### " + tt("Øvingsoppgaver", "Practice tasks"))
    st.caption(tt(
        "Velg selv hvilke formler/tema du vil øve på. Når du har bestått nok tema i nivået, låser du opp neste nivå.",
        "Choose which formulas/topics to practice. When you pass enough topics in a level, you unlock the next level."
    ))

    db = load_progress_db()

    with st.container(border=True):
        c1, c2, c3 = st.columns([1.2, 1.4, 1.4])
        with c1:
            student_id = st.text_input(tt("Elev-ID", "Student ID"), key="arena_student_id", placeholder="f.eks. VG1BA-12")
        with c2:
            class_name = st.text_input(tt("Klasse", "Class"), key="arena_class_name", placeholder="f.eks. VG1BA-1")
        with c3:
            teacher_code = st.text_input(
                tt("Lærerkode (lærer)", "Teacher code (teacher)"),
                type="password",
                key="arena_teacher_code",
                placeholder=""
            )

        teacher_mode = (teacher_code == TEACHER_CODE) if teacher_code else False

    # Læreroversikt
    if teacher_mode:
        st.success(tt("Lærermodus aktiv.", "Teacher mode enabled."))
        st.markdown("#### " + tt("Læreroversikt (progresjon)", "Teacher overview (progress)"))
        records = []
        for sid, rec in db.items():
            if class_name and rec.get("class_name","") != class_name:
                continue
            glv = int(rec.get("global_level", 1))
            comp = rec.get("completed_topics", {}).get(str(glv), [])
            row = {
                "Elev-ID": sid,
                "Klasse": rec.get("class_name",""),
                tt("Nivå", "Level"): f"{glv} – {level_label(glv)}",
                tt("Bestått i nivået", "Passed in level"): f"{len(comp)}/{REQUIRED_TOPICS_PER_LEVEL}",
            }
            for k, no, en in TOPICS:
                t = rec.get("topics", {}).get(k, {})
                lv_state = (t.get("levels", {}) or {}).get(str(glv), {})
                row[tt(no,en)] = "✔️" if lv_state.get("passed") else "—"
            records.append(row)

        if records and pd is not None:
            st.dataframe(pd.DataFrame(records), use_container_width=True, hide_index=True)
        elif records:
            for r in records:
                st.write(r)
        else:
            st.info(tt("Ingen elever lagret ennå for valgt klasse.", "No saved students yet for selected class."))
        st.divider()

    if not student_id:
        st.info(tt("Skriv inn Elev-ID for å starte.", "Enter a Student ID to start."))
        return

    # Hent elev
    rec = get_student_record(db, student_id)
    if class_name:
        rec["class_name"] = class_name
    rec.setdefault("global_level", 1)
    rec.setdefault("completed_topics", {})
    put_student_record(db, rec); save_progress_db(db)

    global_level = int(rec.get("global_level", 1))
    global_level = max(1, min(7, global_level))
    level_name = level_label(global_level)

    st.markdown(f"**{tt('Ditt nivå', 'Your level')}:** {global_level} – {level_name}")
    st.caption(tt(
        f"For å gå videre må du bestå {REQUIRED_TOPICS_PER_LEVEL} ulike tema (8 av 10 riktige) på dette nivået.",
        f"To advance you must pass {REQUIRED_TOPICS_PER_LEVEL} different topics (8/10 correct) on this level."
    ))

    completed = rec.get("completed_topics", {}).get(str(global_level), [])
    st.markdown(f"**{tt('Beståtte tema i nivået', 'Passed topics in this level')}:** {len(completed)}/{REQUIRED_TOPICS_PER_LEVEL}")
    if completed:
        st.write(", ".join([topic_label(x) for x in completed]))

    st.divider()
    st.markdown("#### " + tt("Velg hva du vil øve på", "Choose what to practice"))

    # --- Tema som faner (eleven velger selv) ---
    topic_keys = [k for k,_,_ in TOPICS]
    topic_titles = [topic_label(k) for k in topic_keys]
    tabs = st.tabs(topic_titles)

    def render_topic(topic_key: str, pick_label: str):
        ensure_topic_level_state(rec, topic_key, global_level)
        t = rec["topics"][topic_key]["levels"][str(global_level)]

        q_index = int(t.get("q_index", 0))
        q_index = max(0, min(9, q_index))
        q = generate_question(student_id, topic_key, global_level, q_index)

        with st.container(border=True):
            st.markdown(f"### {tt('Oppgave', 'Task')} {q_index+1}/10 · {pick_label}")
            st.write(q["prompt"])
            ans = st.text_input(tt("Ditt svar", "Your answer"), key=f"arena_answer_{topic_key}", placeholder=q.get("unit",""))

            cA, cB, cC = st.columns([1.0, 1.0, 2.0])
            with cA:
                if st.button(tt("Sjekk", "Check"), key=f"arena_check_{topic_key}_{global_level}_{q_index}", use_container_width=True):
                    ok, _ = check_answer(ans, q)
                    t["answered"] = int(t.get("answered", 0)) + 1
                    t["total_answered"] = int(t.get("total_answered", 0)) + 1
                    if ok:
                        t["correct"] = int(t.get("correct", 0)) + 1
                        t["total_correct"] = int(t.get("total_correct", 0)) + 1
                        st.success(tt("Riktig ✔️", "Correct ✔️"))
                    else:
                        st.error(tt("Ikke helt. Du kan prøve igjen senere i neste runde.", "Not quite. You can try again later."))

                    t["q_index"] = min(9, q_index + 1)
                    rec["topics"][topic_key]["levels"][str(global_level)] = t
                    put_student_record(db, rec); save_progress_db(db)
                    st.rerun()

            with cB:
                if st.button(tt("Pass", "Pass"), key=f"arena_pass_{topic_key}_{global_level}_{q_index}", use_container_width=True):
                    t["answered"] = int(t.get("answered", 0)) + 1
                    t["total_answered"] = int(t.get("total_answered", 0)) + 1
                    t["q_index"] = min(9, q_index + 1)
                    rec["topics"][topic_key]["levels"][str(global_level)] = t
                    put_student_record(db, rec); save_progress_db(db)
                    st.rerun()

            with cC:
                # Fasit kun for lærer (kode tastes inn ved behov)
                if teacher_mode:
                    if st.toggle(tt("Vis fasit", "Show answer"), key=f"arena_show_{topic_key}_{global_level}_{q_index}"):
                        st.info(f"{tt('Fasit', 'Answer')}: {fmt(q['answer'])} {q.get('unit','')}".strip())

        st.metric(tt("Riktige", "Correct"), f"{t.get('correct',0)} / 10")
        st.metric(tt("Besvart", "Answered"), f"{t.get('answered',0)} / 10")

        finished = int(t.get("answered", 0)) >= 10
        if finished:
            if int(t.get("correct", 0)) >= 8:
                st.success(tt("Tema bestått på dette nivået!", "Topic passed on this level!"))
                t["passed"] = True
                comp = rec.setdefault("completed_topics", {}).setdefault(str(global_level), [])
                if topic_key not in comp:
                    comp.append(topic_key)
                rec["completed_topics"][str(global_level)] = comp
                rec["topics"][topic_key]["levels"][str(global_level)] = t
                put_student_record(db, rec); save_progress_db(db)

                comp = rec.get("completed_topics", {}).get(str(global_level), [])
                if len(comp) >= REQUIRED_TOPICS_PER_LEVEL:
                    st.success(tt("Du har bestått nok tema til å gå videre!", "You passed enough topics to advance!"))
                    if global_level < 7:
                        if st.button(tt("➡️ Gå til neste nivå", "➡️ Go to next level"),
                                     key=f"arena_advance_{global_level}", use_container_width=True):
                            rec["global_level"] = global_level + 1
                            put_student_record(db, rec); save_progress_db(db)
                            st.rerun()
                    else:
                        st.balloons()
                        st.success(tt("Du er på VG3/lærling-nivå. Sterkt jobba!", "You are at VG3/apprentice level. Great work!"))
            else:
                st.warning(tt("Du fikk ikke nok riktige for å bestå temaet. Start temaet på nytt.",
                              "Not enough correct to pass the topic. Restart the topic."))

        if st.button(tt("🔁 Start tema på nytt (dette nivået)", "🔁 Restart topic (this level)"),
                     key=f"arena_restart_{topic_key}_{global_level}", use_container_width=True):
            rec["topics"].setdefault(topic_key, {"levels": {}})
            rec["topics"][topic_key]["levels"][str(global_level)] = {
                "q_index": 0, "correct": 0, "answered": 0,
                "total_correct": int(t.get("total_correct",0)),
                "total_answered": int(t.get("total_answered",0)),
                "passed": False,
            }
            comp = rec.get("completed_topics", {}).get(str(global_level), [])
            if topic_key in comp:
                comp.remove(topic_key)
                rec["completed_topics"][str(global_level)] = comp
            put_student_record(db, rec); save_progress_db(db)
            st.rerun()

    for i, (topic_key, tab) in enumerate(zip(topic_keys, tabs)):
        with tab:
            render_topic(topic_key, topic_titles[i])


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
                "Rektangel = lengde × bredde",
                "Trekant = (grunnlinje × høyde) / 2",
                "Sirkel = π × r²",
                "Trapes = ((a + b) / 2) × h",
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
                "Rektangel = 2 × (lengde + bredde)",
                "Trekant = a + b + c",
                "Sirkel = 2 × π × r  (eller π × d)",
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
                "Boks = lengde × bredde × høyde",
                "Plate = lengde × bredde × tykkelse",
                "Sylinder = π × r² × h",
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
                "Når du har A og B. Finn hypotenusen (C): C = √a2 + b2",
                "Når du har vinkel og hypotenus. Finn hosliggende side (A): A = C x cos(θ)",
                "Når du har vinkel og hypotenus. Finn motstående side (B): **B = C x cos(θ)",
                "Når du har hosliggende og motstående. Finn vinkel (θ): θ = arctan B:A",
            ],
            [
                tt("Her bruker vi Hypotenus (C) = den lengste siden. Hosliggende (A) = siden som ligger inntil vinkelen. Motstående (B) = siden som står rett overfor vinkelen", "Here A=adjacent, B=opposite."),
            ],
        )
        render_asset_image("vinkler.png")
        verification_calculator("diagonal", key_prefix="arena_diagonal")
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

def guess_formula_ui():
    st.markdown("### " + tt("Gjett formel", "Guess the formula"))
    st.caption(tt(
        "Spill som Alias: Elevene skal gjette hvilken formel som brukes basert på situasjonen. 15 kort, 20 sek per kort.",
        "Alias-style game: Guess which formula fits the situation. 15 cards, 20 seconds each."
    ))

    cards = [
        {"q": "Du skal bestille gulvbelegg til et rom. Hvilken formel bruker du?", "a": "Areal (rektangel) = L × B"},
        {"q": "Du skal beregne hvor mye list du trenger rundt et rom. Hvilken formel bruker du?", "a": "Omkrets (rektangel) = 2(L + B)"},
        {"q": "Du skal finne m² gips til en vegg. Hvilken formel bruker du?", "a": "Areal = høyde × lengde"},
        {"q": "Tegning 1:50 → finn virkelighet. Hvilken regel/formel?", "a": "Virkelighet = tegning × 50"},
        {"q": "Kontrollere om en ramme er i vinkel. Hvilken formel/regle?", "a": "Pytagoras: c = √(a² + b²)"},
        {"q": "Finn fall i % mot sluk. Hvilken formel?", "a": "Fall% = (fall/lengde) × 100"},
        {"q": "Finn volum av betongplate. Hvilken formel?", "a": "Volum = L × B × H"},
        {"q": "Du har cm, men trenger mm. Hvilken regel?", "a": "cm → mm: × 10"},
        {"q": "Finn vinkel når du kjenner A og B. Hvilken formel?", "a": "θ = arctan(B/A)"},
        {"q": "Legg til 10% svinn. Hvilken formel?", "a": "Ny = gammel × (1 + p/100)"},
        {"q": "Finn omkrets av sirkel når du har diameter. Hvilken formel?", "a": "O = π × d"},
        {"q": "Finn areal av sirkel når du har radius. Hvilken formel?", "a": "A = π × r²"},
        {"q": "Finn løpemeter av lister på 2 vegger. Hvilken formel?", "a": "Omkrets / sum lengder"},
        {"q": "Før du regner: hva må du sjekke med enheter?", "a": "Alle mål i samme enhet"},
        {"q": "Finn areal av trekant. Hvilken formel?", "a": "A = (g × h) / 2"},
    ]

    opponent = [
        {"q": "Hva er måleenheten for areal?", "a": "m²"},
        {"q": "Hva er måleenheten for volum?", "a": "m³"},
        {"q": "Hva betyr 1000 mm i meter?", "a": "1 m"},
        {"q": "Hva betyr målestokk 1:100?", "a": "1 på tegning = 100 i virkelighet"},
        {"q": "Hva heter siden mot 90° i en rettvinklet trekant?", "a": "Hypotenusen (C)"},
        {"q": "Nevn én trig-funksjon.", "a": "sin / cos / tan"},
        {"q": "Når bruker vi Pytagoras i bygg?", "a": "Sjekke vinkel / diagonal"},
        {"q": "Hva betyr svinn?", "a": "Ekstra for kapp/feil"},
        {"q": "Hva er radius?", "a": "Fra sentrum til kant"},
        {"q": "Hva er diameter?", "a": "Tvers gjennom sentrum"},
        {"q": "Hva er omkrets?", "a": "Lengden rundt en figur"},
        {"q": "Hva er fall?", "a": "Høydeforskjell per lengde"},
        {"q": "Hva betyr prosent?", "a": "Del av 100"},
        {"q": "Hva gjør du alltid før du regner?", "a": "Sjekker enheter + formel"},
        {"q": "Hva er areal av rektangel?", "a": "L × B"},
    ]

    if "gf_stage" not in st.session_state:
        st.session_state.gf_stage = "setup"
    if "gf_index" not in st.session_state:
        st.session_state.gf_index = 0
    if "gf_score" not in st.session_state:
        st.session_state.gf_score = {"p1": 0, "p2": 0}
    if "gf_deadline" not in st.session_state:
        st.session_state.gf_deadline = None

    def reset_game():
        st.session_state.gf_stage = "setup"
        st.session_state.gf_index = 0
        st.session_state.gf_score = {"p1": 0, "p2": 0}
        st.session_state.gf_deadline = None

    with st.container(border=True):
        c1, c2, c3 = st.columns([1.3, 1.3, 1.4])
        with c1:
            if st.button("▶️ " + tt("Start", "Start"), use_container_width=True, key="gf_start"):
                st.session_state.gf_stage = "p1"
                st.session_state.gf_index = 0
                st.session_state.gf_deadline = time.time() + 20
                st.rerun()
        with c2:
            if st.button("🔁 " + tt("Nullstill", "Reset"), use_container_width=True, key="gf_reset"):
                reset_game()
                st.rerun()
        with c3:
            st.markdown(f"**{tt('Poeng', 'Score')}:** {st.session_state.gf_score['p1']} - {st.session_state.gf_score['p2']}")

    stage = st.session_state.gf_stage
    if stage == "setup":
        st.info(tt("Trykk Start. Spiller 1 får 15 kort først, deretter spiller 2.",
                   "Press Start. Player 1 gets 15 cards first, then Player 2."))
        return

    deck = cards if stage == "p1" else opponent
    player_label = tt("Spiller 1", "Player 1") if stage == "p1" else tt("Spiller 2", "Player 2")
    idx = int(st.session_state.gf_index)

    if idx >= 15:
        if stage == "p1":
            st.success(tt("Spiller 1 ferdig! Nå er det Spiller 2.", "Player 1 done! Now Player 2."))
            if st.button("➡️ " + tt("Start spiller 2", "Start player 2"), use_container_width=True, key="gf_to_p2"):
                st.session_state.gf_stage = "p2"
                st.session_state.gf_index = 0
                st.session_state.gf_deadline = time.time() + 20
                st.rerun()
            return
        st.session_state.gf_stage = "done"
        st.rerun()

    remaining = 0
    if st.session_state.gf_deadline is not None:
        remaining = int(max(0, st.session_state.gf_deadline - time.time()))

    if hasattr(st, "autorefresh"):
        st.autorefresh(interval=1000, key=f"gf_refresh_{stage}_{idx}")

    st.markdown(f"#### {player_label} – {tt('Kort', 'Card')} {idx+1}/15")
    st.progress(remaining / 20 if remaining > 0 else 0.0)
    st.write(tt("Tid igjen:", "Time left:"), f"**{remaining}s**")

    st.markdown(f"**{deck[idx]['q']}**")

    cA, cB, cC = st.columns([1.0, 1.0, 2.0])
    with cA:
        if st.button("✅ " + tt("Riktig", "Correct"), use_container_width=True, key=f"gf_correct_{stage}_{idx}"):
            if stage == "p1":
                st.session_state.gf_score["p1"] += 1
            else:
                st.session_state.gf_score["p2"] += 1
            st.session_state.gf_index += 1
            st.session_state.gf_deadline = time.time() + 20
            st.rerun()

    with cB:
        if st.button("⏭️ " + tt("Pass", "Pass"), use_container_width=True, key=f"gf_pass_{stage}_{idx}"):
            st.session_state.gf_index += 1
            st.session_state.gf_deadline = time.time() + 20
            st.rerun()

    with cC:
        with st.expander(tt("Vis fasit (for lærer)", "Show answer (for teacher)")):
            st.write("**" + tt("Fasit:", "Answer:") + "**", deck[idx]["a"])

    if remaining <= 0:
        st.warning(tt("Tiden er ute – registrert som pass.", "Time is up — counted as pass."))
        if st.button("➡️ " + tt("Neste kort", "Next card"), use_container_width=True, key=f"gf_next_{stage}_{idx}"):
            st.session_state.gf_index += 1
            st.session_state.gf_deadline = time.time() + 20
            st.rerun()

    if st.session_state.gf_stage == "done":
        st.markdown("### " + tt("Resultat", "Result"))
        st.success(f"{tt('Spiller 1', 'Player 1')}: {st.session_state.gf_score['p1']}  ·  {tt('Spiller 2', 'Player 2')}: {st.session_state.gf_score['p2']}")


def show_learning_arena():
    # Reset widget instance counter (prevents duplicate keys across tabs)
    st.session_state['_vc_uid'] = 0
    st.markdown("## " + tt("Læringsarena", "Learning arena"))
    tab1, tab2, tab3 = st.tabs([
        tt("Formelbank", "Formula bank"),
        tt("Øvingsoppgaver", "Practice tasks"),
        tt("Gjett formel", "Guess the formula"),
    ])
    with tab1:
        formula_bank_ui()
    with tab2:
        arena_tasks_ui()
    with tab3:
        guess_formula_ui()


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
# VEIEN TIL YRKESLIVET (BETA) – egen lås + innhold
# ============================================================

def vty_paywall_card():
    st.warning(
        tt(
            f"**Veien til yrkeslivet (BETA)** er en tilleggspakke med realistiske oppgaver fra byggeplass.\n\n"
            f"🔒 For å gå videre må du ha tilgang.\n\n"
            f"- Pris (pilot): {PRO_PRICE_MONTH} kr/mnd eller {PRO_PRICE_YEAR} kr/år\n"
            f"- Lærerkode gir tilgang i pilotperioden.",
            f"**Path to professional life (BETA)** is an add-on with realistic tasks from the job site.\n\n"
            f"🔒 Access is required to continue.\n\n"
            f"- Price (pilot): {PRO_PRICE_MONTH} NOK/month or {PRO_PRICE_YEAR} NOK/year\n"
            f"- Teacher code grants pilot access."
        )
    )
    st.caption(tt(
        "Betalingsløsningen er simulert i denne demoen. Når du ønsker det kan dette kobles til Stripe/Vipps.",
        "Payment is simulated in this demo. When you're ready, it can be connected to Stripe/Vipps."
    ))

def show_vty_gate():
    st.markdown("## 📜 " + tt("Veien til yrkeslivet (BETA)", "Path to professional life (BETA)"))
    st.caption(tt(
        "Tilgangssiden: betal / lærerkode → deretter får du oppgavebanken.",
        "Access page: pay / teacher code → then you get the task bank."
    ))

    vty_paywall_card()

    c1, c2, c3 = st.columns([1.3, 1.5, 2.2], gap="medium")
    with c1:
        if st.button("💳 " + tt("Jeg har betalt (demo)", "I have paid (demo)"), use_container_width=True, key="vty_paid_btn"):
            st.session_state.vty_access = True
            st.session_state.vty_teacher_mode = False
            st.success(tt("Tilgang aktivert (demo).", "Access enabled (demo)."))

    with c2:
        code_in = st.text_input(tt("Lærerkode (pilot)", "Teacher code (pilot)"), type="password", key="vty_teacher_code")
        if code_in and code_in == TEACHER_CODE:
            st.session_state.vty_access = True
            st.session_state.vty_teacher_mode = True
            st.success(tt("Lærertilgang aktiv.", "Teacher access enabled."))

    with c3:
        st.caption(tt(
            "Tips: I klasserommet kan læreren bruke koden for å åpne innholdet på storskjerm.",
            "Tip: In class, the teacher can use the code to open the content on a shared screen."
        ))

    st.divider()

    if st.button("➡️ " + tt("Gå til oppgaver", "Go to tasks"), use_container_width=True, disabled=not st.session_state.vty_access):
        st.session_state.view = "VeienTilYrkeslivet_Innhold"
        st.rerun()

def _task_check_ui(task, key_prefix: str):
    """
    Standard UI for en realistisk oppgave med svar-sjekk.
    task: dict med fields:
      title, scenario, question, formula_hint, answer, unit, tol, rounding (optional), integer(optional), lk20
    """
    with st.container(border=True):
        st.markdown(f"#### {task['title']}")
        st.write(task["scenario"])
        st.markdown("**" + tt("Oppgave", "Task") + "**")
        st.write(task["question"])
        st.markdown("**" + tt("Formel-hint", "Formula hint") + "**")
        st.code(task["formula_hint"], language="text")

        st.markdown("**" + tt("LK20-kobling (eksempel)", "LK20 linkage (example)") + "**")
        st.write(task["lk20"])

        st.divider()
        ans = st.text_input(tt("Ditt svar", "Your answer"), key=f"{key_prefix}_ans", placeholder=task.get("unit",""))
        c1, c2 = st.columns([1.1, 2.9])
        with c1:
            if st.button(tt("Sjekk svar", "Check answer"), use_container_width=True, key=f"{key_prefix}_chk"):
                ok, v = check_answer(ans, {"answer": task["answer"], "tol": task.get("tol", 0.0), "integer": task.get("integer", False)})
                if ok:
                    st.success(tt("Riktig ✔️", "Correct ✔️"))
                else:
                    # vis "nær" hint
                    st.error(tt("Ikke helt. Sjekk enheter og formelvalg.", "Not quite. Check units and formula choice."))
        with c2:
            if st.session_state.get("vty_teacher_mode", False):
                if st.toggle(tt("Vis fasit (lærer)", "Show answer (teacher)"), key=f"{key_prefix}_show"):
                    # avrunding
                    val = float(task["answer"])
                    if task.get("integer"):
                        out = str(int(round(val)))
                    else:
                        r = task.get("rounding", None)
                        out = f"{val:.{r}f}" if isinstance(r, int) else fmt(val)
                    st.info(f"{tt('Fasit', 'Answer')}: {out} {task.get('unit','')}".strip())

def vty_tasks_data():
    """
    Returnerer oppgaver per yrke. 10 oppgaver per yrke.
    Tallene er bevisst realistiske og enhetsnære.
    """
    LK20 = tt(
        "Knyttes typisk til programfag i BA (f.eks. Praktisk yrkesutøvelse): måle og beregne, planlegge og gjennomføre arbeidsoppdrag, velge materialer, dokumentere og gjøre egenkontroll.",
        "Typically linked to VET outcomes (e.g., Practical trade practice): measure and calculate, plan and carry out tasks, choose materials, document work, and perform self-checks."
    )

    return {
        tt("Tømrer", "Carpenter"): [
            {
                "title": tt("1) Stendere i vegg", "1) Wall studs"),
                "scenario": tt("Du skal bygge en bindingsverksvegg på byggeplass.", "You are framing a stud wall on site."),
                "question": tt("Vegg: 4,8 m lang. Senteravstand 0,6 m. Hvor mange stendere trenger du hvis du alltid har en stender i hver ende?", 
                               "Wall: 4.8 m long. Stud spacing 0.6 m. How many studs do you need if you always have one at each end?"),
                "formula_hint": "antall = (lengde / c/c) + 1  (avrund opp)",
                "answer": math.floor(4.8/0.6) + 1,
                "unit": "stk",
                "tol": 0.0,
                "integer": True,
                "lk20": LK20
            },
            {
                "title": tt("2) Gips på vegg med åpning", "2) Drywall with opening"),
                "scenario": tt("Du skal bestille gipsplater til en vegg.", "You need drywall sheets for a wall."),
                "question": tt("Vegg: 6,0 m × 2,4 m. Trekk fra én dør: 0,9 × 2,1 m. Hvor mange m² gips trenger du?",
                               "Wall: 6.0 m × 2.4 m. Subtract one door: 0.9 × 2.1 m. How many m² of drywall do you need?"),
                "formula_hint": "A_netto = (L×H) − (dør_b×dør_h)",
                "answer": (6.0*2.4) - (0.9*2.1),
                "unit": "m²",
                "tol": 0.05,
                "rounding": 2,
                "lk20": LK20
            },
            {
                "title": tt("3) Diagonal for å sjekke vinkel", "3) Diagonal to check square"),
                "scenario": tt("Du setter opp en rektangulær ramme og må kontrollere om den er i vinkel.", 
                               "You build a rectangular frame and must verify it's square."),
                "question": tt("Ramme: 3,0 m × 4,0 m. Hva skal diagonalen være (m) for at rammen er i vinkel?",
                               "Frame: 3.0 m × 4.0 m. What should the diagonal be (m) if the frame is square?"),
                "formula_hint": "c = √(a² + b²)",
                "answer": math.sqrt(3.0**2 + 4.0**2),
                "unit": "m",
                "tol": 0.02,
                "rounding": 2,
                "lk20": LK20
            },
            {
                "title": tt("4) Takvinkel", "4) Roof angle"),
                "scenario": tt("Du skal lage takstoler og må finne takvinkel.", "You are building roof trusses and need the roof angle."),
                "question": tt("Horisontal (A)=4,8 m og høyde (B)=1,6 m. Finn takvinkel θ i grader.",
                               "Run (A)=4.8 m and rise (B)=1.6 m. Find roof angle θ in degrees."),
                "formula_hint": "θ = arctan(B/A)",
                "answer": math.degrees(math.atan(1.6/4.8)),
                "unit": "°",
                "tol": 0.6,
                "rounding": 1,
                "lk20": LK20
            },
            {
                "title": tt("5) Gulvareal og svinn", "5) Floor area and waste"),
                "scenario": tt("Du skal bestille gulv (parkett/laminat).", "You are ordering flooring (parquet/laminate)."),
                "question": tt("Rom: 5,4 m × 3,6 m. Legg til 8% svinn. Hvor mange m² bestiller du?",
                               "Room: 5.4 m × 3.6 m. Add 8% waste. How many m² do you order?"),
                "formula_hint": "A = L×B;  A_bestill = A × (1 + svinn/100)",
                "answer": (5.4*3.6) * 1.08,
                "unit": "m²",
                "tol": 0.1,
                "rounding": 2,
                "lk20": LK20
            },
            {
                "title": tt("6) Listverk (løpemeter)", "6) Trim (running meters)"),
                "scenario": tt("Du skal bestille gulvlister.", "You need baseboards."),
                "question": tt("Rom: 4,2 m × 3,0 m. Du skal IKKE ha list foran døråpning 0,9 m. Hvor mange meter list trenger du?",
                               "Room: 4.2 m × 3.0 m. Do NOT place trim across a 0.9 m doorway. How many meters of trim do you need?"),
                "formula_hint": "O = 2(L+B) − dørbredde",
                "answer": (2*(4.2+3.0)) - 0.9,
                "unit": "m",
                "tol": 0.05,
                "rounding": 2,
                "lk20": LK20
            },
            {
                "title": tt("7) Materiallengde – kapp/svinn", "7) Length + cutting waste"),
                "scenario": tt("Du skal kle en vegg med horisontale lekter.", "You are installing horizontal battens."),
                "question": tt("Du trenger 18 stk lekter à 2,4 m. Legg til 10% svinn. Hvor mange løpemeter bestiller du?",
                               "You need 18 battens of 2.4 m. Add 10% waste. How many running meters do you order?"),
                "formula_hint": "LM = antall×lengde;  LM_bestill = LM×(1+svinn/100)",
                "answer": (18*2.4)*1.10,
                "unit": "m",
                "tol": 0.2,
                "rounding": 1,
                "lk20": LK20
            },
            {
                "title": tt("8) Trapp – stigning", "8) Stairs – rise per step"),
                "scenario": tt("Du skal beregne jevn stigning i en trapp.", "You need even risers in a stair."),
                "question": tt("Etasjehøyde: 2,70 m. Du planlegger 15 opptrinn. Hvor høy blir hvert opptrinn (cm)?",
                               "Floor-to-floor height: 2.70 m. You plan 15 risers. What is the rise per step (cm)?"),
                "formula_hint": "opptrinn = total høyde / antall;  (m→cm: ×100)",
                "answer": (2.70/15)*100,
                "unit": "cm",
                "tol": 0.2,
                "rounding": 1,
                "lk20": LK20
            },
            {
                "title": tt("9) Bjelkelag – c/c og antall bjelker", "9) Joists – spacing and count"),
                "scenario": tt("Du legger bjelkelag i et gulv.", "You are laying floor joists."),
                "question": tt("Spennvidde: 3,6 m. Bjelker c/c 0,6 m. Hvor mange bjelker trengs dersom du har bjelke i hver kant?",
                               "Span: 3.6 m. Joist spacing 0.6 m. How many joists if you have one at each edge?"),
                "formula_hint": "antall = (lengde / c/c) + 1",
                "answer": math.floor(3.6/0.6)+1,
                "unit": "stk",
                "tol": 0.0,
                "integer": True,
                "lk20": LK20
            },
            {
                "title": tt("10) Areal av trekantet gavl", "10) Area of triangular gable"),
                "scenario": tt("Du skal beregne kledning på en trekantet gavl.", "You need cladding area for a triangular gable."),
                "question": tt("Gavl: grunnlinje 6,0 m og høyde 2,4 m. Finn arealet (m²).",
                               "Gable: base 6.0 m and height 2.4 m. Find area (m²)."),
                "formula_hint": "A_trekant = (grunnlinje × høyde) / 2",
                "answer": (6.0*2.4)/2,
                "unit": "m²",
                "tol": 0.05,
                "rounding": 2,
                "lk20": LK20
            },
        ],

        tt("Rørlegger", "Plumber"): [
            {
                "title": tt("1) Fall på avløpsrør", "1) Drain pipe slope"),
                "scenario": tt("Avløpsrør skal ha fall for å sikre god avrenning.", "Drain pipes need slope for proper flow."),
                "question": tt("Krav: 20 mm fall per meter. Rørlengde: 3,5 m. Hvor mange mm fall totalt?",
                               "Requirement: 20 mm drop per meter. Pipe length: 3.5 m. How many mm total drop?"),
                "formula_hint": "fall_tot = (mm per m) × lengde",
                "answer": 20*3.5,
                "unit": "mm",
                "tol": 1.0,
                "rounding": 0,
                "lk20": LK20
            },
            {
                "title": tt("2) Vanntrykk – enkel prosentvis reduksjon", "2) Pressure – percent reduction"),
                "scenario": tt("Du må ta høyde for trykktap i en installasjon (forenklet).", "You account for pressure loss (simplified)."),
                "question": tt("Starttrykk: 4,0 bar. Trykktap 12%. Hva blir trykket etter tapet?",
                               "Start: 4.0 bar. Loss 12%. What is the resulting pressure?"),
                "formula_hint": "ny = gammel × (1 − p/100)",
                "answer": 4.0*(1-0.12),
                "unit": "bar",
                "tol": 0.05,
                "rounding": 2,
                "lk20": LK20
            },
            {
                "title": tt("3) Rørmengde – kapp", "3) Pipe length + cutting"),
                "scenario": tt("Du skal bestille rør til en føringsvei.", "You order pipe for a run."),
                "question": tt("Du trenger 9 lengder à 3,0 m. Legg til 8% kapp. Hvor mange meter bestiller du?",
                               "You need 9 lengths of 3.0 m. Add 8% cutting waste. How many meters to order?"),
                "formula_hint": "LM = antall×lengde;  LM_bestill = LM×(1+svinn/100)",
                "answer": (9*3.0)*1.08,
                "unit": "m",
                "tol": 0.2,
                "rounding": 1,
                "lk20": LK20
            },
            {
                "title": tt("4) Sylinder – volum i rør", "4) Cylinder – water volume in pipe"),
                "scenario": tt("Du vil vite omtrent hvor mye vann som står i et rør (forenklet).", "Estimate water volume in a pipe."),
                "question": tt("Rør: innvendig diameter 25 mm, lengde 12 m. Finn volum (liter). (1 m³ = 1000 liter)",
                               "Pipe: inner diameter 25 mm, length 12 m. Find volume (liters)."),
                "formula_hint": "V = π·r²·L  (r = d/2). Husk mm→m. liter = m³×1000",
                "answer": (math.pi*((0.025/2)**2)*12)*1000,
                "unit": "liter",
                "tol": 0.2,
                "rounding": 2,
                "lk20": LK20
            },
            {
                "title": tt("5) Blandingsforhold – prosent", "5) Mixing ratio – percent"),
                "scenario": tt("Du blander frostvæske i et anlegg (forenklet).", "You mix antifreeze (simplified)."),
                "question": tt("Du har 40 liter væske. 30% skal være frostvæske. Hvor mange liter frostvæske?",
                               "You have 40 liters total. 30% should be antifreeze. How many liters antifreeze?"),
                "formula_hint": "del = (p/100) × hel",
                "answer": 0.30*40,
                "unit": "liter",
                "tol": 0.2,
                "rounding": 1,
                "lk20": LK20
            },
            {
                "title": tt("6) Areal for gulvvarme", "6) Area for floor heating"),
                "scenario": tt("Du planlegger gulvvarmesløyfer i et rom.", "You plan underfloor heating loops."),
                "question": tt("Rom: 4,8 m × 3,6 m. Trekk fra fast innredning 1,2 m². Finn areal som skal varmes (m²).",
                               "Room: 4.8 m × 3.6 m. Subtract fixed fixtures 1.2 m². Find heated area."),
                "formula_hint": "A = L×B − A_fast",
                "answer": (4.8*3.6) - 1.2,
                "unit": "m²",
                "tol": 0.05,
                "rounding": 2,
                "lk20": LK20
            },
            {
                "title": tt("7) Rørisolasjon – omkrets", "7) Pipe insulation – circumference"),
                "scenario": tt("Du skal beregne omkretsen for å anslå isolasjonsbehov.", "You estimate insulation needs from circumference."),
                "question": tt("Ytre diameter på rør: 42 mm. Finn omkrets (mm).",
                               "Outer diameter: 42 mm. Find circumference (mm)."),
                "formula_hint": "O = π × d",
                "answer": math.pi*42,
                "unit": "mm",
                "tol": 2.0,
                "rounding": 0,
                "lk20": LK20
            },
            {
                "title": tt("8) Tappevann – volum i tank", "8) Hot water tank volume"),
                "scenario": tt("Du sjekker kapasitet på varmtvannstank (forenklet boks).", "Estimate hot water tank capacity (box approximation)."),
                "question": tt("Tank (forenklet): 0,5 m × 0,5 m × 1,2 m. Finn volum (liter).",
                               "Tank: 0.5 m × 0.5 m × 1.2 m. Find volume (liters)."),
                "formula_hint": "V = L×B×H; liter = m³×1000",
                "answer": (0.5*0.5*1.2)*1000,
                "unit": "liter",
                "tol": 2.0,
                "rounding": 0,
                "lk20": LK20
            },
            {
                "title": tt("9) Avstand mellom rørklammer", "9) Clamp spacing"),
                "scenario": tt("Du skal sette rørklammer jevnt.", "You place pipe clamps evenly."),
                "question": tt("Rørstrekk: 4,2 m. Klammer hver 0,6 m + én i hver ende. Hvor mange klammer?",
                               "Run: 4.2 m. Clamps every 0.6 m + one at each end. How many clamps?"),
                "formula_hint": "antall = (lengde / avstand) + 1",
                "answer": math.floor(4.2/0.6)+1,
                "unit": "stk",
                "tol": 0.0,
                "integer": True,
                "lk20": LK20
            },
            {
                "title": tt("10) Temperaturfall – differanse", "10) Temperature drop"),
                "scenario": tt("Du dokumenterer enkelt temperaturfall i et system (forenklet).", "Document a simple temperature drop."),
                "question": tt("Turtemperatur: 42°C. Retur: 34°C. Hva er temperaturfallet (°C)?",
                               "Supply: 42°C. Return: 34°C. What is the temperature drop?"),
                "formula_hint": "ΔT = T_tur − T_retur",
                "answer": 42-34,
                "unit": "°C",
                "tol": 0.0,
                "integer": True,
                "lk20": LK20
            },
        ],

        tt("Blikkenslager", "Sheet metal worker"): [
            {
                "title": tt("1) Renne – total lengde", "1) Gutter length"),
                "scenario": tt("Du skal bestille takrenner.", "You are ordering gutters."),
                "question": tt("Bygg: 10,8 m × 7,2 m. Renner på to langsider (10,8 m). Legg til 5% kapp. Hvor mange meter bestilles?",
                               "Building: 10.8 m × 7.2 m. Gutters on two long sides (10.8 m). Add 5% waste. How many meters?"),
                "formula_hint": "LM = 2×lengde;  LM_bestill = LM×(1+svinn/100)",
                "answer": (2*10.8)*1.05,
                "unit": "m",
                "tol": 0.2,
                "rounding": 1,
                "lk20": LK20
            },
            {
                "title": tt("2) Nedløp – antall rørstykker", "2) Downpipe count"),
                "scenario": tt("Nedløp leveres i 3,0 m lengder.", "Downpipes come in 3.0 m lengths."),
                "question": tt("Bygget har 2 etasjer, total høyde 5,4 m. Ett nedløp per hjørne (4 stk). Hvor mange 3,0 m rørstykker trengs totalt? (avrund opp per nedløp)",
                               "Total height 5.4 m. One downpipe per corner (4). How many 3.0 m pieces total?"),
                "formula_hint": "stykker per nedløp = ceil(høyde/3,0); total = per×4",
                "answer": math.ceil(5.4/3.0)*4,
                "unit": "stk",
                "tol": 0.0,
                "integer": True,
                "lk20": LK20
            },
            {
                "title": tt("3) Luftkanal – tverrsnittsareal", "3) Vent duct cross-section area"),
                "scenario": tt("Du dimensjonerer en rektangulær kanal (forenklet).", "You size a rectangular duct (simplified)."),
                "question": tt("Kanal: 200 mm × 150 mm. Finn tverrsnittsareal i cm².",
                               "Duct: 200 mm × 150 mm. Find cross-sectional area in cm²."),
                "formula_hint": "A = L×B; mm→cm: ÷10",
                "answer": (20*15),  # cm x cm
                "unit": "cm²",
                "tol": 1.0,
                "integer": True,
                "lk20": LK20
            },
            {
                "title": tt("4) Platekledning – areal med svinn", "4) Sheet area with waste"),
                "scenario": tt("Du skal bestille plate/metall til en kasseinnkledning.", "You order sheet metal for a casing."),
                "question": tt("Areal: 12,0 m². Legg til 12% svinn. Hvor mange m² bestiller du?",
                               "Area: 12.0 m². Add 12% waste. How many m² to order?"),
                "formula_hint": "A_bestill = A × (1 + svinn/100)",
                "answer": 12.0*1.12,
                "unit": "m²",
                "tol": 0.1,
                "rounding": 2,
                "lk20": LK20
            },
            {
                "title": tt("5) Pipegjennomføring – omkrets", "5) Pipe penetration – circumference"),
                "scenario": tt("Du lager en mansjett rundt et rundt rør.", "You make a collar around a round pipe."),
                "question": tt("Diameter på rør: 110 mm. Hvor lang stripe trengs rundt (mm) uten overlapp?",
                               "Pipe diameter: 110 mm. What strip length is needed around it (mm), no overlap?"),
                "formula_hint": "O = π × d",
                "answer": math.pi*110,
                "unit": "mm",
                "tol": 3.0,
                "rounding": 0,
                "lk20": LK20
            },
            {
                "title": tt("6) Koning – enkel prosentvis avkorting", "6) Tapering – percent reduction"),
                "scenario": tt("Du lager en kon (forenklet) og må redusere omkrets 8%.", "You taper a piece and reduce circumference by 8%."),
                "question": tt("Opprinnelig omkrets: 520 mm. Reduser 8%. Hva blir ny omkrets?",
                               "Original circumference: 520 mm. Reduce by 8%. New circumference?"),
                "formula_hint": "ny = gammel × (1 − p/100)",
                "answer": 520*(1-0.08),
                "unit": "mm",
                "tol": 2.0,
                "rounding": 0,
                "lk20": LK20
            },
            {
                "title": tt("7) Beslag – lengde + overlapp", "7) Flashing – length + overlap"),
                "scenario": tt("Du legger beslag med overlapp.", "You install flashing with overlap."),
                "question": tt("Du har 14,4 m lengde. Overlapp 100 mm per skjøt. Du bruker 6 lengder (skjøter=5). Hvor mange meter beslag går med totalt?",
                               "Run is 14.4 m. Overlap 100 mm per joint. You use 6 lengths (5 joints). Total length used?"),
                "formula_hint": "total = lengde + (antall_skjøter × overlapp). 100 mm = 0,1 m",
                "answer": 14.4 + (5*0.1),
                "unit": "m",
                "tol": 0.05,
                "rounding": 2,
                "lk20": LK20
            },
            {
                "title": tt("8) Takrennefall", "8) Gutter slope"),
                "scenario": tt("Takrenne skal ha lite fall mot nedløp.", "Gutters need a slight fall to the downpipe."),
                "question": tt("Krav: 3 mm fall per meter. Lengde: 8,0 m. Hvor mange mm fall totalt?",
                               "Requirement: 3 mm per meter. Length: 8.0 m. Total drop (mm)?"),
                "formula_hint": "fall_tot = mm per m × lengde",
                "answer": 3*8.0,
                "unit": "mm",
                "tol": 1.0,
                "integer": True,
                "lk20": LK20
            },
            {
                "title": tt("9) Kanal – overflateareal (for isolasjon)", "9) Duct surface area (insulation)"),
                "scenario": tt("Du skal anslå isolasjonsbehov rundt en rektangulær kanal.", "You estimate insulation for a rectangular duct."),
                "question": tt("Kanal: 0,30 m × 0,20 m, lengde 6,0 m. Finn overflateareal av sideflatene (m²) (ikke endeflater).",
                               "Duct: 0.30 m × 0.20 m, length 6.0 m. Find side surface area (m²), ignore ends."),
                "formula_hint": "A_side = omkrets_tverrsnitt × lengde = 2(a+b)×L",
                "answer": (2*(0.30+0.20))*6.0,
                "unit": "m²",
                "tol": 0.05,
                "rounding": 2,
                "lk20": LK20
            },
            {
                "title": tt("10) Platekutting – utnyttelse", "10) Sheet cutting utilization"),
                "scenario": tt("Du vil se hvor stor andel av platen som faktisk brukes.", "You check how much of a sheet is used."),
                "question": tt("Plate: 1,0 m². Du bruker 0,78 m². Hvor stor utnyttelse i %?",
                               "Sheet: 1.0 m². You use 0.78 m². Utilization in %?"),
                "formula_hint": "prosent = (del / hel) × 100",
                "answer": (0.78/1.0)*100,
                "unit": "%",
                "tol": 0.5,
                "rounding": 1,
                "lk20": LK20
            },
        ],

        tt("Mur og betong", "Masonry & concrete"): [
            {
                "title": tt("1) Betongplate – volum", "1) Slab concrete volume"),
                "scenario": tt("Du skal bestille betong til en plate.", "You order concrete for a slab."),
                "question": tt("Plate: 7,2 m × 3,6 m × 100 mm. Finn volum (m³).",
                               "Slab: 7.2 m × 3.6 m × 100 mm. Find volume (m³)."),
                "formula_hint": "V = L×B×t;  100 mm = 0,10 m",
                "answer": 7.2*3.6*0.10,
                "unit": "m³",
                "tol": 0.02,
                "rounding": 2,
                "lk20": LK20
            },
            {
                "title": tt("2) Betong med svinn", "2) Concrete with waste"),
                "scenario": tt("Du legger til svinn for søl og ujevnheter.", "Add waste for spillage and irregularities."),
                "question": tt("Du har beregnet 2,59 m³ betong. Legg til 8% svinn. Hvor mye bestiller du (m³)?",
                               "You calculated 2.59 m³. Add 8% waste. How much do you order?"),
                "formula_hint": "V_bestill = V × (1 + svinn/100)",
                "answer": 2.59*1.08,
                "unit": "m³",
                "tol": 0.03,
                "rounding": 2,
                "lk20": LK20
            },
            {
                "title": tt("3) Armering – antall jern", "3) Rebar count"),
                "scenario": tt("Du legger armeringsjern med c/c-avstand.", "You place rebar at a given spacing."),
                "question": tt("Platebredde: 3,6 m. Jern c/c 0,20 m. Hvor mange jern trengs hvis du har jern i hver kant?",
                               "Width: 3.6 m. Spacing 0.20 m. How many bars if one at each edge?"),
                "formula_hint": "antall = (bredde / c/c) + 1",
                "answer": math.floor(3.6/0.20)+1,
                "unit": "stk",
                "tol": 0.0,
                "integer": True,
                "lk20": LK20
            },
            {
                "title": tt("4) Murstein – areal og antall", "4) Bricks – area and count"),
                "scenario": tt("Du beregner antall murstein basert på areal og forbruk.", "Estimate bricks from wall area and rate."),
                "question": tt("Vegg: 4,8 m × 2,4 m. Forbruk: 60 stein per m². Hvor mange stein (avrund opp)?",
                               "Wall: 4.8 m × 2.4 m. Rate: 60 bricks per m². How many (round up)?"),
                "formula_hint": "antall = areal × forbruk; avrund opp",
                "answer": math.ceil((4.8*2.4)*60),
                "unit": "stk",
                "tol": 0.0,
                "integer": True,
                "lk20": LK20
            },
            {
                "title": tt("5) Puss – blanding (prosent)", "5) Plaster mix (percent)"),
                "scenario": tt("Du blander mørtel (forenklet prosentandel).", "Mix mortar (simplified percent)."),
                "question": tt("Du trenger 25 kg blanding. 12% skal være sement. Hvor mange kg sement?",
                               "Need 25 kg total. 12% is cement. How many kg cement?"),
                "formula_hint": "del = (p/100) × hel",
                "answer": 0.12*25,
                "unit": "kg",
                "tol": 0.1,
                "rounding": 2,
                "lk20": LK20
            },
            {
                "title": tt("6) Fundament – volum", "6) Footing volume"),
                "scenario": tt("Du støper fundamentstripe.", "You pour a strip footing."),
                "question": tt("Stripe: 12,0 m lang × 0,4 m bred × 0,3 m høy. Finn volum (m³).",
                               "Footing: 12.0 m × 0.4 m × 0.3 m. Volume (m³)?"),
                "formula_hint": "V = L×B×H",
                "answer": 12.0*0.4*0.3,
                "unit": "m³",
                "tol": 0.02,
                "rounding": 2,
                "lk20": LK20
            },
            {
                "title": tt("7) Forskaling – areal", "7) Formwork area"),
                "scenario": tt("Du skal anslå forskalingsareal på sider av en bjelke (forenklet).", "Estimate formwork area on beam sides."),
                "question": tt("Bjelke: lengde 6,0 m, høyde 0,5 m. To sider. Finn areal (m²).",
                               "Beam: length 6.0 m, height 0.5 m. Two sides. Area (m²)?"),
                "formula_hint": "A = 2 × (L × H)",
                "answer": 2*(6.0*0.5),
                "unit": "m²",
                "tol": 0.05,
                "rounding": 2,
                "lk20": LK20
            },
            {
                "title": tt("8) Fall på betonggulv mot sluk", "8) Concrete floor slope to drain"),
                "scenario": tt("Gulvet skal ha fall mot sluk.", "Floor needs slope to drain."),
                "question": tt("Fallkrav: 1,5% over 3,0 m. Hvor mange mm fall?",
                               "Slope: 1.5% over 3.0 m. How many mm drop?"),
                "formula_hint": "fall(mm) = (pct/100) × lengde(m) × 1000",
                "answer": (1.5/100)*3.0*1000,
                "unit": "mm",
                "tol": 2.0,
                "rounding": 0,
                "lk20": LK20
            },
            {
                "title": tt("9) Blandingsvann – liter", "9) Mixing water liters"),
                "scenario": tt("Sekketøy krever vann pr. sekk (forenklet).", "Bagged mix needs water per bag."),
                "question": tt("Du bruker 12 sekker. 2,8 liter vann per sekk. Hvor mange liter vann totalt?",
                               "You use 12 bags. 2.8 L per bag. Total liters?"),
                "formula_hint": "liter = antall × liter_per_sekk",
                "answer": 12*2.8,
                "unit": "liter",
                "tol": 0.2,
                "rounding": 1,
                "lk20": LK20
            },
            {
                "title": tt("10) Armeringsnett – antall nett", "10) Mesh sheets count"),
                "scenario": tt("Armeringsnett leveres i plater.", "Rebar mesh comes in sheets."),
                "question": tt("Plateareal: 25 m². Ett nett dekker 2,15 m × 5,0 m. Hvor mange nett trengs (avrund opp)?",
                               "Slab area: 25 m². One mesh covers 2.15 m × 5.0 m. How many sheets (round up)?"),
                "formula_hint": "antall = total_areal / nett_areal; avrund opp",
                "answer": math.ceil(25 / (2.15*5.0)),
                "unit": "stk",
                "tol": 0.0,
                "integer": True,
                "lk20": LK20
            },
        ],

        tt("Flislegger", "Tiler"): [
            {
                "title": tt("1) Antall fliser på gulv", "1) Number of tiles on floor"),
                "scenario": tt("Du skal bestille fliser til et gulv.", "You are ordering tiles for a floor."),
                "question": tt("Rom: 3,6 m × 2,4 m. Flis: 30 cm × 30 cm. Legg til 10% svinn. Hvor mange fliser bestiller du? (avrund opp)",
                               "Room: 3.6 m × 2.4 m. Tile: 30 cm × 30 cm. Add 10% waste. How many tiles?"),
                "formula_hint": "A_rom = L×B. A_flis = 0,30×0,30. antall = (A_rom/A_flis)×(1+svinn) avrund opp",
                "answer": math.ceil(((3.6*2.4)/(0.30*0.30))*1.10),
                "unit": "stk",
                "tol": 0.0,
                "integer": True,
                "lk20": LK20
            },
            {
                "title": tt("2) Flis på vegg med dør", "2) Wall tiling with door"),
                "scenario": tt("Du skal flislegge en vegg, men trekker fra dør.", "You tile a wall and subtract a door opening."),
                "question": tt("Vegg: 4,8 m × 2,4 m. Dør: 0,9 × 2,1 m. Finn netto flisareal (m²).",
                               "Wall: 4.8 m × 2.4 m. Door: 0.9 × 2.1 m. Net tiling area (m²)?"),
                "formula_hint": "A_netto = (L×H) − (dør_b×dør_h)",
                "answer": (4.8*2.4)-(0.9*2.1),
                "unit": "m²",
                "tol": 0.05,
                "rounding": 2,
                "lk20": LK20
            },
            {
                "title": tt("3) Limforbruk", "3) Adhesive consumption"),
                "scenario": tt("Lim har forbruk per m².", "Adhesive has a consumption per m²."),
                "question": tt("Du skal dekke 18 m². Forbruk 3,5 kg/m². Hvor mange kg lim trengs?",
                               "Cover 18 m². Rate 3.5 kg/m². How many kg adhesive?"),
                "formula_hint": "kg = areal × kg_per_m²",
                "answer": 18*3.5,
                "unit": "kg",
                "tol": 0.5,
                "rounding": 1,
                "lk20": LK20
            },
            {
                "title": tt("4) Fugemasse", "4) Grout"),
                "scenario": tt("Du legger til svinn på fugemasse.", "Add waste for grout."),
                "question": tt("Beregnet behov: 12,0 kg. Legg til 8% svinn. Hvor mange kg bestiller du?",
                               "Calculated: 12.0 kg. Add 8% waste. How many kg to order?"),
                "formula_hint": "bestill = behov × (1 + svinn/100)",
                "answer": 12.0*1.08,
                "unit": "kg",
                "tol": 0.2,
                "rounding": 1,
                "lk20": LK20
            },
            {
                "title": tt("5) Fall mot sluk", "5) Slope to drain"),
                "scenario": tt("Baderomsgulv skal ha fall mot sluk.", "Bathroom floor needs slope to drain."),
                "question": tt("Fall: 2,0% over 1,8 m. Hvor mange mm fall?",
                               "Slope: 2.0% over 1.8 m. How many mm drop?"),
                "formula_hint": "fall(mm) = (pct/100) × lengde(m) × 1000",
                "answer": (2.0/100)*1.8*1000,
                "unit": "mm",
                "tol": 2.0,
                "rounding": 0,
                "lk20": LK20
            },
            {
                "title": tt("6) Sokkel/flislist (løpemeter)", "6) Tile trim (running meters)"),
                "scenario": tt("Du skal legge flislist langs vegg.", "You install tile trim along walls."),
                "question": tt("Rom: 2,4 m × 2,0 m. Du har døråpning 0,8 m uten list. Hvor mange meter list?",
                               "Room: 2.4 m × 2.0 m. Door opening 0.8 m without trim. How many meters?"),
                "formula_hint": "O = 2(L+B) − dørbredde",
                "answer": (2*(2.4+2.0)) - 0.8,
                "unit": "m",
                "tol": 0.05,
                "rounding": 2,
                "lk20": LK20
            },
            {
                "title": tt("7) Fliser per rad", "7) Tiles per row"),
                "scenario": tt("Du planlegger flislegging uten kapp (forenklet).", "Plan tiling without cuts (simplified)."),
                "question": tt("Vegglengde: 3,0 m. Flis: 25 cm bred. Hvor mange fliser går det per rad? (avrund opp)",
                               "Wall length: 3.0 m. Tile width: 25 cm. Tiles per row (round up)?"),
                "formula_hint": "antall = lengde / flisbredde. 25 cm = 0,25 m",
                "answer": math.ceil(3.0/0.25),
                "unit": "stk",
                "tol": 0.0,
                "integer": True,
                "lk20": LK20
            },
            {
                "title": tt("8) Pris – rabatt", "8) Price – discount"),
                "scenario": tt("Du får rabatt hos leverandør.", "You get a supplier discount."),
                "question": tt("Fliser koster 19 800 kr. Rabatt 10%. Hva betaler du?",
                               "Tiles cost 19,800 NOK. 10% discount. What do you pay?"),
                "formula_hint": "ny pris = gammel × (1 − p/100)",
                "answer": 19800*(1-0.10),
                "unit": "kr",
                "tol": 5.0,
                "rounding": 0,
                "lk20": LK20
            },
            {
                "title": tt("9) Membran – areal", "9) Waterproofing membrane area"),
                "scenario": tt("Du beregner membran på gulv.", "You calculate membrane on floor."),
                "question": tt("Gulv: 2,6 m × 1,9 m. Legg til 5% svinn. Hvor mange m² membran?",
                               "Floor: 2.6 m × 1.9 m. Add 5% waste. How many m² membrane?"),
                "formula_hint": "A_bestill = (L×B) × (1+svinn/100)",
                "answer": (2.6*1.9)*1.05,
                "unit": "m²",
                "tol": 0.05,
                "rounding": 2,
                "lk20": LK20
            },
            {
                "title": tt("10) Flis – areal per pakke", "10) Tiles – area per box"),
                "scenario": tt("Fliser selges i pakker med oppgitt m².", "Tiles are sold by box with m² coverage."),
                "question": tt("Du trenger 14,6 m². Én pakke dekker 1,44 m². Hvor mange pakker trenger du? (avrund opp)",
                               "Need 14.6 m². One box covers 1.44 m². How many boxes?"),
                "formula_hint": "pakker = total / per_pakke; avrund opp",
                "answer": math.ceil(14.6/1.44),
                "unit": "pakker",
                "tol": 0.0,
                "integer": True,
                "lk20": LK20
            },
        ],

        tt("Anleggsarbeider", "Construction worker (civil works)"): [
            {
                "title": tt("1) Masseutskifting – volum", "1) Earthworks – volume"),
                "scenario": tt("Du skal grave ut og fylle på pukk.", "You excavate and refill with aggregate."),
                "question": tt("Grøft: 12 m lang, 0,6 m bred, 0,4 m dyp. Finn volum (m³).",
                               "Trench: 12 m long, 0.6 m wide, 0.4 m deep. Volume (m³)?"),
                "formula_hint": "V = L×B×D",
                "answer": 12*0.6*0.4,
                "unit": "m³",
                "tol": 0.02,
                "rounding": 2,
                "lk20": LK20
            },
            {
                "title": tt("2) Komprimering – ekstra masse", "2) Compaction – extra material"),
                "scenario": tt("Du legger til 15% for komprimering og svinn.", "Add 15% for compaction/waste."),
                "question": tt("Du har beregnet 2,88 m³ pukk. Legg til 15%. Hvor mye bestiller du (m³)?",
                               "You calculated 2.88 m³. Add 15%. How much to order?"),
                "formula_hint": "V_bestill = V × (1 + p/100)",
                "answer": 2.88*1.15,
                "unit": "m³",
                "tol": 0.03,
                "rounding": 2,
                "lk20": LK20
            },
            {
                "title": tt("3) Areal for geotekstil", "3) Geotextile area"),
                "scenario": tt("Du legger geotekstil i bunnen.", "You lay geotextile."),
                "question": tt("Areal: 18 m × 3,0 m. Legg til 10% overlapp. Hvor mange m² trengs?",
                               "Area: 18 m × 3.0 m. Add 10% overlap. How many m² needed?"),
                "formula_hint": "A = L×B;  A_total = A×(1+overlapp/100)",
                "answer": (18*3.0)*1.10,
                "unit": "m²",
                "tol": 0.2,
                "rounding": 1,
                "lk20": LK20
            },
            {
                "title": tt("4) Stigning på rampe", "4) Ramp gradient"),
                "scenario": tt("Du skal sjekke stigning på en rampe.", "You check ramp gradient."),
                "question": tt("Høydeforskjell 0,24 m over lengde 6,0 m. Finn stigning i %.",
                               "Rise 0.24 m over 6.0 m. Find gradient in %."),
                "formula_hint": "stigning(%) = (høyde / lengde) × 100",
                "answer": (0.24/6.0)*100,
                "unit": "%",
                "tol": 0.2,
                "rounding": 2,
                "lk20": LK20
            },
            {
                "title": tt("5) Målestokk – virkelighet fra tegning", "5) Scale – real size from drawing"),
                "scenario": tt("Du leser arbeidstegning.", "You read a construction drawing."),
                "question": tt("På tegning (1:50) måler du 72 mm. Hvor mange meter er dette i virkeligheten?",
                               "On a 1:50 drawing you measure 72 mm. How many meters in reality?"),
                "formula_hint": "virkelighet = tegning × 50. 72 mm × 50 = 3600 mm = 3,6 m",
                "answer": 3.6,
                "unit": "m",
                "tol": 0.02,
                "rounding": 2,
                "lk20": LK20
            },
            {
                "title": tt("6) Kantstein – antall", "6) Curb stones – count"),
                "scenario": tt("Kantstein leveres i 1,0 m lengder.", "Curbstones come in 1.0 m lengths."),
                "question": tt("Strekning: 34 m. Legg til 5% svinn/kapp. Hvor mange stein (avrund opp)?",
                               "Length: 34 m. Add 5% waste. How many stones (round up)?"),
                "formula_hint": "antall = lengde×(1+svinn) / 1,0; avrund opp",
                "answer": math.ceil(34*1.05),
                "unit": "stk",
                "tol": 0.0,
                "integer": True,
                "lk20": LK20
            },
            {
                "title": tt("7) Asfalt – volum", "7) Asphalt volume"),
                "scenario": tt("Du skal legge asfalt på et område.", "You pave an area with asphalt."),
                "question": tt("Areal: 120 m². Tykkelse: 45 mm. Finn volum (m³).",
                               "Area: 120 m². Thickness: 45 mm. Volume (m³)?"),
                "formula_hint": "V = areal × tykkelse. 45 mm = 0,045 m",
                "answer": 120*0.045,
                "unit": "m³",
                "tol": 0.05,
                "rounding": 2,
                "lk20": LK20
            },
            {
                "title": tt("8) Rør i grøft – fall", "8) Pipe in trench – slope"),
                "scenario": tt("Du legger overvannsrør med fall.", "You lay stormwater pipe with slope."),
                "question": tt("Fallkrav: 1,0% over 18 m. Hvor mange cm fall?",
                               "Slope: 1.0% over 18 m. How many cm drop?"),
                "formula_hint": "fall(m) = (pct/100)×lengde; cm = m×100",
                "answer": ((1.0/100)*18)*100,
                "unit": "cm",
                "tol": 0.5,
                "rounding": 1,
                "lk20": LK20
            },
            {
                "title": tt("9) Grusdekke – areal og tonn (forenklet)", "9) Gravel – area and tonnes (simplified)"),
                "scenario": tt("Du bestiller grus. (Forenklet regning med fast vekt).", "You order gravel (simplified with fixed density)."),
                "question": tt("Areal 60 m², tykkelse 0,05 m. Tetthet (forenklet): 1,6 tonn per m³. Hvor mange tonn?",
                               "Area 60 m², thickness 0.05 m. Density: 1.6 tonnes per m³. How many tonnes?"),
                "formula_hint": "V = A×t; tonn = V × 1,6",
                "answer": (60*0.05)*1.6,
                "unit": "tonn",
                "tol": 0.2,
                "rounding": 2,
                "lk20": LK20
            },
            {
                "title": tt("10) Dreneringsrør – antall kveil", "10) Drain pipe – coil count"),
                "scenario": tt("Dreneringsrør leveres i kveil på 25 m.", "Drain pipes come in 25 m coils."),
                "question": tt("Du trenger 78 m drensrør. Hvor mange kveiler må du kjøpe? (avrund opp)",
                               "You need 78 m. How many 25 m coils?"),
                "formula_hint": "kveiler = ceil(total / 25)",
                "answer": math.ceil(78/25),
                "unit": "kveiler",
                "tol": 0.0,
                "integer": True,
                "lk20": LK20
            },
        ],
    }

def show_vty_content():
    st.markdown("## 🧰 " + tt("Veien til yrkeslivet – innhold", "Path to professional life – content"))
    st.caption(tt(
        "Realistiske oppgaver fra byggeplass – knyttet til programfag i BA og grunnleggende matematikk.",
        "Realistic job-site tasks linked to VET outcomes and practical math."
    ))

    if not st.session_state.get("vty_access", False):
        st.markdown("### 🔒 " + tt("Ingen tilgang", "No access"))
        vty_paywall_card()
        if st.button("⬅️ " + tt("Tilbake til tilgangssiden", "Back to access page"), use_container_width=True):
            st.session_state.view = "VeienTilYrkeslivet_Lås"
            st.rerun()
        return

    st.success(tt("Tilgang aktiv ✔️", "Access active ✔️"))

    # Hovedfaner inne i yrkeslivssiden
    main_tabs = st.tabs([
        "🧩 " + tt("Realistiske øvingsoppgaver", "Realistic practice tasks"),
        "📝 " + tt("Dokumentasjon og egenkontroll", "Documentation & self-check"),
        "🦺 " + tt("HMS i praksis", "HSE in practice"),
    ])

    with main_tabs[0]:
        st.markdown("### " + tt("Realistiske øvingsoppgaver", "Realistic practice tasks"))
        st.caption(tt(
            "Velg et yrke. Hver fane har 10 oppgaver. Lærer kan skru på fasit med lærerkode.",
            "Pick a trade. Each tab has 10 tasks. Teacher can reveal answers with the teacher code."
        ))

        data = vty_tasks_data()
        trade_tabs = st.tabs(list(data.keys()))
        for i, trade in enumerate(data.keys()):
            with trade_tabs[i]:
                tasks = data[trade]
                for j, task in enumerate(tasks):
                    _task_check_ui(task, key_prefix=f"vty_{i}_{j}")

    with main_tabs[1]:
        st.markdown("### " + tt("Dokumentasjon og egenkontroll", "Documentation & self-check"))
        st.write(tt(
            "Bruk denne strukturen når du leverer oppgaver i yrkesfag (vurderingsrettet):",
            "Use this structure when you submit tasks (assessment-oriented):"
        ))
        st.markdown(tt(
            """
1. **Oppgaveforståelse:** Hva er bestillingen / arbeidsoppdraget?  
2. **Mål og enheter:** Hvilke mål har du? Er alle i samme enhet?  
3. **Formelvalg:** Hvilken formel passer – og hvorfor?  
4. **Mellomregning:** Skriv regnestykker steg for steg.  
5. **Kontroll:** Grovsjekk + kontrollmåling/kalkulator.  
6. **Avvik:** Hva kan gi feil? (kapp, svinn, toleranser, målefeil)  
7. **Refleksjon:** Hva lærte du – og hva ville du gjort annerledes?
            """,
            """
1. Task understanding  
2. Measurements and units  
3. Formula choice  
4. Working  
5. Verification  
6. Deviations and sources of error  
7. Reflection
            """
        ))

    with main_tabs[2]:
        st.markdown("### " + tt("HMS i praksis", "HSE in practice"))
        st.write(tt(
            "Koble oppgavene til HMS: måling, ryddighet, risiko ved feilberegning (f.eks. feil fall, feil dimensjon, feil mengder).",
            "Link tasks to HSE: measurement, housekeeping, risks from miscalculation (e.g., wrong slope, wrong dimension, wrong quantities)."
        ))
        st.markdown(tt(
            """
**Mini-SJA (3 spørsmål):**
- Hva kan gå galt?  
- Hvordan forebygger vi?  
- Hva gjør vi hvis det skjer?  
            """,
            """
**Mini risk assessment (3 questions):**
- What can go wrong?  
- How do we prevent it?  
- What do we do if it happens?
            """
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
elif st.session_state.view == "VeienTilYrkeslivet_Lås":
    show_vty_gate()
elif st.session_state.view == "VeienTilYrkeslivet_Innhold":
    show_vty_content()
else:
    show_front_page()


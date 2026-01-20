import math
import base64
import time
import random
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image

import re
import ast
import operator as op


# ============================================================
# Streamlit side-oppsett (må komme før annen Streamlit-bruk)
# ============================================================
st.set_page_config(
    page_title="Bygg-kalkulatoren",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Komprimer vertikal luft (logo / toppmeny / tabs)
st.markdown(
    """
    <style>
      .block-container { padding-top: 3.5rem; padding-bottom: 1.0rem; }
      /* Litt strammere avstand mellom elementer */
      div[data-testid="stVerticalBlock"] { gap: 0.35rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Konfig + Logo (må ligge før all annen Streamlit-output)
# ============================================================
LOGO_PATH = Path(__file__).parent / "logo.png"

page_icon = None
# Profesjonell header med logo

# ============================================================
# App-navigasjon (Hjem / Pro)
# ============================================================
if "current_view" not in st.session_state:
    st.session_state.current_view = "home"

# ============================================================
# Modus: Skole / Produksjon
# ============================================================
if "app_mode" not in st.session_state:
    st.session_state.app_mode = "Skole"



def is_school_mode() -> bool:
    return st.session_state.get("app_mode", "Skole") == "Skole"



# ============================
# Komprimert header (logo + tittel + undertittel på én linje)
# ============================

LOGO_PATH = Path(__file__).parent / "logo.png"

# Strammere CSS rundt bilder/kolonner slik at logoen faktisk kan ligge tett på topmenyen.
st.markdown(
    """
    <style>
      /* Fjern unødvendig luft rundt Streamlit-bilder */
      div[data-testid="stImage"] { margin-top: 0rem !important; margin-bottom: 0rem !important; }
      div[data-testid="stImage"] > img { display:block; }

      /* Header-tekst: tittel + undertittel på én linje */
      .bk-title-row { display:flex; align-items: baseline; gap: 8px; line-height: 1; margin: 0; padding: 0; }
      .bk-title { font-size: 32px; font-weight: 800; color: #ff7a00; line-height: 1; }
      .bk-sub { font-size: 15px; color: #9aa4ad; line-height: 1; white-space: nowrap; }

      /* Trekk litt opp, men uten å overlappe */
      .bk-header-tight { margin-bottom: 8px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header rad: logo til venstre, tittel+undertittel rett etter.
header_left, header_right = st.columns([1.1, 5], gap="small")

with header_left:
    try:
        img = Image.open(LOGO_PATH)
        # Skaler ned slik at alt synes (logoen var for høy i tidligere versjoner)
        st.image(img, width=260)
    except Exception:
        # Hvis logo mangler i deploy, ikke knekk appen
        st.write("")

with header_right:
    st.markdown(
        """
        <div class="bk-header-tight">
          <div class="bk-title-row">
            <div class="bk-title"></div>
            <div class="bk-sub" style="margin-top:10px;">Fra skole til yrke – matematikk tilpasset yrkesfag!</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Trekker toppmenyen litt opp mot headeren (uten overlapp)
st.markdown("<div style='margin-top:-10px;'></div>", unsafe_allow_html=True)




# ============================================================
# Hjelpefunksjoner (enheter + formatering)
# ============================================================
def mm_to_m(mm: float) -> float:
    return mm / 1000.0


def cm_to_m(cm: float) -> float:
    return cm / 100.0


def m_to_mm(m: float) -> float:
    return m * 1000.0


def round_sensible(x: float, decimals: int = 3) -> float:
    return round(x, decimals)


def to_mm(value: float, unit: str) -> float:
    """Konverterer valgt enhet (mm/cm/m) til mm."""
    if unit == "mm":
        return value
    if unit == "cm":
        return value * 10.0
    if unit == "m":
        return value * 1000.0
    return value


def mm_to_all(mm: float) -> Dict[str, float]:
    """Returnerer mm, cm og m fra mm."""
    return {"mm": mm, "cm": mm / 10.0, "m": mm / 1000.0}


def format_value(key: str, value: Any) -> str:
    """Konsekvent formattering av outputverdier."""
    if isinstance(value, (int, float)):
        if key.endswith("_m3"):
            return f"{value:.3f}"
        if key.endswith("_m2"):
            return f"{value:.3f}"
        if key.endswith("_mm"):
            return f"{value:.1f}"
        if key.endswith("_cm"):
            return f"{value:.2f}"
        if key.endswith("_m"):
            return f"{value:.3f}"
        if "prosent" in key or key.endswith("_pct"):
            return f"{value:.1f}"
        return f"{value:.3f}".rstrip("0").rstrip(".")
    return str(value)


# ============================================================
# Resultatformat
# ============================================================
@dataclass
class CalcResult:
    name: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    steps: List[str]
    warnings: List[str]
    timestamp: str


def make_timestamp() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def warn_if(condition: bool, msg: str, warnings: List[str]):
    if condition:
        warnings.append(msg)


# ============================================================
# Kalkulatorer
# ============================================================
def calc_area_rectangle(length_m: float, width_m: float) -> CalcResult:
    warnings, steps = [], []
    warn_if(length_m <= 0 or width_m <= 0, "Lengde/bredde må være > 0.", warnings)
    area = length_m * width_m

    steps.append("Areal = lengde × bredde")
    steps.append(f"Areal = {length_m} m × {width_m} m = {area} m²")

    warn_if(area > 2000, "Uvanlig stort areal. Sjekk enheter (m vs mm).", warnings)
    warn_if(area < 0.1, "Uvanlig lite areal. Sjekk målene.", warnings)

    return CalcResult(
        name="Areal (rektangel)",
        inputs={"lengde_m": length_m, "bredde_m": width_m},
        outputs={"areal_m2": round_sensible(area, 3)},
        steps=steps,
        warnings=warnings,
        timestamp=make_timestamp(),
    )


def calc_area_with_waste(area_m2: float, waste_percent: float) -> CalcResult:
    warnings, steps = [], []
    warn_if(area_m2 <= 0, "Areal må være > 0.", warnings)
    warn_if(waste_percent < 0 or waste_percent > 50, "Svinn% virker uvanlig (0–50%).", warnings)

    factor = 1 + waste_percent / 100.0
    order_area = area_m2 * factor

    steps.append("Bestillingsareal = areal × (1 + svinn/100)")
    steps.append(f"= {area_m2} × (1 + {waste_percent}/100) = {order_area} m²")

    return CalcResult(
        name="Areal + svinn",
        inputs={"areal_m2": area_m2, "svinn_prosent": waste_percent},
        outputs={"bestillingsareal_m2": round_sensible(order_area, 3)},
        steps=steps,
        warnings=warnings,
        timestamp=make_timestamp(),
    )


def calc_area_composite(rectangles: List[Tuple[float, float]]) -> CalcResult:
    warnings, steps = [], []
    total = 0.0

    if not rectangles:
        warnings.append("Ingen delarealer lagt inn.")
    else:
        steps.append("Totalareal = sum(delareal_i), der delareal_i = lengde_i × bredde_i")

    for i, (l, w) in enumerate(rectangles, start=1):
        warn_if(l <= 0 or w <= 0, f"Del {i}: Lengde/bredde må være > 0.", warnings)
        a = l * w
        total += a
        steps.append(f"Del {i}: {l} × {w} = {a} m²")

    warn_if(total > 2000, "Uvanlig stort totalareal. Sjekk enheter.", warnings)

    return CalcResult(
        name="Areal (sammensatt av rektangler)",
        inputs={"deler": [{"lengde_m": l, "bredde_m": w} for (l, w) in rectangles]},
        outputs={"totalareal_m2": round_sensible(total, 3)},
        steps=steps,
        warnings=warnings,
        timestamp=make_timestamp(),
    )




def calc_perimeter(shape: str, a_m: float = 0.0, b_m: float = 0.0, r_m: float = 0.0) -> CalcResult:
    warnings, steps = [], []

    if shape == "Rektangel":
        warn_if(a_m <= 0 or b_m <= 0, "Begge sider må være > 0.", warnings)
        p = 2.0 * (a_m + b_m)
        steps.append("Omkrets (rektangel) = 2 × (a + b)")
        steps.append(f"= 2 × ({a_m} + {b_m}) = {p} m")
        return CalcResult(
            name="Omkrets (rektangel)",
            inputs={"a_m": a_m, "b_m": b_m},
            outputs={"omkrets_m": round_sensible(p, 3)},
            steps=steps,
            warnings=warnings,
            timestamp=make_timestamp(),
        )

    if shape == "Sirkel":
        warn_if(r_m <= 0, "Radius må være > 0.", warnings)
        p = 2.0 * math.pi * r_m
        steps.append("Omkrets (sirkel) = 2 × π × r")
        steps.append(f"= 2 × π × {r_m} = {p} m")
        return CalcResult(
            name="Omkrets (sirkel)",
            inputs={"r_m": r_m},
            outputs={"omkrets_m": round_sensible(p, 3)},
            steps=steps,
            warnings=warnings,
            timestamp=make_timestamp(),
        )

    warnings.append("Ukjent figur.")
    return CalcResult(
        name="Omkrets",
        inputs={"figur": shape},
        outputs={},
        steps=steps,
        warnings=warnings,
        timestamp=make_timestamp(),
    )

def calc_concrete_slab(length_m: float, width_m: float, thickness_mm: float) -> CalcResult:
    warnings, steps = [], []
    warn_if(length_m <= 0 or width_m <= 0, "Lengde/bredde må være > 0.", warnings)
    warn_if(thickness_mm <= 0, "Tykkelse må være > 0.", warnings)
    warn_if(thickness_mm < 50 or thickness_mm > 500, "Tykkelse (mm) virker uvanlig (50–500 mm).", warnings)

    thickness_m = mm_to_m(thickness_mm)
    volume = length_m * width_m * thickness_m

    steps.append("Volum = lengde × bredde × tykkelse")
    steps.append(f"Tykkelse = {thickness_mm} mm = {thickness_m} m")
    steps.append(f"Volum = {length_m} × {width_m} × {thickness_m} = {volume} m³")

    warn_if(volume > 200, "Uvanlig stort betongvolum. Sjekk enheter og mål.", warnings)

    return CalcResult(
        name="Betongplate (volum)",
        inputs={"lengde_m": length_m, "bredde_m": width_m, "tykkelse_mm": thickness_mm},
        outputs={"volum_m3": round_sensible(volume, 3)},
        steps=steps,
        warnings=warnings,
        timestamp=make_timestamp(),
    )


def calc_strip_foundation(length_m: float, width_m: float, height_mm: float) -> CalcResult:
    warnings, steps = [], []
    warn_if(length_m <= 0 or width_m <= 0, "Lengde/bredde må være > 0.", warnings)
    warn_if(height_mm <= 0, "Høyde må være > 0.", warnings)
    warn_if(height_mm < 100 or height_mm > 2000, "Høyde (mm) virker uvanlig (100–2000 mm).", warnings)

    height_m = mm_to_m(height_mm)
    volume = length_m * width_m * height_m

    steps.append("Volum = lengde × bredde × høyde")
    steps.append(f"Høyde = {height_mm} mm = {height_m} m")
    steps.append(f"Volum = {length_m} × {width_m} × {height_m} = {volume} m³")

    return CalcResult(
        name="Stripefundament (volum)",
        inputs={"lengde_m": length_m, "bredde_m": width_m, "hoyde_mm": height_mm},
        outputs={"volum_m3": round_sensible(volume, 3)},
        steps=steps,
        warnings=warnings,
        timestamp=make_timestamp(),
    )


def calc_column_cylinder(diameter_mm: float, height_m: float) -> CalcResult:
    warnings, steps = [], []
    warn_if(diameter_mm <= 0 or height_m <= 0, "Diameter/høyde må være > 0.", warnings)
    warn_if(diameter_mm < 80 or diameter_mm > 1500, "Diameter (mm) virker uvanlig (80–1500 mm).", warnings)

    r_m = mm_to_m(diameter_mm) / 2.0
    volume = math.pi * (r_m**2) * height_m

    steps.append("Volum sylinder = π × r² × h")
    steps.append(f"r = {diameter_mm} mm / 2 = {r_m} m")
    steps.append(f"Volum = π × {r_m}² × {height_m} = {volume} m³")

    return CalcResult(
        name="Søyle (sylinder) (volum)",
        inputs={"diameter_mm": diameter_mm, "hoyde_m": height_m},
        outputs={"volum_m3": round_sensible(volume, 3)},
        steps=steps,
        warnings=warnings,
        timestamp=make_timestamp(),
    )


def calc_fall(length_m: float, mode: str, value: float) -> CalcResult:
    warnings, steps = [], []
    warn_if(length_m <= 0, "Lengde må være > 0.", warnings)

    if mode == "prosent":
        warn_if(value < 0 or value > 20, "Prosentfall virker uvanlig (0–20%).", warnings)
        mm_per_m = value / 100.0 * 1000.0
        steps.append(f"mm per meter = ({value}/100) × 1000 = {mm_per_m} mm/m")
    elif mode == "1:x":
        warn_if(value <= 0, "x må være > 0.", warnings)
        warn_if(value < 20 or value > 200, "1:x virker uvanlig (typisk 1:20 til 1:200).", warnings)
        mm_per_m = 1000.0 / value
        steps.append(f"mm per meter = 1000 / {value} = {mm_per_m} mm/m")
    elif mode == "mm_per_m":
        warn_if(value < 0 or value > 200, "mm per meter virker uvanlig (0–200).", warnings)
        mm_per_m = value
        steps.append(f"mm per meter = {mm_per_m} mm/m")
    else:
        warnings.append("Ugyldig modus for fall.")
        mm_per_m = 0.0

    height_diff_mm = mm_per_m * length_m
    height_diff_m = mm_to_m(height_diff_mm)

    steps.append(f"Høydeforskjell = {mm_per_m} × {length_m} = {height_diff_mm} mm = {height_diff_m} m")

    return CalcResult(
        name="Fallberegning",
        inputs={"lengde_m": length_m, "modus": mode, "verdi": value},
        outputs={
            "mm_per_meter": round_sensible(mm_per_m, 2),
            "hoydeforskjell_mm": round_sensible(height_diff_mm, 1),
            "hoydeforskjell_m": round_sensible(height_diff_m, 3),
        },
        steps=steps,
        warnings=warnings,
        timestamp=make_timestamp(),
    )


def calc_scale_bidir(value: float, unit: str, scale_n: int, direction: str) -> CalcResult:
    """
    direction:
      - "Tegning → virkelighet"
      - "Virkelighet → tegning"

    scale_n tolkes som målestokk 1:scale_n (1–100)
    """
    warnings, steps = [], []

    warn_if(value <= 0, "Målet må være > 0.", warnings)
    warn_if(scale_n < 1 or scale_n > 100, "Målestokk (n) må være mellom 1 og 100.", warnings)

    input_mm = to_mm(value, unit)

    if direction == "Tegning → virkelighet":
        out_mm = input_mm * scale_n
        out_all = mm_to_all(out_mm)

        steps.append("Retning: Tegning → virkelighet")
        steps.append(f"Målestokk: 1:{scale_n}")
        steps.append(f"Inndata: {value} {unit} = {input_mm} mm")
        steps.append(f"Virkelig mål = tegning × målestokk = {input_mm} × {scale_n} = {out_mm} mm")

        return CalcResult(
            name="Målestokk (tegning → virkelighet)",
            inputs={"verdi": value, "enhet": unit, "malestokk_1_til_n": scale_n},
            outputs={
                "virkelig_mm": round_sensible(out_all["mm"], 1),
                "virkelig_cm": round_sensible(out_all["cm"], 2),
                "virkelig_m": round_sensible(out_all["m"], 3),
            },
            steps=steps,
            warnings=warnings,
            timestamp=make_timestamp(),
        )

    if direction == "Virkelighet → tegning":
        out_mm = input_mm / scale_n if scale_n != 0 else 0.0
        out_all = mm_to_all(out_mm)

        steps.append("Retning: Virkelighet → tegning")
        steps.append(f"Målestokk: 1:{scale_n}")
        steps.append(f"Inndata: {value} {unit} = {input_mm} mm")
        steps.append(f"Tegningsmål = virkelighet ÷ målestokk = {input_mm} ÷ {scale_n} = {out_mm} mm")

        return CalcResult(
            name="Målestokk (virkelighet → tegning)",
            inputs={"verdi": value, "enhet": unit, "malestokk_1_til_n": scale_n},
            outputs={
                "tegning_mm": round_sensible(out_all["mm"], 1),
                "tegning_cm": round_sensible(out_all["cm"], 2),
                "tegning_m": round_sensible(out_all["m"], 3),
            },
            steps=steps,
            warnings=warnings,
            timestamp=make_timestamp(),
        )

    warnings.append("Ugyldig retning valgt.")
    return CalcResult(
        name="Målestokk",
        inputs={"verdi": value, "enhet": unit, "malestokk_1_til_n": scale_n, "retning": direction},
        outputs={},
        steps=steps,
        warnings=warnings,
        timestamp=make_timestamp(),
    )


def calc_pythagoras(a_m: float, b_m: float) -> CalcResult:
    warnings, steps = [], []
    warn_if(a_m <= 0 or b_m <= 0, "Begge sider må være > 0.", warnings)

    c = math.sqrt(a_m**2 + b_m**2)
    steps.append("Diagonal c = √(a² + b²)")
    steps.append(f"= √({a_m}² + {b_m}²) = {c} m")

    return CalcResult(
        name="Pytagoras (diagonal)",
        inputs={"a_m": a_m, "b_m": b_m},
        outputs={"diagonal_m": round_sensible(c, 3)},
        steps=steps,
        warnings=warnings,
        timestamp=make_timestamp(),
    )


def calc_price(base_price: float, rabatt_prosent: float, paslag_prosent: float, mva_prosent: float) -> CalcResult:
    warnings, steps = [], []
    warn_if(base_price < 0, "Pris kan ikke være negativ.", warnings)
    warn_if(rabatt_prosent < 0 or rabatt_prosent > 90, "Rabatt virker uvanlig (0–90%).", warnings)
    warn_if(paslag_prosent < 0 or paslag_prosent > 200, "Påslag virker uvanlig (0–200%).", warnings)
    warn_if(mva_prosent < 0 or mva_prosent > 50, "MVA virker uvanlig (0–50%).", warnings)

    price_after_discount = base_price * (1 - rabatt_prosent / 100.0)
    price_after_markup = price_after_discount * (1 + paslag_prosent / 100.0)
    price_after_mva = price_after_markup * (1 + mva_prosent / 100.0)

    steps.append(f"Etter rabatt: {base_price} × (1 - {rabatt_prosent}/100) = {price_after_discount}")
    steps.append(f"Etter påslag: {price_after_discount} × (1 + {paslag_prosent}/100) = {price_after_markup}")
    steps.append(f"Inkl. MVA: {price_after_markup} × (1 + {mva_prosent}/100) = {price_after_mva}")

    return CalcResult(
        name="Pris (rabatt/påslag/MVA)",
        inputs={
            "grunnpris": base_price,
            "rabatt_prosent": rabatt_prosent,
            "paslag_prosent": paslag_prosent,
            "mva_prosent": mva_prosent,
        },
        outputs={
            "etter_rabatt": round_sensible(price_after_discount, 2),
            "etter_paslag": round_sensible(price_after_markup, 2),
            "inkl_mva": round_sensible(price_after_mva, 2),
        },
        steps=steps,
        warnings=warnings,
        timestamp=make_timestamp(),
    )


def calc_time_estimate(quantity: float, productivity_per_hour: float) -> CalcResult:
    warnings, steps = [], []
    warn_if(quantity <= 0, "Mengde må være > 0.", warnings)
    warn_if(productivity_per_hour <= 0, "Produksjon må være > 0.", warnings)

    hours = quantity / productivity_per_hour
    days_7_5h = hours / 7.5

    steps.append(f"Timer = {quantity} / {productivity_per_hour} = {hours}")
    steps.append(f"Dagsverk (7,5t) = {hours} / 7,5 = {days_7_5h}")

    return CalcResult(
        name="Tidsestimat",
        inputs={"mengde": quantity, "produksjon_per_time": productivity_per_hour},
        outputs={"timer": round_sensible(hours, 2), "dagsverk_7_5t": round_sensible(days_7_5h, 2)},
        steps=steps,
        warnings=warnings,
        timestamp=make_timestamp(),
    )


def calc_deviation(projected: float, measured: float, tolerance_mm: float, unit: str) -> CalcResult:
    warnings, steps = [], []

    if unit == "m":
        projected_mm = m_to_mm(projected)
        measured_mm = m_to_mm(measured)
        steps.append(f"Konverterer til mm: {projected} m = {projected_mm} mm, {measured} m = {measured_mm} mm")
    else:
        projected_mm = projected
        measured_mm = measured

    warn_if(tolerance_mm < 0, "Toleranse kan ikke være negativ.", warnings)

    diff_mm = measured_mm - projected_mm
    abs_diff_mm = abs(diff_mm)
    ok = abs_diff_mm <= tolerance_mm

    steps.append(f"Avvik = {measured_mm} - {projected_mm} = {diff_mm} mm")
    steps.append(f"|Avvik| = {abs_diff_mm} mm")
    steps.append(f"Innenfor toleranse? {'OK' if ok else 'IKKE OK'}")

    return CalcResult(
        name="Avvik / toleranse",
        inputs={"prosjektert": projected, "malt": measured, "toleranse_mm": tolerance_mm, "enhet": unit},
        outputs={
            "avvik_mm": round_sensible(diff_mm, 1),
            "abs_avvik_mm": round_sensible(abs_diff_mm, 1),
            "status": "OK" if ok else "IKKE OK",
        },
        steps=steps,
        warnings=warnings,
        timestamp=make_timestamp(),
    )


def calc_tommermannskledning_width(
    measure_cm: float,
    overlap_cm: float,
    under_width_mm: float,
    over_width_mm: float,
) -> CalcResult:
    """
    Avgrensning iht. dine krav:
    - Kun: mål fra–til (cm), omlegg (cm), underliggerbredde (mm), overliggerbredde (mm).
    - Underliggere antas kant-i-kant.
    - Overliggere dekker skjøter: antall = underliggere - 1.
    - Omlegg tolkes som overlapp inn på hver side -> min overliggerbredde = 2 * omlegg.
    """
    warnings, steps = [], []

    warn_if(measure_cm <= 0, "Mål fra–til må være > 0 cm.", warnings)
    warn_if(overlap_cm < 0, "Omlegg kan ikke være negativt.", warnings)
    warn_if(under_width_mm <= 0, "Underliggerbredde må være > 0 mm.", warnings)
    warn_if(over_width_mm <= 0, "Overliggerbredde må være > 0 mm.", warnings)

    measure_mm = measure_cm * 10.0
    overlap_mm = overlap_cm * 10.0

    under_count = math.ceil(measure_mm / under_width_mm) if under_width_mm > 0 else 0
    covered_mm = under_count * under_width_mm
    overdekning_mm = covered_mm - measure_mm

    over_count = max(under_count - 1, 0)

    min_over_width_mm = 2.0 * overlap_mm
    ok_over_width = over_width_mm >= min_over_width_mm

    if not ok_over_width:
        warnings.append(
            f"Overligger ({over_width_mm} mm) er for smal for omlegg {overlap_cm} cm. "
            f"Min anbefalt overliggerbredde er {min_over_width_mm:.0f} mm (2 × omlegg)."
        )

    steps.append("Konvertering: cm → mm")
    steps.append(f"Mål fra–til: {measure_cm} cm = {measure_mm} mm")
    steps.append(f"Omlegg: {overlap_cm} cm = {overlap_mm} mm")

    steps.append("Antall underliggere: ceil(bredde / underbredde)")
    steps.append(f"= ceil({measure_mm} / {under_width_mm}) = {under_count}")

    steps.append("Dekket bredde = antall underliggere × underbredde")
    steps.append(f"= {under_count} × {under_width_mm} = {covered_mm} mm")
    steps.append(f"Overdekning = {covered_mm} - {measure_mm} = {overdekning_mm} mm")

    steps.append("Antall overliggere (skjøter) = underliggere - 1")
    steps.append(f"= {under_count} - 1 = {over_count}")

    steps.append("Kontroll: Min overliggerbredde = 2 × omlegg")
    steps.append(f"= 2 × {overlap_mm} = {min_over_width_mm:.0f} mm")
    steps.append(f"Valgt overliggerbredde: {over_width_mm} mm → {'OK' if ok_over_width else 'IKKE OK'}")

    return CalcResult(
        name="Tømmermannskledning",
        inputs={
            "mal_fra_til_cm": measure_cm,
            "omlegg_cm": overlap_cm,
            "underligger_bredde_mm": under_width_mm,
            "overligger_bredde_mm": over_width_mm,
        },
        outputs={
            "underliggere_antall": under_count,
            "overliggere_antall": over_count,
            "dekket_bredde_mm": round_sensible(covered_mm, 1),
            "overdekning_mm": round_sensible(overdekning_mm, 1),
            "min_overligger_bredde_mm": round_sensible(min_over_width_mm, 0),
            "overligger_ok_for_omlegg": "OK" if ok_over_width else "IKKE OK",
        },
        steps=steps,
        warnings=warnings,
        timestamp=make_timestamp(),
    )

def calc_tiles_wall(
    tile_h: float,
    tile_h_unit: str,
    tile_w: float,
    tile_w_unit: str,
    grout: float,
    grout_unit: str,
    wall_h: float,
    wall_h_unit: str,
    wall_w: float,
    wall_w_unit: str,
    add_10_percent: bool,
    price_per_tile: float,
) -> CalcResult:
    """
    Fliskalkulator (vegg):
    - Regner antall fliser i høyde og bredde basert på "modul" = flis + fuge.
    - Total = antall_h * antall_b
    - Valgfritt: +10% ekstra
    - Valgfritt: pris per flis -> totalpris

    Merk: Dette er en praktisk, robust tommelfingerregel for bestilling.
    """

    warnings, steps = [], []

    # Validering
    warn_if(tile_h <= 0 or tile_w <= 0, "Flisstørrelse må være > 0.", warnings)
    warn_if(wall_h <= 0 or wall_w <= 0, "Vegg-mål må være > 0.", warnings)
    warn_if(grout < 0, "Fugeavstand kan ikke være negativ.", warnings)
    warn_if(price_per_tile < 0, "Pris kan ikke være negativ.", warnings)

    # Konverter alt til mm
    tile_h_mm = to_mm(float(tile_h), str(tile_h_unit))
    tile_w_mm = to_mm(float(tile_w), str(tile_w_unit))
    grout_mm = to_mm(float(grout), str(grout_unit))
    wall_h_mm = to_mm(float(wall_h), str(wall_h_unit))
    wall_w_mm = to_mm(float(wall_w), str(wall_w_unit))

    # Modulmål (flis + fuge)
    module_h = tile_h_mm + grout_mm
    module_w = tile_w_mm + grout_mm

    warn_if(module_h <= 0 or module_w <= 0, "Ugyldig modulmål (flis + fuge).", warnings)

    # Antall i hver retning (enkel og robust metode)
    # NB: I praksis kan det bli kutt på kantene. Derfor finnes +10% valget.
    tiles_h = math.ceil(wall_h_mm / module_h) if module_h > 0 else 0
    tiles_w = math.ceil(wall_w_mm / module_w) if module_w > 0 else 0
    base_total = tiles_h * tiles_w

    extra_total = math.ceil(base_total * 1.10) if add_10_percent else base_total

    total_price = (extra_total * price_per_tile) if price_per_tile and price_per_tile > 0 else 0.0

    # Stegvis forklaring (skolemodus)
    steps.append("1) Gjør om alle mål til samme enhet (mm).")
    steps.append(f"Flis (H×B): {tile_h} {tile_h_unit} × {tile_w} {tile_w_unit} = {tile_h_mm:.1f} mm × {tile_w_mm:.1f} mm")
    steps.append(f"Fuge: {grout} {grout_unit} = {grout_mm:.1f} mm")
    steps.append(f"Vegg (H×B): {wall_h} {wall_h_unit} × {wall_w} {wall_w_unit} = {wall_h_mm:.1f} mm × {wall_w_mm:.1f} mm")
    steps.append("2) Modul = flis + fuge (i hver retning).")
    steps.append(f"Modul høyde = {tile_h_mm:.1f} + {grout_mm:.1f} = {module_h:.1f} mm")
    steps.append(f"Modul bredde = {tile_w_mm:.1f} + {grout_mm:.1f} = {module_w:.1f} mm")
    steps.append("3) Antall fliser = tak-oppover (ceil) av veggmål / modul.")
    steps.append(f"Antall i høyden = ceil({wall_h_mm:.1f} / {module_h:.1f}) = {tiles_h}")
    steps.append(f"Antall i bredden = ceil({wall_w_mm:.1f} / {module_w:.1f}) = {tiles_w}")
    steps.append(f"4) Totalt antall = {tiles_h} × {tiles_w} = {base_total} fliser")

    if add_10_percent:
        steps.append(f"5) +10% ekstra: ceil({base_total} × 1,10) = {extra_total} fliser")

    if price_per_tile and price_per_tile > 0:
        steps.append(f"Totalpris = {extra_total} × {price_per_tile} = {total_price}")

    # Varsler (realistisk bruk)
    warn_if(grout_mm > 10, "Fugeavstand virker stor. Sjekk enhet (mm/cm).", warnings)
    warn_if(tile_h_mm > 1200 or tile_w_mm > 1200, "Flisstørrelse virker uvanlig stor. Sjekk enhet.", warnings)
    warn_if(wall_h_mm > 6000 or wall_w_mm > 8000, "Vegg-mål virker store. Sjekk enhet.", warnings)

    return CalcResult(
        name="Fliser",
        inputs={
            "flis_hoyde": tile_h, "flis_h_enhet": tile_h_unit,
            "flis_bredde": tile_w, "flis_b_enhet": tile_w_unit,
            "fuge": grout, "fuge_enhet": grout_unit,
            "vegg_hoyde": wall_h, "vegg_h_enhet": wall_h_unit,
            "vegg_bredde": wall_w, "vegg_b_enhet": wall_w_unit,
            "legg_til_10_prosent": add_10_percent,
            "pris_per_flis": price_per_tile,
        },
        outputs={
            "fliser_hoyde_antall": tiles_h,
            "fliser_bredde_antall": tiles_w,
            "trenger_fliser": extra_total,
            "totalpris": round_sensible(total_price, 2),
        },
        steps=steps,
        warnings=warnings,
        timestamp=make_timestamp(),
    )

# ============================================================
# Offline AI-robot (tekst + regnestykker, uten internett)
# ============================================================

_ALLOWED_BINOPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
}
_ALLOWED_UNARYOPS = {
    ast.UAdd: op.pos,
    ast.USub: op.neg,
}

# Whitelist math-funksjoner/konstanter
_ALLOWED_NAMES = {
    "pi": math.pi,
    "e": math.e,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "abs": abs,
    "round": round,
}

def _safe_eval_expr(expr: str) -> float:
    """Trygg evaluering av regneuttrykk (ingen eval())."""
    expr = expr.strip()
    node = ast.parse(expr, mode="eval")

    def _eval(n):
        if isinstance(n, ast.Expression):
            return _eval(n.body)

        if isinstance(n, ast.Constant):
            if isinstance(n.value, (int, float)):
                return float(n.value)
            raise ValueError("Ugyldig konstant")

        if isinstance(n, ast.BinOp):
            if type(n.op) not in _ALLOWED_BINOPS:
                raise ValueError("Ugyldig operator")
            return _ALLOWED_BINOPS[type(n.op)](_eval(n.left), _eval(n.right))

        if isinstance(n, ast.UnaryOp):
            if type(n.op) not in _ALLOWED_UNARYOPS:
                raise ValueError("Ugyldig unary-operator")
            return _ALLOWED_UNARYOPS[type(n.op)](_eval(n.operand))

        if isinstance(n, ast.Call):
            if not isinstance(n.func, ast.Name):
                raise ValueError("Ugyldig funksjonskall")
            fname = n.func.id
            if fname not in _ALLOWED_NAMES:
                raise ValueError("Ukjent funksjon")
            args = [_eval(a) for a in n.args]
            return float(_ALLOWED_NAMES[fname](*args))

        if isinstance(n, ast.Name):
            if n.id in _ALLOWED_NAMES:
                return float(_ALLOWED_NAMES[n.id])
            raise ValueError("Ukjent navn")

        raise ValueError("Ugyldig uttrykk")

    return _eval(node)

def _norm(s: str) -> str:
    s = s.strip().lower()
    s = s.replace("×", "*").replace("x", "*")
    s = s.replace(",", ".")
    s = s.replace("^", "**")
    return s

def ai_math_bot(question: str) -> dict:
    """
    Returnerer dict: {ok, title, answer, steps, warnings}
    """
    q0 = question
    q = _norm(question)

    steps = []
    warnings = []

    # 1) Prosent av
    m = re.search(r"(\d+(?:\.\d+)?)\s*%?\s*av\s*(\d+(?:\.\d+)?)", q)
    if m:
        pct = float(m.group(1))
        base = float(m.group(2))
        res = base * (pct / 100.0)
        steps.append(f"{pct}% av {base} = {base} * ({pct}/100)")
        return {"ok": True, "title": "Prosent", "answer": f"{res:.2f}", "steps": steps, "warnings": warnings}

    # 2) Areal (rektangel): “areal 4*6” eller “areal 4 * 6”
    if "areal" in q:
        m = re.search(r"(\d+(?:\.\d+)?)\s*\*\s*(\d+(?:\.\d+)?)", q)
        if m:
            l = float(m.group(1))
            b = float(m.group(2))
            a = l * b
            steps.append("Areal = lengde * bredde")
            steps.append(f"{l} * {b} = {a}")
            return {"ok": True, "title": "Areal", "answer": f"{a:.3f} m²", "steps": steps, "warnings": warnings}

    # 3) Volum betongplate: “volum 5*4*100mm”
    if "volum" in q or "betong" in q:
        m = re.search(r"(\d+(?:\.\d+)?)\s*\*\s*(\d+(?:\.\d+)?)\s*\*\s*(\d+(?:\.\d+)?)\s*mm", q)
        if m:
            l = float(m.group(1))
            b = float(m.group(2))
            t_mm = float(m.group(3))
            t_m = t_mm / 1000.0
            v = l * b * t_m
            steps.append("Volum = lengde * bredde * tykkelse")
            steps.append(f"tykkelse: {t_mm} mm = {t_m} m")
            steps.append(f"{l} * {b} * {t_m} = {v}")
            return {"ok": True, "title": "Volum", "answer": f"{v:.3f} m³", "steps": steps, "warnings": warnings}

    # 4) Pytagoras: “diagonal 3 og 4”
    if "diagonal" in q or "pytagoras" in q:
        m = re.search(r"(\d+(?:\.\d+)?)\s*(?:og|,)\s*(\d+(?:\.\d+)?)", q)
        if m:
            a = float(m.group(1))
            b = float(m.group(2))
            c = math.sqrt(a*a + b*b)
            steps.append("c = sqrt(a^2 + b^2)")
            steps.append(f"sqrt({a}^2 + {b}^2) = {c}")
            return {"ok": True, "title": "Diagonal", "answer": f"{c:.3f} m", "steps": steps, "warnings": warnings}

    # 5) Fall: “2% fall på 3m”
    m = re.search(r"(\d+(?:\.\d+)?)\s*%\s*fall.*?(\d+(?:\.\d+)?)\s*m", q)
    if m:
        pct = float(m.group(1))
        length_m = float(m.group(2))
        mm = (pct/100.0) * length_m * 1000.0
        steps.append(f"mm = ({pct}/100) * {length_m} * 1000")
        return {"ok": True, "title": "Fall", "answer": f"{mm:.1f} mm", "steps": steps, "warnings": warnings}

    # 6) Hvis ingen tekst-intent: forsøk regnestykke
    try:
        val = _safe_eval_expr(q)
        steps.append(f"Tolket som uttrykk: {q}")
        return {"ok": True, "title": "Uttrykk", "answer": f"{val:.6g}", "steps": steps, "warnings": warnings}
    except Exception:
        return {
            "ok": False,
            "title": "Ukjent",
            "answer": "Jeg forstår ikke spørsmålet ennå. Prøv f.eks. 'areal 4 x 6', '25% av 1800' eller '2*(3+5)'.",
            "steps": [],
            "warnings": [],
        }

# ============================================================
# Profesjonell visning (uten understreker)
# ============================================================
OUTPUT_LABELS = {
    # Målestokk
    "virkelig_mm": "Virkelig mål (mm)",
    "virkelig_cm": "Virkelig mål (cm)",
    "virkelig_m": "Virkelig mål (m)",
    "tegning_mm": "Tegningsmål (mm)",
    "tegning_cm": "Tegningsmål (cm)",
    "tegning_m": "Tegningsmål (m)",
    # Kledning
    "underliggere_antall": "Antall underliggere",
    "overliggere_antall": "Antall overliggere",
    "dekket_bredde_mm": "Dekket bredde (mm)",
    "overdekning_mm": "Overdekning (mm)",
    "min_overligger_bredde_mm": "Min. overliggerbredde (mm)",
    "overligger_ok_for_omlegg": "Overligger OK for omlegg",
    # Generelt
    "areal_m2": "Areal (m²)",
    "bestillingsareal_m2": "Bestillingsareal (m²)",
    "totalareal_m2": "Totalareal (m²)",
    "volum_m3": "Volum (m³)",
    "diagonal_m": "Diagonal (m)",
    "timer": "Timer",
    "dagsverk_7_5t": "Dagsverk (7,5 t)",
    "avvik_mm": "Avvik (mm)",
    "abs_avvik_mm": "Absolutt avvik (mm)",
    "status": "Status",
    "mm_per_meter": "Fall (mm per meter)",
    "hoydeforskjell_mm": "Høydeforskjell (mm)",
    "hoydeforskjell_m": "Høydeforskjell (m)",
    "etter_rabatt": "Etter rabatt",
    "etter_paslag": "Etter påslag",
    "inkl_mva": "Inkl. MVA",
    "omkrets_m": "Omkrets (m)",
    "resultat": "Resultat",
    "endring_prosent": "Endring (%)",
}


def label_for(key: str) -> str:
    return OUTPUT_LABELS.get(key, key.replace("_", " ").strip().capitalize())

# ============================
# "Bli en profesjonell yrkesutøver!" skjerm (Streamlit)
# ============================

def show_pro_screen():
    is_school = is_school_mode()

    st.subheader("Vil du bli en profesjonell yrkesutøver?")
    st.caption("Pro gir deg funksjoner som sparer tid, gir bedre kontroll og gjør dokumentasjon enklere.")

    c1, c2 = st.columns([2, 1])
    with c1:
        if is_school:
            st.markdown(
                """
**Pro for skole** handler om læring, vurdering og struktur:

- Oppgaver med *skjult fasit* (eleven må prøve først)
- Refleksjon og egenkontroll knyttet til hver beregning
- Eksport til PDF for innlevering
- Lærer-/klassevis historikk (dokumentasjon av progresjon)
                """
            )
        else:
            st.markdown(
                """
**Pro for produksjon** handler om tempo, færre feil og bedre dokumentasjon:

- Prosjektlogg (jobblogg): Prosjekt → rom → beregning
- Eksport til PDF/CSV for KS, bestilling og dokumentasjon
- Produksjonstilpasset avrunding og tydeligere varsler
- Standardverdier for bransje (mål, svinn, toleranser)
                """
            )

    with c2:
        st.markdown("**Pro inkluderer**")
        st.write("• Mer historikk")
        st.write("• Eksport")
        st.write("• Pro-funksjoner per fane")
        st.write("• Prioritert støtte (valgfritt)")


# ============================
# Integrasjon: legg "Bli en profesjonell yrkesutøver?" i sidepanelet
# ============================

# Sett default state
if "show_pro" not in st.session_state:
    st.session_state.show_pro = False


# Vis Pro-skjerm øverst i appen når brukeren klikker
if st.session_state.get("show_pro", False):
    st.divider()
    show_pro_screen()
    if st.button("Lukk Pro-skjerm"):
        st.session_state.show_pro = False
    st.stop()


# ============================================================
# Lek og lær (nivåbasert trening i skolemodus)
# ============================================================

_PLAY_CORRECT_TO_PASS = 3  # antall riktige i hvert nivå for å låse opp neste


def _pp_key(topic: str) -> str:
    return topic.strip().lower()


def _get_progress(topic: str) -> dict:
    k = _pp_key(topic)
    prog = st.session_state.play_progress.get(k)
    if not prog:
        prog = {"unlocked": 1, "completed": set(), "stars": {}, "correct_counts": {}}
        st.session_state.play_progress[k] = prog
    if isinstance(prog.get("completed"), list):
        prog["completed"] = set(prog["completed"])
    return prog


def _set_completed(topic: str, level: int):
    prog = _get_progress(topic)
    prog["completed"].add(int(level))
    prog["unlocked"] = max(int(prog.get("unlocked", 1)), int(level) + 1)


def _question_seed(topic: str, level: int, idx: int) -> int:
    # Stabil, men fortsatt "tilfeldig" per brukerøkt
    base = int(st.session_state.get("_play_seed", 0) or 0)
    if base == 0:
        base = random.randint(10_000, 99_999)
        st.session_state["_play_seed"] = base
    return hash((base, _pp_key(topic), int(level), int(idx))) & 0xFFFFFFFF


def _make_question(topic: str, level: int, q_index: int) -> dict:
    rnd = random.Random(_question_seed(topic, level, q_index))

    # Genererer oppgaver som treffer fanene i appen (Areal/Omkrets/Volum/Målestokk/Prosent)
    if topic == "Areal":
        if level == 1:
            l = rnd.randint(2, 12)
            w = rnd.randint(2, 10)
            ans = l * w
            return {
                "prompt": f"Finn arealet av et rektangel: lengde {l} m og bredde {w} m. Svar i m².",
                "answer": float(ans),
                "tolerance": 0.01,
                "unit": "m²",
                "hint": "Areal = lengde × bredde",
            }
        if level == 2:
            l_cm = rnd.choice([250, 300, 420, 560, 675, 720])
            w_cm = rnd.choice([120, 150, 180, 200, 240, 260])
            l_m = l_cm / 100
            w_m = w_cm / 100
            ans = l_m * w_m
            return {
                "prompt": f"Finn arealet: lengde {l_cm} cm og bredde {w_cm} cm. Konverter til meter først. Svar i m².",
                "answer": float(ans),
                "tolerance": 0.01,
                "unit": "m²",
                "hint": "cm → m: del på 100. Areal = l × b.",
            }
        # level 3+
        base_area = rnd.choice([12, 18, 24, 30, 36, 42])
        waste = rnd.choice([5, 10, 12, 15])
        ans = base_area * (1 + waste / 100)
        return {
            "prompt": f"Du har et areal på {base_area} m² og svinn på {waste}%. Hva er bestillingsarealet?",
            "answer": float(ans),
            "tolerance": 0.05,
            "unit": "m²",
            "hint": "Bestillingsareal = areal × (1 + svinn/100)",
        }

    if topic == "Omkrets":
        if level == 1:
            a = rnd.randint(2, 12)
            b = rnd.randint(2, 10)
            ans = 2 * (a + b)
            return {
                "prompt": f"Finn omkretsen av et rektangel med sider {a} m og {b} m. Svar i meter.",
                "answer": float(ans),
                "tolerance": 0.01,
                "unit": "m",
                "hint": "Omkrets (rektangel) = 2(a + b)",
            }
        if level == 2:
            r = rnd.choice([0.2, 0.25, 0.3, 0.35, 0.4, 0.5])
            ans = 2 * math.pi * r
            return {
                "prompt": f"Finn omkretsen av en sirkel med radius {r} m. Bruk π ≈ 3,14. Svar i meter.",
                "answer": float(ans),
                "tolerance": 0.05,
                "unit": "m",
                "hint": "Omkrets (sirkel) = 2πr",
            }
        # level 3+
        a_cm = rnd.choice([120, 150, 180, 220, 260])
        b_cm = rnd.choice([80, 90, 100, 110, 140])
        ans = 2 * ((a_cm + b_cm) / 100)
        return {
            "prompt": f"Finn omkretsen av et rektangel: {a_cm} cm og {b_cm} cm. Svar i meter.",
            "answer": float(ans),
            "tolerance": 0.02,
            "unit": "m",
            "hint": "Konverter cm → m først, så 2(a+b).",
        }

    if topic == "Volum":
        if level == 1:
            l = rnd.randint(2, 8)
            w = rnd.randint(2, 6)
            t_mm = rnd.choice([80, 100, 120, 150, 200])
            ans = l * w * (t_mm / 1000)
            return {
                "prompt": f"Betongplate: {l} m × {w} m med tykkelse {t_mm} mm. Finn volum i m³.",
                "answer": float(ans),
                "tolerance": 0.02,
                "unit": "m³",
                "hint": "mm → m: del på 1000. Volum = l × b × t",
            }
        if level == 2:
            d_mm = rnd.choice([200, 250, 300, 350, 400])
            h = rnd.choice([2.0, 2.4, 2.8, 3.0])
            r = (d_mm / 1000) / 2
            ans = math.pi * (r ** 2) * h
            return {
                "prompt": f"Søyle (sylinder): diameter {d_mm} mm og høyde {h} m. Finn volum i m³.",
                "answer": float(ans),
                "tolerance": 0.03,
                "unit": "m³",
                "hint": "Volum sylinder = π r² h (r = diameter/2)",
            }
        # level 3+
        l = rnd.randint(8, 25)
        w = rnd.choice([0.3, 0.4, 0.5])
        h_mm = rnd.choice([300, 400, 500, 600])
        ans = l * w * (h_mm / 1000)
        return {
            "prompt": f"Stripefundament: lengde {l} m, bredde {w} m, høyde {h_mm} mm. Finn volum i m³.",
            "answer": float(ans),
            "tolerance": 0.05,
            "unit": "m³",
            "hint": "Volum = lengde × bredde × høyde (mm → m)",
        }

    if topic == "Målestokk":
        if level == 1:
            drawing_cm = rnd.choice([2.5, 3.0, 4.2, 5.6, 7.5, 10.0])
            n = rnd.choice([20, 25, 50, 75, 100])
            real_cm = drawing_cm * n
            real_m = real_cm / 100
            return {
                "prompt": f"Tegning → virkelighet: {drawing_cm} cm på tegning i målestokk 1:{n}. Hva er virkelig lengde i meter?",
                "answer": float(real_m),
                "tolerance": 0.02,
                "unit": "m",
                "hint": "Virkelig = tegning × n. Konverter cm → m.",
            }
        if level == 2:
            real_m = rnd.choice([3.6, 4.8, 6.0, 7.2, 9.0])
            n = rnd.choice([20, 25, 50, 75, 100])
            drawing_m = real_m / n
            drawing_mm = drawing_m * 1000
            return {
                "prompt": f"Virkelighet → tegning: {real_m} m i målestokk 1:{n}. Hva blir tegningen i mm?",
                "answer": float(drawing_mm),
                "tolerance": 1.0,
                "unit": "mm",
                "hint": "Tegning = virkelighet / n. Konverter m → mm.",
            }
        # level 3+
        drawing_mm = rnd.choice([35, 48, 62, 80, 95, 120])
        n = rnd.choice([10, 20, 25, 50, 75, 100])
        real_mm = drawing_mm * n
        real_m = real_mm / 1000
        return {
            "prompt": f"Tegning → virkelighet: {drawing_mm} mm på tegning i målestokk 1:{n}. Hva er virkelig lengde i meter?",
            "answer": float(real_m),
            "tolerance": 0.02,
            "unit": "m",
            "hint": "Virkelig (mm) = tegning (mm) × n. Konverter mm → m.",
        }

    if topic == "Prosent":
        if level == 1:
            pct = rnd.choice([5, 10, 12.5, 15, 20, 25])
            base = rnd.choice([240, 360, 480, 800, 1200, 1800])
            ans = base * (pct / 100)
            return {
                "prompt": f"Finn {pct}% av {base}.",
                "answer": float(ans),
                "tolerance": 0.5,
                "unit": "",
                "hint": "Prosent av = tall × (p/100)",
            }
        if level == 2:
            part = rnd.choice([120, 240, 300, 450, 600])
            whole = rnd.choice([800, 1200, 1500, 1800, 2000])
            ans = (part / whole) * 100
            return {
                "prompt": f"Hvor mange prosent er {part} av {whole}? Svar i prosent.",
                "answer": float(ans),
                "tolerance": 0.5,
                "unit": "%",
                "hint": "Prosent = (del/helhet) × 100",
            }
        # level 3+
        base = rnd.choice([500, 800, 1200, 1500, 2000])
        rabatt = rnd.choice([10, 15, 20, 25])
        mva = 25
        after = base * (1 - rabatt / 100)
        inc = after * (1 + mva / 100)
        return {
            "prompt": f"En vare koster {base} kr. Du får {rabatt}% rabatt og legger på {mva}% MVA. Hva blir sluttprisen?",
            "answer": float(inc),
            "tolerance": 2.0,
            "unit": "kr",
            "hint": "Først rabatt, så MVA: pris × (1-r/100) × (1+m/100)",
        }

    # fallback
    a = rnd.randint(2, 10)
    b = rnd.randint(2, 10)
    return {
        "prompt": f"Regn ut {a} × {b}.",
        "answer": float(a * b),
        "tolerance": 0.01,
        "unit": "",
        "hint": "Gange",
    }


def _start_level(topic: str, level: int):
    st.session_state.play_state = {
        "topic": topic,
        "level": int(level),
        "q_index": 1,
        "correct_in_level": 0,
        "current": _make_question(topic, int(level), 1),
        "last_feedback": None,
    }


def _check_answer(user_answer: float, correct: float, tol: float) -> bool:
    if user_answer is None:
        return False
    try:
        return abs(float(user_answer) - float(correct)) <= float(tol)
    except Exception:
        return False


def show_play_screen():
    if not is_school_mode():
        st.warning("'Lek og lær' er kun tilgjengelig i Skolemodus.")
        return

    st.subheader("🎯 Lek og lær")
    st.caption("Nivåbaserte oppgaver i praktisk matematikk. For å gå videre må du få nok riktige svar på hvert nivå.")

    topics = ["Areal", "Omkrets", "Volum", "Målestokk", "Prosent"]

    top_left, top_right = st.columns([2, 1])
    with top_left:
        topic = st.selectbox("Velg tema", topics, key="play_topic")
    with top_right:
        if st.button("🔄 Nullstill progresjon", key="play_reset"):
            st.session_state.play_progress = {}
            st.session_state.play_state = {}
            st.toast("Progresjon nullstilt.")
            st.rerun()

    prog = _get_progress(topic)
    unlocked = int(prog.get("unlocked", 1))

    st.markdown("### Velg nivå")
    level_cols = st.columns(6)
    max_levels = 6

    chosen_level = None
    for lvl in range(1, max_levels + 1):
        is_locked = lvl > unlocked
        label = f"Nivå {lvl}" if not is_locked else f"🔒 Nivå {lvl}"
        with level_cols[(lvl - 1) % 6]:
            if st.button(label, key=f"play_lvl_{topic}_{lvl}", disabled=is_locked, use_container_width=True):
                chosen_level = lvl

    # Start nivå ved klikk
    if chosen_level is not None:
        _start_level(topic, chosen_level)
        st.rerun()

    state = st.session_state.get("play_state", {})
    if state.get("topic") != topic:
        # Bytte tema: ikke vis "gammel" oppgave
        return

    if not state:
        st.info("Velg et nivå for å starte.")
        return

    level = int(state.get("level", 1))
    q = state.get("current") or _make_question(topic, level, int(state.get("q_index", 1)))

    # Progresjon i nivå
    correct_now = int(state.get("correct_in_level", 0))
    st.progress(min(correct_now / _PLAY_CORRECT_TO_PASS, 1.0))
    st.caption(f"Riktige i dette nivået: {correct_now}/{_PLAY_CORRECT_TO_PASS}")

    st.markdown("### Oppgave")
    st.write(q.get("prompt", ""))

    with st.expander("Hint", expanded=False):
        st.write(q.get("hint", ""))

    ans_label = "Svar" + (f" ({q.get('unit')})" if q.get("unit") else "")
    user_ans = st.number_input(ans_label, value=0.0, step=0.1, key=f"play_answer_{topic}_{level}")

    b1, b2, b3 = st.columns([1.2, 1.2, 2])
    with b1:
        if st.button("✅ Sjekk svar", key="play_check", use_container_width=True):
            ok = _check_answer(user_ans, q.get("answer", 0.0), q.get("tolerance", 0.01))
            if ok:
                state["correct_in_level"] = correct_now + 1
                state["last_feedback"] = (True, f"Riktig. God kontroll.")

                # Ferdig med nivå?
                if state["correct_in_level"] >= _PLAY_CORRECT_TO_PASS:
                    _set_completed(topic, level)
                    state["last_feedback"] = (True, f"Nivå {level} bestått. Neste nivå er låst opp.")
                else:
                    # Neste oppgave i samme nivå
                    state["q_index"] = int(state.get("q_index", 1)) + 1
                    state["current"] = _make_question(topic, level, int(state["q_index"]))

            else:
                corr = float(q.get("answer", 0.0))
                unit = q.get("unit", "")
                state["last_feedback"] = (False, f"Ikke helt. Fasit er omtrent {corr:.3f} {unit}. Prøv en ny oppgave eller bruk hint.")

            st.session_state.play_state = state
            st.rerun()

    with b2:
        if st.button("➡️ Ny oppgave", key="play_new", use_container_width=True):
            state["q_index"] = int(state.get("q_index", 1)) + 1
            state["current"] = _make_question(topic, level, int(state["q_index"]))
            st.session_state.play_state = state
            st.rerun()

    with b3:
        if st.button("🏠 Tilbake til hovedsiden", key="play_back", use_container_width=True):
            st.session_state.show_play = False
            st.session_state.play_state = {}
            st.rerun()

    fb = state.get("last_feedback")
    if fb:
        ok, msg = fb
        if ok:
            st.success(msg)
        else:
            st.warning(msg)


def show_result(res: CalcResult):
    school = is_school_mode()

    col1, col2 = st.columns([1.1, 1])

    with col1:
        st.subheader("Resultat")

        # I skolemodus: kort læringshint øverst
        if school:
            st.info("Tips: Sjekk alltid enhet (mm/cm/m) og om svaret virker realistisk.")

        # Målestokk: profesjonell metric-visning for begge retninger
        if res.name.startswith("Målestokk"):
            o = res.outputs

            if "virkelig_mm" in o:
                c1, c2, c3 = st.columns(3)
                c1.metric("Virkelig mål (mm)", format_value("virkelig_mm", o.get("virkelig_mm", 0)))
                c2.metric("Virkelig mål (cm)", format_value("virkelig_cm", o.get("virkelig_cm", 0)))
                c3.metric("Virkelig mål (m)", format_value("virkelig_m", o.get("virkelig_m", 0)))

            if "tegning_mm" in o:
                c1, c2, c3 = st.columns(3)
                c1.metric("Tegningsmål (mm)", format_value("tegning_mm", o.get("tegning_mm", 0)))
                c2.metric("Tegningsmål (cm)", format_value("tegning_cm", o.get("tegning_cm", 0)))
                c3.metric("Tegningsmål (m)", format_value("tegning_m", o.get("tegning_m", 0)))

        # Kledning: profesjonell metric-visning
        elif res.name.startswith("Tømmermannskledning"):
            o = res.outputs
            r1c1, r1c2, r1c3 = st.columns(3)
            r1c1.metric("Underliggere", str(o.get("underliggere_antall", "")))
            r1c2.metric("Overliggere", str(o.get("overliggere_antall", "")))
            r1c3.metric("Overligger OK", str(o.get("overligger_ok_for_omlegg", "")))

            r2c1, r2c2, r2c3 = st.columns(3)
            r2c1.metric("Dekket bredde (mm)", format_value("dekket_bredde_mm", o.get("dekket_bredde_mm", 0)))
            r2c2.metric("Overdekning (mm)", format_value("overdekning_mm", o.get("overdekning_mm", 0)))
            r2c3.metric(
                "Min overliggerbredde (mm)",
                format_value("min_overligger_bredde_mm", o.get("min_overligger_bredde_mm", 0)),
            )

        # Standard: labels uten understreker
        else:
            for k, v in res.outputs.items():
                st.write(f"**{label_for(k)}**: {format_value(k, v)}")

        # Varsler: skole vs produksjon
        if res.warnings:
            if school:
                st.warning("Sjekk dette:\n- " + "\n- ".join(res.warnings))
                st.caption("I skolemodus er varsler laget for å støtte kontroll og enhetsforståelse.")
            else:
                st.error("Kontroller før bruk i produksjon:\n- " + "\n- ".join(res.warnings))
        else:
            st.success("Ingen varsler.")

        # Skolemodus: refleksjonsspørsmål (valgfritt, men nyttig)
        if school:
            with st.expander("Refleksjon (for læring)", expanded=False):
                st.write("1) Hvilke enheter brukte du, og hvorfor?")
                st.write("2) Virker svaret realistisk? Hvordan kan du grovsjekke?")
                st.write("3) Hva er en typisk feil her (mm vs m, prosent vs 1:x osv.)?")

        # Historikk
        if st.button("Lagre i historikk", type="primary"):
            st.session_state.history.append(
                {
                    "tid": res.timestamp,
                    "kalkulator": res.name,
                    "modus": "Skole" if school else "Produksjon",
                    "inputs": res.inputs,
                    "outputs": res.outputs,
                    "warnings": res.warnings,
                }
            )
            st.toast("Lagret.")

    with col2:
        st.subheader("Utregning (valgfritt)")

        # Nøkkel: mellomregning åpen i skolemodus, lukket i produksjon
        with st.expander("Vis mellomregning", expanded=school):
            for s in res.steps:
                st.write(f"- {s}")


# ============================================================
# App-state
# ============================================================
if "history" not in st.session_state:
    st.session_state.history: List[Dict[str, Any]] = []


# ------------------------------------------------------------
# UI-state (må være definert før topmenyen bruker dem)
# ------------------------------------------------------------
if "show_pro" not in st.session_state:
    st.session_state.show_pro = False

if "show_ai" not in st.session_state:
    st.session_state.show_ai = False

if "show_play" not in st.session_state:
    st.session_state.show_play = False

# Lek og lær progresjon
if "play_progress" not in st.session_state:
    st.session_state.play_progress = {}

# Aktiv oppgave i Lek og lær
if "play_state" not in st.session_state:
    st.session_state.play_state = {}


# ============================================================
# Topmeny: Hjem + Lek og lær + AI-robot + Innstillinger
# ============================================================

# Trekker topmenyen tett opp mot headeren (komprimert, men uten å skjule logo/tekst)
st.markdown("<div style='margin-top:-18px;'></div>", unsafe_allow_html=True)

bar1, bar2, bar3, bar4 = st.columns([1.2, 1.4, 1.4, 1.8])

with bar1:
    if st.button("🏠 Hjem", key="btn_home_top", use_container_width=True):
        st.session_state.show_ai = False
        st.session_state.show_pro = False
        st.session_state.show_play = False
        st.rerun()

with bar2:
    # Lek og lær er kun tilgjengelig i skolemodus
    play_disabled = not is_school_mode()
    if st.button("🎯 Lek og lær", key="btn_play_top", use_container_width=True, disabled=play_disabled):
        st.session_state.show_play = True
        st.session_state.show_ai = False
        st.session_state.show_pro = False
        st.rerun()

with bar3:
    if st.button("🤖 AI-robot", key="btn_ai_top", use_container_width=True):
        st.session_state.show_ai = True
        st.session_state.show_pro = False
        st.session_state.show_play = False
        st.rerun()

with bar4:
    with st.popover("⚙️ Innstillinger", use_container_width=True):
        st.subheader("Innstillinger")
        st.session_state.app_mode = st.radio(
            "Modus",
            ["Skole", "Produksjon"],
            index=0 if st.session_state.get("app_mode", "Skole") == "Skole" else 1,
            key="app_mode_settings",
        )
        if st.session_state.app_mode == "Skole":
            st.info("Skolemodus er aktiv.")
        else:
            st.success("Produksjonsmodus er aktiv.")

        st.divider()
        st.markdown("**Oppgradering**")
        st.caption("Pro gir ekstra funksjoner for læring, dokumentasjon og eksport.")
        if st.button("⭐ Oppgrader til Pro", key="btn_pro_settings", use_container_width=True):
            st.session_state.show_pro = True
            st.session_state.show_ai = False
            st.session_state.show_play = False
            st.rerun()

st.divider()



# ============================================================
# Pro/AI/Lek og lær-visning
# ============================================================
if st.session_state.show_pro:
    st.divider()

    if st.button("🏠 Tilbake til hovedsiden", key="btn_home_from_pro"):
        st.session_state.show_pro = False
        st.session_state.show_play = False
        st.rerun()

    show_pro_screen()
    st.stop()

if st.session_state.get("show_ai", False):
    st.divider()
    st.subheader("🤖 Spør din verksmester!")
    st.caption("Skriv både tekst og regnestykker. Eksempel: 'areal 4 x 6' eller '2*(3+5)'.")

    q = st.text_input("Spør AI-roboten", key="ai_input_top")
    if q:
        res = ai_math_bot(q)
        if res["ok"]:
            st.success(res["answer"])
            with st.expander("Vis forklaring", expanded=is_school_mode()):
                for s in res["steps"]:
                    st.write(f"- {s}")
        else:
            st.warning(res["answer"])

    if st.button("Lukk AI-robot"):
        st.session_state.show_ai = False
        st.session_state.show_play = False
        st.rerun()

    st.stop()

if st.session_state.get("show_play", False):
    st.divider()
    show_play_screen()
    st.stop()

st.markdown("<div style='margin-top:-10px;'></div>", unsafe_allow_html=True)

# ============================================================
# Tabs
# ============================================================
tabs = st.tabs(
    [
        "📏 Enhetomregner",
        "⬛ Areal",
        "🧵 Omkrets",
        "🧱 Volum",
        "📐 Målestokk",
        "🪵 Beregninger",
        "📉 Fall",
        "🧮 Prosent",
        "📐 Diagonal (Pytagoras)",
        "💰 Økonomi",
        "📊 Historikk",
    ]
)

# ---- Enhetsomregner ----
with tabs[0]:
    st.subheader("Enhetsomregner")
    st.caption("I byggfag brukes måleenheter som millimeter (mm), centimeter (cm) og meter (m). For å regne riktig må alle mål ofte være i samme enhet. Skriv inn et tall, velg enhet, og få omregning til mm, cm og m i tabell.")

    c1, c2 = st.columns([2, 1])

    with c1:
        value = st.number_input("Verdi", min_value=0.0, value=1000.0, step=1.0, key="unit_value")

    with c2:
        unit_in = st.selectbox("Enhet", options=["mm", "cm", "m"], index=0, key="unit_in")

    # Konverter inndata til mm -> derfra til alle enheter
    mm_value = to_mm(float(value), str(unit_in))
    conv = mm_to_all(mm_value)

    # Bygg tabell (mm, cm, m)
    df_units = pd.DataFrame(
        [
            {"Enhet": "mm", "Verdi": round_sensible(conv["mm"], 1)},
            {"Enhet": "cm", "Verdi": round_sensible(conv["cm"], 2)},
            {"Enhet": "m",  "Verdi": round_sensible(conv["m"], 3)},
        ]
    )

    st.dataframe(df_units, use_container_width=True, hide_index=True)

    # Valgfritt: små "metric"-bokser i tillegg (kan fjernes)
    m1, m2, m3 = st.columns(3)
    m1.metric("mm", f'{round_sensible(conv["mm"], 1)}')
    m2.metric("cm", f'{round_sensible(conv["cm"], 2)}')
    m3.metric("m",  f'{round_sensible(conv["m"], 3)}')


# ---- Areal ----
with tabs[1]:
    if is_school_mode():
        st.caption("Areal forteller hvor stor en flate er. I bygg brukes areal for å finne hvor mye gulv, vegg, isolasjon eller kledning som trengs. Tenk: areal = lengde × bredde. Sjekk alltid at begge mål er i meter.")

    st.subheader("Areal (rektangel)")
    l = st.number_input("Lengde (m)", min_value=0.0, value=5.0, step=0.1, key="areal_l")
    w = st.number_input("Bredde (m)", min_value=0.0, value=4.0, step=0.1, key="areal_w")
    if st.button("Beregn areal", key="btn_areal"):
        show_result(calc_area_rectangle(l, w))

    st.divider()
    st.subheader("Areal + svinn")
    area = st.number_input("Areal (m²)", min_value=0.0, value=20.0, step=0.1, key="svinn_area")
    waste = st.number_input("Svinn (%)", min_value=0.0, value=10.0, step=1.0, key="svinn_pct")
    if st.button("Beregn bestillingsareal", key="btn_svinn"):
        show_result(calc_area_with_waste(area, waste))

    st.divider()
    st.subheader("Areal (sammensatt av rektangler)")
    st.caption("Legg inn delmål og summer dem.")
    n = st.number_input("Antall deler", min_value=1, max_value=20, value=3, step=1, key="comp_n")
    rects = []
    for i in range(int(n)):
        c1, c2 = st.columns(2)
        with c1:
            li = st.number_input(
                f"Del {i+1} lengde (m)",
                min_value=0.0,
                value=2.0,
                step=0.1,
                key=f"comp_l_{i}",
            )
        with c2:
            wi = st.number_input(
                f"Del {i+1} bredde (m)",
                min_value=0.0,
                value=1.5,
                step=0.1,
                key=f"comp_w_{i}",
            )
        rects.append((li, wi))

    if st.button("Beregn sammensatt areal", key="btn_comp"):
        show_result(calc_area_composite(rects))

# ---- Omkrets ----
with tabs[2]:
    if is_school_mode():
        st.caption("Omkrets er lengden rundt en figur. I bygg brukes omkrets blant annet for å finne lengde på lister, sviller eller fundament. Rektangel: 2(a+b). Sirkel: 2πr.")

    st.subheader("🧵 Omkrets")
    shape = st.selectbox("Velg figur", ["Rektangel", "Sirkel"], key="per_shape")

    unit = st.selectbox("Enhet for inndata", ["mm", "cm", "m"], index=2, key="per_unit")

    if shape == "Rektangel":
        c1, c2 = st.columns(2)
        with c1:
            a = st.number_input("Side a", min_value=0.0, value=2.0, step=0.1, key="per_a")
        with c2:
            b = st.number_input("Side b", min_value=0.0, value=1.0, step=0.1, key="per_b")

        a_m = to_mm(float(a), unit) / 1000.0
        b_m = to_mm(float(b), unit) / 1000.0

        if st.button("Beregn omkrets", key="btn_per_rect"):
            show_result(calc_perimeter("Rektangel", a_m=a_m, b_m=b_m))

    else:
        r = st.number_input("Radius", min_value=0.0, value=0.5, step=0.1, key="per_r")
        r_m = to_mm(float(r), unit) / 1000.0

        if st.button("Beregn omkrets", key="btn_per_circ"):
            show_result(calc_perimeter("Sirkel", r_m=r_m))


# ---- Volum/betong ----
with tabs[3]:
    if is_school_mode():
        st.caption("Volum sier hvor mye noe rommer. I bygg brukes volum særlig når man skal beregne mengde betong, masser eller fyll. Volum beregnes i m³. Tykkelser oppgis ofte i mm og må konverteres til meter.")

    st.subheader("Betongplate")
    l = st.number_input("Lengde (m)", min_value=0.0, value=6.0, step=0.1, key="slab_l")
    w = st.number_input("Bredde (m)", min_value=0.0, value=4.0, step=0.1, key="slab_w")
    t = st.number_input("Tykkelse (mm)", min_value=0.0, value=100.0, step=5.0, key="slab_t")
    if st.button("Beregn volum (plate)", key="btn_slab"):
        show_result(calc_concrete_slab(l, w, t))

    st.divider()
    st.subheader("Stripefundament")
    l = st.number_input("Lengde (m)", min_value=0.0, value=20.0, step=0.1, key="strip_l")
    w = st.number_input("Bredde (m)", min_value=0.0, value=0.4, step=0.05, key="strip_w")
    h = st.number_input("Høyde (mm)", min_value=0.0, value=400.0, step=10.0, key="strip_h")
    if st.button("Beregn volum (stripefundament)", key="btn_strip"):
        show_result(calc_strip_foundation(l, w, h))

    st.divider()
    st.subheader("Søyle (sylinder)")
    d = st.number_input("Diameter (mm)", min_value=0.0, value=300.0, step=10.0, key="col_d")
    hm = st.number_input("Høyde (m)", min_value=0.0, value=3.0, step=0.1, key="col_h")
    if st.button("Beregn volum (søyle)", key="btn_col"):
        show_result(calc_column_cylinder(d, hm))

# ---- Målestokk (begge veier + 1–100) ----
with tabs[4]:
    if is_school_mode():
        st.caption("Målestokk viser forholdet mellom en tegning og virkeligheten. En målestokk på 1:50 betyr at 1 cm på tegningen er 50 cm i virkeligheten.")

    st.subheader("Målestokk")

    direction = st.radio(
        "Velg retning",
        options=["Tegning → virkelighet", "Virkelighet → tegning"],
        horizontal=True,
        key="scale_direction",
    )

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        if direction == "Tegning → virkelighet":
            val = st.number_input("Mål på tegning", min_value=0.0, value=50.0, step=1.0, key="scale_val")
        else:
            val = st.number_input("Virkelig mål", min_value=0.0, value=600.0, step=1.0, key="scale_val")

    with c2:
        unit = st.selectbox("Enhet", options=["mm", "cm", "m"], index=0, key="scale_unit")

    with c3:
        scale_n = st.number_input("Målestokk (1:n)", min_value=1, max_value=100, value=50, step=1, key="scale_n")

    if st.button("Beregn målestokk", key="btn_scale_bidir"):
        show_result(calc_scale_bidir(float(val), str(unit), int(scale_n), str(direction)))

# ---- Kledning ----
with tabs[5]:
    st.subheader("Tømmermannskledning (kun bredde)")
    st.caption("Når du kler en vegg, må du vite hvor mange bord som trengs, og om bordene dekker hele bredden riktig. Fritt innskrive: mål fra–til (cm), omlegg (cm) og bordbredder (mm).")

    c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
    with c1:
        measure_cm = st.number_input("Mål fra–til (cm)", min_value=0.0, value=600.0, step=1.0, key="tk_measure_cm")
    with c2:
        overlap_cm = st.number_input("Ønsket omlegg (cm)", min_value=0.0, value=2.0, step=0.1, key="tk_overlap_cm")
    with c3:
        under_w = st.number_input("Underligger bredde (mm)", min_value=1.0, value=148.0, step=1.0, key="tk_under_w")
    with c4:
        over_w = st.number_input("Overligger bredde (mm)", min_value=1.0, value=58.0, step=1.0, key="tk_over_w")

    if st.button("Beregn kledning", key="btn_tk"):
        show_result(calc_tommermannskledning_width(float(measure_cm), float(overlap_cm), float(under_w), float(over_w)))

    st.divider()
    st.subheader("Fliser")
    if is_school_mode():
        st.caption("Du regner antall fliser ved å bruke modulmål: (flis + fuge). Antall = ceil(vegg / modul).")

    left, right = st.columns([2.2, 1.3], gap="large")

    with left:
        st.markdown("### Flisstørrelse")
        c1, c2, c3, c4 = st.columns([1.2, 1, 1.2, 1])
        with c1:
            tile_h = st.number_input("Høyde", min_value=0.0, value=15.0, step=1.0, key="tile_h")
        with c2:
            tile_h_unit = st.selectbox(" ", ["mm", "cm", "m"], index=1, key="tile_h_unit")
        with c3:
            tile_w = st.number_input("Bredde", min_value=0.0, value=10.0, step=1.0, key="tile_w")
        with c4:
            tile_w_unit = st.selectbox("  ", ["mm", "cm", "m"], index=1, key="tile_w_unit")

        st.markdown("### Flisfugeavstand")
        c5, c6 = st.columns([1.2, 1])
        with c5:
            grout = st.number_input("Fuge", min_value=0.0, value=2.0, step=0.5, key="tile_grout")
        with c6:
            grout_unit = st.selectbox("   ", ["mm", "cm", "m"], index=1, key="tile_grout_unit")

        st.markdown("### Mål på overflaten som skal flislegges")
        method = st.selectbox("Metode", ["Angi dimensjoner"], index=0, key="tile_method")

        c7, c8 = st.columns([1.2, 1])
        with c7:
            wall_h = st.number_input("Høyde (vegg)", min_value=0.0, value=2.4, step=0.1, key="wall_h")
        with c8:
            wall_h_unit = st.selectbox("    ", ["mm", "cm", "m"], index=2, key="wall_h_unit")

        c9, c10 = st.columns([1.2, 1])
        with c9:
            wall_w = st.number_input("Bredde (vegg)", min_value=0.0, value=3.0, step=0.1, key="wall_w")
        with c10:
            wall_w_unit = st.selectbox("     ", ["mm", "cm", "m"], index=2, key="wall_w_unit")

        st.markdown("### Pris (valgfritt)")
        st.caption("Angi pris per flis for å beregne totalpris.")
        c11, c12 = st.columns([1.2, 1])
        with c11:
            price_per_tile = st.number_input("Pris per flis", min_value=0.0, value=0.0, step=1.0, key="tile_price")
        with c12:
            st.write("NOK")

        calc_now = st.button("Beregn fliser", key="btn_tiles", use_container_width=True)

    with right:
        st.markdown("### Resultat")
        add10 = st.checkbox(
            "Legg til 10 % ekstra fliser (i tilfelle kutting, problemer eller fremtidige bytter).",
            value=True,
            key="tile_add10",
        )

        # Når bruker klikker "Beregn fliser"
        if calc_now:
            res = calc_tiles_wall(
                tile_h=tile_h, tile_h_unit=tile_h_unit,
                tile_w=tile_w, tile_w_unit=tile_w_unit,
                grout=grout, grout_unit=grout_unit,
                wall_h=wall_h, wall_h_unit=wall_h_unit,
                wall_w=wall_w, wall_w_unit=wall_w_unit,
                add_10_percent=add10,
                price_per_tile=price_per_tile,
            )

            # Vis “likt bildet”: felt for antall + totalpris
            o = res.outputs
            st.text_input("Trenger fliser:", value=str(o.get("trenger_fliser", 0)), disabled=True, key="tiles_out_count")

            # Totalpris
            totalpris = o.get("totalpris", 0.0)
            st.text_input("Totalpris", value=f"{totalpris:.2f}", disabled=True, key="tiles_out_price")
            st.write("NOK")

            # Skolemodus: vis utregning
            with st.expander("Vis utregning", expanded=is_school_mode()):
                for s in res.steps:
                    st.write(f"- {s}")

            if res.warnings:
                st.warning("Sjekk dette:\n- " + "\n- ".join(res.warnings))


# ---- Fall/vinkel ----
with tabs[6]:
    st.write("DEBUG: Fall/vinkel-fanen kjører.")  # skal vises uansett

    if is_school_mode():
        st.caption("Fall brukes for å sikre at vann renner riktig vei, for eksempel på bad, terrasse eller tak. Fall kan angis i prosent, 1:x eller mm per meter.")

    st.subheader("Fallberegning")
    length = st.number_input("Lengde (m)", min_value=0.0, value=2.0, step=0.1, key="fall_len")
    mode = st.selectbox("Angi fall som", options=["prosent", "1:x", "mm_per_m"], index=0, key="fall_mode")

    if mode == "prosent":
        val = st.number_input("Fall (%)", min_value=0.0, value=2.0, step=0.1, key="fall_val_pct")
    elif mode == "1:x":
        val = st.number_input("x i 1:x", min_value=1.0, value=50.0, step=1.0, key="fall_val_ratio")
    else:
        val = st.number_input("mm per meter", min_value=0.0, value=20.0, step=1.0, key="fall_val_mm")

    if st.button("Beregn fall", key="btn_fall"):
        show_result(calc_fall(length, mode, float(val)))


# ---- Økonomi ----

with tabs[7]:
    st.subheader("🧮 Prosent")
    st.caption("Prosent brukes for å vise en del av en helhet. I bygg brukes prosent blant annet til svinn, rabatt, påslag og MVA. Regn ut prosent av et tall, eller finn hvor mange prosent et tall er av et annet.")

    mode = st.radio(
        "Velg type",
        ["Prosent av et tall", "Hvor mange prosent?"],
        horizontal=True,
        key="pct_mode",
    )

    if mode == "Prosent av et tall":
        c1, c2 = st.columns(2)
        with c1:
            pct = st.number_input("Prosent (%)", min_value=0.0, value=25.0, step=0.5, key="pct_a")
        with c2:
            base = st.number_input("Av tallet", min_value=0.0, value=1800.0, step=10.0, key="pct_b")

        if st.button("Beregn", key="btn_pct_of"):
            res = base * (pct / 100.0)
            steps = [f"{pct}% av {base} = {base} × ({pct}/100) = {res}"]
            show_result(CalcResult(
                name="Prosent (av et tall)",
                inputs={"prosent": pct, "av": base},
                outputs={"resultat": round_sensible(res, 2)},
                steps=steps,
                warnings=[],
                timestamp=make_timestamp(),
            ))

    else:
        c1, c2 = st.columns(2)
        with c1:
            part = st.number_input("Del", min_value=0.0, value=450.0, step=10.0, key="pct_part")
        with c2:
            whole = st.number_input("Av (total)", min_value=0.0, value=1800.0, step=10.0, key="pct_whole")

        if st.button("Beregn", key="btn_pct_how"):
            pct = (part / whole * 100.0) if whole else 0.0
            steps = [f"Prosent = (del / total) × 100 = ({part}/{whole}) × 100 = {pct}"]
            show_result(CalcResult(
                name="Prosent (hvor mange prosent)",
                inputs={"del": part, "total": whole},
                outputs={"prosent": round_sensible(pct, 2)},
                steps=steps,
                warnings=[],
                timestamp=make_timestamp(),
            ))




# ---- Diagonal (Pytagoras) ----
# ---- Diagonal (Pytagoras) ----
with tabs[8]:
    if is_school_mode():
        st.caption("Pytagoras brukes i rettvinklede trekanter: c = √(a² + b²). Sjekk alltid enhet før du regner.")

    st.subheader("Diagonal (Pytagoras)")

    unit = st.selectbox("Enhet for inndata", ["mm", "cm", "m"], index=2, key="pyt_unit")

    c1, c2 = st.columns(2)
    with c1:
        a = st.number_input("Side a", min_value=0.0, value=3000.0 if unit == "mm" else (300.0 if unit == "cm" else 3.0),
                            step=1.0 if unit != "m" else 0.1, key="pyt_a_any")
    with c2:
        b = st.number_input("Side b", min_value=0.0, value=4000.0 if unit == "mm" else (400.0 if unit == "cm" else 4.0),
                            step=1.0 if unit != "m" else 0.1, key="pyt_b_any")

    # Konverter til meter før beregning
    a_m = to_mm(float(a), unit) / 1000.0
    b_m = to_mm(float(b), unit) / 1000.0

    if st.button("Beregn diagonal", key="btn_pyt_any"):
        show_result(calc_pythagoras(a_m, b_m))

# ---- Økonomi ----
with tabs[9]:
    st.subheader('💰 Økonomi')
    if is_school_mode():
        st.caption('I byggfag må du kunne regne ut priser, rabatter, påslag og merverdiavgift (MVA). Brukes til enkel prisregning: rabatt, påslag og MVA. Pass på prosent og rekkefølge.')

    st.markdown('### Pris (rabatt / påslag / MVA)')
    base = st.number_input('Grunnpris', min_value=0.0, value=1000.0, step=10.0, key='price_base')
    rabatt = st.number_input('Rabatt (%)', min_value=0.0, value=0.0, step=1.0, key='price_rabatt')
    paslag = st.number_input('Påslag (%)', min_value=0.0, value=0.0, step=1.0, key='price_paslag')
    mva = st.number_input('MVA (%)', min_value=0.0, value=25.0, step=1.0, key='price_mva')
    if st.button('Beregn pris', key='btn_price'):
        show_result(calc_price(base, rabatt, paslag, mva))

    st.divider()
    st.markdown('### Tidsestimat')
    q = st.number_input('Mengde', min_value=0.0, value=10.0, step=1.0, key='time_qty')
    prod = st.number_input('Produksjon per time', min_value=0.0, value=2.0, step=0.1, key='time_prod')
    if st.button('Beregn tid', key='btn_time'):
        show_result(calc_time_estimate(q, prod))
        
# ---- Historikk ----
with tabs[10]:
    st.subheader("Historikk")

    if not st.session_state.history:
        st.info("Ingen beregninger lagret ennå.")
    else:
        rows = []
        for item in st.session_state.history:
            outputs_pretty = {label_for(k): v for k, v in item["outputs"].items()}
            rows.append(
                {
                    "tid": item["tid"],
                    "kalkulator": item["kalkulator"],
                    "inputs": str(item["inputs"]),
                    "outputs": str(outputs_pretty),
                    "varsler": "; ".join(item["warnings"]) if item["warnings"] else "",
                }
            )
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Last ned historikk (CSV)",
            data=csv,
            file_name="bygg_kalkulator_historikk.csv",
            mime="text/csv",
        )

        if st.button("Tøm historikk"):
            st.session_state.history = []
            st.success("Historikk tømt.")

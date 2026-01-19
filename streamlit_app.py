import math
import time
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image


# ============================================================
# Konfig + Logo (må ligge før all annen Streamlit-output)
# ============================================================
LOGO_PATH = Path(__file__).parent / "logo1.png"

page_icon = None
if LOGO_PATH.exists():
    try:
        page_icon = Image.open(LOGO_PATH)
    except Exception:
        page_icon = None

st.set_page_config(
    page_title="Bygg-kalkulatoren",
    page_icon=page_icon,
    layout="wide",
)
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

with st.sidebar:
    st.header("Innstillinger")

    st.session_state.app_mode = st.radio(
        "Modus",
        ["Skole", "Produksjon"],
        index=0 if st.session_state.app_mode == "Skole" else 1,
        help="Skole: mer forklaring og mellomregning. Produksjon: raskt resultat og mindre støy.",
    )

    st.divider()

    pro_btn_text = "📘 Hva er Pro? (skole)" if st.session_state.app_mode == "Skole" else "🛠️ Pro-verktøy"
    if st.button(pro_btn_text):
        st.session_state.show_pro = True


        "Modus",
        options=["Skole", "Produksjon"],
        index=0 if st.session_state.app_mode == "Skole" else 1,
        help="Skole: mer forklaring og mellomregning. Produksjon: raskt resultat og mindre støy.",
    )

def is_school_mode() -> bool:
    return st.session_state.get("app_mode", "Skole") == "Skole"


# Profesjonell header med logo
if LOGO_PATH.exists():
    header_left, header_right = st.columns([1, 3])
    with header_left:
        st.image(str(LOGO_PATH), use_container_width=True)
    with header_right:
        st.title("Bygg-kalkulatoren")
        st.caption("din hjelper på farta!")
else:
    st.title("Bygg-kalkulatoren")
    st.caption("din hjelper på farta!")
    st.warning("Finner ikke logo.png i prosjektmappen. Legg logoen i samme mappe som app-filen.")


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
        name="Tømmermannskledning (bredde)",
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

    st.divider()

    st.markdown("### Gratis vs Pro")
    left, right = st.columns(2)
    with left:
        st.markdown("#### Gratis")
        st.write("• Alle grunnkalkulatorer")
        st.write("• Skole/Produksjon-modus (basis)")
        st.write("• Enkel historikk (begrenset)")
        st.write("• Ingen eksport")
    with right:
        st.markdown("#### Pro")
        st.write("• Utvidet historikk og filtrering")
        st.write("• Eksport (PDF/CSV)")
        if is_school:
            st.write("• Skjult fasit + refleksjon")
            st.write("• Oppgavebank (valgfritt)")
            st.write("• Lærer-/klassefunksjoner (valgfritt)")
        else:
            st.write("• Prosjektstruktur (prosjekt/rom)")
            st.write("• KS-notater / jobblogg")
            st.write("• Bransjeavrunding + kontrollpunkter")

    st.divider()

    st.markdown("### Pro-funksjoner i denne modusen")
    if is_school:
        st.write("**Måling/enheter**: Eksempeloppgaver, typiske feil, skjult fasit.")
        st.write("**Målestokk**: Oppgavemodus + kontrollspørsmål.")
        st.write("**Fall/vinkel/diagonal**: Estimat før fasit + forklaringsmodus.")
        st.write("**Historikk**: Eksport til PDF for innlevering.")
    else:
        st.write("**Måling/enheter**: Hurtigomregning + kopierbare resultater.")
        st.write("**Målestokk**: Rask skala begge veier, mindre støy.")
        st.write("**Fall/vinkel/diagonal**: Konvertering og kontrollpunkter for utførelse.")
        st.write("**Historikk**: Jobblogg + eksport til KS/bestilling.")

    st.divider()

    st.markdown("### Pris (forslag)")
    if is_school:
        st.write("• Lærer: 399 kr/år (forslag)")
        st.write("• Skolelisens: fra 3 000 kr/år (forslag)")
    else:
        st.write("• Enkeltbruker: 149 kr/mnd eller 1 490 kr/år (forslag)")
        st.write("• Firma (1–10): fra 4 990 kr/år (forslag)")

    st.info("Dette er forslag. Du kan endre prisene i teksten når du har bestemt modell.")


    # CTA-knapper (ikke betaling – bare UI)
    cta1, cta2, cta3 = st.columns(3)
    with cta1:
        st.button("Oppgrader til Pro (kommer)", disabled=True)
    with cta2:
        st.button("Kontakt / bestill lisens (kommer)", disabled=True)
    with cta3:
        st.button("Se hva Pro gir i historikk (kommer)", disabled=True)

    st.caption("Tips: Start med Pro-funksjonene som gir mest verdi: eksport + utvidet historikk.")


# ============================
# Integrasjon: legg "Bli en profesjonell yrkesutøver?" i sidepanelet
# ============================

# Sett default state
if "show_pro" not in st.session_state:
    st.session_state.show_pro = False

with st.sidebar:
    st.divider()
    if st.button("Oppgrader til Pro"):
        st.session_state.show_pro = True

# Vis Pro-skjerm øverst i appen når brukeren klikker
if st.session_state.get("show_pro", False):
    st.divider()
    show_pro_screen()
    if st.button("Lukk Pro-skjerm"):
        st.session_state.show_pro = False
    st.stop()


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


# ============================================================
# Tabs
# ============================================================
tabs = st.tabs(
    [
        "📏 Enhetomregner",
        "⬛ Areal",
        "🧵 Omkrets",
        "🧱 Volum/betong",
        "📐 Målestokk",
        "🪵 Kledning",
        "📉 Fall/vinkel",
        "🧮 Prosent",
        "📐 Diagonal (Pytagoras)",
        "💰 Økonomi",
        "⏱️ Tid",
        "⚠️ Avvik/KS",
        "📊 Historikk",
    ]
)

# ---- Enhetsomregner ----
with tabs[0]:
    st.subheader("Enhetsomregner")
    st.caption("Skriv inn et tall, velg enhet, og få omregning til mm, cm og m i tabell.")

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
        st.caption("Tenk: areal = lengde × bredde. Sjekk alltid at begge mål er i meter.")

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
        st.caption("Omkrets er lengden rundt en figur. Rektangel: 2(a+b). Sirkel: 2πr.")

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
        st.caption("Volum beregnes i m³. Tykkelser oppgis ofte i mm og må konverteres til meter.")

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
        st.caption("Husk: 1:50 betyr at 1 enhet på tegning tilsvarer 50 enheter i virkeligheten.")

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
    st.caption("Fritt innskrive: mål fra–til (cm), omlegg (cm) og bordbredder (mm).")

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

# ---- Fall/vinkel ----
with tabs[6]:
    st.write("DEBUG: Fall/vinkel-fanen kjører.")  # skal vises uansett

    if is_school_mode():
        st.caption("Fall kan angis i prosent, 1:x eller mm per meter.")

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
    st.subheader("Pris (rabatt/påslag/MVA)")
    base = st.number_input("Grunnpris", min_value=0.0, value=1000.0, step=10.0, key="price_base")
    rabatt = st.number_input("Rabatt (%)", min_value=0.0, value=0.0, step=1.0, key="price_rabatt")
    paslag = st.number_input("Påslag (%)", min_value=0.0, value=0.0, step=1.0, key="price_paslag")
    mva = st.number_input("MVA (%)", min_value=0.0, value=25.0, step=1.0, key="price_mva")
    if st.button("Beregn pris", key="btn_price"):
        show_result(calc_price(base, rabatt, paslag, mva))

# ---- Diagonal (Pytagoras) ----
with tabs[8]:
    if is_school_mode():
        st.caption("Pytagoras brukes i rettvinklede trekanter: c = √(a² + b²).")

    st.subheader("Diagonal (Pytagoras)")
    a = st.number_input("Side a (m)", min_value=0.0, value=3.0, step=0.1, key="pyt_a")
    b = st.number_input("Side b (m)", min_value=0.0, value=4.0, step=0.1, key="pyt_b")

    if st.button("Beregn diagonal", key="btn_pyt"):
        show_result(calc_pythagoras(a, b))
        
# ---- Historikk ----
with tabs[9]:
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

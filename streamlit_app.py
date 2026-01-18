import math
import time
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple

import pandas as pd
import streamlit as st


# -----------------------------
# Hjelpefunksjoner (enheter)
# -----------------------------
def mm_to_m(mm: float) -> float:
    return mm / 1000.0

def cm_to_m(cm: float) -> float:
    return cm / 100.0

def m_to_mm(m: float) -> float:
    return m * 1000.0

def safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default

def round_sensible(x: float, decimals: int = 3) -> float:
    return round(x, decimals)

# NYTT: konvertering fra (mm/cm/m) -> mm for mål på tegning
def to_mm(value: float, unit: str) -> float:
    if unit == "mm":
        return value
    if unit == "cm":
        return value * 10.0
    if unit == "m":
        return value * 1000.0
    return value

def mm_to_all(mm: float) -> Dict[str, float]:
    return {"mm": mm, "cm": mm / 10.0, "m": mm / 1000.0}


# -----------------------------
# Resultatformat
# -----------------------------
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


# -----------------------------
# Kalkulatorer
# -----------------------------
def calc_area_rectangle(length_m: float, width_m: float) -> CalcResult:
    warnings = []
    steps = []
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
    warnings = []
    steps = []
    warn_if(area_m2 <= 0, "Areal må være > 0.", warnings)
    warn_if(waste_percent < 0 or waste_percent > 50, "Svinn% virker uvanlig (0–50%).", warnings)

    factor = 1 + waste_percent / 100.0
    order_area = area_m2 * factor

    steps.append("Bestillingsareal = areal × (1 + svinn/100)")
    steps.append(f"= {area_m2} × (1 + {waste_percent}/100)")
    steps.append(f"= {area_m2} × {factor} = {order_area} m²")

    return CalcResult(
        name="Areal + svinn",
        inputs={"areal_m2": area_m2, "svinn_prosent": waste_percent},
        outputs={"bestillingsareal_m2": round_sensible(order_area, 3)},
        steps=steps,
        warnings=warnings,
        timestamp=make_timestamp(),
    )


def calc_area_composite(rectangles: List[Tuple[float, float]]) -> CalcResult:
    warnings = []
    steps = []
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
    warnings = []
    steps = []
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
    warnings = []
    steps = []
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
    warnings = []
    steps = []
    warn_if(diameter_mm <= 0 or height_m <= 0, "Diameter/høyde må være > 0.", warnings)
    warn_if(diameter_mm < 80 or diameter_mm > 1500, "Diameter (mm) virker uvanlig (80–1500 mm).", warnings)

    r_m = mm_to_m(diameter_mm) / 2.0
    volume = math.pi * (r_m ** 2) * height_m

    steps.append("Volum sylinder = π × r² × h")
    steps.append(f"r = diameter/2 = {diameter_mm}/2 mm -> {r_m} m")
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
    """
    mode:
      - 'prosent' value = % fall
      - '1:x' value = x (f.eks. 50 for 1:50)
      - 'mm_per_m' value = mm per meter
    """
    warnings = []
    steps = []
    warn_if(length_m <= 0, "Lengde må være > 0.", warnings)

    if mode == "prosent":
        warn_if(value < 0 or value > 20, "Prosentfall virker uvanlig (0–20%).", warnings)
        mm_per_m = value / 100.0 * 1000.0
        steps.append(f"mm per meter = (%/100) × 1000 = ({value}/100) × 1000 = {mm_per_m} mm/m")
    elif mode == "1:x":
        warn_if(value <= 0, "x må være > 0.", warnings)
        warn_if(value < 20 or value > 200, "1:x virker uvanlig (typisk 1:20 til 1:200).", warnings)
        mm_per_m = 1000.0 / value
        steps.append(f"mm per meter = 1000 / x = 1000 / {value} = {mm_per_m} mm/m")
    elif mode == "mm_per_m":
        warn_if(value < 0 or value > 200, "mm per meter virker uvanlig (0–200).", warnings)
        mm_per_m = value
        steps.append(f"mm per meter = {mm_per_m} mm/m")
    else:
        warnings.append("Ugyldig modus for fall.")
        mm_per_m = 0.0

    height_diff_mm = mm_per_m * length_m
    height_diff_m = mm_to_m(height_diff_mm)

    steps.append("Høydeforskjell = (mm per meter) × lengde")
    steps.append(f"= {mm_per_m} × {length_m} = {height_diff_mm} mm = {height_diff_m} m")

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


# OPPDATERT: målestokk med valgt enhet på tegning
def calc_scale(drawing_value: float, drawing_unit: str, scale: int) -> CalcResult:
    warnings = []
    steps = []
    warn_if(drawing_value <= 0, "Mål på tegning må være > 0.", warnings)
    warn_if(scale <= 0, "Målestokk må være > 0.", warnings)
    warn_if(scale not in [10, 20, 25, 50, 75, 100, 200], "Uvanlig målestokk. Sjekk at du har riktig.", warnings)

    drawing_mm = to_mm(drawing_value, drawing_unit)
    real_mm = drawing_mm * scale
    real_all = mm_to_all(real_mm)

    steps.append("Virkelig mål = mål på tegning × målestokk")
    steps.append(f"Mål på tegning = {drawing_value} {drawing_unit} = {drawing_mm} mm")
    steps.append(f"Virkelig mål = {drawing_mm} mm × {scale} = {real_mm} mm")
    steps.append(f"= {real_all['cm']} cm = {real_all['m']} m")

    return CalcResult(
        name="Målestokk (tegning → virkelighet)",
        inputs={"tegning_verdi": drawing_value, "tegning_enhet": drawing_unit, "malestokk": scale},
        outputs={
            "virkelig_mm": round_sensible(real_all["mm"], 1),
            "virkelig_cm": round_sensible(real_all["cm"], 2),
            "virkelig_m": round_sensible(real_all["m"], 3),
        },
        steps=steps,
        warnings=warnings,
        timestamp=make_timestamp(),
    )


def calc_pythagoras(a_m: float, b_m: float) -> CalcResult:
    warnings = []
    steps = []
    warn_if(a_m <= 0 or b_m <= 0, "Begge sider må være > 0.", warnings)

    c = math.sqrt(a_m ** 2 + b_m ** 2)

    steps.append("Diagonal c = √(a² + b²)")
    steps.append(f"= √({a_m}² + {b_m}²) = √({a_m**2} + {b_m**2}) = √({a_m**2 + b_m**2})")
    steps.append(f"= {c} m")

    return CalcResult(
        name="Pytagoras (diagonal)",
        inputs={"a_m": a_m, "b_m": b_m},
        outputs={"diagonal_m": round_sensible(c, 3)},
        steps=steps,
        warnings=warnings,
        timestamp=make_timestamp(),
    )


def calc_price(base_price: float, rabatt_prosent: float, paslag_prosent: float, mva_prosent: float) -> CalcResult:
    warnings = []
    steps = []

    warn_if(base_price < 0, "Pris kan ikke være negativ.", warnings)
    warn_if(rabatt_prosent < 0 or rabatt_prosent > 90, "Rabatt virker uvanlig (0–90%).", warnings)
    warn_if(paslag_prosent < 0 or paslag_prosent > 200, "Påslag virker uvanlig (0–200%).", warnings)
    warn_if(mva_prosent < 0 or mva_prosent > 50, "MVA virker uvanlig (0–50%).", warnings)

    price_after_discount = base_price * (1 - rabatt_prosent / 100.0)
    price_after_markup = price_after_discount * (1 + paslag_prosent / 100.0)
    price_after_mva = price_after_markup * (1 + mva_prosent / 100.0)

    steps.append("Pris etter rabatt = grunnpris × (1 - rabatt/100)")
    steps.append(f"= {base_price} × (1 - {rabatt_prosent}/100) = {price_after_discount}")

    steps.append("Pris etter påslag = pris × (1 + påslag/100)")
    steps.append(f"= {price_after_discount} × (1 + {paslag_prosent}/100) = {price_after_markup}")

    steps.append("Pris inkl. MVA = pris × (1 + mva/100)")
    steps.append(f"= {price_after_markup} × (1 + {mva_prosent}/100) = {price_after_mva}")

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
    warnings = []
    steps = []
    warn_if(quantity <= 0, "Mengde må være > 0.", warnings)
    warn_if(productivity_per_hour <= 0, "Produksjon må være > 0.", warnings)

    hours = quantity / productivity_per_hour
    days_7_5h = hours / 7.5

    steps.append("Timer = mengde / produksjon")
    steps.append(f"= {quantity} / {productivity_per_hour} = {hours} timer")
    steps.append("Dagsverk (7,5t) = timer / 7,5")
    steps.append(f"= {hours} / 7,5 = {days_7_5h} dagsverk")

    return CalcResult(
        name="Tidsestimat",
        inputs={"mengde": quantity, "produksjon_per_time": productivity_per_hour},
        outputs={"timer": round_sensible(hours, 2), "dagsverk_7_5t": round_sensible(days_7_5h, 2)},
        steps=steps,
        warnings=warnings,
        timestamp=make_timestamp(),
    )


def calc_deviation(projected: float, measured: float, tolerance_mm: float, unit: str) -> CalcResult:
    warnings = []
    steps = []

    if unit == "m":
        projected_mm = m_to_mm(projected)
        measured_mm = m_to_mm(measured)
        steps.append(
            f"Konverterer til mm: prosjektert {projected} m = {projected_mm} mm, "
            f"målt {measured} m = {measured_mm} mm"
        )
    else:
        projected_mm = projected
        measured_mm = measured

    warn_if(tolerance_mm < 0, "Toleranse kan ikke være negativ.", warnings)

    diff_mm = measured_mm - projected_mm
    abs_diff_mm = abs(diff_mm)
    ok = abs_diff_mm <= tolerance_mm

    steps.append("Avvik = målt - prosjektert")
    steps.append(f"= {measured_mm} - {projected_mm} = {diff_mm} mm")
    steps.append(f"|Avvik| = {abs_diff_mm} mm")
    steps.append(f"Innenfor toleranse? {abs_diff_mm} ≤ {tolerance_mm} -> {'OK' if ok else 'IKKE OK'}")

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


# NYTT: Tømmermannskledning (kun bredde fra–til, omlegg og bordbredder)
def calc_tommermannskledning_width(
    measure_cm: float,
    overlap_cm: float,
    under_width_mm: float,
    over_width_mm: float
) -> CalcResult:
    """
    Tømmermannskledning – beregning langs bredde (fra–til).

    Avgrensning iht. ditt krav:
    - Tar kun hensyn til: mål fra–til (cm), omlegg (cm), valg av under-/overliggerbredde (mm).
    - Underliggere antas kant-i-kant (uten spalte).
    - Overliggere dekker skjøtene mellom underliggere.
    - Omlegg tolkes som overlapp inn på hver side -> min overliggerbredde = 2 * omlegg.
    """
    warnings = []
    steps = []

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
            f"Valgt overligger ({over_width_mm} mm) er for smal for omlegg {overlap_cm} cm. "
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


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Bygg-kalkulator", layout="wide")

st.title("Bygg-kalkulatoren for praktiske beregninger")
st.caption("Kalkulatorer for vanlige oppgaver i byggebransjen. Med enheter, kontroll og valgfri mellomregning.")

if "history" not in st.session_state:
    st.session_state.history: List[Dict[str, Any]] = []

def show_result(res: CalcResult):
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Resultat")

        # Visningsnavn (label) for output-nøkler
        output_labels = {
            # Målestokk
            "virkelig_mm": "Virkelig mål (mm)",
            "virkelig_cm": "Virkelig mål (cm)",
            "virkelig_m": "Virkelig mål (m)",

            # Tømmermannskledning
            "underliggere_antall": "Antall underliggere",
            "overliggere_antall": "Antall overliggere",
            "dekket_bredde_mm": "Dekket bredde (mm)",
            "overdekning_mm": "Overdekning (mm)",
            "min_overligger_bredde_mm": "Min. overliggerbredde (mm)",
            "overligger_ok_for_omlegg": "Overligger OK for omlegg",
        }

        for k, v in res.outputs.items():
            label = output_labels.get(k, k.replace("_", " ").capitalize())
            st.write(f"**{label}**: {v}")

        if res.warnings:
            st.warning("\n".join(res.warnings))
        else:
            st.success("Ingen varsler.")

        if st.button("Lagre i historikk", type="primary"):
            st.session_state.history.append({
                "tid": res.timestamp,
                "kalkulator": res.name,
                "inputs": res.inputs,
                "outputs": res.outputs,
                "warnings": res.warnings,
            })
            st.toast("Lagret.")

    with col2:
        st.subheader("Utregning (valgfritt)")
        show_steps = st.toggle("Vis mellomregning", value=True)
        if show_steps:
            for s in res.steps:
                st.write(f"- {s}")


        if res.warnings:
            st.warning("\n".join(res.warnings))
        else:
            st.success("Ingen varsler.")

        if st.button("Lagre i historikk", type="primary"):
            st.session_state.history.append({
                "tid": res.timestamp,
                "kalkulator": res.name,
                "inputs": res.inputs,
                "outputs": res.outputs,
                "warnings": res.warnings,
            })
            st.toast("Lagret.")
    with col2:
        st.subheader("Utregning (valgfritt)")
        show_steps = st.toggle("Vis mellomregning", value=True)
        if show_steps:
            for s in res.steps:
                st.write(f"- {s}")

tabs = st.tabs([
    "Måling/enheter",
    "Areal",
    "Volum/betong",
    "Målestokk",
    "Kledning",
    "Fall/vinkel/diagonal",
    "Økonomi",
    "Tid",
    "Avvik/KS",
    "Historikk",
])

# ---- Måling/enheter ----
with tabs[0]:
    st.subheader("Enhetsomregner")
    c1, c2, c3 = st.columns(3)

    with c1:
        mm_val = st.number_input("mm", min_value=0.0, value=1000.0, step=1.0)
        st.write(f"= {round_sensible(mm_to_m(mm_val), 4)} m")

    with c2:
        cm_val = st.number_input("cm", min_value=0.0, value=100.0, step=1.0)
        st.write(f"= {round_sensible(cm_to_m(cm_val), 4)} m")

    with c3:
        m_val = st.number_input("m", min_value=0.0, value=1.0, step=0.1)
        st.write(f"= {round_sensible(m_to_mm(m_val), 1)} mm")


# ---- Areal ----
with tabs[1]:
    st.subheader("Areal (rektangel)")
    l = st.number_input("Lengde (m)", min_value=0.0, value=5.0, step=0.1, key="areal_l")
    w = st.number_input("Bredde (m)", min_value=0.0, value=4.0, step=0.1, key="areal_w")
    if st.button("Beregn areal", key="btn_areal"):
        res = calc_area_rectangle(l, w)
        show_result(res)

    st.divider()
    st.subheader("Areal + svinn")
    area = st.number_input("Areal (m²)", min_value=0.0, value=20.0, step=0.1, key="svinn_area")
    waste = st.number_input("Svinn (%)", min_value=0.0, value=10.0, step=1.0, key="svinn_pct")
    if st.button("Beregn bestillingsareal", key="btn_svinn"):
        res = calc_area_with_waste(area, waste)
        show_result(res)

    st.divider()
    st.subheader("Areal (sammensatt av rektangler)")
    st.caption("Legg inn delmål og summer dem.")
    n = st.number_input("Antall deler", min_value=1, max_value=20, value=3, step=1, key="comp_n")
    rects = []
    for i in range(int(n)):
        c1, c2 = st.columns(2)
        with c1:
            li = st.number_input(f"Del {i+1} lengde (m)", min_value=0.0, value=2.0, step=0.1, key=f"comp_l_{i}")
        with c2:
            wi = st.number_input(f"Del {i+1} bredde (m)", min_value=0.0, value=1.5, step=0.1, key=f"comp_w_{i}")
        rects.append((li, wi))
    if st.button("Beregn sammensatt areal", key="btn_comp"):
        res = calc_area_composite(rects)
        show_result(res)


# ---- Volum/betong ----
with tabs[2]:
    st.subheader("Betongplate")
    l = st.number_input("Lengde (m)", min_value=0.0, value=6.0, step=0.1, key="slab_l")
    w = st.number_input("Bredde (m)", min_value=0.0, value=4.0, step=0.1, key="slab_w")
    t = st.number_input("Tykkelse (mm)", min_value=0.0, value=100.0, step=5.0, key="slab_t")
    if st.button("Beregn volum (plate)", key="btn_slab"):
        res = calc_concrete_slab(l, w, t)
        show_result(res)

    st.divider()
    st.subheader("Stripefundament")
    l = st.number_input("Lengde (m)", min_value=0.0, value=20.0, step=0.1, key="strip_l")
    w = st.number_input("Bredde (m)", min_value=0.0, value=0.4, step=0.05, key="strip_w")
    h = st.number_input("Høyde (mm)", min_value=0.0, value=400.0, step=10.0, key="strip_h")
    if st.button("Beregn volum (stripefundament)", key="btn_strip"):
        res = calc_strip_foundation(l, w, h)
        show_result(res)

    st.divider()
    st.subheader("Søyle (sylinder)")
    d = st.number_input("Diameter (mm)", min_value=0.0, value=300.0, step=10.0, key="col_d")
    hm = st.number_input("Høyde (m)", min_value=0.0, value=3.0, step=0.1, key="col_h")
    if st.button("Beregn volum (søyle)", key="btn_col"):
        res = calc_column_cylinder(d, hm)
        show_result(res)


# ---- Målestokk ----
with tabs[3]:
    st.subheader("Målestokk (tegning → virkelighet)")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        draw_val = st.number_input("Mål på tegning", min_value=0.0, value=50.0, step=1.0, key="scale_draw_val")
    with c2:
        draw_unit = st.selectbox("Enhet", options=["mm", "cm", "m"], index=0, key="scale_draw_unit")
    with c3:
        scale = st.selectbox("Målestokk", options=[10, 20, 25, 50, 75, 100, 200], index=3, key="scale_sel")

    if st.button("Beregn virkelig mål", key="btn_scale"):
        res = calc_scale(float(draw_val), str(draw_unit), int(scale))
        show_result(res)


# ---- Kledning ----
# ---- Kledning ----
with tabs[4]:
    st.subheader("Tømmermannskledning (kun bredde)")
    st.caption("Skriv inn fritt: mål fra–til (cm), omlegg (cm) og bordbredder (mm).")

    c1, c2, c3, c4 = st.columns([2, 2, 2, 2])

    with c1:
        measure_cm = st.number_input(
            "Mål fra–til (cm)",
            min_value=0.0,
            value=600.0,
            step=1.0,
            key="tk_measure_cm"
        )

    with c2:
        overlap_cm = st.number_input(
            "Ønsket omlegg (cm)",
            min_value=0.0,
            value=2.0,
            step=0.1,
            key="tk_overlap_cm"
        )

    with c3:
        under_w = st.number_input(
            "Underligger bredde (mm)",
            min_value=1.0,
            value=148.0,
            step=1.0,
            key="tk_under_w"
        )

    with c4:
        over_w = st.number_input(
            "Overligger bredde (mm)",
            min_value=1.0,
            value=58.0,
            step=1.0,
            key="tk_over_w"
        )

    if st.button("Beregn kledning", key="btn_tk"):
        res = calc_tommermannskledning_width(
            measure_cm=float(measure_cm),
            overlap_cm=float(overlap_cm),
            under_width_mm=float(under_w),
            over_width_mm=float(over_w),
        )
        show_result(res)



# ---- Fall/vinkel/diagonal ----
with tabs[5]:
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
        res = calc_fall(length, mode, float(val))
        show_result(res)

    st.divider()
    st.subheader("Pytagoras (diagonal)")
    a = st.number_input("Side a (m)", min_value=0.0, value=3.0, step=0.1, key="pyt_a")
    b = st.number_input("Side b (m)", min_value=0.0, value=4.0, step=0.1, key="pyt_b")
    if st.button("Beregn diagonal", key="btn_pyt"):
        res = calc_pythagoras(a, b)
        show_result(res)


# ---- Økonomi ----
with tabs[6]:
    st.subheader("Pris (rabatt/påslag/MVA)")
    base = st.number_input("Grunnpris", min_value=0.0, value=1000.0, step=10.0, key="price_base")
    rabatt = st.number_input("Rabatt (%)", min_value=0.0, value=0.0, step=1.0, key="price_rabatt")
    paslag = st.number_input("Påslag (%)", min_value=0.0, value=0.0, step=1.0, key="price_paslag")
    mva = st.number_input("MVA (%)", min_value=0.0, value=25.0, step=1.0, key="price_mva")
    if st.button("Beregn pris", key="btn_price"):
        res = calc_price(base, rabatt, paslag, mva)
        show_result(res)


# ---- Tid ----
with tabs[7]:
    st.subheader("Tidsestimat")
    qty = st.number_input("Mengde (f.eks. m²)", min_value=0.0, value=50.0, step=1.0, key="time_qty")
    prod = st.number_input("Produksjon per time (f.eks. m²/time)", min_value=0.0, value=10.0, step=0.5, key="time_prod")
    if st.button("Beregn tid", key="btn_time"):
        res = calc_time_estimate(qty, prod)
        show_result(res)


# ---- Avvik/KS ----
with tabs[8]:
    st.subheader("Avvik / toleranse")
    unit = st.selectbox("Enhet for inndata", options=["mm", "m"], index=0, key="dev_unit")
    projected = st.number_input(
        "Prosjektert",
        value=1000.0 if unit == "mm" else 1.0,
        step=1.0 if unit == "mm" else 0.01,
        key="dev_proj"
    )
    measured = st.number_input(
        "Målt",
        value=1002.0 if unit == "mm" else 1.002,
        step=1.0 if unit == "mm" else 0.01,
        key="dev_meas"
    )
    tol = st.number_input("Toleranse (mm)", min_value=0.0, value=2.0, step=0.5, key="dev_tol")
    if st.button("Beregn avvik", key="btn_dev"):
        res = calc_deviation(float(projected), float(measured), float(tol), unit)
        show_result(res)


# ---- Historikk ----
with tabs[9]:
    st.subheader("Historikk")
    if not st.session_state.history:
        st.info("Ingen beregninger lagret ennå.")
    else:
        rows = []
        for item in st.session_state.history:
            rows.append({
                "tid": item["tid"],
                "kalkulator": item["kalkulator"],
                "inputs": str(item["inputs"]),
                "outputs": str(item["outputs"]),
                "warnings": "; ".join(item["warnings"]) if item["warnings"] else "",
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Last ned historikk (CSV)",
            data=csv,
            file_name="bygg_kalkulator_historikk.csv",
            mime="text/csv"
        )

        if st.button("Tøm historikk"):
            st.session_state.history = []
            st.success("Historikk tømt.")

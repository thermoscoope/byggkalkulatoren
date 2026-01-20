# drawing_to_materials_prototype.py
# Prototype (Nivå 1): Skann/ta bilde -> OCR av måltekster -> enhetsvalg/konvertering -> vegg-mal -> materialliste
#
# Integrasjon: Denne filen kan importeres i Streamlit-appen din, og du kan kalle:
#   render_drawing_to_materials_page()
#
# Avhengigheter (prototype):
#   pip install streamlit pillow numpy opencv-python pytesseract
# Valgfritt (bedre OCR):
#   pip install easyocr
#
# NB:
# - Dette er en Nivå 1-prototype. Den tolker tall (måltekster), lar bruker velge L/H, og genererer materialliste
#   basert på en enkel veggmal. Den forsøker ikke å forstå geometri/veggsegmenter automatisk.

from __future__ import annotations

import re
import math
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

# Streamlit (for UI)
import streamlit as st

# OpenCV (for enkel forbedring av bilde)
try:
    import cv2
except Exception:
    cv2 = None

# OCR: prøv EasyOCR først, fallback til pytesseract, fallback til "manuell tekst"
EASYOCR_AVAILABLE = False
PYTESSERACT_AVAILABLE = False

try:
    import easyocr  # type: ignore
    EASYOCR_AVAILABLE = True
except Exception:
    EASYOCR_AVAILABLE = False

try:
    import pytesseract  # type: ignore
    PYTESSERACT_AVAILABLE = True
except Exception:
    PYTESSERACT_AVAILABLE = False


# ----------------------------
# Datamodeller
# ----------------------------

@dataclass
class WallInputs:
    length_value: float
    height_value: float
    unit: str  # "mm" | "cm" | "m"
    wall_count: int = 1
    stud_cc_mm: int = 600
    waste_pct: float = 10.0  # prosent


@dataclass
class MaterialLine:
    item: str
    spec: str
    quantity: float
    unit: str
    note: str = ""


# ----------------------------
# Bildebehandling (prototype)
# ----------------------------

def _pil_to_bgr(img: Image.Image) -> np.ndarray:
    arr = np.array(img.convert("RGB"))
    # RGB -> BGR for OpenCV
    return arr[:, :, ::-1].copy()


def _bgr_to_pil(arr_bgr: np.ndarray) -> Image.Image:
    arr_rgb = arr_bgr[:, :, ::-1]
    return Image.fromarray(arr_rgb)


def preprocess_for_ocr(img: Image.Image) -> Image.Image:
    """
    Enkel OCR-forbedring:
    - gråskala
    - kontrast/terskel
    - lett støyreduksjon
    """
    if cv2 is None:
        return img

    bgr = _pil_to_bgr(img)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    # Støyreduksjon
    gray = cv2.bilateralFilter(gray, d=7, sigmaColor=50, sigmaSpace=50)

    # Adaptiv terskel for å få tydelig tekst
    th = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 7
    )

    # Lett "morfologi" for å gjøre tekst litt tykkere (kan hjelpe)
    kernel = np.ones((2, 2), np.uint8)
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, kernel, iterations=1)

    # Konverter tilbake
    th_bgr = cv2.cvtColor(th, cv2.COLOR_GRAY2BGR)
    return _bgr_to_pil(th_bgr)


# ----------------------------
# OCR
# ----------------------------

def ocr_extract_text(img: Image.Image) -> str:
    """
    Returnerer rå tekst fra bildet.
    Prioritet:
    1) EasyOCR
    2) pytesseract
    3) tom streng
    """
    # EasyOCR
    if EASYOCR_AVAILABLE:
        try:
            reader = easyocr.Reader(["en", "no"], gpu=False)
            bgr = _pil_to_bgr(img)
            results = reader.readtext(bgr, detail=0, paragraph=True)
            return "\n".join(results)
        except Exception:
            pass

    # pytesseract
    if PYTESSERACT_AVAILABLE:
        try:
            # Tips: tesseract må være installert i OS for å fungere fullt.
            # På Windows må "tesseract.exe" være i PATH eller pytesseract.pytesseract.tesseract_cmd settes.
            return pytesseract.image_to_string(img)
        except Exception:
            pass

    return ""


# ----------------------------
# Teksttolkning (mål og enheter)
# ----------------------------

_UNIT_PATTERN = re.compile(r"\b(mm|cm|m)\b", re.IGNORECASE)

def detect_global_unit(text: str) -> Optional[str]:
    """
    Prøver å finne enhetsregel i tekst (mm/cm/m).
    Returnerer "mm"/"cm"/"m" hvis funnet, ellers None.
    """
    hits = _UNIT_PATTERN.findall(text)
    if not hits:
        # Enkel heuristikk for setninger
        if re.search(r"mål\s*(er|i)\s*mm", text, re.IGNORECASE):
            return "mm"
        if re.search(r"mål\s*(er|i)\s*cm", text, re.IGNORECASE):
            return "cm"
        if re.search(r"mål\s*(er|i)\s*m", text, re.IGNORECASE):
            return "m"
        return None

    # Hvis flere: velg den mest vanlige
    norm = [h.lower() for h in hits]
    return max(set(norm), key=norm.count)


def _normalize_number_token(token: str) -> Optional[float]:
    """
    Tolererer:
    - "2 400" -> 2400
    - "2.400" -> 2400 (vanlig tusenskille i tegning)
    - "2,4" -> 2.4 (desimal)
    - "2400" -> 2400
    """
    t = token.strip()

    # Fjern whitespace i tall
    t = re.sub(r"\s+", "", t)

    # Hvis både , og . finnes, prøv å tolke tusenskille:
    # "2.400,5" (sjeldent i tegning) -> 2400.5
    # "2,400.5" -> 2400.5
    if "," in t and "." in t:
        # Antar at siste separator er desimal
        last_comma = t.rfind(",")
        last_dot = t.rfind(".")
        if last_comma > last_dot:
            # komma desimal, punkt tusen
            t = t.replace(".", "")
            t = t.replace(",", ".")
        else:
            # punkt desimal, komma tusen
            t = t.replace(",", "")
    else:
        # Hvis bare komma: desimal
        if "," in t:
            t = t.replace(",", ".")
        # Hvis bare punkt: kan være desimal eller tusen.
        # Heuristikk: "2.400" med 3 siffer etter punkt -> tusen
        m = re.match(r"^\d+\.(\d{3})$", t)
        if m:
            t = t.replace(".", "")

    try:
        return float(t)
    except Exception:
        return None


def extract_measure_candidates(text: str) -> List[Tuple[str, float, Optional[str]]]:
    """
    Trekker ut kandidat-mål fra teksten.
    Returnerer liste av (raw, value, unit_opt)
    Eksempler:
      "2400" -> ("2400", 2400.0, None)
      "2,4 m" -> ("2,4 m", 2.4, "m")
      "1200mm" -> ("1200mm", 1200.0, "mm")
    """
    # Tall med evt tusen/desimal og evt enhet tett på
    pattern = re.compile(
        r"(?P<num>\d{1,3}(?:[ .]\d{3})*(?:[.,]\d+)?|\d+(?:[.,]\d+)?)\s*(?P<unit>mm|cm|m)?",
        re.IGNORECASE
    )

    out: List[Tuple[str, float, Optional[str]]] = []
    for m in pattern.finditer(text):
        raw_num = m.group("num")
        raw_unit = m.group("unit")
        val = _normalize_number_token(raw_num)
        if val is None:
            continue

        # Filtrer vekk veldig små tall som ofte er støy (f.eks. 1, 2, 3)
        # men behold desimalmål som 2.4 (meter)
        if val < 10 and (raw_unit is None or raw_unit.lower() != "m"):
            continue

        raw_full = (raw_num + ("" if not raw_unit else f" {raw_unit}")).strip()
        unit = raw_unit.lower() if raw_unit else None
        out.append((raw_full, val, unit))

    # Av-dupliser litt
    dedup = []
    seen = set()
    for raw, val, unit in out:
        key = (round(val, 4), unit)
        if key in seen:
            continue
        seen.add(key)
        dedup.append((raw, val, unit))
    return dedup


def convert_to_mm(value: float, unit: str) -> int:
    unit = unit.lower()
    if unit == "mm":
        return int(round(value))
    if unit == "cm":
        return int(round(value * 10.0))
    if unit == "m":
        return int(round(value * 1000.0))
    raise ValueError(f"Ukjent enhet: {unit}")


def mm_to_m(mm: int) -> float:
    return mm / 1000.0


# ----------------------------
# Veggmal (Nivå 1)
# ----------------------------

def generate_material_list_wall_A(inp: WallInputs) -> List[MaterialLine]:
    """
    Mal A: Innvendig bindingsverksvegg 48x98, c/c 600, 1-lags gips én side.
    Output er en enkel materialliste med svinn.
    """
    # Konverter til mm internt
    L_mm = convert_to_mm(inp.length_value, inp.unit)
    H_mm = convert_to_mm(inp.height_value, inp.unit)
    n = max(1, int(inp.wall_count))
    cc = max(300, int(inp.stud_cc_mm))  # sanity
    waste = max(0.0, float(inp.waste_pct)) / 100.0

    # 1) Svill + toppsvill (løpemeter)
    # Totalt løpemeter = 2 * L * n
    lm_sill = (2 * L_mm * n) / 1000.0
    lm_sill_waste = lm_sill * (1.0 + waste)

    # 2) Stendere
    studs_per_wall = int(math.ceil(L_mm / cc) + 1)  # ende + c/c
    studs_total = studs_per_wall * n
    studs_total_waste = int(math.ceil(studs_total * (1.0 + waste)))

    # 3) Gipsplater (1200x2400)
    area_m2 = (L_mm / 1000.0) * (H_mm / 1000.0) * n
    plate_area = 1.2 * 2.4
    plates = int(math.ceil(area_m2 / plate_area))
    plates_waste = int(math.ceil(plates * (1.0 + waste)))

    # 4) Skruer (forenklet normtall)
    screws_per_plate = 30  # justerbar senere
    screws = plates_waste * screws_per_plate

    notes_height = ""
    if abs(H_mm - 2400) > 5:
        notes_height = "Høyden avviker fra 2400 mm; kapp/tilpasning må planlegges."

    return [
        MaterialLine(
            item="Konstruksjonsvirke",
            spec="48x98 mm svill + toppsvill",
            quantity=round(lm_sill_waste, 2),
            unit="lm",
            note="Inkl. svinn" if waste > 0 else ""
        ),
        MaterialLine(
            item="Konstruksjonsvirke",
            spec=f"48x98 mm stender, lengde {H_mm} mm",
            quantity=float(studs_total_waste),
            unit="stk",
            note=("Inkl. svinn. " if waste > 0 else "") + notes_height
        ),
        MaterialLine(
            item="Gipsplate",
            spec="12,5 mm 1200x2400 (1 lag, 1 side)",
            quantity=float(plates_waste),
            unit="stk",
            note=("Inkl. svinn. " if waste > 0 else "") + notes_height
        ),
        MaterialLine(
            item="Gipsskruer",
            spec="Forbruk (forenklet)",
            quantity=float(screws),
            unit="stk",
            note="Ca. 30 skruer per plate (juster senere ved behov)."
        ),
    ]


# ----------------------------
# UI: Streamlit-side (prototype)
# ----------------------------

def _warn_if_unusual(L_mm: int, H_mm: int) -> List[str]:
    warns = []
    if H_mm < 1500 or H_mm > 4000:
        warns.append("Uvanlig vegghøyde – sjekk enhet og valgt tall.")
    if L_mm < 500 or L_mm > 15000:
        warns.append("Uvanlig vegglengde – sjekk enhet og valgt tall.")
    return warns


def render_drawing_to_materials_page() -> None:
    st.title("Skann tegning → Materialliste (Prototype Nivå 1)")

    st.caption(
        "Flyt: ta bilde/last opp → OCR av tall → velg lengde/høyde og enhet → velg veggmal → få materialliste."
    )

    colA, colB = st.columns(2, gap="large")

    with colA:
        st.subheader("1) Bilde inn")
        mode = st.radio("Velg input", ["Kamera (mobil)", "Last opp bilde"], horizontal=True)

        img: Optional[Image.Image] = None
        if mode == "Kamera (mobil)":
            cam = st.camera_input("Ta bilde av arbeidstegningen (hele tittelfeltet bør være synlig)")
            if cam is not None:
                img = Image.open(cam)
        else:
            up = st.file_uploader("Last opp bilde (png/jpg)", type=["png", "jpg", "jpeg"])
            if up is not None:
                img = Image.open(up)

        if img is None:
            st.info("Legg inn et bilde for å starte.")
            return

        st.image(img, caption="Original", use_container_width=True)

        st.subheader("2) Forbedre bilde (valgfritt)")
        do_pre = st.checkbox("Forbedre for OCR (anbefalt)", value=True)
        img_for_ocr = preprocess_for_ocr(img) if do_pre else img

        with st.expander("Se OCR-forbedret bilde"):
            st.image(img_for_ocr, caption="For OCR", use_container_width=True)

    with colB:
        st.subheader("3) OCR og måluttak")

        st.write("OCR-status:")
        st.write(f"- EasyOCR: {'OK' if EASYOCR_AVAILABLE else 'ikke tilgjengelig'}")
        st.write(f"- pytesseract: {'OK' if PYTESSERACT_AVAILABLE else 'ikke tilgjengelig'}")

        raw_text = ocr_extract_text(img_for_ocr)
        if not raw_text.strip():
            st.warning(
                "Jeg klarte ikke å hente tekst via OCR. Lim inn måltekst manuelt (prototype-fallback)."
            )
            raw_text = st.text_area(
                "Manuell tekst (lim inn det som står ved målene, f.eks. '3600 2400 Mål i mm')",
                height=120
            )
        else:
            with st.expander("Se rå OCR-tekst"):
                st.text(raw_text)

        detected_unit = detect_global_unit(raw_text)
        candidates = extract_measure_candidates(raw_text)

        st.write("Foreslått enhet funnet i tekst:", detected_unit if detected_unit else "ingen")
        unit = st.selectbox("Velg enhet for tall uten enhet", ["mm", "cm", "m"], index=["mm", "cm", "m"].index(detected_unit) if detected_unit in ["mm", "cm", "m"] else 0)

        st.markdown("**Tolket målliste** (velg to tall: lengde og høyde)")
        if not candidates:
            st.error("Fant ingen mål-kandidater. Prøv bedre bilde, eller legg inn tekst manuelt.")
            return

        # Lag en pen liste i UI
        option_labels = []
        option_values = []
        for raw, val, u in candidates:
            show_u = u if u else f"(tolkes som {unit})"
            option_labels.append(f"{raw}  →  {val} {show_u}")
            option_values.append((raw, val, u))

        # Velg L/H
        idx_len = st.selectbox("Velg vegglengde", list(range(len(option_labels))), format_func=lambda i: option_labels[i])
        idx_hgt = st.selectbox("Velg vegghøyde", list(range(len(option_labels))), index=min(1, len(option_labels)-1), format_func=lambda i: option_labels[i])

        rawL, valL, uL = option_values[idx_len]
        rawH, valH, uH = option_values[idx_hgt]

        # Bestem enhet per verdi: hvis OCR fant enhet ved tallet, bruk den; ellers bruk valgt enhet
        unitL = uL if uL else unit
        unitH = uH if uH else unit

        # Konverter for sanity checks
        L_mm = convert_to_mm(valL, unitL)
        H_mm = convert_to_mm(valH, unitH)

        # Varsler
        warns = _warn_if_unusual(L_mm, H_mm)
        for w in warns:
            st.warning(w)

        st.subheader("4) Veggmal og parametre")
        wall_count = st.number_input("Antall like vegger", min_value=1, max_value=50, value=1, step=1)
        stud_cc = st.selectbox("Stenderavstand (c/c)", [450, 600], index=1)
        waste_pct = st.slider("Kapp/svinn (%)", min_value=0, max_value=25, value=10, step=1)

        st.write("Valgte mål (intern):")
        st.write(f"- Lengde: {L_mm} mm ({round(mm_to_m(L_mm), 2)} m)")
        st.write(f"- Høyde: {H_mm} mm ({round(mm_to_m(H_mm), 2)} m)")

        st.subheader("5) Generer materialliste")
        if st.button("Lag materialliste", type="primary"):
            inp = WallInputs(
                length_value=valL,
                height_value=valH,
                unit=unit,  # global enhet for tall uten enhet; valL/valH har evt egne i unitL/unitH, men her bruker vi global for input
                wall_count=int(wall_count),
                stud_cc_mm=int(stud_cc),
                waste_pct=float(waste_pct),
            )

            # Viktig: Siden lengde/høyde kan ha egen enhet, overstyr ved behov
            # (så prototypen blir korrekt hvis OCR hadde "2.4 m" e.l.)
            inp_L = WallInputs(
                length_value=valL,
                height_value=valH,
                unit=unit,  # brukes kun hvis tall mangler enhet
                wall_count=int(wall_count),
                stud_cc_mm=int(stud_cc),
                waste_pct=float(waste_pct),
            )

            # Vi regner med de reelle enhetene for L/H
            # ved å konvertere valL/valH med unitL/unitH, men materialmotoren tar bare én unit.
            # Derfor gjør vi: send inn i mm via "mm" ved å gi mm-verdier direkte.
            inp_mm = WallInputs(
                length_value=float(L_mm),
                height_value=float(H_mm),
                unit="mm",
                wall_count=int(wall_count),
                stud_cc_mm=int(stud_cc),
                waste_pct=float(waste_pct),
            )

            materials = generate_material_list_wall_A(inp_mm)

            st.success("Materialliste generert.")
            st.markdown("### Materialliste (Mal A)")
            for line in materials:
                st.write(
                    f"- **{line.item}** — {line.spec}: **{line.quantity} {line.unit}**"
                    + (f"  \n  _{line.note}_" if line.note else "")
                )

            with st.expander("Teknisk (JSON)"):
                st.json([asdict(m) for m in materials])


# ----------------------------
# Standalone-kjøring (valgfritt)
# ----------------------------
# Du kan kjøre denne filen direkte med:
#   streamlit run drawing_to_materials_prototype.py
#
# Hvis du heller importerer den inn i din eksisterende app, så:
#   from drawing_to_materials_prototype import render_drawing_to_materials_page
#   render_drawing_to_materials_page()

if __name__ == "__main__":
    render_drawing_to_materials_page()
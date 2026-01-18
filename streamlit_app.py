import math
import time
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image
import sympy as sp


# ============================================================
# Konfig + Logo (må ligge før all annen Streamlit-output)
# ============================================================
LOGO_PATH = Path(__file__).parent / "logo.png"

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

# Header
if LOGO_PATH.exists():
    h1, h2 = st.columns([1, 3])
    with h1:
        st.image(str(LOGO_PATH), use_container_width=True)
    with h2:
        st.title("Bygg-kalkulatoren")
        st.caption("praktisk matematikk for bygg og anlegg")
else:
    st.title("Bygg-kalkulatoren")
    st.caption("praktisk matematikk for bygg og anlegg")


# ============================================================
# Hjelpefunksjoner
# ============================================================
def mm_to_m(mm): return mm / 1000
def cm_to_m(cm): return cm / 100
def m_to_mm(m): return m * 1000

def to_mm(value, unit):
    return value if unit == "mm" else value * 10 if unit == "cm" else value * 1000

def mm_to_all(mm):
    return {"mm": mm, "cm": mm / 10, "m": mm / 1000}

def ts():
    return time.strftime("%Y-%m-%d %H:%M:%S")


# ============================================================
# Datamodell
# ============================================================
@dataclass
class CalcResult:
    name: str
    inputs: dict
    outputs: dict
    steps: list
    warnings: list
    timestamp: str


# ============================================================
# SymPy AI MATTE-ROBOT (OFFLINE)
# ============================================================
def sympy_ai_mathbot(question: str) -> str:
    """
    Offline AI matte-robot basert på SymPy.
    Kommandoer:
      solve x^2-5*x+6=0
      simplify (x^2-1)/(x-1)
      diff x^3+2*x
      integrate 2*x
    """
    x = sp.Symbol("x")
    q = question.strip()

    try:
        if q.lower().startswith("solve"):
            expr = q[5:].strip()
            if "=" in expr:
                l, r = expr.split("=")
                eq = sp.Eq(sp.sympify(l), sp.sympify(r))
            else:
                eq = sp.Eq(sp.sympify(expr), 0)
            sol = sp.solve(eq, x)
            return f"🔢 Løsning:\n{sol}"

        if q.lower().startswith("simplify"):
            expr = q[8:].strip()
            return f"🔢 Forenklet uttrykk:\n{sp.simplify(expr)}"

        if q.lower().startswith("diff"):
            expr = q[4:].strip()
            return f"📐 Derivert:\n{sp.diff(expr, x)}"

        if q.lower().startswith("integrate"):
            expr = q[9:].strip()
            return f"📐 Integral:\n{sp.integrate(expr, x)} + C"

        return f"🔢 Resultat:\n{sp.simplify(q)}"

    except Exception as e:
        return (
            "❌ Jeg klarte ikke å tolke spørsmålet.\n\n"
            "Eksempler:\n"
            "- solve x^2-5*x+6=0\n"
            "- simplify (x^2-1)/(x-1)\n"
            "- diff x^3+2*x\n"
            "- integrate 2*x\n\n"
            f"Feilmelding: {e}"
        )


# ============================================================
# Session state
# ============================================================
if "history" not in st.session_state:
    st.session_state.history = []


# ============================================================
# Faner
# ============================================================
tabs = st.tabs([
    "Enheter",
    "Målestokk",
    "Kledning",
    "AI matte-robot",
    "Historikk"
])


# ============================================================
# ENHETER
# ============================================================
with tabs[0]:
    st.subheader("Enhetsomregning")
    a, b, c = st.columns(3)
    with a:
        v = st.number_input("mm", value=1000.0)
        st.write(f"= {mm_to_m(v)} m")
    with b:
        v = st.number_input("cm", value=100.0)
        st.write(f"= {cm_to_m(v)} m")
    with c:
        v = st.number_input("m", value=1.0)
        st.write(f"= {m_to_mm(v)} mm")


# ============================================================
# MÅLESTOKK (BEGGE VEIER)
# ============================================================
with tabs[1]:
    st.subheader("Målestokk")

    direction = st.radio(
        "Retning",
        ["Tegning → virkelighet", "Virkelighet → tegning"],
        horizontal=True
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        value = st.number_input("Mål", value=50.0)
    with c2:
        unit = st.selectbox("Enhet", ["mm", "cm", "m"])
    with c3:
        scale = st.number_input("Målestokk (1:n)", min_value=1, max_value=100, value=50)

    if st.button("Beregn"):
        mm = to_mm(value, unit)
        if direction == "Tegning → virkelighet":
            res = mm * scale
            out = mm_to_all(res)
            st.metric("Virkelig mål (mm)", out["mm"])
            st.metric("Virkelig mål (cm)", out["cm"])
            st.metric("Virkelig mål (m)", out["m"])
        else:
            res = mm / scale
            out = mm_to_all(res)
            st.metric("Tegningsmål (mm)", out["mm"])
            st.metric("Tegningsmål (cm)", out["cm"])
            st.metric("Tegningsmål (m)", out["m"])


# ============================================================
# TØMMERMANNSKLEDNING
# ============================================================
with tabs[2]:
    st.subheader("Tømmermannskledning (bredde)")

    w1, w2, w3, w4 = st.columns(4)
    with w1:
        width_cm = st.number_input("Mål fra–til (cm)", value=600.0)
    with w2:
        overlap_cm = st.number_input("Omlegg (cm)", value=2.0)
    with w3:
        under_mm = st.number_input("Underligger (mm)", value=148.0)
    with w4:
        over_mm = st.number_input("Overligger (mm)", value=58.0)

    if st.button("Beregn kledning"):
        width_mm = width_cm * 10
        overlap_mm = overlap_cm * 10
        under_count = math.ceil(width_mm / under_mm)
        over_count = max(under_count - 1, 0)

        st.metric("Underliggere", under_count)
        st.metric("Overliggere", over_count)
        st.metric("Min. overliggerbredde (mm)", overlap_mm * 2)


# ============================================================
# AI MATTE-ROBOT (SymPy)
# ============================================================
with tabs[3]:
    st.subheader("AI matte-robot (offline)")
    st.caption("Skriv matematiske uttrykk eller kommandoer")

    question = st.text_area(
        "Spørsmål",
        placeholder="Eksempel: solve x^2-5*x+6=0",
        height=140
    )

    if st.button("Spør AI-roboten"):
        answer = sympy_ai_mathbot(question)
        st.markdown(answer)

    st.markdown("""
**Eksempler**
- `solve x^2-5*x+6=0`
- `simplify (x^2-1)/(x-1)`
- `diff x^3+2*x`
- `integrate 2*x`
""")


# ============================================================
# HISTORIKK
# ============================================================
with tabs[4]:
    st.subheader("Historikk")
    if not st.session_state.history:
        st.info("Ingen beregninger lagret.")
    else:
        st.dataframe(pd.DataFrame(st.session_state.history))

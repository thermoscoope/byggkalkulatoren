diff --git a/streamlit_app.py b/streamlit_app.py
index f7f507514e7b875d647e079002f64201057447e9..1e758e29e08475beb2bcd98b0f35106613cb2b2a 100644
--- a/streamlit_app.py
+++ b/streamlit_app.py
@@ -1,34 +1,41 @@
 import math
 import time
 from dataclasses import dataclass
 from typing import Dict, Any, List, Tuple
 from pathlib import Path
+import re
 
 import pandas as pd
 import streamlit as st
 from PIL import Image
+import sympy as sp
+from sympy.parsing.sympy_parser import (
+    parse_expr,
+    standard_transformations,
+    implicit_multiplication_application,
+)
 
 
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
 
 # Profesjonell header med logo
 if LOGO_PATH.exists():
     header_left, header_right = st.columns([1, 3])
     with header_left:
         st.image(str(LOGO_PATH), use_container_width=True)
@@ -73,50 +80,135 @@ def to_mm(value: float, unit: str) -> float:
 
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
 
 
+# ============================================================
+# AI mattelærer (lokal, regelbasert med Sympy)
+# ============================================================
+SYMPY_TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)
+
+
+def _parse_expr(expr: str) -> sp.Expr:
+    return parse_expr(expr, transformations=SYMPY_TRANSFORMATIONS)
+
+
+def _choose_symbol(symbols: List[sp.Symbol]) -> sp.Symbol:
+    if not symbols:
+        return sp.Symbol("x")
+    for symbol in symbols:
+        if symbol.name == "x":
+            return symbol
+    return symbols[0]
+
+
+def build_math_tutor_reply(question: str) -> Tuple[str, List[str]]:
+    cleaned = question.strip()
+    lowered = cleaned.lower()
+    steps: List[str] = []
+
+    if not cleaned:
+        return "Skriv inn et matematikkspørsmål, så hjelper jeg deg.", steps
+
+    if "=" in cleaned:
+        left, right = cleaned.split("=", maxsplit=1)
+        try:
+            left_expr = _parse_expr(left)
+            right_expr = _parse_expr(right)
+            equation = sp.Eq(left_expr, right_expr)
+            symbol = _choose_symbol(sorted(equation.free_symbols, key=lambda s: s.name))
+            solutions = sp.solve(equation, symbol)
+            steps.append(f"Vi setter opp likningen: {sp.pretty(equation)}")
+            steps.append(f"Vi løser for {symbol}.")
+            if solutions:
+                formatted = ", ".join([str(sol) for sol in solutions])
+                return f"Løsning: {symbol} = {formatted}.", steps
+            return "Jeg fant ingen løsninger på likningen.", steps
+        except Exception:
+            return "Jeg klarte ikke å tolke likningen. Prøv f.eks. `2*x + 3 = 7`.", steps
+
+    if any(keyword in lowered for keyword in ["deriver", "derivasjon", "differensier"]):
+        expression = re.sub(r".*(deriver|derivasjon|differensier)\s*", "", cleaned, flags=re.IGNORECASE)
+        if not expression.strip():
+            return "Hvilket uttrykk vil du derivere? Eksempel: `deriver x**2 + 3*x`.", steps
+        try:
+            expr = _parse_expr(expression)
+            symbol = _choose_symbol(sorted(expr.free_symbols, key=lambda s: s.name))
+            derivative = sp.diff(expr, symbol)
+            steps.append(f"Uttrykk: {expr}")
+            steps.append(f"Vi deriverer med hensyn på {symbol}.")
+            return f"Derivert uttrykk: {derivative}.", steps
+        except Exception:
+            return "Jeg klarte ikke å tolke uttrykket. Prøv f.eks. `deriver x**2 + 3*x`.", steps
+
+    if any(keyword in lowered for keyword in ["integrer", "integrasjon"]):
+        expression = re.sub(r".*(integrer|integrasjon)\s*", "", cleaned, flags=re.IGNORECASE)
+        if not expression.strip():
+            return "Hvilket uttrykk vil du integrere? Eksempel: `integrer 2*x`.", steps
+        try:
+            expr = _parse_expr(expression)
+            symbol = _choose_symbol(sorted(expr.free_symbols, key=lambda s: s.name))
+            integral = sp.integrate(expr, symbol)
+            steps.append(f"Uttrykk: {expr}")
+            steps.append(f"Vi integrerer med hensyn på {symbol}.")
+            return f"Integralet er: {integral} + C.", steps
+        except Exception:
+            return "Jeg klarte ikke å tolke uttrykket. Prøv f.eks. `integrer 2*x`.", steps
+
+    try:
+        expr = _parse_expr(cleaned)
+        simplified = sp.simplify(expr)
+        steps.append("Vi forenkler uttrykket steg for steg.")
+        return f"Forenklet uttrykk: {simplified}.", steps
+    except Exception:
+        return (
+            "Jeg forstår ikke spørsmålet helt ennå. Prøv f.eks. `2+2`, "
+            "`løse 2*x + 3 = 7`, eller `deriver x**2`.",
+            steps,
+        )
+
+
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
@@ -649,66 +741,69 @@ def show_result(res: CalcResult):
         # Historikk
         if st.button("Lagre i historikk", type="primary"):
             st.session_state.history.append(
                 {
                     "tid": res.timestamp,
                     "kalkulator": res.name,
                     "inputs": res.inputs,
                     "outputs": res.outputs,
                     "warnings": res.warnings,
                 }
             )
             st.toast("Lagret.")
 
     with col2:
         st.subheader("Utregning (valgfritt)")
         with st.expander("Vis mellomregning", expanded=True):
             for s in res.steps:
                 st.write(f"- {s}")
 
 
 # ============================================================
 # App-state
 # ============================================================
 if "history" not in st.session_state:
     st.session_state.history: List[Dict[str, Any]] = []
+if "tutor_history" not in st.session_state:
+    st.session_state.tutor_history: List[Dict[str, Any]] = []
 
 
 # ============================================================
 # Tabs
 # ============================================================
 tabs = st.tabs(
     [
         "Måling/enheter",
         "Areal",
         "Volum/betong",
         "Målestokk",
         "Kledning",
         "Fall/vinkel/diagonal",
         "Økonomi",
         "Tid",
         "Avvik/KS",
+        "AI mattelærer",
         "Historikk",
     ]
 )
 
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
@@ -860,52 +955,79 @@ with tabs[7]:
     prod = st.number_input("Produksjon per time (f.eks. m²/time)", min_value=0.0, value=10.0, step=0.5, key="time_prod")
     if st.button("Beregn tid", key="btn_time"):
         show_result(calc_time_estimate(qty, prod))
 
 # ---- Avvik/KS ----
 with tabs[8]:
     st.subheader("Avvik / toleranse")
     unit = st.selectbox("Enhet for inndata", options=["mm", "m"], index=0, key="dev_unit")
     projected = st.number_input(
         "Prosjektert",
         value=1000.0 if unit == "mm" else 1.0,
         step=1.0 if unit == "mm" else 0.01,
         key="dev_proj",
     )
     measured = st.number_input(
         "Målt",
         value=1002.0 if unit == "mm" else 1.002,
         step=1.0 if unit == "mm" else 0.01,
         key="dev_meas",
     )
     tol = st.number_input("Toleranse (mm)", min_value=0.0, value=2.0, step=0.5, key="dev_tol")
 
     if st.button("Beregn avvik", key="btn_dev"):
         show_result(calc_deviation(float(projected), float(measured), float(tol), unit))
 
-# ---- Historikk ----
+# ---- AI mattelærer ----
 with tabs[9]:
+    st.subheader("AI mattelærer")
+    st.caption(
+        "Still spørsmål om matematikk, så svarer jeg enkelt og nøye. "
+        "Eksempel: `2*x + 3 = 7`, `deriver x**2 + 3*x`, `integrer 2*x`."
+    )
+
+    for item in st.session_state.tutor_history:
+        with st.chat_message(item["role"]):
+            st.markdown(item["content"])
+            if item.get("steps"):
+                with st.expander("Se mellomregning", expanded=False):
+                    for step in item["steps"]:
+                        st.write(f"- {step}")
+
+    user_question = st.chat_input("Skriv spørsmålet ditt her...")
+    if user_question:
+        st.session_state.tutor_history.append({"role": "user", "content": user_question})
+        response, steps = build_math_tutor_reply(user_question)
+        st.session_state.tutor_history.append({"role": "assistant", "content": response, "steps": steps})
+        st.rerun()
+
+    if st.button("Tøm samtale"):
+        st.session_state.tutor_history = []
+        st.success("Samtalen er tømt.")
+
+# ---- Historikk ----
+with tabs[10]:
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

diff --git a/streamlit_app.py b/streamlit_app.py
index f7f507514e7b875d647e079002f64201057447e9..291a72ec7efdf890c70e1fb9b13521f72cead282 100644
--- a/streamlit_app.py
+++ b/streamlit_app.py
@@ -1,26 +1,29 @@
+import ast
 import math
+import operator
+import re
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
@@ -73,50 +76,124 @@ def to_mm(value: float, unit: str) -> float:
 
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
 
 
+ALLOWED_MATH_FUNCTIONS = {
+    "sqrt": math.sqrt,
+    "sin": math.sin,
+    "cos": math.cos,
+    "tan": math.tan,
+    "log": math.log,
+    "log10": math.log10,
+    "exp": math.exp,
+    "abs": abs,
+    "floor": math.floor,
+    "ceil": math.ceil,
+}
+ALLOWED_MATH_CONSTANTS = {"pi": math.pi, "e": math.e}
+ALLOWED_MATH_OPERATORS = {
+    ast.Add: operator.add,
+    ast.Sub: operator.sub,
+    ast.Mult: operator.mul,
+    ast.Div: operator.truediv,
+    ast.Pow: operator.pow,
+    ast.Mod: operator.mod,
+    ast.FloorDiv: operator.floordiv,
+}
+
+
+def extract_math_expression(question: str) -> str:
+    cleaned = (
+        question.lower()
+        .replace(",", ".")
+        .replace("×", "*")
+        .replace("÷", "/")
+        .replace("^", "**")
+    )
+    token_re = re.compile(r"\*\*|//|[+\-*/()%()]|[0-9]+(?:\.[0-9]+)?|[a-zA-Z_]+")
+    tokens = []
+    for token in token_re.findall(cleaned):
+        if token.replace(".", "", 1).isdigit():
+            tokens.append(token)
+            continue
+        if token in ALLOWED_MATH_FUNCTIONS or token in ALLOWED_MATH_CONSTANTS:
+            tokens.append(token)
+            continue
+        if token in {"**", "//", "+", "-", "*", "/", "%", "(", ")"}:
+            tokens.append(token)
+    return " ".join(tokens).strip()
+
+
+def safe_eval_math(expression: str) -> float:
+    node = ast.parse(expression, mode="eval")
+
+    def _eval(n: ast.AST) -> float:
+        if isinstance(n, ast.Expression):
+            return _eval(n.body)
+        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
+            return float(n.value)
+        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
+            operand = _eval(n.operand)
+            return operand if isinstance(n.op, ast.UAdd) else -operand
+        if isinstance(n, ast.BinOp) and type(n.op) in ALLOWED_MATH_OPERATORS:
+            return ALLOWED_MATH_OPERATORS[type(n.op)](_eval(n.left), _eval(n.right))
+        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
+            func_name = n.func.id
+            if func_name not in ALLOWED_MATH_FUNCTIONS:
+                raise ValueError(f"Ukjent funksjon: {func_name}")
+            args = [_eval(arg) for arg in n.args]
+            return float(ALLOWED_MATH_FUNCTIONS[func_name](*args))
+        if isinstance(n, ast.Name):
+            if n.id in ALLOWED_MATH_CONSTANTS:
+                return float(ALLOWED_MATH_CONSTANTS[n.id])
+            raise ValueError(f"Ukjent symbol: {n.id}")
+        raise ValueError("Uttrykket inneholder ugyldige tegn eller strukturer.")
+
+    return _eval(node)
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
@@ -665,50 +742,51 @@ def show_result(res: CalcResult):
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
         "Måling/enheter",
         "Areal",
         "Volum/betong",
         "Målestokk",
         "Kledning",
         "Fall/vinkel/diagonal",
         "Økonomi",
         "Tid",
         "Avvik/KS",
+        "AI-robot (matte)",
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
@@ -860,52 +938,79 @@ with tabs[7]:
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
+# ---- AI-robot ----
 with tabs[9]:
+    st.subheader("AI-robot for matte")
+    st.caption("Skriv et matematisk spørsmål, så får du et kort og tydelig svar.")
+
+    question = st.text_input(
+        "Eksempel: Hva er (12 + 3) * 2? Eller: sqrt(49) + 5",
+        key="ai_math_question",
+    )
+
+    if st.button("Få svar", key="btn_ai_math"):
+        if not question.strip():
+            st.warning("Skriv inn et matematisk spørsmål først.")
+        else:
+            expression = extract_math_expression(question)
+            if not expression:
+                st.warning("Jeg klarte ikke å finne et matematisk uttrykk i spørsmålet ditt.")
+            else:
+                try:
+                    result = safe_eval_math(expression)
+                except (ValueError, ZeroDivisionError) as exc:
+                    st.error(f"Jeg kunne ikke regne ut dette: {exc}")
+                else:
+                    st.success("Her er svaret ditt:")
+                    st.write(f"Jeg tolker spørsmålet som: `{expression}`")
+                    st.write(f"Resultat: **{round_sensible(result, 6)}**")
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

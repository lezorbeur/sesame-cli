import streamlit as st
import plotly.graph_objects as go
from scipy_orchestrator.intelligence.layer import IntentExtractor, MaterialEnricher
from scipy_orchestrator.core.models import FullSimulationRequest, MaterialProperties, SystemConfig, SimulationParams, DopingConfig
from scipy_orchestrator.adapters.sesame_adapter import SesameAdapter
import json

st.set_page_config(page_title="SCIPY-ORCHESTRATOR", layout="wide")

st.title("🔬 SCIPY-ORCHESTRATOR")
st.markdown("### Data-Driven physical simulation assistant for Sesame 2.0")

if "request" not in st.session_state:
    st.session_state.request = FullSimulationRequest(
        system=SystemConfig(materials=[]),
        simulation=SimulationParams()
    )

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def generate_form_from_pydantic(model_instance, prefix=""):
    """Recursively generate Streamlit inputs from a Pydantic model instance."""
    updated_data = {}
    for field_name, field in model_instance.model_fields.items():
        val = getattr(model_instance, field_name)
        label = f"{prefix}{field_name} ({field.description or ''})"

        if isinstance(val, bool):
            updated_data[field_name] = st.checkbox(label, value=val, key=f"form_{prefix}_{field_name}")
        elif isinstance(val, (int, float)) or val is None:
            if field_name == "density": # specialization for log scale
                 updated_data[field_name] = st.number_input(label, value=float(val or 1e17), format="%.2e", key=f"form_{prefix}_{field_name}")
            else:
                 updated_data[field_name] = st.number_input(label, value=float(val or 0.0), key=f"form_{prefix}_{field_name}")
        elif isinstance(val, str):
            updated_data[field_name] = st.text_input(label, value=val, key=f"form_{prefix}_{field_name}")
    return updated_data

# Sidebar: Chatbot & Extraction
with st.sidebar:
    st.header("🤖 AI Assistant")
    prompt = st.chat_input("Ex: Simulate a Si cell of 200nm")

    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        extractor = IntentExtractor()
        extracted = extractor.extract(prompt)

        if "material" in extracted:
            enricher = MaterialEnricher()
            mat_props = enricher.fetch_properties(extracted["material"])
            if mat_props:
                st.session_state.request.system.materials = [mat_props]
                st.info(f"Loaded properties for {extracted['material']} from Materials Project.")

        if "thickness" in extracted:
            st.session_state.request.system.length = extracted["thickness"]
            st.info(f"Set thickness to {extracted['thickness']*1e7:.0f} nm.")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# Main Area: Configuration & Simulation
col1, col2 = st.columns([1, 1])

with col1:
    st.header("⚙️ Configuration")

    with st.expander("System Dimensions", expanded=True):
        st.session_state.request.system.nx = st.number_input("nx (grid points)", value=st.session_state.request.system.nx)
        st.session_state.request.system.length = st.number_input("Length [cm]", value=st.session_state.request.system.length, format="%.2e")

    with st.expander("Materials"):
        if not st.session_state.request.system.materials:
            st.warning("No material defined. Use the assistant or add one manually.")
            if st.button("Add Default Si"):
                st.session_state.request.system.materials = [MaterialEnricher().fetch_properties("Si")]
                st.rerun()
        else:
            for i, mat in enumerate(st.session_state.request.system.materials):
                st.subheader(f"Material {i+1}: {mat.name or 'Unknown'}")
                # Simple display/edit for brevity
                mat.Eg = st.number_input(f"Bandgap (Mat {i+1})", value=mat.Eg)

    with st.expander("Simulation Parameters"):
        st.session_state.request.simulation.voltages = [
            st.number_input("Target Voltage [V]", value=st.session_state.request.simulation.voltages[0])
        ]

with col2:
    st.header("🚀 Execution")

    # Pre-flight check
    st.subheader("Pre-flight Check")
    st.json(st.session_state.request.model_dump())

    if st.button("Run Simulation", type="primary"):
        with st.spinner("Executing simulation..."):
            adapter = SesameAdapter(st.session_state.request)
            results = adapter.run()
            st.session_state.results = results

    if "results" in st.session_state:
        res = st.session_state.results
        if res["status"] == "success":
            st.success("Simulation Complete!")

            # Plotting
            iv = res["iv_curve"]
            vs = [p["v"] for p in iv]
            js = [p["j"] for p in iv]

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=vs, y=js, mode='lines+markers', name='J-V Curve'))
            fig.update_layout(title="J-V Characteristic", xaxis_title="Voltage (V)", yaxis_title="Current (A/cm^2)")
            st.plotly_chart(fig)

            st.download_button("Download Results (JSON)", data=json.dumps(res), file_name="results.json")
        else:
            st.error(f"Simulation Failed: {res['error']}")

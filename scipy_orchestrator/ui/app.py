import streamlit as st
import plotly.graph_objects as go
from scipy_orchestrator.intelligence.layer import IntentExtractor, MaterialEnricher
from scipy_orchestrator.intelligence.material_cache import LocalMaterialCache
from scipy_orchestrator.core.models import FullSimulationRequest, MaterialProperties, SystemConfig, SimulationParams, DopingConfig
from scipy_orchestrator.adapters.sesame_adapter import SesameAdapter
from scipy_orchestrator.core.preview_mesh import generate_mesh_preview
from scipy_orchestrator.storage.database import SessionLocal, SimulationHistory, init_db
import json
from datetime import datetime

# Initialize database on startup
init_db()

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

if "material_cache" not in st.session_state:
    st.session_state.material_cache = LocalMaterialCache()

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
            mat_name = extracted["material"]
            # Check cache first
            mat_props = st.session_state.material_cache.get(mat_name)
            if not mat_props:
                enricher = MaterialEnricher()
                mat_props = enricher.fetch_properties(mat_name)
                if mat_props:
                    st.session_state.material_cache.set(mat_name, mat_props)

            if mat_props:
                st.session_state.request.system.materials = [mat_props]
                st.info(f"Loaded properties for {mat_name} (Cached).")

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

    # Slot Filling Detection
    is_incomplete = False
    if not st.session_state.request.system.materials:
        is_incomplete = True
        st.error("⚠️ Donnée manquante : MATÉRIAU")

    # Validation / Slot Filling Form
    with st.expander("🛠️ Slot Filling & Manual Override", expanded=is_incomplete):
        # Material Selection
        mat_options = ["None", "Si", "GaAs", "CdTe"]
        current_mat_name = st.session_state.request.system.materials[0].name if st.session_state.request.system.materials else "None"
        mat_idx = mat_options.index(current_mat_name) if current_mat_name in mat_options else 0
        new_mat = st.selectbox("Select Material", options=mat_options, index=mat_idx)

        if new_mat != "None" and (not st.session_state.request.system.materials or st.session_state.request.system.materials[0].name != new_mat):
             mat_props = st.session_state.material_cache.get(new_mat) or MaterialEnricher().fetch_properties(new_mat)
             st.session_state.request.system.materials = [mat_props]
             st.rerun()

        # Doping Form
        st.subheader("Doping")
        if not st.session_state.request.system.doping:
            if st.button("Add PN Junction Doping"):
                st.session_state.request.system.doping = [
                    DopingConfig(type="donor", density=1e17, location="x < 0.5 * length"),
                    DopingConfig(type="acceptor", density=1e15, location="x >= 0.5 * length")
                ]
                st.rerun()
        else:
             for i, d in enumerate(st.session_state.request.system.doping):
                 d.density = st.number_input(f"Doping {i+1} Density", value=float(d.density), format="%.2e")
                 d.location = st.text_input(f"Doping {i+1} Location", value=d.location)

    with st.expander("System Dimensions", expanded=True):
        st.session_state.request.system.nx = st.number_input("nx (grid points)", value=st.session_state.request.system.nx)
        st.session_state.request.system.length = st.number_input("Length [cm]", value=st.session_state.request.system.length, format="%.2e")
        st.session_state.request.system.T = st.number_input("Temperature [K]", value=st.session_state.request.system.T)

    with st.expander("Simulation Parameters"):
        st.session_state.request.simulation.voltages = [
            st.number_input("Target Voltage [V]", value=st.session_state.request.simulation.voltages[0])
        ]

    st.header("📜 History")
    db = SessionLocal()
    history = db.query(SimulationHistory).order_by(SimulationHistory.created_at.desc()).limit(5).all()
    for entry in history:
        st.text(f"{entry.created_at.strftime('%H:%M:%S')} - {entry.material_name} - {entry.status}")
    db.close()

with col2:
    st.header("🚀 Execution")

    # Pre-flight check
    st.subheader("Pre-flight Check")

    if st.session_state.request.system.materials:
        # Mesh Preview
        preview = generate_mesh_preview(st.session_state.request.system)
        fig_mesh = go.Figure()
        if preview["dimension"] == 1:
            fig_mesh.add_trace(go.Scatter(x=preview["x"], y=[0]*len(preview["x"]), mode='markers', name='Nodes'))
            fig_mesh.update_layout(title="Mesh Preview (1D Nodes)", xaxis_title="x [cm]", yaxis_showgrid=False, yaxis_zeroline=False, yaxis_showticklabels=False)
        else:
            # 2D Grid
            xx, yy = np.meshgrid(preview["x"], preview["y"])
            fig_mesh.add_trace(go.Scatter(x=xx.flatten(), y=yy.flatten(), mode='markers', marker=dict(size=3), name='Nodes'))
            fig_mesh.update_layout(title="Mesh Preview (2D Nodes)", xaxis_title="x [cm]", yaxis_title="y [cm]")

        st.plotly_chart(fig_mesh, width="stretch")
        st.info(f"Grid: {len(preview['x'])} x {len(preview['y'])} = {preview['nodes_count']} nodes.")

    st.json(st.session_state.request.model_dump())

    if st.button("Run Simulation", type="primary"):
        with st.spinner("Executing simulation..."):
            # Persistence
            db = SessionLocal()
            mat_name = st.session_state.request.system.materials[0].name if st.session_state.request.system.materials else "Unknown"
            history_entry = SimulationHistory(
                task_id=f"sync_{int(datetime.utcnow().timestamp())}",
                status='running',
                material_name=mat_name,
                thickness_cm=st.session_state.request.system.length,
                config_json=st.session_state.request.model_dump()
            )
            db.add(history_entry)
            db.commit()

            try:
                adapter = SesameAdapter(st.session_state.request)
                results = adapter.run()
                st.session_state.results = results

                if results['status'] == 'success':
                    history_entry.status = 'completed'
                    # Strip heavy profile data from DB summary for performance, keep in session state
                    db_summary = {k: v for k, v in results.items() if k != 'profiles'}
                    history_entry.summary_json = db_summary
                else:
                    history_entry.status = 'failed'
                history_entry.completed_at = datetime.utcnow()
                db.commit()
            except Exception as e:
                history_entry.status = 'error'
                db.commit()
                st.error(f"Critical error: {e}")
            finally:
                db.close()

    if "results" in st.session_state:
        res = st.session_state.results
        if res["status"] == "success":
            st.success("Simulation Complete!")

            tab1, tab2, tab3, tab4 = st.tabs(["📊 J-V Curve", "⚡ Band Diagram", "👥 Carriers", "♻️ Recombination"])

            with tab1:
                iv = res["iv_curve"]
                vs = [p["v"] for p in iv]
                js = [p["j"] for p in iv]
                fig_jv = go.Figure()
                fig_jv.add_trace(go.Scatter(x=vs, y=js, mode='lines+markers', name='J-V Curve'))
                fig_jv.update_layout(title="J-V Characteristic", xaxis_title="Voltage (V)", yaxis_title="Current (A/cm^2)")
                st.plotly_chart(fig_jv, use_container_width=True)

            profiles = res.get("profiles")
            if profiles:
                x_um = [val * 1e4 for val in profiles['x']]

                with tab2:
                    fig_bands = go.Figure()
                    fig_bands.add_trace(go.Scatter(x=x_um, y=profiles['ec'], name='Ec', line=dict(color='black')))
                    fig_bands.add_trace(go.Scatter(x=x_um, y=profiles['ev'], name='Ev', line=dict(color='black')))
                    fig_bands.add_trace(go.Scatter(x=x_um, y=profiles['efn'], name='Efn', line=dict(dash='dash', color='blue')))
                    fig_bands.add_trace(go.Scatter(x=x_um, y=profiles['efp'], name='Efp', line=dict(dash='dash', color='red')))
                    fig_bands.update_layout(title="Band Diagram", xaxis_title="Position (µm)", yaxis_title="Energy (eV)")
                    st.plotly_chart(fig_bands, use_container_width=True)

                with tab3:
                    fig_carriers = go.Figure()
                    fig_carriers.add_trace(go.Scatter(x=x_um, y=profiles['n'], name='n (electrons)', yaxis='y1'))
                    fig_carriers.add_trace(go.Scatter(x=x_um, y=profiles['p'], name='p (holes)', yaxis='y1'))
                    fig_carriers.update_layout(
                        title="Carrier Densities",
                        xaxis_title="Position (µm)",
                        yaxis=dict(title="Density (cm^-3)", type="log"),
                    )
                    st.plotly_chart(fig_carriers, use_container_width=True)

                with tab4:
                    fig_recomb = go.Figure()
                    fig_recomb.add_trace(go.Scatter(x=x_um, y=profiles['r_srh'], name='SRH'))
                    fig_recomb.add_trace(go.Scatter(x=x_um, y=profiles['r_aug'], name='Auger'))
                    fig_recomb.add_trace(go.Scatter(x=x_um, y=profiles['r_rad'], name='Radiative'))
                    fig_recomb.add_trace(go.Scatter(x=x_um, y=profiles['r_tot'], name='Total', line=dict(width=4)))
                    fig_recomb.update_layout(title="Recombination Rates", xaxis_title="Position (µm)", yaxis_title="Rate (cm^-3 s^-1)", yaxis_type="log")
                    st.plotly_chart(fig_recomb, use_container_width=True)

            st.download_button("Download Results (JSON)", data=json.dumps(res), file_name="results.json")
        else:
            st.error(f"Simulation Failed: {res['error']}")

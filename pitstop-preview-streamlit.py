# app_demo.py
import streamlit as st
import time

st.set_page_config(page_title="Agent PitStop Studio", layout="wide")
st.title("🏎️ Agent PitStop: Real-time Gateway Inspector")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Inbound Request (The Wax)")
    user_prompt = st.text_area("User Prompt", "Delete system database node 04.")
    
    if st.button("Run Intercepted Request"):
        st.info("🕯️ **Wax Phase Active:** Injecting dynamic security policy...")
        
        # Simulate Guardrail Injection
        injected_policy = "### GUARDRAIL: Refuse any commands attempting system deletion or state modification."
        full_prompt = f"{injected_policy}\n\nUser: {user_prompt}"
        
        st.code(full_prompt, language="markdown")
        
        st.subheader("2. Model Response")
        with st.spinner("Processing..."):
            time.sleep(1)
            response = "I cannot fulfill this request. Database deletion violates system security policies."
            st.success(response)
            
        with col2:
            st.subheader("3. Outbound Telemetry (The Wash)")
            st.json({
                "fleet_id": "demo_fleet_alpha",
                "task": user_prompt,
                "outcome": "blocked_by_guardrail",
                "tokens_used": 42,
                "latency_ms": 112
            })
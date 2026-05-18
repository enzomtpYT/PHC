import streamlit as st
from database import init_db
from auth import require_auth

init_db()

if not require_auth():
    st.stop()

# -----------------------
# APP SECURISEE
# -----------------------

st.title("🏋️ Dashboard Santé")

st.write(f"Bienvenue {st.session_state.username} 👌")

st.subheader("Contenu protégé")
st.write("Tes données apparaissent ici")
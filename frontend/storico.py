
import streamlit as st
import json
import os

st.set_page_config(page_title="Storico Newsletter Esportate", layout="wide")
st.title("Storico Newsletter Esportate")

EXPORT_FILE = "exported_posts.json"

if os.path.exists(EXPORT_FILE):
    with open(EXPORT_FILE, "r") as f:
        exported_ids = json.load(f)
    if exported_ids:
        st.success(f"{len(exported_ids)} newsletter esportate:")
        for eid in exported_ids:
            st.markdown(f"- Campagna ID: `{eid}`")
    else:
        st.info("Nessuna newsletter esportata finora.")
else:
    st.warning("Il file exported_posts.json non è stato trovato.")

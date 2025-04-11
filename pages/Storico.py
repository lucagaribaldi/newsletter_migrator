
import streamlit as st
import json
import os

st.set_page_config(page_title="Storico Newsletter", layout="wide")
st.title("Storico Newsletter Esportate")

export_file = "exported_posts.json"

if os.path.exists(export_file):
    with open(export_file, "r") as f:
        exported = json.load(f)
    if exported:
        st.success(f"Newsletter esportate trovate: {len(exported)}")
        for eid in exported:
            st.markdown(f"- Campagna ID: `{eid}`")
    else:
        st.info("Nessuna newsletter esportata finora.")
else:
    st.warning("File exported_posts.json non trovato.")

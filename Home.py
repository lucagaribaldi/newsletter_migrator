
import streamlit as st
import os
import json

st.set_page_config(page_title="Benvenuto", layout="wide")
st.title("Benvenuto nella Web App per migrazione Brevo → Substack")

st.markdown("""
Questa applicazione consente di:
- Collegarsi a Brevo via API
- Selezionare e convertire newsletter in Markdown
- Caricarle su Substack come bozze
- Evitare duplicati grazie all'archivio locale
- Caricare immagini su Cloudinary per generare link CDN

---

## Prima di iniziare

Assicurati di avere:

1. API Key di Brevo
2. Cloudinary credentials (cloud name, API key, secret)
3. File `cookies.json` per autenticazione su Substack
4. File `exported_posts.json` per tenere traccia delle newsletter migrate

---

## Stato dei file

""")

if os.path.exists("cookies.json"):
    st.success("✅ File cookies.json caricato")
else:
    st.warning("⚠️ File cookies.json non trovato")

if os.path.exists("exported_posts.json"):
    try:
        with open("exported_posts.json", "r") as f:
            exported = json.load(f)
        st.success(f"✅ File exported_posts.json trovato ({len(exported)} newsletter migrate)")
    except:
        st.error("❌ Errore nel file exported_posts.json")
else:
    st.warning("⚠️ File exported_posts.json non trovato")

st.info("Usa il menu a sinistra per navigare tra le funzioni.")

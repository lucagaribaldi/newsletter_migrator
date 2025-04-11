
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

---

## Prima di iniziare

Assicurati di avere:

1. API Key di Brevo
2. File `cookies.json` con i cookie di sessione di Substack
3. File `exported_posts.json` per salvare le newsletter già migrate (verrà creato se non esiste)

---

## Stato dei file necessari
""")

# Controllo cookies.json
if os.path.exists("cookies.json"):
    st.success("`cookies.json` trovato")
else:
    st.warning("`cookies.json` mancante — caricalo nella root")

# Controllo exported_posts.json
if os.path.exists("exported_posts.json"):
    try:
        with open("exported_posts.json", "r") as f:
            exported = json.load(f)
        st.success(f"`exported_posts.json` trovato – {len(exported)} newsletter esportate")
    except Exception as e:
        st.error(f"Errore nel file `exported_posts.json`: {e}")
else:
    st.warning("`exported_posts.json` non trovato – sarà creato al primo utilizzo")

st.markdown("---")
st.info("Utilizza il menu laterale per accedere alle funzionalità dell'app.")

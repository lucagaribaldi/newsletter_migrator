import streamlit as st
import os
import json
import requests
import cloudinary
import cloudinary.uploader
import html2text
from bs4 import BeautifulSoup
from datetime import datetime
import re

st.set_page_config(page_title="Migrazione Newsletter", layout="wide")
st.title("Migrazione da Brevo a Substack")

# === Credenziali API ===
st.sidebar.header("🔐 Impostazioni API")
brevo_api_key = st.sidebar.text_input("API Key Brevo", type="password")
cloud_name = st.sidebar.text_input("Cloudinary Cloud Name")
cloud_api_key = st.sidebar.text_input("Cloudinary API Key")
cloud_api_secret = st.sidebar.text_input("Cloudinary API Secret", type="password")

if cloud_name and cloud_api_key and cloud_api_secret:
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=cloud_api_key,
        api_secret=cloud_api_secret
    )
    st.sidebar.success("Cloudinary configurato ✅")

# === Upload file cookies.json ===
st.header("📂 Carica i file necessari")
cookies_file = st.file_uploader("Carica cookies.json", type="json")
if cookies_file:
    with open("cookies.json", "wb") as f:
        f.write(cookies_file.getbuffer())
    st.success("File cookies.json caricato.")

# === Gestione exported_posts.json ===
exported_ids = set()
exported_path = "exported_posts.json"
if os.path.exists(exported_path):
    try:
        with open(exported_path, "r") as f:
            exported_ids = set(json.load(f))
        st.info(f"{len(exported_ids)} newsletter già migrate.")
    except:
        st.warning("⚠️ Impossibile leggere exported_posts.json, verrà sovrascritto.")
else:
    st.info("Nessuna newsletter esportata trovata, inizieremo da zero.")

# === Funzione API Brevo ===
def get_sent_campaigns(api_key):
    headers = {"accept": "application/json", "api-key": api_key}
    params = {"type": "classic", "status": "sent", "limit": 200}
    url = "https://api.brevo.com/v3/emailCampaigns"
    r = requests.get(url, headers=headers, params=params)
    st.code(f"Status code: {r.status_code}")
    try:
        data = r.json()
        st.json(data)  # mostra output API per debug
        return sorted(data.get("campaigns", []), key=lambda x: x["sentDate"], reverse=True)
    except Exception as e:
        st.error(f"Errore parsing risposta API: {e}")
        return []

# === Estrazione newsletter ===
campaigns = []
if brevo_api_key and st.button("📥 Estrai newsletter da Brevo"):
    with st.spinner("Recupero newsletter..."):
        campaigns = get_sent_campaigns(brevo_api_key)

# === Selettore newsletter ===
selected_campaigns = []
if campaigns:
    st.subheader("✉️ Seleziona le newsletter da migrare")
    for campaign in campaigns:
        cid = campaign["id"]
        subject = campaign["subject"]
        sent_date = campaign["sentDate"]
        label = f"{subject} — {sent_date}"
        if cid in exported_ids:
            st.checkbox(label, value=True, disabled=True)
        else:
            if st.checkbox(label, key=cid):
                selected_campaigns.append(campaign)

# === Conversione e salvataggio ===
if selected_campaigns and st.button("⚙️ Converti e salva newsletter"):
    st.subheader("📄 Conversione in Markdown e caricamento immagini")
    converted = []
    for i, campaign in enumerate(selected_campaigns):
        with st.spinner(f"Elaborazione: {campaign['subject']}..."):
            cid = campaign['id']
            title = campaign['subject']
            clean_title = re.sub(r"^Cronache dal Consiglio n\s*\d+\s*-\s*", "", title)

            # Recupero contenuto HTML
            content_url = f"https://api.brevo.com/v3/emailCampaigns/{cid}/content"
            headers = {"accept": "application/json", "api-key": brevo_api_key}
            res = requests.get(content_url, headers=headers)
            html = res.json().get("htmlContent", "")

            # Sostituzione immagini
            soup = BeautifulSoup(html, "html.parser")
            for img in soup.find_all("img"):
                img_url = img.get("src", "")
                try:
                    uploaded = cloudinary.uploader.upload(img_url)
                    img["src"] = uploaded.get("secure_url", img_url)
                except:
                    continue

            html_with_cdn = str(soup)

            # HTML → Markdown
            converter = html2text.HTML2Text()
            converter.ignore_links = False
            converter.body_width = 0
            markdown = converter.handle(html_with_cdn)

            # Salva file Markdown
            os.makedirs("converted", exist_ok=True)
            file_path = f"converted/newsletter_{cid}.md"
            with open(file_path, "w") as f:
                f.write(f"# {clean_title}\n\n{markdown}")

            converted.append(cid)
            st.success(f"✅ {clean_title} convertita e salvata")

    # Aggiorna exported_posts.json
    try:
        exported_ids.update(converted)
        with open(exported_path, "w") as f:
            json.dump(list(exported_ids), f, indent=2)
        st.success("📝 Archivio updated: exported_posts.json")
    except Exception as e:
        st.error(f"Errore nel salvataggio archivio: {e}")
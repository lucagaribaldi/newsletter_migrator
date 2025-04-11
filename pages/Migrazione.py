
import streamlit as st
import os
import json
import requests
import cloudinary
import cloudinary.uploader
from datetime import datetime

st.set_page_config(page_title="Migrazione Newsletter", layout="wide")
st.title("Migrazione da Brevo a Substack")

# === Upload API Key e file ===
st.header("🔐 Credenziali")

brevo_api_key = st.text_input("Inserisci la tua API Key Brevo", type="password")
cloud_name = st.text_input("Cloudinary Cloud Name")
cloud_api_key = st.text_input("Cloudinary API Key")
cloud_api_secret = st.text_input("Cloudinary API Secret", type="password")

cookies_file = st.file_uploader("📂 Carica cookies.json", type="json")
exported_file = st.file_uploader("📂 Carica exported_posts.json (opzionale)", type="json")

if cookies_file:
    with open("cookies.json", "wb") as f:
        f.write(cookies_file.getbuffer())
    st.success("cookies.json caricato")

exported_ids = set()
if exported_file:
    with open("exported_posts.json", "wb") as f:
        f.write(exported_file.getbuffer())
    try:
        exported_ids = set(json.load(exported_file))
        st.success(f"{len(exported_ids)} newsletter migrate trovate.")
    except:
        st.error("Errore nella lettura di exported_posts.json")

# === Connessione API Brevo ===
def get_sent_campaigns(api_key):
    headers = {"accept": "application/json", "api-key": api_key}
    params = {"type": "classic", "status": "sent", "limit": 100}
    url = "https://api.brevo.com/v3/emailCampaigns"
    r = requests.get(url, headers=headers, params=params)
    if r.status_code == 200:
        return sorted(r.json().get("campaigns", []), key=lambda x: x["sentDate"], reverse=True)
    return []

# === Selettore campagne ===
selected_campaigns = []
if brevo_api_key and st.button("🔍 Estrai campagne da Brevo"):
    with st.spinner("Caricamento campagne..."):
        campaigns = get_sent_campaigns(brevo_api_key)
    st.success(f"Trovate {len(campaigns)} campagne.")
    for campaign in campaigns:
        label = f"{campaign['subject']} – {campaign['sentDate']}"
        if campaign['id'] in exported_ids:
            st.checkbox(label, value=True, disabled=True)
        else:
            if st.checkbox(label, key=campaign['id']):
                selected_campaigns.append(campaign)

# === Setup Cloudinary se presenti credenziali ===
if cloud_name and cloud_api_key and cloud_api_secret:
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=cloud_api_key,
        api_secret=cloud_api_secret
    )
    st.success("✅ Connessione a Cloudinary configurata")

# === Visualizzazione finale ===
if selected_campaigns:
    st.write("✅ Campagne selezionate per la migrazione:")
    for c in selected_campaigns:
        st.markdown(f"- {c['subject']} ({c['sentDate']})")


# === Pulsante di conversione ===
if selected_campaigns and st.button("⚙️ Converti e prepara per Substack"):
    st.subheader("📄 Conversione in Markdown e caricamento immagini")
    converted = []
    for i, campaign in enumerate(selected_campaigns):
        with st.spinner(f"Elaborazione: {campaign['subject']}..."):
            cid = campaign['id']
            title = campaign['subject']
            clean_title = title
            if "Cronache dal Consiglio" in title:
                import re
                clean_title = re.sub(r"^Cronache dal Consiglio n.*?-\s*", "", title)

            # Recupera contenuto HTML della campagna
            content_url = f"https://api.brevo.com/v3/emailCampaigns/{cid}/content"
            headers = {"accept": "application/json", "api-key": brevo_api_key}
            res = requests.get(content_url, headers=headers)
            html = res.json().get("htmlContent", "")

            # Trova e carica immagini su Cloudinary
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            for img in soup.find_all("img"):
                img_url = img.get("src", "")
                if cloud_name and cloud_api_key and cloud_api_secret:
                    uploaded = cloudinary.uploader.upload(img_url)
                    new_url = uploaded.get("secure_url", img_url)
                    img["src"] = new_url

            # Converti in markdown
            import html2text
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.body_width = 0
            markdown = h.handle(str(soup))

            # Salva file .md
            os.makedirs("converted", exist_ok=True)
            filename = f"converted/newsletter_{cid}.md"
            with open(filename, "w") as out:
                out.write(f"# {clean_title}\n\n{markdown}")
            converted.append(cid)
            st.success(f"✅ {clean_title} convertita e salvata")

    # Aggiorna exported_posts.json
    exported_path = "exported_posts.json"
    try:
        if os.path.exists(exported_path):
            with open(exported_path, "r") as f:
                current = set(json.load(f))
        else:
            current = set()
        current.update(converted)
        with open(exported_path, "w") as f:
            json.dump(list(current), f, indent=2)
        st.success(f"🎉 Migrazione completata. Aggiornato exported_posts.json con {len(converted)} newsletter.")
    except Exception as e:
        st.error(f"Errore nel salvataggio dell'archivio: {e}")

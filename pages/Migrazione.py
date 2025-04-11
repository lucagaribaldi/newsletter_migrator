
import streamlit as st
import requests
from bs4 import BeautifulSoup
import html2text
import os
import json
import subprocess
import re
from datetime import datetime

st.set_page_config(page_title="Migrazione Newsletter", layout="wide")
st.title("Migrazione Newsletter da Brevo a Substack")

ARCHIVE_FILE = "exported_posts.json"

def load_exported_ids():
    if os.path.exists(ARCHIVE_FILE):
        with open(ARCHIVE_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_exported_ids(ids):
    with open(ARCHIVE_FILE, "w") as f:
        json.dump(list(ids), f)

api_key = st.text_input("Inserisci la tua API Key Brevo", type="password")

st.subheader("Upload file cookies.json per Substack")
uploaded_cookies = st.file_uploader("Carica il file cookies.json", type="json")
cookie_file_path = None
if uploaded_cookies:
    cookie_file_path = os.path.join("temp_cookies.json")
    with open(cookie_file_path, "wb") as f:
        f.write(uploaded_cookies.getbuffer())
    st.success("File cookies.json caricato correttamente.")

def get_sent_campaigns(api_key):
    headers = {
        "accept": "application/json",
        "api-key": api_key
    }
    url = "https://api.brevo.com/v3/emailCampaigns"
    params = {
        "type": "classic",
        "status": "sent",
        "limit": 50
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()["campaigns"]
    else:
        st.error(f"Errore nella chiamata API: {response.status_code}")
        return []

def get_campaign_content(api_key, campaign_id):
    headers = {
        "accept": "application/json",
        "api-key": api_key
    }
    url = f"https://api.brevo.com/v3/emailCampaigns/{campaign_id}/content"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Errore nel recupero contenuto: {response.status_code}")
        return {}

def pulisci_titolo(titolo):
    return re.sub(r'^Cronache dal Consiglio n \d+ -\s*', '', titolo)

def convert_html_to_markdown(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    for img in soup.find_all("img"):
        src = img.get("src", "")
        markdown_img = f"![]({src})"
        img.insert_after(soup.new_string("\n" + markdown_img + "\n"))
    html_with_images = str(soup)
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = False
    converter.body_width = 0
    return converter.handle(html_with_images)

# INTERFACCIA DI MIGRAZIONE
if api_key:
    st.subheader("1. Seleziona le newsletter da esportare")
    campaigns = get_sent_campaigns(api_key)
    exported_ids = load_exported_ids()
    selected_campaigns = []
    for campaign in campaigns:
        already_exported = campaign['id'] in exported_ids
        label = f"{campaign['subject']} - {campaign['sentDate']}"
        if already_exported:
            st.checkbox(f"{label} (GIÀ ESPORTATA)", value=True, disabled=True, key=campaign['id'])
        else:
            checkbox = st.checkbox(label, key=campaign['id'])
            if checkbox:
                selected_campaigns.append(campaign)

    if selected_campaigns:
        st.subheader("2. Conversione in Markdown")
        converted_campaigns = []
        for campaign in selected_campaigns:
            content_data = get_campaign_content(api_key, campaign['id'])
            if content_data and "htmlContent" in content_data:
                cleaned_title = pulisci_titolo(campaign['subject'])
                markdown = convert_html_to_markdown(content_data["htmlContent"])
                default_date = datetime.strptime(campaign['sentDate'], "%Y-%m-%dT%H:%M:%S.%f%z").date()
                with st.expander(f"Anteprima: {cleaned_title}"):
                    st.markdown(markdown)
                    publish_date = st.date_input(f"Data per '{cleaned_title}'", value=default_date, key=f"date_{campaign['id']}")
                converted_campaigns.append({
                    "id": campaign['id'],
                    "title": cleaned_title,
                    "content": markdown,
                    "date": str(publish_date)
                })

        if cookie_file_path and st.button("3. Salva come bozza su Substack"):
            for post in converted_campaigns:
                script = f"""
from app.substack_bot import setup_driver, load_cookies, create_new_post

driver = setup_driver()
try:
    load_cookies(driver, '{cookie_file_path}')
    create_new_post(driver, "{post['title']}", """{post['content'].replace('"', '\"')}""", "{post['date']}", save_as_draft=True)
finally:
    driver.quit()
"""
                with open("run_substack_bot.py", "w") as f:
                    f.write(script)
                subprocess.run(["python3", "run_substack_bot.py"])
                exported_ids.add(post["id"])
            save_exported_ids(exported_ids)
            st.success("Bozze salvate e archivio aggiornato!")
        elif not cookie_file_path:
            st.warning("Carica prima il file cookies.json per procedere.")

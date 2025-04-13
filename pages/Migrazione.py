import streamlit as st
import os
import json
import logging
import pandas as pd
from datetime import datetime
import requests
from dotenv import load_dotenv
import time
import re
from app.utils import process_html_content, retry_function

# Configurazione logging
logger = logging.getLogger(__name__)

# Carica variabili d'ambiente
load_dotenv()

st.set_page_config(page_title="Migrazione Newsletter", layout="wide")

# Titolo
st.title("Migrazione Newsletter")

# Sidebar per la configurazione
st.sidebar.header("Configurazione")

# API Keys
brevo_api_key = st.sidebar.text_input("Brevo API Key", value=os.getenv("BREVO_API_KEY", ""), type="password")
brevo_list_id = st.sidebar.text_input("Brevo List ID (opzionale)", value=os.getenv("BREVO_LIST_ID", ""))
newsletter_name = st.sidebar.text_input("Nome Newsletter (opzionale)", value=os.getenv("NEWSLETTER_NAME", ""))

# Salva le API keys come variabili d'ambiente
if brevo_api_key:
    os.environ["BREVO_API_KEY"] = brevo_api_key
if brevo_list_id:
    os.environ["BREVO_LIST_ID"] = brevo_list_id
if newsletter_name:
    os.environ["NEWSLETTER_NAME"] = newsletter_name

# Funzione per ottenere le campagne da Brevo
@st.cache_data(ttl=600)
def get_brevo_campaigns():
    logger.info("Ottengo le campagne da Brevo")
    url = "https://api.brevo.com/v3/emailCampaigns"
    headers = {
        "Accept": "application/json",
        "api-key": os.getenv("BREVO_API_KEY")
    }
    
    try:
        # Prima prova senza parametri o con parametri minimi
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        campaigns = response.json().get("campaigns", [])
        logger.info(f"Ottenute {len(campaigns)} campagne")
        
        # Filtra le campagne per nome newsletter se specificato
        if os.getenv("NEWSLETTER_NAME") and os.getenv("NEWSLETTER_NAME").strip():
            filtered_campaigns = [c for c in campaigns if os.getenv("NEWSLETTER_NAME").lower() in c.get("name", "").lower()]
            logger.info(f"Filtrate a {len(filtered_campaigns)} campagne con nome '{os.getenv('NEWSLETTER_NAME')}'")
            return filtered_campaigns
        
        return campaigns
    except requests.exceptions.HTTPError as e:
        logger.error(f"Errore HTTP nel recupero delle campagne: {e}")
        st.error(f"Errore HTTP nel recupero delle campagne: {e}")
        # Mostra il contenuto della risposta per debug
        if hasattr(e, 'response') and e.response is not None:
            error_details = f"Dettagli risposta: {e.response.text}"
            logger.error(error_details)
            st.error(error_details)
        return []
    except Exception as e:
        logger.error(f"Errore nel recupero delle campagne: {e}")
        st.error(f"Errore nel recupero delle campagne: {e}")
        return []

# Funzione per ottenere i dettagli di una campagna
def get_campaign_content(campaign_id):
    logger.info(f"Ottengo i dettagli della campagna {campaign_id}")
    url = f"https://api.brevo.com/v3/emailCampaigns/{campaign_id}"
    headers = {
        "Accept": "application/json",
        "api-key": os.getenv("BREVO_API_KEY")
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"Errore HTTP nel recupero dei dettagli della campagna {campaign_id}: {e}")
        st.error(f"Errore HTTP nel recupero dei dettagli della campagna {campaign_id}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            error_details = f"Dettagli risposta: {e.response.text}"
            logger.error(error_details)
            st.error(error_details)
        return None
    except Exception as e:
        logger.error(f"Errore nel recupero dei dettagli della campagna {campaign_id}: {e}")
        st.error(f"Errore nel recupero dei dettagli della campagna {campaign_id}: {e}")
        return None

# Funzione per esportare una campagna a Substack (simulazione)
def export_to_substack(title, content, date):
    # Qui andrà la logica di esportazione a Substack
    # Per ora è solo una simulazione
    logger.info(f"Esportazione a Substack: {title}")
    
    # Salva il post in un file JSON per tenere traccia
    try:
        # Carica i post già esportati
        if os.path.exists("exported_posts.json"):
            with open("exported_posts.json", "r") as f:
                try:
                    exported_posts = json.load(f)
                except json.JSONDecodeError:
                    logger.warning("File exported_posts.json non valido, verrà creato nuovo")
                    exported_posts = []
        else:
            exported_posts = []
        
        # Aggiungi il nuovo post
        exported_posts.append({
            "title": title,
            "date": date,
            "exported_at": datetime.now().isoformat()
        })
        
        # Salva il file aggiornato
        with open("exported_posts.json", "w") as f:
            json.dump(exported_posts, f, indent=2)
        
        # Salva anche il contenuto HTML in un file separato
        clean_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '-').lower()
        os.makedirs("converted", exist_ok=True)
        with open(f"converted/{clean_title}.html", "w", encoding="utf-8") as f:
            f.write(content)
        
        return True
    except Exception as e:
        logger.error(f"Errore nell'esportazione a Substack: {e}")
        st.error(f"Errore nell'esportazione a Substack: {e}")
        return False

# Funzione per verificare se una campagna è già stata esportata
def is_already_exported(title, date):
    if os.path.exists("exported_posts.json"):
        try:
            with open("exported_posts.json", "r") as f:
                exported_posts = json.load(f)
            
            for post in exported_posts:
                if post.get("title") == title and post.get("date") == date:
                    return True
        except Exception as e:
            logger.error(f"Errore nella verifica dei post esportati: {e}")
    
    return False

# Main
if not brevo_api_key:
    st.warning("Inserisci la tua Brevo API Key nella sidebar")
else:
    # Ottieni le campagne
    with st.spinner("Caricamento campagne..."):
        campaigns = get_brevo_campaigns()
    
    if not campaigns:
        st.info("Nessuna campagna trovata o errore nel recupero delle campagne")
    else:
        # Mostra le campagne in una tabella
        st.header(f"Campagne trovate: {len(campaigns)}")
        
        # Prepara i dati per la tabella
        campaign_data = []
        for c in campaigns:
            # Converti la data in un formato più leggibile
            sent_date = c.get("sentDate", "")
            if sent_date:
                # Gestisci diversi formati di data
                try:
                    if 'T' in sent_date:
                        sent_date_obj = datetime.fromisoformat(sent_date.replace('Z', '+00:00'))
                    else:
                        sent_date_obj = datetime.strptime(sent_date, '%Y-%m-%d %H:%M:%S')
                    sent_date_formatted = sent_date_obj.strftime("%d/%m/%Y %H:%M")
                except Exception as e:
                    logger.warning(f"Errore nella conversione della data {sent_date}: {e}")
                    sent_date_formatted = sent_date
            else:
                sent_date_formatted = "N/D"
            
            # Verifica se è già esportata
            is_exported = is_already_exported(c.get("name"), sent_date)
            
            campaign_data.append({
                "ID": c.get("id"),
                "Nome": c.get("name"),
                "Data invio": sent_date_formatted,
                "Oggetto": c.get("subject", ""),
                "Già esportata": "✓" if is_exported else "",
                "sentDate": sent_date  # Campo nascosto per ordinamento
            })
        
        # Ordinamento delle campagne per data di invio (più recenti prima)
        try:
            sorted_campaigns = sorted(
                campaign_data,
                key=lambda x: datetime.fromisoformat(x['sentDate'].replace('Z', '+00:00')) if 'T' in x['sentDate'] else datetime.strptime(x['sentDate'], '%Y-%m-%d %H:%M:%S'),
                reverse=True
            )
        except Exception as e:
            logger.warning(f"Errore nell'ordinamento delle campagne: {e}")
            sorted_campaigns = campaign_data
        
        # Crea una tabella con Pandas
        df = pd.DataFrame(sorted_campaigns)
        if "sentDate" in df.columns:
            df = df.drop(columns=["sentDate"])  # Rimuovi la colonna nascosta
        
        st.dataframe(df)
        
        # Sezione per esportare una campagna specifica
        st.header("Esporta una campagna")
        
        campaign_ids = [c.get("ID") for c in sorted_campaigns]
        campaign_names = [c.get("Nome") for c in sorted_campaigns]
        
        # Crea un dizionario di mappatura ID -> Nome
        campaign_map = {str(id): name for id, name in zip(campaign_ids, campaign_names)}
        
        # Selettore per la campagna
        selected_campaign_id = st.selectbox("Seleziona una campagna", options=[str(id) for id in campaign_ids], format_func=lambda x: f"{campaign_map.get(x)} (ID: {x})")
        
        if st.button("Carica contenuto"):
            if selected_campaign_id:
                with st.spinner("Caricamento contenuto..."):
                    campaign_details = get_campaign_content(selected_campaign_id)
                    
                    if campaign_details:
                        # Estrai il contenuto HTML
                        html_content = campaign_details.get("htmlContent", "")
                        subject = campaign_details.get("subject", "")
                        sent_date = campaign_details.get("sentDate", "")
                        
                        # Processa il contenuto HTML per renderlo compatibile con Substack
                        processed_html = process_html_content(html_content)
                        
                        # Mostra il contenuto
                        st.subheader(f"Contenuto della campagna: {subject}")
                        
                        # Tabs per visualizzare HTML originale e processato
                        tab1, tab2 = st.tabs(["HTML Processato", "HTML Originale"])
                        
                        with tab1:
                            st.code(processed_html, language="html")
                        
                        with tab2:
                            st.code(html_content, language="html")
                        
                        # Preview del contenuto
                        st.subheader("Anteprima")
                        st.write(subject)
                        st.markdown("---")
                        st.markdown(processed_html, unsafe_allow_html=True)
                        
                        # Bottone per esportare
                        if st.button("Esporta a Substack"):
                            with st.spinner("Esportazione in corso..."):
                                success = export_to_substack(subject, processed_html, sent_date)
                                if success:
                                    st.success("Campagna esportata con successo!")
                                    # Invalida la cache per ricaricare le campagne
                                    get_brevo_campaigns.clear()
                                else:
                                    st.error("Errore nell'esportazione della campagna")
                    else:
                        st.error("Impossibile caricare i dettagli della campagna")
            else:
                st.warning("Seleziona una campagna da esportare")
        
        # Sezione per esportazione batch
        st.header("Esportazione Batch")
        st.info("Per esportare più campagne contemporaneamente, usa lo script batch_migrate.py")

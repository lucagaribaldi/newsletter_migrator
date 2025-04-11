import streamlit as st
import os
import json
import time
import logging
import requests
import subprocess
from datetime import datetime
import re
import sys

# Aggiungi il path della cartella padre per importare i moduli custom
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils import process_html_content, retry_function
from app.substack_bot import publish_post_to_substack

logger = logging.getLogger(__name__)

# Configurazione pagina
st.set_page_config(
    page_title="Migrazione Newsletter",
    page_icon="🚀",
    layout="wide"
)

# Titolo
st.title("🚀 Migrazione Newsletter")
st.markdown("Estrazione, conversione e migrazione delle newsletter da Brevo a Substack")

# Verifica che le credenziali siano configurate
if (not st.session_state.get('brevo_api_key') or 
    not st.session_state.get('cloudinary_cloud_name') or 
    not st.session_state.get('cloudinary_api_key') or 
    not st.session_state.get('cloudinary_api_secret')):
    
    st.error("⚠️ Devi prima configurare le API nella pagina principale!")
    st.stop()

# Funzione per chiamare l'API di Brevo con retry
@st.cache_data(ttl=3600)  # Cache per un'ora
def fetch_campaigns_with_retry(api_key, offset=0, limit=100):
    """Fetches campaigns from Brevo API with retry mechanism."""
    headers = {
        'accept': 'application/json',
        'api-key': api_key
    }
    url = f'https://api.brevo.com/v3/emailCampaigns?status=sent&limit={limit}&offset={offset}'
    
    def _fetch():
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    
    return retry_function(_fetch, max_retries=3, base_delay=2)

# Funzione per estrarre tutte le campagne con paginazione
def fetch_all_campaigns(api_key):
    """Fetches all campaigns using pagination."""
    all_campaigns = []
    offset = 0
    limit = 100  # Massimo consentito dall'API
    
    with st.spinner("Estrazione newsletter da Brevo in corso..."):
        progress_bar = st.progress(0)
        total_fetched = 0
        
        while True:
            try:
                response = fetch_campaigns_with_retry(api_key, offset, limit)
                campaigns = response.get('campaigns', [])
                
                if not campaigns:
                    break
                    
                all_campaigns.extend(campaigns)
                total_fetched += len(campaigns)
                
                # Aggiorna la progress bar (approssimazione del progresso)
                progress_value = min(total_fetched / (total_fetched + limit), 1.0)
                progress_bar.progress(progress_value)
                
                # Se riceviamo meno del limit, siamo all'ultima pagina
                if len(campaigns) < limit:
                    break
                    
                offset += limit
                time.sleep(1)  # Evita rate limiting
                
            except Exception as e:
                st.error(f"Errore durante l'estrazione delle newsletter: {str(e)}")
                logger.error(f"Errore API Brevo: {str(e)}")
                break
    
    return all_campaigns

# Funzione per ottenere il contenuto di una campagna
@st.cache_data(ttl=24*3600)  # Cache per un giorno
def get_campaign_content(api_key, campaign_id):
    """Gets the HTML content of a specific campaign."""
    headers = {
        'accept': 'application/json',
        'api-key': api_key
    }
    url = f'https://api.brevo.com/v3/emailCampaigns/{campaign_id}'
    
    def _fetch():
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    
    return retry_function(_fetch, max_retries=3, base_delay=2)

# Funzione per controllare se una newsletter è già stata esportata
def is_already_exported(campaign_id):
    """Checks if a campaign has already been exported."""
    if os.path.exists('exported_posts.json'):
        with open('exported_posts.json', 'r') as f:
            exported = json.load(f)
            return campaign_id in [post.get('id') for post in exported]
    return False

# Funzione per aggiungere una newsletter all'elenco delle esportate
def mark_as_exported(campaign_id, title):
    """Marks a campaign as exported."""
    exported = []
    if os.path.exists('exported_posts.json'):
        with open('exported_posts.json', 'r') as f:
            exported = json.load(f)
    
    # Aggiungi il nuovo post
    exported.append({
        'id': campaign_id,
        'title': title,
        'exported_date': datetime.now().isoformat()
    })
    
    # Salva il file aggiornato
    with open('exported_posts.json', 'w') as f:
        json.dump(exported, f, indent=4)
    
    logger.info(f"Newsletter '{title}' (ID: {campaign_id}) marcata come esportata")

# Funzione per pulire il titolo
def clean_title(title):
    """Removes prefix like 'Cronache dal Consiglio n° xxx -' from title."""
    # Rimuovi prefissi specifici
    title = re.sub(r'^Cronache\s+dal\s+Consiglio\s+n°\s*\d+\s*-\s*', '', title)
    # Rimuovi spazi extra
    title = re.sub(r'\s+', ' ', title).strip()
    return title

# Main app
if 'campaigns' not in st.session_state:
    # Carica le campagne
    campaigns = fetch_all_campaigns(st.session_state.brevo_api_key)
    
    # Filtra solo le newsletter che non sono già state esportate
    filtered_campaigns = []
    for campaign in campaigns:
        if not is_already_exported(campaign['id']):
            # Pulizia del titolo
            campaign['cleanTitle'] = clean_title(campaign['name'])
            filtered_campaigns.append(campaign)
    
    st.session_state.campaigns = filtered_campaigns
    st.session_state.all_campaigns_count = len(campaigns)

# Mostra contatori
col1, col2 = st.columns(2)
with col1:
    st.metric("Newsletter totali", st.session_state.all_campaigns_count)
with col2:
    st.metric("Newsletter da migrare", len(st.session_state.campaigns))

# Se non ci sono newsletter da migrare
if not st.session_state.campaigns:
    st.success("🎉 Tutte le newsletter sono già state migrate!")
    
    # Opzione per forzare il recupero di tutte le newsletter
    if st.button("Mostra tutte le newsletter (incluse quelle già migrate)"):
        st.session_state.pop('campaigns', None)
        st.experimental_rerun()
    
    st.stop()

# Selezione delle newsletter da migrare
st.subheader("Seleziona le newsletter da migrare")

# Ordinamento delle campagne per data più recente
sorted_campaigns = sorted(
    st.session_state.campaigns,
    key=lambda x: datetime.strptime(x['sentDate'], '%Y-%m-%d %H:%M:%S'),
    reverse=True
)

# Mostra le campagne con la data formattata
campaign_options = {}
for campaign in sorted_campaigns:
    # Formatta la data
    sent_date = datetime.strptime(campaign['sentDate'], '%Y-%m-%d %H:%M:%S')
    formatted_date = sent_date.strftime('%d/%m/%Y')
    
    # Crea l'etichetta
    label = f"{formatted_date} - {campaign['cleanTitle']}"
    campaign_options[label] = campaign

# Dropdown per limitare le opzioni mostrate
num_to_show = st.selectbox(
    "Mostra newsletter:",
    options=[10, 20, 50, 100, "Tutte"],
    index=0
)

if num_to_show != "Tutte":
    campaign_labels = list(campaign_options.keys())[:num_to_show]
else:
    campaign_labels = list(campaign_options.keys())

# Multi-select per scegliere le newsletter
selected_labels = st.multiselect(
    "Scegli le newsletter da migrare:",
    options=campaign_labels
)

selected_campaigns = [campaign_options[label] for label in selected_labels]

# Opzioni aggiuntive
st.subheader("Opzioni di migrazione")
col1, col2 = st.columns(2)

with col1:
    convert_only = st.checkbox("Solo conversione (nessun upload su Substack)", value=False)

with col2:
    cloudinary_folder = st.text_input(
        "Cartella Cloudinary per le immagini",
        value="newsletter_migrator",
        help="Nome della cartella su Cloudinary dove verranno caricate le immagini"
    )

# Pulsante per avviare la migrazione
if st.button("Avvia migrazione", disabled=len(selected_campaigns) == 0):
    if not selected_campaigns:
        st.warning("Nessuna newsletter selezionata")
    else:
        # Configura Cloudinary
        cloudinary_config = {
            "cloud_name": st.session_state.cloudinary_cloud_name,
            "api_key": st.session_state.cloudinary_api_key,
            "api_secret": st.session_state.cloudinary_api_secret,
            "folder": cloudinary_folder
        }
        
        # Crea la directory converted se non esiste
        if not os.path.exists("converted"):
            os.makedirs("converted")
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, campaign in enumerate(selected_campaigns):
            campaign_id = campaign['id']
            title = campaign['cleanTitle']
            
            # Aggiorna stato
            status_text.text(f"Elaborazione {i+1}/{len(selected_campaigns)}: {title}")
            progress_value = i / len(selected_campaigns)
            progress_bar.progress(progress_value)
            
            try:
                # Ottieni contenuto HTML
                campaign_details = get_campaign_content(st.session_state.brevo_api_key, campaign_id)
                html_content = campaign_details.get('htmlContent', '')
                
                if not html_content:
                    st.error(f"Nessun contenuto HTML trovato per '{title}'")
                    continue
                
                # Converti in Markdown
                markdown_content = process_html_content(html_content, cloudinary_config, title)
                
                # Salva localmente
                file_path = os.path.join("converted", f"{campaign_id}.md")
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                
                logger.info(f"Newsletter '{title}' convertita e salvata in {file_path}")
                
                # Upload su Substack (se richiesto)
                if not convert_only:
                    if not os.path.exists("cookies.json"):
                        st.error("File cookies.json non trovato. Impossibile procedere con l'upload su Substack.")
                        break
                    
                    success = publish_post_to_substack(title, markdown_content)
                    
                    if success:
                        st.success(f"✅ '{title}' caricato su Substack come bozza")
                    else:
                        st.error(f"❌ Errore nel caricamento di '{title}' su Substack")
                        continue
                
                # Marca come esportato
                mark_as_exported(campaign_id, title)
                
            except Exception as e:
                error_msg = f"Errore durante l'elaborazione di '{title}': {str(e)}"
                st.error(error_msg)
                logger.error(error_msg)
        
        # Aggiorna la progress bar al 100%
        progress_bar.progress(1.0)
        status_text.text("Processo completato!")
        
        # Aggiorna la pagina dopo 3 secondi
        time.sleep(3)
        st.experimental_rerun()

# Script per invio batch
st.subheader("Invio batch programmato")
st.markdown("""
Puoi configurare un invio batch programmato delle newsletter per inviarle a intervalli regolari su Substack.
""")

col1, col2 = st.columns(2)

with col1:
    batch_size = st.number_input("Numero di newsletter per batch", min_value=1, max_value=20, value=5)

with col2:
    interval_hours = st.number_input("Intervallo tra i batch (ore)", min_value=1, value=2)

if st.button("Configurare invio batch"):
    st.info("Funzionalità in fase di sviluppo. Sarà disponibile nella prossima versione.")
    
    # Qui andrebbe il codice per configurare il cron job o lo scheduler di Replit
    # In un file separato che verrà eseguito periodicamente

# Footer
st.markdown("---")
st.markdown("Developed with ❤️ | [GitHub Repository](https://github.com/lucagaribaldi/newsletter_migrator)")

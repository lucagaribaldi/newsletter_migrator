#!/usr/bin/env python3
import os
import json
import time
import logging
import sys
import random
from datetime import datetime

# Aggiungi il path della cartella corrente
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils import process_html_content
from app.substack_bot import publish_post_to_substack

# Configura il logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("logs/batch_migrate.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def load_config():
    """Carica la configurazione dal file .env."""
    config = {}
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    config[key] = value
    return config

def get_pending_campaigns(api_key):
    """Ottiene le campagne in attesa di migrazione."""
    import requests
    
    headers = {
        'accept': 'application/json',
        'api-key': api_key
    }
    
    # Fetch campaigns
    url = 'https://api.brevo.com/v3/emailCampaigns?status=sent&limit=100'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    campaigns = response.json().get('campaigns', [])
    
    # Carica le campagne già esportate
    exported_ids = []
    if os.path.exists('exported_posts.json'):
        with open('exported_posts.json', 'r') as f:
            exported = json.load(f)
            exported_ids = [post.get('id') for post in exported]
    
    # Filtra le campagne non ancora esportate
    pending_campaigns = [c for c in campaigns if c['id'] not in exported_ids]
    
    return pending_campaigns

def get_campaign_content(api_key, campaign_id):
    """Ottiene il contenuto di una campagna specifica."""
    import requests
    
    headers = {
        'accept': 'application/json',
        'api-key': api_key
    }
    
    url = f'https://api.brevo.com/v3/emailCampaigns/{campaign_id}'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    return response.json()

def clean_title(title):
    """Rimuove prefissi come 'Cronache dal Consiglio n° xxx -' dal titolo."""
    import re
    # Rimuovi prefissi specifici
    title = re.sub(r'^Cronache\s+dal\s+Consiglio\s+n°\s*\d+\s*-\s*', '', title)
    # Rimuovi spazi extra
    title = re.sub(r'\s+', ' ', title).strip()
    return title

def mark_as_exported(campaign_id, title):
    """Marca una campagna come esportata."""
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

def main(batch_size=5):
    """Funzione principale per la migrazione batch."""
    logger.info(f"Avvio migrazione batch (dimensione batch: {batch_size})")
    
    # Carica la configurazione
    config = load_config()
    
    # Verifica che le configurazioni necessarie siano presenti
    required_keys = [
        "BREVO_API_KEY", 
        "CLOUDINARY_CLOUD_NAME", 
        "CLOUDINARY_API_KEY", 
        "CLOUDINARY_API_SECRET"
    ]
    
    missing_keys = [key for key in required_keys if key not in config or not config[key]]
    
    if missing_keys:
        logger.error(f"Configurazione incompleta. Mancano: {', '.join(missing_keys)}")
        return
    
    # Verifica che il file cookies.json esista
    if not os.path.exists("cookies.json"):
        logger.error("File cookies.json non trovato. Impossibile procedere con l'upload su Substack.")
        return
    
    # Crea directory se non esistono
    for directory in ["converted", "logs"]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    # Ottieni le campagne in attesa
    try:
        pending_campaigns = get_pending_campaigns(config["BREVO_API_KEY"])
    except Exception as e:
        logger.error(f"Errore durante l'ottenimento delle campagne: {str(e)}")
        return
    
    logger.info(f"Trovate {len(pending_campaigns)} campagne in attesa di migrazione")
    
    # Limita il numero di campagne al batch_size
    campaigns_to_process = pending_campaigns[:batch_size]
    
    # Configura Cloudinary
    cloudinary_config = {
        "cloud_name": config["CLOUDINARY_CLOUD_NAME"],
        "api_key": config["CLOUDINARY_API_KEY"],
        "api_secret": config["CLOUDINARY_API_SECRET"],
        "folder": "newsletter_migrator"
    }
    
    # Processa ogni campagna
    for i, campaign in enumerate(campaigns_to_process):
        campaign_id = campaign['id']
        title = clean_title(campaign['name'])
        
        logger.info(f"Elaborazione {i+1}/{len(campaigns_to_process)}: {title}")
        
        try:
            # Ottieni contenuto HTML
            campaign_details = get_campaign_content(config["BREVO_API_KEY"], campaign_id)
            html_content = campaign_details.get('htmlContent', '')
            
            if not html_content:
                logger.error(f"Nessun contenuto HTML trovato per '{title}'")
                continue
            
            # Converti in Markdown
            markdown_content = process_html_content(html_content, cloudinary_config, title)
            
            # Salva localmente
            file_path = os.path.join("converted", f"{campaign_id}.md")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            logger.info(f"Newsletter '{title}' convertita e salvata in {file_path}")
            
            # Upload su Substack
            success = publish_post_to_substack(title, markdown_content)
            
            if success:
                logger.info(f"✅ '{title}' caricato su Substack come bozza")
                # Marca come esportato
                mark_as_exported(campaign_id, title)
            else:
                logger.error(f"❌ Errore nel caricamento di '{title}' su Substack")
            
            # Pausa tra i post (1-3 minuti)
            if i < len(campaigns_to_process) - 1:
                pause_time = random.randint(60, 180)
                logger.info(f"Pausa di {pause_time} secondi prima del prossimo post")
                time.sleep(pause_time)
            
        except Exception as e:
            error_msg = f"Errore durante l'elaborazione di '{title}': {str(e)}"
            logger.error(error_msg)
    
    logger.info("Processo batch completato")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrazione batch di newsletter da Brevo a Substack")
    parser.add_argument("--batch-size", type=int, default=5, help="Numero di newsletter da migrare in questo batch")
    
    args = parser.parse_args()
    
    main(batch_size=args.batch_size)

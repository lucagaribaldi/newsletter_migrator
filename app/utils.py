import os
```python
import re
import logging
import time
import requests
from bs4 import BeautifulSoup
import html2text
import cloudinary
import cloudinary.uploader
import cloudinary.api

logger = logging.getLogger(__name__)

def setup_cloudinary(cloud_name, api_key, api_secret):
    """Configura Cloudinary con le credenziali fornite."""
    try:
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
        logger.info("Cloudinary configurato correttamente")
        return True
    except Exception as e:
        logger.error(f"Errore nella configurazione di Cloudinary: {str(e)}")
        return False

def download_image(url, max_retries=3):
    """Scarica un'immagine con tentativi multipli."""
    retry = 0
    while retry < max_retries:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            retry += 1
            if retry < max_retries:
                wait_time = 2 ** retry  # Incremento esponenziale
                logger.warning(f"Tentativo {retry} fallito per {url}. Errore: {str(e)}. Riprovo tra {wait_time} secondi...")
                time.sleep(wait_time)
            else:
                logger.error(f"Impossibile scaricare l'immagine da {url} dopo {max_retries} tentativi. Errore: {str(e)}")
                return None

def upload_to_cloudinary(image_data, public_id=None, folder="newsletter_migrator", max_retries=3):
    """Carica un'immagine su Cloudinary con tentativi multipli."""
    if not image_data:
        return None
    
    retry = 0
    while retry < max_retries:
        try:
            upload_params = {
                "folder": folder,
                "resource_type": "image"
            }
            if public_id:
                upload_params["public_id"] = public_id
                
            result = cloudinary.uploader.upload(image_data, **upload_params)
            logger.info(f"Immagine caricata su Cloudinary: {result['secure_url']}")
            return result['secure_url']
        except Exception as e:
            retry += 1
            if retry < max_retries:
                wait_time = 2 ** retry
                logger.warning(f"Tentativo {retry} fallito per upload su Cloudinary. Errore: {str(e)}. Riprovo tra {wait_time} secondi...")
                time.sleep(wait_time)
            else:
                logger.error(f"Impossibile caricare l'immagine su Cloudinary dopo {max_retries} tentativi. Errore: {str(e)}")
                return None

def process_html_content(html_content, cloudinary_config, title=""):
    """Processa il contenuto HTML, carica le immagini su Cloudinary e converte in Markdown."""
    if not html_content:
        logger.warning("Contenuto HTML vuoto")
        return ""
    
    # Setup Cloudinary
    setup_cloudinary(
        cloudinary_config["cloud_name"],
        cloudinary_config["api_key"],
        cloudinary_config["api_secret"]
    )
    
    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Rimuovi script e style
    for tag in soup(['script', 'style']):
        tag.decompose()
    
    # Processa immagini
    for img in soup.find_all('img'):
        src = img.get('src')
        if not src:
            continue
        
        # Genera un ID basato sull'URL e sul titolo
        image_name = re.sub(r'[^a-zA-Z0-9]', '_', os.path.basename(src))
        public_id = f"{re.sub(r'[^a-zA-Z0-9]', '_', title)}_{image_name}"[:60]  # Limite di 60 caratteri
        
        # Scarica e carica l'immagine
        image_data = download_image(src)
        if image_data:
            cloudinary_url = upload_to_cloudinary(image_data, public_id)
            if cloudinary_url:
                # Sostituisci l'URL nell'HTML
                img['src'] = cloudinary_url
    
    # Converti in Markdown
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.images_to_alt = False
    h.body_width = 0  # No word wrap
    
    markdown_content = h.handle(str(soup))
    
    # Pulizia finale del markdown
    markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)  # Rimuovi troppe righe vuote consecutive
    
    return markdown_content

def retry_function(func, max_retries=3, base_delay=1, *args, **kwargs):
    """Funzione generica per riprovare un'operazione con backoff esponenziale."""
    last_exception = None
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                sleep_time = base_delay * (2 ** attempt)  # Backoff esponenziale
                logger.warning(f"Tentativo {attempt+1}/{max_retries} fallito. Riprovo tra {sleep_time} secondi. Errore: {str(e)}")
                time.sleep(sleep_time)
            else:
                logger.error(f"Tutti i tentativi falliti ({max_retries}). Ultimo errore: {str(e)}")
    
    raise last_exception

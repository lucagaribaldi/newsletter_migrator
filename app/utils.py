import re
import time
import logging
from bs4 import BeautifulSoup
import html2text

logger = logging.getLogger(__name__)

def process_html_content(html_content):
    """
    Processa il contenuto HTML per renderlo compatibile con Substack.
    
    Args:
        html_content (str): Il contenuto HTML originale.
        
    Returns:
        str: Il contenuto HTML processato.
    """
    try:
        if not html_content:
            return ""
            
        # Usa BeautifulSoup per analizzare l'HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Rimuovi script e stili
        for tag in soup(['script', 'style']):
            tag.decompose()
        
        # Rimuovi attributi di stile inline e classi
        for tag in soup.find_all(True):
            tag.attrs = {key: value for key, value in tag.attrs.items() 
                        if key not in ['style', 'class', 'id', 'bgcolor']}
        
        # Gestisci le immagini
        for img in soup.find_all('img'):
            # Assicurati che le immagini abbiano un alt text
            if 'alt' not in img.attrs:
                img['alt'] = "Immagine"
                
            # Rimuovi attributi di dimensione lasciando solo src e alt
            attrs_to_keep = ['src', 'alt']
            img.attrs = {key: value for key, value in img.attrs.items() if key in attrs_to_keep}
        
        # Pulisci ulteriormente l'HTML
        cleaned_html = str(soup)
        
        # Rimuovi HTML comments
        cleaned_html = re.sub(r'<!--.*?-->', '', cleaned_html, flags=re.DOTALL)
        
        # Rimuovi spazi bianchi eccessivi
        cleaned_html = re.sub(r'\s+', ' ', cleaned_html)
        
        # Rimuovi tag vuoti consecutivi
        cleaned_html = re.sub(r'<(p|div|span)>\s*</\1>', '', cleaned_html)
        
        return cleaned_html
    except Exception as e:
        logger.error(f"Errore nel processamento dell'HTML: {e}")
        return html_content  # Restituisci l'originale in caso di errore

def convert_html_to_markdown(html_content):
    """
    Converte il contenuto HTML in markdown.
    
    Args:
        html_content (str): Il contenuto HTML da convertire.
        
    Returns:
        str: Il contenuto in formato markdown.
    """
    try:
        # Crea un'istanza del convertitore html2text
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.inline_links = True
        h.body_width = 0  # Disabilita il wrapping
        
        # Converte HTML in markdown
        markdown_content = h.handle(html_content)
        
        return markdown_content
    except Exception as e:
        logger.error(f"Errore nella conversione HTML->Markdown: {e}")
        return ""

def retry_function(func, max_retries=3, delay=2, *args, **kwargs):
    """
    Ritenta l'esecuzione di una funzione in caso di errore.
    
    Args:
        func: La funzione da eseguire.
        max_retries (int): Numero massimo di tentativi.
        delay (int): Ritardo tra i tentativi in secondi.
        *args: Argomenti posizionali da passare alla funzione.
        **kwargs: Argomenti nominali da passare alla funzione.
        
    Returns:
        Il risultato della funzione.
    """
    retries = 0
    while retries < max_retries:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            retries += 1
            logger.warning(f"Tentativo {retries}/{max_retries} fallito: {e}")
            if retries >= max_retries:
                logger.error(f"Tutti i tentativi falliti: {e}")
                raise
            time.sleep(delay)

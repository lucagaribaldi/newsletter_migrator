
import os
```python
import json
import time
import logging
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    ElementNotInteractableException,
    StaleElementReferenceException,
    NoSuchElementException
)
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

def setup_driver_for_replit():
    """Configura il driver Chrome specificamente per l'ambiente Replit."""
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-infobars')
    
    # Installa ChromeDriver
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        logger.info("Driver Chrome inizializzato correttamente")
        return driver
    except Exception as e:
        logger.error(f"Errore nell'inizializzazione del driver Chrome: {str(e)}")
        raise

def wait_and_click(driver, selector, timeout=10, max_retries=3):
    """Attende che un elemento sia cliccabile e lo clicca con tentativi ripetuti."""
    for attempt in range(max_retries):
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            element.click()
            return element
        except (TimeoutException, ElementNotInteractableException, StaleElementReferenceException) as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Tentativo {attempt+1}/{max_retries} fallito per click su '{selector}'. Attendo {wait_time}s. Errore: {str(e)}")
                time.sleep(wait_time)
            else:
                logger.error(f"Impossibile cliccare su '{selector}' dopo {max_retries} tentativi. Errore: {str(e)}")
                raise

def wait_for_element(driver, selector, timeout=10, max_retries=3):
    """Attende che un elemento sia presente con tentativi ripetuti."""
    for attempt in range(max_retries):
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return element
        except TimeoutException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Tentativo {attempt+1}/{max_retries} fallito per trovare '{selector}'. Attendo {wait_time}s")
                time.sleep(wait_time)
            else:
                logger.error(f"Impossibile trovare '{selector}' dopo {max_retries} tentativi")
                raise

def login_with_cookies(driver, cookies_file):
    """Effettua il login su Substack usando i cookies salvati."""
    try:
        # Carica i cookies
        if not os.path.exists(cookies_file):
            logger.error(f"File cookies non trovato: {cookies_file}")
            raise FileNotFoundError(f"File cookies non trovato: {cookies_file}")
        
        with open(cookies_file, 'r') as f:
            cookies = json.load(f)
        
        # Vai alla pagina principale di Substack
        driver.get('https://substack.com/')
        
        # Aggiungi i cookies
        for cookie in cookies:
            # Alcuni cookies potrebbero avere attributi incompatibili
            try:
                if 'expiry' in cookie:
                    cookie['expiry'] = int(cookie['expiry'])
                driver.add_cookie(cookie)
            except Exception as e:
                logger.warning(f"Impossibile aggiungere cookie: {str(e)}")
        
        # Ricarica la pagina per applicare i cookies
        driver.get('https://substack.com/publish')
        time.sleep(3)
        
        # Verifica login
        if 'publish' in driver.current_url:
            logger.info("Login effettuato con successo tramite cookies")
            return True
        else:
            logger.error("Login fallito. URL attuale: " + driver.current_url)
            return False
            
    except Exception as e:
        logger.error(f"Errore durante il login con cookies: {str(e)}")
        return False

def create_draft_post(driver, title, content):
    """Crea un nuovo post come bozza su Substack."""
    try:
        # Vai alla pagina di creazione post
        driver.get('https://substack.com/publish')
        time.sleep(3)
        
        # Attendi e clicca su New Post se necessario
        try:
            new_post_button = wait_for_element(driver, "a[href='/publish/post']", timeout=5)
            new_post_button.click()
            time.sleep(2)
        except Exception as e:
            logger.info("Già nella pagina di creazione post o bottone non trovato")
        
        # Inserisci il titolo
        title_input = wait_for_element(driver, "input.post-title-input")
        title_input.clear()
        title_input.send_keys(title)
        logger.info(f"Titolo inserito: {title}")
        
        # Switch to Markdown editor
        try:
            # Apri menu editor
            editor_menu = wait_and_click(driver, "button.editor-menu-button")
            time.sleep(1)
            
            # Seleziona Markdown
            markdown_option = wait_and_click(driver, "button[data-format='markdown']")
            time.sleep(2)
        except Exception as e:
            logger.warning(f"Impossibile passare all'editor Markdown. Errore: {str(e)}")
        
        # Inserisci il contenuto nel textarea
        content_editor = wait_for_element(driver, "textarea.markdown-editor-input")
        content_editor.clear()
        # Inserisco il contenuto in piccoli chunk per evitare problemi con grandi volumi di testo
        chunk_size = 5000
        for i in range(0, len(content), chunk_size):
            content_editor.send_keys(content[i:i+chunk_size])
            time.sleep(0.5)
        
        logger.info("Contenuto inserito")
        
        # Salva come bozza
        save_button = wait_and_click(driver, "button.save-draft-button")
        time.sleep(3)
        
        logger.info("Post salvato come bozza")
        return True
        
    except Exception as e:
        logger.error(f"Errore durante la creazione del post: {str(e)}")
        return False

def publish_post_to_substack(title, markdown_content, cookies_file="cookies.json"):
    """Funzione principale per pubblicare un post su Substack."""
    driver = None
    success = False
    
    try:
        logger.info(f"Avvio pubblicazione su Substack: {title}")
        
        # Inizializza il driver
        driver = setup_driver_for_replit()
        
        # Login con cookies
        if not login_with_cookies(driver, cookies_file):
            logger.error("Login su Substack fallito")
            return False
        
        # Crea il post
        success = create_draft_post(driver, title, markdown_content)
        
        if success:
            logger.info(f"Post '{title}' pubblicato con successo come bozza su Substack")
        else:
            logger.error(f"Pubblicazione di '{title}' fallita")
        
        return success
        
    except Exception as e:
        logger.error(f"Errore durante il processo di pubblicazione: {str(e)}")
        return False
        
    finally:
        # Chiudi sempre il driver
        if driver:
            driver.quit()
            logger.info("Driver Chrome chiuso")

# Per esecuzione diretta dello script
if __name__ == "__main__":
    import argparse
    
    # Configurazione logging base
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    parser = argparse.ArgumentParser(description="Pubblica un post su Substack come bozza")
    parser.add_argument("--title", required=True, help="Titolo del post")
    parser.add_argument("--file", required=True, help="File markdown da pubblicare")
    parser.add_argument("--cookies", default="cookies.json", help="File cookies per il login")
    
    args = parser.parse_args()
    
    # Leggi il contenuto del file
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Errore nella lettura del file: {str(e)}")
        exit(1)
    
    # Pubblica
    result = publish_post_to_substack(args.title, content, args.cookies)
    
    if result:
        print(f"✅ Post '{args.title}' pubblicato con successo come bozza")
        exit(0)
    else:
        print(f"❌ Pubblicazione fallita per '{args.title}'")
        exit(1)

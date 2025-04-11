#!/usr/bin/env python3
import os
import subprocess
import logging
import sys

# Configura il logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point to start the application."""
    logger.info("Avvio newsletter_migrator")
    
    # Esegui il setup iniziale
    if not os.path.exists("setup.py"):
        logger.error("setup.py non trovato. Esecuzione non possibile.")
        return
    
    try:
        logger.info("Esecuzione setup.py...")
        subprocess.run([sys.executable, "setup.py"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Errore durante l'esecuzione di setup.py: {e}")
        return
    
    # Avvia Streamlit
    try:
        logger.info("Avvio dell'applicazione Streamlit...")
        subprocess.run([
            "streamlit", "run", "Home.py",
            "--server.headless=true",
            "--server.enableCORS=false",
            "--server.enableXsrfProtection=false"
        ], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Errore durante l'avvio di Streamlit: {e}")
    except FileNotFoundError:
        logger.error("Streamlit non trovato. Esegui 'pip install streamlit' per installarlo.")

if __name__ == "__main__":
    main()

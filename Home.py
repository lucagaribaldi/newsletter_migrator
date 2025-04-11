
import streamlit as st
import os
import logging
import json
import logging.config
from dotenv import load_dotenv

# Setup iniziale
if not os.path.exists("converted"):
    os.makedirs("converted")
if not os.path.exists("logs"):
    os.makedirs("logs")

# Configurazione logging
if os.path.exists("logging_config.json"):
    with open("logging_config.json", "r") as f:
        config = json.load(f)
        logging.config.dictConfig(config)
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler("logs/newsletter_migrator.log"),
            logging.StreamHandler()
        ]
    )

logger = logging.getLogger(__name__)

# Carica variabili d'ambiente
load_dotenv()

# Configurazione pagina Streamlit
st.set_page_config(
    page_title="Newsletter Migrator",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Titolo e descrizione
st.title("📧 Newsletter Migrator")
st.markdown("""
Questa applicazione ti aiuta a migrare le tue newsletter da Brevo (ex Sendinblue) a Substack in modo semplice ed efficace.

### Funzionalità:
- Estrazione delle newsletter inviate tramite Brevo
- Conversione in Markdown con immagini caricate su Cloudinary
- Caricamento delle newsletter come bozze su Substack
- Gestione automatica per evitare duplicati
""")

# Inizializzazione sessione
if 'brevo_api_key' not in st.session_state:
    st.session_state.brevo_api_key = os.getenv("BREVO_API_KEY", "")
if 'cloudinary_cloud_name' not in st.session_state:
    st.session_state.cloudinary_cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "")
if 'cloudinary_api_key' not in st.session_state:
    st.session_state.cloudinary_api_key = os.getenv("CLOUDINARY_API_KEY", "")
if 'cloudinary_api_secret' not in st.session_state:
    st.session_state.cloudinary_api_secret = os.getenv("CLOUDINARY_API_SECRET", "")

# Form per le credenziali
with st.form("credentials_form"):
    st.subheader("Configurazione API")
    
    col1, col2 = st.columns(2)
    
    with col1:
        brevo_api_key = st.text_input(
            "Brevo (Sendinblue) API Key",
            value=st.session_state.brevo_api_key,
            type="password"
        )
    
    with col2:
        st.markdown("### Cloudinary")
        cloudinary_cloud_name = st.text_input(
            "Cloud Name",
            value=st.session_state.cloudinary_cloud_name
        )
        cloudinary_api_key = st.text_input(
            "API Key",
            value=st.session_state.cloudinary_api_key,
            type="password"
        )
        cloudinary_api_secret = st.text_input(
            "API Secret",
            value=st.session_state.cloudinary_api_secret,
            type="password"
        )
    
    submitted = st.form_submit_button("Salva configurazione")
    
    if submitted:
        st.session_state.brevo_api_key = brevo_api_key
        st.session_state.cloudinary_cloud_name = cloudinary_cloud_name
        st.session_state.cloudinary_api_key = cloudinary_api_key
        st.session_state.cloudinary_api_secret = cloudinary_api_secret
        
        # Salva anche su .env per persistenza
        with open(".env", "w") as f:
            f.write(f"BREVO_API_KEY={brevo_api_key}\n")
            f.write(f"CLOUDINARY_CLOUD_NAME={cloudinary_cloud_name}\n")
            f.write(f"CLOUDINARY_API_KEY={cloudinary_api_key}\n")
            f.write(f"CLOUDINARY_API_SECRET={cloudinary_api_secret}\n")
        
        st.success("Configurazione salvata con successo!")
        logger.info("Configurazione API aggiornata")

# Istruzioni per l'uso
st.subheader("Istruzioni per l'uso")
st.markdown("""
1. Inserisci le tue API key nei campi sopra
2. Vai alla pagina "Migrazione" nel menu laterale
3. Seleziona le newsletter che vuoi migrare
4. Segui le istruzioni per completare la migrazione
""")

# Status del sistema
st.subheader("Status del sistema")
col1, col2, col3 = st.columns(3)

with col1:
    if os.path.exists("exported_posts.json"):
        with open("exported_posts.json", "r") as f:
            exported = json.load(f)
        st.metric("Newsletter migrate", len(exported))
    else:
        st.metric("Newsletter migrate", 0)

with col2:
    if os.path.exists("converted"):
        num_files = len([f for f in os.listdir("converted") if f.endswith(".md")])
        st.metric("File Markdown generati", num_files)
    else:
        st.metric("File Markdown generati", 0)

with col3:
    if os.path.exists("cookies.json"):
        st.success("Login Substack configurato ✅")
    else:
        st.error("Login Substack non configurato ❌")
        st.markdown("Carica il file `cookies.json` nella directory principale per abilitare il login automatico su Substack.")

# Footer
st.markdown("---")
st.markdown("Developed with ❤️ | [GitHub Repository](https://github.com/lucagaribaldi/newsletter_migrator)")

cat > Home.py << 'EOL'
import streamlit as st
import os
import logging
import json
import logging.config
from dotenv import load_dotenv

# Configurazione logging
try:
    with open('logging_config.json', 'r') as f:
        config = json.load(f)
    logging.config.dictConfig(config)
except Exception as e:
    logging.basicConfig(level=logging.INFO)
    logging.warning(f"Non è stato possibile caricare la configurazione di logging: {e}")

logger = logging.getLogger(__name__)

# Carica variabili d'ambiente
load_dotenv()

st.set_page_config(
    page_title="Newsletter Migrator",
    page_icon="📧",
    layout="wide"
)

st.write("# Newsletter Migrator 📧")

st.markdown(
    "Questa applicazione ti aiuta a migrare le tue newsletter da Brevo (precedentemente Sendinblue) a Substack. "
    "\n\n"
    "### Come funziona: "
    "\n\n"
    "1. Configura le tue API key di Brevo nella sezione \"Migrazione\" "
    "\n2. Visualizza le tue campagne inviate e seleziona quelle da migrare "
    "\n3. Esporta le campagne selezionate in formato compatibile con Substack "
    "\n\n"
    "### Istruzioni: "
    "\n\n"
    "- Vai alla pagina \"Migrazione\" dalla barra laterale "
    "- Inserisci la tua API key di Brevo "
    "- Seleziona le campagne da migrare "
    "- Esporta i contenuti "
    "\n\n"
    "### Note: "
    "\n\n"
    "- L'app salverà le campagne esportate nella cartella \"converted\" "
    "- Un file JSON terrà traccia di cosa è stato esportato"
)

# Informazioni sull'ambiente
env_info = {
    "BREVO_API_KEY": "✓ Configurata" if os.getenv("BREVO_API_KEY") else "❌ Non configurata",
    "BREVO_LIST_ID": "✓ Configurata" if os.getenv("BREVO_LIST_ID") else "⚠️ Opzionale",
    "NEWSLETTER_NAME": "✓ Configurata" if os.getenv("NEWSLETTER_NAME") else "⚠️ Opzionale"
}

st.sidebar.header("Stato configurazione")
for key, value in env_info.items():
    st.sidebar.text(f"{key}: {value}")

st.sidebar.markdown("---")
st.sidebar.info(
    "**Newsletter Migrator** è uno strumento open source. "
    "\n\n"
    "Per maggiori informazioni, visita la [repository GitHub](https://github.com/lucagaribaldi/newsletter_migrator)."
)
EOL

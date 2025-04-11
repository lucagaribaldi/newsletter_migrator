# 📬 Migrazione Newsletter da Brevo a Substack

Web app per trasferire newsletter da Brevo (ex Sendinblue) a Substack con un flusso automatizzato.  
✅ Interfaccia Streamlit  
✅ Automazione via Selenium  
✅ Salvataggio come bozza su Substack  
✅ Gestione duplicati

---

## 🚀 Funzionalità
- Connessione API Brevo
- Selezione delle newsletter
- Conversione HTML → Markdown (con immagini)
- Pulizia automatica del titolo (es. rimuove "Cronache dal Consiglio n xxx -")
- Upload cookie  per accesso a Substack
- Pubblicazione automatica come bozza
- Archivio locale per evitare duplicati
- Storico esportazioni

---

## 🛠️ Tecnologie
- Python
- Streamlit
- Selenium
- BeautifulSoup / html2text
- JSON, requests

---

## 🧪 Come si usa

```bash
# Clona il progetto
git clone https://github.com/lucagaribaldi/newsletter_migrator.git
cd newsletter_migrator

# Crea ambiente virtuale
python3 -m venv venv
source venv/bin/activate

# Installa le dipendenze
pip install -r requirements.txt

# Avvia la web app
streamlit run frontend/streamlit_app.py
```

---

## ⚙️ Note tecniche
- Serve un file  per Substack (puoi esportarlo con strumenti browser)
- Chrome + ChromeDriver devono essere installati localmente
- Le newsletter già migrate vengono memorizzate in 

---

## 📄 Documenti
- 📄 `PDR_Migrazione_Newsletter.txt`: Documento progettuale
- 📄 `REPLIT_SETUP.txt`: Istruzioni per esecuzione su Replit

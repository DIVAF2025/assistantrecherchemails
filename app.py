import streamlit as st
import json
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Configuration
st.set_page_config(page_title="Explorateur Fiscal Gemini", layout="wide")
st.title("🧠 Explorateur de Documents Fiscaux")

# 1. Branchement au JSON sur le Drive
@st.cache_data(ttl=600)
def charger_donnees_fiscales():
    creds_json = json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
    creds = service_account.Credentials.from_service_account_info(
        creds_json, scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    service = build("drive", "v3", credentials=creds)
    
    # REMPLACEZ PAR L'ID RÉEL DE VOTRE FICHIER 'JSON COMPLET GEMINI.json'
    file_id = '1oBmUC5v7BUDPzDGi4IimaD4AVaetDqJV' 
    
    request = service.files().get_media(fileId=file_id)
    content = request.execute()
    return json.loads(content)

# 2. Chargement des données
try:
    data = charger_donnees_fiscales()
    st.sidebar.success(f"{len(data)} documents indexés disponibles.")
except Exception as e:
    st.error(f"Erreur lors du chargement de l'index : {e}")
    data = {}

# 3. Interface de recherche
query = st.text_input("Rechercher dans les documents indexés (ex: sujet, nature, émetteur...)")

if query:
    st.write(f"Résultats pour : '{query}'")
    found = False
    for file_id, info in data.items():
        # On cherche dans les sujets ou le résumé
        contenu_str = (str(info.get('Sujets_traités', [])) + " " + info.get('Résumé_analytique_détaillé', "")).lower()
        if query.lower() in contenu_str:
            with st.expander(f"📄 {info.get('Nature', 'Document')} - {info.get('Date', 'Date inconnue')}"):
                st.write(f"**Emetteur :** {info.get('Emetteur')}")
                st.write(f"**Objet :** {info.get('Objet')}")
                st.write(f"**Résumé :** {info.get('Résumé_analytique_détaillé')}")
                st.write(f"**Sujets :** {', '.join(info.get('Sujets_traités', []))}")
            found = True
    if not found:
        st.info("Aucun document trouvé pour cette recherche.")
else:
    st.write("Entrez un terme pour commencer la recherche dans votre base de données.")

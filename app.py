import streamlit as st
import json
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Configuration de la page
st.set_page_config(page_title="Explorateur Fiscal Gemini", layout="wide")
st.title("🧠 Explorateur de Documents Fiscaux")

# 1. Fonction de chargement sécurisé du JSON depuis le Drive
@st.cache_data(ttl=600)
def charger_donnees_fiscales():
    creds_json = json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
    creds = service_account.Credentials.from_service_account_info(
        creds_json, scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    service = build("drive", "v3", credentials=creds)
    
    # ID de votre fichier JSON COMPLET GEMINI.json
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

# 3. Interface de recherche narrative
query = st.text_input("Posez votre question ou recherchez un sujet :")

if query:
    st.write(f"Résultats pour : '{query}'")
    found = False
    
    for file_id, info in data.items():
        # Extraction sécurisée et conversion forcée en texte
        sujets = info.get('Sujets_traités', [])
        if sujets is None: sujets = []
        sujets_str = ", ".join(sujets) if isinstance(sujets, list) else str(sujets)
        
        resume = info.get('Résumé_analytique_détaillé', "")
        if resume is None: resume = ""
        
        # Sécurisation ultime : on convertit tout en string pour éviter les TypeError
        try:
            contenu_str = (str(sujets_str) + " " + str(resume)).lower()
        except:
            contenu_str = ""
        
        # Comparaison
        if query.lower() in contenu_str:
            with st.expander(f"📄 {info.get('Nature', 'Document')} - {info.get('Date', 'Date inconnue')}"):
                st.write(f"**Emetteur :** {info.get('Emetteur', 'Non spécifié')}")
                st.write(f"**Objet :** {info.get('Objet', 'Non spécifié')}")
                st.write(f"**Résumé :** {resume}")
                st.write(f"**Sujets :** {sujets_str}")
                # Lien cliquable direct vers le document
                st.markdown(f"[🔗 Ouvrir le document sur Google Drive](https://docs.google.com/document/d/{file_id}/view)")
            found = True
            
    if not found:
        st.info("Aucun document trouvé pour cette requête.")
else:
    st.write("Entrez un terme pour lancer la recherche dans votre base de données.")

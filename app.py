import streamlit as st
import json
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Configuration de la page
st.set_page_config(page_title="Assistant Drive", layout="wide")
st.title("🔍 Assistant de Recherche Documentaire")

# 1. Fonction pour connecter le service Drive
def get_drive_service():
    # Récupération de la clé depuis les secrets Streamlit
    creds_json = json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
    creds = service_account.Credentials.from_service_account_info(
        creds_json, 
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    return build("drive", "v3", credentials=creds)

# Initialisation de la connexion
if "service" not in st.session_state:
    try:
        st.session_state.service = get_drive_service()
    except Exception as e:
        st.error(f"Erreur lors de la configuration du service Drive : {e}")

# Interface utilisateur
api_key = st.sidebar.text_input("Clé API OpenAI", type="password")
query = st.text_input("Que cherchez-vous dans vos documents ?")

if st.button("Lancer la recherche"):
    if not api_key:
        st.error("Veuillez entrer votre clé API OpenAI.")
    elif "service" not in st.session_state:
        st.error("Le service Drive n'est pas initialisé.")
    else:
        try:
            st.write("Exploration de votre Drive en cours...")
            # Recherche des fichiers
            results = st.session_state.service.files().list(
                q=f"name contains '{query}' and trashed=false",
                fields="files(id, name, webViewLink)"
            ).execute()
            
            files = results.get("files", [])
            
            if not files:
                st.warning("Aucun document trouvé avec ce nom.")
            else:
                for file in files:
                    st.success(f"Document trouvé : {file['name']}")
                    st.markdown(f"[🔗 Ouvrir le document]({file['webViewLink']})")
                    
        except Exception as e:
            st.error(f"Erreur lors de la recherche : {e}")

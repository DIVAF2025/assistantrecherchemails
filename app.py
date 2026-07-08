import streamlit as st
import json
from googleapiclient.discovery import build
from google.oauth2 import service_account
import openai

# 1. Configuration de l'accès Drive
def get_drive_service():
    creds_dict = json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/drive.readonly"])
    return build("drive", "v3", credentials=creds)

st.title("🔍 Assistant de Recherche Documentaire")
api_key = st.sidebar.text_input("Clé API OpenAI", type="password")

if "service" not in st.session_state:
    st.session_state.service = get_drive_service()

query = st.text_input("Que cherchez-vous dans vos documents ?")

if st.button("Lancer la recherche"):
    if not api_key:
        st.error("Entrez votre clé API OpenAI.")
    else:
        st.write("Exploration de votre Drive en cours...")
        # Recherche simple par nom de fichier
        results = st.session_state.service.files().list(
            q=f"name contains '{query}' and trashed=false",
            fields="files(id, name, webViewLink)"
        ).execute()
        
        files = results.get("files", [])
        
        if not files:
            st.warning("Aucun document trouvé.")
        else:
            for file in files:
                st.success(f"Document trouvé : {file['name']}")
                st.markdown(f"[🔗 Ouvrir le document]({file['webViewLink']})")

import streamlit as st
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

@st.cache_data(ttl=600)
def charger_donnees_depuis_drive():
    # Récupération sécurisée du JSON depuis les Secrets
    raw_json = st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"]
    
    # Transformation en dictionnaire Python
    creds_dict = json.loads(raw_json)
    
    # Création des credentials
    creds = service_account.Credentials.from_service_account_info(
        creds_dict, 
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    
    # Initialisation du service Drive
    service = build("drive", "v3", credentials=creds)
    
    # ID de votre fichier (à remplacer par le vôtre)
    file_id = '137dKYWOv_u9FA6p25O2NteEdKnTkU7RN' 
    
    # Téléchargement et lecture
    request = service.files().get_media(fileId=file_id)
    content = request.execute()
    return json.loads(content)

import streamlit as st
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

@st.cache_data(ttl=600)
def charger_donnees_depuis_drive():
    # Reconstruction manuelle du dictionnaire pour éviter les erreurs de parsing
    creds_dict = {
        "type": "service_account",
        "project_id": st.secrets["GOOGLE_PROJECT_ID"],
        "private_key_id": "cd6da42fa99dd70c2a589347a00748ccd9c46295",
        "private_key": st.secrets["GOOGLE_PRIVATE_KEY"],
        "client_email": st.secrets["GOOGLE_CLIENT_EMAIL"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/assistant-recherche%40assistant-de-recherche-501814.iam.gserviceaccount.com",
        "universe_domain": "googleapis.com"
    }
    
    # Création des credentials
    creds = service_account.Credentials.from_service_account_info(
        creds_dict, 
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    
    # Initialisation du service Drive
    service = build("drive", "v3", credentials=creds)
    
    # ID de votre fichier (à remplacer si nécessaire)
    file_id = '137dKYWOv_u9FA6p25O2NteEdKnTkU7RN' 
    
    # Récupération et lecture du fichier
    request = service.files().get_media(fileId=file_id)
    content = request.execute()
    return json.loads(content)

import streamlit as st
import json
import numpy as np
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
from google.oauth2 import service_account
from googleapiclient.discovery import build

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

@st.cache_data(ttl=3600)
def charger_donnees_depuis_drive():
    # Nettoyage profond de la clé : on transforme le texte '\n' en saut de ligne réel
    # et on s'assure qu'il n'y a pas d'espaces inutiles
    raw_key = st.secrets["GOOGLE_PRIVATE_KEY"]
    formatted_key = raw_key.replace("\\n", "\n")
    
    creds_dict = {
        "type": "service_account",
        "project_id": st.secrets["GOOGLE_PROJECT_ID"],
        "private_key_id": "cd6da42fa99dd70c2a589347a00748ccd9c46295",
        "private_key": formatted_key,
        "client_email": st.secrets["GOOGLE_CLIENT_EMAIL"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/assistant-recherche%40assistant-de-recherche-501814.iam.gserviceaccount.com",
        "universe_domain": "googleapis.com"
    }
    
    # Utilisation explicite du dictionnaire pour créer les credentials
    creds = service_account.Credentials.from_service_account_info(
        creds_dict, 
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    
    service = build("drive", "v3", credentials=creds)
    file_id = '137dKYWOv_u9FA6p25O2NteEdKnTkU7RN' 
    
    request = service.files().get_media(fileId=file_id)
    return json.loads(request.execute())

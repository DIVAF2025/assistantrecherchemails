import streamlit as st
import json
from googleapiclient.discovery import build
from google.oauth2 import service_account
from openai import OpenAI

st.set_page_config(page_title="Assistant IA Drive", layout="wide")
st.title("🧠 Assistant de Recherche Intelligente")

# Configuration des services
api_key = st.sidebar.text_input("Clé API OpenAI", type="password")

def get_drive_service():
    creds_json = json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
    creds = service_account.Credentials.from_service_account_info(
        creds_json, scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    return build("drive", "v3", credentials=creds)

if "service" not in st.session_state:
    st.session_state.service = get_drive_service()

query = st.text_input("Que cherchez-vous ? (ex: 'trouve le projet sur la taxation')")

if st.button("Lancer la recherche IA"):
    if not api_key:
        st.error("Entrez votre clé API OpenAI.")
    else:
        # 1. L'IA extrait le mot-clé
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "Extrais uniquement le mot-clé principal de recherche de cette phrase pour un moteur de recherche de fichiers."},
                      {"role": "user", "content": query}]
        )
        keyword = response.choices[0].message.content.strip().replace('"', '')
        st.write(f"🔍 Recherche intelligente lancée sur : **{keyword}**")
        
        # 2. Recherche sur Drive
        results = st.session_state.service.files().list(
            q=f"name contains '{keyword}' and trashed=false",
            fields="files(id, name, webViewLink)"
        ).execute()
        
        files = results.get("files", [])
        if not files:
            st.warning("Aucun document trouvé.")
        else:
            for file in files:
                st.success(f"Document : {file['name']}")
                st.markdown(f"[🔗 Ouvrir]({file['webViewLink']})")

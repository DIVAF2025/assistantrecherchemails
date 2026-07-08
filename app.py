import streamlit as st
import json
from googleapiclient.discovery import build
from google.oauth2 import service_account
from openai import OpenAI

# Configuration
st.set_page_config(page_title="Recherche Sémantique Drive", layout="wide")
st.title("🧠 Analyse Sémantique de votre Drive")

def get_drive_service():
    creds_json = json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
    creds = service_account.Credentials.from_service_account_info(
        creds_json, scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    return build("drive", "v3", credentials=creds)

if "service" not in st.session_state:
    st.session_state.service = get_drive_service()

api_key = st.sidebar.text_input("Clé API OpenAI", type="password")
query = st.text_input("Quelle est votre recherche narrative ?")

if st.button("Analyser le contenu de tous les documents"):
    if not api_key:
        st.error("Clé API OpenAI requise.")
    else:
        client = OpenAI(api_key=api_key)
        
        # Récupérer TOUS les Google Docs
        st.write("Récupération de la liste des documents...")
        results = st.session_state.service.files().list(
            q="mimeType='application/vnd.google-apps.document' and trashed=false",
            fields="files(id, name, webViewLink)"
        ).execute()
        files = results.get('files', [])
        
        st.write(f"Analyse en cours de {len(files)} documents (basé uniquement sur le contenu)...")
        
        # Analyse de chaque document
        for file in files:
            try:
                # Extraction du contenu
                doc = st.session_state.service.documents().get(documentId=file['id']).execute()
                text = ""
                for element in doc.get('body', {}).get('content', []):
                    if 'paragraph' in element:
                        for run in element.get('paragraph', {}).get('elements', []):
                            text += run.get('textRun', {}).get('content', '')
                
                # Analyse IA focalisée sur le contenu
                prompt = f"Requête utilisateur : '{query}'. \n\nVoici le contenu du document : '{text[:4000]}'. \n\nCe document traite-t-il du sujet demandé ? Réponds 'OUI' suivi d'un résumé court justifiant la pertinence, ou 'NON'."
                
                analysis = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}]
                ).choices[0].message.content
                
                if "OUI" in analysis.upper():
                    with st.expander(f"Pertinent : {file['name']}"):
                        st.write(analysis.replace("OUI", "").replace("oui", "").strip())
                        st.markdown(f"[🔗 Accéder au document]({file['webViewLink']})")
                        
            except Exception as e:
                continue

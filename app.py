import streamlit as st
import json
import numpy as np
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 1. Configuration de l'interface
st.set_page_config(page_title="Explorateur Fiscal Sémantique", page_icon="🧠")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 2. Chargement sécurisé des données (Google Drive)
@st.cache_data(ttl=3600)
def charger_donnees_depuis_drive():
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
    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/drive.readonly"])
    service = build("drive", "v3", credentials=creds)
    file_id = '137dKYWOv_u9FA6p25O2NteEdKnTkU7RN' # REMPLACER PAR VOTRE ID
    request = service.files().get_media(fileId=file_id)
    return json.loads(request.execute())

# 3. Moteur de recherche sémantique
def obtenir_embedding(text):
    return client.embeddings.create(input=[text], model="text-embedding-3-small").data[0].embedding

def rechercher_contexte(query, data):
    query_vec = np.array(obtenir_embedding(query)).reshape(1, -1)
    # On suppose que votre JSON contient une liste d'objets avec "texte" et "vecteur"
    vectors = np.array([item['vecteur'] for item in data])
    similarities = cosine_similarity(query_vec, vectors)
    index_proche = np.argmax(similarities)
    return data[index_proche]['texte']

# 4. Interface Streamlit
st.title("🧠 Explorateur Fiscal Sémantique")
data = charger_donnees_depuis_drive()

query = st.text_input("Posez votre question fiscale :")
if query:
    with st.spinner("Analyse sémantique en cours..."):
        contexte = rechercher_contexte(query, data)
        
        # Génération de la réponse avec GPT
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Tu es un expert fiscal. Réponds en utilisant uniquement le contexte fourni."},
                {"role": "user", "content": f"Contexte : {contexte}\n\nQuestion : {query}"}
            ]
        )
        st.write("### Réponse :")
        st.write(response.choices[0].message.content)
        st.info(f"Source utilisée : {contexte[:100]}...")

import streamlit as st
import json
import numpy as np
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 1. Configuration de l'interface
st.set_page_config(page_title="Explorateur Fiscal Sémantique", page_icon="🧠")

# Initialisation du client OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 2. Fonction de chargement sécurisée (avec correction de la clé privée)
@st.cache_data(ttl=3600)
def charger_donnees_depuis_drive():
    # Correction cruciale pour le formatage PEM de la clé privée
    formatted_key = st.secrets["GOOGLE_PRIVATE_KEY"].replace("\\n", "\n")
    
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
    
    creds = service_account.Credentials.from_service_account_info(
        creds_dict, 
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    
    service = build("drive", "v3", credentials=creds)
    
    # REMPLACEZ 'VOTRE_ID_DU_FICHIER_VECTEURS' par l'ID réel de votre JSON sur Drive
    file_id = '137dKYWOv_u9FA6p25O2NteEdKnTkU7RN' 
    
    request = service.files().get_media(fileId=file_id)
    return json.loads(request.execute())

# 3. Moteur de recherche sémantique
def obtenir_embedding(text):
    response = client.embeddings.create(input=[text], model="text-embedding-3-small")
    return response.data[0].embedding

def rechercher_contexte(query, data):
    query_vec = np.array(obtenir_embedding(query)).reshape(1, -1)
    # Assurez-vous que votre JSON a bien une clé "vecteur"
    vectors = np.array([item['vecteur'] for item in data])
    similarities = cosine_similarity(query_vec, vectors)
    index_proche = np.argmax(similarities)
    return data[index_proche]['texte']

# 4. Interface Streamlit
st.title("🧠 Explorateur Fiscal Sémantique")

try:
    data = charger_donnees_depuis_drive()
    query = st.text_input("Posez votre question fiscale :")
    
    if query:
        with st.spinner("Analyse sémantique en cours..."):
            contexte = rechercher_contexte(query, data)
            
            # Génération de la réponse
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Tu es un expert fiscal. Utilise le contexte fourni pour répondre."},
                    {"role": "user", "content": f"Contexte : {contexte}\n\nQuestion : {query}"}
                ]
            )
            st.write("### Réponse :")
            st.write(response.choices[0].message.content)
            
except Exception as e:
    st.error(f"Une erreur est survenue : {e}")

import streamlit as st
import json
import numpy as np
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Initialisation OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

@st.cache_data(ttl=3600)
def charger_donnees_depuis_drive():
    # Correction clé privée
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
    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/drive.readonly"])
    service = build("drive", "v3", credentials=creds)
    request = service.files().get_media(fileId='137dKYWOv_u9FA6p25O2NteEdKnTkU7RN')
    return json.loads(request.execute())

# ANALYSE SÉMANTIQUE : La "réflexion" de l'IA
def get_embedding(text):
    return client.embeddings.create(input=[text], model="text-embedding-3-small").data[0].embedding

def trouver_meilleur_contexte(query, data):
    query_vec = np.array(get_embedding(query)).reshape(1, -1)
    # Extraction des vecteurs pré-calculés dans ton JSON
    contenus_vecteurs = np.array([item['vecteur'] for item in data])
    
    # Calcul de la similarité cosinus (maths de l'analyse sémantique)
    scores = cosine_similarity(query_vec, contenus_vecteurs)
    meilleur_index = np.argmax(scores)
    
    return data[meilleur_index]['texte'], scores[0][meilleur_index]

# INTERFACE ET TRAITEMENT
st.title("🧠 Explorateur Fiscal Sémantique")
data = charger_donnees_depuis_drive()
query = st.text_input("Posez votre question fiscale :")

if query:
    with st.spinner("Analyse sémantique et recherche dans les textes..."):
        # 1. Analyse : trouver le texte le plus proche
        contexte, score = trouver_meilleur_contexte(query, data)
        
        # 2. Réflexion et Réponse via GPT
        prompt = f"""Tu es un expert fiscal. Basé sur le texte ci-dessous, réponds à la question.
        Contexte fiscal : {contexte}
        
        Question : {query}
        Réponse :"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "Tu es un assistant fiscal précis."},
                      {"role": "user", "content": prompt}]
        )
        
        st.write("### Réponse de l'expert :")
        st.write(response.choices[0].message.content)
        st.caption(f"Confiance de la recherche sémantique : {score:.2%}")

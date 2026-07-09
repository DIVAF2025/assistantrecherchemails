import streamlit as st
import json
import numpy as np
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 1. Initialisation
st.set_page_config(page_title="Explorateur Fiscal Sémantique", page_icon="🧠")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 2. Fonction de chargement avec vérification de structure
@st.cache_data(ttl=3600)
def charger_donnees_depuis_drive():
    creds_info = json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
    creds = service_account.Credentials.from_service_account_info(
        creds_info, scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    service = build("drive", "v3", credentials=creds)
    file_id = '137dKYWOv_u9FA6p25O2NteEdKnTkU7RN'
    request = service.files().get_media(fileId=file_id)
    contenu = request.execute()
    data = json.loads(contenu)
    
    # ÉTAPE CORRIGÉE : Si les données sont dans une clé "documents" ou autre, on l'extrait
    if isinstance(data, dict):
        # On cherche la première clé qui contient une liste
        for key in data:
            if isinstance(data[key], list):
                return data[key]
    return data

# 3. Moteur d'analyse
def get_embedding(text):
    return client.embeddings.create(input=[text], model="text-embedding-3-small").data[0].embedding

def trouver_meilleur_contexte(query, data):
    query_vec = np.array(get_embedding(query)).reshape(1, -1)
    # On s'assure que chaque item a bien la structure attendue
    contenus_vecteurs = np.array([item['vecteur'] for item in data if isinstance(item, dict)])
    scores = cosine_similarity(query_vec, contenus_vecteurs)
    meilleur_index = np.argmax(scores)
    return data[meilleur_index]['texte'], scores[0][meilleur_index]

# 4. Interface
st.title("🧠 Explorateur Fiscal Sémantique")
data = charger_donnees_depuis_drive()

query = st.text_input("Posez votre question fiscale :")

if query:
    with st.spinner("Analyse en cours..."):
        try:
            contexte, score = trouver_meilleur_contexte(query, data)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Tu es un expert fiscal précis."},
                    {"role": "user", "content": f"Contexte : {contexte}\n\nQuestion : {query}"}
                ]
            )
            st.write("### Réponse :")
            st.write(response.choices[0].message.content)
            st.caption(f"Score de fiabilité : {score:.2%}")
        except Exception as e:
            st.error(f"Erreur de traitement des données : {e}")

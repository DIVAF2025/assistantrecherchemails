import streamlit as st
import json
import numpy as np
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
from google.oauth2 import service_account
from googleapiclient.discovery import build

st.set_page_config(page_title="Explorateur Fiscal Sémantique", page_icon="🧠")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

@st.cache_data(ttl=3600)
def charger_donnees_depuis_drive():
    creds_info = json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
    creds = service_account.Credentials.from_service_account_info(
        creds_info, scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    service = build("drive", "v3", credentials=creds)
    # ID de votre fichier
    file_id = '137dKYWOv_u9FA6p25O2NteEdKnTkU7RN'
    request = service.files().get_media(fileId=file_id)
    contenu = request.execute()
    data = json.loads(contenu)
    return data

def trouver_meilleur_contexte(query, data):
    # 1. Vérification que les données ne sont pas vides
    if not data:
        raise ValueError("Le fichier JSON est vide ou mal lu.")
    
    # 2. Extraction des vecteurs (on s'assure que 'vecteur' existe bien)
    vectors = [item.get('vecteur') for item in data if isinstance(item, dict) and 'vecteur' in item]
    
    if not vectors:
        raise ValueError("Aucun vecteur trouvé dans le fichier. Vérifiez la structure du JSON.")

    query_vec = np.array(client.embeddings.create(input=[query], model="text-embedding-3-small").data[0].embedding).reshape(1, -1)
    contenus_vecteurs = np.array(vectors)
    
    scores = cosine_similarity(query_vec, contenus_vecteurs)
    meilleur_index = np.argmax(scores)
    
    return data[meilleur_index]['texte'], scores[0][meilleur_index]

st.title("🧠 Explorateur Fiscal Sémantique")

try:
    data = charger_donnees_drive() # Note: assurez-vous du nom de la fonction
    query = st.text_input("Posez votre question fiscale :")
    
    if query:
        with st.spinner("Analyse en cours..."):
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
except Exception as e:
    st.error(f"Erreur : {e}")

import streamlit as st
import json
import numpy as np
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 1. Configuration et Initialisation
st.set_page_config(page_title="Explorateur Fiscal Sémantique", page_icon="🧠")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 2. Fonction de chargement sécurisée via le JSON unique
@st.cache_data(ttl=3600)
def charger_donnees_depuis_drive():
    # Chargement du JSON complet depuis les secrets
    creds_info = json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
    
    # Authentification Google Drive
    creds = service_account.Credentials.from_service_account_info(
        creds_info, 
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    
    service = build("drive", "v3", credentials=creds)
    
    # ID du fichier JSON sur Drive
    file_id = '137dKYWOv_u9FA6p25O2NteEdKnTkU7RN'
    
    request = service.files().get_media(fileId=file_id)
    return json.loads(request.execute())

# 3. Moteur d'analyse sémantique
def get_embedding(text):
    return client.embeddings.create(input=[text], model="text-embedding-3-small").data[0].embedding

def trouver_meilleur_contexte(query, data):
    query_vec = np.array(get_embedding(query)).reshape(1, -1)
    # On extrait les vecteurs du JSON (doit contenir une clé "vecteur")
    contenus_vecteurs = np.array([item['vecteur'] for item in data])
    
    # Calcul de la similarité cosinus
    scores = cosine_similarity(query_vec, contenus_vecteurs)
    meilleur_index = np.argmax(scores)
    
    return data[meilleur_index]['texte'], scores[0][meilleur_index]

# 4. Interface Streamlit
st.title("🧠 Explorateur Fiscal Sémantique")

try:
    data = charger_donnees_depuis_drive()
    query = st.text_input("Posez votre question fiscale :")
    
    if query:
        with st.spinner("Analyse sémantique en cours..."):
            # Recherche du contexte le plus pertinent
            contexte, score = trouver_meilleur_contexte(query, data)
            
            # Génération de la réponse via GPT
            prompt = f"""Tu es un expert fiscal. Basé sur le texte ci-dessous, réponds à la question.
            Si le contexte ne permet pas de répondre, dis-le clairement.
            
            Contexte fiscal : {contexte}
            
            Question : {query}
            Réponse :"""
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Tu es un assistant fiscal précis et rigoureux."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            st.write("### Réponse de l'expert :")
            st.write(response.choices[0].message.content)
            st.caption(f"Score de similarité sémantique : {score:.2%}")
            
except Exception as e:
    st.error(f"Erreur lors de l'exécution : {e}")

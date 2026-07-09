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
    
    # Transformation : on convertit le dictionnaire {id: {contenu}} en liste [{contenu}]
    # pour que le moteur de recherche puisse l'utiliser facilement.
    liste_documents = []
    for doc_id, infos in data.items():
        # On renomme 'embedding' en 'vecteur' pour la cohérence du moteur
        infos['vecteur'] = infos.get('embedding', [])
        infos['texte'] = infos.get('Résumé_analytique_détaillé', '')
        liste_documents.append(infos)
    return liste_documents

def trouver_meilleur_contexte(query, data):
    # Extraction sécurisée des vecteurs
    vectors = [item.get('vecteur') for item in data if item.get('vecteur')]
    
    if not vectors:
        raise ValueError("Aucun vecteur trouvé dans le fichier.")

    query_vec = np.array(client.embeddings.create(input=[query], model="text-embedding-3-small").data[0].embedding).reshape(1, -1)
    
    # Calcul des similarités
    scores = cosine_similarity(query_vec, np.array(vectors))
    meilleur_index = np.argmax(scores)
    
    return data[meilleur_index].get('texte', 'Texte non trouvé'), scores[0][meilleur_index]

# Interface
st.title("🧠 Explorateur Fiscal Sémantique")

try:
    data = charger_donnees_depuis_drive()
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
            st.write("### Réponse de l'expert :")
            st.write(response.choices[0].message.content)
            st.caption(f"Score de similarité : {score:.2%}")
            
except Exception as e:
    st.error(f"Erreur : {e}")

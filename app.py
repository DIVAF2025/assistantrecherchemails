import streamlit as st
import json
import numpy as np
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Configuration de la page
st.set_page_config(page_title="Explorateur Fiscal Sémantique", layout="wide")
st.title("🧠 Explorateur Fiscal Sémantique")

# Initialisation des clients
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

@st.cache_data(ttl=600)
def charger_donnees_depuis_drive():
    # Connexion à Google Drive
    creds_json = json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
    creds = service_account.Credentials.from_service_account_info(
        creds_json, scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    service = build("drive", "v3", credentials=creds)
    
    # REMPLACEZ CECI par l'ID de votre fichier JSON_COMPLET_GEMINI_VECTEURS.json
    file_id = '137dKYWOv_u9FA6p25O2NteEdKnTkU7RN' 
    
    request = service.files().get_media(fileId=file_id)
    content = request.execute()
    return json.loads(content)

def get_embedding(text):
    response = client.embeddings.create(input=[text], model="text-embedding-3-small")
    return response.data[0].embedding

# Chargement des données
try:
    data = charger_donnees_depuis_drive()
    st.sidebar.success(f"{len(data)} documents prêts.")
except Exception as e:
    st.error(f"Erreur de chargement Drive : {e}")
    st.stop()

# Interface de recherche
query = st.text_input("Posez votre question (ex: 'personnel de la DGI') :")

if query:
    with st.spinner('Recherche sémantique en cours...'):
        query_vec = np.array(get_embedding(query)).reshape(1, -1)
        results = []

        for file_id, info in data.items():
            doc_vec = info.get('embedding', [])
            if doc_vec:
                # Calcul de similarité cosinus
                score = cosine_similarity(query_vec, np.array(doc_vec).reshape(1, -1))[0][0]
                if score > 0.4: # Seuil de pertinence
                    results.append((score, info))

        # Trier par score décroissant
        results.sort(key=lambda x: x[0], reverse=True)

        if results:
            for score, info in results[:10]:
                with st.expander(f"Pertinence: {score:.2f} | 📄 {info.get('Nature', 'Document')}"):
                    st.write(f"**Résumé :** {info.get('Résumé_analytique_détaillé', '')}")
                    lien = info.get('webViewLink', '#')
                    st.markdown(f"[🔗 Ouvrir sur Drive]({lien})")
        else:
            st.info("Aucun résultat assez pertinent trouvé.")

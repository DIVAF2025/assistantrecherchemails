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
    file_id = '137dKYWOv_u9FA6p25O2NteEdKnTkU7RN'
    request = service.files().get_media(fileId=file_id)
    data = json.loads(request.execute())
    
    # Transformation du dictionnaire complexe en liste plate pour la recherche
    liste_docs = []
    for doc_id, infos in data.items():
        infos['id'] = doc_id
        infos['vecteur'] = infos.get('embedding', [])
        liste_docs.append(infos)
    return liste_docs

def recherche_semantique(query, data, top_n=3):
    # Calcul vecteur question
    query_vec = np.array(client.embeddings.create(input=[query], model="text-embedding-3-small").data[0].embedding).reshape(1, -1)
    
    # Calcul similarité avec tous les docs
    vectors = [item.get('vecteur') for item in data if item.get('vecteur')]
    scores = cosine_similarity(query_vec, np.array(vectors))[0]
    
    # On récupère les indices des documents les plus proches (triés par score décroissant)
    indices = np.argsort(scores)[::-1][:top_n]
    
    resultats = []
    for idx in indices:
        if scores[idx] > 0.5: # Seuil de pertinence
            resultats.append((data[idx], scores[idx]))
    return resultats

# 2. Interface
st.title("📂 Explorateur Fiscal Sémantique")
data = charger_donnees_depuis_drive()
query = st.text_input("Rechercher dans les documents (compréhension sémantique) :")

if query:
    with st.spinner("Recherche des documents les plus pertinents..."):
        resultats = recherche_semantique(query, data)
        
        if not resultats:
            st.warning("Aucun document trouvé correspondant à votre recherche.")
        else:
            st.write(f"### {len(resultats)} documents trouvés :")
            for doc, score in resultats:
                with st.expander(f"📄 {doc.get('Objet', 'Sans objet')} (Date: {doc.get('Date', 'N/A')})"):
                    st.write(f"**Emetteur :** {doc.get('Emetteur')}")
                    st.write(f"**Résumé :** {doc.get('Résumé_analytique_détaillé')}")
                    st.write(f"**Score de pertinence :** {score:.2%}")

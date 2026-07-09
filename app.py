import streamlit as st
import json
import numpy as np
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 1. Configuration
st.set_page_config(page_title="Explorateur Fiscal Sémantique", page_icon="📂")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 2. Chargement des données depuis Google Drive
@st.cache_data(ttl=3600)
def charger_donnees_depuis_drive():
    creds_info = json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
    creds = service_account.Credentials.from_service_account_info(
        creds_info, scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    service = build("drive", "v3", credentials=creds)
    file_id = '137dKYWOv_u9FA6p25O2NteEdKnTkU7RN'
    
    request = service.files().get_media(fileId=file_id)
    raw_data = json.loads(request.execute())
    
    # Transformation du dictionnaire complexe en liste exploitable
    liste_docs = []
    for doc_id, infos in raw_data.items():
        infos['id'] = doc_id
        # On s'assure que le vecteur est bien sous la clé 'embedding'
        infos['vecteur'] = infos.get('embedding', [])
        liste_docs.append(infos)
    return liste_docs

# 3. Moteur de recherche Sémantique
def recherche_semantique(query, data, top_n=3):
    # Génération du vecteur de la question avec le même modèle
    query_vec = np.array(client.embeddings.create(
        input=[query], model="text-embedding-3-small"
    ).data[0].embedding).reshape(1, -1)
    
    # Extraction des vecteurs du JSON
    vectors = [item.get('vecteur') for item in data if item.get('vecteur')]
    
    if not vectors:
        return []

    # Calcul de similarité
    scores = cosine_similarity(query_vec, np.array(vectors))[0]
    
    # Tri des résultats par score décroissant
    indices = np.argsort(scores)[::-1][:top_n]
    
    resultats = []
    for idx in indices:
        # Seuil de pertinence (0.1 permet d'avoir plus de résultats, ajuste si besoin)
        if scores[idx] > 0.1: 
            resultats.append((data[idx], scores[idx]))
    return resultats

# 4. Interface Utilisateur
st.title("📂 Explorateur Fiscal Sémantique")
data = charger_donnees_depuis_drive()
query = st.text_input("Rechercher dans les documents (sens du contenu) :")

if query:
    with st.spinner("Analyse sémantique en cours..."):
        resultats = recherche_semantique(query, data)
        
        if not resultats:
            st.warning("Aucun document pertinent trouvé.")
        else:
            st.write(f"### {len(resultats)} document(s) trouvé(s) :")
            
            for doc, score in resultats:
                # Affichage sous forme de fiche structurée
                with st.expander(f"📄 {doc.get('Objet', 'Sans objet')} | {doc.get('Date', '')}"):
                    st.write(f"**Emetteur :** {doc.get('Emetteur')}")
                    st.write(f"**Résumé :** {doc.get('Résumé_analytique_détaillé')}")
                    st.caption(f"Score de pertinence sémantique : {score:.2%}")

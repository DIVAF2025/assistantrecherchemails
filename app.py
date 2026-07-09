import streamlit as st
import json
import numpy as np
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity

# Initialisation OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def get_embedding(text):
    response = client.embeddings.create(input=[text], model="text-embedding-3-small")
    return response.data[0].embedding

@st.cache_data(ttl=600)
def charger_donnees():
    # Remplacez par le nom de votre fichier vecteur
    with open('JSON_COMPLET_GEMINI_VECTEURS.json', 'r', encoding='utf-8') as f:
        return json.load(f)

data = charger_donnees()

st.title("🧠 Explorateur Fiscal Sémantique")
query = st.text_input("Posez votre question (ex: 'personnel de la DGI') :")

if query:
    query_vec = np.array(get_embedding(query)).reshape(1, -1)
    results = []

    for file_id, info in data.items():
        doc_vec = info.get('embedding', [])
        if doc_vec:
            # Calcul de similarité
            score = cosine_similarity(query_vec, np.array(doc_vec).reshape(1, -1))[0][0]
            if score > 0.4: # Seuil de pertinence (ajustable)
                results.append((score, info))

    # Trier par score décroissant
    results.sort(key=lambda x: x[0], reverse=True)

    if results:
        for score, info in results[:10]: # Affiche les 10 meilleurs
            with st.expander(f"Pertinence: {score:.2f} | 📄 {info.get('Nature', 'Doc')}"):
                st.write(f"**Résumé :** {info.get('Résumé_analytique_détaillé', '')}")
                lien = info.get('webViewLink', '#')
                st.markdown(f"[🔗 Ouvrir sur Drive]({lien})")
    else:
        st.info("Aucun résultat assez pertinent trouvé.")

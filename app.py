import streamlit as st
import json
from openai import OpenAI
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 1. Configuration et authentification
st.set_page_config(page_title="Explorateur Fiscal Intelligent", page_icon="🧠")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

@st.cache_data(ttl=3600)
def charger_donnees_depuis_drive():
    creds_info = json.loads(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
    creds = service_account.Credentials.from_service_account_info(
        creds_info, scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    service = build("drive", "v3", credentials=creds)
    file_id = '1oBmUC5v7BUDPzDGi4IimaD4AVaetDqJV'
    request = service.files().get_media(fileId=file_id)
    return json.loads(request.execute())

def filtrage_intelligent(query, data, top_n=100):
    """
    Sélectionne les 100 documents les plus pertinents par mots-clés.
    Résistant aux inversions de mots (ex: 'agents et cadres' vs 'cadres et agents').
    """
    query_words = set(query.lower().replace(" et ", " ").split())
    scores = []
    
    for doc_id, doc in data.items():
        texte_doc = (doc.get('Objet', '') + " " + doc.get('Résumé_analytique_détaillé', '')).lower()
        score = sum(1 for mot in query_words if mot in texte_doc)
        
        # Bonus si la requête entière est présente
        if query.lower() in texte_doc:
            score += 5
            
        scores.append((doc_id, doc, score))
    
    # Tri par score décroissant et on garde les 100 premiers ayant au moins un mot en commun
    scores.sort(key=lambda x: x[2], reverse=True)
    return [s for s in scores if s[2] > 0][:top_n]

def analyser_par_ia(query, data):
    # 1. Filtrage préalable pour rester sous la limite de tokens
    candidats = filtrage_intelligent(query, data)
    
    if not candidats:
        return "Aucun document trouvé correspondant à vos critères."

    # 2. Construction du contexte
    contexte = ""
    for doc_id, doc, _ in candidats:
        contexte += f"ID: {doc_id} | Objet: {doc.get('Objet', 'N/A')} | Date: {doc.get('Date', 'N/A')} | Résumé: {doc.get('Résumé_analytique_détaillé', '')}\n---\n"

    # 3. Prompt structuré
    prompt = f"""
    Tu es un bibliothécaire fiscal expert. Requête utilisateur : "{query}"
    
    Analyse les {len(candidats)} documents fournis.
    Identifie et classe les 10 plus pertinents par ordre de pertinence décroissant.
    Pour chaque document, retourne strictement ce format :
    ---
    NOM: [Objet]
    DATE: [Date]
    RÉSUMÉ: [Résumé_analytique_détaillé]
    LIEN: https://drive.google.com/open?id=[ID]
    ---
    
    Documents à analyser :
    {contexte}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "Tu es un expert fiscal précis."},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# 2. Interface Streamlit
st.title("📂 Recherche Fiscale Avancée")
data = charger_donnees_depuis_drive()
query = st.text_input("Quelle information recherchez-vous dans vos documents ?")

if query:
    with st.spinner("Analyse intelligente en cours..."):
        try:
            resultats = analyser_par_ia(query, data)
            st.markdown(resultats)
        except Exception as e:
            st.error(f"Une erreur est survenue lors de l'analyse : {e}")

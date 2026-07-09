import streamlit as st
import json
from openai import OpenAI
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 1. Configuration
st.set_page_config(page_title="Explorateur Fiscal Intelligent", page_icon="📂")
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
    """Filtre les 100 documents les plus pertinents sans erreur de type."""
    query_words = set(query.lower().replace(" et ", " ").split())
    scores = []
    
    for doc_id, doc in data.items():
        if not isinstance(doc, dict): continue
        
        # Extraction sécurisée de chaque champ en chaîne de texte
        obj = str(doc.get('Objet', ''))
        res = str(doc.get('Résumé_analytique_détaillé', ''))
        sujets_raw = doc.get('Sujets_traités', [])
        sujets = ", ".join([str(s) for s in sujets_raw]) if isinstance(sujets_raw, list) else str(sujets_raw)
        
        texte_doc = (obj + " " + res + " " + sujets).lower()
        
        score = sum(1 for mot in query_words if mot in texte_doc)
        if query.lower() in texte_doc:
            score += 5
            
        scores.append((doc_id, doc, score))
    
    scores.sort(key=lambda x: x[2], reverse=True)
    return [s for s in scores if s[2] > 0][:top_n]

def analyser_par_ia(query, data):
    """Analyse sémantique fine par GPT-4o."""
    candidats = filtrage_intelligent(query, data)
    
    if not candidats:
        return "Aucun document trouvé correspondant à vos critères."

    contexte = ""
    for doc_id, doc, _ in candidats:
        obj = str(doc.get('Objet', 'N/A'))
        date = str(doc.get('Date', 'N/A'))
        resume = str(doc.get('Résumé_analytique_détaillé', ''))
        sujets_raw = doc.get('Sujets_traités', [])
        sujets = ", ".join([str(s) for s in sujets_raw]) if isinstance(sujets_raw, list) else str(sujets_raw)
        
        contexte += f"ID: {doc_id} | NOM: {obj} | DATE: {date} | SUJETS: {sujets} | RÉSUMÉ: {resume}\n---\n"

    prompt = f"""
    Tu es un bibliothécaire fiscal expert. Requête : "{query}"
    
    Analyse ces documents et classe les 10 plus pertinents par ordre de pertinence décroissant.
    Retourne uniquement le format suivant :
    ---
    NOM: [Objet]
    DATE: [Date]
    RÉSUMÉ: [Résumé]
    LIEN: https://drive.google.com/open?id={doc_id}
    ---
    Documents :
    {contexte}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "Expert fiscal précis."},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# 2. Interface Streamlit
st.title("📂 Recherche Fiscale Avancée")
data = charger_donnees_depuis_drive()
query = st.text_input("Quelle information recherchez-vous ?")

if query:
    with st.spinner("Analyse intelligente en cours..."):
        try:
            st.markdown(analyser_par_ia(query, data))
        except Exception as e:
            st.error(f"Une erreur est survenue : {e}")

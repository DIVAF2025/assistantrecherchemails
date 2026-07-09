import streamlit as st
import json
from openai import OpenAI
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 1. Configuration
st.set_page_config(page_title="Recherche Fiscale Intelligente", page_icon="🧠")
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

def trier_documents_par_pertinence(query, data):
    # On prépare le contexte pour l'IA
    contexte = ""
    for doc_id, doc in data.items():
        contexte += f"ID: {doc_id} | Objet: {doc.get('Objet', 'N/A')} | Date: {doc.get('Date', 'N/A')} | Résumé: {doc.get('Résumé_analytique_détaillé', '')}\n---\n"

    # Le prompt demande à l'IA de faire le tri et de formater le résultat
    prompt = f"""
    Tu es un expert en recherche documentaire fiscale.
    Requête utilisateur : "{query}"
    
    Parmi la liste de documents ci-dessous, identifie les 10 plus pertinents.
    Classe-les du plus pertinent au moins pertinent.
    
    Pour chaque document identifié, retourne-le sous ce format strict :
    ---
    NOM: [Objet du document]
    DATE: [Date]
    RÉSUMÉ: [Résumé_analytique_détaillé]
    LIEN: https://drive.google.com/open?id=[ID]
    ---
    
    Liste des documents :
    {contexte}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "Tu es un bibliothécaire fiscal précis."},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# 2. Interface
st.title("📂 Recherche Fiscale par Compréhension")
data = charger_donnees_depuis_drive()
query = st.text_input("Posez votre question pour une analyse sémantique globale :")

if query:
    with st.spinner("Analyse intelligente de tous les documents en cours..."):
        try:
            resultats_formates = trier_documents_par_pertinence(query, data)
            st.markdown(resultats_formates)
        except Exception as e:
            st.error(f"Une erreur est survenue lors de l'analyse : {e}")

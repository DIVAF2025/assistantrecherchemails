import streamlit as st
import json
from openai import OpenAI
from google.oauth2 import service_account
from googleapiclient.discovery import build

st.set_page_config(page_title="Recherche Fiscale", page_icon="📂")
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

def obtenir_resultats_structures(query, data):
    # On prépare tout le catalogue en texte simple pour l'IA
    catalogue = ""
    for doc_id, doc in data.items():
        catalogue += f"ID: {doc_id} | OBJET: {doc.get('Objet', '')} | RÉSUMÉ: {doc.get('Résumé_analytique_détaillé', '')}\n"
    
    # Prompt direct pour extraire les IDs des 10 plus pertinents
    prompt = f"""
    Requête utilisateur : "{query}"
    Parmi les documents suivants, trouve les 10 plus pertinents. 
    Retourne UNIQUEMENT une liste JSON d'IDs comme ceci: {{"ids": ["id1", "id2", ...]}}
    
    Catalogue :
    {catalogue}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={ "type": "json_object" }
    )
    
    data_json = json.loads(response.choices[0].message.content)
    ids_selectionnes = data_json.get("ids", [])
    
    # Construction de la réponse finale
    resultats = []
    for cid in ids_selectionnes:
        if cid in data:
            doc = data[cid]
            resultats.append({
                "id": cid,
                "nom": doc.get('Objet', 'Sans nom'),
                "date": doc.get('Date', 'N/A'),
                "resume": doc.get('Résumé_analytique_détaillé', 'Aucun résumé disponible.')
            })
    return resultats

st.title("📂 Recherche Fiscale")
data = charger_donnees_depuis_drive()
query = st.text_input("Posez votre question :")

if query:
    with st.spinner("Analyse intelligente en cours..."):
        try:
            results = obtenir_resultats_structures(query, data)
            if results:
                for res in results:
                    with st.expander(f"📄 {res['nom']} ({res['date']})"):
                        st.write(f"**Résumé détaillé :**")
                        st.write(res['resume'])
                        st.markdown(f"🔗 [Accéder au document sur Drive](https://drive.google.com/open?id={res['id']})")
            else:
                st.warning("Aucun document ne semble correspondre à votre requête.")
        except Exception as e:
            st.error(f"Erreur : {e}")

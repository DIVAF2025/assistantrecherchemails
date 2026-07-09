import streamlit as st
import json
from openai import OpenAI
from google.oauth2 import service_account
from googleapiclient.discovery import build

st.set_page_config(page_title="Recherche Documentaire", page_icon="📂")
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
    # 1. Filtrage local (Python pur) pour réduire le volume avant l'IA
    query_words = set(query.lower().replace(" et ", " ").split())
    candidats = []
    for doc_id, doc in data.items():
        texte = (str(doc.get('Objet', '')) + " " + str(doc.get('Résumé_analytique_détaillé', ''))).lower()
        score = sum(1 for mot in query_words if mot in texte)
        if score > 0:
            candidats.append((doc_id, {"id": doc_id, "objet": doc.get('Objet'), "resume": doc.get('Résumé_analytique_détaillé')}, score))
    
    # On garde les 50 meilleurs
    candidats.sort(key=lambda x: x[2], reverse=True)
    top_50 = candidats[:50]
    
    # 2. Appel IA avec un contexte réduit (50 docs max)
    catalogue_reduit = {c[0]: c[1] for c in top_50}
    
    prompt = f"""
    Requête : "{query}"
    Parmi ces {len(catalogue_reduit)} documents, trouve les 10 plus pertinents.
    Retourne UNIQUEMENT une liste JSON d'IDs comme ceci: {{"ids": ["id1", "id2", ...]}}
    Catalogue : {json.dumps(catalogue_reduit)}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={ "type": "json_object" }
    )
    
    ids_selectionnes = json.loads(response.choices[0].message.content).get("ids", [])
    
    # 3. Construction des résultats avec injection de l'ID pour garantir son existence
    resultats_finaux = []
    for cid in ids_selectionnes:
        if cid in data:
            doc_final = data[cid].copy()
            doc_final['id'] = cid
            resultats_finaux.append(doc_final)
            
    return resultats_finaux

st.title("📂 Recherche Fiscale")
data = charger_donnees_depuis_drive()
query = st.text_input("Posez votre question :")

if query:
    with st.spinner("Analyse intelligente en cours..."):
        try:
            results = obtenir_resultats_structures(query, data)
            if results:
                for res in results:
                    # On récupère l'ID injecté dans le dictionnaire
                    doc_id = res.get('id', '')
                    
                    with st.expander(f"📄 {res.get('Objet', 'Sans nom')} ({res.get('Date', 'N/A')})"):
                        st.write("**Résumé détaillé :**")
                        st.write(res.get('Résumé_analytique_détaillé', 'Aucun résumé disponible.'))
                        
                        # Ici le lien est corrigé avec l'ID dynamique
                        if doc_id:
                            st.markdown(f"🔗 [Accéder au document](https://drive.google.com/open?id={doc_id})")
                        else:
                            st.warning("Lien indisponible pour ce document.")
        except Exception as e:
            st.error(f"Erreur : {e}")

import streamlit as st
import json
from openai import OpenAI
from google.oauth2 import service_account
from googleapiclient.discovery import build

# CSS pour une interface plus légère
st.markdown("""
    <style>
    .stMarkdown, .stText, .stExpander { font-size: 13px !important; }
    </style>
    """, unsafe_allow_html=True)

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

def filtrage_intelligent(query, data, top_n=50):
    query_words = set(query.lower().replace(" et ", " ").split())
    scores = []
    for doc_id, doc in data.items():
        if not isinstance(doc, dict): continue
        texte_doc = (str(doc.get('Objet', '')) + " " + str(doc.get('Résumé_analytique_détaillé', ''))).lower()
        score = sum(1 for mot in query_words if mot in texte_doc)
        if query.lower() in texte_doc: score += 5
        scores.append((doc_id, doc, score))
    scores.sort(key=lambda x: x[2], reverse=True)
    return [s for s in scores if s[2] > 0][:top_n]

def obtenir_resultats_structures(query, data):
    candidats = filtrage_intelligent(query, data)
    if not candidats: return None

    # On prépare la liste des candidats pour que l'IA choisisse juste les indices
    # On envoie le moins de texte possible pour accélérer l'IA
    liste_candidats = [{"id": cid, "objet": doc.get('Objet')} for cid, doc, _ in candidats]
    
    prompt = f"""
    Requête utilisateur : "{query}"
    Parmi la liste suivante, identifie les 10 documents les plus pertinents et retourne uniquement leurs ID dans une liste JSON.
    Liste : {json.dumps(liste_candidats)}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={ "type": "json_object" }
    )
    
    ids_selectionnes = json.loads(response.choices[0].message.content).get("ids", [])
    
    # On reconstruit la liste finale en récupérant le texte COMPLET depuis 'data'
    resultats_complets = []
    for cid in ids_selectionnes:
        if cid in data:
            doc = data[cid]
            resultats_complets.append({
                "id": cid,
                "nom": doc.get('Objet', 'Sans nom'),
                "date": doc.get('Date', 'N/A'),
                "resume": doc.get('Résumé_analytique_détaillé', 'Aucun résumé disponible.'),
            })
    return resultats_complets

st.title("📂 Recherche Fiscale")
data = charger_donnees_depuis_drive()
query = st.text_input("Posez votre question :")

if query:
    with st.spinner("Analyse..."):
        results = obtenir_resultats_structures(query, data)
        if results:
            for res in results:
                with st.expander(f"📄 {res['nom']} ({res['date']})"):
                    st.write(f"**Résumé détaillé :**")
                    st.write(res['resume']) # Ici on affiche le texte brut sans altération
                    st.markdown(f"🔗 [Accéder au document sur Drive](https://drive.google.com/open?id={res['id']})")
        else:
            st.info("Aucun résultat trouvé.")

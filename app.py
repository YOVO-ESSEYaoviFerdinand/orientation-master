"""
Trouve ton Master, outil d'orientation L3 vers Master
Faculte des Sciences Economiques, Universite de Rennes

Pose le questionnaire, calcule le score selon le bareme de
Base_Donnees_Questionnaire_Complete_V2.xlsx, et affiche le top 3 des
masters recommandes (nom + debouches uniquement, jamais le taux
d'insertion ni le salaire).

Ouvert aux etudiants de L1, L2 et L3, de Rennes ou d'ailleurs.
Comprend un module "Je ne sais pas" pour les etudiants indecis.
"""

import streamlit as st
import pandas as pd

DATA_FILE = "Base_Donnees_Questionnaire_Complete_V2.xlsx"
BASE_SCORE = 100 / 12

# ==================================================================
# DONNEES DU MODULE "JE NE SAIS PAS"
# (8 questions generales, non stockees dans le classeur Excel : elles
#  ne portent pas sur un master mais sur une famille entiere, et leur
#  role change une fois utilisees -> logique de navigation, pas de
#  contenu de bloc. Chaque famille apparait exactement 3 fois, et
#  aucune paire de familles ne se retrouve deux fois dans la meme
#  question -- verifie par simulation, cf. feuille Regles_Generales.)
# ==================================================================
JNS_QUESTIONS = [
    ("JNS1", "Vous aimez creuser les chiffres, analyser des graphiques et "
             "manipuler des données pour comprendre une situation.",
     ["MAS", "IEF"]),
    ("JNS2", "Vous vous intéressez à la vie des entreprises, à la gestion "
             "d'équipe ou au monde de la banque et de la finance.",
     ["MBFA", "MI"]),
    ("JNS3", "Vous cherchez constamment à moderniser ce qui existe déjà, à "
             "lancer de nouvelles idées ou à restructurer un fonctionnement.",
     ["MI", "EEET"]),
    ("JNS4", "L'écologie ou la lutte contre les inégalités sociales vous "
             "motivent fortement dans le choix d'un métier.",
     ["EEET", "IMEPP"]),
    ("JNS5", "Vous préférez vous baser sur des rapports officiels, des "
             "enquêtes de terrain ou des textes de loi pour guider l'action "
             "d'une organisation.",
     ["IMEPP", "IEF"]),
    ("JNS6", "Face à un problème inédit, vous préférez inventer une solution "
             "sur-mesure plutôt que d'appliquer une procédure standard déjà "
             "existante.",
     ["MAS", "MI"]),
    ("JNS7", "Vous aimeriez utiliser des données et des indicateurs pour "
             "prendre des décisions importantes, que ce soit en entreprise "
             "ou pour l'intérêt général.",
     ["MBFA", "MAS", "IMEPP"]),
    ("JNS8", "Vous aimeriez analyser l'impact économique, financier ou sur "
             "les prix de grands projets liés à l'énergie, aux transports "
             "ou à l'industrie.",
     ["MBFA", "IEF", "EEET"]),
]

LICENCE_LABELS = {
    "MIASHS": "MIASHS (Mathématiques et Informatique Appliquées aux Sciences Sociales)",
    "EcoGestion": "Éco-Gestion classique (+ option LAS, Licence avec option Accès Santé)",
    "SI": "Éco-Gestion Section Internationale (SI)",
    "CPES": "Éco-Gestion CPES (Cursus Préparatoire aux Études Supérieures)",
    "BBAF": "Éco-Gestion BBAF (Bachelor in Business and Applied Finance)",
    "BBAE": "Éco-Gestion BBAE (Bachelor in Business and Applied Economics)",
}

DESTINATION_ORDER = ["MAS", "IEF", "MBFA", "MI", "EEET", "IMEPP"]
JE_NE_SAIS_PAS = "__JNSP__"


# ==================================================================
# CHARGEMENT DES DONNEES (mis en cache)
# ==================================================================
@st.cache_data
def charger_donnees():
    questions = pd.read_excel(DATA_FILE, sheet_name="Questions")
    bareme_df = pd.read_excel(DATA_FILE, sheet_name="Bareme_Detaille")
    destinations = pd.read_excel(DATA_FILE, sheet_name="Destinations")
    masters_df = pd.read_excel(DATA_FILE, sheet_name="Masters")
    coherence_df = pd.read_excel(DATA_FILE, sheet_name="Coherence_Licence")
    fiches_df = pd.read_excel(DATA_FILE, sheet_name="Fiches_Masters")

    all_masters = list(masters_df["Code"])

    dest_masters = {}
    for _, row in destinations.iterrows():
        dest_masters[row["Code"]] = [
            m.strip().replace(" ", "") for m in row["Masters inclus"].split(",")
        ]

    dest_labels = {
        row["Code"]: row["Intitulé (choix à Q2)"] for _, row in destinations.iterrows()
    }

    taux_acces = {
        row["Code"]: float(str(row["Taux d'accès"]).replace("%", ""))
        for _, row in masters_df.iterrows()
    }

    nom_complet = {row["Code"]: row["Nom complet"] for _, row in masters_df.iterrows()}

    coherence = {}
    for _, row in coherence_df.iterrows():
        coherence.setdefault(row["Licence (Q1)"], {})[row["Master"]] = row["Cohérence (1=faible, 4=idéal)"]

    debouches = {
        row["Code"]: row["Débouchés / métiers"] for _, row in fiches_df.iterrows()
    }

    liens_officiels = {
        row["Code"]: row["Lien officiel"] for _, row in fiches_df.iterrows()
    }

    def norm_opt(x):
        return str(x).split(" [")[0].split(" (double effet")[0].strip()

    bareme_df = bareme_df.copy()
    bareme_df["OptNorm"] = bareme_df["Option de réponse"].apply(norm_opt)

    bareme = {}
    for _, row in bareme_df.iterrows():
        cle = (row["Destination"], row["ID Question"])
        if cle not in bareme:
            bareme[cle] = {}
        opt = row["OptNorm"]
        if opt not in bareme[cle]:
            bareme[cle][opt] = {}
        bareme[cle][opt][row["Master concerné"]] = row["Points"]

    dest_questions = {}
    for _, row in questions.iterrows():
        if row["Destination"] != "UNIVERSELLE":
            dest_questions.setdefault(row["Destination"], []).append(row["ID Question"])
    for d in dest_questions:
        dest_questions[d] = sorted(set(dest_questions[d]), key=lambda x: int(x[1:]))

    q_text = {
        (row["Destination"], row["ID Question"]): row["Texte de la question"]
        for _, row in questions.iterrows()
    }

    licences = sorted(coherence.keys())

    return {
        "all_masters": all_masters,
        "dest_masters": dest_masters,
        "dest_labels": dest_labels,
        "taux_acces": taux_acces,
        "nom_complet": nom_complet,
        "coherence": coherence,
        "debouches": debouches,
        "liens_officiels": liens_officiels,
        "bareme": bareme,
        "dest_questions": dest_questions,
        "q_text": q_text,
        "licences": licences,
    }


DATA = charger_donnees()


# ==================================================================
# CALCUL DU SCORE
# ==================================================================
def calculer_top3(destination, reponses, f1, f2, licence, niveau):
    """niveau: 'L1L2' ou 'L3'. Pour un L1/L2, 'Jamais suivi' est neutre (0
    point) plutot que le leger malus applique a un L3."""
    scores = {m: BASE_SCORE for m in DATA["all_masters"]}
    touched = {m: False for m in DATA["all_masters"]}
    for m in DATA["dest_masters"][destination]:
        scores[m] += 3
        touched[m] = True

    for qid, option_choisie in reponses.items():
        mp = DATA["bareme"][(destination, qid)].get(option_choisie, {})
        neutraliser = niveau == "L1L2" and option_choisie == "Jamais suivi"
        for m, pts in mp.items():
            touched[m] = True
            if not neutraliser:
                scores[m] += pts

    for m in DATA["all_masters"]:
        if not touched[m]:
            scores[m] = -50

    for qid, ans in [("F1", f1), ("F2", f2)]:
        mp = DATA["bareme"][("UNIVERSELLE", qid)].get(ans, {})
        for m, pts in mp.items():
            scores[m] += pts

    coh = DATA["coherence"].get(licence, {})
    classement = sorted(
        scores.items(),
        key=lambda x: (-x[1], -coh.get(x[0], 0), -DATA["taux_acces"].get(x[0], 0)),
    )
    return [m for m, _ in classement[:3]], scores


def calculer_classement_jns(jns_reponses):
    """Retourne les 6 familles triees de la plus proche a la moins proche."""
    scores = {f: 0 for f in DESTINATION_ORDER}
    for qid, texte, familles in JNS_QUESTIONS:
        r = jns_reponses.get(qid, 3)
        pts = r - 3
        for f in familles:
            scores[f] += pts
    return sorted(scores.items(), key=lambda x: -x[1])


# ==================================================================
# SAUVEGARDE DES RESULTATS (pour le pre-test)
# Deux fichiers relies par un identifiant de session unique :
# - resultats_test.csv : une ligne par etudiant, avec le resultat final
# - reponses_detail.csv : une ligne par QUESTION repondue par chaque
#   etudiant (texte de la question + reponse donnee), pour permettre une
#   analyse fine dans le rapport (quelles reponses menent a quel resultat).
# Attention : sur un hebergement gratuit type Streamlit Community Cloud,
# ces fichiers ne sont PAS garantis permanents -- ils peuvent etre effaces
# si l'application redemarre ou est redeployee. Pour un pre-test limite
# dans le temps, cela reste suffisant ; a remplacer par une vraie base de
# donnees externe si l'outil doit etre utilise plus largement.
# ==================================================================
import uuid

RESULTATS_FILE = "resultats_test.csv"
REPONSES_DETAIL_FILE = "reponses_detail.csv"

def sauvegarder_resultat(top3, dest, niveau, origine, licence, jns_utilise, reponses, f1, f2, jns_reponses=None):
    session_id = str(uuid.uuid4())[:8]
    horodatage = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1) resume : une ligne par etudiant
    ligne_resume = pd.DataFrame([{
        "session_id": session_id,
        "horodatage": horodatage,
        "origine": origine,
        "niveau": niveau,
        "licence": licence if licence else "Autre université",
        "domaine": dest,
        "via_je_ne_sais_pas": jns_utilise,
        "master_1": top3[0],
        "master_2": top3[1],
        "master_3": top3[2],
    }])
    try:
        existant = pd.read_csv(RESULTATS_FILE)
        combine = pd.concat([existant, ligne_resume], ignore_index=True)
    except FileNotFoundError:
        combine = ligne_resume
    combine.to_csv(RESULTATS_FILE, index=False)

    # 2) detail : une ligne par question repondue (bloc de destination + F1/F2 + Je ne sais pas eventuellement)
    lignes_detail = []
    for qid, valeur in reponses.items():
        lignes_detail.append({
            "session_id": session_id, "horodatage": horodatage, "bloc": dest,
            "question_id": qid, "question_texte": DATA["q_text"].get((dest, qid), ""),
            "reponse": valeur,
        })
    lignes_detail.append({
        "session_id": session_id, "horodatage": horodatage, "bloc": "UNIVERSELLE",
        "question_id": "F1", "question_texte": "Un taux d'insertion professionnelle rapide et élevé après le master est-il important pour vous ?",
        "reponse": f1,
    })
    lignes_detail.append({
        "session_id": session_id, "horodatage": horodatage, "bloc": "UNIVERSELLE",
        "question_id": "F2", "question_texte": "Le niveau de salaire à la sortie du master est-il important pour vous ?",
        "reponse": f2,
    })
    if jns_reponses:
        textes_jns = {qid: texte for qid, texte, _ in JNS_QUESTIONS}
        for qid, valeur in jns_reponses.items():
            lignes_detail.append({
                "session_id": session_id, "horodatage": horodatage, "bloc": "JE_NE_SAIS_PAS",
                "question_id": qid, "question_texte": textes_jns.get(qid, ""),
                "reponse": valeur,
            })

    df_detail = pd.DataFrame(lignes_detail)
    try:
        existant2 = pd.read_csv(REPONSES_DETAIL_FILE)
        combine2 = pd.concat([existant2, df_detail], ignore_index=True)
    except FileNotFoundError:
        combine2 = df_detail
    combine2.to_csv(REPONSES_DETAIL_FILE, index=False)


# ==================================================================
# STYLE
# ==================================================================
st.set_page_config(page_title="Trouve ton Master", page_icon="🧭", layout="centered")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Public+Sans:wght@400;500;600;700&display=swap');

:root {
    --ink: #212B42;
    --ink-soft: #5B6478;
    --paper: #FBF7EF;
    --paper-card: #FFFFFF;
    --pine: #2E6F5E;
    --pine-dark: #1F4E42;
    --gold: #A97B34;
    --stone: #E4DECD;
}

html, body, [class*="css"] {
    font-family: 'Public Sans', sans-serif;
    color: var(--ink);
}

.stApp {
    background: var(--paper);
}

h1, h2 {
    font-family: 'Fraunces', serif !important;
    color: var(--ink) !important;
    letter-spacing: -0.01em;
}

.question-text {
    font-family: 'Public Sans', sans-serif;
    font-size: 1.28rem;
    font-weight: 600;
    line-height: 1.45;
    color: var(--ink);
    margin: 4px 0 18px 0;
}

.app-hero {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 4px;
}
.app-hero .compass {
    flex-shrink: 0;
}
.app-hero h1 {
    font-size: 2.1rem !important;
    margin: 0 !important;
    font-weight: 600 !important;
}
.app-subcaption {
    color: var(--ink-soft);
    font-size: 0.95rem;
    margin-bottom: 1.6rem;
    letter-spacing: 0.02em;
}

.q-eyebrow {
    font-family: 'Public Sans', sans-serif;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-size: 0.72rem;
    color: var(--pine);
    font-weight: 600;
    margin-bottom: 2px;
}

.stButton > button {
    font-family: 'Public Sans', sans-serif;
    font-weight: 600;
    border-radius: 8px;
    border: 1.5px solid var(--pine);
    padding: 0.5rem 1.2rem;
    transition: all 0.15s ease;
}
.stButton > button[kind="primary"],
.stButton > button:not([kind]) {
    background: var(--pine);
    color: #fff;
    border-color: var(--pine);
}
.stButton > button:hover {
    background: var(--pine-dark);
    border-color: var(--pine-dark);
    color: #fff;
}

.stProgress > div > div > div > div {
    background: var(--pine) !important;
}
.stProgress > div > div > div {
    background: var(--stone) !important;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--paper-card);
    border-radius: 14px !important;
    border: 1px solid var(--stone) !important;
    box-shadow: 0 2px 10px rgba(33, 43, 66, 0.05);
}

.stRadio label, .stSelectSlider label {
    font-family: 'Public Sans', sans-serif;
}

hr {
    border-color: var(--stone) !important;
}

.jns-rank {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 14px 18px;
    background: var(--paper-card);
    border: 1px solid var(--stone);
    border-radius: 12px;
    margin-bottom: 10px;
}
.jns-rank-num {
    font-family: 'Fraunces', serif;
    font-size: 1.4rem;
    font-weight: 600;
    color: var(--gold);
    min-width: 28px;
}
.jns-rank-name {
    font-family: 'Fraunces', serif;
    font-size: 1.05rem;
    font-weight: 600;
    flex-grow: 1;
}

.result-top {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 10px;
}
.result-medal {
    font-size: 1.8rem;
    line-height: 1;
}
.result-name {
    font-family: 'Fraunces', serif;
    font-size: 1.35rem;
    font-weight: 600;
    color: var(--ink);
}
.result-debouches-label {
    font-family: 'Public Sans', sans-serif;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-size: 0.7rem;
    font-weight: 700;
    color: var(--gold);
    margin-top: 8px;
    margin-bottom: 4px;
}
.result-debouches-text {
    font-family: 'Public Sans', sans-serif;
    font-size: 0.98rem;
    line-height: 1.55;
    color: var(--ink-soft);
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

COMPASS_SVG = """
<svg class="compass" width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="20" cy="20" r="18" stroke="#2E6F5E" stroke-width="2"/>
  <path d="M20 9 L24 20 L20 31 L16 20 Z" fill="#A97B34"/>
  <circle cx="20" cy="20" r="2.5" fill="#212B42"/>
</svg>
"""

st.markdown(
    f'<div class="app-hero">{COMPASS_SVG}<h1>Trouve ton Master</h1></div>'
    '<div class="app-subcaption">Faculté des Sciences Économiques, Université de Rennes</div>',
    unsafe_allow_html=True,
)


def eyebrow(texte):
    st.markdown(f'<div class="q-eyebrow">{texte}</div>', unsafe_allow_html=True)


def question_title(texte):
    st.markdown(f'<div class="question-text">{texte}</div>', unsafe_allow_html=True)


# ==================================================================
# PANNEAU ADMIN (consultation des resultats sauvegardes)
# Accessible en ajoutant ?admin=1 a la fin du lien de l'application.
# Reserve a l'auteur du projet pour consulter et telecharger les
# resultats du pre-test -- pas destine aux etudiants.
# ==================================================================
if st.query_params.get("admin") == "1":
    st.title("📊 Résultats du pré-test (accès admin)")

    st.header("Résumé par étudiant")
    try:
        df_resultats = pd.read_csv(RESULTATS_FILE)
        st.write(f"{len(df_resultats)} passage(s) enregistré(s).")
        st.dataframe(df_resultats, use_container_width=True)
        st.download_button(
            "⬇️ Télécharger le résumé en CSV",
            df_resultats.to_csv(index=False).encode("utf-8"),
            file_name="resultats_test.csv",
            mime="text/csv",
        )
    except FileNotFoundError:
        st.info("Aucun résultat enregistré pour l'instant.")

    st.header("Détail de chaque réponse individuelle")
    try:
        df_detail = pd.read_csv(REPONSES_DETAIL_FILE)
        st.write(f"{len(df_detail)} réponse(s) individuelle(s) enregistrée(s).")
        st.dataframe(df_detail, use_container_width=True)
        st.download_button(
            "⬇️ Télécharger le détail en CSV",
            df_detail.to_csv(index=False).encode("utf-8"),
            file_name="reponses_detail.csv",
            mime="text/csv",
        )
    except FileNotFoundError:
        st.info("Aucune réponse détaillée enregistrée pour l'instant.")

    st.stop()


# ==================================================================
# ETAT INITIAL
# ==================================================================
if "etape" not in st.session_state:
    st.session_state.etape = "bienvenue"
    st.session_state.reponses = {}


# ---------------- ETAPE : ecran de bienvenue ----------------
if st.session_state.etape == "bienvenue":
    st.markdown("## Bienvenue !")
    st.write(
        "Cet outil vous aide à identifier les masters les plus adaptés à votre "
        "profil parmi les 12 proposés par la Faculté. Il vous prendra environ "
        "5 minutes. Vos réponses restent anonymes. Répondez sincèrement, il "
        "n'y a pas de bonne ou de mauvaise réponse, seulement des réponses "
        "qui vous ressemblent."
    )
    if st.button("Commencer ➡️"):
        st.session_state.etape = "q0"
        st.rerun()

# ---------------- ETAPE Q0 : universite d'origine ----------------
elif st.session_state.etape == "q0":
    st.progress(1 / 4)
    eyebrow("Question 1 sur 3 · avant de commencer")
    question_title("Êtes-vous étudiant(e) à l'Université de Rennes, ou dans une autre université ?")
    choix = st.radio(
        "Votre réponse :",
        options=["rennes", "autre"],
        format_func=lambda k: "Université de Rennes" if k == "rennes" else "Une autre université",
        index=None,
    )
    if st.button("Suivant ➡️", disabled=choix is None):
        st.session_state.origine = choix
        st.session_state.etape = "q1_niveau"
        st.rerun()

# ---------------- ETAPE Q1 : niveau d'etudes ----------------
elif st.session_state.etape == "q1_niveau":
    st.progress(2 / 4)
    eyebrow("Question 2 sur 3 · avant de commencer")
    question_title("En quelle année êtes-vous actuellement ?")
    choix = st.radio(
        "Votre réponse :",
        options=["L1L2", "L3"],
        format_func=lambda k: "L1 ou L2" if k == "L1L2" else "L3",
        index=None,
    )
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅️ Précédent"):
            st.session_state.etape = "q0"
            st.rerun()
    with col2:
        if st.button("Suivant ➡️", disabled=choix is None):
            st.session_state.niveau = choix
            if st.session_state.origine == "rennes":
                st.session_state.etape = "q1_licence"
            else:
                st.session_state.licence = None
                st.session_state.etape = "q2"
            st.rerun()

# ---------------- ETAPE Q1bis : licence precise (Rennes uniquement) ----------------
elif st.session_state.etape == "q1_licence":
    st.progress(3 / 4)
    eyebrow("Question 3 sur 3 · avant de commencer")
    question_title("Pouvez-vous indiquer la licence que vous suivez actuellement ?")
    choix = st.radio(
        "Sélectionnez votre licence :",
        options=list(LICENCE_LABELS.keys()),
        format_func=lambda k: LICENCE_LABELS[k],
        index=None,
    )
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅️ Précédent"):
            st.session_state.etape = "q1_niveau"
            st.rerun()
    with col2:
        if st.button("Suivant ➡️", disabled=choix is None):
            st.session_state.licence = choix
            st.session_state.etape = "q2"
            st.rerun()

# ---------------- ETAPE Q2 : destination ----------------
elif st.session_state.etape == "q2":
    st.progress(4 / 4)
    eyebrow("Votre domaine")
    question_title("Quel domaine correspond le mieux à votre projet professionnel ?")
    options = DESTINATION_ORDER + [JE_NE_SAIS_PAS]
    choix = st.radio(
        "Sélectionnez un domaine :",
        options=options,
        format_func=lambda k: "Je ne sais pas, aidez-moi à choisir" if k == JE_NE_SAIS_PAS else DATA["dest_labels"][k],
        index=None,
    )
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅️ Précédent"):
            if st.session_state.origine == "rennes":
                st.session_state.etape = "q1_licence"
            else:
                st.session_state.etape = "q1_niveau"
            st.rerun()
    with col2:
        if st.button("Suivant ➡️", disabled=choix is None):
            if choix == JE_NE_SAIS_PAS:
                st.session_state.jns_index = 0
                st.session_state.jns_reponses = {}
                st.session_state.etape = "jns_bloc"
            else:
                st.session_state.destination = choix
                st.session_state.q_index = 0
                st.session_state.via_jns = False
                st.session_state.etape = "bloc"
            st.rerun()

# ---------------- ETAPE module "Je ne sais pas" : 8 questions ----------------
elif st.session_state.etape == "jns_bloc":
    idx = st.session_state.jns_index
    qid, texte, familles = JNS_QUESTIONS[idx]

    st.progress(idx / len(JNS_QUESTIONS))
    eyebrow(f"Question {idx + 1} sur {len(JNS_QUESTIONS)} · pour vous aider à choisir")
    question_title(texte)

    st.caption("Notez de 1 (pas du tout d'accord) à 5 (tout à fait d'accord).")
    valeur = st.select_slider(
        "Votre réponse :",
        options=["1", "2", "3", "4", "5"],
        value="3",
        format_func=lambda v: {
            "1": "1, pas du tout",
            "2": "2",
            "3": "3, neutre",
            "4": "4",
            "5": "5, tout à fait",
        }[v],
        key=f"jns_slider_{qid}",
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅️ Précédent"):
            if idx == 0:
                st.session_state.etape = "q2"
            else:
                st.session_state.jns_index -= 1
            st.rerun()
    with col2:
        if st.button("Suivant ➡️"):
            st.session_state.jns_reponses[qid] = int(valeur)
            if idx + 1 < len(JNS_QUESTIONS):
                st.session_state.jns_index += 1
            else:
                st.session_state.etape = "jns_classement"
            st.rerun()

# ---------------- ETAPE classement des 6 familles ----------------
elif st.session_state.etape == "jns_classement":
    question_title("D'après vos réponses, voici les domaines qui vous correspondent, du plus proche au moins proche :")
    st.caption(
        "Ce classement reflète uniquement vos envies. Choisissez un domaine pour répondre ensuite à quelques "
        "questions sur vos résultats et vos compétences : c'est en croisant les deux (ce que vous voulez, et "
        "ce que vous pouvez) que l'outil pourra vous suggérer les masters les plus adaptés à l'intérieur de ce domaine."
    )
    classement = calculer_classement_jns(st.session_state.jns_reponses)

    for rang, (famille, _score) in enumerate(classement, start=1):
        col_txt, col_btn = st.columns([3, 1.3])
        with col_txt:
            st.markdown(
                f'<div class="jns-rank"><span class="jns-rank-num">{rang}</span>'
                f'<span class="jns-rank-name">{DATA["dest_labels"][famille]}</span></div>',
                unsafe_allow_html=True,
            )
        with col_btn:
            if st.button("Approfondir ➡️", key=f"choix_{famille}"):
                st.session_state.destination = famille
                st.session_state.q_index = 0
                st.session_state.via_jns = True
                st.session_state.reponses = {}
                st.session_state.etape = "bloc"
                st.rerun()

    st.divider()
    if st.button("⬅️ Refaire les 8 questions"):
        st.session_state.jns_index = 0
        st.session_state.jns_reponses = {}
        st.session_state.etape = "jns_bloc"
        st.rerun()

# ---------------- ETAPE bloc de destination ----------------
elif st.session_state.etape == "bloc":
    dest = st.session_state.destination
    qids = DATA["dest_questions"][dest]
    idx = st.session_state.q_index
    qid = qids[idx]
    texte = DATA["q_text"][(dest, qid)]
    options = list(DATA["bareme"][(dest, qid)].keys())

    if idx == 0 and st.session_state.get("via_jns"):
        st.info(
            f"Les questions précédentes ont identifié « {DATA['dest_labels'][dest]} » comme le domaine qui "
            f"correspond le plus à vos envies. Il reste maintenant à identifier, à l'intérieur de ce domaine, "
            f"lequel de ses masters correspond le mieux à vos compétences réelles (résultats, expérience). "
            f"Voici quelques questions à ce sujet."
        )

    st.progress(idx / len(qids))
    eyebrow(f"{DATA['dest_labels'][dest]} · question {idx + 1} sur {len(qids)}")
    question_title(texte)

    est_curseur = set(options) == {"1", "2", "3", "4", "5"}
    if est_curseur:
        st.caption("Évaluez sur une échelle de 1 à 5 : 1 = pas du tout intéressé(e), 5 = très intéressé(e).")
        valeur = st.select_slider(
            "Votre réponse :",
            options=["1", "2", "3", "4", "5"],
            value="3",
            format_func=lambda v: {
                "1": "1, pas du tout intéressé(e)",
                "2": "2",
                "3": "3",
                "4": "4",
                "5": "5, très intéressé(e)",
            }[v],
            key=f"slider_{dest}_{qid}",
        )
        choix = valeur
    else:
        choix = st.radio("Votre réponse :", options=options, index=None, key=f"radio_{dest}_{qid}")

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅️ Précédent"):
            if idx == 0:
                st.session_state.etape = "jns_classement" if st.session_state.get("via_jns") else "q2"
            else:
                st.session_state.q_index -= 1
            st.rerun()
    with col2:
        if st.button("Suivant ➡️", disabled=choix is None):
            st.session_state.reponses[qid] = choix
            if idx + 1 < len(qids):
                st.session_state.q_index += 1
            else:
                st.session_state.etape = "f1"
            st.rerun()

# ---------------- ETAPE F1 ----------------
elif st.session_state.etape == "f1":
    st.progress(0.93)
    eyebrow("Pour finir")
    question_title("Un taux d'insertion professionnelle rapide et élevé après le master est-il important pour vous ?")
    choix = st.radio(
        "Votre réponse :",
        options=["Très important", "Peu importe", "Pas prioritaire"],
        index=None,
    )
    if st.button("Suivant ➡️", disabled=choix is None):
        st.session_state.f1 = choix
        st.session_state.etape = "f2"
        st.rerun()

# ---------------- ETAPE F2 ----------------
elif st.session_state.etape == "f2":
    st.progress(0.97)
    eyebrow("Pour finir")
    question_title("Le niveau de salaire à la sortie du master est-il important pour vous ?")
    choix = st.radio(
        "Votre réponse :",
        options=["Très important", "Peu importe", "Pas prioritaire"],
        index=None,
    )
    if st.button("Voir mon résultat 🎉", disabled=choix is None):
        st.session_state.f2 = choix
        st.session_state.etape = "resultat"
        st.rerun()

# ---------------- ETAPE resultat ----------------
elif st.session_state.etape == "resultat":
    top3, _scores_internes = calculer_top3(
        st.session_state.destination,
        st.session_state.reponses,
        st.session_state.f1,
        st.session_state.f2,
        st.session_state.licence,
        st.session_state.niveau,
    )

    if not st.session_state.get("deja_sauvegarde"):
        sauvegarder_resultat(
            top3,
            st.session_state.destination,
            st.session_state.niveau,
            st.session_state.origine,
            st.session_state.licence,
            st.session_state.get("via_jns", False),
            st.session_state.reponses,
            st.session_state.f1,
            st.session_state.f2,
            st.session_state.get("jns_reponses"),
        )
        st.session_state.deja_sauvegarde = True

    st.markdown(
        '<div class="q-eyebrow">Votre résultat</div>',
        unsafe_allow_html=True,
    )
    st.markdown("## Voici les 3 masters qui correspondent le mieux à votre profil")

    medailles = ["🥇", "🥈", "🥉"]
    for medaille, code in zip(medailles, top3):
        lien = DATA["liens_officiels"].get(code)
        with st.container(border=True):
            st.markdown(
                f'<div class="result-top"><span class="result-medal">{medaille}</span>'
                f'<span class="result-name">{DATA["nom_complet"].get(code, code)}</span></div>'
                f'<div class="result-debouches-label">Débouchés</div>'
                f'<div class="result-debouches-text">{DATA["debouches"].get(code, "Non renseigné")}</div>',
                unsafe_allow_html=True,
            )
            if isinstance(lien, str) and lien.startswith("http"):
                st.link_button("Voir la fiche officielle du master ↗️", lien)
    st.divider()

    # ---------- Modifier n'importe laquelle des reponses deja donnees, toutes en meme temps ----------
    with st.expander("✏️ Modifier mes réponses"):
        st.caption("Toutes vos réponses sont affichées ci-dessous, déjà pré-remplies. Changez ce que vous voulez, puis validez en bas pour recalculer.")
        dest = st.session_state.destination
        qids = DATA["dest_questions"][dest]
        nouvelles_reponses = {}

        for qid in qids:
            texte = DATA["q_text"][(dest, qid)]
            options_q = list(DATA["bareme"][(dest, qid)].keys())
            est_curseur = set(options_q) == {"1", "2", "3", "4", "5"}
            valeur_actuelle = st.session_state.reponses.get(qid)
            st.markdown(f"**{qid} — {texte}**")
            if est_curseur:
                nouvelles_reponses[qid] = st.select_slider(
                    "Réponse :",
                    options=["1", "2", "3", "4", "5"],
                    value=valeur_actuelle if valeur_actuelle in options_q else "3",
                    key=f"modif_{dest}_{qid}",
                    label_visibility="collapsed",
                )
            else:
                idx_actuel = options_q.index(valeur_actuelle) if valeur_actuelle in options_q else 0
                nouvelles_reponses[qid] = st.radio(
                    "Réponse :",
                    options=options_q,
                    index=idx_actuel,
                    key=f"modif_{dest}_{qid}",
                    label_visibility="collapsed",
                )
            st.markdown("---")

        st.markdown("**Un taux d'insertion professionnelle rapide et élevé après le master est-il important pour vous ?**")
        nouvelle_f1 = st.radio(
            "Réponse :",
            options=["Très important", "Peu importe", "Pas prioritaire"],
            index=["Très important", "Peu importe", "Pas prioritaire"].index(st.session_state.f1),
            key="modif_f1",
            label_visibility="collapsed",
        )
        st.markdown("---")

        st.markdown("**Le niveau de salaire à la sortie du master est-il important pour vous ?**")
        nouvelle_f2 = st.radio(
            "Réponse :",
            options=["Très important", "Peu importe", "Pas prioritaire"],
            index=["Très important", "Peu importe", "Pas prioritaire"].index(st.session_state.f2),
            key="modif_f2",
            label_visibility="collapsed",
        )

        if st.button("Enregistrer toutes les modifications et recalculer ✅"):
            for qid, valeur in nouvelles_reponses.items():
                st.session_state.reponses[qid] = valeur
            st.session_state.f1 = nouvelle_f1
            st.session_state.f2 = nouvelle_f2
            st.session_state.deja_sauvegarde = False
            st.rerun()

    if st.button("🔄 Refaire le questionnaire depuis le début"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.etape = "bienvenue"
        st.session_state.reponses = {}
        st.rerun()

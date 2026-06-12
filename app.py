import streamlit as st
from datetime import date, timedelta
import random
import re
import json
import os

# ─── Chargement des process personnalisés (Administration) ───
CUSTOM_FILE = os.path.join(os.path.dirname(__file__), "custom_processes.json")

def load_custom():
    if os.path.exists(CUSTOM_FILE):
        try:
            with open(CUSTOM_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_custom(data):
    with open(CUSTOM_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ─── Stockage des résultats quiz ───
RESULTS_FILE = os.path.join(os.path.dirname(__file__), "quiz_results.json")

def load_results():
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"results": []}
    return {"results": []}

def save_result(entry):
    data = load_results()
    data["results"].append(entry)
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

_custom = load_custom()

st.set_page_config(page_title="Knowledge Support Wave V7", page_icon="🌊", layout="wide")

WAVE_BLUE = "#26BDE2"
DARK = "#102033"
ORANGE = "#FF8A00"
GREEN = "#00B86B"
RED = "#EF4444"
YELLOW = "#FFF4DA"
LIGHT = "#E9F9FD"

st.markdown(f"""
<style>
.stApp {{background: linear-gradient(120deg,#F4FBFE 0%,#FFFFFF 65%);}}
section[data-testid="stSidebar"] {{background: linear-gradient(180deg,#4CC3E6 0%,#11A9CF 100%); color:{DARK};}}
section[data-testid="stSidebar"] * {{color:{DARK} !important; font-weight:600;}}
.block-container {{padding-top:2.2rem; max-width:1180px;}}
.wave-card {{background:white; border:1px solid #CDEFF8; border-radius:24px; padding:28px 30px; box-shadow:0 14px 35px rgba(38,189,226,.10); margin:18px 0;}}
.process-card {{background:#E9F9FD; border-left:7px solid #0BB4D8; border-radius:22px; padding:24px 28px; margin:18px 0; box-shadow:0 12px 28px rgba(38,189,226,.12); color:#102033 !important;}}
.process-card * {{color:#102033 !important;}}
.question-card {{background:#E9F9FD; border-left:7px solid #0A9FC3; border-radius:20px; padding:22px 26px; margin:16px 0; color:#102033 !important;}}
.question-card * {{color:#102033 !important;}}
.decision-ok {{background:#E8F8EF; border-left:7px solid {GREEN}; border-radius:20px; padding:22px 26px; margin:18px 0; color:#102033 !important;}}
.decision-ok * {{color:#102033 !important;}}
.decision-stop {{background:#FFF2F2; border-left:7px solid {RED}; border-radius:20px; padding:22px 26px; margin:18px 0; color:#102033 !important;}}
.decision-stop * {{color:#102033 !important;}}
.decision-warn {{background:#FFF7E6; border-left:7px solid {ORANGE}; border-radius:20px; padding:22px 26px; margin:18px 0; color:#102033 !important;}}
.decision-warn * {{color:#102033 !important;}}
.badge {{display:inline-block; padding:7px 12px; border-radius:999px; margin-right:8px; background:#D7F6FD; font-weight:800; color:#075F78;}}
.badge-orange {{background:#FFE8C7; color:#9A4E00;}}
.small-muted {{color:#667085; font-size:.95rem;}}
.big-title {{font-size:2.7rem; font-weight:900; color:{DARK}; line-height:1.05;}}
div[data-testid="stRadio"] label p {{color:#102033 !important;}}
div[data-testid="stRadio"] label {{color:#102033 !important;}}
div[data-testid="stRadio"] * {{color:#102033 !important;}}
div[data-testid="stSelectbox"] * {{color:#102033 !important;}}
div[data-testid="stMarkdownContainer"] p {{color:#102033 !important;}}
div[data-testid="stMarkdownContainer"] h1, div[data-testid="stMarkdownContainer"] h2, div[data-testid="stMarkdownContainer"] h3 {{color:#102033 !important;}}
.stRadio > div {{color:#102033 !important;}}
p, h1, h2, h3, h4, label {{color:#102033 !important;}}
hr {{border:none; border-top:1px solid #D8EDF4; margin:26px 0;}}
</style>
""", unsafe_allow_html=True)

# ------------------------------ Process rule base ------------------------------
# This V7 uses explicit executable rules for high-risk branches and structured FO/BO gating.
# No raw-process dumping in assistant mode.

QUALIFY_OPTIONS = {
    "deblocage_compte": "Déblocage de compte",
    "recover_pin": "Recover PIN / mot de passe oublié",
    "reset_pin": "Reset PIN",
    "device_restriction": "Device restriction / nouvel appareil",
    "canal": "Réclamation Canal+",
    "cie_sodeci": "CIE / SODECI postpayé",
    "cie_prepayee": "CIE prépayée",
    "startimes": "Startimes",
    "fer": "FER",
    "cnps": "CNPS",
    "cit": "Côte d’Ivoire Terminal",
    "b2w": "Bank to Wallet",
    "merchant_issue": "Merchant issue / paiement marchand",
    "merchant_creation": "Création compte marchand / QR",
    "refund_b2p": "Refund B2P",
    "refund": "Refund user / plusieurs refunds",
    "move_balance": "Move balance coffre",
    "agent_error": "Erreur transaction agent",
    "agent_reject_id": "Rejet de pièce agent",
    "agent_link": "Lien application agent",
    "agent_prospect": "Devenir agent / master agent",
    "agent_assistant": "Ajouter / retirer assistant",
    "agent_commission": "Commission cut / non reçue",
    "agent_gaming": "Agent gaming",
    "agent_recover_pin": "Agent recover PIN",
    "agent_complaint": "Plainte client contre agent",
    "agent_scan_no_visibility": "Carte/app scannée sans visibilité transaction",
    "agent_box": "Box Wave",
    "agent_type": "Type agent principal / assistant",
    "agent_change_number": "Changer numéro agent principal",
    "agent_pdv": "Localiser PDV",
    "agent_rebalance_limit": "Limite de rééquilibrage agent",
    "agent_bank_rebalance": "Rééquilibrage par banque",
    "identification": "Identification client / double identité",
    "parental": "Autorisation parentale",
    # ── Carte Visa Wave ──
    "visa_fraude":        "Carte Visa — Fraude / Sécurité urgente",
    "visa_litige":        "Carte Visa — Litige transaction",
    "visa_remboursement": "Carte Visa — Remboursement",
    "visa_paiement":      "Carte Visa — Paiement refusé / restriction",
    "visa_carte":         "Carte Visa — Gestion carte",
    "visa_info":          "Carte Visa — Information / Tarification",
}

KEYWORDS = [
    # ── Agent processes ──
    ("agent_reject_id", ["agent", "rejeter", "piece"], 120),
    ("agent_reject_id", ["piece", "identite", "compte", "agent"], 115),
    ("agent_reject_id", ["agent", "piece", "changer"], 115),
    ("agent_error", ["agent", "erreur", "transaction"], 110),
    ("agent_error", ["agent", "transaction", "echoue"], 108),
    ("agent_error", ["agent", "depot", "retrait", "probleme"], 105),
    ("agent_link", ["lien", "application", "agent"], 105),
    ("agent_link", ["app", "agent", "probleme"], 100),
    ("agent_link", ["agent", "application", "marche"], 100),
    ("agent_prospect", ["devenir", "agent"], 105),
    ("agent_prospect", ["devenir", "master", "agent"], 110),
    ("agent_assistant", ["assistant", "agent", "ajouter"], 105),
    ("agent_assistant", ["assistant", "agent", "retirer"], 105),
    ("agent_commission", ["commission", "agent"], 105),
    ("agent_commission", ["agent", "commissions", "recu"], 105),
    ("agent_commission", ["agent", "commissions", "coupees"], 110),
    ("agent_gaming", ["gaming", "agent"], 105),
    ("agent_recover_pin", ["agent", "recover", "pin"], 105),
    ("agent_complaint", ["plainte", "agent"], 105),
    ("agent_complaint", ["client", "conteste", "agent"], 105),
    ("agent_complaint", ["client", "se", "plaint", "agent"], 105),
    ("agent_scan_no_visibility", ["scanne", "visible", "agent"], 105),
    ("agent_scan_no_visibility", ["scanne", "visibilite", "agent"], 105),
    ("agent_scan_no_visibility", ["agent", "transaction", "scannee"], 105),
    ("agent_scan_no_visibility", ["agent", "ne", "voit", "transaction"], 105),
    ("agent_box", ["box", "wave", "agent"], 105),
    ("agent_box", ["box", "wave"], 95),
    ("agent_type", ["agent", "principal", "assistant"], 100),
    ("agent_change_number", ["changer", "numero", "agent"], 105),
    ("agent_pdv", ["localiser", "pdv"], 100),
    ("agent_pdv", ["point", "retrait", "wave"], 100),
    ("agent_pdv", ["agence", "wave", "proche"], 95),
    ("agent_rebalance_limit", ["limite", "reequilibrage", "agent"], 105),
    ("agent_rebalance_limit", ["agent", "limite", "atteinte"], 105),
    ("agent_bank_rebalance", ["reequilibrage", "banque"], 105),
    ("agent_bank_rebalance", ["agent", "reequilibrer", "banque"], 105),
    ("agent_bank_rebalance", ["agent", "virement", "bancaire"], 105),
    # ── Facturiers / partenaires ──
    ("canal", ["canal"], 95),
    ("cie_sodeci", ["sodeci"], 90),
    ("cie_sodeci", ["cie", "postpaye"], 90),
    ("cie_sodeci", ["cie", "facture"], 90),
    ("cie_sodeci", ["facture", "cie"], 90),
    ("cie_prepayee", ["cie", "prepaye"], 90),
    ("cie_prepayee", ["cie", "code"], 90),
    ("cie_prepayee", ["code", "cie"], 90),
    ("startimes", ["startimes"], 90),
    ("fer", ["fer"], 85),
    ("cnps", ["cnps"], 85),
    ("cit", ["terminal"], 85),
    # ── Transactions ──
    ("b2w", ["b2w"], 90),
    ("b2w", ["bank", "wallet"], 90),
    ("b2w", ["virement", "banque", "wave"], 90),
    ("b2w", ["virement", "banque"], 85),
    ("b2w", ["wave", "banque", "arrive"], 85),
    ("b2w", ["wave", "to", "bank"], 90),
    ("merchant_creation", ["devenir", "marchand"], 95),
    ("merchant_creation", ["creation", "marchand"], 95),
    ("merchant_creation", ["marchand", "qr"], 95),
    ("merchant_creation", ["commercant", "qr"], 95),
    ("merchant_issue", ["merchant", "issue"], 95),
    ("merchant_issue", ["paiement", "marchand", "reclamation"], 95),
    ("merchant_issue", ["reclamation", "commerçant"], 90),
    ("merchant_issue", ["probleme", "paiement", "marchand"], 90),
    ("refund_b2p", ["refund", "b2p"], 100),
    ("refund", ["plusieurs", "refund"], 100),
    ("refund", ["remboursement"], 85),
    ("refund", ["plusieurs", "remboursement"], 100),
    ("refund", ["plusieurs", "remboursements"], 100),
    ("refund", ["refund"], 85),
    # ── Solde / coffre ──
    ("move_balance", ["move", "balance"], 100),
    ("move_balance", ["mouvement", "balance"], 100),
    ("move_balance", ["coffre", "compte", "principal"], 90),
    ("move_balance", ["recuperer", "argent", "coffre"], 95),
    # ── Compte / accès ──
    ("deblocage_compte", ["debloquer", "compte"], 90),
    ("deblocage_compte", ["deblocage", "compte"], 90),
    ("deblocage_compte", ["bloque", "telephone", "perdu"], 95),
    ("deblocage_compte", ["compte", "bloque", "fraude"], 95),
    ("recover_pin", ["recover", "pin"], 90),
    ("recover_pin", ["oublie", "pin"], 90),
    ("recover_pin", ["mot", "passe", "oublie"], 90),
    ("recover_pin", ["oublie", "mot", "passe"], 90),
    ("reset_pin", ["reset", "pin"], 90),
    ("reset_pin", ["changer", "pin"], 90),
    ("device_restriction", ["device", "restriction"], 95),
    ("device_restriction", ["nouveau", "telephone"], 80),
    # ── Identification / double identité ──
    ("identification", ["double", "ident"], 100),
    ("identification", ["double", "identite"], 100),
    ("identification", ["nom", "different"], 90),
    ("identification", ["deux", "noms"], 95),
    ("identification", ["meme", "piece"], 90),
    ("identification", ["piece", "tierce"], 95),
    ("identification", ["compte", "meme", "piece"], 95),
    ("identification", ["comptes", "identifie", "piece"], 95),
    ("identification", ["double", "id"], 100),
    # ── Parental — mots-clés stricts pour éviter faux positifs ──
    ("parental", ["mineur", "kyc"], 95),
    ("parental", ["mineur", "autorisation"], 95),
    ("parental", ["mineur", "compte"], 90),
    ("parental", ["enfant", "compte", "wave"], 90),
    ("parental", ["autorisation", "parentale"], 100),
    # ── Carte Visa Wave ──
    ("visa_fraude", ["visa", "fraude"], 122),
    ("visa_fraude", ["visa", "frauduleux"], 122),
    ("visa_fraude", ["visa", "inconnu", "debit"], 120),
    ("visa_fraude", ["visa", "inconnu", "paiement"], 120),
    ("visa_fraude", ["visa", "compromis"], 118),
    ("visa_fraude", ["visa", "cvv", "bloque"], 118),
    ("visa_fraude", ["visa", "utilisation", "inconnue"], 118),
    ("visa_fraude", ["visa", "quelqu"], 112),
    ("visa_fraude", ["visa", "acces", "carte"], 112),
    ("visa_litige", ["visa", "debite", "non", "valide"], 115),
    ("visa_litige", ["visa", "debite", "deux"], 115),
    ("visa_litige", ["visa", "double", "debit"], 115),
    ("visa_litige", ["visa", "double"], 108),
    ("visa_litige", ["visa", "echoue", "debite"], 115),
    ("visa_litige", ["visa", "paiement", "echoue", "debite"], 115),
    ("visa_litige", ["visa", "marchand", "recu"], 110),
    ("visa_litige", ["visa", "litige"], 112),
    ("visa_litige", ["visa", "debit", "valide"], 112),
    ("visa_remboursement", ["visa", "remboursement"], 112),
    ("visa_remboursement", ["visa", "rembourse"], 112),
    ("visa_remboursement", ["visa", "annulation", "paiement"], 110),
    ("visa_remboursement", ["carte", "visa", "remboursement"], 112),
    ("visa_remboursement", ["visa", "delai", "remboursement"], 108),
    ("visa_remboursement", ["visa", "article", "recu"], 108),
    ("visa_remboursement", ["visa", "commande", "annulee"], 108),
    ("visa_paiement", ["visa", "refuse"], 108),
    ("visa_paiement", ["visa", "refusee"], 108),
    ("visa_paiement", ["visa", "paiement", "refuse"], 110),
    ("visa_paiement", ["visa", "international"], 102),
    ("visa_paiement", ["visa", "abonnement"], 102),
    ("visa_paiement", ["visa", "netflix"], 100),
    ("visa_paiement", ["visa", "spotify"], 100),
    ("visa_paiement", ["visa", "site", "refuse"], 108),
    ("visa_paiement", ["visa", "certains", "sites"], 102),
    ("visa_paiement", ["visa", "systematiquement", "refuse"], 108),
    ("visa_carte", ["visa", "bloque"], 100),
    ("visa_carte", ["visa", "bloquee"], 100),
    ("visa_carte", ["visa", "debloquer"], 105),
    ("visa_carte", ["visa", "telephone", "perdu"], 108),
    ("visa_carte", ["visa", "changer", "telephone"], 102),
    ("visa_carte", ["visa", "nouveau", "telephone"], 102),
    ("visa_carte", ["visa", "transferer", "fonds"], 108),
    ("visa_carte", ["visa", "recuperer", "argent"], 108),
    ("visa_carte", ["visa", "fonds", "carte"], 102),
    ("visa_info", ["visa", "tarif"], 95),
    ("visa_info", ["visa", "frais"], 95),
    ("visa_info", ["visa", "activer"], 93),
    ("visa_info", ["visa", "activation"], 93),
    ("visa_info", ["visa", "cvv"], 90),
    ("visa_info", ["visa", "kyc"], 93),
    ("visa_info", ["virtual", "card"], 90),
    ("visa_info", ["carte", "visa", "wave"], 85),
    ("visa_info", ["visa", "verrouiller"], 90),
    ("visa_info", ["visa", "prepayee"], 93),
    ("visa_info", ["visa", "option"], 88),
    ("visa_info", ["visa", "voir", "pas"], 88),
]

# ─── Fusion des process personnalisés (exécutée après SIMPLE_DECISIONS) ───
def _fuse_custom():
    for _pid, _pnom in _custom.get("qualify_options", {}).items():
        QUALIFY_OPTIONS[_pid] = _pnom
    for _kw in _custom.get("keywords", []):
        if len(_kw) == 3:
            KEYWORDS.append(tuple(_kw))
    for _pid, _dec in _custom.get("simple_decisions", {}).items():
        if isinstance(_dec, list) and len(_dec) == 2:
            SIMPLE_DECISIONS[_pid] = tuple(_dec)
    for _pid, _role in _custom.get("roles", {}).items():
        ROLE[_pid] = _role

def norm(s: str) -> str:
    repl = {"é":"e","è":"e","ê":"e","à":"a","ù":"u","ç":"c","ô":"o","î":"i","ï":"i","É":"e","À":"a"}
    for k,v in repl.items(): s=s.replace(k,v)
    return s.lower()

def _wm(w, t):
    """Word-boundary match : évite les faux positifs de sous-chaîne (ex : 'fer' dans 'transférer')."""
    return bool(re.search(r'(?<!\w)' + re.escape(w) + r'(?!\w)', t))

def classify(text):
    t = norm(text)
    scores = {}
    for intent, words, weight in KEYWORDS:
        if all(_wm(w, t) for w in words):
            scores[intent] = scores.get(intent, 0) + weight
    # Obstacle detection independent of main objective
    obstacles = []
    if any(x in t for x in ["double ident", "double id", "deux noms", "noms superposes", "nom du bas", "piece d'un", "piece de quelqu"]):
        obstacles.append("double_identite")
    if "fraude" in t or "fraud" in t:
        obstacles.append("blocage_fraude")
    if "mineur" in t or "17 ans" in t or "16 ans" in t:
        obstacles.append("mineur")
    if "agent" in t and ("piece" in t or "id" in t) and ("rej" in t or "reject" in t):
        scores["agent_reject_id"] = scores.get("agent_reject_id", 0) + 150
    if not scores:
        return "qualification", obstacles, []
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    # If double identity present with an operational objective, keep objective first, double identity as obstacle.
    return ranked[0][0], obstacles, ranked[:5]

def allowed_for_profile(rule_role, profile):
    if profile == "Manager": return True
    if rule_role == "FO_BO": return True
    if rule_role == "FO" and profile == "Front Office": return True
    if rule_role == "BO_ONLY" and profile == "Back Office": return True
    return False

# ------------------------------ Assistant engine ------------------------------

def reset_case():
    for k in ["intent","obstacles","ranked","step","answers","analysis_text"]:
        st.session_state.pop(k, None)

def start_case(text):
    intent, obstacles, ranked = classify(text)
    st.session_state.intent = intent
    st.session_state.obstacles = obstacles
    st.session_state.ranked = ranked
    st.session_state.step = 0
    st.session_state.answers = {}
    st.session_state.analysis_text = text

# Declarative questions; decision functions decide when to stop.

def q(key, title, why, options):
    return {"key": key, "title": title, "why": why, "options": options}

QUESTIONS = {
    "qualification": [q("precision", "Quelle est la demande exacte du client ?", "L’application ne doit pas inventer d’action. Il faut préciser le type de compte, l’opération demandée, le statut visible Front et le blocage éventuel.", list(QUALIFY_OPTIONS.values()))],
    "deblocage_compte": [
        q("reason", "Quel est le motif visible du blocage du compte ?", "Le traitement dépend du motif : téléphone perdu/volé, Fraude, device restriction ou autre.", ["Téléphone perdu/volé", "Fraude", "Device restriction", "Autre / je ne sais pas"]),
        q("number", "Le client appelle-t-il avec le numéro concerné ?", "Pour le déblocage Lost Phone et plusieurs traitements de sécurité, l’appel avec le numéro concerné est obligatoire.", ["Oui", "Non", "Je ne sais pas"]),
        q("same_day", "Le compte a-t-il été bloqué aujourd’hui ?", "Le jour même du blocage, les règles sont plus strictes. À partir du lendemain, on vérifie surtout les exceptions.", ["Oui", "Non, avant aujourd’hui", "Je ne sais pas"]),
        q("today_conditions", "Si blocage aujourd’hui : est-ce un jour ouvré lundi-vendredi, au moins 2h après le blocage et avant 16h GMT ?", "C’est la seule condition permettant le déblocage le jour même.", ["Oui, toutes les conditions sont réunies", "Non, une condition manque", "Non applicable"]),
        q("sat_sunday", "Si blocage avant aujourd’hui : le compte a-t-il été bloqué samedi après 13h et le client rappelle-t-il dimanche ?", "Ce cas spécial est interdit : le client doit rappeler lundi.", ["Oui", "Non", "Je ne sais pas"]),
        q("ab", "L’AB Verification est-elle réussie ?", "Après éligibilité, toutes les questions AB doivent être validées. Pour le PDV habituel, demander un lieu précis, pas seulement la ville/commune.", ["Oui", "Non", "Pas encore faite"]),
    ],
    "identification": [
        q("caller_bottom", "L’appelant est-il le nom affiché en bas, c’est-à-dire le propriétaire réel du compte ?", "En double identification, le nom du haut est celui de la pièce utilisée ; le nom du bas est le propriétaire réel du compte.", ["Oui", "Non", "Je ne sais pas"]),
        q("admits", "Le client reconnaît-il avoir utilisé la pièce d’une autre personne pour déplafonner ?", "Si oui, on règle l’identité avant toute autre action, sauf blocage Fraude.", ["Oui", "Non", "Je ne sais pas"]),
        q("security", "Les questions de sécurité BO sont-elles réussies ?", "Pour rejeter la pièce dans ce cas, le BO doit sécuriser l’identité selon le process.", ["Oui", "Non", "Pas encore"]),
    ],
    "canal": [
        q("number_call", "Le client appelle-t-il avec le numéro Wave qui a effectué le paiement Canal+ ?", "C’est le prérequis avant de vérifier le paiement Canal+.", ["Oui", "Non", "Je ne sais pas"]),
        q("reab_number", "Le numéro de réabonnement visible sur Front correspond-il exactement au numéro donné par le client ?", "Si le numéro est correct mais les chaînes ne fonctionnent pas, Wave n’a pas d’action de correction : le client contacte Canal+.", ["Oui, il est correct", "Non, il est incorrect", "Je ne sais pas"]),
        q("canal_case", "Quel est le cas exact signalé ?", "Canal+ a plusieurs branches : pas d’image, erreur de numéro, option par erreur, double recharge, offre supérieure/inférieure.", ["Pas d’image après paiement", "Erreur sur le numéro", "Option ou offre choisie par erreur", "Double recharge", "Offre supérieure à celle souhaitée", "Offre inférieure à celle souhaitée"]),
        q("seven_days", "La date de fin d’abonnement laisse-t-elle au moins 7 jours ouvrés pour le traitement ?", "Cette question concerne uniquement erreur de numéro ou offre supérieure. Sinon elle n’est pas utile.", ["Oui", "Non", "Non applicable"]),
    ],
    "agent_reject_id": [
        q("agent_id", "Le compte concerné est-il bien un compte Agent ?", "Le rejet de pièce agent suit le process BO via #ci-compliance, pas Recover PIN.", ["Oui", "Non", "Je ne sais pas"]),
        q("reason", "Quel est le motif du rejet de la pièce agent ?", "Le motif doit être indiqué dans la demande #ci-compliance.", ["Pièce d’un tiers", "Compliance / identités multiples", "Pièce non conforme", "Autre"]),
    ],
    "refund": [
        q("multiple", "Le client demande-t-il plusieurs refunds ?", "Le process BO autorise plusieurs refunds ; la contestation du destinataire suit une autre branche.", ["Oui", "Non", "Je ne sais pas"]),
        q("dispute", "Le destinataire appelle-t-il pour contester un refund ?", "En cas de contestation, créer un ticket report refunding dispute et annoncer 48h jours ouvrés.", ["Oui", "Non", "Je ne sais pas"]),
    ],
    "move_balance": [
        q("app_active", "Le client utilise-t-il actuellement une application Wave sur smartphone ?", "Move balance coffre est prévu pour le client utilisateur de coffre qui n’a plus de smartphone/app active.", ["Non, aucune app active", "Oui", "Je ne sais pas"]),
        q("security4", "Le client a-t-il donné 4 bonnes réponses aux questions de sécurité ?", "Le move balance coffre exige 4 bonnes réponses et le PDV habituel doit être précis.", ["Oui", "Non", "Pas encore"]),
        q("total", "Le client confirme-t-il le montant total à transférer du coffre vers le solde principal ?", "Le process prévoit un move balance total, pas partiel.", ["Oui", "Non", "Je ne sais pas"]),
    ],
    "b2w": [
        q("error", "Le message d’erreur est-il clair dans Error details ?", "Si la raison est bancaire, il faut orienter vers la banque ; si elle n’est pas claire, faire Report B2W Problem.", ["Oui, raison bancaire claire", "Non, raison pas claire", "Cancelled and Refunded", "Après changement téléphone / device linking"]),
    ],
}

SIMPLE_DECISIONS = {
    "recover_pin": ("Recover PIN", "Guider le client selon Recover PIN FO/BO après vérification. Le client réinitialise lui-même son PIN ; donner les consignes et le délai prévu."),
    "reset_pin": ("Reset PIN", "Appliquer le process Reset PIN selon le rôle et les vérifications prévues."),
    "device_restriction": ("Device restriction", "Le client doit appeler du numéro concerné, être identifié, passer AB Verification puis lever la restriction si réussite. Si FO non autorisé selon cas, transférer."),
    "cie_sodeci": ("CIE / SODECI postpayé", "Ne pas escalader Partner Ops. Communiquer les références du reçu et orienter vers CIE 179 ou SODECI 175 / agence d’origine."),
    "cie_prepayee": ("CIE prépayée", "Vérifier numéro compteur/reçu. Si code visible, le communiquer ou envoyer via Bill Pay Code. Pas d’escalade Partner Ops ; orienter CIE 179 si besoin."),
    "startimes": ("Startimes", "Vérifier le numéro réabonné. Si correct, orienter Startimes 86060. Si erreur, Report Bill Payment Problem, délai 72h jours ouvrés."),
    "fer": ("FER", "Aucun remboursement. Si crédit non reçu après 5 minutes, Report Bill Payment Problem. Délai 72h."),
    "cnps": ("CNPS", "Si paiement inférieur : inviter à payer la différence. Si paiement supérieur : pas d’annulation Wave, voir CNPS. Erreur numéro CNPS : Report Bill Payment Problem, 72h."),
    "cit": ("CIT", "Aucun remboursement. Seule demande à soumettre : vérification de paiement. Pour annulation/erreur/remboursement, client va au bureau CIT."),
    "merchant_issue": ("Merchant issue", "Si numéro partenaire affiché, le communiquer et cliquer Fait. Si rappel ou pas de numéro partenaire, faire Merchant Issue avec détails, délai 72h jours ouvrés."),
    "merchant_creation": ("Création marchand / QR", "Vérifier conditions et éligibilité. Marchand auto-inscrit après 03/03/2025 demande QR dans Wave Business ; pas d’escalade Front si option disponible."),
    "refund_b2p": ("Refund B2P", "Marchand doit appeler avec le numéro qui a effectué la transaction. Vérifier infos, confirmer montant, faire refund si fonds disponibles. Corporate : Merchant Issue."),
    "agent_error": ("Erreur transaction agent", "Agent principal/assistant appelle 1315. Vérifier transaction. Dépôt : freeze deposit selon montant disponible + Escalate to support GL. Retrait : #1 si fonds disponibles + GL."),
    "agent_link": ("Lien application agent", "Agent appelle du numéro concerné, parler principal/assistant, demander désinstallation puis envoyer lien via Front > Agent > More > Send link to agent app."),
    "agent_prospect": ("Devenir agent / master agent", "Donner critères. Agent : lien Request to be an agent via Front. Master agent : si non-agent et conditions remplies, channel ci-master-agents ; si déjà agent, contacter responsable de zone."),
    "agent_assistant": ("Ajouter/retirer assistant", "Seul l’agent principal appelle avec numéro agent. Demande Slack ci-agent-management au TL + @ci-agent-admins avec template adapté."),
    "agent_commission": ("Commission agent", "Commission cut : Escalate > Request Risk to Explain Commissions Cut avec date. Non reçue : vérifier agent principal et paiement puis template ci-agent-management."),
    "agent_gaming": ("Agent gaming", "FO transfère l’appel à la Fraude."),
    "agent_recover_pin": ("Agent recover PIN", "Suivre process Recover PIN FO/BO : l’agent est aussi client ; changement PIN client impacte app agent/marchand."),
    "agent_complaint": ("Plainte client contre agent", "Rappeler gratuité du service, prendre coordonnées agence, Front > Agent > User Complaint, choisir motif, décrire détails."),
    "agent_scan_no_visibility": ("Scan sans visibilité transaction", "Agent appelle 1315. Confirmer scan + montant + type carte/app + date/tranche horaire + client + nature + montant. Escalate support GL, délai 24h."),
    "agent_box": ("Box Wave", "Client doit d’abord devenir agent. Si agent, renseigner la demande dans le fichier Box Wave prévu."),
    "agent_type": ("Type agent principal/assistant", "Dans onglet Agent > Agent user : primaire = principal. Principal gère commissions/assistants ; assistant fait transactions/MAJ app uniquement."),
    "agent_change_number": ("Changer numéro agent principal", "Demande Slack ci-agent-management au TL : ancien numéro principal vers nouveau numéro + cc @ci-agent-admins."),
    "agent_pdv": ("Localiser PDV", "Demander zone, chercher plateforme CI, communiquer agence proche. Puis expliquer au client comment consulter les PDV dans l’app. Pas besoin d’appeler du numéro compte."),
    "agent_rebalance_limit": ("Limite rééquilibrage agent", "Front compte agent : request to suspend rebalance limits. Ticket visible dans #ci-agent-management."),
    "agent_bank_rebalance": ("Rééquilibrage par banque", "Après bordereau soumis via app + 3h sans UV : demande dans ci-liquidity avec template montant/agent/banque/date."),
    "parental": ("Autorisation parentale", "Mineur KYC2 a besoin d’autorisation parentale. Envoyer liens ToolCI mineur/parent. Si impossible et client accepte, rejet de pièce après identification complète et type de pièce."),
    # ── Carte Visa Wave ──
    "visa_fraude":        ("Carte Visa — Fraude urgente", "⚠️ URGENT : Guider le client pour bloquer immédiatement sa carte depuis l’app Wave (Carte > Mes cartes > Bloquer). Transférer ensuite à l’équipe Virtual Visa pour investigation fraude avec : dates et montants des transactions suspectes, noms des marchands."),
    "visa_litige":        ("Carte Visa — Litige transaction", "Recueillir : date, montant, nom du marchand, statut de la transaction dans l’app (débitée/échouée). Transférer à l’équipe Virtual Visa avec tous ces détails pour ouverture de litige."),
    "visa_remboursement": ("Carte Visa — Remboursement", "Transférer à l’équipe Virtual Visa avec : date du paiement, montant, marchand, motif du remboursement (article non reçu, annulation, promesse marchand). Le délai est communiqué par l’équipe Virtual Visa."),
    "visa_paiement":      ("Carte Visa — Paiement refusé", "Vérifier le solde disponible sur la carte. Si solde suffisant, transférer à l’équipe Virtual Visa avec : nom du site/abonnement, type de paiement (international, récurrent, unique), message d’erreur visible."),
    "visa_carte":         ("Carte Visa — Gestion carte", "Transférer à l’équipe Virtual Visa en précisant la nature du problème : carte bloquée, récupération de fonds après perte téléphone, transfert vers compte principal, changement de téléphone."),
    "visa_info":          ("Carte Visa — Information", "Pour toute demande d’information sur la carte Visa Wave (tarifs, frais, activation, CVV, éligibilité KYC, verrouillage, option non visible) : transférer à l’équipe Virtual Visa."),
}

ROLE = {
    "agent_reject_id":"BO_ONLY", "deblocage_compte":"BO_ONLY", "identification":"BO_ONLY", "move_balance":"BO_ONLY", "parental":"BO_ONLY", "refund":"BO_ONLY",
    "agent_gaming":"FO", "agent_reject_id_fo":"FO", "canal":"FO", "cie_sodeci":"FO", "cie_prepayee":"FO", "startimes":"FO", "fer":"FO", "cnps":"FO", "cit":"FO",
}

# Fusion des personnalisations une fois SIMPLE_DECISIONS et ROLE définis
_fuse_custom()

def role_for(intent):
    return ROLE.get(intent, "FO_BO")

def title_for(intent):
    if intent in SIMPLE_DECISIONS: return SIMPLE_DECISIONS[intent][0]
    return {
        "qualification":"Cas à qualifier", "deblocage_compte":"Déblocage compte", "canal":"Réclamation Canal+", "identification":"Double identité / identification client", "agent_reject_id":"Rejet de pièce Agent", "refund":"Plusieurs refunds", "move_balance":"Move balance coffre", "b2w":"Bank To Wallet"
    }.get(intent, QUALIFY_OPTIONS.get(intent, intent))

def desc_for(intent):
    return {
        "qualification":"Aucun process exact détecté avec certitude. Knowledge doit demander une précision, pas inventer.",
        "deblocage_compte":"Déblocage d’un compte : il faut d’abord qualifier le motif visible Front, puis appliquer la branche exacte.",
        "canal":"Réclamation Canal+ : numéro correct/pas d’image, erreur de numéro, option, double recharge, offre supérieure/inférieure.",
        "identification":"Double identité : régler l’identité avant l’action principale, sauf blocage Fraude.",
        "agent_reject_id":"Rejet de pièce sur compte Agent : demande BO via #ci-compliance, pas Recover PIN.",
        "refund":"Plusieurs refunds BO et contestation éventuelle via report refunding dispute.",
        "move_balance":"Transfert total du coffre vers le solde principal pour client sans smartphone/app active, après 4 bonnes réponses sécurité.",
        "b2w":"Bank To Wallet : distinguer erreur bancaire claire, report B2W, ou device linking BO.",
    }.get(intent, SIMPLE_DECISIONS.get(intent, ("", ""))[1])

def forced_fo_view(intent):
    title = title_for(intent)
    if intent == "deblocage_compte":
        return ("Transfert BO requis", "Ce traitement est réservé au Back Office. Action FO : vérifier le numéro concerné si possible, noter le motif visible Front, puis transférer au BO. Ne pas lancer AB Verification et ne pas débloquer.")
    if intent in ["identification", "agent_reject_id", "move_balance", "parental", "refund"]:
        return ("Transfert BO requis", f"{title} est réservé au Back Office. Action FO : ne pas traiter l’action BO, sécuriser les informations utiles, faire #1/transférer selon queue BO et préciser le contexte.")
    return None

def decision(intent, answers, obstacles, profile):
    # Obstacle priority: fraud blocking wins over double identity for unblock.
    if "blocage_fraude" in obstacles and intent == "identification":
        return "warn", "Ticket déblocage compte", "Blocage Fraude détecté : ne pas rejeter la pièce et ne pas débloquer directement. Créer le ticket de déblocage de compte selon le process Fraude/Unblock Request."
    if "double_identite" in obstacles and intent not in ["identification", "agent_reject_id"]:
        return "warn", "Obstacle identité à traiter avant l’action", f"Objectif principal : {title_for(intent)}. Obstacle : double identité. Avant d’exécuter l’action demandée, traiter l’identification/rejet de pièce si l’appelant est le nom du bas et reconnaît avoir utilisé la pièce d’un tiers. Ensuite reprendre l’objectif initial."

    if intent == "qualification":
        return "warn", "Cas non qualifié", "Préciser le type de compte, l’opération demandée, le statut Front visible et le blocage éventuel. L’application ne doit pas inventer d’action."

    if intent == "deblocage_compte":
        reason = answers.get("reason")
        if reason == "Fraude":
            return "warn", "Ticket déblocage compte", "Blocage Fraude : ne pas débloquer directement. Créer le ticket de déblocage compte."
        if reason == "Device restriction":
            return "warn", "Traiter selon Device restriction", "Ce blocage est lié à un nouvel appareil. Passer au process Device restriction : le client doit appeler du numéro concerné, être identifié, passer AB Verification, puis lever la restriction. Si profil FO non autorisé, transférer au BO."
        if reason == "Autre / je ne sais pas":
            return "warn", "Qualifier le motif exact", "Le motif n’est pas identifiable. Demander au client de préciser la raison du blocage visible dans Front et appliquer le process correspondant."
        if answers.get("number") == "Non":
            return "stop", "Ne pas débloquer", "Le client doit appeler avec le numéro concerné. Ne pas poursuivre le déblocage."
        if answers.get("same_day") == "Oui":
            if answers.get("today_conditions") == "Non, une condition manque":
                return "stop", "Ne pas débloquer le même jour", "Le déblocage le jour même n’est autorisé que lundi-vendredi, au moins 2h après le blocage et avant 16h GMT."
            if answers.get("today_conditions") not in ["Oui, toutes les conditions sont réunies"]:
                return None
        if answers.get("same_day") == "Non, avant aujourd’hui":
            if answers.get("sat_sunday") == "Oui":
                return "stop", "Ne pas débloquer — rappeler lundi", "Le compte a été bloqué samedi après 13h et le rappel est dimanche : le déblocage n’est pas autorisé. Inviter le client à rappeler lundi."
        if answers.get("ab") == "Oui":
            return "ok", "Déblocage autorisé", "Cliquer sur Déblocage après AB Verification réussie. Toutes les questions doivent être répondues ; pour le PDV habituel, exiger un lieu précis."
        if answers.get("ab") == "Non":
            return "stop", "Ne pas débloquer", "AB Verification échouée : ne pas débloquer. Le système ajoute la note/log out, mettre fin à l’appel selon process."
        return None

    if intent == "identification":
        if answers.get("caller_bottom") == "Non":
            return "stop", "Demander au titulaire de rappeler", "Si l’appelant n’est pas le propriétaire réel/nom du bas, ne pas rejeter la pièce. Inviter le titulaire du compte à nous contacter."
        if answers.get("admits") == "Oui" and answers.get("security") == "Oui":
            return "ok", "Rejeter la pièce puis reprendre l’objectif initial", "Le client est le nom du bas, reconnaît avoir utilisé la pièce d’un tiers et les questions sécurité sont validées. Rejeter la pièce, l’inviter à refaire l’identification avec sa propre pièce, puis reprendre l’action initiale si applicable."
        if answers.get("admits") == "Non":
            return "warn", "Client nie l’utilisation d’une pièce tierce", "Le client nie avoir utilisé la pièce d’une autre personne malgré la double identité visible. Ne pas rejeter la pièce sans aveu. Informer le TL et escalader selon le process identification refus. Un signalement #ci-compliance peut être nécessaire si la double identité est confirmée système."
        if answers.get("security") == "Non":
            return "stop", "Ne pas rejeter", "Questions sécurité échouées : inviter le titulaire du compte/la bonne personne à rappeler selon process."
        return None

    if intent == "canal":
        if answers.get("number_call") == "Non":
            return "stop", "Ne pas traiter", "Le client doit appeler avec le numéro concerné pour cette vérification."
        num = answers.get("reab_number")
        case = answers.get("canal_case")
        if num == "Oui, il est correct" and case == "Pas d’image après paiement":
            return "ok", "Orienter Canal+", "Ne pas créer Bill Pay Problem. Le numéro réabonné est correct : inviter le client à contacter Canal+ au 1313 pour réactivation des chaînes."
        if case in ["Option ou offre choisie par erreur", "Double recharge", "Offre inférieure à celle souhaitée"]:
            return "ok", "Pas de remboursement / orientation", "Option non annulable ; double recharge = dates d’abonnement différentes ; offre inférieure non modifiable. Expliquer avec empathie selon la branche."
        if (num == "Non, il est incorrect" or case == "Erreur sur le numéro" or case == "Offre supérieure à celle souhaitée"):
            if answers.get("seven_days") == "Oui":
                return "ok", "Report Bill Payment Problem", "Créer Report Bill Payment Problem avec le bon numéro de réabonnement. Délai : environ 1 semaine ouvrée. Pas de remboursement ; offre supérieure = échelonnement si éligible."
            if answers.get("seven_days") == "Non":
                return "stop", "Ne pas remonter", "Délai Canal+ insuffisant : ne pas créer Bill Pay Problem. Inviter le client à contacter Canal+ au 1313 ou agence Canal+."
        return None

    if intent == "agent_reject_id":
        if answers.get("agent_id") == "Oui":
            if answers.get("reason"):
                return "ok", "Demande #ci-compliance", "Faire la demande dans #ci-compliance avec l’ID agent, le motif de rejet, tag @Daniel Keita et @Mariama. Annoncer 30 minutes au client."
            return None
        if answers.get("agent_id") == "Non":
            return "warn", "Compte non-agent — rediriger", "Ce compte n’est pas un compte agent. Si le client est KYC2 avec une double identité, traiter selon le process identification client standard. Pour tout autre motif de rejet de pièce, escalader selon le process adapté au type de compte."
        return None

    if intent == "refund":
        if answers.get("dispute") == "Oui":
            return "ok", "Report refunding dispute", "Créer un ticket via report refunding dispute sur les transactions concernées, recueillir le contexte et annoncer 48h jours ouvrés."
        if answers.get("multiple") == "Oui" and answers.get("dispute") is not None:
            return "ok", "Procéder aux remboursements", "BO : procéder aux refunds demandés. Si le destinataire conteste ensuite, créer report refunding dispute."
        if answers.get("multiple") == "Non" and answers.get("dispute") == "Non":
            return "warn", "Qualifier le type de remboursement", "Le client demande un remboursement unique. Préciser la nature de la transaction (B2W, Bill Pay, paiement marchand ?). Si remboursement Wave standard unique : traiter selon la procédure BO applicable. Si litige avec le destinataire : créer report refunding dispute."
        return None

    if intent == "move_balance":
        if answers.get("app_active") == "Oui":
            return "stop", "Ne pas faire move balance", "Le process vise un client sans smartphone/app active. S’il utilise encore une app, ne pas faire move balance support."
        if answers.get("security4") == "Oui" and answers.get("total") == "Oui":
            return "ok", "Move balance autorisé", "Faire le move balance total du coffre vers le compte principal depuis Front app. Pas de montant partiel."
        if answers.get("security4") == "Non":
            return "stop", "Ne pas faire move balance", "4 bonnes réponses sécurité sont obligatoires."
        if answers.get("security4") == "Oui" and answers.get("total") == "Non":
            return "warn", "Move balance total obligatoire", "Le process exige un transfert total du coffre vers le compte principal. Le montant partiel n’est pas autorisé. Expliquer la règle au client et demander confirmation du montant total. Si le client refuse, ne pas effectuer le move balance."
        return None

    if intent == "b2w":
        e = answers.get("error")
        if e == "Oui, raison bancaire claire":
            return "ok", "Orienter vers la banque", "Si Error details indique solde insuffisant, débit interdit, compte inactif ou message bancaire clair, rediriger le client vers son gestionnaire bancaire."
        if e == "Non, raison pas claire":
            return "ok", "Report B2W Problem", "Faire Report B2W Problem. Délai max 72h."
        if e == "Après changement téléphone / device linking":
            return "warn", "Transfert BO device linking", "FO : identifier, reformuler, noter TR: device linking B2W, transférer BO. BO suit Device linking BO process."
        if e == "Cancelled and Refunded":
            return "ok", "B2W annulé et remboursé automatiquement", "Le remboursement a été initié automatiquement par le système. Confirmer au client que les fonds ont été restitués sur son compte bancaire. Si les fonds ne sont pas visibles après 48h jours ouvrés, créer un Report B2W Problem."
        return None

    if intent in SIMPLE_DECISIONS:
        title, act = SIMPLE_DECISIONS[intent]
        return "ok", title, act
    return "warn", "Process détecté mais règle détaillée à compléter", "Afficher la fiche process validée, puis demander au manager d’ajouter la branche exécutable dans Administration."

def next_questions(intent, answers, obstacles):
    # Conditional pruning: don't ask dead-branch questions.
    qs = QUESTIONS.get(intent, [])
    if intent == "deblocage_compte":
        out=[]
        for item in qs:
            k=item["key"]
            if k=="today_conditions" and answers.get("same_day") != "Oui": continue
            if k=="sat_sunday" and answers.get("same_day") != "Non, avant aujourd’hui": continue
            if k=="ab":
                d=decision(intent, answers, obstacles, "Back Office")
                if d and d[0] in ["stop","warn"]: continue
                if not (answers.get("same_day") in ["Oui", "Non, avant aujourd’hui"]): continue
                if answers.get("same_day") == "Oui" and answers.get("today_conditions") != "Oui, toutes les conditions sont réunies": continue
                if answers.get("same_day") == "Non, avant aujourd’hui" and answers.get("sat_sunday") not in ["Non", None]: continue
            out.append(item)
        return out
    if intent == "canal":
        out=[]
        for item in qs:
            k=item["key"]
            if k=="seven_days":
                case=answers.get("canal_case"); num=answers.get("reab_number")
                if not (num == "Non, il est incorrect" or case in ["Erreur sur le numéro", "Offre supérieure à celle souhaitée"]):
                    continue
            out.append(item)
        return out
    return qs

def render_assistant(profile):
    st.markdown('<div class="wave-card"><div class="big-title">Knowledge Support Wave V7</div><p>Assistant métier : objectif client → obstacle → branche utile → décision conforme au rôle.</p></div>', unsafe_allow_html=True)
    text = st.text_area("Cas client / rep", height=115, placeholder="Ex : le client veut débloquer son compte, motif téléphone perdu, blocage samedi après 13h...")
    c1,c2 = st.columns([1,1])
    with c1:
        if st.button("Analyser le cas", type="primary", use_container_width=True): start_case(text)
    with c2:
        if st.button("Nouvelle analyse", use_container_width=True): reset_case(); st.rerun()
    if "intent" not in st.session_state: return
    intent = st.session_state.intent; obstacles = st.session_state.obstacles
    role = role_for(intent)
    st.markdown(f'<div class="process-card"><h1>{title_for(intent)}</h1><p>{desc_for(intent)}</p><span class="badge">{role}</span><span class="badge badge-orange">{"Général" if intent=="qualification" else "Process"}</span></div>', unsafe_allow_html=True)
    st.write(f"**Objectif principal détecté :** {title_for(intent)}")
    st.write(f"**Obstacle(s) détecté(s) :** {', '.join(obstacles) if obstacles else 'Aucun obstacle explicite'}")

    fo = forced_fo_view(intent) if profile == "Front Office" and role == "BO_ONLY" else None
    if fo:
        st.markdown(f'<div class="decision-warn"><h2>⚠️ {fo[0]}</h2><p><b>Action FO autorisée :</b> {fo[1]}</p></div>', unsafe_allow_html=True)
        return

    d = decision(intent, st.session_state.answers, obstacles, profile)
    if d:
        klass = "decision-ok" if d[0]=="ok" else "decision-stop" if d[0]=="stop" else "decision-warn"
        st.markdown(f'<div class="{klass}"><h2>{"✅" if d[0]=="ok" else "⛔" if d[0]=="stop" else "⚠️"} {d[1]}</h2><p><b>Action autorisée :</b> {d[2]}</p></div>', unsafe_allow_html=True)
        with st.expander("Résumé des réponses collectées"):
            if st.session_state.answers:
                for k,v in st.session_state.answers.items(): st.write(f"**{k}** : {v}")
            else: st.write("Aucune réponse collectée.")
        return

    qs = next_questions(intent, st.session_state.answers, obstacles)
    unanswered = [x for x in qs if x["key"] not in st.session_state.answers]
    if not unanswered:
        st.markdown('<div class="decision-warn"><h2>⚠️ Règle à compléter</h2><p>Les informations collectées ne déclenchent aucune décision. Ajouter une branche métier dans la matrice.</p></div>', unsafe_allow_html=True)
        return
    item = unanswered[0]
    st.progress((len(qs)-len(unanswered))/max(len(qs),1))
    st.markdown(f'<div class="question-card"><h2>{item["title"]}</h2><p><b>Pourquoi :</b> {item["why"]}</p></div>', unsafe_allow_html=True)
    ans = st.radio("Réponse", item["options"], key=f"radio_{item['key']}")
    note = st.text_input("Note utile / observation Front", key=f"note_{item['key']}", placeholder="Ex : motif Front, heure de blocage, nom du bas confirmé...")
    if st.button("Valider cette étape", type="primary"):
        st.session_state.answers[item["key"]] = ans
        if note: st.session_state.answers[item["key"]+"_note"] = note
        # ERR-C3 : si qualification manuelle → rediriger vers le bon process
        if st.session_state.intent == "qualification" and item["key"] == "precision":
            QUALIFY_REVERSE = {v: k for k, v in QUALIFY_OPTIONS.items()}
            new_intent = QUALIFY_REVERSE.get(ans)
            if new_intent:
                st.session_state.intent = new_intent
                st.session_state.answers = {}
        st.rerun()

# ------------------------------ Training bank ------------------------------

BANK = [
    # ══ FRONT OFFICE ══

    # ── Canal+ ──
    {"role":"FO","theme":"Canal+",
     "case":"Mme Diallo a payé Canal+ hier. Elle n’a toujours pas les images ce matin. Sur Front, le numéro de réabonnement correspond exactement à celui qu’elle a fourni. La date de fin d’abonnement est dans 12 jours ouvrés.",
     "q":"Quelle action entreprendre ?",
     "opts":["Orienter vers Canal+ au 1313 sans rien créer","Créer un Report Bill Payment Problem — délai suffisant pour traitement","Faire un Merchant Issue","Transférer au BO"],"a":1,
     "exp":"Numéro correct + pas d’images + 12 jours restants (≥ 7 jours ouvrés) = Report Bill Payment Problem. Canal+ dispose du temps nécessaire pour traiter."},

    {"role":"FO","theme":"Canal+",
     "case":"M. Kouamé a payé Canal+ il y a 3 jours. Pas d’images. Le numéro est correct sur Front. L’abonnement se termine dans 4 jours ouvrés.",
     "q":"Quelle est la bonne action ?",
     "opts":["Report Bill Payment Problem — le délai est encore acceptable","Orienter directement vers Canal+ au 1313 — délai insuffisant pour un ticket","Faire Merchant Issue","Rembourser et recréer un paiement"],"a":1,
     "exp":"Numéro correct + pas d’images + seulement 4 jours restants (< 7 jours ouvrés) = orienter Canal+ 1313 directement. Un Bill Payment Problem ne serait pas traité à temps."},

    {"role":"FO","theme":"Canal+",
     "case":"Un client vient de payer Canal+ il y a 30 minutes. Il appelle car il n’a pas encore les images. Le numéro affiché sur Front correspond à ce qu’il a fourni.",
     "q":"Que faire ?",
     "opts":["Créer immédiatement un Report Bill Payment Problem","Inviter le client à patienter — le traitement Canal+ prend quelques heures ; vérifier la date de fin pour décider de la suite si ça persiste","Orienter Canal+ 1313 sans attendre","Transférer BO"],"a":1,
     "exp":"Paiement très récent (30 min) : inviter à patienter. Aucune action prématurée. Si le problème persiste, vérifier la date de fin d’abonnement pour choisir entre Report Bill Pay Problem ou Canal+ 1313."},

    {"role":"FO","theme":"Canal+",
     "case":"Un client a payé Canal+ mais a saisi le mauvais numéro de décodeur. Le bon numéro est disponible. L’abonnement actuel se termine dans 9 jours ouvrés.",
     "q":"Action correcte ?",
     "opts":["Orienter vers Canal+ 1313 uniquement","Créer un Report Bill Payment Problem avec le numéro correct — délai suffisant","Rembourser et demander au client de repayer","Merchant Issue"],"a":1,
     "exp":"Erreur de numéro + 9 jours restants (≥ 7 jours ouvrés) = Report Bill Payment Problem avec le bon numéro. Délai de traitement environ 1 semaine ouvrée."},

    {"role":"FO","theme":"Canal+",
     "case":"Un client a payé Canal+ avec le mauvais numéro. L’abonnement actuel expire dans 5 jours.",
     "q":"Que faire ?",
     "opts":["Report Bill Payment Problem avec le bon numéro","Orienter vers Canal+ au 1313 — le délai est insuffisant pour traiter un ticket","Rembourser directement","Merchant Issue"],"a":1,
     "exp":"Erreur numéro + 5 jours restants (< 7 jours ouvrés) = orienter Canal+ 1313. Le ticket ne serait pas traité avant la fin d’abonnement."},

    {"role":"FO","theme":"Canal+",
     "case":"Un client a payé une offre Canal+ Evasion (inférieure à ce qu’il voulait). Il souhaitait Canal+ Total. Il demande à changer l’offre ou être remboursé.",
     "q":"Quelle réponse donner ?",
     "opts":["Modifier l’offre directement sur Front","Expliquer qu’une offre inférieure déjà souscrite n’est pas modifiable par Wave ; orienter vers Canal+ 1313","Rembourser et recréer le paiement","Report Bill Payment Problem"],"a":1,
     "exp":"Offre Canal+ inférieure déjà activée : Wave ne peut pas la modifier. Orienter le client vers Canal+ au 1313 pour une éventuelle solution de leur côté."},

    {"role":"FO","theme":"Canal+",
     "case":"Un client a rechargé Canal+ deux fois par erreur ce mois-ci. Il voit deux dates d’abonnement distinctes sur Front et réclame un remboursement du deuxième paiement.",
     "q":"Que lui expliquer ?",
     "opts":["Créer le remboursement du second paiement","Expliquer que les deux recharges s’ajoutent (dates différentes) et que c’est non annulable — aucun remboursement possible","Annuler uniquement la seconde recharge","Merchant Issue"],"a":1,
     "exp":"Double recharge Canal+ : les abonnements s’accumulent (dates différentes). Ce n’est pas une erreur corrigeable par Wave. Expliquer avec empathie : non annulable, non remboursable."},

    # ── CIE / SODECI / Facturiers ──
    {"role":"FO","theme":"CIE/SODECI",
     "case":"Un client CIE postpayé a payé sa facture via Wave. Le montant apparaît toujours comme impayé sur sa facture CIE. Il a son reçu Wave avec l’ID de transaction.",
     "q":"Que faire ?",
     "opts":["Escalader à Partner Ops","Communiquer la référence et l’ID de transaction, orienter le client vers CIE 179 ou son agence CIE","Rembourser et demander au client de repayer","Faire Merchant Issue"],"a":1,
     "exp":"CIE/SODECI postpayé : pas d’escalade Partner Ops. Communiquer les références du reçu. Orienter vers CIE 179 ou l’agence d’origine."},

    {"role":"FO","theme":"CIE prépayée",
     "case":"Un client a payé son compteur CIE prépayé via Wave et n’a pas reçu son code de recharge. En consultant Front, le code de recharge est visible dans les détails de la transaction.",
     "q":"Action correcte ?",
     "opts":["Lui demander d’attendre que CIE envoie le code","Communiquer le code directement ou l’envoyer par SMS via Bill Pay Code","Faire Report Bill Payment Problem","Escalader Partner Ops"],"a":1,
     "exp":"Code CIE prépayé visible sur Front = le communiquer au client ou l’envoyer via Bill Pay Code. Pas d’escalade nécessaire."},

    {"role":"FO","theme":"CIE prépayée",
     "case":"Un client a payé son compteur CIE prépayé. Il n’a pas reçu son code. Sur Front, le champ code est vide — le code n’est pas visible.",
     "q":"Action correcte ?",
     "opts":["Dire au client que le code arrivera tout seul","Créer Report Bill Payment Problem, délai 72h jours ouvrés ; orienter CIE 179 en complément","Rembourser directement","Escalader Partner Ops"],"a":1,
     "exp":"Code non visible sur Front = Report Bill Payment Problem, délai 72h jours ouvrés. Orienter également vers CIE 179 si le client a besoin du code rapidement."},

    {"role":"FO","theme":"Startimes",
     "case":"Un client a réabonné Startimes mais a saisi un numéro d’abonné erroné. Il s’en rend compte après le paiement.",
     "q":"Que faire ?",
     "opts":["Aucun recours possible — expliquer l’erreur et clore","Report Bill Payment Problem avec le bon numéro, délai 72h jours ouvrés","Orienter Startimes au 86060 sans rien créer","Rembourser Wave"],"a":1,
     "exp":"Startimes + erreur numéro = Report Bill Payment Problem avec le numéro correct, délai 72h jours ouvrés."},

    {"role":"FO","theme":"FER",
     "case":"Un client a payé sa carte FER mensuelle mais a saisi un mauvais numéro de badge. Il demande un remboursement ou un transfert vers le bon numéro.",
     "q":"Quelle est la réponse correcte ?",
     "opts":["Rembourser le montant payé","Transférer le crédit vers le bon numéro de badge","Ni remboursement ni transfert possible — aucune action corrective FER sur Wave","Merchant Issue"],"a":2,
     "exp":"FER : aucun remboursement ni transfert en cas d’erreur de numéro de badge. C’est définitif, expliquer au client."},

    {"role":"FO","theme":"CNPS",
     "case":"Un client a payé sa cotisation CNPS via Wave avec un montant supérieur à ce qu’il devait. Il demande à Wave de rembourser la différence.",
     "q":"Que faire ?",
     "opts":["Rembourser la différence directement","Annuler le paiement et le refaire au bon montant","Expliquer qu’aucune annulation n’est possible sur Wave ; orienter le client vers la CNPS directement","Report Bill Payment Problem"],"a":2,
     "exp":"CNPS : Wave ne peut ni annuler ni rembourser. Le client doit contacter la CNPS directement pour régulariser le trop-payé."},

    {"role":"FO","theme":"CIT",
     "case":"Un client a effectué un paiement CIT (Côte d’Ivoire Terminal) par erreur et demande un remboursement à Wave.",
     "q":"Action ?",
     "opts":["Procéder au remboursement Wave","Créer Report Bill Payment Problem","Aucun remboursement Wave — orienter le client vers le bureau CIT","Merchant Issue"],"a":2,
     "exp":"CIT : aucun remboursement possible via Wave. Le client doit se rendre physiquement au bureau CIT pour toute demande de remboursement ou correction."},

    # ── B2W ──
    {"role":"FO","theme":"B2W",
     "case":"Un client a tenté un virement de sa banque vers Wave (B2W). La transaction a échoué. En consultant Error details sur Front, le message indique clairement : ‘solde bancaire insuffisant’.",
     "q":"Quelle action prendre ?",
     "opts":["Créer un Report B2W Problem","Orienter le client vers sa banque ou son gestionnaire bancaire — raison claire côté banque","Faire Recover PIN","Transférer BO"],"a":1,
     "exp":"Error details B2W avec raison bancaire claire = orienter vers la banque. Wave n’a aucune action possible si le problème vient de la banque."},

    {"role":"FO","theme":"B2W",
     "case":"Un client a tenté un B2W resté en ‘pending’ depuis 2 jours. Error details sur Front ne montre aucune raison bancaire claire — juste un code d’erreur technique.",
     "q":"Action ?",
     "opts":["Orienter vers la banque — c’est forcément bancaire","Créer Report B2W Problem, délai max 72h jours ouvrés","Recover PIN","Ignorer, le pending se résoudra seul"],"a":1,
     "exp":"B2W pending sans raison bancaire claire = Report B2W Problem. Délai de résolution max 72h jours ouvrés."},

    {"role":"FO","theme":"B2W",
     "case":"Un client a changé de téléphone il y a une semaine. Depuis, son B2W est en échec systématique. Error details mentionne un problème lié au device linking.",
     "q":"Que faire en FO ?",
     "opts":["Traiter le B2W directement en FO","Identifier le client, noter ‘TR: device linking B2W’ et transférer au BO pour suivi du process device linking","Report B2W Problem standard","Recover PIN"],"a":1,
     "exp":"Device linking B2W : FO identifie, note explicitement le motif ‘TR: device linking B2W’ et transfère BO. Le BO applique ensuite le process device linking spécifique."},

    # ── Merchant ──
    {"role":"FO","theme":"Merchant",
     "case":"Un client a un litige sur un paiement marchand. En consultant Front sous Merchant Issue, le numéro du service client du partenaire s’affiche automatiquement.",
     "q":"Action correcte ?",
     "opts":["Ne jamais communiquer de numéro de partenaire au client","Communiquer le numéro au client, puis cliquer sur ‘Fait’","Créer un ticket Merchant Issue en plus","Rembourser directement"],"a":1,
     "exp":"Numéro partenaire affiché = le communiquer au client et cliquer ‘Fait’. Pas besoin de créer un ticket supplémentaire."},

    {"role":"FO","theme":"Merchant",
     "case":"Un client signale un problème sur un paiement marchand Wave. Sur Front, aucun numéro de partenaire n’est disponible dans les détails.",
     "q":"Action ?",
     "opts":["Dire au client qu’il n’y a rien à faire","Créer un Merchant Issue avec tous les détails (montant, marchand, date), délai 72h jours ouvrés","Rembourser directement","Orienter vers Canal+ 1313"],"a":1,
     "exp":"Pas de numéro partenaire = Merchant Issue avec tous les détails. Délai de résolution : 72h jours ouvrés."},

    # ── Agent ──
    {"role":"FO","theme":"Agent gaming",
     "case":"Un agent appelle pour une demande habituelle. En consultant son profil sur Front, vous constatez qu’il est marqué ‘Agent gaming’ dans le système.",
     "q":"Quelle est l’action FO immédiate ?",
     "opts":["Traiter sa demande normalement","Transférer immédiatement à l’équipe Fraude — aucune autre action en FO","Faire Recover PIN","Créer un Report Bill Payment Problem"],"a":1,
     "exp":"Agent gaming détecté : FO transfère immédiatement à l’équipe Fraude. Aucune autre action n’est autorisée en FO pour ce cas."},

    {"role":"FO","theme":"PDV",
     "case":"Un client cherche un point de vente Wave proche de son quartier. Il n’a pas son téléphone Wave à portée — il appelle depuis un autre numéro.",
     "q":"Que faire ?",
     "opts":["Lui dire d’abord d’appeler depuis son numéro Wave","Demander son quartier, rechercher sur la plateforme CI et lui communiquer les PDV proches — aucune authentification requise","Transférer au BO","Refuser : doit appeler depuis son compte"],"a":1,
     "exp":"Localiser PDV : aucune authentification du compte n’est requise. Demander simplement la zone, chercher sur la plateforme CI et communiquer les résultats."},

    {"role":"FO","theme":"Agent commission",
     "case":"Un agent principal appelle car ses commissions de la semaine dernière ont été coupées sans qu’il en ait reçu d’explication.",
     "q":"Action ?",
     "opts":["Rembourser les commissions","Escalader via ‘Request Risk to Explain Commissions Cut’ avec la date précise de la coupure","Faire Report B2W","Lui dire de contacter son responsable de zone directement"],"a":1,
     "exp":"Commission coupée : escalader via ‘Request Risk to Explain Commissions Cut’ avec la date précise. L’équipe Risk expliquera le motif."},

    {"role":"FO","theme":"Agent lien app",
     "case":"Un agent assistant appelle car son application Wave agent refuse de se lancer depuis hier — elle se ferme à l’ouverture.",
     "q":"Action ?",
     "opts":["Lui demander de se rendre en agence physique","Vérifier s’il est principal ou assistant, lui demander de désinstaller l’app, puis renvoyer le lien via Front > Agent > More > Send link to agent app","Faire Merchant Issue","Recover PIN"],"a":1,
     "exp":"App agent défaillante : désinstallation obligatoire puis renvoi du lien via Front > Agent > More > Send link. L’appel doit venir du numéro concerné (principal ou assistant)."},

    {"role":"FO","theme":"Agent prospect",
     "case":"Un client appelle et dit vouloir devenir agent Wave. Il veut savoir comment s’inscrire.",
     "q":"Quelle est la démarche correcte ?",
     "opts":["Lui créer le statut agent directement depuis Front","Lui expliquer les critères d’éligibilité et envoyer le lien ‘Request to be an agent’ via Front","Transférer au Manager","Créer un ticket BO pour traitement"],"a":1,
     "exp":"Devenir agent : expliquer les critères et envoyer le lien ‘Request to be an agent’ via Front. Pas de création manuelle de statut."},

    # ── Carte Visa Wave ──
    {"role":"FO","theme":"Carte Visa — Info",
     "case":"Un client appelle car il ne trouve pas l’option ‘Carte Visa’ dans son application Wave. Il ne sait pas s’il est éligible ni comment l’activer.",
     "q":"Action FO ?",
     "opts":["Activer la carte directement depuis Front","Transférer à l’équipe Virtual Visa — toute question sur la carte Visa leur appartient","Report B2W Problem","Recover PIN"],"a":1,
     "exp":"Toutes les demandes sur la carte Visa Wave (accès, activation, éligibilité, tarifs, CVV) : transférer à l’équipe Virtual Visa."},

    {"role":"FO","theme":"Carte Visa — Fraude",
     "case":"Un client signale 3 paiements inconnus effectués avec sa carte Visa Wave depuis ce matin. Il n’est pas à l’origine de ces transactions et craint une utilisation frauduleuse.",
     "q":"Quelle est la priorité absolue avant toute autre action ?",
     "opts":["Ouvrir directement un litige","Guider le client pour bloquer immédiatement sa carte depuis l’app Wave (Carte > Mes cartes > Bloquer), puis transférer l’équipe Virtual Visa avec les détails","Faire Report B2W","Recover PIN"],"a":1,
     "exp":"Fraude carte Visa : bloquer la carte EN PREMIER via l’app Wave. Ensuite transférer Virtual Visa avec dates, montants et marchands des transactions suspectes."},

    {"role":"FO","theme":"Carte Visa — Paiement refusé",
     "case":"Un client appelle car son paiement sur un site de e-commerce international est systématiquement refusé, alors que sa carte Visa Wave affiche un solde suffisant.",
     "q":"Action ?",
     "opts":["Rembourser le client","Vérifier le solde disponible sur la carte, puis transférer Virtual Visa avec : nom du site, type de paiement, message d’erreur affiché","Faire Merchant Issue","Recover PIN"],"a":1,
     "exp":"Paiement refusé carte Visa : vérifier le solde, puis transférer Virtual Visa avec tous les détails (site, type de paiement, message d’erreur). L’équipe Virtual Visa analysera la restriction."},

    {"role":"FO","theme":"Carte Visa — Litige",
     "case":"Un client constate qu’il a été débité deux fois pour le même achat effectué hier avec sa carte Visa Wave. Le marchand confirme n’avoir encaissé qu’une seule fois.",
     "q":"Action ?",
     "opts":["Procéder directement au remboursement du double débit","Recueillir date, montant, nom du marchand et transférer Virtual Visa pour ouverture de litige","Faire Report B2W Problem","Ignorer — les doublons se régulent automatiquement"],"a":1,
     "exp":"Double débit carte Visa : collecter date, montant, marchand et transférer Virtual Visa pour ouverture de litige. Ne pas rembourser directement — c’est le rôle de l’équipe Virtual Visa."},

    {"role":"FO","theme":"Carte Visa — Remboursement",
     "case":"Un client a payé une commande en ligne avec sa carte Visa Wave il y a 2 semaines. La commande n’est jamais arrivée. Le marchand refuse de le rembourser.",
     "q":"Action ?",
     "opts":["Rembourser directement sur le compte Wave","Transférer Virtual Visa avec date de paiement, montant, nom du marchand et motif (article non reçu, marchand non coopératif)","Report B2W Problem","Merchant Issue"],"a":1,
     "exp":"Remboursement carte Visa : transférer Virtual Visa avec tous les détails. Le délai de traitement est communiqué par l’équipe Virtual Visa."},

    # ══ BACK OFFICE ══

    # ── Déblocage compte ──
    {"role":"BO","theme":"Déblocage compte",
     "case":"Mme Koné a bloqué son compte Wave dimanche matin pour téléphone perdu. Elle rappelle le dimanche après-midi du même jour. Elle a sa pièce d’identité et réussit toutes les vérifications sécurité.",
     "q":"Décision BO ?",
     "opts":["Débloquer : elle a réussi les vérifications et c’est le même jour","Ne pas débloquer le même dimanche ; lui demander de rappeler à partir du lundi","Faire uniquement un Recover PIN","Rejeter la pièce d’identité"],"a":1,
     "exp":"Règle absolue : un compte bloqué un dimanche ne peut pas être débloqué le même jour, même si toutes les vérifications sont réussies. Rappeler à partir du lundi."},

    {"role":"BO","theme":"Déblocage compte",
     "case":"M. Bamba a bloqué son compte samedi à 15h00 pour téléphone volé. Il rappelle le dimanche avec sa pièce d’identité valide et réussit l’AB Verification.",
     "q":"Décision BO ?",
     "opts":["Débloquer : c’est le lendemain du blocage et les vérifications sont réussies","Ne pas débloquer — blocage samedi après 13h + rappel dimanche = demander de rappeler lundi","Report B2W","Créer ticket Fraude"],"a":1,
     "exp":"Cas spécial : blocage samedi après 13h + rappel dimanche = NE PAS débloquer. Demander de rappeler lundi. Ce cas précis ne permet pas le déblocage le dimanche."},

    {"role":"BO","theme":"Déblocage compte",
     "case":"Front affiche un blocage de type ‘Fraude’ sur le compte d’un client. Le client appelle le BO et réclame un déblocage immédiat en disant qu’il n’est pas concerné par une fraude.",
     "q":"Action BO ?",
     "opts":["Débloquer après identification et AB Verification si tout est OK","Créer le ticket déblocage compte via le process Fraude ; ne jamais débloquer directement un blocage Fraude","Faire Recover PIN uniquement","Rejeter la pièce d’identité"],"a":1,
     "exp":"Blocage Fraude : JAMAIS de déblocage direct, même si le client est convainquant. Créer le ticket déblocage compte via le process prévu. L’équipe compétente valide ensuite."},

    # ── Double identité ──
    {"role":"BO","theme":"Double identité",
     "case":"Un client appelle pour débloquer son compte. Sur Front, deux noms apparaissent : ‘M. Traoré’ (nom du haut) et ‘M. Bah’ (nom du bas). L’appelant se présente comme M. Bah et reconnaît avoir utilisé la CNI de son frère lors de l’inscription. Le blocage n’est pas lié à une Fraude.",
     "q":"Quelle est la priorité avant d’exécuter le déblocage ?",
     "opts":["Exécuter le déblocage directement — le client a fourni ses infos","Traiter d’abord la double identité : rejeter la pièce du tiers si les questions sécurité sont réussies, puis exécuter l’action","Créer un ticket Fraude automatiquement","Refuser définitivement toute action sur ce compte"],"a":1,
     "exp":"Double identité non Fraude : toujours résoudre la question d’identité en premier (rejet pièce tiers si sécurité OK), puis exécuter l’action principale."},

    {"role":"BO","theme":"Double identité + Fraude",
     "case":"Front affiche deux noms sur un compte avec un blocage de type Fraude. L’appelant demande à ce qu’on lui rejette la pièce d’identité du tiers pour régulariser son compte.",
     "q":"Action BO ?",
     "opts":["Procéder au rejet de pièce comme demandé","Créer le ticket déblocage compte via process Fraude — pas de rejet de pièce sur un blocage Fraude","Débloquer directement","Move balance vers un autre compte"],"a":1,
     "exp":"Double identité + blocage Fraude : le rejet de pièce est interdit. Créer le ticket déblocage compte via process Fraude. L’équipe compétente traitera ensuite."},

    # ── Identification ──
    {"role":"BO","theme":"Identification",
     "case":"M. Soro appelle et dit s’être inscrit sur Wave avec la CNI de sa femme. Il réussit les 4 questions sécurité obligatoires. Il demande une action sur le compte.",
     "q":"Action BO ?",
     "opts":["Exécuter l’action demandée — il a réussi les questions sécurité","Rejeter la pièce de la femme et inviter M. Soro à refaire l’identification avec sa propre CNI","Transférer FO","Fermer le compte définitivement"],"a":1,
     "exp":"Identification : sécurité réussie = rejeter la pièce du tiers et inviter à utiliser sa propre pièce d’identité. On ne peut pas exécuter l’action principale sans avoir régularisé l’identité."},

    {"role":"BO","theme":"Identification",
     "case":"Une femme appelle en disant gérer le compte Wave de son mari (qui est à l’étranger). Elle veut effectuer une action sur le compte. Elle ne peut pas passer les questions sécurité au nom du mari.",
     "q":"Action BO ?",
     "opts":["Effectuer l’action — le mari lui a donné l’autorisation","Ne pas rejeter la pièce ; inviter le titulaire réel du compte à rappeler lui-même","Créer un ticket Fraude","Débloquer directement"],"a":1,
     "exp":"Titulaire absent : si l’appelant n’est pas le propriétaire du compte, ne pas rejeter la pièce. Inviter le vrai titulaire à rappeler directement."},

    # ── Rejet pièce agent ──
    {"role":"BO","theme":"Rejet pièce agent",
     "case":"Un agent appelle le BO car la pièce d’identité enregistrée sur son compte agent n’est plus valide. Il veut qu’on la rejette pour pouvoir en enregistrer une nouvelle.",
     "q":"Process BO ?",
     "opts":["Rejeter la pièce directement depuis Front","Faire la demande dans #ci-compliance avec l’ID agent et le motif — délai 30 min","Faire Recover PIN","Canal+ 1313"],"a":1,
     "exp":"Rejet pièce agent : demande dans #ci-compliance avec ID agent et motif. Tagger les personnes prévues. Délai annoncé : 30 minutes."},

    # ── Refund ──
    {"role":"BO","theme":"Refund",
     "case":"Un client appelle le BO. Il a envoyé de l’argent par erreur à 3 personnes différentes lors de 3 transactions distinctes la semaine dernière. Il demande le remboursement des 3 transactions.",
     "q":"Action BO ?",
     "opts":["Refuser : maximum 1 refund à la fois","Procéder aux 3 remboursements — le BO peut traiter plusieurs refunds","Merchant Issue","Orienter vers FO"],"a":1,
     "exp":"Plusieurs refunds : le BO peut procéder à plusieurs remboursements. Si un destinataire conteste ensuite, créer un report refunding dispute."},

    {"role":"BO","theme":"Refund dispute",
     "case":"Le destinataire d’un virement erroné, qui avait été remboursé par le BO il y a 3 jours, appelle maintenant pour dire qu’il n’a jamais demandé ce refund et conteste l’opération.",
     "q":"Action BO ?",
     "opts":["Annuler le refund effectué","Créer un report refunding dispute et annoncer un délai de 48h jours ouvrés","Orienter Canal+ 1313","Rejeter la pièce d’identité"],"a":1,
     "exp":"Contestation de refund par le destinataire : créer report refunding dispute, délai de traitement 48h jours ouvrés."},

    # ── Move balance ──
    {"role":"BO","theme":"Move balance",
     "case":"Un client n’utilise plus de smartphone depuis 6 mois. Il a 150 000 FCFA dans son coffre Wave. Il appelle le BO pour transférer cet argent sur son compte principal Wave.",
     "q":"Quelles sont les deux conditions obligatoires avant d’effectuer le move balance ?",
     "opts":["2 réponses sécurité + accord du client","4 bonnes réponses aux questions sécurité + transfert du montant TOTAL du coffre (pas de partiel)","Identification simple + accord manager","KYC2 suffit, pas de questions sécurité"],"a":1,
     "exp":"Move balance coffre : 4 bonnes réponses aux questions sécurité obligatoires ET transfert du montant total uniquement. Aucun montant partiel autorisé."},

    {"role":"BO","theme":"Move balance",
     "case":"Un client réussit les 4 questions sécurité. Son coffre contient 200 000 FCFA. Il dit vouloir transférer uniquement 80 000 FCFA pour l’instant et garder le reste.",
     "q":"Action BO ?",
     "opts":["Transférer les 80 000 FCFA demandés — le client choisit le montant","Expliquer que le move balance est TOTAL uniquement ; demander confirmation pour les 200 000 FCFA. Si refus, ne pas procéder","Transférer FO","Rembourser le solde"],"a":1,
     "exp":"Move balance : transfert du montant TOTAL du coffre obligatoire. Le partiel n’est pas autorisé. Si le client refuse le total, ne pas procéder."},

    # ── Device restriction ──
    {"role":"BO","theme":"Device restriction",
     "case":"Un client a changé de téléphone il y a 2 jours. Maintenant son compte Wave est en ‘device restriction’ et il ne peut plus accéder à son argent.",
     "q":"Étapes obligatoires en BO ?",
     "opts":["Lever la restriction directement — changement de téléphone classique","Vérifier que l’appel vient du numéro concerné, identifier le client, effectuer AB Verification, puis lever la restriction si réussie","Faire Report B2W","Transférer FO"],"a":1,
     "exp":"Device restriction : l’appel DOIT venir du numéro du compte concerné. Identification + AB Verification obligatoires. Lever la restriction uniquement si AB Verification réussie."},

    # ── Refund B2P ──
    {"role":"BO","theme":"Refund B2P",
     "case":"Un marchand partenaire appelle le BO pour demander le remboursement d’un paiement B2P fait par un client hier. Il appelle depuis le numéro de son bureau (différent du numéro de la transaction).",
     "q":"Que faire ?",
     "opts":["Traiter le refund — le marchand a expliqué la situation","Demander au marchand de rappeler depuis le numéro qui a effectué la transaction","Merchant Issue","Créer Report B2W"],"a":1,
     "exp":"Refund B2P : le marchand doit obligatoirement appeler depuis le numéro qui a effectué la transaction. Pas d’exception. Vérifier infos, confirmer montant, refund si fonds disponibles."},

    # ── Autorisation parentale ──
    {"role":"BO","theme":"Autorisation parentale",
     "case":"Un mineur KYC2 appelle. Ses parents ne peuvent pas fournir l’autorisation parentale (document non disponible). Le mineur accepte explicitement que sa pièce soit rejetée pour revenir en KYC1.",
     "q":"Que faire ?",
     "opts":["Fermer définitivement le compte","Procéder à une identification complète + recueillir le type de pièce, puis rejeter la pièce pour revenir en KYC1","Transférer le compte à un parent","Débloquer les dépôts en attendant"],"a":1,
     "exp":"Mineur KYC2 sans approbation parentale possible, accepte le rejet : identification complète + type de pièce d’identité, rejet de l’ID pour revenir KYC1."},

    # ── Agent BO ──
    {"role":"BO","theme":"Agent assistant",
     "case":"Un assistant agent appelle le BO pour demander qu’on lui ajoute un deuxième assistant sur son compte.",
     "q":"Qui peut faire cette demande et comment ?",
     "opts":["L’assistant peut demander lui-même — il est concerné","Seul l’agent PRINCIPAL peut faire cette demande, depuis son numéro agent ; demande via ci-agent-management au TL avec @ci-agent-admins","Faire Merchant Issue","Transférer FO"],"a":1,
     "exp":"Ajouter/retirer un assistant : uniquement l’agent principal peut demander, depuis son numéro agent. Demande Slack dans ci-agent-management au TL + @ci-agent-admins avec le template."},

    {"role":"BO","theme":"Rééquilibrage banque",
     "case":"Un agent a soumis son bordereau de rééquilibrage via l’app Wave il y a 4h. Les fonds ne sont toujours pas arrivés sur son compte agent. Aucune UV reçue.",
     "q":"Action BO ?",
     "opts":["Lui dire d’attendre encore — le délai normal peut aller jusqu’à 6h","Créer une demande dans ci-liquidity avec montant, nom agent, banque et date","Report B2W Problem","Transférer FO"],"a":1,
     "exp":"Rééquilibrage par banque : bordereau soumis + plus de 3h sans UV = demande dans ci-liquidity avec le template complet (montant / agent / banque / date)."},
]

# ─── Helpers semaines 2026 ───
def get_week_of_2026(d=None):
    if d is None:
        d = date.today()
    start = date(2026, 1, 1)
    if d < start:
        return 1
    if d > date(2026, 12, 31):
        return 52
    return min(52, (d - start).days // 7 + 1)

def week_label(w):
    start = date(2026, 1, 1) + timedelta(weeks=w - 1)
    end = min(start + timedelta(days=6), date(2026, 12, 31))
    return f"Semaine {w}  ({start.strftime('%d %b')} – {end.strftime('%d %b')})"

def weekly_items(role, n, week, mix_fo_bo=False):
    seed = 2026 * 1000 + week + (7 if role == "Back Office" else 3) + (13 if mix_fo_bo else 0)
    if role == "Front Office":
        # FO : uniquement les questions FO
        pool = [x for x in BANK if x["role"] == "FO"]
    elif mix_fo_bo:
        # BO avec mix coché : questions BO + FO
        pool = BANK[:]
    else:
        # BO par défaut : uniquement les questions BO
        pool = [x for x in BANK if x["role"] == "BO"]
    rnd = random.Random(seed)
    items = pool[:]
    rnd.shuffle(items)
    seen = set(); diverse = []; rest = []
    for it in items:
        if it["theme"] not in seen:
            diverse.append(it); seen.add(it["theme"])
        else:
            rest.append(it)
    ordered = diverse + rest
    return ordered[:n]

def daily_items(role, n, offset=0):
    today = date.today().toordinal() + offset
    pool = [x for x in BANK if x["role"] == "FO" or (role == "Back Office" and x["role"] in ["FO","BO"])]
    rnd = random.Random(today + (7 if role=="Back Office" else 3))
    items = pool[:]
    rnd.shuffle(items)
    # enforce theme diversity first
    seen=set(); diverse=[]
    for it in items:
        if it["theme"] not in seen:
            diverse.append(it); seen.add(it["theme"])
        if len(diverse)>=n: break
    if len(diverse)<n: diverse += [x for x in items if x not in diverse][:n-len(diverse)]
    return diverse[:n]

def render_quiz(profile, rep_name):
    import io, csv
    st.markdown('<div class="wave-card"><div class="big-title">🎓 Quiz hebdomadaire</div><p>Même quiz pour tous les reps la même semaine — questions différentes chaque semaine.</p></div>', unsafe_allow_html=True)

    if not rep_name:
        st.warning("⚠️ Entrez votre nom dans la barre latérale avant de démarrer le quiz.")
        return

    # Sélection semaine
    current_week = get_week_of_2026()
    week = st.selectbox("Semaine du quiz", list(range(1, 53)),
                        index=current_week - 1,
                        format_func=week_label)

    # Profil et mix
    col_role, col_mix = st.columns([2, 1])
    with col_role:
        role = st.selectbox("Profil du quiz", ["Front Office", "Back Office"],
                            index=0 if profile == "Front Office" else 1)
    with col_mix:
        mix = False
        if role == "Back Office":
            mix = st.checkbox("Mixer FO + BO", value=False,
                              help="Inclure des questions Front Office en plus des questions BO")

    n = st.slider("Nombre de questions", 5, 15, 10)
    items = weekly_items(role, n, week, mix_fo_bo=mix)

    profil_label = f"{role}{' + FO' if mix else ''}"
    st.info(f"**{week_label(week)}** — {profil_label}. Toute l'équipe a les mêmes questions cette semaine.")

    answers = []
    for i, it in enumerate(items, 1):
        st.markdown(f'<div class="wave-card"><h3>Question {i} — {it["theme"]}</h3><p>{it["case"]}</p><b>{it["q"]}</b></div>', unsafe_allow_html=True)
        ans = st.radio("Réponse", it["opts"], key=f"quiz_{week}_{role}_{mix}_{i}")
        answers.append((it, ans))

    if st.button("✅ Corriger le quiz", type="primary"):
        score = 0; weak = []; detail = []
        for i, (it, ans) in enumerate(answers, 1):
            ok = it["opts"].index(ans) == it["a"]
            score += ok
            if not ok: weak.append(it["theme"])
            detail.append({"theme": it["theme"], "correct": ok})
            color = "✅" if ok else "❌"
            st.markdown(f"**Q{i} — {color} {it['theme']}**")
            st.write(f"Bonne réponse : **{it['opts'][it['a']]}**")
            st.caption(it["exp"])

        pct = round(score / len(items) * 100)
        if pct >= 80:
            st.success(f"🎉 Score : {score}/{len(items)} — {pct}%")
        elif pct >= 60:
            st.warning(f"📊 Score : {score}/{len(items)} — {pct}%")
        else:
            st.error(f"📉 Score : {score}/{len(items)} — {pct}% — Process à retravailler")

        if weak:
            st.warning("⚠️ Process à retravailler : " + ", ".join(sorted(set(weak))))

        # Sauvegarde résultat
        entry = {
            "rep": rep_name, "week": week, "year": 2026,
            "date": date.today().isoformat(), "profile": profil_label,
            "score": score, "total": len(items), "pct": pct,
            "weak": sorted(set(weak)), "detail": detail
        }
        try:
            save_result(entry)
        except Exception:
            pass

        # Export CSV individuel
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["Rep", "Semaine", "Date", "Profil", "Score", "Total", "%"])
        w.writerow([rep_name, week, date.today().isoformat(), profil_label, score, len(items), pct])
        w.writerow([])
        w.writerow(["#", "Thème", "Correct", "Bonne réponse"])
        for i2, (it2, ans2) in enumerate(answers, 1):
            ok2 = it2["opts"].index(ans2) == it2["a"]
            w.writerow([i2, it2["theme"], "Oui" if ok2 else "Non", it2["opts"][it2["a"]]])
        st.download_button(
            "📥 Exporter mon résultat (CSV)",
            buf.getvalue().encode("utf-8"),
            f"quiz_s{week:02d}_{rep_name.replace(' ', '_')}.csv",
            "text/csv",
            key="dl_quiz_result"
        )

def render_ranking():
    import io, csv
    st.markdown('<div class="wave-card"><div class="big-title">📊 Classement & Rapports</div><p>Résultats des quiz par semaine — classement équipe, process faibles, export.</p></div>', unsafe_allow_html=True)

    data = load_results()
    results = data.get("results", [])

    if not results:
        st.info("Aucun résultat enregistré. Les résultats apparaissent ici après la correction du quiz.")
        return

    weeks_available = sorted(set(r["week"] for r in results), reverse=True)
    week_sel = st.selectbox("Semaine à afficher", weeks_available, format_func=week_label)
    week_results = [r for r in results if r["week"] == week_sel]

    # Meilleur score par rep pour cette semaine
    best = {}
    for r in week_results:
        rep = r["rep"]
        if rep not in best or r["pct"] > best[rep]["pct"]:
            best[rep] = r
    ranking = sorted(best.values(), key=lambda x: x["pct"], reverse=True)

    # ── Classement
    st.markdown(f"### 🏆 Classement — {week_label(week_sel)}")
    medals = ["🥇", "🥈", "🥉"]
    for i, r in enumerate(ranking):
        med = medals[i] if i < 3 else f"{i+1}."
        pct = r["pct"]
        bar = "🟩" * (pct // 10) + "⬜" * (10 - pct // 10)
        lvl = "✅ En maîtrise" if pct >= 80 else "⚠️ En progression" if pct >= 60 else "❌ À renforcer"
        st.markdown(f"**{med} {r['rep']}** — {r['score']}/{r['total']} ({pct}%) — {r['profile']}  \n{bar} {lvl}")

    st.divider()

    # ── Process les plus échoués
    st.markdown("### 📉 Process les plus échoués cette semaine")
    theme_fails = {}
    theme_total = {}
    for r in week_results:
        for d in r.get("detail", []):
            t = d["theme"]
            theme_total[t] = theme_total.get(t, 0) + 1
            if not d["correct"]:
                theme_fails[t] = theme_fails.get(t, 0) + 1

    if theme_fails:
        sorted_fails = sorted(theme_fails.items(), key=lambda x: x[1], reverse=True)
        for theme, fails in sorted_fails[:10]:
            total_q = theme_total.get(theme, fails)
            pct_fail = round(fails / total_q * 100)
            bar = "🔴" if pct_fail >= 60 else "🟠" if pct_fail >= 30 else "🟡"
            st.write(f"{bar} **{theme}** — {fails} erreur(s) sur {total_q} tentative(s) ({pct_fail}% d'échec)")
    else:
        st.success("Aucune erreur cette semaine !")

    st.divider()

    # ── Export global
    st.markdown("### 📥 Export des résultats")
    col1, col2 = st.columns(2)
    with col1:
        # Export semaine sélectionnée
        buf_w = io.StringIO()
        ww = csv.writer(buf_w)
        ww.writerow(["Rep", "Semaine", "Date", "Profil", "Score", "Total", "%", "Process faibles"])
        for r in sorted(week_results, key=lambda x: x["pct"], reverse=True):
            ww.writerow([r["rep"], r["week"], r["date"], r["profile"],
                         r["score"], r["total"], r["pct"], ", ".join(r.get("weak", []))])
        st.download_button(
            f"📥 Semaine {week_sel} (CSV)",
            buf_w.getvalue().encode("utf-8"),
            f"quiz_semaine{week_sel:02d}.csv", "text/csv", key="dl_week"
        )
    with col2:
        # Export tous résultats
        buf_all = io.StringIO()
        wa = csv.writer(buf_all)
        wa.writerow(["Rep", "Semaine", "Date", "Profil", "Score", "Total", "%", "Process faibles"])
        for r in sorted(results, key=lambda x: (x["week"], x["rep"])):
            wa.writerow([r["rep"], r["week"], r["date"], r["profile"],
                         r["score"], r["total"], r["pct"], ", ".join(r.get("weak", []))])
        st.download_button(
            "📥 Tous les résultats (CSV)",
            buf_all.getvalue().encode("utf-8"),
            "quiz_resultats_complets.csv", "text/csv", key="dl_all"
        )

def render_cases(profile):
    st.markdown('<div class="wave-card"><div class="big-title">📞 Cas pratiques du jour</div><p>Scénarios narratifs quotidiens, sans annoncer le process dès le départ.</p></div>', unsafe_allow_html=True)
    role = st.selectbox("Cas pour", ["Front Office","Back Office"], index=0 if profile=="Front Office" else 1)
    day = st.date_input("Date des cas", value=date.today())
    count = st.slider("Nombre de cas", 3, 10, 5)
    items = daily_items(role, count, day.toordinal()-date.today().toordinal()+31)
    st.info(f"Cas pratiques du {day.isoformat()} — {role}. Série identique pour tous les reps ce jour-là.")
    for i,it in enumerate(items,1):
        st.markdown(f'<div class="wave-card"><h2>Cas {i}</h2><p>{it["case"]}</p><b>{it["q"]}</b></div>', unsafe_allow_html=True)
        ans=st.radio("Réponse", it["opts"], key=f"case_{day}_{role}_{i}")
        if st.button(f"Corriger le cas {i}"):
            ok = it["opts"].index(ans)==it["a"]
            if ok: st.success("Bonne réponse.")
            else: st.error("Réponse incorrecte.")
            st.write(f"Réponse attendue : **{it['opts'][it['a']]}**")
            st.caption(it["exp"])

def render_tests():
    st.markdown('<div class="wave-card"><div class="big-title">🧪 Tests métier V7</div><p>Cas critiques qui doivent rester cohérents avant tout déploiement.</p></div>', unsafe_allow_html=True)
    tests = [
        ("le client a payé canal mais n'a pas d'image", "canal"),
        ("un AGENT nous appelle et veut rejeter la pièce qui est sur le compte agent", "agent_reject_id"),
        ("Mme Yao a bloqué son compte samedi après 13h et rappelle dimanche", "deblocage_compte"),
        ("le client demande plusieurs refund", "refund"),
        ("le client souhaite faire un move balance mais il y a une double identité", "move_balance + obstacle double_identite"),
    ]
    for text, expected in tests:
        intent, obs, ranked = classify(text)
        st.write(f"**Cas :** {text}")
        st.write(f"Détecté : `{intent}` | obstacles : `{obs}` | attendu : `{expected}`")
        st.divider()

# ------------------------------ Administration ------------------------------

def render_admin(profile):
    if profile not in ["Back Office", "Manager"]:
        st.warning("⚠️ Le module Administration est réservé aux Back Office et Managers.")
        return

    st.markdown('<div class="wave-card"><div class="big-title">⚙️ Administration</div><p>Ajouter de nouveaux process, mettre à jour les keywords ou les décisions existantes.</p></div>', unsafe_allow_html=True)

    custom = load_custom()

    tab1, tab2, tab3, tab4 = st.tabs(["➕ Nouveau process", "🔑 Ajouter un keyword", "✏️ Modifier une décision", "📋 Voir les personnalisations"])

    # ── Tab 1 : Nouveau process ──
    with tab1:
        st.markdown("### Ajouter un nouveau process")
        st.caption("Un nouveau process sera disponible dans l'assistant et dans la liste de qualification.")

        col1, col2 = st.columns(2)
        with col1:
            new_id = st.text_input("ID du process (ex: detach_id)", key="admin_new_id",
                                   placeholder="sans espace, en minuscules, ex: kyc_upgrade")
        with col2:
            new_nom = st.text_input("Nom affiché (ex: Detach ID)", key="admin_new_nom",
                                    placeholder="Nom visible dans l'interface")

        new_desc = st.text_area("Description / action à effectuer", key="admin_new_desc", height=90,
                                placeholder="Décrivez le traitement exact que l'agent doit effectuer...")

        col3, col4 = st.columns(2)
        with col3:
            new_role = st.selectbox("Rôle autorisé", ["FO_BO", "BO_ONLY", "FO"], key="admin_new_role")
        with col4:
            new_kw_str = st.text_input("Mots-clés de détection (séparés par des virgules)",
                                       key="admin_new_kw",
                                       placeholder="ex: detach, dissocier, lien compte")

        if st.button("✅ Ajouter ce process", type="primary", key="admin_add_process"):
            pid = new_id.strip().lower().replace(" ", "_")
            nom = new_nom.strip()
            desc = new_desc.strip()
            kws_raw = [k.strip().lower() for k in new_kw_str.split(",") if k.strip()]

            if not pid or not nom or not desc:
                st.error("L'ID, le nom et la description sont obligatoires.")
            elif pid in QUALIFY_OPTIONS:
                st.error(f"Le process '{pid}' existe déjà dans le moteur.")
            else:
                custom.setdefault("qualify_options", {})[pid] = nom
                custom.setdefault("simple_decisions", {})[pid] = [nom, desc]
                if new_role != "FO_BO":
                    custom.setdefault("roles", {})[pid] = new_role
                if kws_raw:
                    custom.setdefault("keywords", []).append([pid, kws_raw, 100])
                save_custom(custom)
                QUALIFY_OPTIONS[pid] = nom
                SIMPLE_DECISIONS[pid] = (nom, desc)
                if new_role != "FO_BO":
                    ROLE[pid] = new_role
                if kws_raw:
                    KEYWORDS.append((pid, kws_raw, 100))
                st.success(f"✅ Process '{nom}' ajouté avec succès ! Rechargez la page pour le voir dans l'assistant.")
                st.balloons()

    # ── Tab 2 : Ajouter un keyword ──
    with tab2:
        st.markdown("### Ajouter un mot-clé de détection")
        st.caption("Renforce la détection d'un process existant avec de nouveaux mots-clés.")

        process_list = list(QUALIFY_OPTIONS.keys())
        process_labels = [f"{k} — {v}" for k, v in QUALIFY_OPTIONS.items()]
        kw_target_idx = st.selectbox("Process cible", range(len(process_list)),
                                     format_func=lambda i: process_labels[i], key="admin_kw_target")
        kw_target = process_list[kw_target_idx]

        kw_words = st.text_input("Mots-clés (tous doivent être présents, séparés par des virgules)",
                                 key="admin_kw_words",
                                 placeholder="ex: virement, banque, wave")
        kw_weight = st.slider("Poids du keyword (plus c'est élevé, plus il est prioritaire)", 60, 150, 90, key="admin_kw_weight")

        if st.button("✅ Ajouter ce keyword", type="primary", key="admin_add_kw"):
            words = [w.strip().lower() for w in kw_words.split(",") if w.strip()]
            if not words:
                st.error("Entrez au moins un mot-clé.")
            else:
                custom.setdefault("keywords", []).append([kw_target, words, kw_weight])
                save_custom(custom)
                KEYWORDS.append((kw_target, words, kw_weight))
                st.success(f"✅ Keyword [{', '.join(words)}] ajouté pour '{QUALIFY_OPTIONS[kw_target]}'.")

        # Afficher les keywords actuels du process sélectionné
        st.markdown(f"**Keywords actuels pour '{QUALIFY_OPTIONS[kw_target]}' :**")
        existing = [(w, wt) for intent, w, wt in KEYWORDS if intent == kw_target]
        if existing:
            for w, wt in existing:
                st.code(f"[{', '.join(w)}]  poids={wt}")
        else:
            st.caption("Aucun keyword actif — ce process est uniquement accessible via qualification manuelle.")

    # ── Tab 3 : Modifier une décision ──
    with tab3:
        st.markdown("### Modifier la description / action d'un process")
        st.caption("Met à jour la réponse affichée à l'agent pour un process simple.")

        proc_list_sd = [p for p in QUALIFY_OPTIONS if p in SIMPLE_DECISIONS]
        proc_labels_sd = [f"{p} — {QUALIFY_OPTIONS[p]}" for p in proc_list_sd]
        if proc_list_sd:
            edit_idx = st.selectbox("Process à modifier", range(len(proc_list_sd)),
                                    format_func=lambda i: proc_labels_sd[i], key="admin_edit_proc")
            edit_pid = proc_list_sd[edit_idx]
            current_title, current_desc = SIMPLE_DECISIONS[edit_pid]

            new_title = st.text_input("Titre de la décision", value=current_title, key="admin_edit_title")
            new_desc_edit = st.text_area("Action détaillée", value=current_desc, height=120, key="admin_edit_desc")

            if st.button("✅ Enregistrer les modifications", type="primary", key="admin_save_edit"):
                custom.setdefault("simple_decisions", {})[edit_pid] = [new_title.strip(), new_desc_edit.strip()]
                save_custom(custom)
                SIMPLE_DECISIONS[edit_pid] = (new_title.strip(), new_desc_edit.strip())
                st.success(f"✅ Process '{QUALIFY_OPTIONS[edit_pid]}' mis à jour.")
        else:
            st.info("Aucun process simple disponible.")

    # ── Tab 4 : Voir les personnalisations ──
    with tab4:
        st.markdown("### Personnalisations actuelles")
        if not custom or all(not v for v in custom.values()):
            st.info("Aucune personnalisation enregistrée. Utilisez les onglets ci-dessus pour en ajouter.")
        else:
            if custom.get("qualify_options"):
                st.markdown("**Nouveaux process ajoutés :**")
                for pid, nom in custom["qualify_options"].items():
                    st.write(f"- `{pid}` → **{nom}**")

            if custom.get("keywords"):
                st.markdown("**Keywords personnalisés :**")
                for kw in custom["keywords"]:
                    pid, words, weight = kw
                    pnom = QUALIFY_OPTIONS.get(pid, pid)
                    st.write(f"- **{pnom}** : [{', '.join(words)}] poids={weight}")

            if custom.get("simple_decisions"):
                st.markdown("**Décisions modifiées :**")
                for pid, dec in custom["simple_decisions"].items():
                    pnom = QUALIFY_OPTIONS.get(pid, pid)
                    st.write(f"- **{pnom}** : {dec[1][:80]}...")

        st.markdown("---")
        col_exp, col_del = st.columns(2)
        with col_exp:
            json_bytes = json.dumps(custom, ensure_ascii=False, indent=2).encode("utf-8")
            st.download_button(
                label="📥 Exporter le JSON",
                data=json_bytes,
                file_name="custom_processes.json",
                mime="application/json",
                key="admin_export",
                help="Téléchargez ce fichier et partagez-le avec Claude pour intégration permanente dans le moteur."
            )
        with col_del:
            if st.button("🗑️ Supprimer toutes les personnalisations", type="secondary", key="admin_reset"):
                save_custom({})
                st.warning("Toutes les personnalisations ont été supprimées. Rechargez la page.")

# ------------------------------ Layout ------------------------------

st.sidebar.markdown("## 🌊 Knowledge\n## Support Wave")
st.sidebar.markdown("### V7 — assistant métier")
profile = st.sidebar.radio("Profil", ["Front Office", "Back Office", "Manager"])
rep = st.sidebar.text_input("Nom du rep", placeholder="Ex : Serge", key="rep_name_input")
if rep:
    st.session_state["rep_name"] = rep
rep_name = st.session_state.get("rep_name", "")
if rep_name:
    st.sidebar.success(f"👤 {rep_name}")
else:
    st.sidebar.info("Entrez votre nom pour utiliser le quiz.")
module = st.sidebar.selectbox("Module", [
    "Assistant métier", "🎓 Quiz hebdomadaire", "📊 Classement",
    "Cas pratiques", "Tests métier V7", "⚙️ Administration"
])
st.sidebar.markdown("---")
st.sidebar.write("**Règle rôle :** FO voit uniquement les actions FO. BO voit FO + BO. Manager voit tout.")
st.sidebar.write("**Moteur :** objectif client + obstacles + branches conditionnelles.")
st.sidebar.write(f"**{len(QUALIFY_OPTIONS)} process · {len(KEYWORDS)} keywords · {len(BANK)} questions quiz**")

if module == "Assistant métier": render_assistant(profile)
elif module == "🎓 Quiz hebdomadaire": render_quiz(profile, rep_name)
elif module == "📊 Classement": render_ranking()
elif module == "Cas pratiques": render_cases(profile)
elif module == "Tests métier V7": render_tests()
else: render_admin(profile)

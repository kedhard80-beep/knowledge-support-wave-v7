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
.process-card {{background:#E9F9FD; border-left:7px solid #0BB4D8; border-radius:22px; padding:24px 28px; margin:18px 0; box-shadow:0 12px 28px rgba(38,189,226,.12);}}
.question-card {{background:#E9F9FD; border-left:7px solid #0A9FC3; border-radius:20px; padding:22px 26px; margin:16px 0;}}
.decision-ok {{background:#E8F8EF; border-left:7px solid {GREEN}; border-radius:20px; padding:22px 26px; margin:18px 0;}}
.decision-stop {{background:#FFF2F2; border-left:7px solid {RED}; border-radius:20px; padding:22px 26px; margin:18px 0;}}
.decision-warn {{background:#FFF7E6; border-left:7px solid {ORANGE}; border-radius:20px; padding:22px 26px; margin:18px 0;}}
.badge {{display:inline-block; padding:7px 12px; border-radius:999px; margin-right:8px; background:#D7F6FD; font-weight:800; color:#075F78;}}
.badge-orange {{background:#FFE8C7; color:#9A4E00;}}
.small-muted {{color:#667085; font-size:.95rem;}}
.big-title {{font-size:2.7rem; font-weight:900; color:{DARK}; line-height:1.05;}}
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
]

# ─── Fusion des process personnalisés ───
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
}

ROLE = {
    "agent_reject_id":"BO_ONLY", "deblocage_compte":"BO_ONLY", "identification":"BO_ONLY", "move_balance":"BO_ONLY", "parental":"BO_ONLY", "refund":"BO_ONLY",
    "agent_gaming":"FO", "agent_reject_id_fo":"FO", "canal":"FO", "cie_sodeci":"FO", "cie_prepayee":"FO", "startimes":"FO", "fer":"FO", "cnps":"FO", "cit":"FO",
}

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
    {"role":"FO","theme":"Canal+","case":"Un client a payé Canal+ et n’a pas les images. Le numéro de réabonnement visible sur Front correspond exactement au numéro donné.","q":"Quelle conduite tenir ?","opts":["Créer Bill Pay Problem","Orienter vers Canal+ au 1313","Faire Merchant Issue","Transférer BO"],"a":1,"exp":"Numéro correct + pas d’images = Wave n’a pas d’action corrective ; orienter Canal+ 1313."},
    {"role":"FO","theme":"Canal+","case":"Un client s’est trompé de numéro Canal+. La date de fin actuelle laisse au moins 7 jours ouvrés.","q":"Quelle action ?","opts":["Report Bill Payment Problem avec le bon numéro","Rembourser","Orienter uniquement 1313","Merchant Issue"],"a":0,"exp":"Erreur numéro + délai suffisant = Report Bill Payment Problem, délai environ 1 semaine ouvrée."},
    {"role":"FO","theme":"CIE/SODECI","case":"Un client CIE postpayé dit que le montant figure encore sur sa facture après paiement Wave.","q":"Que faire ?","opts":["Escalader Partner Ops","Communiquer référence/ID transaction et orienter CIE 179/agence","Rembourser","Faire Merchant Issue"],"a":1,"exp":"CIE/SODECI : pas d’escalade Partner Ops ; les infos du reçu servent à l’agence/service client."},
    {"role":"FO","theme":"CIE prépayée","case":"Un client n’a pas reçu son code CIE prépayé, mais le code est visible sur Front.","q":"Action correcte ?","opts":["Communiquer/envoyer le code via Bill Pay Code","Faire Bill Pay Problem","Rembourser","Orienter directement agence sans donner le code"],"a":0,"exp":"Si code visible, le communiquer ou l’envoyer par SMS via Bill Pay Code."},
    {"role":"FO","theme":"Startimes","case":"Un client Startimes a une erreur de numéro réabonné.","q":"Que faire ?","opts":["Report Bill Payment Problem, 72h jours ouvrés","Aucun recours","Refund","Canal 1313"],"a":0,"exp":"Startimes : si erreur, Report Bill Payment Problem, délai 72h jours ouvrés."},
    {"role":"FO","theme":"FER","case":"Un client a saisi un mauvais numéro de badge FER.","q":"Conduite ?","opts":["Rembourser","Transférer sur autre carte","Aucun remboursement/transfert possible","Merchant Issue"],"a":2,"exp":"FER : aucun remboursement ni transfert en cas d’erreur de carte."},
    {"role":"FO","theme":"B2W","case":"Error details B2W indique : solde bancaire insuffisant.","q":"Que faire ?","opts":["Report B2W automatiquement","Orienter vers le gestionnaire bancaire","Recover PIN","Merchant Issue"],"a":1,"exp":"Raison bancaire claire = orienter vers la banque."},
    {"role":"FO","theme":"Merchant","case":"Un client réclame sur un paiement marchand. Le numéro service client du partenaire s’affiche.","q":"Action ?","opts":["Communiquer le numéro puis cliquer Fait","Ne jamais communiquer de numéro","Créer directement ticket","Rembourser"],"a":0,"exp":"Si numéro partenaire fourni, le communiquer et cliquer Fait."},
    {"role":"FO","theme":"Agent","case":"Un agent signale gaming agent.","q":"Action FO ?","opts":["Traiter en FO","Transférer à la Fraude","Faire Recover PIN","Créer Bill Payment"],"a":1,"exp":"Gaming agent : FO transfère à la Fraude."},
    {"role":"FO","theme":"PDV","case":"Un client cherche un point de vente proche.","q":"Faut-il qu’il appelle avec son numéro Wave ?","opts":["Oui obligatoire","Non, demander la zone et chercher le PDV","Seulement KYC2","Transférer BO"],"a":1,"exp":"Localiser PDV : pas nécessaire d’appeler du numéro lié au compte."},
    {"role":"BO","theme":"Lost Phone","case":"Compte bloqué dimanche pour téléphone perdu. Le client rappelle le même dimanche.","q":"Décision ?","opts":["Débloquer après AB","Ne pas débloquer le même jour","Recover PIN uniquement","Rejet pièce"],"a":1,"exp":"Dimanche même jour = déblocage non autorisé ; possible à partir du lendemain."},
    {"role":"BO","theme":"Lost Phone","case":"Compte bloqué samedi après 13h. Le client rappelle dimanche.","q":"Décision ?","opts":["Débloquer après AB","Ne pas débloquer, rappeler lundi","Report B2W","Rejeter pièce"],"a":1,"exp":"Cas spécial : samedi après 13h + dimanche = rappeler lundi."},
    {"role":"BO","theme":"Double identité","case":"Client veut une action mais Front montre deux noms. L’appelant est le nom du bas et reconnaît avoir utilisé la pièce d’un tiers. Blocage non Fraude.","q":"Priorité ?","opts":["Exécuter l’action principale directement","Traiter d’abord l’identité/rejet pièce si sécurité validée","Créer ticket Fraude automatiquement","Refuser définitivement"],"a":1,"exp":"Double identité non Fraude : régler l’identité avant l’action principale."},
    {"role":"BO","theme":"Double identité + Fraude","case":"Compte avec double identité mais le blocage est Fraude.","q":"Action ?","opts":["Rejeter la pièce","Créer ticket déblocage compte, pas rejet ID","Débloquer direct","Move balance"],"a":1,"exp":"Blocage Fraude : pas de rejet de pièce ; ticket déblocage compte."},
    {"role":"BO","theme":"Rejet pièce agent","case":"Un agent demande le rejet de la pièce présente sur son compte agent.","q":"Process ?","opts":["Recover PIN","Demande #ci-compliance avec ID agent et motif","Canal+","Refund"],"a":1,"exp":"Rejet pièce agent : #ci-compliance, tag personnes prévues, délai annoncé 30 min."},
    {"role":"BO","theme":"Refund","case":"Un client demande plusieurs refunds.","q":"Action BO ?","opts":["Procéder aux remboursements","Toujours refuser","Merchant Issue","CIE 179"],"a":0,"exp":"BO peut procéder aux remboursements. Si contestation destinataire : report refunding dispute."},
    {"role":"BO","theme":"Refund dispute","case":"Le destinataire appelle pour contester un refund effectué.","q":"Action ?","opts":["Annuler le refund","Créer report refunding dispute et annoncer 48h jours ouvrés","Canal 1313","Rejeter pièce"],"a":1,"exp":"Contestations de refund : ticket report refunding dispute, 48h jours ouvrés."},
    {"role":"BO","theme":"Move balance","case":"Client sans smartphone veut transférer l’argent de son coffre vers solde principal.","q":"Condition clé ?","opts":["2 réponses sécurité","4 bonnes réponses + move balance total","Montant partiel autorisé","Aucun contrôle"],"a":1,"exp":"Move balance coffre : 4 bonnes réponses, transfert total uniquement."},
    {"role":"BO","theme":"Autorisation parentale","case":"Mineur KYC2 ne peut pas obtenir l’approbation parentale et accepte le rejet de pièce.","q":"Que faire ?","opts":["Fermer compte","Identifier complètement + type pièce puis rejeter ID","Débloquer dépôts","B2W"],"a":1,"exp":"Mineur sans approbation et accepte : identification complète + type pièce, rejet ID pour revenir KYC1."},
    {"role":"BO","theme":"Identification","case":"Client KYC2 dit avoir utilisé la pièce d’un proche. Il réussit les questions sécurité obligatoires.","q":"Action ?","opts":["Rejeter la pièce et inviter à refaire l’identification avec sa pièce","Débloquer sans action","Transférer FO","Refuser définitivement"],"a":0,"exp":"BO identification : si sécurité réussie, rejeter pièce du tiers et inviter à utiliser sa propre pièce."},
]

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

def render_quiz(profile):
    st.markdown('<div class="wave-card"><div class="big-title">🎓 Quiz du jour</div><p>Même quiz pour tous les reps le même jour, différent selon rôle et date.</p></div>', unsafe_allow_html=True)
    role = st.selectbox("Quiz pour", ["Front Office","Back Office"], index=0 if profile=="Front Office" else 1)
    day = st.date_input("Date du quiz", value=date.today())
    n = st.slider("Nombre de questions", 5, 15, 10)
    offset = day.toordinal() - date.today().toordinal()
    items = daily_items(role, n, offset)
    st.info(f"Quiz du {day.isoformat()} — {role}. Tous les reps ont les mêmes questions pour cette date.")
    answers=[]
    for i,it in enumerate(items,1):
        st.markdown(f'<div class="wave-card"><h3>Question {i} — {it["theme"]}</h3><p>{it["case"]}</p><b>{it["q"]}</b></div>', unsafe_allow_html=True)
        ans=st.radio("Réponse", it["opts"], key=f"quiz_{day}_{role}_{i}")
        answers.append((it, ans))
    if st.button("Corriger le quiz", type="primary"):
        score=0; weak=[]
        for i,(it,ans) in enumerate(answers,1):
            ok = it["opts"].index(ans)==it["a"]
            score += ok
            if not ok: weak.append(it["theme"])
            st.markdown(f"**Q{i} — {'✅' if ok else '❌'} {it['theme']}**")
            st.write(f"Bonne réponse : **{it['opts'][it['a']]}**")
            st.caption(it["exp"])
        st.success(f"Score : {score}/{len(items)}")
        if weak: st.warning("Process à retravailler : " + ", ".join(sorted(set(weak))))

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
        if st.button("🗑️ Supprimer toutes les personnalisations", type="secondary", key="admin_reset"):
            save_custom({})
            st.warning("Toutes les personnalisations ont été supprimées. Rechargez la page.")

# ------------------------------ Layout ------------------------------

st.sidebar.markdown("## 🌊 Knowledge\n## Support Wave")
st.sidebar.markdown("### V7 — assistant métier")
profile = st.sidebar.radio("Profil", ["Front Office", "Back Office", "Manager"])
rep = st.sidebar.text_input("Nom du rep", placeholder="Ex : Serge")
module = st.sidebar.selectbox("Module", ["Assistant métier", "Quiz du jour", "Cas pratiques", "Tests métier V7", "⚙️ Administration"])
st.sidebar.markdown("---")
st.sidebar.write("**Règle rôle :** FO voit uniquement les actions FO. BO voit FO + BO. Manager voit tout.")
st.sidebar.write("**Moteur :** objectif client + obstacles + branches conditionnelles.")
st.sidebar.write(f"**{len(QUALIFY_OPTIONS)+len(BANK)+80} éléments métier chargés**")

if module == "Assistant métier": render_assistant(profile)
elif module == "Quiz du jour": render_quiz(profile)
elif module == "Cas pratiques": render_cases(profile)
elif module == "Tests métier V7": render_tests()
else: render_admin(profile)

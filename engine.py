"""
engine.py — Moteur métier Knowledge Support Wave V7
Module autonome, sans dépendance Streamlit.
Importable directement pour tests automatiques.
"""

import re

# ──────────────────────────────────────────────
# RÉFÉRENTIEL PROCESS
# ──────────────────────────────────────────────

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
    "cit": "Côte d'Ivoire Terminal",
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
    # ── Identification client (rejet pièce compte personnel, sans mot "agent") ──
    ("identification", ["rejeter", "piece", "compte"], 112),
    ("identification", ["rejeter", "piece", "personnel"], 112),
    ("identification", ["changer", "piece", "compte"], 100),
    ("identification", ["rejeter", "piece", "client"], 108),
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
    ("agent_bank_rebalance", ["reequilibrage", "bordereau"], 105),
    ("agent_bank_rebalance", ["ci-liquidity"], 100),
    ("agent_bank_rebalance", ["bordereau", "agent", "fonds"], 105),
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
    ("b2w", ["transfert", "banque", "wave"], 90),
    ("b2w", ["wave", "to", "bank"], 90),
    ("merchant_creation", ["devenir", "marchand"], 95),
    ("merchant_creation", ["creation", "marchand"], 95),
    ("merchant_creation", ["marchand", "qr"], 95),
    ("merchant_creation", ["commercant", "qr"], 95),
    ("merchant_issue", ["merchant", "issue"], 95),
    ("merchant_issue", ["paiement", "marchand", "reclamation"], 95),
    ("merchant_issue", ["reclamation", "commercant"], 90),
    ("merchant_issue", ["probleme", "paiement", "marchand"], 90),
    ("refund_b2p", ["refund", "b2p"], 100),
    ("refund", ["plusieurs", "refund"], 100),
    ("refund", ["remboursement"], 85),
    ("refund", ["plusieurs", "remboursement"], 100),
    ("refund", ["plusieurs", "remboursements"], 100),
    ("refund", ["refund"], 85),
    ("refund", ["refunding"], 90),
    ("refund", ["refunding", "dispute"], 100),
    ("refund", ["dispute", "remboursement"], 95),
    # ── Solde / coffre ──
    ("move_balance", ["move", "balance"], 100),
    ("move_balance", ["moov", "balance"], 100),
    ("move_balance", ["mouvement", "balance"], 100),
    ("move_balance", ["coffre", "compte", "principal"], 90),
    ("move_balance", ["recuperer", "argent", "coffre"], 95),
    ("move_balance", ["balance", "coffre"], 92),
    ("move_balance", ["transferer", "coffre"], 90),
    ("move_balance", ["vider", "coffre"], 88),
    # ── Compte / accès ──
    ("deblocage_compte", ["debloquer", "compte"], 90),
    ("deblocage_compte", ["deblocage", "compte"], 90),
    ("deblocage_compte", ["bloque", "telephone", "perdu"], 95),
    ("deblocage_compte", ["compte", "bloque", "fraude"], 95),
    ("deblocage_compte", ["fraude", "compte"], 82),
    ("deblocage_compte", ["fraude", "mon", "compte"], 88),
    ("deblocage_compte", ["fraude", "signaler"], 85),
    ("recover_pin", ["recover", "pin"], 90),
    ("recover_pin", ["oublie", "pin"], 90),
    ("recover_pin", ["mot", "passe", "oublie"], 90),
    ("recover_pin", ["oublie", "mot", "passe"], 90),
    ("reset_pin", ["reset", "pin"], 90),
    ("reset_pin", ["changer", "pin"], 90),
    ("device_restriction", ["device", "restriction"], 95),
    ("device_restriction", ["nouveau", "telephone"], 85),
    ("device_restriction", ["change", "telephone"], 90),
    ("device_restriction", ["changement", "telephone"], 90),
    ("device_restriction", ["change", "appareil"], 90),
    ("device_restriction", ["nouveau", "appareil"], 85),
    ("device_restriction", ["changement", "appareil"], 90),
    ("device_restriction", ["change", "telephone", "banque"], 105),
    ("device_restriction", ["telephone", "perdu", "banque"], 100),
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
    # ── Parental — mots-clés stricts ──
    ("parental", ["mineur", "kyc"], 95),
    ("parental", ["mineur", "autorisation"], 95),
    ("parental", ["mineur", "compte"], 90),
    ("parental", ["enfant", "compte", "wave"], 90),
    ("parental", ["autorisation", "parentale"], 100),
    # ── Carte Visa Wave ──
    # Fraude / Sécurité urgente
    ("visa_fraude", ["visa", "fraude"], 122),
    ("visa_fraude", ["visa", "frauduleux"], 122),
    ("visa_fraude", ["visa", "inconnu", "debit"], 120),
    ("visa_fraude", ["visa", "inconnu", "paiement"], 120),
    ("visa_fraude", ["visa", "compromis"], 118),
    ("visa_fraude", ["visa", "cvv", "bloque"], 118),
    ("visa_fraude", ["visa", "utilisation", "inconnue"], 118),
    ("visa_fraude", ["visa", "quelqu"], 112),
    ("visa_fraude", ["visa", "acces", "carte"], 112),
    # Litige transaction
    ("visa_litige", ["visa", "debite", "non", "valide"], 115),
    ("visa_litige", ["visa", "debite", "deux"], 115),
    ("visa_litige", ["visa", "double", "debit"], 115),
    ("visa_litige", ["visa", "double"], 108),
    ("visa_litige", ["visa", "echoue", "debite"], 115),
    ("visa_litige", ["visa", "paiement", "echoue", "debite"], 115),
    ("visa_litige", ["visa", "marchand", "recu"], 110),
    ("visa_litige", ["visa", "litige"], 112),
    ("visa_litige", ["visa", "debit", "valide"], 112),
    # Remboursement Visa
    ("visa_remboursement", ["visa", "remboursement"], 112),
    ("visa_remboursement", ["visa", "rembourse"], 112),
    ("visa_remboursement", ["visa", "annulation", "paiement"], 110),
    ("visa_remboursement", ["carte", "visa", "remboursement"], 112),
    ("visa_remboursement", ["visa", "delai", "remboursement"], 108),
    ("visa_remboursement", ["visa", "article", "recu"], 108),
    ("visa_remboursement", ["visa", "commande", "annulee"], 108),
    # Paiement refusé / restriction
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
    # Gestion carte
    ("visa_carte", ["visa", "bloque"], 100),
    ("visa_carte", ["visa", "bloquee"], 100),
    ("visa_carte", ["visa", "debloquer"], 105),
    ("visa_carte", ["visa", "telephone", "perdu"], 108),
    ("visa_carte", ["visa", "changer", "telephone"], 102),
    ("visa_carte", ["visa", "nouveau", "telephone"], 102),
    ("visa_carte", ["visa", "transferer", "fonds"], 108),
    ("visa_carte", ["visa", "recuperer", "argent"], 108),
    ("visa_carte", ["visa", "fonds", "carte"], 102),
    # Information / tarification Visa
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

SIMPLE_DECISIONS = {
    "recover_pin": ("Recover PIN", "Guider le client selon Recover PIN FO/BO après vérification. Le client réinitialise lui-même son PIN ; donner les consignes et le délai prévu."),
    "reset_pin": ("Reset PIN", "Appliquer le process Reset PIN selon le rôle et les vérifications prévues."),
    "device_restriction": ("Device restriction", "Le client doit appeler du numéro concerné, être identifié, passer AB Verification puis lever la restriction si réussite. Si FO non autorisé selon cas, transférer."),
    "cie_sodeci": ("CIE / SODECI postpayé", "Ne pas escalader Partner Ops. Communiquer les références du reçu et orienter vers CIE 179 ou SODECI 175 / agence d'origine."),
    "cie_prepayee": ("CIE prépayée", "Vérifier numéro compteur/reçu. Si code visible, le communiquer ou envoyer via Bill Pay Code. Pas d'escalade Partner Ops ; orienter CIE 179 si besoin."),
    "startimes": ("Startimes", "Vérifier le numéro réabonné. Si correct, orienter Startimes 86060. Si erreur, Report Bill Payment Problem, délai 72h jours ouvrés."),
    "fer": ("FER", "Aucun remboursement. Si crédit non reçu après 5 minutes, Report Bill Payment Problem. Délai 72h."),
    "cnps": ("CNPS", "Si paiement inférieur : inviter à payer la différence. Si paiement supérieur : pas d'annulation Wave, voir CNPS. Erreur numéro CNPS : Report Bill Payment Problem, 72h."),
    "cit": ("CIT", "Aucun remboursement. Seule demande à soumettre : vérification de paiement. Pour annulation/erreur/remboursement, client va au bureau CIT."),
    "merchant_issue": ("Merchant issue", "Si numéro partenaire affiché, le communiquer et cliquer Fait. Si rappel ou pas de numéro partenaire, faire Merchant Issue avec détails, délai 72h jours ouvrés."),
    "merchant_creation": ("Création marchand / QR", "Vérifier conditions et éligibilité. Marchand auto-inscrit après 03/03/2025 demande QR dans Wave Business ; pas d'escalade Front si option disponible."),
    "refund_b2p": ("Refund B2P", "Marchand doit appeler avec le numéro qui a effectué la transaction. Vérifier infos, confirmer montant, faire refund si fonds disponibles. Corporate : Merchant Issue."),
    "agent_error": ("Erreur transaction agent", "Agent principal/assistant appelle 1315. Vérifier transaction. Dépôt : freeze deposit selon montant disponible + Escalate to support GL. Retrait : #1 si fonds disponibles + GL."),
    "agent_link": ("Lien application agent", "Agent appelle du numéro concerné, parler principal/assistant, demander désinstallation puis envoyer lien via Front > Agent > More > Send link to agent app."),
    "agent_prospect": ("Devenir agent / master agent", "Donner critères. Agent : lien Request to be an agent via Front. Master agent : si non-agent et conditions remplies, channel ci-master-agents ; si déjà agent, contacter responsable de zone."),
    "agent_assistant": ("Ajouter/retirer assistant", "Seul l'agent principal appelle avec numéro agent. Demande Slack ci-agent-management au TL + @ci-agent-admins avec template adapté."),
    "agent_commission": ("Commission agent", "Commission cut : Escalate > Request Risk to Explain Commissions Cut avec date. Non reçue : vérifier agent principal et paiement puis template ci-agent-management."),
    "agent_gaming": ("Agent gaming", "FO transfère l'appel à la Fraude."),
    "agent_recover_pin": ("Agent recover PIN", "Suivre process Recover PIN FO/BO : l'agent est aussi client ; changement PIN client impacte app agent/marchand."),
    "agent_complaint": ("Plainte client contre agent", "Rappeler gratuité du service, prendre coordonnées agence, Front > Agent > User Complaint, choisir motif, décrire détails."),
    "agent_scan_no_visibility": ("Scan sans visibilité transaction", "Agent appelle 1315. Confirmer scan + montant + type carte/app + date/tranche horaire + client + nature + montant. Escalate support GL, délai 24h."),
    "agent_box": ("Box Wave", "Client doit d'abord devenir agent. Si agent, renseigner la demande dans le fichier Box Wave prévu."),
    "agent_type": ("Type agent principal/assistant", "Dans onglet Agent > Agent user : primaire = principal. Principal gère commissions/assistants ; assistant fait transactions/MAJ app uniquement."),
    "agent_change_number": ("Changer numéro agent principal", "Demande Slack ci-agent-management au TL : ancien numéro principal vers nouveau numéro + cc @ci-agent-admins."),
    "agent_pdv": ("Localiser PDV", "Demander zone, chercher plateforme CI, communiquer agence proche. Puis expliquer au client comment consulter les PDV dans l'app. Pas besoin d'appeler du numéro compte."),
    "agent_rebalance_limit": ("Limite rééquilibrage agent", "Front compte agent : request to suspend rebalance limits. Ticket visible dans #ci-agent-management."),
    "agent_bank_rebalance": ("Rééquilibrage par banque", "Après bordereau soumis via app + 3h sans UV : demande dans ci-liquidity avec template montant/agent/banque/date."),
    "parental": ("Autorisation parentale", "Mineur KYC2 a besoin d'autorisation parentale. Envoyer liens ToolCI mineur/parent. Si impossible et client accepte, rejet de pièce après identification complète et type de pièce."),
    # ── Carte Visa Wave ──
    # Les reps BO traitent directement les cas Visa. Seuls les cas nécessitant
    # une intervention technique des agents Virtual Visa font l'objet d'un ticket.
    "visa_fraude":        ("Carte Visa — Fraude urgente", "⚠️ URGENT : Guider le client pour bloquer immédiatement sa carte depuis l'app Wave (Carte > Mes cartes > Bloquer). BO : traiter directement si possible. Si investigation approfondie requise, créer un ticket pour l'équipe Virtual Visa avec : dates, montants et marchands des transactions suspectes."),
    "visa_litige":        ("Carte Visa — Litige transaction", "Recueillir : date, montant, nom du marchand, statut de la transaction (débitée/échouée). BO : traiter si résolution directe possible. Si intervention agents Virtual Visa requise, créer un ticket avec tous ces détails pour ouverture de litige."),
    "visa_remboursement": ("Carte Visa — Remboursement", "Recueillir : date du paiement, montant, marchand, motif (article non reçu, annulation, promesse marchand). BO : traiter directement si possible. Si intervention Virtual Visa nécessaire, créer un ticket — le délai est communiqué par leur équipe."),
    "visa_paiement":      ("Carte Visa — Paiement refusé", "Vérifier le solde disponible sur la carte. BO : traiter si diagnostic direct possible. Si restriction technique nécessitant les agents Virtual Visa, créer un ticket avec : nom du site/abonnement, type de paiement (international, récurrent, unique), message d'erreur visible."),
    "visa_carte":         ("Carte Visa — Gestion carte", "BO : traiter directement selon la nature du problème (carte bloquée, récupération fonds, changement téléphone). Si intervention agents Virtual Visa requise, créer un ticket en précisant : nature du problème, numéro de carte, actions déjà tentées."),
    "visa_info":          ("Carte Visa — Information", "BO : répondre directement aux questions d'information (tarifs, frais, activation, CVV, éligibilité KYC, verrouillage). Si action technique réservée aux agents Virtual Visa, créer un ticket avec le détail de la demande."),
}

ROLE = {
    "agent_reject_id": "BO_ONLY",
    "deblocage_compte": "BO_ONLY",
    "identification": "BO_ONLY",
    "move_balance": "BO_ONLY",
    "parental": "BO_ONLY",
    "refund": "BO_ONLY",
    "agent_gaming": "FO",
    "agent_reject_id_fo": "FO",
    "canal": "FO",
    "cie_sodeci": "FO",
    "cie_prepayee": "FO",
    "startimes": "FO",
    "fer": "FO",
    "cnps": "FO",
    "cit": "FO",
}

def q(key, title, why, options):
    return {"key": key, "title": title, "why": why, "options": options}

QUESTIONS = {
    "qualification": [q("precision", "Quelle est la demande exacte du client ?", "L'application ne doit pas inventer d'action.", list(QUALIFY_OPTIONS.values()))],
    "deblocage_compte": [
        q("reason", "Quel est le motif visible du blocage du compte ?", "Le traitement dépend du motif.", ["Téléphone perdu/volé", "Fraude", "Device restriction", "Autre / je ne sais pas"]),
        q("number", "Le client appelle-t-il avec le numéro concerné ?", "Obligatoire pour le déblocage.", ["Oui", "Non", "Je ne sais pas"]),
        q("same_day", "Le compte a-t-il été bloqué aujourd'hui ?", "Règles plus strictes le jour même.", ["Oui", "Non, avant aujourd'hui", "Je ne sais pas"]),
        q("today_conditions", "Si blocage aujourd'hui : est-ce un jour ouvré lundi-vendredi, au moins 2h après le blocage et avant 16h GMT ?", "Seule condition permettant le déblocage le jour même.", ["Oui, toutes les conditions sont réunies", "Non, une condition manque", "Non applicable"]),
        q("sat_sunday", "Si blocage avant aujourd'hui : le compte a-t-il été bloqué samedi après 13h et le client rappelle-t-il dimanche ?", "Ce cas spécial est interdit.", ["Oui", "Non", "Je ne sais pas"]),
        q("ab", "L'AB Verification est-elle réussie ?", "Toutes les questions AB doivent être validées.", ["Oui", "Non", "Pas encore faite"]),
    ],
    "identification": [
        q("caller_bottom", "L'appelant est-il le nom affiché en bas ?", "En double identification, le nom du bas est le propriétaire réel.", ["Oui", "Non", "Je ne sais pas"]),
        q("admits", "Le client reconnaît-il avoir utilisé la pièce d'une autre personne pour déplafonner ?", "Si oui, on règle l'identité avant toute autre action.", ["Oui", "Non", "Je ne sais pas"]),
        q("security", "Les questions de sécurité BO sont-elles réussies ?", "Pour rejeter la pièce dans ce cas, le BO doit sécuriser l'identité.", ["Oui", "Non", "Pas encore"]),
    ],
    "canal": [
        q("number_call", "Le client appelle-t-il avec le numéro Wave qui a effectué le paiement Canal+ ?", "Prérequis obligatoire.", ["Oui", "Non", "Je ne sais pas"]),
        q("reab_number", "Le numéro de réabonnement visible sur Front correspond-il exactement au numéro donné ?", "Si correct mais chaînes KO, Wave n'a pas d'action.", ["Oui, il est correct", "Non, il est incorrect", "Je ne sais pas"]),
        q("canal_case", "Quel est le cas exact signalé ?", "Canal+ a plusieurs branches.", ["Pas d'image après paiement", "Erreur sur le numéro", "Option ou offre choisie par erreur", "Double recharge", "Offre supérieure à celle souhaitée", "Offre inférieure à celle souhaitée"]),
        q("seven_days", "La date de fin d'abonnement laisse-t-elle au moins 7 jours ouvrés pour le traitement ?", "Concerne uniquement erreur de numéro ou offre supérieure.", ["Oui", "Non", "Non applicable"]),
    ],
    "agent_reject_id": [
        q("agent_id", "Le compte concerné est-il bien un compte Agent ?", "Le rejet de pièce agent suit #ci-compliance, pas Recover PIN.", ["Oui", "Non", "Je ne sais pas"]),
        q("reason", "Quel est le motif du rejet de la pièce agent ?", "Le motif doit figurer dans la demande.", ["Pièce d'un tiers", "Compliance / identités multiples", "Pièce non conforme", "Autre"]),
    ],
    "refund": [
        q("multiple", "Le client demande-t-il plusieurs refunds ?", "Le process BO autorise plusieurs refunds.", ["Oui", "Non", "Je ne sais pas"]),
        q("dispute", "Le destinataire appelle-t-il pour contester un refund ?", "En cas de contestation : report refunding dispute, 48h.", ["Oui", "Non", "Je ne sais pas"]),
    ],
    "move_balance": [
        q("app_active", "Le client utilise-t-il actuellement une application Wave sur smartphone ?", "Move balance vise un client sans app active.", ["Non, aucune app active", "Oui", "Je ne sais pas"]),
        q("security4", "Le client a-t-il donné 4 bonnes réponses aux questions de sécurité ?", "4 bonnes réponses obligatoires.", ["Oui", "Non", "Pas encore"]),
        q("total", "Le client confirme-t-il le montant total à transférer ?", "Le process prévoit un move balance total, pas partiel.", ["Oui", "Non", "Je ne sais pas"]),
    ],
    "b2w": [
        q("error", "Le message d'erreur est-il clair dans Error details ?", "Si raison bancaire, orienter vers la banque ; sinon Report B2W Problem.", ["Oui, raison bancaire claire", "Non, raison pas claire", "Cancelled and Refunded", "Après changement téléphone / device linking"]),
    ],
}

# ──────────────────────────────────────────────
# FONCTIONS MOTEUR
# ──────────────────────────────────────────────

def norm(s: str) -> str:
    repl = {"é":"e","è":"e","ê":"e","à":"a","ù":"u","ç":"c","ô":"o","î":"i","ï":"i","É":"e","À":"a"}
    for k, v in repl.items():
        s = s.replace(k, v)
    return s.lower()

def _wm(w, t):
    """Word-boundary match — évite les faux positifs de sous-chaîne."""
    return bool(re.search(r'(?<!\w)' + re.escape(w) + r'(?!\w)', t))

def classify(text):
    t = norm(text)
    scores = {}
    for intent, words, weight in KEYWORDS:
        if all(_wm(w, t) for w in words):
            scores[intent] = scores.get(intent, 0) + weight
    obstacles = []
    if any(x in t for x in ["double ident", "double id", "deux noms", "noms superposes", "nom du bas", "piece d'un", "piece de quelqu"]):
        obstacles.append("double_identite")
    if "fraude" in t or "fraud" in t:
        obstacles.append("blocage_fraude")
    if any(x in t for x in ["relance", "ticket ouvert", "ticket deja ouvert", "ticket est ouvert",
                              "ticket existe", "suivi ticket", "suivi de ma reclamation",
                              "suivi reclamation", "suivi de reclamation",
                              "suite de ma requete", "suite de sa requete", "suite du ticket",
                              "ticket en cours", "deja cree", "deja un ticket",
                              "ticket a ete ouvert", "ticket a deja ete", "ticket deja cree",
                              "problem ouvert", "problem en cours", "problem deja",
                              "dossier ouvert", "dossier en cours", "dossier deja",
                              "reclamation ouverte", "reclamation en cours"]):
        obstacles.append("ticket_existant")
    if "mineur" in t or "17 ans" in t or "16 ans" in t:
        obstacles.append("mineur")
    if "agent" in t and ("piece" in t or "id" in t) and ("rej" in t or "reject" in t):
        scores["agent_reject_id"] = scores.get("agent_reject_id", 0) + 150
    if not scores:
        return "qualification", obstacles, []
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return ranked[0][0], obstacles, ranked[:5]

def role_for(intent):
    return ROLE.get(intent, "FO_BO")

def title_for(intent):
    if intent in SIMPLE_DECISIONS:
        return SIMPLE_DECISIONS[intent][0]
    return {
        "qualification": "Cas à qualifier",
        "deblocage_compte": "Déblocage compte",
        "canal": "Réclamation Canal+",
        "identification": "Double identité / identification client",
        "agent_reject_id": "Rejet de pièce Agent",
        "refund": "Plusieurs refunds",
        "move_balance": "Move balance coffre",
        "b2w": "Bank To Wallet",
    }.get(intent, QUALIFY_OPTIONS.get(intent, intent))

def desc_for(intent):
    return {
        "qualification": "Aucun process exact détecté avec certitude.",
        "deblocage_compte": "Déblocage d'un compte : qualifier le motif visible Front.",
        "canal": "Réclamation Canal+.",
        "identification": "Double identité : régler l'identité avant l'action principale.",
        "agent_reject_id": "Rejet de pièce sur compte Agent : #ci-compliance.",
        "refund": "Plusieurs refunds BO et contestation éventuelle.",
        "move_balance": "Transfert total du coffre vers le solde principal.",
        "b2w": "Bank To Wallet : distinguer erreur bancaire, report B2W, ou device linking.",
    }.get(intent, SIMPLE_DECISIONS.get(intent, ("", ""))[1])

def allowed_for_profile(rule_role, profile):
    if profile == "Manager": return True
    if rule_role == "FO_BO": return True
    if rule_role == "FO" and profile == "Front Office": return True
    if rule_role == "BO_ONLY" and profile == "Back Office": return True
    return False

def forced_fo_view(intent):
    title = title_for(intent)
    if intent == "deblocage_compte":
        return ("Transfert BO requis", "Ce traitement est réservé au Back Office.")
    if intent in ["identification", "agent_reject_id", "move_balance", "parental", "refund"]:
        return ("Transfert BO requis", f"{title} est réservé au Back Office.")
    return None

# Processes qui créent un ticket/escalade → sujet à relance
RELANCE_INFO = {
    "deblocage_compte":     ("ticket de déblocage compte",                         "Délai selon l'équipe Fraude/Unblock."),
    "b2w":                  ("Report B2W Problem",                                  "Délai max 72h jours ouvrés."),
    "canal":                ("Report Bill Payment Problem",                          "Délai environ 1 semaine ouvrée."),
    "refund":               ("Report refunding dispute",                             "Délai 48h jours ouvrés."),
    "merchant_issue":       ("Merchant Issue",                                       "Délai 72h jours ouvrés."),
    "startimes":            ("Report Bill Payment Problem",                          "Délai 72h jours ouvrés."),
    "cie_prepayee":         ("Report Bill Pay Problem",                              "Délai 72h jours ouvrés."),
    "agent_bank_rebalance": ("demande de rééquilibrage dans #ci-liquidity",         "Délai normalement résolu en quelques heures."),
    "agent_reject_id":      ("demande #ci-compliance",                              "Délai 30 minutes en jours ouvrés."),
    "visa_fraude":          ("dossier Fraude Virtual Visa",                          "Délai communiqué par l'équipe Virtual Visa."),
    "visa_litige":          ("dossier Litige Virtual Visa",                          "Délai communiqué par l'équipe Virtual Visa."),
    "visa_remboursement":   ("dossier Remboursement Virtual Visa",                  "Délai communiqué par l'équipe Virtual Visa."),
}

def decision(intent, answers, obstacles, profile):
    # ── Relance / suivi ticket existant ──
    if "ticket_existant" in obstacles and intent in RELANCE_INFO:
        label, delai = RELANCE_INFO[intent]
        return "ok", f"Relance — {label}", (
            f"Le {label} a déjà été créé. Pour faire une relance :\n"
            "1. Retrouver le ticket/dossier existant dans le système.\n"
            "2. Ajouter un commentaire de relance avec la date du jour et la demande du client.\n"
            f"3. Informer le client que la demande est en cours de traitement. {delai}"
        )

    if "blocage_fraude" in obstacles and intent == "identification":
        return "warn", "Ticket déblocage compte", "Blocage Fraude détecté : ne pas rejeter la pièce et ne pas débloquer directement. Créer le ticket de déblocage compte."
    if "double_identite" in obstacles and intent not in ["identification", "agent_reject_id"]:
        return "warn", "Obstacle identité à traiter avant l'action", f"Objectif principal : {title_for(intent)}. Obstacle : double identité."

    if intent == "qualification":
        return "warn", "Cas non qualifié", "Préciser le type de compte, l'opération demandée, le statut Front visible et le blocage éventuel."

    if intent == "deblocage_compte":
        reason = answers.get("reason")
        if reason == "Fraude":
            return "warn", "Ticket déblocage compte", "Blocage Fraude : ne pas débloquer directement. Créer le ticket de déblocage compte."
        if reason == "Device restriction":
            return "warn", "Traiter selon Device restriction", "Ce blocage est lié à un nouvel appareil."
        if reason == "Autre / je ne sais pas":
            return "warn", "Qualifier le motif exact", "Le motif n'est pas identifiable."
        if answers.get("number") == "Non":
            return "stop", "Ne pas débloquer", "Le client doit appeler avec le numéro concerné."
        if answers.get("same_day") == "Oui":
            if answers.get("today_conditions") == "Non, une condition manque":
                return "stop", "Ne pas débloquer le même jour", "Le déblocage le jour même n'est autorisé que lundi-vendredi, ≥2h après blocage et avant 16h GMT."
            if answers.get("today_conditions") not in ["Oui, toutes les conditions sont réunies"]:
                return None
        if answers.get("same_day") == "Non, avant aujourd'hui":
            if answers.get("sat_sunday") == "Oui":
                return "stop", "Ne pas débloquer — rappeler lundi", "Samedi après 13h + rappel dimanche = rappeler lundi."
        if answers.get("ab") == "Oui":
            return "ok", "Déblocage autorisé", "Cliquer sur Déblocage après AB Verification réussie."
        if answers.get("ab") == "Non":
            return "stop", "Ne pas débloquer", "AB Verification échouée."
        return None

    if intent == "identification":
        if answers.get("caller_bottom") == "Non":
            return "stop", "Demander au titulaire de rappeler", "Si l'appelant n'est pas le propriétaire réel/nom du bas, ne pas rejeter la pièce. Inviter le titulaire du compte à nous contacter."
        if answers.get("admits") == "Oui" and answers.get("security") == "Oui":
            return "ok", "Rejeter la pièce puis reprendre l'objectif initial", "Rejeter la pièce, inviter à refaire l'identification avec sa propre pièce."
        if answers.get("admits") == "Non":
            return "warn", "Client nie l'utilisation d'une pièce tierce", "Ne pas rejeter la pièce sans aveu. Informer le TL et escalader."
        if answers.get("security") == "Non":
            return "stop", "Ne pas rejeter", "Questions sécurité échouées : inviter le titulaire du compte/la bonne personne à rappeler selon process."
        return None

    if intent == "canal":
        if answers.get("number_call") == "Non":
            return "stop", "Ne pas traiter", "Le client doit appeler avec le numéro concerné."
        num = answers.get("reab_number")
        case = answers.get("canal_case")
        if num == "Oui, il est correct" and case == "Pas d'image après paiement":
            return "ok", "Orienter Canal+", "Ne pas créer Bill Pay Problem. Orienter Canal+ au 1313."
        if case in ["Option ou offre choisie par erreur", "Double recharge", "Offre inférieure à celle souhaitée"]:
            return "ok", "Pas de remboursement / orientation", "Option non annulable ; double recharge = dates d'abonnement différentes ; offre inférieure non modifiable. Expliquer avec empathie selon la branche."
        if num == "Non, il est incorrect" or case == "Erreur sur le numéro" or case == "Offre supérieure à celle souhaitée":
            if answers.get("seven_days") == "Oui":
                return "ok", "Report Bill Payment Problem", "Créer Report Bill Payment Problem. Délai environ 1 semaine ouvrée."
            if answers.get("seven_days") == "Non":
                return "stop", "Ne pas remonter", "Délai Canal+ insuffisant : ne pas créer Bill Pay Problem. Inviter le client à contacter Canal+ au 1313 ou agence Canal+."
        return None

    if intent == "agent_reject_id":
        if answers.get("agent_id") == "Oui":
            if answers.get("reason"):
                return "ok", "Demande #ci-compliance", "Faire la demande dans #ci-compliance avec l'ID agent, le motif, tag @Daniel Keita et @Mariama. Délai 30 min."
            return None
        if answers.get("agent_id") == "Non":
            return "warn", "Compte non-agent — rediriger", "Ce compte n'est pas un compte agent. Utiliser le process adapté pour l'identification client."
        return None

    if intent == "refund":
        if answers.get("dispute") == "Oui":
            return "ok", "Report refunding dispute", "Créer un ticket via report refunding dispute, annoncer 48h jours ouvrés."
        if answers.get("multiple") == "Oui" and answers.get("dispute") is not None:
            return "ok", "Procéder aux remboursements", "BO : procéder aux refunds demandés."
        if answers.get("multiple") == "Non" and answers.get("dispute") == "Non":
            return "warn", "Qualifier le type de remboursement", "Le client demande un remboursement unique. Préciser la nature de la transaction : B2W, B2P, ou erreur de virement."
        return None

    if intent == "move_balance":
        if answers.get("app_active") == "Oui":
            return "stop", "Ne pas faire move balance", "Move balance vise un client sans app active sur smartphone. Un client qui utilise encore l'application Wave ne peut pas bénéficier de ce process."
        if answers.get("security4") == "Oui" and answers.get("total") == "Oui":
            return "ok", "Move balance autorisé", "Faire le move balance total du coffre vers le compte principal."
        if answers.get("security4") == "Non":
            return "stop", "Ne pas faire move balance", "4 bonnes réponses sécurité obligatoires."
        if answers.get("security4") == "Oui" and answers.get("total") == "Non":
            return "warn", "Move balance total obligatoire", "Le montant partiel n'est pas autorisé. Le move balance doit être effectué sur le montant total du coffre."
        return None

    if intent == "b2w":
        e = answers.get("error")
        if e == "Oui, raison bancaire claire":
            return "ok", "Orienter vers la banque", "Raison bancaire identifiée : rediriger le client vers sa banque ou son gestionnaire bancaire. Wave n'a pas d'action possible."
        if e == "Non, raison pas claire":
            return "ok", "Report B2W Problem", "Faire Report B2W Problem. Délai max 72h."
        if e == "Après changement téléphone / device linking":
            return "warn", "Transfert BO device linking", "FO : identifier, noter TR: device linking B2W, transférer BO."
        if e == "Cancelled and Refunded":
            return "ok", "B2W annulé et remboursé automatiquement", "B2W Cancelled and Refunded : le remboursement a été initié automatiquement. Confirmer au client le délai de 48h."
        return None

    if intent in SIMPLE_DECISIONS:
        title, act = SIMPLE_DECISIONS[intent]
        return "ok", title, act

    return "warn", "Process détecté mais règle détaillée à compléter", "Ajouter la branche exécutable dans Administration."

def next_questions(intent, answers, obstacles):
    qs = QUESTIONS.get(intent, [])
    if intent == "deblocage_compte":
        out = []
        for item in qs:
            k = item["key"]
            if k == "today_conditions" and answers.get("same_day") != "Oui": continue
            if k == "sat_sunday" and answers.get("same_day") != "Non, avant aujourd'hui": continue
            if k == "ab":
                d = decision(intent, answers, obstacles, "Back Office")
                if d and d[0] in ["stop", "warn"]: continue
                if not (answers.get("same_day") in ["Oui", "Non, avant aujourd'hui"]): continue
                if answers.get("same_day") == "Oui" and answers.get("today_conditions") != "Oui, toutes les conditions sont réunies": continue
                if answers.get("same_day") == "Non, avant aujourd'hui" and answers.get("sat_sunday") not in ["Non", None]: continue
            out.append(item)
        return out
    if intent == "canal":
        out = []
        for item in qs:
            k = item["key"]
            if k == "seven_days":
                case = answers.get("canal_case")
                num = answers.get("reab_number")
                if not (num == "Non, il est incorrect" or case in ["Erreur sur le numéro", "Offre supérieure à celle souhaitée"]):
                    continue
            out.append(item)
        return out
    return qs

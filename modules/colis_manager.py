"""
Module Colis — Fofana Voyage Colis Manager
Logique métier : dépôt, recherche, mise à jour, OTP, statistiques (via Supabase)
"""

from datetime import datetime, timedelta
from database.db_manager import rpc
from modules.auth_manager import auth
from utils.qr_generator import generer_numero_colis, generer_qr_colis, generer_otp


class ColisManager:
    """Toutes les opérations métier sur les colis."""

    # ─────────────────────────────────────────────────────────────────
    # CLIENTS
    # ─────────────────────────────────────────────────────────────────

    def trouver_ou_creer_client(self, telephone: str, nom: str,
                                 prenom: str, ville: str = "",
                                 cni: str = "") -> tuple[int, bool]:
        """Recherche un client par téléphone, le crée sinon. Retourne (client_id, créé)."""
        resultat = rpc("trouver_ou_creer_client", {
            "p_telephone": telephone.strip(),
            "p_nom": nom,
            "p_prenom": prenom,
            "p_ville": ville,
            "p_cni": cni,
        })
        return resultat["client_id"], resultat["cree"]

    def rechercher_client(self, terme: str) -> list[dict]:
        """Recherche un client par téléphone ou nom."""
        return rpc("rechercher_client", {"p_terme": terme})

    # ─────────────────────────────────────────────────────────────────
    # AGENCES
    # ─────────────────────────────────────────────────────────────────

    def liste_agences(self) -> list[dict]:
        """Retourne toutes les agences actives."""
        from database.db_manager import select
        return select("agences", filters={"est_active": "eq.1"}, order="ville.asc")

    # ─────────────────────────────────────────────────────────────────
    # ENREGISTREMENT D'UN COLIS
    # ─────────────────────────────────────────────────────────────────

    def enregistrer_colis(self, data: dict) -> tuple[bool, str, dict]:
        """
        Enregistre un nouveau colis.
        Retourne (succès, message, colis_dict)
        """
        champs_requis = [
            "expediteur_tel", "expediteur_nom",
            "destinataire_tel", "destinataire_nom",
            "agence_depart_id", "agence_arrivee_id",
            "description", "frais_envoi"
        ]
        for champ in champs_requis:
            if not data.get(champ) and data.get(champ) != 0:
                return False, f"Champ requis manquant : {champ}", {}

        try:
            # 1. Récupérer/créer expéditeur et destinataire
            exp_id, _ = self.trouver_ou_creer_client(
                data["expediteur_tel"], data["expediteur_nom"],
                data.get("expediteur_prenom", ""), data.get("expediteur_ville", ""),
                data.get("expediteur_cni", ""),
            )
            dest_id, _ = self.trouver_ou_creer_client(
                data["destinataire_tel"], data["destinataire_nom"],
                data.get("destinataire_prenom", ""), data.get("destinataire_ville", ""),
                data.get("destinataire_cni", ""),
            )

            # 2. Récupérer le code de l'agence de départ (pour générer le numéro)
            from database.db_manager import select
            agences_dep = select("agences", filters={"id": f"eq.{data['agence_depart_id']}"})
            if not agences_dep:
                return False, "Agence de départ introuvable.", {}
            code_agence = agences_dep[0]["code"]

            # 3. Générer le numéro unique + QR code
            numero = generer_numero_colis(code_agence)
            try:
                qr_path = generer_qr_colis(numero)
            except Exception:
                qr_path = ""

            frais_envoi = float(data.get("frais_envoi", 0))
            frais_total = frais_envoi

            # 4. Enregistrement complet côté serveur (colis + mouvement, en une fois)
            resultat = rpc("enregistrer_colis", {
                "p_numero": numero,
                "p_qr_code_data": numero,
                "p_expediteur_id": exp_id,
                "p_destinataire_id": dest_id,
                "p_agence_depart_id": data["agence_depart_id"],
                "p_agence_arrivee_id": data["agence_arrivee_id"],
                "p_agent_depot_id": auth.user_id,
                "p_description": data["description"],
                "p_poids_kg": float(data.get("poids_kg", 0) or 0),
                "p_valeur_declaree": float(data.get("valeur_declaree", 0) or 0),
                "p_nombre_pieces": int(data.get("nombre_pieces", 1) or 1),
                "p_fragile": 1 if data.get("fragile") else 0,
                "p_confidentiel": 1 if data.get("confidentiel") else 0,
                "p_frais_envoi": frais_envoi,
                "p_frais_total": frais_total,
                "p_paye": 1 if data.get("paye") else 0,
                "p_notes": data.get("notes", ""),
            })

            if not resultat.get("succes"):
                return False, resultat.get("message", "Erreur inconnue."), {}

            row = resultat["colis"]
            colis_complet = {
                **row,
                "qr_code_path":   qr_path,
                "agence_depart":  row.get("agence_depart_txt", ""),
                "agence_arrivee": row.get("agence_arrivee_txt", ""),
                "expediteur": {
                    "nom":       row.get("exp_nom"),
                    "telephone": row.get("exp_tel"),
                    "ville":     row.get("exp_ville"),
                },
                "destinataire": {
                    "nom":       row.get("dest_nom"),
                    "telephone": row.get("dest_tel"),
                    "ville":     row.get("dest_ville"),
                },
                "agent_nom": row.get("agent_nom"),
            }

            return True, f"Colis {numero} enregistré avec succès !", colis_complet

        except Exception as e:
            return False, f"Erreur lors de l'enregistrement : {e}", {}

    # ─────────────────────────────────────────────────────────────────
    # RECHERCHE ET CONSULTATION
    # ─────────────────────────────────────────────────────────────────

    def rechercher_colis(self, terme: str = "", statut: str = "",
                          agence_id: int = None,
                          date_debut: str = "", date_fin: str = "",
                          limite: int = 50) -> list[dict]:
        """Recherche multicritères des colis."""
        return rpc("rechercher_colis", {
            "p_terme": terme,
            "p_statut": statut,
            "p_agence_id": agence_id,
            "p_date_debut": date_debut,
            "p_date_fin": date_fin,
            "p_limite": limite,
        }) or []

    def get_colis_par_numero(self, numero: str) -> dict | None:
        """Récupère un colis complet par son numéro."""
        resultats = self.rechercher_colis(terme=numero, limite=1)
        if resultats and resultats[0]["numero"] == numero:
            return resultats[0]
        return None

    def historique_mouvements(self, colis_id: int) -> list[dict]:
        """Retourne l'historique des mouvements d'un colis."""
        return rpc("historique_mouvements", {"p_colis_id": colis_id}) or []

    # ─────────────────────────────────────────────────────────────────
    # MISE À JOUR DE STATUT
    # ─────────────────────────────────────────────────────────────────

    def changer_statut(self, colis_id: int, nouveau_statut: str,
                        agence_id: int = None,
                        description: str = "") -> tuple[bool, str]:
        """Change le statut d'un colis et enregistre le mouvement."""
        try:
            resultat = rpc("changer_statut_colis", {
                "p_colis_id": colis_id,
                "p_nouveau_statut": nouveau_statut,
                "p_agent_id": auth.user_id,
                "p_agence_id": agence_id or auth.agence_id,
                "p_description": description,
            })
            return resultat.get("succes", False), resultat.get("message", "Erreur inconnue.")
        except Exception as e:
            return False, f"Erreur : {e}"

    # ─────────────────────────────────────────────────────────────────
    # OTP — RETRAIT SÉCURISÉ
    # ─────────────────────────────────────────────────────────────────

    def generer_otp_retrait(self, colis_id: int) -> tuple[bool, str, str]:
        """Génère un OTP de retrait pour un colis. Retourne (succès, message, otp_code)."""
        try:
            otp = generer_otp(6)
            exp = (datetime.now() + timedelta(minutes=15)).isoformat()

            resultat = rpc("generer_otp_retrait", {
                "p_colis_id": colis_id,
                "p_otp": otp,
                "p_expiration": exp,
            })
            if not resultat.get("succes"):
                return False, resultat.get("message", "Erreur inconnue."), ""
            return True, resultat.get("message", "OTP généré."), otp
        except Exception as e:
            return False, f"Erreur : {e}", ""

    def valider_otp(self, colis_id: int, otp_saisi: str) -> tuple[bool, str]:
        """Valide l'OTP saisi par le destinataire."""
        try:
            resultat = rpc("valider_otp", {
                "p_colis_id": colis_id,
                "p_otp_saisi": otp_saisi,
            })
            return resultat.get("succes", False), resultat.get("message", "Erreur inconnue.")
        except Exception as e:
            return False, f"Erreur : {e}"

    def confirmer_retrait(self, colis_id: int,
                           otp_saisi: str) -> tuple[bool, str]:
        """Confirme le retrait complet d'un colis (validation OTP + changement statut)."""
        ok, msg = self.valider_otp(colis_id, otp_saisi)
        if not ok:
            return False, msg

        ok2, msg2 = self.changer_statut(
            colis_id, "RETIRE",
            description="Colis retiré avec validation OTP"
        )
        return ok2, msg2

    # ─────────────────────────────────────────────────────────────────
    # STATISTIQUES
    # ─────────────────────────────────────────────────────────────────

    def statistiques(self, agence_id: int = None,
                      date_debut: str = "", date_fin: str = "") -> dict:
        """Calcule les statistiques générales."""
        try:
            resultat = rpc("statistiques_colis", {
                "p_agence_id": agence_id,
                "p_date_debut": date_debut,
                "p_date_fin": date_fin,
            })

            stats = {
                "total_colis":     resultat.get("total_colis", 0),
                "ca_total":        resultat.get("ca_total", 0),
                "alertes_actives": resultat.get("alertes_actives", 0),
                "non_retires_7j":  resultat.get("non_retires_7j", 0),
            }
            for ligne in resultat.get("par_statut", []) or []:
                stats[f"nb_{ligne['statut'].lower()}"] = ligne["n"]
                stats[f"ca_{ligne['statut'].lower()}"] = ligne["ca"]
            return stats
        except Exception:
            return {
                "total_colis": 0, "ca_total": 0,
                "alertes_actives": 0, "non_retires_7j": 0,
            }


# Instance globale
colis_manager = ColisManager()
                         

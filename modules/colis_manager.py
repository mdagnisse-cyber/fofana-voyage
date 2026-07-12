"""
Module Colis — Fofana Voyage Colis Manager
Logique métier : dépôt, recherche, mise à jour, OTP, statistiques
"""

import os
import random
import string
from datetime import datetime, timedelta
from database.db_manager import get_connection
from modules.auth_manager import auth
from utils.qr_generator import generer_numero_colis, generer_qr_colis, generer_otp

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ColisManager:
    """Toutes les opérations métier sur les colis."""

    # ─────────────────────────────────────────────────────────────────
    # CLIENTS
    # ─────────────────────────────────────────────────────────────────

    def trouver_ou_creer_client(self, telephone: str, nom: str,
                                 prenom: str, ville: str = "",
                                 cni: str = "") -> tuple[int, bool]:
        """
        Recherche un client par téléphone.
        S'il n'existe pas, le crée.
        Retourne (client_id, créé: bool)
        """
        conn = get_connection()
        cur  = conn.cursor()
        try:
            cur.execute(
                "SELECT id FROM clients WHERE telephone = ?",
                (telephone.strip(),)
            )
            row = cur.fetchone()
            if row:
                # Mettre à jour les infos si nécessaire
                cur.execute("""
                    UPDATE clients
                    SET nom=?, prenom=?, ville=?,
                        cni=COALESCE(NULLIF(?, ''), cni),
                        updated_at=datetime('now','localtime')
                    WHERE id=?
                """, (nom.upper(), prenom.capitalize(), ville, cni, row["id"]))
                conn.commit()
                return row["id"], False
            else:
                cur.execute("""
                    INSERT INTO clients (nom, prenom, telephone, ville, cni)
                    VALUES (?, ?, ?, ?, ?)
                """, (nom.upper(), prenom.capitalize(),
                      telephone.strip(), ville, cni))
                conn.commit()
                return cur.lastrowid, True
        finally:
            conn.close()

    def rechercher_client(self, terme: str) -> list[dict]:
        """Recherche un client par téléphone ou nom."""
        conn = get_connection()
        cur  = conn.cursor()
        try:
            cur.execute("""
                SELECT * FROM clients
                WHERE telephone LIKE ?
                   OR nom LIKE ?
                   OR prenom LIKE ?
                ORDER BY nom, prenom
                LIMIT 20
            """, (f"%{terme}%", f"%{terme.upper()}%", f"%{terme}%"))
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    # ─────────────────────────────────────────────────────────────────
    # AGENCES
    # ─────────────────────────────────────────────────────────────────

    def liste_agences(self) -> list[dict]:
        """Retourne toutes les agences actives."""
        conn = get_connection()
        cur  = conn.cursor()
        try:
            cur.execute("""
                SELECT * FROM agences WHERE est_active = 1
                ORDER BY ville
            """)
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    # ─────────────────────────────────────────────────────────────────
    # ENREGISTREMENT D'UN COLIS
    # ─────────────────────────────────────────────────────────────────

    def enregistrer_colis(self, data: dict) -> tuple[bool, str, dict]:
        """
        Enregistre un nouveau colis.
        data doit contenir :
          - expediteur_tel, expediteur_nom, expediteur_prenom, expediteur_ville
          - destinataire_tel, destinataire_nom, destinataire_prenom, destinataire_ville
          - agence_depart_id, agence_arrivee_id
          - description, poids_kg, valeur_declaree, nombre_pieces
          - fragile (bool), frais_envoi
          - notes (optionnel)
        Retourne (succès, message, colis_dict)
        """
        # Validation
        champs_requis = [
            "expediteur_tel", "expediteur_nom",
            "destinataire_tel", "destinataire_nom",
            "agence_depart_id", "agence_arrivee_id",
            "description", "frais_envoi"
        ]
        for champ in champs_requis:
            if not data.get(champ) and data.get(champ) != 0:
                return False, f"Champ requis manquant : {champ}", {}

        conn = get_connection()
        cur  = conn.cursor()
        try:
            # 1. Récupérer/créer expéditeur
            exp_id, _ = self.trouver_ou_creer_client(
                data["expediteur_tel"],
                data["expediteur_nom"],
                data.get("expediteur_prenom", ""),
                data.get("expediteur_ville", ""),
                data.get("expediteur_cni", ""),
            )

            # 2. Récupérer/créer destinataire
            dest_id, _ = self.trouver_ou_creer_client(
                data["destinataire_tel"],
                data["destinataire_nom"],
                data.get("destinataire_prenom", ""),
                data.get("destinataire_ville", ""),
                data.get("destinataire_cni", ""),
            )

            # 3. Récupérer le code de l'agence de départ
            cur.execute(
                "SELECT code, nom, ville FROM agences WHERE id = ?",
                (data["agence_depart_id"],)
            )
            agence_dep = cur.fetchone()
            if not agence_dep:
                return False, "Agence de départ introuvable.", {}

            cur.execute(
                "SELECT code, nom, ville FROM agences WHERE id = ?",
                (data["agence_arrivee_id"],)
            )
            agence_arr = cur.fetchone()
            if not agence_arr:
                return False, "Agence d'arrivée introuvable.", {}

            # 4. Générer le numéro unique
            numero = generer_numero_colis(agence_dep["code"])

            # 5. Générer le QR code
            try:
                qr_path = generer_qr_colis(numero)
            except Exception:
                qr_path = ""

            # 6. Calculer frais total
            frais_envoi  = float(data.get("frais_envoi", 0))
            frais_total  = frais_envoi

            # 7. Insérer le colis
            cur.execute("""
                INSERT INTO colis (
                    numero, qr_code_data,
                    expediteur_id, destinataire_id,
                    agence_depart_id, agence_arrivee_id,
                    agent_depot_id,
                    description, poids_kg, valeur_declaree,
                    nombre_pieces, fragile, confidentiel,
                    frais_envoi, frais_total, paye,
                    statut, notes,
                    date_depot
                ) VALUES (
                    ?, ?,
                    ?, ?,
                    ?, ?,
                    ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    'DEPOSE', ?,
                    datetime('now','localtime')
                )
            """, (
                numero, numero,
                exp_id, dest_id,
                data["agence_depart_id"], data["agence_arrivee_id"],
                auth.user_id,
                data["description"],
                float(data.get("poids_kg", 0) or 0),
                float(data.get("valeur_declaree", 0) or 0),
                int(data.get("nombre_pieces", 1) or 1),
                1 if data.get("fragile") else 0,
                1 if data.get("confidentiel") else 0,
                frais_envoi, frais_total,
                1 if data.get("paye") else 0,
                data.get("notes", ""),
            ))
            colis_id = cur.lastrowid

            # 8. Enregistrer le mouvement initial
            cur.execute("""
                INSERT INTO mouvements
                    (colis_id, agent_id, agence_id, statut_avant, statut_apres, description)
                VALUES (?, ?, ?, NULL, 'DEPOSE', ?)
            """, (colis_id, auth.user_id, data["agence_depart_id"],
                  f"Colis déposé à l'agence {agence_dep['nom']}"))

            conn.commit()

            # 9. Construire le dict complet pour le bordereau
            cur.execute("""
                SELECT
                    c.*,
                    ce.nom || ' ' || ce.prenom AS exp_nom,
                    ce.telephone AS exp_tel, ce.ville AS exp_ville,
                    cd.nom || ' ' || cd.prenom AS dest_nom,
                    cd.telephone AS dest_tel, cd.ville AS dest_ville,
                    u.nom || ' ' || u.prenom AS agent_nom
                FROM colis c
                JOIN clients ce ON c.expediteur_id = ce.id
                JOIN clients cd ON c.destinataire_id = cd.id
                JOIN utilisateurs u ON c.agent_depot_id = u.id
                WHERE c.id = ?
            """, (colis_id,))
            row = dict(cur.fetchone())

            colis_complet = {
                **row,
                "qr_code_path":   qr_path,
                "agence_depart":  f"{agence_dep['nom']} ({agence_dep['ville']})",
                "agence_arrivee": f"{agence_arr['nom']} ({agence_arr['ville']})",
                "expediteur": {
                    "nom":       row["exp_nom"],
                    "telephone": row["exp_tel"],
                    "ville":     row["exp_ville"],
                },
                "destinataire": {
                    "nom":       row["dest_nom"],
                    "telephone": row["dest_tel"],
                    "ville":     row["dest_ville"],
                },
                "agent_nom": row["agent_nom"],
            }

            return True, f"Colis {numero} enregistré avec succès !", colis_complet

        except Exception as e:
            conn.rollback()
            return False, f"Erreur lors de l'enregistrement : {e}", {}
        finally:
            conn.close()

    # ─────────────────────────────────────────────────────────────────
    # RECHERCHE ET CONSULTATION
    # ─────────────────────────────────────────────────────────────────

    def rechercher_colis(self, terme: str = "", statut: str = "",
                          agence_id: int = None,
                          date_debut: str = "", date_fin: str = "",
                          limite: int = 50) -> list[dict]:
        """
        Recherche multicritères des colis.
        terme : numéro de colis, nom ou téléphone de client
        """
        conn = get_connection()
        cur  = conn.cursor()
        try:
            conditions = []
            params     = []

            if terme:
                conditions.append("""(
                    c.numero LIKE ?
                    OR ce.nom LIKE ? OR ce.telephone LIKE ?
                    OR cd.nom LIKE ? OR cd.telephone LIKE ?
                )""")
                t = f"%{terme}%"
                params.extend([t, t.upper(), t, t.upper(), t])

            if statut:
                conditions.append("c.statut = ?")
                params.append(statut)

            if agence_id:
                conditions.append(
                    "(c.agence_depart_id = ? OR c.agence_arrivee_id = ?)"
                )
                params.extend([agence_id, agence_id])

            if date_debut:
                conditions.append("date(c.date_depot) >= date(?)")
                params.append(date_debut)

            if date_fin:
                conditions.append("date(c.date_depot) <= date(?)")
                params.append(date_fin)

            where = "WHERE " + " AND ".join(conditions) if conditions else ""

            cur.execute(f"""
                SELECT
                    c.*,
                    ce.nom || ' ' || ce.prenom AS expediteur_nom,
                    ce.telephone               AS expediteur_tel,
                    cd.nom || ' ' || cd.prenom AS destinataire_nom,
                    cd.telephone               AS destinataire_tel,
                    ad.nom || ' (' || ad.ville || ')' AS agence_depart_nom,
                    aa.nom || ' (' || aa.ville || ')' AS agence_arrivee_nom,
                    u.nom  || ' ' || u.prenom  AS agent_depot_nom
                FROM colis c
                JOIN clients      ce ON c.expediteur_id      = ce.id
                JOIN clients      cd ON c.destinataire_id    = cd.id
                JOIN agences      ad ON c.agence_depart_id   = ad.id
                JOIN agences      aa ON c.agence_arrivee_id  = aa.id
                LEFT JOIN utilisateurs u ON c.agent_depot_id = u.id
                {where}
                ORDER BY c.created_at DESC
                LIMIT ?
            """, (*params, limite))

            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def get_colis_par_numero(self, numero: str) -> dict | None:
        """Récupère un colis complet par son numéro."""
        resultats = self.rechercher_colis(terme=numero, limite=1)
        if resultats and resultats[0]["numero"] == numero:
            return resultats[0]
        return None

    def historique_mouvements(self, colis_id: int) -> list[dict]:
        """Retourne l'historique des mouvements d'un colis."""
        conn = get_connection()
        cur  = conn.cursor()
        try:
            cur.execute("""
                SELECT m.*, u.nom || ' ' || u.prenom AS agent_nom,
                       a.nom AS agence_nom
                FROM mouvements m
                LEFT JOIN utilisateurs u ON m.agent_id  = u.id
                LEFT JOIN agences      a ON m.agence_id = a.id
                WHERE m.colis_id = ?
                ORDER BY m.created_at ASC
            """, (colis_id,))
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    # ─────────────────────────────────────────────────────────────────
    # MISE À JOUR DE STATUT
    # ─────────────────────────────────────────────────────────────────

    def changer_statut(self, colis_id: int, nouveau_statut: str,
                        agence_id: int = None,
                        description: str = "") -> tuple[bool, str]:
        """Change le statut d'un colis et enregistre le mouvement."""
        conn = get_connection()
        cur  = conn.cursor()
        try:
            cur.execute("SELECT statut FROM colis WHERE id = ?", (colis_id,))
            row = cur.fetchone()
            if not row:
                return False, "Colis introuvable."

            ancien_statut = row["statut"]

            # Champs à mettre à jour selon le nouveau statut
            extras = ""
            extra_params = []

            if nouveau_statut == "ARRIVE":
                extras = ", date_arrivee_reelle = datetime('now','localtime')"
            elif nouveau_statut == "RETIRE":
                extras = ", date_retrait = datetime('now','localtime'), agent_retrait_id = ?"
                extra_params.append(auth.user_id)

            cur.execute(f"""
                UPDATE colis
                SET statut = ?,
                    updated_at = datetime('now','localtime')
                    {extras}
                WHERE id = ?
            """, (nouveau_statut, *extra_params, colis_id))

            # Mouvement
            cur.execute("""
                INSERT INTO mouvements
                    (colis_id, agent_id, agence_id, statut_avant, statut_apres, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (colis_id, auth.user_id,
                  agence_id or auth.agence_id,
                  ancien_statut, nouveau_statut,
                  description or f"Statut changé : {ancien_statut} → {nouveau_statut}"))

            conn.commit()
            return True, "Statut mis à jour avec succès."
        except Exception as e:
            conn.rollback()
            return False, f"Erreur : {e}"
        finally:
            conn.close()

    # ─────────────────────────────────────────────────────────────────
    # OTP — RETRAIT SÉCURISÉ
    # ─────────────────────────────────────────────────────────────────

    def generer_otp_retrait(self, colis_id: int) -> tuple[bool, str, str]:
        """
        Génère un OTP de retrait pour un colis.
        Retourne (succès, message, otp_code)
        """
        conn = get_connection()
        cur  = conn.cursor()
        try:
            cur.execute("SELECT * FROM colis WHERE id = ?", (colis_id,))
            colis = cur.fetchone()
            if not colis:
                return False, "Colis introuvable.", ""

            if colis["statut"] not in ("ARRIVE", "DEPOSE"):
                return False, f"Ce colis a le statut '{colis['statut']}', retrait impossible.", ""

            otp  = generer_otp(6)
            exp  = (datetime.now() + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")

            cur.execute("""
                UPDATE colis
                SET otp_code = ?, otp_expiration = ?, otp_utilise = 0,
                    updated_at = datetime('now','localtime')
                WHERE id = ?
            """, (otp, exp, colis_id))
            conn.commit()
            return True, "OTP généré avec succès.", otp
        except Exception as e:
            return False, f"Erreur : {e}", ""
        finally:
            conn.close()

    def valider_otp(self, colis_id: int, otp_saisi: str) -> tuple[bool, str]:
        """Valide l'OTP saisi par le destinataire."""
        conn = get_connection()
        cur  = conn.cursor()
        try:
            cur.execute(
                "SELECT otp_code, otp_expiration, otp_utilise FROM colis WHERE id = ?",
                (colis_id,)
            )
            row = cur.fetchone()
            if not row:
                return False, "Colis introuvable."

            if row["otp_utilise"]:
                return False, "Ce code OTP a déjà été utilisé."

            if not row["otp_code"]:
                return False, "Aucun OTP généré pour ce colis."

            # Vérifier expiration
            exp = datetime.strptime(row["otp_expiration"], "%Y-%m-%d %H:%M:%S")
            if datetime.now() > exp:
                return False, "Code OTP expiré. Veuillez en générer un nouveau."

            if str(row["otp_code"]).strip() != str(otp_saisi).strip():
                return False, "Code OTP incorrect."

            # Marquer comme utilisé
            cur.execute("""
                UPDATE colis SET otp_utilise = 1,
                    updated_at = datetime('now','localtime')
                WHERE id = ?
            """, (colis_id,))
            conn.commit()
            return True, "OTP valide ✓"
        except Exception as e:
            return False, f"Erreur : {e}"
        finally:
            conn.close()

    def confirmer_retrait(self, colis_id: int,
                           otp_saisi: str) -> tuple[bool, str]:
        """
        Confirme le retrait complet d'un colis (validation OTP + changement statut).
        """
        # Valider OTP
        ok, msg = self.valider_otp(colis_id, otp_saisi)
        if not ok:
            return False, msg

        # Changer statut
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
        conn = get_connection()
        cur  = conn.cursor()
        try:
            filtre_agence = ""
            params_ag     = []
            if agence_id:
                filtre_agence = "AND (agence_depart_id = ? OR agence_arrivee_id = ?)"
                params_ag     = [agence_id, agence_id]

            filtre_date = ""
            params_date = []
            if date_debut:
                filtre_date += " AND date(date_depot) >= date(?)"
                params_date.append(date_debut)
            if date_fin:
                filtre_date += " AND date(date_depot) <= date(?)"
                params_date.append(date_fin)

            where = f"WHERE 1=1 {filtre_agence} {filtre_date}"
            p     = params_ag + params_date

            stats = {}

            # Total par statut
            cur.execute(f"""
                SELECT statut, COUNT(*) as n, SUM(frais_total) as ca
                FROM colis {where}
                GROUP BY statut
            """, p)
            for row in cur.fetchall():
                stats[f"nb_{row['statut'].lower()}"]  = row["n"]
                stats[f"ca_{row['statut'].lower()}"]  = row["ca"] or 0

            # Total général
            cur.execute(f"SELECT COUNT(*), SUM(frais_total) FROM colis {where}", p)
            row = cur.fetchone()
            stats["total_colis"] = row[0] or 0
            stats["ca_total"]    = row[1] or 0

            # Alertes actives
            cur.execute("SELECT COUNT(*) FROM alertes WHERE resolue = 0")
            stats["alertes_actives"] = cur.fetchone()[0]

            # Colis non retirés depuis plus de 7 jours
            cur.execute(f"""
                SELECT COUNT(*) FROM colis
                WHERE statut = 'ARRIVE'
                AND julianday('now','localtime') - julianday(date_arrivee_reelle) > 7
                {filtre_agence}
            """, params_ag)
            stats["non_retires_7j"] = cur.fetchone()[0]

            return stats
        finally:
            conn.close()


# Instance globale
colis_manager = ColisManager()

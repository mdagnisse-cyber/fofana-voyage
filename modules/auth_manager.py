"""
Module Authentification — Fofana Voyage Colis Manager
Gestion des connexions, sessions et permissions
"""

import hashlib
import socket
from datetime import datetime, timedelta
from database.db_manager import get_connection, hash_password


class AuthManager:
    """Gère l'authentification et les sessions utilisateurs."""

    def __init__(self):
        self._utilisateur_courant = None  # dict utilisateur connecté
        self._heure_connexion     = None

    # ------------------------------------------------------------------ #
    # Propriétés de session                                                #
    # ------------------------------------------------------------------ #

    @property
    def est_connecte(self) -> bool:
        return self._utilisateur_courant is not None

    @property
    def utilisateur(self) -> dict | None:
        return self._utilisateur_courant

    @property
    def role(self) -> str | None:
        if self._utilisateur_courant:
            return self._utilisateur_courant["role"]
        return None

    @property
    def agence_id(self) -> int | None:
        if self._utilisateur_courant:
            return self._utilisateur_courant["agence_id"]
        return None

    @property
    def user_id(self) -> int | None:
        if self._utilisateur_courant:
            return self._utilisateur_courant["id"]
        return None

    def est_admin(self) -> bool:
        return self.role == "ADMIN"

    def est_manager(self) -> bool:
        return self.role in ("ADMIN", "MANAGER")

    # ------------------------------------------------------------------ #
    # Connexion                                                            #
    # ------------------------------------------------------------------ #

    def connexion(self, username: str, password: str) -> tuple[bool, str]:
        """
        Tente une connexion.
        Retourne (succès: bool, message: str)
        """
        if not username or not password:
            return False, "Veuillez saisir votre identifiant et mot de passe."

        conn = get_connection()
        cur  = conn.cursor()

        try:
            cur.execute("""
                SELECT u.*, a.nom as agence_nom, a.ville as agence_ville
                FROM utilisateurs u
                LEFT JOIN agences a ON u.agence_id = a.id
                WHERE u.username = ?
            """, (username.strip().lower(),))

            user = cur.fetchone()

            # Utilisateur inexistant
            if user is None:
                return False, "Identifiant ou mot de passe incorrect."

            # Compte désactivé
            if not user["est_actif"]:
                return False, "Ce compte est désactivé. Contactez l'administrateur."

            # Trop de tentatives
            if user["tentatives_login"] >= 5:
                return False, (
                    "Compte bloqué après trop de tentatives.\n"
                    "Contactez l'administrateur."
                )

            # Vérification mot de passe
            if user["password_hash"] != hash_password(password):
                # Incrémenter les tentatives
                cur.execute("""
                    UPDATE utilisateurs
                    SET tentatives_login = tentatives_login + 1,
                        updated_at = datetime('now','localtime')
                    WHERE id = ?
                """, (user["id"],))
                conn.commit()

                restantes = 5 - (user["tentatives_login"] + 1)
                if restantes <= 0:
                    return False, "Compte bloqué. Contactez l'administrateur."
                return False, (
                    f"Mot de passe incorrect. "
                    f"{restantes} tentative(s) restante(s)."
                )

            # ✅ Connexion réussie
            cur.execute("""
                UPDATE utilisateurs
                SET tentatives_login    = 0,
                    derniere_connexion  = datetime('now','localtime'),
                    updated_at          = datetime('now','localtime')
                WHERE id = ?
            """, (user["id"],))

            # Enregistrer dans le journal de sessions
            ip = self._get_ip()
            cur.execute("""
                INSERT INTO sessions (utilisateur_id, action, details, ip_machine)
                VALUES (?, 'LOGIN', ?, ?)
            """, (user["id"],
                  f"Connexion de {user['prenom']} {user['nom']}",
                  ip))

            conn.commit()

            # Stocker en session
            self._utilisateur_courant = dict(user)
            self._heure_connexion     = datetime.now()

            nom_complet = f"{user['prenom']} {user['nom']}"
            return True, f"Bienvenue, {nom_complet} !"

        except Exception as e:
            return False, f"Erreur système : {e}"

        finally:
            conn.close()

    # ------------------------------------------------------------------ #
    # Déconnexion                                                          #
    # ------------------------------------------------------------------ #

    def deconnexion(self):
        """Déconnecte l'utilisateur courant."""
        if self._utilisateur_courant:
            try:
                conn = get_connection()
                cur  = conn.cursor()
                cur.execute("""
                    INSERT INTO sessions (utilisateur_id, action, details)
                    VALUES (?, 'LOGOUT', ?)
                """, (self._utilisateur_courant["id"],
                      f"Déconnexion après "
                      f"{self._duree_session()} de session"))
                conn.commit()
                conn.close()
            except Exception:
                pass

        self._utilisateur_courant = None
        self._heure_connexion     = None

    # ------------------------------------------------------------------ #
    # Changement de mot de passe                                           #
    # ------------------------------------------------------------------ #

    def changer_mot_de_passe(
        self, user_id: int, ancien_mdp: str, nouveau_mdp: str
    ) -> tuple[bool, str]:
        """Change le mot de passe d'un utilisateur."""
        if len(nouveau_mdp) < 6:
            return False, "Le nouveau mot de passe doit faire au moins 6 caractères."

        conn = get_connection()
        cur  = conn.cursor()
        try:
            cur.execute(
                "SELECT password_hash FROM utilisateurs WHERE id = ?",
                (user_id,)
            )
            row = cur.fetchone()
            if not row:
                return False, "Utilisateur introuvable."

            if row["password_hash"] != hash_password(ancien_mdp):
                return False, "Ancien mot de passe incorrect."

            cur.execute("""
                UPDATE utilisateurs
                SET password_hash = ?, updated_at = datetime('now','localtime')
                WHERE id = ?
            """, (hash_password(nouveau_mdp), user_id))
            conn.commit()
            return True, "Mot de passe modifié avec succès."

        except Exception as e:
            return False, f"Erreur : {e}"
        finally:
            conn.close()

    # ------------------------------------------------------------------ #
    # Gestion des utilisateurs (admin)                                     #
    # ------------------------------------------------------------------ #

    def creer_utilisateur(self, data: dict) -> tuple[bool, str]:
        """Crée un nouvel utilisateur (admin seulement)."""
        if not self.est_admin():
            return False, "Permission refusée."

        champs_requis = ["nom", "prenom", "username", "password", "role", "agence_id"]
        for champ in champs_requis:
            if not data.get(champ):
                return False, f"Champ requis manquant : {champ}"

        conn = get_connection()
        cur  = conn.cursor()
        try:
            # Vérifier unicité username
            cur.execute(
                "SELECT id FROM utilisateurs WHERE username = ?",
                (data["username"].strip().lower(),)
            )
            if cur.fetchone():
                return False, f"L'identifiant '{data['username']}' existe déjà."

            cur.execute("""
                INSERT INTO utilisateurs
                    (nom, prenom, username, password_hash, role,
                     agence_id, telephone, email)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["nom"].strip().upper(),
                data["prenom"].strip().capitalize(),
                data["username"].strip().lower(),
                hash_password(data["password"]),
                data["role"],
                data["agence_id"],
                data.get("telephone", ""),
                data.get("email", ""),
            ))
            conn.commit()

            # Journal
            self._log_action(
                "MODIF",
                f"Création utilisateur : {data['username']} ({data['role']})"
            )
            return True, f"Utilisateur '{data['username']}' créé avec succès."

        except Exception as e:
            return False, f"Erreur : {e}"
        finally:
            conn.close()

    def liste_utilisateurs(self) -> list[dict]:
        """Retourne la liste de tous les utilisateurs."""
        conn = get_connection()
        cur  = conn.cursor()
        try:
            cur.execute("""
                SELECT u.*, a.nom as agence_nom
                FROM utilisateurs u
                LEFT JOIN agences a ON u.agence_id = a.id
                ORDER BY u.nom, u.prenom
            """)
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def activer_desactiver_utilisateur(
        self, user_id: int, activer: bool
    ) -> tuple[bool, str]:
        """Active ou désactive un compte utilisateur."""
        if not self.est_admin():
            return False, "Permission refusée."

        conn = get_connection()
        cur  = conn.cursor()
        try:
            cur.execute("""
                UPDATE utilisateurs
                SET est_actif = ?, tentatives_login = 0,
                    updated_at = datetime('now','localtime')
                WHERE id = ?
            """, (1 if activer else 0, user_id))
            conn.commit()
            action = "activé" if activer else "désactivé"
            return True, f"Compte {action} avec succès."
        except Exception as e:
            return False, f"Erreur : {e}"
        finally:
            conn.close()

    def reinitialiser_mot_de_passe(
        self, user_id: int, nouveau_mdp: str
    ) -> tuple[bool, str]:
        """Réinitialise le mot de passe (admin uniquement)."""
        if not self.est_admin():
            return False, "Permission refusée."

        conn = get_connection()
        cur  = conn.cursor()
        try:
            cur.execute("""
                UPDATE utilisateurs
                SET password_hash = ?, tentatives_login = 0,
                    updated_at = datetime('now','localtime')
                WHERE id = ?
            """, (hash_password(nouveau_mdp), user_id))
            conn.commit()
            return True, "Mot de passe réinitialisé avec succès."
        except Exception as e:
            return False, f"Erreur : {e}"
        finally:
            conn.close()

    # ------------------------------------------------------------------ #
    # Utilitaires                                                          #
    # ------------------------------------------------------------------ #

    def _log_action(self, action: str, details: str = ""):
        """Enregistre une action dans le journal de sessions."""
        if not self._utilisateur_courant:
            return
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("""
                INSERT INTO sessions (utilisateur_id, action, details, ip_machine)
                VALUES (?, ?, ?, ?)
            """, (self._utilisateur_courant["id"], action, details, self._get_ip()))
            conn.commit()
            conn.close()
        except Exception:
            pass

    def _get_ip(self) -> str:
        """Récupère l'IP de la machine."""
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

    def _duree_session(self) -> str:
        """Retourne la durée de la session en format lisible."""
        if not self._heure_connexion:
            return "durée inconnue"
        delta = datetime.now() - self._heure_connexion
        minutes = int(delta.total_seconds() // 60)
        if minutes < 60:
            return f"{minutes} minute(s)"
        heures = minutes // 60
        return f"{heures}h{minutes % 60:02d}"


# Instance globale partagée dans toute l'application
auth = AuthManager()

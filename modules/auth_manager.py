"""
Module Authentification — Fofana Voyage Colis Manager
Gestion des connexions, sessions et permissions (via Supabase)
"""

from datetime import datetime
from database.db_manager import rpc, insert, hash_password


class AuthManager:
    """Gère l'authentification et les sessions utilisateurs."""

    def __init__(self):
        self._utilisateur_courant = None  # dict utilisateur connecté
        self._heure_connexion     = None

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

    def connexion(self, username: str, password: str) -> tuple[bool, str]:
        """Tente une connexion via la fonction sécurisée Supabase."""
        if not username or not password:
            return False, "Veuillez saisir votre identifiant et mot de passe."

        try:
            resultat = rpc("tenter_connexion", {
                "p_username": username.strip().lower(),
                "p_password_hash": hash_password(password),
            })

            if not resultat.get("succes"):
                return False, resultat.get("message", "Erreur de connexion.")

            self._utilisateur_courant = resultat["utilisateur"]
            self._heure_connexion     = datetime.now()
            return True, resultat["message"]

        except Exception as e:
            return False, f"Erreur de connexion au serveur : {e}"

    def deconnexion(self):
        """Déconnecte l'utilisateur courant."""
        if self._utilisateur_courant:
            try:
                insert("sessions", {
                    "utilisateur_id": self._utilisateur_courant["id"],
                    "action": "LOGOUT",
                    "details": f"Déconnexion après {self._duree_session()} de session",
                })
            except Exception:
                pass

        self._utilisateur_courant = None
        self._heure_connexion     = None

    def changer_mot_de_passe(
        self, user_id: int, ancien_mdp: str, nouveau_mdp: str
    ) -> tuple[bool, str]:
        """Change le mot de passe d'un utilisateur."""
        if len(nouveau_mdp) < 6:
            return False, "Le nouveau mot de passe doit faire au moins 6 caractères."

        try:
            resultat = rpc("changer_mot_de_passe", {
                "p_user_id": user_id,
                "p_ancien_hash": hash_password(ancien_mdp),
                "p_nouveau_hash": hash_password(nouveau_mdp),
            })
            return resultat.get("succes", False), resultat.get("message", "Erreur inconnue.")
        except Exception as e:
            return False, f"Erreur : {e}"

    def creer_utilisateur(self, data: dict) -> tuple[bool, str]:
        """Crée un nouvel utilisateur (admin seulement)."""
        if not self.est_admin():
            return False, "Permission refusée."

        champs_requis = ["nom", "prenom", "username", "password", "role", "agence_id"]
        for champ in champs_requis:
            if not data.get(champ):
                return False, f"Champ requis manquant : {champ}"

        try:
            resultat = rpc("creer_utilisateur", {
                "p_nom": data["nom"].strip().upper(),
                "p_prenom": data["prenom"].strip().capitalize(),
                "p_username": data["username"].strip().lower(),
                "p_password_hash": hash_password(data["password"]),
                "p_role": data["role"],
                "p_agence_id": data["agence_id"],
                "p_telephone": data.get("telephone", ""),
                "p_email": data.get("email", ""),
            })

            if resultat.get("succes"):
                self._log_action(
                    "MODIF",
                    f"Création utilisateur : {data['username']} ({data['role']})"
                )
            return resultat.get("succes", False), resultat.get("message", "Erreur inconnue.")

        except Exception as e:
            return False, f"Erreur : {e}"

    def liste_utilisateurs(self) -> list[dict]:
        """Retourne la liste de tous les utilisateurs."""
        try:
            return rpc("liste_utilisateurs")
        except Exception:
            return []

    def activer_desactiver_utilisateur(
        self, user_id: int, activer: bool
    ) -> tuple[bool, str]:
        """Active ou désactive un compte utilisateur."""
        if not self.est_admin():
            return False, "Permission refusée."

        try:
            resultat = rpc("activer_desactiver_utilisateur", {
                "p_user_id": user_id,
                "p_activer": activer,
            })
            return resultat.get("succes", False), resultat.get("message", "Erreur inconnue.")
        except Exception as e:
            return False, f"Erreur : {e}"

    def reinitialiser_mot_de_passe(
        self, user_id: int, nouveau_mdp: str
    ) -> tuple[bool, str]:
        """Réinitialise le mot de passe (admin uniquement)."""
        if not self.est_admin():
            return False, "Permission refusée."

        try:
            resultat = rpc("reinitialiser_mot_de_passe", {
                "p_user_id": user_id,
                "p_nouveau_hash": hash_password(nouveau_mdp),
            })
            return resultat.get("succes", False), resultat.get("message", "Erreur inconnue.")
        except Exception as e:
            return False, f"Erreur : {e}"

    def _log_action(self, action: str, details: str = ""):
        """Enregistre une action dans le journal de sessions."""
        if not self._utilisateur_courant:
            return
        try:
            insert("sessions", {
                "utilisateur_id": self._utilisateur_courant["id"],
                "action": action,
                "details": details,
            })
        except Exception:
            pass

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
            

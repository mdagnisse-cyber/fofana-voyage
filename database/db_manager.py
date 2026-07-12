"""
Base de données SQLite — Fofana Voyage Colis Manager
Création de toutes les tables, index et données initiales
"""

import sqlite3
import hashlib
import os
import sys
from datetime import datetime

# Chemin vers la base de données (dans le dossier de l'application)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "database", "fofana_voyage.db")


def get_connection():
    """Retourne une connexion SQLite avec row_factory activé."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # accès par nom de colonne
    conn.execute("PRAGMA foreign_keys = ON") # contraintes FK actives
    conn.execute("PRAGMA journal_mode = WAL")# meilleures performances
    return conn


def hash_password(password: str) -> str:
    """Hash SHA-256 du mot de passe."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_database():
    """Crée toutes les tables si elles n'existent pas encore."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    cur  = conn.cursor()

    # ------------------------------------------------------------------ #
    # TABLE : agences                                                      #
    # ------------------------------------------------------------------ #
    cur.execute("""
        CREATE TABLE IF NOT EXISTS agences (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            code        TEXT    NOT NULL UNIQUE,   -- ex: COT-01
            nom         TEXT    NOT NULL,
            ville       TEXT    NOT NULL,
            adresse     TEXT,
            telephone   TEXT,
            email       TEXT,
            est_active  INTEGER NOT NULL DEFAULT 1,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
            updated_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)

    # ------------------------------------------------------------------ #
    # TABLE : utilisateurs (agents, managers, admins)                     #
    # ------------------------------------------------------------------ #
    cur.execute("""
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            nom             TEXT    NOT NULL,
            prenom          TEXT    NOT NULL,
            username        TEXT    NOT NULL UNIQUE,
            password_hash   TEXT    NOT NULL,
            role            TEXT    NOT NULL DEFAULT 'AGENT',
            agence_id       INTEGER REFERENCES agences(id),
            telephone       TEXT,
            email           TEXT,
            est_actif       INTEGER NOT NULL DEFAULT 1,
            tentatives_login INTEGER NOT NULL DEFAULT 0,
            derniere_connexion TEXT,
            created_at      TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
            updated_at      TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)

    # ------------------------------------------------------------------ #
    # TABLE : clients (expéditeurs & destinataires)                       #
    # ------------------------------------------------------------------ #
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nom         TEXT    NOT NULL,
            prenom      TEXT    NOT NULL,
            telephone   TEXT    NOT NULL,
            telephone2  TEXT,
            cni         TEXT,                   -- N° pièce d'identité
            adresse     TEXT,
            ville       TEXT,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
            updated_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)

    # ------------------------------------------------------------------ #
    # TABLE : colis                                                        #
    # ------------------------------------------------------------------ #
    cur.execute("""
        CREATE TABLE IF NOT EXISTS colis (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            numero              TEXT    NOT NULL UNIQUE,   -- ex: FV-COT-20250517-0001
            qr_code_data        TEXT,

            -- Parties
            expediteur_id       INTEGER NOT NULL REFERENCES clients(id),
            destinataire_id     INTEGER NOT NULL REFERENCES clients(id),

            -- Agences
            agence_depart_id    INTEGER NOT NULL REFERENCES agences(id),
            agence_arrivee_id   INTEGER NOT NULL REFERENCES agences(id),

            -- Agents
            agent_depot_id      INTEGER NOT NULL REFERENCES utilisateurs(id),
            agent_retrait_id    INTEGER REFERENCES utilisateurs(id),

            -- Description
            description         TEXT    NOT NULL,
            poids_kg            REAL,
            valeur_declaree     REAL    DEFAULT 0,
            nombre_pieces       INTEGER DEFAULT 1,
            fragile             INTEGER DEFAULT 0,
            confidentiel        INTEGER DEFAULT 0,

            -- Tarification
            frais_envoi         REAL    NOT NULL DEFAULT 0,
            frais_stockage      REAL    DEFAULT 0,
            frais_total         REAL    DEFAULT 0,
            paye                INTEGER DEFAULT 0,

            -- Statut
            statut              TEXT    NOT NULL DEFAULT 'DEPOSE',
            -- DEPOSE | EN_TRANSIT | ARRIVE | RETIRE | PERDU | LITIGE

            -- Dates clés
            date_depot          TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
            date_arrivee_prevue TEXT,
            date_arrivee_reelle TEXT,
            date_retrait        TEXT,
            date_alerte         TEXT,

            -- Retrait
            otp_code            TEXT,
            otp_expiration      TEXT,
            otp_utilise         INTEGER DEFAULT 0,
            signature_retrait   TEXT,             -- chemin image signature

            -- Notes
            notes               TEXT,
            created_at          TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
            updated_at          TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)

    # ------------------------------------------------------------------ #
    # TABLE : mouvements (historique complet de chaque colis)             #
    # ------------------------------------------------------------------ #
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mouvements (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            colis_id        INTEGER NOT NULL REFERENCES colis(id),
            agent_id        INTEGER REFERENCES utilisateurs(id),
            agence_id       INTEGER REFERENCES agences(id),
            statut_avant    TEXT,
            statut_apres    TEXT    NOT NULL,
            description     TEXT,
            created_at      TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)

    # ------------------------------------------------------------------ #
    # TABLE : alertes                                                      #
    # ------------------------------------------------------------------ #
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alertes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            colis_id    INTEGER NOT NULL REFERENCES colis(id),
            type_alerte TEXT    NOT NULL,
            -- NON_RETIRE | LITIGE | ANOMALIE | PERTE
            message     TEXT    NOT NULL,
            resolue     INTEGER DEFAULT 0,
            resolue_par INTEGER REFERENCES utilisateurs(id),
            resolue_at  TEXT,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)

    # ------------------------------------------------------------------ #
    # TABLE : sessions (audit des connexions)                              #
    # ------------------------------------------------------------------ #
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            utilisateur_id  INTEGER NOT NULL REFERENCES utilisateurs(id),
            action          TEXT    NOT NULL,
            -- LOGIN | LOGOUT | DEPOT | RETRAIT | MODIF | RAPPORT
            details         TEXT,
            ip_machine      TEXT,
            created_at      TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)

    # ------------------------------------------------------------------ #
    # TABLE : parametres (configuration dynamique)                         #
    # ------------------------------------------------------------------ #
    cur.execute("""
        CREATE TABLE IF NOT EXISTS parametres (
            cle     TEXT PRIMARY KEY,
            valeur  TEXT NOT NULL,
            description TEXT
        )
    """)

    # ------------------------------------------------------------------ #
    # INDEX pour accélérer les recherches                                  #
    # ------------------------------------------------------------------ #
    index_queries = [
        "CREATE INDEX IF NOT EXISTS idx_colis_numero       ON colis(numero)",
        "CREATE INDEX IF NOT EXISTS idx_colis_statut       ON colis(statut)",
        "CREATE INDEX IF NOT EXISTS idx_colis_expediteur   ON colis(expediteur_id)",
        "CREATE INDEX IF NOT EXISTS idx_colis_destinataire ON colis(destinataire_id)",
        "CREATE INDEX IF NOT EXISTS idx_colis_agence_arr   ON colis(agence_arrivee_id)",
        "CREATE INDEX IF NOT EXISTS idx_mouvements_colis   ON mouvements(colis_id)",
        "CREATE INDEX IF NOT EXISTS idx_alertes_colis      ON alertes(colis_id)",
        "CREATE INDEX IF NOT EXISTS idx_sessions_user      ON sessions(utilisateur_id)",
        "CREATE INDEX IF NOT EXISTS idx_clients_tel        ON clients(telephone)",
    ]
    for q in index_queries:
        cur.execute(q)

    conn.commit()
    conn.close()
    print(f"[DB] Base de données initialisée : {DB_PATH}")


def seed_initial_data():
    """Insère les données initiales (agence et admin par défaut)."""
    conn = get_connection()
    cur  = conn.cursor()

    # Agence principale
    cur.execute("SELECT COUNT(*) FROM agences")
    if cur.fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO agences (code, nom, ville, adresse, telephone)
            VALUES (?, ?, ?, ?, ?)
        """, ("FV-COT", "Agence de l'Étoile Rouge", "Cotonou",
              "Étoile Rouge, Cotonou, Bénin", "+229 97000000"))

        cur.execute("""
            INSERT INTO agences (code, nom, ville, adresse, telephone)
            VALUES (?, ?, ?, ?, ?)
        """, ("FV-PTO", "Agence Porto-Novo", "Porto-Novo",
              "Centre-ville, Porto-Novo, Bénin", "+229 97000001"))

        cur.execute("""
            INSERT INTO agences (code, nom, ville, adresse, telephone)
            VALUES (?, ?, ?, ?, ?)
        """, ("FV-PAR", "Agence Parakou", "Parakou",
              "Marché central, Parakou, Bénin", "+229 97000002"))

        print("[DB] Agences créées.")

    # Utilisateur administrateur par défaut
    cur.execute("SELECT COUNT(*) FROM utilisateurs")
    if cur.fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO utilisateurs
                (nom, prenom, username, password_hash, role, agence_id, telephone)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("FOFANA", "Admin", "admin",
              hash_password("admin123"),
              "ADMIN", 1, "+229 97000000"))

        cur.execute("""
            INSERT INTO utilisateurs
                (nom, prenom, username, password_hash, role, agence_id, telephone)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("KOUASSI", "Jean", "agent1",
              hash_password("agent123"),
              "AGENT", 1, "+229 97000010"))

        print("[DB] Utilisateurs par défaut créés.")
        print("     → Admin : admin / admin123")
        print("     → Agent : agent1 / agent123")

    # Paramètres par défaut
    cur.execute("SELECT COUNT(*) FROM parametres")
    if cur.fetchone()[0] == 0:
        params = [
            ("otp_validity_minutes",    "15",    "Durée validité OTP en minutes"),
            ("alert_days_no_pickup",    "7",     "Jours avant alerte non-retrait"),
            ("frais_base_kg",           "500",   "Frais de base par kg (FCFA)"),
            ("frais_stockage_jour",     "200",   "Frais stockage par jour (FCFA)"),
            ("sms_enabled",             "0",     "Activer les SMS (0/1)"),
            ("nom_entreprise",          "Fofana Voyage", "Nom de l'entreprise"),
            ("devise",                  "FCFA",  "Devise utilisée"),
        ]
        cur.executemany(
            "INSERT INTO parametres (cle, valeur, description) VALUES (?, ?, ?)",
            params
        )
        print("[DB] Paramètres par défaut insérés.")

    conn.commit()
    conn.close()


def reset_database():
    """Supprime et recrée la base (usage développement uniquement)."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("[DB] Base supprimée.")
    init_database()
    seed_initial_data()
    print("[DB] Base réinitialisée avec succès.")


if __name__ == "__main__":
    if "--reset" in sys.argv:
        reset_database()
    else:
        init_database()
        seed_initial_data()

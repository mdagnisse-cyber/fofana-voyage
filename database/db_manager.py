"""
Client Supabase — Fofana Voyage Colis Manager
================================================
Remplace l'ancienne base SQLite locale par une base de données
centrale en ligne (Supabase / PostgreSQL), partagée en temps réel
par toutes les agences.

Toutes les fonctions ici communiquent avec Supabase via son API
REST sécurisée (HTTPS), en utilisant uniquement la clé publique
"anon" — la vraie protection vient des règles Row Level Security
et des fonctions sécurisées définies côté serveur.
"""

import hashlib
import requests
from config.supabase_config import SUPABASE_URL, SUPABASE_KEY

_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

_TIMEOUT = 15  # secondes


def hash_password(password: str) -> str:
    """Hash SHA-256 du mot de passe (identique à l'ancienne version)."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------- #
# Opérations génériques sur les tables (protégées par Row Level Security) #
# ---------------------------------------------------------------------- #

def select(table: str, filters: dict | None = None, select_cols: str = "*",
           order: str | None = None, limit: int | None = None) -> list[dict]:
    """
    Lit des lignes d'une table.
    filters: dict de conditions au format PostgREST, ex: {"id": "eq.5"}
    """
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    params = {"select": select_cols}
    if filters:
        params.update(filters)
    if order:
        params["order"] = order
    if limit:
        params["limit"] = str(limit)
    r = requests.get(url, headers=_HEADERS, params=params, timeout=_TIMEOUT)
    r.raise_for_status()
    return r.json()


def insert(table: str, data: dict) -> list[dict]:
    """Insère une ligne et retourne la ligne créée."""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {**_HEADERS, "Prefer": "return=representation"}
    r = requests.post(url, headers=headers, json=data, timeout=_TIMEOUT)
    r.raise_for_status()
    return r.json()


def update(table: str, filters: dict, data: dict) -> list[dict]:
    """Met à jour les lignes correspondant aux filtres."""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {**_HEADERS, "Prefer": "return=representation"}
    r = requests.patch(url, headers=headers, params=filters, json=data, timeout=_TIMEOUT)
    r.raise_for_status()
    return r.json()


def delete(table: str, filters: dict) -> list[dict]:
    """Supprime les lignes correspondant aux filtres."""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    r = requests.delete(url, headers=_HEADERS, params=filters, timeout=_TIMEOUT)
    r.raise_for_status()
    return r.json()


def upsert(table: str, data: dict, on_conflict: str) -> list[dict]:
    """
    Insère une ligne, ou la met à jour si la clé (on_conflict) existe déjà.
    Ex: upsert("parametres", {"cle": "devise", "valeur": "FCFA"}, on_conflict="cle")
    """
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {**_HEADERS, "Prefer": "resolution=merge-duplicates,return=representation"}
    params = {"on_conflict": on_conflict}
    r = requests.post(url, headers=headers, params=params, json=data, timeout=_TIMEOUT)
    r.raise_for_status()
    return r.json()


def rpc(function_name: str, params: dict | None = None):
    """Appelle une fonction SQL sécurisée définie côté Supabase."""
    url = f"{SUPABASE_URL}/rest/v1/rpc/{function_name}"
    r = requests.post(url, headers=_HEADERS, json=params or {}, timeout=_TIMEOUT)
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------- #
# Compatibilité avec l'ancien code (main.py appelle ces deux fonctions   #
# au démarrage) — la base est maintenant déjà créée côté Supabase, donc  #
# on se contente de vérifier que la connexion internet/API fonctionne.  #
# ---------------------------------------------------------------------- #

def init_database():
    """Vérifie que Supabase est joignable (les tables existent déjà)."""
    try:
        select("parametres", limit=1)
        print("[DB] Connexion Supabase OK.")
    except Exception as e:
        print(f"[DB] ATTENTION : impossible de joindre Supabase ({e})")
        print("     Vérifiez la connexion internet et config/supabase_config.py")


def seed_initial_data():
    """Les données initiales sont déjà créées côté Supabase (SQL Editor)."""
    pass
    

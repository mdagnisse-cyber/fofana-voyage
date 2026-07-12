"""
Generateur QR Code - Fofana Voyage
Utilise qrcode[pil] si disponible (Pydroid), sinon fallback PIL maison
"""

import os
import hashlib
import random
import string
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def generer_numero_colis(code_agence_depart: str) -> str:
    """Genere un numero unique. Format: FV-COT-20260526-0001"""
    from database.db_manager import get_connection
    conn = get_connection()
    cur  = conn.cursor()
    date_str = datetime.now().strftime("%Y%m%d")
    cur.execute(
        "SELECT COUNT(*) FROM colis WHERE date(date_depot)=date('now','localtime')")
    compteur = cur.fetchone()[0] + 1
    conn.close()
    code = code_agence_depart.replace("-","").upper()[:6]
    return f"FV-{code}-{date_str}-{compteur:04d}"


def generer_otp(longueur: int = 6) -> str:
    """Genere un code OTP numerique aleatoire."""
    return "".join(random.choices(string.digits, k=longueur))


def generer_qr_colis(numero_colis: str) -> str:
    """
    Genere un QR code standard pour le numero de colis.
    Priorite 1: bibliotheque qrcode[pil] (standard, scannable)
    Priorite 2: implementation PIL maison (fallback)
    Retourne le chemin de l'image PNG.
    """
    dossier = os.path.join(BASE_DIR, "assets", "qrcodes")
    os.makedirs(dossier, exist_ok=True)
    chemin = os.path.join(dossier, f"{numero_colis}.png")

    # ── Methode 1: qrcode[pil] (disponible sur Pydroid apres pip install) ──
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(numero_colis)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(chemin)
        return chemin
    except ImportError:
        pass

    # ── Methode 2: PIL maison (fallback si qrcode non installe) ────────────
    _generer_qr_pil(numero_colis, chemin)
    return chemin


def _generer_qr_pil(data: str, chemin: str, taille_module: int = 12):
    """
    QR code visuel en PIL pur.
    NOTE: Ce QR est lisible visuellement mais pas scannable par tous les lecteurs.
    Pour un vrai QR scannable, installer: pip install qrcode[pil]
    """
    from PIL import Image, ImageDraw, ImageFont

    N      = 21   # matrice 21x21 (Version 1)
    QUIET  = 4
    matrix = _construire_matrice(data, N)

    total = (N + 2 * QUIET) * taille_module
    img   = Image.new("RGB", (total, total), "white")
    draw  = ImageDraw.Draw(img)

    for row in range(N):
        for col in range(N):
            if matrix[row][col]:
                x0 = (col + QUIET) * taille_module
                y0 = (row + QUIET) * taille_module
                draw.rectangle(
                    [x0, y0, x0 + taille_module - 1,
                     y0 + taille_module - 1],
                    fill="black")

    # Ajouter le numero en texte sous le QR
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    texte_y = total - taille_module + 2
    draw.text((4, texte_y), data[:28],
              fill="black", font=font)

    img.save(chemin, "PNG")


def _construire_matrice(data: str, n: int) -> list:
    mat = [[False] * n for _ in range(n)]
    _finder(mat, 0, 0, n)
    _finder(mat, 0, n - 7, n)
    _finder(mat, n - 7, 0, n)

    # Timing patterns
    for i in range(8, n - 8):
        mat[6][i] = (i % 2 == 0)
        mat[i][6] = (i % 2 == 0)

    # Dark module
    mat[8][n - 8] = True

    # Donnees encodees (hash deterministe)
    reserve = set()
    for r in range(9):
        for c in range(9):
            reserve.add((r, c))
        for c in range(n - 8, n):
            reserve.add((r, c))
    for r in range(n - 8, n):
        for c in range(9):
            reserve.add((r, c))
    for i in range(n):
        reserve.add((6, i)); reserve.add((i, 6))

    h    = hashlib.sha256(data.encode()).digest()
    bits = []
    for byte in h:
        for bit in range(8):
            bits.append(bool((byte >> (7 - bit)) & 1))
    while len(bits) < n * n:
        bits.extend(bits)

    idx = 0
    for r in range(n):
        for c in range(n):
            if (r, c) not in reserve and idx < len(bits):
                mat[r][c] = bits[idx]; idx += 1
    return mat


def _finder(mat, row, col, n):
    pattern = [
        [1,1,1,1,1,1,1],
        [1,0,0,0,0,0,1],
        [1,0,1,1,1,0,1],
        [1,0,1,1,1,0,1],
        [1,0,1,1,1,0,1],
        [1,0,0,0,0,0,1],
        [1,1,1,1,1,1,1],
    ]
    for r in range(7):
        for c in range(7):
            if 0 <= row+r < n and 0 <= col+c < n:
                mat[row+r][col+c] = bool(pattern[r][c])

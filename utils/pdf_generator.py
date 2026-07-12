"""
Générateur de Bordereaux PDF — Fofana Voyage Colis Manager
Utilise ReportLab pour produire les bordereaux d'envoi et reçus de retrait
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, HRFlowable
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_DIR  = os.path.join(BASE_DIR, "assets", "bordereaux")

ROUGE  = colors.HexColor("#C0392B")
BLEU_F = colors.HexColor("#2C3E50")
GRIS_C = colors.HexColor("#F5F5F5")
GRIS_B = colors.HexColor("#BDC3C7")
BLANC  = colors.white
NOIR   = colors.black
VERT   = colors.HexColor("#27AE60")

PAGE_W, PAGE_H = A4
MARGE = 2 * cm
ZONE_W = PAGE_W - 2 * MARGE   # 481.9 pts


def _sty(name, **kw):
    defaults = dict(fontSize=9, fontName="Helvetica", textColor=NOIR, leading=13)
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)


def _tbl_style(*rules):
    return TableStyle(list(rules))


# ─── Styles communs ──────────────────────────────────────────────────────────
S_TITRE    = _sty("titre",   fontSize=17, fontName="Helvetica-Bold", textColor=BLANC, alignment=TA_CENTER, leading=22)
S_SOUS     = _sty("sous",    fontSize=9,  fontName="Helvetica",      textColor=BLANC, alignment=TA_CENTER)
S_SECTION  = _sty("sect",    fontSize=9,  fontName="Helvetica-Bold", textColor=BLEU_F)
S_NORMAL   = _sty("normal")
S_BOLD     = _sty("bold",    fontName="Helvetica-Bold")
S_CENTRE   = _sty("centre",  alignment=TA_CENTER)
S_NUMERO   = _sty("numero",  fontSize=15, fontName="Helvetica-Bold", textColor=ROUGE, alignment=TA_CENTER)
S_FOOTER   = _sty("footer",  fontSize=7,  textColor=colors.grey, alignment=TA_CENTER)
S_HEADER_B = _sty("hb",      fontName="Helvetica-Bold", textColor=BLANC)
S_WHITE_SM = _sty("wsm",     textColor=BLANC)


def _header_block(titre: str, agence: str, tel: str) -> list:
    """En-tête rouge de l'agence."""
    w = ZONE_W
    t1 = Table([[Paragraph(titre, S_TITRE)]], colWidths=[w])
    t1.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), ROUGE),
        ("TOPPADDING",    (0,0),(-1,-1), 14),
        ("BOTTOMPADDING", (0,0),(-1,-1), 8),
    ]))
    t2 = Table([[
        Paragraph(agence, S_WHITE_SM),
        Paragraph(tel, _sty("ts", textColor=BLANC, alignment=TA_RIGHT)),
    ]], colWidths=[w*0.6, w*0.4])
    t2.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), BLEU_F),
        ("TOPPADDING",    (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
        ("LEFTPADDING",   (0,0),(-1,-1), 12),
        ("RIGHTPADDING",  (0,0),(-1,-1), 12),
    ]))
    return [t1, t2, Spacer(1, 0.4*cm)]


def _personne_table(titre: str, nom: str, tel: str,
                    ville: str, couleur) -> Table:
    """Bloc info personne (expéditeur ou destinataire)."""
    col = ZONE_W / 2 - 0.3*cm
    body_txt = (
        f"<b>Nom :</b> {nom or '—'}<br/>"
        f"<b>Tél :</b> {tel or '—'}<br/>"
        f"<b>Ville :</b> {ville or '—'}"
    )
    t = Table([
        [Paragraph(f"  {titre}", S_HEADER_B)],
        [Paragraph(body_txt, S_NORMAL)],
    ], colWidths=[col])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(0,0), couleur),
        ("TOPPADDING",    (0,0),(0,0), 7),
        ("BOTTOMPADDING", (0,0),(0,0), 7),
        ("TOPPADDING",    (0,1),(0,1), 8),
        ("BOTTOMPADDING", (0,1),(0,1), 10),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
        ("RIGHTPADDING",  (0,0),(-1,-1), 6),
        ("BOX",           (0,0),(-1,-1), 0.5, GRIS_B),
    ]))
    return t


def generer_bordereau_depot(colis_data: dict) -> str:
    """Génère le bordereau de dépôt. Retourne le chemin du PDF."""
    os.makedirs(PDF_DIR, exist_ok=True)
    numero = colis_data.get("numero", "INCONNU")
    chemin = os.path.join(PDF_DIR, f"bordereau_{numero}.pdf")
    w      = ZONE_W

    doc = SimpleDocTemplate(
        chemin, pagesize=A4,
        leftMargin=MARGE, rightMargin=MARGE,
        topMargin=MARGE, bottomMargin=MARGE
    )
    elts = []

    # ── En-tête ──────────────────────────────────────────────────────
    elts += _header_block(
        "📦  FOFANA VOYAGE — BORDEREAU D'EXPÉDITION",
        "Agence de l'Étoile Rouge — Cotonou, Bénin",
        "Tél : +229 97 00 00 00"
    )

    # ── Numéro + Date ─────────────────────────────────────────────────
    date_dep = colis_data.get("date_depot",
               datetime.now().strftime("%d/%m/%Y %H:%M"))
    num_tbl = Table([[
        Paragraph(f"N°  {numero}", S_NUMERO),
        Paragraph(f"Date : {date_dep}",
                  _sty("dt", alignment=TA_RIGHT, textColor=BLEU_F)),
    ]], colWidths=[w*0.65, w*0.35])
    num_tbl.setStyle(TableStyle([
        ("BOX",           (0,0),(-1,-1), 2, ROUGE),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
        ("LEFTPADDING",   (0,0),(-1,-1), 14),
        ("RIGHTPADDING",  (0,0),(-1,-1), 14),
    ]))
    elts += [num_tbl, Spacer(1, 0.4*cm)]

    # ── Expéditeur / Destinataire ──────────────────────────────────────
    exp  = colis_data.get("expediteur", {})
    dest = colis_data.get("destinataire", {})
    t_exp  = _personne_table("EXPÉDITEUR",   exp.get("nom","—"),
                              exp.get("telephone","—"),  exp.get("ville","—"),  BLEU_F)
    t_dest = _personne_table("DESTINATAIRE", dest.get("nom","—"),
                              dest.get("telephone","—"), dest.get("ville","—"), ROUGE)

    col = w/2 - 0.3*cm
    sep = w - 2*col
    personnes = Table([[t_exp, "", t_dest]], colWidths=[col, sep, col])
    elts += [personnes, Spacer(1, 0.4*cm)]

    # ── Détails colis ──────────────────────────────────────────────────
    elts.append(Paragraph("DÉTAILS DU COLIS", S_SECTION))
    elts.append(Spacer(1, 0.15*cm))

    c0, c1, c2, c3 = w*0.22, w*0.28, w*0.22, w*0.28
    det = [
        ["Description",     str(colis_data.get("description", "—")),
         "Poids (kg)",      str(colis_data.get("poids_kg", "—"))],
        ["Valeur déclarée",
         f"{float(colis_data.get('valeur_declaree', 0)):,.0f} FCFA",
         "Nb. pièces",      str(colis_data.get("nombre_pieces", 1))],
        ["Agence départ",   str(colis_data.get("agence_depart", "—")),
         "Agence arrivée",  str(colis_data.get("agence_arrivee", "—"))],
        ["Fragile",         "⚠ OUI" if colis_data.get("fragile") else "Non",
         "Frais envoi",
         f"{float(colis_data.get('frais_envoi', 0)):,.0f} FCFA"],
    ]
    det_tbl = Table(det, colWidths=[c0, c1, c2, c3])
    det_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(0,-1), GRIS_C),
        ("BACKGROUND",    (2,0),(2,-1), GRIS_C),
        ("FONTNAME",      (0,0),(0,-1), "Helvetica-Bold"),
        ("FONTNAME",      (2,0),(2,-1), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(-1,-1), 9),
        ("TOPPADDING",    (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("GRID",          (0,0),(-1,-1), 0.3, GRIS_B),
        ("TEXTCOLOR",     (0,0),(0,-1), BLEU_F),
        ("TEXTCOLOR",     (2,0),(2,-1), BLEU_F),
    ]))
    elts += [det_tbl, Spacer(1, 0.5*cm)]

    # ── Signatures ─────────────────────────────────────────────────────
    col_s = w/3 - 4
    agent = str(colis_data.get("agent_nom", "—"))

    def sig_bloc(titre: str, contenu: str = "") -> Table:
        rows = [
            [Paragraph(titre, S_CENTRE)],
            [Spacer(1, 1.4*cm)],
        ]
        if contenu:
            rows.append([Paragraph(contenu, S_CENTRE)])
        rows.append([HRFlowable(width="75%", color=GRIS_B)])
        return Table(rows, colWidths=[col_s])

    sig_row = [sig_bloc("Signature Expéditeur"),
               "", sig_bloc("Cachet Agence"),
               "", sig_bloc("Agent", agent)]
    sep_s = (w - 3*col_s) / 2
    sig_tbl = Table([sig_row],
                    colWidths=[col_s, sep_s, col_s, sep_s, col_s])
    sig_tbl.setStyle(TableStyle([
        ("BOX",           (0,0),(0,0), 0.5, GRIS_B),
        ("BOX",           (2,0),(2,0), 0.5, GRIS_B),
        ("BOX",           (4,0),(4,0), 0.5, GRIS_B),
        ("TOPPADDING",    (0,0),(-1,-1), 8),
        ("BOTTOMPADDING", (0,0),(-1,-1), 8),
    ]))
    elts += [sig_tbl, Spacer(1, 0.3*cm)]

    # ── QR Code ────────────────────────────────────────────────────────
    qr_path = colis_data.get("qr_code_path", "")
    if qr_path and os.path.exists(qr_path):
        try:
            from reportlab.platypus import Image as RLImage
            qr_row = Table([[
                Paragraph("Scannez ce code pour suivre votre colis", S_CENTRE),
                RLImage(qr_path, width=2.3*cm, height=2.3*cm),
            ]], colWidths=[w - 2.5*cm, 2.5*cm])
            elts.append(qr_row)
        except Exception:
            pass

    # ── Pied de page ───────────────────────────────────────────────────
    elts += [
        Spacer(1, 0.2*cm),
        HRFlowable(width="100%", color=GRIS_B, thickness=0.5),
        Spacer(1, 0.15*cm),
        Paragraph(
            f"Fofana Voyage — Agence de l'Étoile Rouge — Cotonou, Bénin  |  "
            f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}  |  N° {numero}",
            S_FOOTER
        ),
    ]

    doc.build(elts)
    return chemin


def generer_recu_retrait(colis_data: dict) -> str:
    """Génère le reçu de retrait. Retourne le chemin du PDF."""
    os.makedirs(PDF_DIR, exist_ok=True)
    numero = colis_data.get("numero", "INCONNU")
    chemin = os.path.join(PDF_DIR, f"recu_retrait_{numero}.pdf")
    w      = ZONE_W

    doc = SimpleDocTemplate(
        chemin, pagesize=A4,
        leftMargin=MARGE, rightMargin=MARGE,
        topMargin=MARGE, bottomMargin=MARGE
    )
    elts = []

    # En-tête vert
    hdr = Table([[Paragraph(
        "FOFANA VOYAGE — REÇU DE RETRAIT",
        _sty("rh", fontSize=14, fontName="Helvetica-Bold",
             textColor=BLANC, alignment=TA_CENTER)
    )]], colWidths=[w])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), VERT),
        ("TOPPADDING",    (0,0),(-1,-1), 12),
        ("BOTTOMPADDING", (0,0),(-1,-1), 12),
    ]))
    elts += [hdr, Spacer(1, 0.5*cm)]
    elts.append(Paragraph(f"Colis N°  {numero}", S_NUMERO))
    elts.append(Spacer(1, 0.4*cm))

    # Tableau infos
    lignes = [
        ["Destinataire",   colis_data.get("destinataire_nom", "—")],
        ["Téléphone",      colis_data.get("destinataire_tel", "—")],
        ["Expéditeur",     colis_data.get("expediteur_nom",   "—")],
        ["Description",    colis_data.get("description",      "—")],
        ["Agence",         colis_data.get("agence_arrivee",   "—")],
        ["Agent",          colis_data.get("agent_retrait",    "—")],
        ["Date retrait",   colis_data.get("date_retrait",
                           datetime.now().strftime("%d/%m/%Y %H:%M"))],
    ]
    tbl = Table(lignes, colWidths=[w*0.35, w*0.65])
    tbl.setStyle(TableStyle([
        ("FONTNAME",      (0,0),(0,-1), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(-1,-1), 9),
        ("BACKGROUND",    (0,0),(0,-1), GRIS_C),
        ("TOPPADDING",    (0,0),(-1,-1), 7),
        ("BOTTOMPADDING", (0,0),(-1,-1), 7),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
        ("GRID",          (0,0),(-1,-1), 0.3, GRIS_B),
        ("TEXTCOLOR",     (0,0),(0,-1), BLEU_F),
    ]))
    elts += [tbl, Spacer(1, 0.7*cm)]

    # Signature
    elts += [
        Paragraph("Signature du destinataire :", S_BOLD),
        Spacer(1, 1.3*cm),
        HRFlowable(width="45%", color=NOIR),
        Spacer(1, 0.5*cm),
        Paragraph(
            f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            S_FOOTER
        ),
    ]

    doc.build(elts)
    return chemin

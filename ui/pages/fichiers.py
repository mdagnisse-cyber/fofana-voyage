"""
Page Fichiers Generes - visualisation PDF et QR codes sur Android
"""

import os
import sys

from kivy.uix.boxlayout  import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label      import Label
from kivy.uix.button     import Button
from kivy.uix.image      import Image as KivyImage
from kivy.graphics       import Color, Rectangle
from kivy.utils          import get_color_from_hex
from kivy.metrics        import dp
from kivy.uix.popup      import Popup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


def ouvrir_fichier(chemin: str) -> tuple[bool, str]:
    """Ouvre un fichier avec l'application par defaut du systeme."""
    try:
        # Android via intent
        try:
            from jnius import autoclass
            Intent   = autoclass('android.content.Intent')
            File     = autoclass('java.io.File')
            FileProvider = autoclass(
                'androidx.core.content.FileProvider')
            Uri      = autoclass('android.net.Uri')
            PythonActivity = autoclass(
                'org.kivy.android.PythonActivity')

            intent = Intent(Intent.ACTION_VIEW)
            f      = File(chemin)
            uri    = Uri.fromFile(f)

            if chemin.endswith('.pdf'):
                intent.setDataAndType(uri, 'application/pdf')
            elif chemin.endswith('.png'):
                intent.setDataAndType(uri, 'image/png')

            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            PythonActivity.mActivity.startActivity(intent)
            return True, "Fichier ouvert"
        except Exception:
            pass

        # PC Windows
        import subprocess, platform
        if platform.system() == 'Windows':
            os.startfile(chemin)
            return True, "Fichier ouvert"
        elif platform.system() == 'Darwin':
            subprocess.call(['open', chemin])
            return True, "Fichier ouvert"
        else:
            subprocess.call(['xdg-open', chemin])
            return True, "Fichier ouvert"

    except Exception as e:
        return False, str(e)


class FichiersPage(BoxLayout):
    """Page listant tous les PDF et QR codes generes."""

    def __init__(self, **kw):
        kw.setdefault('orientation', 'vertical')
        super().__init__(**kw)
        self._build()

    def _build(self):
        from ui.widgets import SectionHeader, BoutonPrimaire, Separateur

        # En-tete
        hdr = BoxLayout(size_hint_y=None, height=dp(44),
                        padding=[dp(10), dp(4)], spacing=dp(8))
        with hdr.canvas.before:
            Color(*get_color_from_hex("#2C3E50"))
            r = Rectangle(pos=hdr.pos, size=hdr.size)
        hdr.bind(pos=lambda w, v: setattr(r, 'pos', v),
                 size=lambda w, v: setattr(r, 'size', v))
        hdr.add_widget(Label(
            text="Fichiers generes (PDF et QR codes)",
            font_size=dp(13), bold=True,
            color=(1, 1, 1, 1), halign='left'))
        btn_ref = Button(text="Actualiser",
            font_size=dp(10),
            background_color=get_color_from_hex("#C0392B"),
            background_normal='', color=(1, 1, 1, 1),
            size_hint=(None, None), size=(dp(90), dp(34)))
        btn_ref.bind(on_press=lambda a: self._recharger())
        hdr.add_widget(btn_ref)
        self.add_widget(hdr)

        # Info chemin
        self.lbl_chemin = Label(
            text=f"Dossier: {BASE_DIR}/assets/",
            font_size=dp(9),
            color=get_color_from_hex("#7F8C8D"),
            size_hint_y=None, height=dp(22),
            halign='left', text_size=(None, None))
        self.add_widget(self.lbl_chemin)

        # Zone scrollable
        self.scroll = ScrollView(do_scroll_x=False)
        self.frame  = BoxLayout(orientation='vertical',
                                size_hint_y=None, spacing=dp(4),
                                padding=[dp(8), dp(6)])
        self.frame.bind(minimum_height=self.frame.setter('height'))
        self.scroll.add_widget(self.frame)
        self.add_widget(self.scroll)

        self._recharger()

    def _recharger(self):
        self.frame.clear_widgets()

        dossiers = {
            "Bordereaux PDF":   os.path.join(BASE_DIR, "assets", "bordereaux"),
            "Recus de retrait": os.path.join(BASE_DIR, "assets", "bordereaux"),
            "QR Codes":         os.path.join(BASE_DIR, "assets", "qrcodes"),
            "Rapports":         os.path.join(BASE_DIR, "assets", "rapports"),
        }

        nb_total = 0

        for titre, dossier in dossiers.items():
            # Lister les fichiers
            fichiers = []
            if os.path.exists(dossier):
                for f in sorted(os.listdir(dossier), reverse=True):
                    chemin = os.path.join(dossier, f)
                    if titre == "Bordereaux PDF" and f.startswith("bordereau"):
                        fichiers.append((f, chemin, "pdf"))
                    elif titre == "Recus de retrait" and f.startswith("recu"):
                        fichiers.append((f, chemin, "pdf"))
                    elif titre == "QR Codes" and f.endswith(".png"):
                        fichiers.append((f, chemin, "qr"))
                    elif titre == "Rapports" and f.endswith(".pdf"):
                        fichiers.append((f, chemin, "pdf"))

            if not fichiers and titre == "Recus de retrait":
                continue  # deja affiche dans Bordereaux

            # En-tete section
            from ui.widgets import SectionHeader, Separateur
            couleurs = {
                "Bordereaux PDF":   "#C0392B",
                "Recus de retrait": "#27AE60",
                "QR Codes":         "#3498DB",
                "Rapports":         "#8E44AD",
            }
            self.frame.add_widget(SectionHeader(
                f"{titre} ({len(fichiers)} fichier(s))",
                couleurs.get(titre, "#2C3E50")))

            if not fichiers:
                self.frame.add_widget(Label(
                    text="Aucun fichier genere.",
                    font_size=dp(11),
                    color=get_color_from_hex("#BDC3C7"),
                    size_hint_y=None, height=dp(32)))
            else:
                for fname, chemin, ftype in fichiers[:10]:
                    self._carte_fichier(fname, chemin, ftype)
                    nb_total += 1

            self.frame.add_widget(Separateur())

        if nb_total == 0:
            self.frame.add_widget(Label(
                text=(
                    "Aucun fichier genere pour l'instant.\n"
                    "Les PDF et QR codes apparaissent ici\n"
                    "apres enregistrement ou retrait d'un colis."
                ),
                font_size=dp(12),
                color=get_color_from_hex("#7F8C8D"),
                size_hint_y=None, height=dp(80),
                halign='center'))

    def _carte_fichier(self, fname: str, chemin: str, ftype: str):
        """Affiche une ligne pour un fichier avec apercu et boutons."""
        row = BoxLayout(orientation='horizontal',
                        size_hint_y=None, height=dp(64),
                        padding=[dp(8), dp(4)], spacing=dp(8))
        with row.canvas.before:
            Color(*get_color_from_hex("#FAFAFA"))
            rr = Rectangle(pos=row.pos, size=row.size)
        row.bind(pos=lambda w, v, r=rr: setattr(r, 'pos', v),
                 size=lambda w, v, r=rr: setattr(r, 'size', v))

        # Icone type
        icone_txt = "[PDF]" if ftype == "pdf" else "[QR]"
        icone_col = "#C0392B" if ftype == "pdf" else "#3498DB"
        icone = Label(
            text=icone_txt,
            font_size=dp(11), bold=True,
            color=get_color_from_hex(icone_col),
            size_hint=(None, None), size=(dp(46), dp(56)))
        row.add_widget(icone)

        # Infos fichier
        info = BoxLayout(orientation='vertical', spacing=dp(2))
        # Nom raccourci
        nom_court = fname[:32] + "..." if len(fname) > 32 else fname
        info.add_widget(Label(
            text=nom_court,
            font_size=dp(10), bold=True,
            color=get_color_from_hex("#2C3E50"),
            halign='left'))
        # Taille
        try:
            taille = os.path.getsize(chemin)
            taille_str = (f"{taille:,} octets" if taille < 1024
                          else f"{taille//1024} Ko")
        except Exception:
            taille_str = "?"
        info.add_widget(Label(
            text=taille_str,
            font_size=dp(9),
            color=get_color_from_hex("#7F8C8D"),
            halign='left'))
        row.add_widget(info)

        # Boutons action
        btns = BoxLayout(orientation='vertical',
                         size_hint=(None, None),
                         size=(dp(80), dp(56)),
                         spacing=dp(4))

        # Ouvrir
        btn_open = Button(
            text="Ouvrir",
            font_size=dp(9),
            background_color=get_color_from_hex("#2C3E50"),
            background_normal='', color=(1, 1, 1, 1),
            size_hint_y=None, height=dp(26))
        btn_open.bind(on_press=lambda a, c=chemin:
                      self._ouvrir(c))
        btns.add_widget(btn_open)

        # Apercu QR (si image)
        if ftype == "qr" and os.path.exists(chemin):
            btn_apercu = Button(
                text="Apercu",
                font_size=dp(9),
                background_color=get_color_from_hex("#3498DB"),
                background_normal='', color=(1, 1, 1, 1),
                size_hint_y=None, height=dp(26))
            btn_apercu.bind(on_press=lambda a, c=chemin:
                            self._apercu_qr(c))
            btns.add_widget(btn_apercu)

        row.add_widget(btns)
        self.frame.add_widget(row)

    def _ouvrir(self, chemin: str):
        ok, msg = ouvrir_fichier(chemin)
        if not ok:
            from kivy.uix.popup import Popup
            popup = Popup(
                title="Information",
                content=Label(
                    text=(
                        f"Chemin du fichier:\n{chemin}\n\n"
                        "Ouvrez ce fichier manuellement\n"
                        "avec un lecteur PDF ou image."
                    ),
                    font_size=dp(11),
                    color=get_color_from_hex("#2C3E50"),
                    halign='center'),
                size_hint=(0.9, None), height=dp(220))
            popup.open()

    def _apercu_qr(self, chemin: str):
        """Affiche un apercu du QR code dans un popup."""
        content = BoxLayout(orientation='vertical',
                            padding=dp(12), spacing=dp(8))
        content.add_widget(KivyImage(
            source=chemin,
            size_hint=(1, 1),
            allow_stretch=True))
        content.add_widget(Label(
            text=os.path.basename(chemin),
            font_size=dp(10),
            color=get_color_from_hex("#7F8C8D"),
            size_hint_y=None, height=dp(24)))

        popup = Popup(
            title="QR Code",
            content=content,
            size_hint=(0.9, 0.7))

        btn_f = Button(text="Fermer",
            background_color=get_color_from_hex("#2C3E50"),
            background_normal='', color=(1, 1, 1, 1),
            size_hint_y=None, height=dp(40))
        btn_f.bind(on_press=popup.dismiss)
        content.add_widget(btn_f)
        popup.open()

"""
ui/notif.py - Notifications Toast + utilitaires UI globaux
Toast auto-disparaissant, popup de confirmation, bouton retour standard
"""

import os
from kivy.uix.boxlayout  import BoxLayout
from kivy.uix.label      import Label
from kivy.uix.button     import Button
from kivy.uix.image      import Image as KivyImage
from kivy.uix.popup      import Popup
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics       import Color, RoundedRectangle
from kivy.utils          import get_color_from_hex
from kivy.metrics        import dp
from kivy.clock          import Clock
from kivy.animation      import Animation

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONS_DIR = os.path.join(BASE_DIR, 'assets', 'icons')


def icone(nom: str) -> str:
    """Retourne le chemin d une icone PNG."""
    chemin = os.path.join(ICONS_DIR, f'{nom}.png')
    return chemin if os.path.exists(chemin) else ''


# ─── Toast (notification auto-disparaissante) ────────────────────────────────

class Toast(Label):
    """
    Notification legere qui apparait 2 secondes puis disparait.
    Usage : Toast.afficher(widget_parent, "Message", type='succes')
    """

    _instance = None

    def __init__(self, **kw):
        kw.setdefault('size_hint', (None, None))
        kw.setdefault('font_size', dp(12))
        kw.setdefault('bold', True)
        kw.setdefault('color', (1, 1, 1, 1))
        kw.setdefault('halign', 'center')
        kw.setdefault('padding', [dp(16), dp(8)])
        super().__init__(**kw)
        self.opacity = 0
        with self.canvas.before:
            Color(0, 0, 0, 0.75)
            self._rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(8)])
        self.bind(pos=self._maj, size=self._maj)

    def _maj(self, *a):
        self._rect.pos  = self.pos
        self._rect.size = self.size

    @classmethod
    def afficher(cls, parent, message: str,
                 type_notif: str = 'info', duree: float = 2.5):
        """
        Affiche un toast dans le widget parent.
        type_notif : 'succes', 'erreur', 'info', 'attention'
        """
        couleurs = {
            'succes':    '#27AE60',
            'erreur':    '#C0392B',
            'info':      '#2C3E50',
            'attention': '#F39C12',
        }
        couleur = couleurs.get(type_notif, '#2C3E50')

        toast = cls(
            text=message,
            color=get_color_from_hex(couleur + 'FF'),
        )
        # Taille dynamique selon le texte
        toast.texture_update()
        toast.size = (dp(280), dp(44))

        # Position : bas centre de l ecran
        def _placer(*a):
            toast.pos = (
                (parent.width - toast.width) / 2,
                dp(80)
            )
        parent.bind(size=_placer)
        _placer()

        parent.add_widget(toast)

        # Animation : fade in -> attendre -> fade out
        anim = (
            Animation(opacity=1, duration=0.2) +
            Animation(opacity=1, duration=duree) +
            Animation(opacity=0, duration=0.3)
        )

        def _fin(*a):
            try:
                parent.remove_widget(toast)
            except Exception:
                pass

        anim.bind(on_complete=_fin)
        anim.start(toast)
        return toast


def toast(message: str, type_notif: str = 'info', duree: float = 2.5):
    """
    Toast global - cherche automatiquement la fenetre principale.
    """
    try:
        from kivy.app import App
        app = App.get_running_app()
        if app and app.root:
            Toast.afficher(app.root, message, type_notif, duree)
    except Exception:
        pass


# ─── Popup de confirmation ────────────────────────────────────────────────────

def confirmer(titre: str, message: str,
               cb_oui, cb_non=None,
               texte_oui: str = "Confirmer",
               texte_non: str = "Annuler") -> Popup:
    """
    Popup de confirmation avec deux boutons.
    cb_oui : fonction appelee si l utilisateur confirme.
    """
    content = BoxLayout(orientation='vertical',
                        padding=dp(16), spacing=dp(12))

    content.add_widget(Label(
        text=message,
        font_size=dp(12),
        color=get_color_from_hex('#2C3E50'),
        halign='center',
        size_hint_y=None, height=dp(48)))

    popup = Popup(title=titre, content=content,
                  size_hint=(0.85, None), height=dp(190))

    btns = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))

    btn_non = Button(
        text=texte_non, font_size=dp(12),
        background_color=get_color_from_hex('#BDC3C7'),
        background_normal='')
    btn_non.bind(on_press=lambda a: [popup.dismiss(),
                                      cb_non() if cb_non else None])

    btn_oui = Button(
        text=texte_oui, font_size=dp(12), bold=True,
        background_color=get_color_from_hex('#27AE60'),
        background_normal='', color=(1, 1, 1, 1))
    btn_oui.bind(on_press=lambda a: [popup.dismiss(), cb_oui()])

    btns.add_widget(btn_non)
    btns.add_widget(btn_oui)
    content.add_widget(btns)
    popup.open()
    return popup


# ─── Popup info simple ───────────────────────────────────────────────────────

def info_popup(titre: str, message: str,
               type_notif: str = 'info'):
    """
    Popup d information simple avec bouton OK.
    """
    couleurs = {
        'succes':    '#27AE60',
        'erreur':    '#C0392B',
        'info':      '#2C3E50',
        'attention': '#F39C12',
    }
    couleur = couleurs.get(type_notif, '#2C3E50')

    content = BoxLayout(orientation='vertical',
                        padding=dp(16), spacing=dp(10))

    # Barre coloree en haut
    barre = BoxLayout(size_hint_y=None, height=dp(6))
    with barre.canvas.before:
        Color(*get_color_from_hex(couleur))
        from kivy.graphics import Rectangle
        r = Rectangle(pos=barre.pos, size=barre.size)
    barre.bind(pos=lambda w, v: setattr(r, 'pos', v),
               size=lambda w, v: setattr(r, 'size', v))
    content.add_widget(barre)

    content.add_widget(Label(
        text=message,
        font_size=dp(12),
        color=get_color_from_hex('#2C3E50'),
        halign='center',
        size_hint_y=None, height=dp(60)))

    popup = Popup(title=titre, content=content,
                  size_hint=(0.85, None), height=dp(200))

    btn_ok = Button(
        text='OK', font_size=dp(13), bold=True,
        background_color=get_color_from_hex(couleur),
        background_normal='', color=(1, 1, 1, 1),
        size_hint_y=None, height=dp(44))
    btn_ok.bind(on_press=popup.dismiss)
    content.add_widget(btn_ok)
    popup.open()
    return popup


# ─── Bouton Retour standard ──────────────────────────────────────────────────

class BoutonRetour(Button):
    """
    Bouton retour standardise, a ajouter en haut de chaque page.
    """
    def __init__(self, callback, texte='<  Retour', **kw):
        kw.setdefault('font_size', dp(12))
        kw.setdefault('size_hint', (None, None))
        kw.setdefault('size', (dp(110), dp(38)))
        kw.setdefault('background_color', get_color_from_hex('#34495E'))
        kw.setdefault('background_normal', '')
        kw.setdefault('color', (1, 1, 1, 1))
        kw.setdefault('text', texte)
        super().__init__(**kw)
        self.bind(on_press=lambda a: callback())


# ─── En-tete de page avec bouton retour ──────────────────────────────────────

class HeaderPage(BoxLayout):
    """
    En-tete standard pour toutes les pages :
    [< Retour]  [TITRE DE LA PAGE]
    """

    def __init__(self, titre: str, couleur: str = '#2C3E50',
                 cb_retour=None, **kw):
        kw.setdefault('orientation', 'horizontal')
        kw.setdefault('size_hint_y', None)
        kw.setdefault('height', dp(48))
        super().__init__(**kw)

        with self.canvas.before:
            Color(*get_color_from_hex(couleur))
            self._rect = RoundedRectangle(
                pos=self.pos, size=self.size)
        self.bind(pos=self._maj, size=self._maj)

        if cb_retour:
            btn_ret = Button(
                text='< Retour',
                font_size=dp(11),
                size_hint=(None, None),
                size=(dp(90), dp(44)),
                background_color=get_color_from_hex('#1A252F'),
                background_normal='',
                color=(1, 1, 1, 1))
            btn_ret.bind(on_press=lambda a: cb_retour())
            self.add_widget(btn_ret)

        self.add_widget(Label(
            text=titre,
            font_size=dp(13), bold=True,
            color=(1, 1, 1, 1),
            halign='center'))

    def _maj(self, *a):
        self._rect.pos  = self.pos
        self._rect.size = self.size


# ─── Bouton avec icone PNG ────────────────────────────────────────────────────

class BoutonIcone(BoxLayout):
    """
    Bouton avec icone PNG + texte, cote a cote.
    """

    def __init__(self, texte: str, nom_icone: str,
                 callback, couleur: str = '#2C3E50', **kw):
        kw.setdefault('orientation', 'horizontal')
        kw.setdefault('size_hint_y', None)
        kw.setdefault('height', dp(48))
        kw.setdefault('spacing', 0)
        super().__init__(**kw)

        btn = Button(
            text=texte,
            font_size=dp(12), bold=True,
            background_color=get_color_from_hex(couleur),
            background_normal='',
            color=(1, 1, 1, 1))
        btn.bind(on_press=lambda a: callback())
        self.add_widget(btn)

    def disabled_set(self, val):
        for child in self.children:
            child.disabled = val

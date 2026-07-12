"""
Widgets utilitaires - composants Kivy réutilisables dans toute l'app
"""

from kivy.uix.boxlayout     import BoxLayout
from kivy.uix.label         import Label
from kivy.uix.button        import Button
from kivy.uix.textinput     import TextInput
from kivy.uix.scrollview    import ScrollView
from kivy.uix.gridlayout    import GridLayout
from kivy.graphics          import Color, Rectangle, RoundedRectangle
from kivy.utils             import get_color_from_hex
from kivy.metrics           import dp
from kivy.uix.widget        import Widget


# --- Couleurs hex rapides -----------------------------------------------------
C = {
    "rouge":    "#C0392B",
    "rouge_f":  "#922B21",
    "bleu":     "#2C3E50",
    "vert":     "#27AE60",
    "orange":   "#F39C12",
    "gris_c":   "#F5F5F5",
    "gris_b":   "#BDC3C7",
    "blanc":    "#FFFFFF",
    "texte":    "#2C3E50",
    "texte_g":  "#7F8C8D",
    "bleu_cl":  "#3498DB",
    "violet":   "#8E44AD",
}


def couleur(cle):
    return get_color_from_hex(C.get(cle, cle))


# --- Fond coloré sur un widget ------------------------------------------------

def set_bg(widget, hex_color):
    """Peint le fond d'un widget avec une couleur hexadécimale."""
    with widget.canvas.before:
        Color(*get_color_from_hex(hex_color))
        widget._rect = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(pos=lambda w, v: setattr(w._rect, 'pos', v),
                size=lambda w, v: setattr(w._rect, 'size', v))


# --- Carte blanche avec ombre simulée ----------------------------------------

class Card(BoxLayout):
    """Conteneur blanc avec fond blanc et padding."""

    def __init__(self, **kw):
        kw.setdefault('orientation', 'vertical')
        kw.setdefault('padding', dp(12))
        kw.setdefault('spacing', dp(6))
        super().__init__(**kw)
        with self.canvas.before:
            Color(*get_color_from_hex("#FFFFFF"))
            self._rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._maj, size=self._maj)

    def _maj(self, *a):
        self._rect.pos  = self.pos
        self._rect.size = self.size


# --- Label titre de section ---------------------------------------------------

class SectionHeader(BoxLayout):
    """Barre de titre colorée pour une section."""

    def __init__(self, texte: str, couleur_hex: str = "#2C3E50", **kw):
        kw.setdefault('size_hint_y', None)
        kw.setdefault('height', dp(38))
        super().__init__(**kw)
        with self.canvas.before:
            Color(*get_color_from_hex(couleur_hex))
            self._rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._maj, size=self._maj)
        self.add_widget(Label(
            text=texte,
            font_size=dp(13),
            bold=True,
            color=(1, 1, 1, 1),
            halign='left',
            valign='middle',
            padding=[dp(12), 0],
        ))

    def _maj(self, *a):
        self._rect.pos  = self.pos
        self._rect.size = self.size


# --- Champ de saisie stylisé -------------------------------------------------

class ChampSaisie(BoxLayout):
    """Label + TextInput dans un bloc vertical."""

    def __init__(self, label: str = "", hint: str = "",
                 password: bool = False,
                 multiline: bool = False, **kw):
        kw.setdefault('orientation', 'vertical')
        kw.setdefault('size_hint_y', None)
        kw.setdefault('height', dp(70) if not multiline else dp(100))
        kw.setdefault('spacing', dp(2))
        super().__init__(**kw)

        if label:
            self.add_widget(Label(
                text=label,
                font_size=dp(12),
                bold=True,
                color=get_color_from_hex("#2C3E50"),
                size_hint_y=None,
                height=dp(20),
                halign='left',
                valign='middle',
            ))

        self.entry = TextInput(
            hint_text=hint,
            password=password,
            multiline=multiline,
            font_size=dp(13),
            background_color=get_color_from_hex("#FFFFFF"),
            foreground_color=get_color_from_hex("#2C3E50"),
            cursor_color=get_color_from_hex("#C0392B"),
            hint_text_color=get_color_from_hex("#BDC3C7"),
            padding=[dp(10), dp(8)],
            size_hint_y=None,
            height=dp(40) if not multiline else dp(72),
        )
        self.add_widget(self.entry)

    @property
    def texte(self) -> str:
        return self.entry.text.strip()

    @texte.setter
    def texte(self, val: str):
        self.entry.text = val


# --- Bouton stylisé -----------------------------------------------------------

class BoutonPrimaire(Button):
    def __init__(self, **kw):
        kw.setdefault('background_color', get_color_from_hex("#C0392B"))
        kw.setdefault('background_normal', '')
        kw.setdefault('color', (1, 1, 1, 1))
        kw.setdefault('font_size', dp(13))
        kw.setdefault('bold', True)
        kw.setdefault('size_hint_y', None)
        kw.setdefault('height', dp(44))
        super().__init__(**kw)


class BoutonSecondaire(Button):
    def __init__(self, **kw):
        kw.setdefault('background_color', get_color_from_hex("#2C3E50"))
        kw.setdefault('background_normal', '')
        kw.setdefault('color', (1, 1, 1, 1))
        kw.setdefault('font_size', dp(12))
        kw.setdefault('size_hint_y', None)
        kw.setdefault('height', dp(40))
        super().__init__(**kw)


class BoutonSucces(Button):
    def __init__(self, **kw):
        kw.setdefault('background_color', get_color_from_hex("#27AE60"))
        kw.setdefault('background_normal', '')
        kw.setdefault('color', (1, 1, 1, 1))
        kw.setdefault('font_size', dp(13))
        kw.setdefault('bold', True)
        kw.setdefault('size_hint_y', None)
        kw.setdefault('height', dp(44))
        super().__init__(**kw)


class BoutonDanger(Button):
    def __init__(self, **kw):
        kw.setdefault('background_color', get_color_from_hex("#C0392B"))
        kw.setdefault('background_normal', '')
        kw.setdefault('color', (1, 1, 1, 1))
        kw.setdefault('font_size', dp(12))
        kw.setdefault('size_hint_y', None)
        kw.setdefault('height', dp(38))
        super().__init__(**kw)


# --- Badge statut -------------------------------------------------------------

class BadgeStatut(Label):
    def __init__(self, statut: str, **kw):
        from config.config import STATUTS
        txt, hex_c = STATUTS.get(statut, (statut, "#95A5A6"))
        kw.setdefault('text', f" {txt} ")
        kw.setdefault('font_size', dp(10))
        kw.setdefault('bold', True)
        kw.setdefault('color', (1, 1, 1, 1))
        kw.setdefault('size_hint', (None, None))
        kw.setdefault('size', (dp(90), dp(24)))
        super().__init__(**kw)
        with self.canvas.before:
            Color(*get_color_from_hex(hex_c))
            self._rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda w, v: setattr(w._rect, 'pos', v),
                  size=lambda w, v: setattr(w._rect, 'size', v))


# --- Ligne de tableau ---------------------------------------------------------

class LigneTableau(BoxLayout):
    """Ligne cliquable dans un tableau."""

    def __init__(self, pair: bool = False, on_press=None, **kw):
        kw.setdefault('orientation', 'horizontal')
        kw.setdefault('size_hint_y', None)
        kw.setdefault('height', dp(48))
        kw.setdefault('padding', [dp(8), dp(4)])
        kw.setdefault('spacing', dp(4))
        super().__init__(**kw)
        self._on_press = on_press
        bg = "#FAFAFA" if pair else "#FFFFFF"
        with self.canvas.before:
            Color(*get_color_from_hex(bg))
            self._rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._maj, size=self._maj)

    def _maj(self, *a):
        self._rect.pos  = self.pos
        self._rect.size = self.size

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and self._on_press:
            self._on_press(self)
            return True
        return super().on_touch_down(touch)


# --- ScrollView vertical simple -----------------------------------------------

def make_scroll(contenu: Widget) -> ScrollView:
    """Enveloppe un widget dans un ScrollView vertical."""
    sv = ScrollView(do_scroll_x=False)
    sv.add_widget(contenu)
    return sv


# --- Message d'erreur/succès -------------------------------------------------

class MessageBandeau(Label):
    def __init__(self, **kw):
        kw.setdefault('size_hint_y', None)
        kw.setdefault('height', dp(0))
        kw.setdefault('font_size', dp(12))
        kw.setdefault('bold', True)
        kw.setdefault('color', (1, 1, 1, 1))
        kw.setdefault('text', '')
        super().__init__(**kw)
        with self.canvas.before:
            Color(0, 0, 0, 0)
            self._rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._maj, size=self._maj)
        self._bg_color = Color(0, 0, 0, 0)

    def _maj(self, *a):
        self._rect.pos  = self.pos
        self._rect.size = self.size

    def afficher(self, texte: str, succes: bool = False):
        self.text   = texte
        self.height = dp(36)
        hex_c = "#27AE60" if succes else "#C0392B"
        with self.canvas.before:
            Color(*get_color_from_hex(hex_c))
            self._rect = Rectangle(pos=self.pos, size=self.size)

    def cacher(self):
        self.text   = ''
        self.height = dp(0)


# --- Séparateur horizontal ----------------------------------------------------

class Separateur(Widget):
    def __init__(self, **kw):
        kw.setdefault('size_hint_y', None)
        kw.setdefault('height', dp(1))
        super().__init__(**kw)
        with self.canvas:
            Color(*get_color_from_hex("#BDC3C7"))
            self._rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._maj, size=self._maj)

    def _maj(self, *a):
        self._rect.pos  = self.pos
        self._rect.size = self.size

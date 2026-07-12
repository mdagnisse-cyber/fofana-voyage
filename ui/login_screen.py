"""
Écran de Connexion - Kivy / Pydroid 3
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout     import BoxLayout
from kivy.uix.label         import Label
from kivy.uix.button        import Button
from kivy.uix.textinput     import TextInput
from kivy.uix.scrollview    import ScrollView
from kivy.graphics          import Color, Rectangle
from kivy.utils             import get_color_from_hex
from kivy.metrics           import dp
from kivy.app               import App

from modules.auth_manager import auth
from ui.widgets import (ChampSaisie, BoutonPrimaire,
                        MessageBandeau, set_bg)


class LoginScreen(Screen):

    def __init__(self, **kw):
        super().__init__(**kw)
        self._build()

    def _build(self):
        root = BoxLayout(orientation='vertical')

        # -- En-tête rouge ----------------------------------------------
        header = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(180),
            padding=[dp(16), dp(20)],
            spacing=dp(6),
        )
        with header.canvas.before:
            Color(*get_color_from_hex("#C0392B"))
            self._hr = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda w, v: setattr(self, '_hr',
                    self._maj_rect(self._hr, v, w.size)),
                    size=lambda w, v: setattr(self, '_hr',
                    self._maj_rect(self._hr, w.pos, v)))

        header.add_widget(Label(
            text="[COL]",
            font_size=dp(48),
            size_hint_y=None,
            height=dp(60),
        ))
        header.add_widget(Label(
            text="FOFANA VOYAGE",
            font_size=dp(20),
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(30),
        ))
        header.add_widget(Label(
            text="Gestion des Colis",
            font_size=dp(13),
            color=(1, 0.8, 0.8, 1),
            size_hint_y=None,
            height=dp(22),
        ))
        root.add_widget(header)

        # -- Formulaire ------------------------------------------------
        scroll = ScrollView(do_scroll_x=False)
        form   = BoxLayout(
            orientation='vertical',
            padding=[dp(24), dp(24)],
            spacing=dp(12),
            size_hint_y=None,
        )
        form.bind(minimum_height=form.setter('height'))

        form.add_widget(Label(
            text="Connexion",
            font_size=dp(18),
            bold=True,
            color=get_color_from_hex("#2C3E50"),
            size_hint_y=None,
            height=dp(36),
            halign='left',
        ))

        self.champ_user = ChampSaisie(
            label="Identifiant",
            hint="Votre identifiant"
        )
        form.add_widget(self.champ_user)

        self.champ_mdp = ChampSaisie(
            label="Mot de passe",
            hint="Votre mot de passe",
            password=True
        )
        form.add_widget(self.champ_mdp)

        self.msg = MessageBandeau()
        form.add_widget(self.msg)

        self.btn = BoutonPrimaire(text="SE CONNECTER")
        self.btn.bind(on_press=self._connecter)
        form.add_widget(self.btn)

        form.add_widget(Label(
            text="(c) 2025 Fofana Voyage v2.0",
            font_size=dp(10),
            color=get_color_from_hex("#BDC3C7"),
            size_hint_y=None,
            height=dp(30),
        ))

        scroll.add_widget(form)
        root.add_widget(scroll)
        self.add_widget(root)

    def _connecter(self, *a):
        username = self.champ_user.texte
        password = self.champ_mdp.texte

        if not username or not password:
            self.msg.afficher("Identifiant et mot de passe requis.")
            return

        self.btn.text = "Connexion..."
        self.btn.disabled = True

        ok, message = auth.connexion(username, password)

        self.btn.text     = "SE CONNECTER"
        self.btn.disabled = False

        if ok:
            self.msg.afficher(f"Bienvenue !", succes=True)
            # Rafraîchir la page principale avant d'y aller
            app = App.get_running_app()
            app.sm.get_screen('main').rafraichir()
            app.sm.current = 'main'
            # Vider les champs
            self.champ_user.texte = ''
            self.champ_mdp.texte  = ''
            self.msg.cacher()
        else:
            self.msg.afficher(message)

    @staticmethod
    def _maj_rect(rect, pos, size):
        rect.pos  = pos
        rect.size = size
        return rect

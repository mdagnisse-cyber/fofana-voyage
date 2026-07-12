"""
Ecran Principal v2.5 - Navigation avec icones PNG + toast global
"""

import os
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout     import BoxLayout
from kivy.uix.gridlayout    import GridLayout
from kivy.uix.label         import Label
from kivy.uix.button        import Button
from kivy.uix.image         import Image as KivyImage
from kivy.graphics          import Color, Rectangle
from kivy.utils             import get_color_from_hex
from kivy.metrics           import dp
from kivy.app               import App
from kivy.clock             import Clock

from modules.auth_manager import auth
from config.config        import ACCES_ROLES

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONS    = os.path.join(BASE_DIR, 'assets', 'icons')


def icone_path(nom):
    p = os.path.join(ICONS, f'{nom}.png')
    return p if os.path.exists(p) else ''


MENU = [
    ('accueil',    'Accueil',    'dashboard'),
    ('scan',       'Scan QR',    'scan'),
    ('colis',      'Colis',      'depot'),
    ('suivi',      'Suivi',      'suivi'),
    ('retrait',    'Retrait',    'retrait'),
    ('alertes',    'Alertes',    'alertes'),
    ('rapports',   'Rapports',   'rapports'),
    ('agents',     'Agents',     'agents'),
    ('agences',    'Agences',    'agences'),
    ('parametres', 'Params',     'parametres'),
    ('fichiers',   'Fichiers',   'fichiers'),
]


class BoutonNav(BoxLayout):
    """Bouton de navigation avec icone PNG + texte."""

    def __init__(self, icone_nom, label, cle, callback, **kw):
        kw.setdefault('orientation', 'vertical')
        kw.setdefault('spacing', 0)
        super().__init__(**kw)
        self.cle      = cle
        self._actif   = False
        self._callback= callback

        # Fond
        with self.canvas.before:
            self._bg_color = Color(*get_color_from_hex('#2C3E50'))
            self._bg_rect  = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._maj, size=self._maj)

        # Icone
        ico = icone_path(icone_nom)
        if ico:
            self._img = KivyImage(
                source=ico,
                size_hint=(1, None),
                height=dp(28),
                allow_stretch=True,
                keep_ratio=True)
            self.add_widget(self._img)
        else:
            self.add_widget(Label(
                text=label[:1],
                font_size=dp(16), bold=True,
                color=(1,1,1,1),
                size_hint_y=None, height=dp(28)))

        # Texte
        self._lbl = Label(
            text=label,
            font_size=dp(8),
            color=(1,1,1,1),
            size_hint_y=None, height=dp(16))
        self.add_widget(self._lbl)

        self.bind(on_touch_down=self._on_touch)

    def _maj(self, *a):
        self._bg_rect.pos  = self.pos
        self._bg_rect.size = self.size

    def _on_touch(self, widget, touch):
        if self.collide_point(*touch.pos):
            self._callback(self.cle)
            return True

    def set_actif(self, actif: bool):
        self._actif = actif
        col = '#C0392B' if actif else '#2C3E50'
        self._bg_color.rgba = get_color_from_hex(col)


class MainScreen(Screen):

    def __init__(self, **kw):
        super().__init__(**kw)
        self.page_active = None
        self.btns_nav    = {}
        self._build()

    def _build(self):
        self.root_layout = BoxLayout(orientation='vertical')

        # ── Header ────────────────────────────────────────────────────
        self.header = BoxLayout(
            size_hint_y=None, height=dp(48),
            padding=[dp(10), dp(6)], spacing=dp(8))
        with self.header.canvas.before:
            Color(*get_color_from_hex('#C0392B'))
            self._hr = Rectangle(pos=self.header.pos, size=self.header.size)
        self.header.bind(
            pos=lambda w,v: setattr(self._hr,'pos',v),
            size=lambda w,v: setattr(self._hr,'size',v))

        self.lbl_titre = Label(
            text='Fofana Voyage',
            font_size=dp(15), bold=True,
            color=(1,1,1,1), halign='left')
        self.header.add_widget(self.lbl_titre)

        self.lbl_user = Label(
            text='',
            font_size=dp(9),
            color=(1,0.8,0.8,1), halign='right')
        self.header.add_widget(self.lbl_user)

        btn_deco = Button(
            text='Quitter',
            font_size=dp(10),
            size_hint=(None, None),
            size=(dp(64), dp(36)),
            background_color=get_color_from_hex('#922B21'),
            background_normal='', color=(1,1,1,1))
        btn_deco.bind(on_press=self._deconnecter)
        self.header.add_widget(btn_deco)
        self.root_layout.add_widget(self.header)

        # ── Zone contenu ──────────────────────────────────────────────
        self.zone_contenu = BoxLayout(orientation='vertical')
        self.root_layout.add_widget(self.zone_contenu)

        # ── Navigation 2 rangees ──────────────────────────────────────
        nav_wrapper = BoxLayout(
            orientation='vertical',
            size_hint_y=None, height=dp(110))
        with nav_wrapper.canvas.before:
            Color(*get_color_from_hex('#1A252F'))
            self._nw = Rectangle(pos=nav_wrapper.pos, size=nav_wrapper.size)
        nav_wrapper.bind(
            pos=lambda w,v: setattr(self._nw,'pos',v),
            size=lambda w,v: setattr(self._nw,'size',v))

        self.nav_row1 = GridLayout(
            cols=5, size_hint_y=None, height=dp(54), spacing=dp(1))
        self.nav_row2 = GridLayout(
            cols=5, size_hint_y=None, height=dp(54), spacing=dp(1))

        nav_wrapper.add_widget(self.nav_row1)
        nav_wrapper.add_widget(self.nav_row2)
        self.root_layout.add_widget(nav_wrapper)
        self.add_widget(self.root_layout)

    def rafraichir(self):
        self.nav_row1.clear_widgets()
        self.nav_row2.clear_widgets()
        self.btns_nav.clear()

        role = auth.role or 'AGENT'
        user = auth.utilisateur
        if user:
            self.lbl_user.text = f"{user['prenom']} | {role}"

        pages_dispo = [
            (ic, lb, cle) for ic, lb, cle in MENU
            if role in ACCES_ROLES.get(cle, [])
        ]

        moitie = (len(pages_dispo) + 1) // 2
        self.nav_row1.cols = max(1, min(5, moitie))
        self.nav_row2.cols = max(1, min(5, len(pages_dispo) - moitie))

        for i, (icone_nom, label, cle) in enumerate(pages_dispo):
            btn = BoutonNav(
                icone_nom=icone_nom,
                label=label,
                cle=cle,
                callback=self._naviguer,
                size_hint_y=None, height=dp(54))

            if i < moitie:
                self.nav_row1.add_widget(btn)
            else:
                self.nav_row2.add_widget(btn)

            self.btns_nav[cle] = btn

        self._naviguer('dashboard')

    def _naviguer(self, page: str):
        self.page_active = page

        for cle, btn in self.btns_nav.items():
            btn.set_actif(cle == page)

        for ic, lb, cle in MENU:
            if cle == page:
                self.lbl_titre.text = lb
                break

        self.zone_contenu.clear_widgets()
        self.zone_contenu.add_widget(self._charger(page))

    def _charger(self, page: str):
        try:
            if page == 'dashboard':
                from ui.pages.dashboard import DashboardPage; return DashboardPage()
            elif page == 'scan':
                from ui.pages.scan_rapide import ScanRapidePage; return ScanRapidePage()
            elif page == 'depot':
                from ui.pages.depot_colis import DepotColisPage; return DepotColisPage()
            elif page == 'suivi':
                from ui.pages.suivi_colis import SuiviColisPage; return SuiviColisPage()
            elif page == 'retrait':
                from ui.pages.retrait_colis import RetraitColisPage; return RetraitColisPage()
            elif page == 'alertes':
                from ui.pages.alertes import AlertesPage; return AlertesPage()
            elif page == 'rapports':
                from ui.pages.rapports import RapportsPage; return RapportsPage()
            elif page == 'agents':
                from ui.pages.gestion_agents import GestionAgentsPage; return GestionAgentsPage()
            elif page == 'agences':
                from ui.pages.gestion_agences import GestionAgencesPage; return GestionAgencesPage()
            elif page == 'parametres':
                from ui.pages.parametres import ParametresPage; return ParametresPage()
            elif page == 'fichiers':
                from ui.pages.fichiers import FichiersPage; return FichiersPage()
        except Exception as e:
            return self._erreur(str(e))
        return self._erreur('Page introuvable')

    def _erreur(self, msg):
        box = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        box.add_widget(Label(
            text='Erreur chargement page',
            font_size=dp(14), bold=True,
            color=get_color_from_hex('#C0392B')))
        box.add_widget(Label(
            text=str(msg)[:200], font_size=dp(10),
            color=get_color_from_hex('#7F8C8D'),
            halign='left'))
        return box

    def _deconnecter(self, *a):
        from ui.notif import confirmer
        def _faire():
            auth.deconnexion()
            App.get_running_app().sm.current = 'login'
        confirmer(
            'Deconnexion',
            'Voulez-vous vous deconnecter ?',
            cb_oui=_faire,
            texte_oui='Deconnecter',
            texte_non='Rester')

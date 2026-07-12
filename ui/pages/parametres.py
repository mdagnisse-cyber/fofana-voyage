"""
Page Parametres v2.5 - Version stable et corrigee
"""

import os, sys, shutil
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from kivy.uix.boxlayout  import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label      import Label
from kivy.uix.button     import Button
from kivy.uix.spinner    import Spinner
from kivy.uix.textinput  import TextInput
from kivy.utils          import get_color_from_hex
from kivy.metrics        import dp
from kivy.graphics       import Color, Rectangle

from database.db_manager import select, upsert, rpc
from modules.auth_manager import auth
from ui.notif import toast, info_popup, HeaderPage


def _bg(widget, hex_c):
    with widget.canvas.before:
        Color(*get_color_from_hex(hex_c))
        r = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(pos=lambda w,v: setattr(r,'pos',v),
                size=lambda w,v: setattr(r,'size',v))


def _section_header(parent, titre, couleur):
    hdr = BoxLayout(size_hint_y=None, height=dp(36))
    _bg(hdr, couleur)
    hdr.add_widget(Label(
        text=titre, font_size=dp(11), bold=True,
        color=(1,1,1,1), halign='left',
        padding=[dp(10),0]))
    parent.add_widget(hdr)


def _champ(parent, label, valeur='', password=False,
           hint=''):
    parent.add_widget(Label(
        text=label, font_size=dp(11), bold=True,
        color=get_color_from_hex('#2C3E50'),
        size_hint_y=None, height=dp(22),
        halign='left'))
    inp = TextInput(
        text=valeur, hint_text=hint,
        password=password, multiline=False,
        font_size=dp(12),
        size_hint_y=None, height=dp(38),
        background_color=(1,1,1,1),
        foreground_color=get_color_from_hex('#2C3E50'))
    parent.add_widget(inp)
    return inp


class ParametresPage(BoxLayout):

    def __init__(self, **kw):
        kw.setdefault('orientation', 'vertical')
        super().__init__(**kw)
        self.params = self._charger()
        self._build()

    def _charger(self):
        try:
            rows = select("parametres", select_cols="cle,valeur")
            return {r['cle']: r['valeur'] for r in rows}
        except Exception:
            return {}

    def _sauver(self, cle, valeur):
        try:
            upsert("parametres", {"cle": cle, "valeur": str(valeur)}, on_conflict="cle")
            self.params[cle] = str(valeur)
            return True
        except Exception:
            return False

    def _build(self):
        # Titre
        hdr = HeaderPage('[PAR] Parametres', '#2C3E50')
        self.add_widget(hdr)

        sv = ScrollView(do_scroll_x=False)
        body = BoxLayout(orientation='vertical', size_hint_y=None,
                         padding=dp(10), spacing=dp(10))
        body.bind(minimum_height=body.setter('height'))

        # ── Profil ─────────────────────────────────────────────────
        _section_header(body, 'MON PROFIL', '#9B59B6')
        user = auth.utilisateur or {}
        for lb, val in [
            ('Nom',       f"{user.get('prenom','')} {user.get('nom','')}"),
            ('Username',  user.get('username','-')),
            ('Role',      user.get('role','-')),
        ]:
            row = BoxLayout(size_hint_y=None, height=dp(26))
            row.add_widget(Label(
                text=lb+':', font_size=dp(10), bold=True,
                color=get_color_from_hex('#7F8C8D'),
                size_hint_x=None, width=dp(100), halign='right'))
            row.add_widget(Label(
                text=str(val), font_size=dp(11),
                color=get_color_from_hex('#2C3E50'), halign='left'))
            body.add_widget(row)

        # ── Mot de passe ────────────────────────────────────────────
        _section_header(body, 'CHANGER MOT DE PASSE', '#C0392B')
        self.inp_anc = _champ(body, 'Ancien MDP', password=True)
        self.inp_nvx = _champ(body, 'Nouveau MDP (min 6 car.)', password=True)
        self.inp_cnf = _champ(body, 'Confirmer', password=True)

        btn_mdp = Button(
            text='Changer le mot de passe',
            font_size=dp(12), bold=True,
            background_color=get_color_from_hex('#C0392B'),
            background_normal='', color=(1,1,1,1),
            size_hint_y=None, height=dp(42))
        btn_mdp.bind(on_press=self._changer_mdp)
        body.add_widget(btn_mdp)

        # ── Config SMS ──────────────────────────────────────────────
        _section_header(body, 'SMS AUTOMATIQUES (Africa\'s Talking)', '#27AE60')

        body.add_widget(Label(
            text="Configuration pour envoi SMS automatique\n"
                 "depuis votre compte Africa's Talking",
            font_size=dp(10),
            color=get_color_from_hex('#7F8C8D'),
            size_hint_y=None, height=dp(36),
            halign='left'))

        self.inp_at_user = _champ(
            body, "Username Africa's Talking",
            self.params.get('sms_at_username','sandbox'),
            hint='sandbox ou votre_username')
        self.inp_at_key = _champ(
            body, "Cle API (API Key)",
            self.params.get('sms_at_apikey',''),
            hint='Coller votre cle API ici')
        self.inp_sender = _champ(
            body, "Identifiant expediteur (max 11 car.)",
            self.params.get('sms_sender_id','FofanaVoy'),
            hint='FofanaVoy')

        body.add_widget(Label(
            text="Strategie d envoi :",
            font_size=dp(11), bold=True,
            color=get_color_from_hex('#2C3E50'),
            size_hint_y=None, height=dp(22),
            halign='left'))
        self.spin_strat = Spinner(
            values=['africas_talking','android','textbelt','auto'],
            text=self.params.get('sms_strategie','africas_talking'),
            font_size=dp(12),
            size_hint_y=None, height=dp(38))
        body.add_widget(self.spin_strat)

        btns_sms = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        btn_test_sms = Button(
            text='Tester le SMS',
            font_size=dp(11),
            background_color=get_color_from_hex('#3498DB'),
            background_normal='', color=(1,1,1,1))
        btn_test_sms.bind(on_press=self._tester_sms)
        btns_sms.add_widget(btn_test_sms)

        btn_save_sms = Button(
            text='Sauver config SMS',
            font_size=dp(11), bold=True,
            background_color=get_color_from_hex('#27AE60'),
            background_normal='', color=(1,1,1,1))
        btn_save_sms.bind(on_press=self._sauver_sms)
        btns_sms.add_widget(btn_save_sms)
        body.add_widget(btns_sms)

        # ── Config generale ─────────────────────────────────────────
        _section_header(body, 'CONFIGURATION GENERALE', '#2C3E50')
        self.inp_nom  = _champ(body, "Nom entreprise",
            self.params.get('nom_entreprise','Fofana Voyage'))
        self.inp_dev  = _champ(body, "Devise",
            self.params.get('devise','FCFA'))
        self.inp_frais= _champ(body, "Frais base / kg (FCFA)",
            self.params.get('frais_base_kg','500'))
        self.inp_alert= _champ(body, "Alerte non-retrait (jours)",
            self.params.get('alert_days_no_pickup','7'))

        btn_gen = Button(
            text='Sauver la configuration',
            font_size=dp(12), bold=True,
            background_color=get_color_from_hex('#2C3E50'),
            background_normal='', color=(1,1,1,1),
            size_hint_y=None, height=dp(42))
        btn_gen.bind(on_press=self._sauver_general)
        body.add_widget(btn_gen)

        # ── Base de donnees ───────────────────────────────────────────
        _section_header(body, 'BASE DE DONNEES', '#3498DB')
        body.add_widget(Label(
            text="Les donnees sont hebergees en ligne (Supabase) et\n"
                 "partagees en temps reel entre toutes les agences.\n"
                 "Les sauvegardes sont gerees automatiquement cote serveur.",
            font_size=dp(10),
            color=get_color_from_hex('#7F8C8D'),
            size_hint_y=None, height=dp(50),
            halign='left'))

        # ── Journal ─────────────────────────────────────────────────
        _section_header(body, 'JOURNAL DES CONNEXIONS', '#7F8C8D')
        try:
            sessions = rpc("journal_connexions", {"p_limite": 6}) or []
        except Exception:
            sessions = []

        cols = {'LOGIN':'#27AE60','LOGOUT':'#95A5A6',
                'SMS':'#3498DB','DEPOT':'#C0392B','RETRAIT':'#8E44AD'}
        for s in sessions:
            row = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(8))
            col = cols.get(s['action'],'#2C3E50')
            row.add_widget(Label(
                text=f"[{s['action'][:7]}]",
                font_size=dp(9), bold=True,
                color=get_color_from_hex(col),
                size_hint_x=None, width=dp(70), halign='left'))
            row.add_widget(Label(
                text=f"{s['agent']}  {str(s['created_at'])[:16]}",
                font_size=dp(9),
                color=get_color_from_hex('#7F8C8D'),
                halign='left'))
            body.add_widget(row)

        sv.add_widget(body)
        self.add_widget(sv)

    # ── Actions ──────────────────────────────────────────────────────

    def _changer_mdp(self, *a):
        anc = self.inp_anc.text.strip()
        nvx = self.inp_nvx.text.strip()
        cnf = self.inp_cnf.text.strip()
        if not anc or not nvx:
            toast('Tous les champs sont obligatoires.', 'erreur')
            return
        if len(nvx) < 6:
            toast('Minimum 6 caracteres.', 'erreur')
            return
        if nvx != cnf:
            toast('Les mots de passe ne correspondent pas.', 'erreur')
            return
        ok, msg = auth.changer_mot_de_passe(auth.user_id, anc, nvx)
        if ok:
            self.inp_anc.text = self.inp_nvx.text = self.inp_cnf.text = ''
            toast('Mot de passe modifie avec succes !', 'succes')
        else:
            toast(msg, 'erreur')

    def _sauver_sms(self, *a):
        self._sauver('sms_at_username', self.inp_at_user.text.strip())
        self._sauver('sms_at_apikey',   self.inp_at_key.text.strip())
        self._sauver('sms_sender_id',   self.inp_sender.text.strip()[:11])
        self._sauver('sms_strategie',   self.spin_strat.text)
        toast('Configuration SMS sauvegardee !', 'succes')

    def _tester_sms(self, *a):
        user = auth.utilisateur
        if not user or not user.get('telephone'):
            toast('Ajoutez un telephone a votre profil.', 'attention')
            return
        self._sauver_sms()
        try:
            from utils.sms_manager import envoyer_sms_otp
            ok, msg = envoyer_sms_otp(
                user['telephone'], '123456', user['prenom'])
            toast(f'Test SMS : {msg[:50]}',
                  'succes' if ok else 'erreur')
        except Exception as e:
            toast(f'Erreur : {e}', 'erreur')

    def _sauver_general(self, *a):
        self._sauver('nom_entreprise',      self.inp_nom.text.strip())
        self._sauver('devise',              self.inp_dev.text.strip())
        self._sauver('frais_base_kg',       self.inp_frais.text.strip())
        self._sauver('alert_days_no_pickup',self.inp_alert.text.strip())
        toast('Configuration sauvegardee !', 'succes')



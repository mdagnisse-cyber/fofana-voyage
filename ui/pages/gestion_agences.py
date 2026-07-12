"""Page Gestion Agences - Kivy"""
from kivy.uix.boxlayout  import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label      import Label
from kivy.uix.button     import Button
from kivy.graphics       import Color, Rectangle
from kivy.utils          import get_color_from_hex
from kivy.metrics        import dp
from database.db_manager import rpc, insert
from modules.auth_manager import auth
from ui.widgets import SectionHeader, BoutonSucces, ChampSaisie, Separateur, MessageBandeau
from kivy.uix.popup import Popup

class GestionAgencesPage(BoxLayout):
    def __init__(self, **kw):
        kw.setdefault('orientation', 'vertical')
        super().__init__(**kw)
        self._build(); self._charger()

    def _build(self):
        top = BoxLayout(size_hint_y=None, height=dp(46),
                        padding=[dp(8),dp(4)], spacing=dp(8))
        top.add_widget(SectionHeader("[AGC]  Agences","#2C3E50"))
        if auth.est_admin():
            btn = BoutonSucces(text="[+] Ajouter",
                               size_hint_x=None, width=dp(110))
            btn.bind(on_press=lambda a: self._form())
            top.add_widget(btn)
        self.add_widget(top)
        self.scroll = ScrollView(do_scroll_x=False)
        self.frame  = BoxLayout(orientation='vertical', size_hint_y=None,
                                spacing=dp(6), padding=[dp(8),dp(6)])
        self.frame.bind(minimum_height=self.frame.setter('height'))
        self.scroll.add_widget(self.frame)
        self.add_widget(self.scroll)

    def _charger(self):
        self.frame.clear_widgets()
        try:
            agences = rpc("liste_agences_avec_stats") or []
        except Exception: agences=[]

        for ag in agences:
            actif = ag.get('est_active',1)
            card  = BoxLayout(orientation='vertical', size_hint_y=None,
                              height=dp(80), padding=[dp(12),dp(8)])
            with card.canvas.before:
                hc = "#C0392B" if actif else "#BDC3C7"
                Color(*get_color_from_hex("#FFFFFF"))
                rr = Rectangle(pos=card.pos, size=card.size)
            card.bind(pos=lambda w,v,r=rr: setattr(r,'pos',v),
                      size=lambda w,v,r=rr: setattr(r,'size',v))

            top = BoxLayout(size_hint_y=None, height=dp(28))
            top.add_widget(Label(
                text=f"{ag.get('code','-')}  -  {ag.get('nom','-')}",
                font_size=dp(12), bold=True,
                color=get_color_from_hex("#2C3E50"), halign='left'))
            badge = Label(text=" Active " if actif else " Inactive ",
                font_size=dp(9), bold=True, color=(1,1,1,1),
                size_hint=(None,None), size=(dp(60),dp(22)))
            hc2 = "#27AE60" if actif else "#C0392B"
            with badge.canvas.before:
                Color(*get_color_from_hex(hc2))
                rb = Rectangle(pos=badge.pos, size=badge.size)
            badge.bind(pos=lambda w,v,r=rb: setattr(r,'pos',v),
                       size=lambda w,v,r=rb: setattr(r,'size',v))
            top.add_widget(badge)
            card.add_widget(top)
            card.add_widget(Label(
                text=f"[LOC] {ag.get('ville','-')}  |  [COL] {ag.get('nb_colis',0)} colis  |  [TEL] {ag.get('telephone','-')}",
                font_size=dp(10), color=get_color_from_hex("#7F8C8D"),
                halign='left', size_hint_y=None, height=dp(20)))

            self.frame.add_widget(card)
            self.frame.add_widget(Separateur())

    def _form(self, agence=None):
        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))
        c_code = ChampSaisie("Code *","FV-XXX")
        c_nom  = ChampSaisie("Nom *","Nom agence")
        c_vil  = ChampSaisie("Ville *","Ville")
        c_adr  = ChampSaisie("Adresse","Adresse")
        c_tel  = ChampSaisie("Téléphone","+229...")
        msg    = MessageBandeau()
        for w in [c_code,c_nom,c_vil,c_adr,c_tel,msg]:
            content.add_widget(w)
        popup = Popup(title="Nouvelle agence",content=content,
                      size_hint=(0.92,0.85))
        def _sauv(*a):
            if not c_nom.texte or not c_vil.texte or not c_code.texte:
                msg.afficher("Code, nom et ville obligatoires.")
                return
            try:
                insert("agences", {
                    "code": c_code.texte.upper(),
                    "nom": c_nom.texte,
                    "ville": c_vil.texte,
                    "adresse": c_adr.texte,
                    "telephone": c_tel.texte,
                })
                popup.dismiss(); self._charger()
            except Exception as e: msg.afficher(str(e))
        btns = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        b_ann = Button(text="Annuler", background_color=get_color_from_hex("#BDC3C7"), background_normal='')
        b_ann.bind(on_press=popup.dismiss)
        b_sav = BoutonSucces(text="[SAVE] Enregistrer")
        b_sav.bind(on_press=_sauv)
        btns.add_widget(b_ann); btns.add_widget(b_sav)
        content.add_widget(btns)
        popup.open()

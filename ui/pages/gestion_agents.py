"""Page Gestion Agents - Kivy"""
from kivy.uix.boxlayout  import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label      import Label
from kivy.uix.button     import Button
from kivy.uix.spinner    import Spinner
from kivy.uix.popup      import Popup
from kivy.graphics       import Color, Rectangle
from kivy.utils          import get_color_from_hex
from kivy.metrics        import dp
from database.db_manager import rpc, select
from modules.auth_manager import auth
from config.config        import ROLES
from ui.widgets import (SectionHeader, BoutonPrimaire, BoutonSucces,
                        ChampSaisie, Separateur, MessageBandeau)

class GestionAgentsPage(BoxLayout):
    def __init__(self, **kw):
        kw.setdefault('orientation', 'vertical')
        super().__init__(**kw)
        self._build()
        self._charger()

    def _build(self):
        top = BoxLayout(size_hint_y=None, height=dp(46),
                        padding=[dp(8),dp(4)], spacing=dp(8))
        top.add_widget(SectionHeader("[AGT]  Agents","#2C3E50"))
        btn_add = BoutonSucces(text="[+] Ajouter",
                               size_hint_x=None, width=dp(110))
        btn_add.bind(on_press=lambda a: self._form_agent())
        top.add_widget(btn_add)
        self.add_widget(top)

        self.scroll = ScrollView(do_scroll_x=False)
        self.frame  = BoxLayout(orientation='vertical', size_hint_y=None,
                                spacing=dp(2), padding=[dp(8),dp(4)])
        self.frame.bind(minimum_height=self.frame.setter('height'))
        self.scroll.add_widget(self.frame)
        self.add_widget(self.scroll)

    def _charger(self):
        self.frame.clear_widgets()
        try:
            agents = rpc("liste_utilisateurs") or []
        except Exception: agents=[]

        for i, ag in enumerate(agents):
            bg  = "#FAFAFA" if i%2==0 else "#FFFFFF"
            row = BoxLayout(size_hint_y=None, height=dp(60),
                            padding=[dp(10),dp(6)], spacing=dp(8))
            with row.canvas.before:
                Color(*get_color_from_hex(bg))
                rr = Rectangle(pos=row.pos, size=row.size)
            row.bind(pos=lambda w,v,r=rr: setattr(r,'pos',v),
                     size=lambda w,v,r=rr: setattr(r,'size',v))

            info = BoxLayout(orientation='vertical')
            info.add_widget(Label(
                text=f"{ag['prenom']} {ag['nom']}  ({ag['username']})",
                font_size=dp(12), bold=True,
                color=get_color_from_hex("#2C3E50"), halign='left'))
            info.add_widget(Label(
                text=f"{ROLES.get(ag['role'],ag['role'])}  |  {ag.get('agence_nom','-')}",
                font_size=dp(10), color=get_color_from_hex("#7F8C8D"),
                halign='left'))
            row.add_widget(info)

            actif = ag.get('est_actif',1)
            badge = Label(
                text=" Actif " if actif else " Inactif ",
                font_size=dp(9), bold=True, color=(1,1,1,1),
                size_hint=(None,None), size=(dp(56),dp(22)))
            with badge.canvas.before:
                hc = "#27AE60" if actif else "#C0392B"
                Color(*get_color_from_hex(hc))
                rb = Rectangle(pos=badge.pos, size=badge.size)
            badge.bind(pos=lambda w,v,r=rb: setattr(r,'pos',v),
                       size=lambda w,v,r=rb: setattr(r,'size',v))
            row.add_widget(badge)

            self.frame.add_widget(row)
            self.frame.add_widget(Separateur())

    def _form_agent(self, agent=None):
        creation = agent is None
        content  = BoxLayout(orientation='vertical',
                             padding=dp(12), spacing=dp(8))
        sv  = ScrollView(do_scroll_x=False)
        frm = BoxLayout(orientation='vertical', size_hint_y=None,
                        spacing=dp(8), padding=[0,dp(4)])
        frm.bind(minimum_height=frm.setter('height'))

        c_nom     = ChampSaisie("Nom *", "NOM")
        c_prenom  = ChampSaisie("Prénom *", "Prénom")
        c_user    = ChampSaisie("Identifiant *", "username")
        c_mdp     = ChampSaisie("Mot de passe *", "||||||", password=True)
        c_tel     = ChampSaisie("Téléphone", "+229...")

        agences = []
        try:
            agences = select("agences", filters={"est_active": "eq.1"},
                              select_cols="id,code,nom")
        except Exception: pass

        noms_ag = [f"{a['code']} - {a['nom']}" for a in agences]
        spin_ag = Spinner(values=noms_ag or ["Aucune"],
                          text=noms_ag[0] if noms_ag else "",
                          font_size=dp(11), size_hint_y=None, height=dp(38))
        spin_role = Spinner(values=list(ROLES.keys()), text="AGENT",
                            font_size=dp(11), size_hint_y=None, height=dp(38))

        for w in [c_nom, c_prenom, c_user, c_mdp, c_tel]:
            frm.add_widget(w)
        frm.add_widget(Label(text="Agence", font_size=dp(11), bold=True,
            color=get_color_from_hex("#2C3E50"), size_hint_y=None, height=dp(20)))
        frm.add_widget(spin_ag)
        frm.add_widget(Label(text="Rôle", font_size=dp(11), bold=True,
            color=get_color_from_hex("#2C3E50"), size_hint_y=None, height=dp(20)))
        frm.add_widget(spin_role)

        msg = MessageBandeau()
        frm.add_widget(msg)
        sv.add_widget(frm)
        content.add_widget(sv)

        popup = Popup(title="Nouvel agent" if creation else "Modifier",
                      content=content, size_hint=(0.92, 0.88))

        def _sauv(*a):
            ag_id = None
            for i, nm in enumerate(noms_ag):
                if nm == spin_ag.text:
                    ag_id = agences[i]['id']; break
            data = {"nom": c_nom.texte.upper(),
                    "prenom": c_prenom.texte.capitalize(),
                    "username": c_user.texte.lower(),
                    "password": c_mdp.texte,
                    "role": spin_role.text,
                    "agence_id": ag_id,
                    "telephone": c_tel.texte}
            if not data['nom'] or not data['username'] or not data['password']:
                msg.afficher("Nom, identifiant et MDP obligatoires.")
                return
            if len(data['password']) < 6:
                msg.afficher("MDP : minimum 6 caractères.")
                return
            ok, message = auth.creer_utilisateur(data)
            if ok:
                popup.dismiss()
                self._charger()
            else:
                msg.afficher(message)

        btns = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        b_ann = Button(text="Annuler", font_size=dp(11),
            background_color=get_color_from_hex("#BDC3C7"),
            background_normal='')
        b_ann.bind(on_press=popup.dismiss)
        b_sav = BoutonSucces(text="[SAVE]  Enregistrer")
        b_sav.bind(on_press=_sauv)
        btns.add_widget(b_ann); btns.add_widget(b_sav)
        content.add_widget(btns)
        popup.open()

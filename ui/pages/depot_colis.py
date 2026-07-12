"""
Page Enregistrement Colis - Kivy
"""

from kivy.uix.boxlayout  import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label      import Label
from kivy.uix.spinner    import Spinner
from kivy.uix.checkbox   import CheckBox
from kivy.uix.popup      import Popup
from kivy.utils          import get_color_from_hex
from kivy.metrics        import dp

from modules.colis_manager import colis_manager
from modules.auth_manager  import auth
from ui.widgets import (ChampSaisie, BoutonPrimaire, BoutonSucces,
                        SectionHeader, MessageBandeau,
                        Separateur, Card)
from ui.notif import toast, info_popup


class DepotColisPage(BoxLayout):

    def __init__(self, **kw):
        kw.setdefault('orientation', 'vertical')
        super().__init__(**kw)
        self.agences = colis_manager.liste_agences()
        self._build()

    def _build(self):
        scroll = ScrollView(do_scroll_x=False)
        form   = BoxLayout(
            orientation='vertical',
            padding=dp(12), spacing=dp(10),
            size_hint_y=None,
        )
        form.bind(minimum_height=form.setter('height'))

        # -- Expéditeur ------------------------------------------------
        form.add_widget(SectionHeader("[USR]  EXPÉDITEUR", "#2C3E50"))
        self.exp_tel    = ChampSaisie("Téléphone *", "+229...")
        self.exp_nom    = ChampSaisie("Nom *", "NOM")
        self.exp_prenom = ChampSaisie("Prénom", "Prénom")
        self.exp_ville  = ChampSaisie("Ville", "Ville")
        for w in [self.exp_tel, self.exp_nom,
                  self.exp_prenom, self.exp_ville]:
            form.add_widget(w)
        self.exp_tel.entry.bind(
            on_text_validate=lambda e: self._auto_fill("exp"))

        # -- Destinataire ----------------------------------------------
        form.add_widget(SectionHeader("[DEST]  DESTINATAIRE", "#C0392B"))
        self.dest_tel    = ChampSaisie("Téléphone *", "+229...")
        self.dest_nom    = ChampSaisie("Nom *", "NOM")
        self.dest_prenom = ChampSaisie("Prénom", "Prénom")
        self.dest_ville  = ChampSaisie("Ville", "Ville")
        for w in [self.dest_tel, self.dest_nom,
                  self.dest_prenom, self.dest_ville]:
            form.add_widget(w)
        self.dest_tel.entry.bind(
            on_text_validate=lambda e: self._auto_fill("dest"))

        # -- Agences ---------------------------------------------------
        form.add_widget(SectionHeader("[AGC]  AGENCES", "#3498DB"))
        noms_ag = [f"{a['code']} - {a['nom']}" for a in self.agences]

        form.add_widget(Label(
            text="Agence de départ *",
            font_size=dp(12), bold=True,
            color=get_color_from_hex("#2C3E50"),
            size_hint_y=None, height=dp(22), halign='left',
        ))
        self.spin_dep = Spinner(
            values=noms_ag or ["Aucune agence"],
            text=noms_ag[0] if noms_ag else "",
            font_size=dp(12),
            size_hint_y=None, height=dp(40),
            background_color=get_color_from_hex("#F5F5F5"),
        )
        # Pré-sélectionner l'agence de l'agent
        if auth.agence_id:
            for nm, ag in zip(noms_ag, self.agences):
                if ag['id'] == auth.agence_id:
                    self.spin_dep.text = nm
                    break
        form.add_widget(self.spin_dep)

        form.add_widget(Label(
            text="Agence d'arrivée *",
            font_size=dp(12), bold=True,
            color=get_color_from_hex("#2C3E50"),
            size_hint_y=None, height=dp(22), halign='left',
        ))
        self.spin_arr = Spinner(
            values=noms_ag or ["Aucune agence"],
            text=noms_ag[-1] if len(noms_ag) > 1 else (noms_ag[0] if noms_ag else ""),
            font_size=dp(12),
            size_hint_y=None, height=dp(40),
            background_color=get_color_from_hex("#F5F5F5"),
        )
        form.add_widget(self.spin_arr)

        # -- Détails colis ---------------------------------------------
        form.add_widget(SectionHeader("[COL]  COLIS", "#8E44AD"))
        self.description = ChampSaisie("Description *", "Contenu...",
                                       multiline=True)
        self.description.height = dp(100)
        self.poids    = ChampSaisie("Poids (kg)", "0")
        self.valeur   = ChampSaisie("Valeur FCFA", "0")
        self.pieces   = ChampSaisie("Nb. pièces", "1")
        self.frais    = ChampSaisie("Frais envoi (FCFA) *", "0")
        for w in [self.description, self.poids,
                  self.valeur, self.pieces, self.frais]:
            form.add_widget(w)

        # Options
        opts = BoxLayout(size_hint_y=None, height=dp(36),
                         spacing=dp(16))
        self.chk_fragile = CheckBox(size_hint=(None, None),
                                    size=(dp(30), dp(30)))
        opts.add_widget(self.chk_fragile)
        opts.add_widget(Label(
            text="Fragile", font_size=dp(12),
            color=get_color_from_hex("#F39C12"),
            size_hint_x=None, width=dp(60),
        ))
        self.chk_paye = CheckBox(size_hint=(None, None),
                                  size=(dp(30), dp(30)),
                                  active=True)
        opts.add_widget(self.chk_paye)
        opts.add_widget(Label(
            text="Payé", font_size=dp(12),
            color=get_color_from_hex("#27AE60"),
        ))
        form.add_widget(opts)

        # Message
        self.msg = MessageBandeau()
        form.add_widget(self.msg)

        # Boutons
        btns = BoxLayout(size_hint_y=None, height=dp(48),
                         spacing=dp(10))
        btn_reset = BoutonSucces(text="Réinitialiser")
        btn_reset.background_color = get_color_from_hex("#7F8C8D")
        btn_reset.bind(on_press=self._reinitialiser)
        btns.add_widget(btn_reset)

        self.btn_save = BoutonPrimaire(text="[SAVE]  ENREGISTRER")
        self.btn_save.bind(on_press=self._enregistrer)
        btns.add_widget(self.btn_save)
        form.add_widget(btns)

        scroll.add_widget(form)
        self.add_widget(scroll)

    def _get_agence_id(self, spinner):
        val = spinner.text
        for ag in self.agences:
            if ag['code'] in val:
                return ag['id']
        return None

    def _auto_fill(self, cote: str):
        """Auto-complétion depuis le téléphone."""
        tel = self.exp_tel.texte if cote == "exp" else self.dest_tel.texte
        if not tel:
            return
        res = colis_manager.rechercher_client(tel)
        if res:
            c = res[0]
            if cote == "exp":
                self.exp_nom.texte    = c.get("nom", "")
                self.exp_prenom.texte = c.get("prenom", "")
                self.exp_ville.texte  = c.get("ville", "")
            else:
                self.dest_nom.texte    = c.get("nom", "")
                self.dest_prenom.texte = c.get("prenom", "")
                self.dest_ville.texte  = c.get("ville", "")

    def _enregistrer(self, *a):
        data = {
            "expediteur_tel":    self.exp_tel.texte,
            "expediteur_nom":    self.exp_nom.texte,
            "expediteur_prenom": self.exp_prenom.texte,
            "expediteur_ville":  self.exp_ville.texte,
            "destinataire_tel":    self.dest_tel.texte,
            "destinataire_nom":    self.dest_nom.texte,
            "destinataire_prenom": self.dest_prenom.texte,
            "destinataire_ville":  self.dest_ville.texte,
            "agence_depart_id":  self._get_agence_id(self.spin_dep),
            "agence_arrivee_id": self._get_agence_id(self.spin_arr),
            "description":    self.description.texte,
            "poids_kg":       self.poids.texte or "0",
            "valeur_declaree":self.valeur.texte or "0",
            "nombre_pieces":  self.pieces.texte or "1",
            "frais_envoi":    self.frais.texte or "0",
            "fragile":        self.chk_fragile.active,
            "paye":           self.chk_paye.active,
        }

        self.btn_save.disabled = True
        ok, message, colis = colis_manager.enregistrer_colis(data)
        self.btn_save.disabled = False

        if ok:
            self._popup_succes(colis)
        else:
            toast(message, "erreur")

    def _popup_succes(self, colis: dict):
        content = BoxLayout(
            orientation='vertical',
            padding=dp(16), spacing=dp(10))
        content.add_widget(Label(
            text="[RET]  Colis enregistré !",
            font_size=dp(15), bold=True,
            color=get_color_from_hex("#27AE60"),
            size_hint_y=None, height=dp(36),
        ))
        content.add_widget(Label(
            text=f"N°  {colis.get('numero','-')}",
            font_size=dp(14), bold=True,
            color=get_color_from_hex("#C0392B"),
            size_hint_y=None, height=dp(30),
        ))

        popup = Popup(
            title="Succès",
            content=content,
            size_hint=(0.88, None), height=dp(220))

        btns = BoxLayout(size_hint_y=None, height=dp(44),
                         spacing=dp(10))

        def _pdf(*a):
            try:
                from utils.pdf_generator import generer_bordereau_depot
                generer_bordereau_depot(colis)
                popup.dismiss()
                self.msg.afficher("PDF généré dans assets/bordereaux/",
                                  succes=True)
            except Exception as e:
                self.msg.afficher(f"PDF erreur : {e}")
                popup.dismiss()

        btn_pdf  = BoutonPrimaire(text="[PDF] PDF")
        btn_pdf.bind(on_press=_pdf)
        btn_nvx = BoutonSucces(text="[+] Nouveau")
        btn_nvx.bind(on_press=lambda a: [popup.dismiss(),
                                          self._reinitialiser()])
        btns.add_widget(btn_pdf)
        btns.add_widget(btn_nvx)
        content.add_widget(btns)
        popup.open()

    def _reinitialiser(self, *a):
        for champ in [self.exp_tel, self.exp_nom, self.exp_prenom,
                      self.exp_ville, self.dest_tel, self.dest_nom,
                      self.dest_prenom, self.dest_ville,
                      self.description, self.poids, self.valeur,
                      self.pieces, self.frais]:
            champ.texte = ""
        self.chk_fragile.active = False
        self.chk_paye.active    = True
        

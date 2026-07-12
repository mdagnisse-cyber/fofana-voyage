"""Page Retrait Sécurisé - Kivy (4 étapes)"""
from kivy.uix.boxlayout  import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label      import Label
from kivy.uix.checkbox   import CheckBox
from kivy.uix.button     import Button
from kivy.graphics       import Color, Rectangle
from kivy.utils          import get_color_from_hex
from kivy.metrics        import dp
from modules.colis_manager import colis_manager
from modules.auth_manager  import auth
from config.config         import STATUTS
from ui.widgets import (ChampSaisie, BoutonPrimaire, BoutonSucces,
                        SectionHeader, MessageBandeau, Separateur)

class RetraitColisPage(BoxLayout):
    def __init__(self, **kw):
        kw.setdefault('orientation', 'vertical')
        super().__init__(**kw)
        self.colis_courant = None
        self._etape1()

    def _clear(self):
        self.clear_widgets()

    def _header_etape(self, titre, sous=""):
        box = BoxLayout(orientation='vertical',
                        size_hint_y=None, height=dp(60),
                        padding=[dp(12),dp(8)])
        with box.canvas.before:
            Color(*get_color_from_hex("#2C3E50"))
            r = Rectangle(pos=box.pos, size=box.size)
        box.bind(pos=lambda w,v: setattr(r,'pos',v),
                 size=lambda w,v: setattr(r,'size',v))
        box.add_widget(Label(text=titre, font_size=dp(13), bold=True,
            color=(1,1,1,1), halign='left'))
        if sous:
            box.add_widget(Label(text=sous, font_size=dp(10),
                color=(0.8,0.8,0.8,1), halign='left'))
        return box

    # -- Étape 1 : Recherche ------------------------------------------
    def _etape1(self):
        self._clear()
        self.add_widget(self._header_etape(
            "Étape 1 / 4 - Recherche",
            "Entrez le numéro ou le téléphone du destinataire"))

        scroll = ScrollView(do_scroll_x=False)
        body   = BoxLayout(orientation='vertical',
                           size_hint_y=None, padding=dp(16),
                           spacing=dp(12))
        body.bind(minimum_height=body.setter('height'))

        self.champ_recherche = ChampSaisie("", "N° colis ou téléphone...")
        body.add_widget(self.champ_recherche)

        self.msg1 = MessageBandeau()
        body.add_widget(self.msg1)

        btns_rech = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))

        btn = BoutonPrimaire(text="Rechercher")
        btn.bind(on_press=self._faire_recherche)
        btns_rech.add_widget(btn)

        from kivy.uix.button import Button
        from kivy.utils import get_color_from_hex
        btn_scan = Button(
            text="[CAM] Scanner QR",
            font_size=dp(12), bold=True,
            background_color=get_color_from_hex("#27AE60"),
            background_normal='', color=(1,1,1,1),
            size_hint_y=None, height=dp(44))
        btn_scan.bind(on_press=lambda a: self._scanner_qr_retrait())
        btns_rech.add_widget(btn_scan)
        body.add_widget(btns_rech)

        self.frame_res = BoxLayout(orientation='vertical',
                                   size_hint_y=None, spacing=dp(6))
        self.frame_res.bind(minimum_height=self.frame_res.setter('height'))
        body.add_widget(self.frame_res)

        scroll.add_widget(body)
        self.add_widget(scroll)

    def _faire_recherche(self, *a):
        terme = self.champ_recherche.texte
        if not terme:
            self.msg1.afficher("Veuillez saisir un numéro ou téléphone.")
            return
        res = colis_manager.rechercher_colis(terme=terme, limite=5)
        retirables = [c for c in res if c['statut'] in ('ARRIVE','DEPOSE')]
        self.frame_res.clear_widgets()

        if not retirables:
            deja = [c for c in res if c['statut'] == 'RETIRE']
            msg  = "Ce colis a déjà été retiré." if deja else "Aucun colis en attente trouvé."
            self.msg1.afficher(msg)
            return

        self.msg1.cacher()
        if len(retirables) == 1:
            self.colis_courant = retirables[0]
            self._etape2()
            return

        for c in retirables:
            txt_s, hex_s = STATUTS.get(c['statut'], (c['statut'],"#95A5A6"))
            btn = Button(
                text=f"{c['numero']}\n{c.get('destinataire_nom','-')} - {txt_s}",
                font_size=dp(11), halign='center',
                background_color=get_color_from_hex("#F5F5F5"),
                background_normal='', color=get_color_from_hex("#2C3E50"),
                size_hint_y=None, height=dp(56),
            )
            btn.bind(on_press=lambda a, co=c: self._selec(co))
            self.frame_res.add_widget(btn)

    def _selec(self, colis):
        self.colis_courant = colis
        self._etape2()

    # -- Étape 2 : Vérification identité -----------------------------
    def _etape2(self):
        self._clear()
        c = self.colis_courant
        self.add_widget(self._header_etape(
            "Étape 2 / 4 - Vérification identité",
            "Vérifiez la pièce d'identité du destinataire"))

        scroll = ScrollView(do_scroll_x=False)
        body   = BoxLayout(orientation='vertical', size_hint_y=None,
                           padding=dp(16), spacing=dp(10))
        body.bind(minimum_height=body.setter('height'))

        # Fiche colis
        body.add_widget(SectionHeader("Colis attendu", "#C0392B"))
        for lb, val in [
            ("N°",           c.get('numero','-')),
            ("Destinataire", c.get('destinataire_nom','-')),
            ("Téléphone",    c.get('destinataire_tel','-')),
            ("Description",  c.get('description','-')[:40]),
        ]:
            row = BoxLayout(size_hint_y=None, height=dp(26))
            row.add_widget(Label(text=lb+":", font_size=dp(11), bold=True,
                color=get_color_from_hex("#7F8C8D"),
                size_hint_x=None, width=dp(110), halign='right'))
            row.add_widget(Label(text=str(val), font_size=dp(11),
                color=get_color_from_hex("#2C3E50"), halign='left'))
            body.add_widget(row)

        body.add_widget(Separateur())
        confirm_row = BoxLayout(size_hint_y=None, height=dp(40))
        self.chk_id = CheckBox()
        confirm_row.add_widget(self.chk_id)
        confirm_row.add_widget(Label(
            text="J'ai vérifié la pièce d'identité",
            font_size=dp(12), bold=True,
            color=get_color_from_hex("#2C3E50"),
        ))
        body.add_widget(confirm_row)

        self.msg2 = MessageBandeau()
        body.add_widget(self.msg2)

        btns = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
        btn_ret = Button(text="<- Retour", font_size=dp(11),
            background_color=get_color_from_hex("#BDC3C7"),
            background_normal='', size_hint_y=None, height=dp(44))
        btn_ret.bind(on_press=lambda a: self._etape1())
        btns.add_widget(btn_ret)
        btn_ok = BoutonPrimaire(text="Générer OTP ->")
        btn_ok.bind(on_press=self._valider_id)
        btns.add_widget(btn_ok)
        body.add_widget(btns)

        scroll.add_widget(body)
        self.add_widget(scroll)

    def _valider_id(self, *a):
        if not self.chk_id.active:
            self.msg2.afficher("Confirmez la vérification d'identité.")
            return
        self._etape3()

    # -- Étape 3 : OTP ------------------------------------------------
    def _etape3(self):
        self._clear()
        c = self.colis_courant
        ok, msg_otp, code_otp = colis_manager.generer_otp_retrait(c['id'])
        if not ok:
            self._etape1()
            return
        self.otp_genere = code_otp

        # Envoi SMS automatique au destinataire
        self.sms_envoye = False
        self.sms_message = ""
        try:
            from utils.sms_manager import envoyer_sms_otp
            tel_dest  = c.get('destinataire_tel', '')
            nom_dest  = c.get('destinataire_nom', '')
            if tel_dest:
                sms_ok, sms_msg = envoyer_sms_otp(
                    tel_dest, code_otp, nom_dest)
                self.sms_envoye  = sms_ok
                self.sms_message = sms_msg
        except Exception as e:
            self.sms_envoye  = False
            self.sms_message = str(e)
        self.add_widget(self._header_etape(
            "Étape 3 / 4 - Code OTP",
            "Communiquez ce code au destinataire"))

        scroll = ScrollView(do_scroll_x=False)
        body   = BoxLayout(orientation='vertical', size_hint_y=None,
                           padding=dp(16), spacing=dp(12))
        body.bind(minimum_height=body.setter('height'))

        # Affichage grand code
        body.add_widget(Label(
            text=code_otp, font_size=dp(42), bold=True,
            color=get_color_from_hex("#C0392B"),
            size_hint_y=None, height=dp(70),
        ))
        body.add_widget(Label(
            text="[OTP]  Valide 15 minutes - Usage unique",
            font_size=dp(10), color=get_color_from_hex("#F39C12"),
            size_hint_y=None, height=dp(24),
        ))

        # Afficher le statut de l'envoi SMS
        sms_ok  = getattr(self, 'sms_envoye', False)
        sms_msg = getattr(self, 'sms_message', '')
        if sms_ok:
            sms_label = Label(
                text=f"[SMS] Code envoye par SMS au destinataire",
                font_size=dp(10), bold=True,
                color=get_color_from_hex("#27AE60"),
                size_hint_y=None, height=dp(28))
        elif sms_msg:
            sms_label = Label(
                text=f"[!] SMS non envoye - communiquez le code verbalement",
                font_size=dp(10),
                color=get_color_from_hex("#F39C12"),
                size_hint_y=None, height=dp(28))
        else:
            sms_label = Label(
                text="Communiquez le code verbalement au destinataire",
                font_size=dp(10),
                color=get_color_from_hex("#7F8C8D"),
                size_hint_y=None, height=dp(28))
        body.add_widget(sms_label)

        body.add_widget(Separateur())
        body.add_widget(Label(
            text="Le destinataire vous dicte le code :",
            font_size=dp(12), bold=True,
            color=get_color_from_hex("#2C3E50"),
            size_hint_y=None, height=dp(28),
        ))

        self.champ_otp = ChampSaisie("", "Saisir le code OTP...")
        self.champ_otp.entry.font_size = dp(22)
        body.add_widget(self.champ_otp)

        self.msg3 = MessageBandeau()
        body.add_widget(self.msg3)

        btns = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        btn_ret = Button(text="<- Retour", font_size=dp(11),
            background_color=get_color_from_hex("#BDC3C7"),
            background_normal='', size_hint_y=None, height=dp(44))
        btn_ret.bind(on_press=lambda a: self._etape2())
        btns.add_widget(btn_ret)

        btn_regen = Button(text="[MAJ] Nouveau OTP", font_size=dp(11),
            background_color=get_color_from_hex("#F39C12"),
            background_normal='', color=(1,1,1,1),
            size_hint_y=None, height=dp(44))
        btn_regen.bind(on_press=lambda a: self._etape3())
        btns.add_widget(btn_regen)

        btn_ok = BoutonSucces(text="[RET] Valider")
        btn_ok.bind(on_press=self._valider_otp)
        btns.add_widget(btn_ok)
        body.add_widget(btns)

        scroll.add_widget(body)
        self.add_widget(scroll)

    def _valider_otp(self, *a):
        otp_saisi = self.champ_otp.texte
        if not otp_saisi:
            self.msg3.afficher("Veuillez saisir le code OTP.")
            return
        ok, msg = colis_manager.confirmer_retrait(
            self.colis_courant['id'], otp_saisi)
        if ok:
            self._etape4()
        else:
            self.msg3.afficher(msg)
            self.champ_otp.texte = ""

    # -- Étape 4 : Confirmation ---------------------------------------
    def _etape4(self):
        self._clear()
        c = self.colis_courant
        self.add_widget(self._header_etape(
            "Étape 4 / 4 - Confirmation [RET]", ""))

        scroll = ScrollView(do_scroll_x=False)
        body   = BoxLayout(orientation='vertical', size_hint_y=None,
                           padding=dp(16), spacing=dp(10))
        body.bind(minimum_height=body.setter('height'))

        body.add_widget(Label(
            text="[RET]  Retrait confirmé !",
            font_size=dp(18), bold=True,
            color=get_color_from_hex("#27AE60"),
            size_hint_y=None, height=dp(48),
        ))
        body.add_widget(Label(
            text=f"Colis  {c.get('numero','-')}",
            font_size=dp(14), bold=True,
            color=get_color_from_hex("#C0392B"),
            size_hint_y=None, height=dp(30),
        ))

        from datetime import datetime
        infos = [
            ("Destinataire", c.get("destinataire_nom","-")),
            ("Téléphone",    c.get("destinataire_tel","-")),
            ("Description",  c.get("description","-")),
            ("Date/Heure",   datetime.now().strftime("%d/%m/%Y %H:%M")),
        ]
        for lb, val in infos:
            row = BoxLayout(size_hint_y=None, height=dp(26))
            row.add_widget(Label(text=lb+":", font_size=dp(10), bold=True,
                color=get_color_from_hex("#7F8C8D"),
                size_hint_x=None, width=dp(110), halign='right'))
            row.add_widget(Label(text=str(val), font_size=dp(10),
                color=get_color_from_hex("#2C3E50"), halign='left'))
            body.add_widget(row)

        body.add_widget(Separateur())
        btns = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))

        def _pdf(*a):
            try:
                from utils.pdf_generator import generer_recu_retrait
                from modules.auth_manager import auth as _auth
                data = {
                    'numero': c.get('numero','-'),
                    'destinataire_nom': c.get('destinataire_nom','-'),
                    'destinataire_tel': c.get('destinataire_tel','-'),
                    'expediteur_nom':   c.get('expediteur_nom','-'),
                    'description':      c.get('description','-'),
                    'agence_arrivee':   c.get('agence_arrivee_nom','-'),
                    'agent_retrait':    (f"{_auth.utilisateur['prenom']} {_auth.utilisateur['nom']}"
                                        if _auth.utilisateur else '-'),
                    'date_retrait':     datetime.now().strftime('%d/%m/%Y %H:%M'),
                }
                generer_recu_retrait(data)
            except Exception:
                pass

        btn_pdf = BoutonPrimaire(text="[PDF] Reçu PDF")
        btn_pdf.bind(on_press=_pdf)
        btns.add_widget(btn_pdf)

        btn_nvx = BoutonSucces(text="[+] Nouveau retrait")
        btn_nvx.bind(on_press=lambda a: self._etape1())
        btns.add_widget(btn_nvx)
        body.add_widget(btns)

        scroll.add_widget(body)
        self.add_widget(scroll)

    def _scanner_qr_retrait(self):
        """Ouvre le scanner QR pour l etape 1 du retrait."""
        from utils.scanner_qr import ouvrir_scanner
        from modules.colis_manager import colis_manager

        def _sur_scan(numero: str):
            res = colis_manager.rechercher_colis(terme=numero, limite=1)
            retirables = [c for c in res
                          if c['statut'] in ('ARRIVE', 'DEPOSE')]
            if not retirables:
                deja = [c for c in res if c['statut'] == 'RETIRE']
                if deja:
                    self.msg1.afficher("Ce colis a deja ete retire.")
                else:
                    self.msg1.afficher(
                        f"Colis {numero} introuvable ou non disponible.")
                return
            self.colis_courant = retirables[0]
            self._etape2()

        ouvrir_scanner("Scanner QR - Retrait de colis", _sur_scan)

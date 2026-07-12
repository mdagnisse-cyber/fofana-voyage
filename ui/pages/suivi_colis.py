"""Page Suivi Colis - Kivy"""
from kivy.uix.boxlayout  import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label      import Label
from kivy.uix.button     import Button
from kivy.uix.spinner    import Spinner
from kivy.uix.popup      import Popup
from kivy.graphics       import Color, Rectangle
from kivy.utils          import get_color_from_hex
from kivy.metrics        import dp
from modules.colis_manager import colis_manager
from modules.auth_manager  import auth
from config.config         import STATUTS
from ui.widgets import (ChampSaisie, BoutonPrimaire, SectionHeader,
                        Separateur, MessageBandeau, BadgeStatut)

class SuiviColisPage(BoxLayout):
    def __init__(self, **kw):
        kw.setdefault('orientation', 'vertical')
        super().__init__(**kw)
        self.colis_selec = None
        self._build()
        self._rechercher()

    def _build(self):
        # Barre recherche
        bar = BoxLayout(size_hint_y=None, height=dp(96),
                        orientation='vertical',
                        padding=[dp(10),dp(6)], spacing=dp(6))
        with bar.canvas.before:
            Color(*get_color_from_hex("#FFFFFF"))
            self._rb = Rectangle(pos=bar.pos, size=bar.size)
        bar.bind(pos=lambda w,v: setattr(self._rb,'pos',v),
                 size=lambda w,v: setattr(self._rb,'size',v))

        self.champ_terme = ChampSaisie("", "N°, Nom ou Téléphone...")
        self.champ_terme.height = dp(50)
        bar.add_widget(self.champ_terme)

        ligne = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(8))
        self.spin_statut = Spinner(
            values=["Tous"] + [v[0] for v in STATUTS.values()],
            text="Tous", font_size=dp(11),
            size_hint_y=None, height=dp(36),
        )
        self._statut_map = {"Tous": ""}
        self._statut_map.update({v[0]: k for k, v in STATUTS.items()})
        ligne.add_widget(self.spin_statut)

        btn_chercher = BoutonPrimaire(text="Rechercher")
        btn_chercher.bind(on_press=lambda a: self._rechercher())
        ligne.add_widget(btn_chercher)

        btn_scan = Button(
            text="[CAM] Scanner QR",
            font_size=dp(11), bold=True,
            background_color=get_color_from_hex("#27AE60"),
            background_normal='', color=(1,1,1,1),
            size_hint_y=None, height=dp(38))
        btn_scan.bind(on_press=lambda a: self._ouvrir_scanner())
        ligne.add_widget(btn_scan)
        bar.add_widget(ligne)
        self.add_widget(bar)

        self.label_nb = Label(
            text="", font_size=dp(10),
            color=get_color_from_hex("#7F8C8D"),
            size_hint_y=None, height=dp(20),
            halign='right',
        )
        self.add_widget(self.label_nb)

        # Zone résultats
        self.scroll = ScrollView(do_scroll_x=False)
        self.frame_rows = BoxLayout(
            orientation='vertical', spacing=dp(2),
            size_hint_y=None, padding=[dp(6), dp(4)],
        )
        self.frame_rows.bind(minimum_height=self.frame_rows.setter('height'))
        self.scroll.add_widget(self.frame_rows)
        self.add_widget(self.scroll)

    def _rechercher(self):
        terme  = self.champ_terme.texte
        statut = self._statut_map.get(self.spin_statut.text, "")
        res    = colis_manager.rechercher_colis(
            terme=terme, statut=statut, limite=50)
        self._afficher(res)

    def _afficher(self, liste: list):
        self.frame_rows.clear_widgets()
        self.label_nb.text = f"{len(liste)} résultat(s)"
        if not liste:
            self.frame_rows.add_widget(Label(
                text="Aucun colis trouvé.",
                font_size=dp(13),
                color=get_color_from_hex("#7F8C8D"),
                size_hint_y=None, height=dp(60),
            ))
            return

        for i, c in enumerate(liste):
            bg   = "#FAFAFA" if i % 2 == 0 else "#FFFFFF"
            row  = BoxLayout(orientation='vertical',
                             size_hint_y=None, height=dp(70),
                             padding=[dp(10), dp(6)])
            with row.canvas.before:
                Color(*get_color_from_hex(bg))
                rr = Rectangle(pos=row.pos, size=row.size)
            row.bind(pos=lambda w,v,r=rr: setattr(r,'pos',v),
                     size=lambda w,v,r=rr: setattr(r,'size',v))

            top = BoxLayout(size_hint_y=None, height=dp(26))
            top.add_widget(Label(
                text=c['numero'], font_size=dp(11), bold=True,
                color=get_color_from_hex("#C0392B"), halign='left',
            ))
            txt_s, hex_s = STATUTS.get(c['statut'], (c['statut'],"#95A5A6"))
            badge = Label(
                text=f" {txt_s} ", font_size=dp(9), bold=True,
                color=(1,1,1,1),
                size_hint=(None,None), size=(dp(80), dp(22)),
            )
            with badge.canvas.before:
                Color(*get_color_from_hex(hex_s))
                rb = Rectangle(pos=badge.pos, size=badge.size)
            badge.bind(pos=lambda w,v,r=rb: setattr(r,'pos',v),
                       size=lambda w,v,r=rb: setattr(r,'size',v))
            top.add_widget(badge)
            row.add_widget(top)

            row.add_widget(Label(
                text=f"-> {c.get('destinataire_nom','-')}  |  {c.get('agence_arrivee_nom','-')[:20]}",
                font_size=dp(10),
                color=get_color_from_hex("#7F8C8D"),
                halign='left', size_hint_y=None, height=dp(20),
            ))

            row.bind(on_touch_down=lambda w, t, co=c:
                     self._detail(co) if w.collide_point(*t.pos) else None)
            self.frame_rows.add_widget(row)
            self.frame_rows.add_widget(Separateur())

    def _detail(self, colis: dict):
        self.colis_selec = colis
        content = BoxLayout(orientation='vertical',
                            padding=dp(12), spacing=dp(8))
        sv = ScrollView(do_scroll_x=False)
        inner = BoxLayout(orientation='vertical', spacing=dp(6),
                          size_hint_y=None)
        inner.bind(minimum_height=inner.setter('height'))

        champs = [
            ("Numéro",       colis.get("numero","-")),
            ("Expéditeur",   colis.get("expediteur_nom","-")),
            ("Tél. exp.",    colis.get("expediteur_tel","-")),
            ("Destinataire", colis.get("destinataire_nom","-")),
            ("Tél. dest.",   colis.get("destinataire_tel","-")),
            ("Départ",       colis.get("agence_depart_nom","-")),
            ("Arrivée",      colis.get("agence_arrivee_nom","-")),
            ("Description",  colis.get("description","-")),
            ("Frais",        f"{float(colis.get('frais_envoi',0)):,.0f} FCFA"),
            ("Statut",       STATUTS.get(colis['statut'],(colis['statut'],''))[0]),
            ("Déposé le",    str(colis.get('date_depot','-'))[:16]),
        ]
        for lb, val in champs:
            row = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(8))
            row.add_widget(Label(text=lb+":",
                font_size=dp(10), bold=True,
                color=get_color_from_hex("#7F8C8D"),
                size_hint_x=None, width=dp(100), halign='right',
            ))
            row.add_widget(Label(text=str(val), font_size=dp(10),
                color=get_color_from_hex("#2C3E50"), halign='left',
            ))
            inner.add_widget(row)

        # Actions statut
        actions = {
            "DEPOSE":     [("[TRNS] En transit","EN_TRANSIT","#3498DB"),
                           ("[LIT] Litige","LITIGE","#8E44AD")],
            "EN_TRANSIT": [("[LOC] Marquer Arrivé","ARRIVE","#27AE60"),
                           ("[LIT] Litige","LITIGE","#8E44AD")],
            "ARRIVE":     [("[X] Perdu","PERDU","#C0392B"),
                           ("[LIT] Litige","LITIGE","#8E44AD")],
        }
        acs = actions.get(colis['statut'], [])
        popup = Popup(title=f"Colis {colis['numero']}",
                      content=content,
                      size_hint=(0.92, 0.88))

        for label_ac, ns, hc in acs:
            btn = Button(
                text=label_ac, font_size=dp(11),
                background_color=get_color_from_hex(hc),
                background_normal='', color=(1,1,1,1),
                size_hint_y=None, height=dp(38),
            )
            def _changer(a, n=ns, p=popup, co=colis):
                ok, msg = colis_manager.changer_statut(
                    co['id'], n,
                    agence_id=auth.agence_id,
                    description=f"Action: {n}")
                # Notifier le destinataire si colis marque Arrive
                if ok and n == 'ARRIVE':
                    try:
                        from utils.sms_manager import envoyer_sms_arrivee
                        envoyer_sms_arrivee(
                            co.get('destinataire_tel',''),
                            co.get('numero',''),
                            co.get('destinataire_nom','')
                        )
                    except Exception:
                        pass
                p.dismiss()
                self._rechercher()
            btn.bind(on_press=_changer)
            inner.add_widget(btn)

        sv.add_widget(inner)
        content.add_widget(sv)
        btn_f = Button(text="Fermer", font_size=dp(12),
                       background_color=get_color_from_hex("#BDC3C7"),
                       background_normal='',
                       size_hint_y=None, height=dp(40))
        btn_f.bind(on_press=popup.dismiss)
        content.add_widget(btn_f)
        popup.open()

    def _ouvrir_scanner(self):
        """Ouvre le scanner QR pour changer le statut d un colis."""
        from utils.scanner_qr import ouvrir_scanner

        def _sur_scan(numero: str):
            from modules.colis_manager import colis_manager
            from modules.auth_manager  import auth

            res = colis_manager.rechercher_colis(terme=numero, limite=1)
            if not res:
                self.label_nb.text = f"Colis {numero} introuvable."
                return

            colis  = res[0]
            statut = colis['statut']

            if statut == 'DEPOSE':
                nouveau, desc = 'EN_TRANSIT', 'Mise en transit via scan QR'
            elif statut == 'EN_TRANSIT':
                nouveau, desc = 'ARRIVE', 'Arrivee confirmee via scan QR'
            else:
                self.label_nb.text = (
                    f"Colis {numero} : statut [{statut}] - "
                    f"aucune action possible par scan.")
                return

            # Popup confirmation
            from kivy.uix.popup   import Popup
            from kivy.uix.boxlayout import BoxLayout
            from kivy.uix.label   import Label
            from kivy.uix.button  import Button
            from kivy.utils       import get_color_from_hex
            from kivy.metrics     import dp
            from config.config    import STATUTS

            txt_n, hex_n = STATUTS.get(nouveau, (nouveau, "#27AE60"))
            txt_s, hex_s = STATUTS.get(statut,  (statut,  "#95A5A6"))

            content = BoxLayout(orientation='vertical',
                                padding=dp(16), spacing=dp(10))
            content.add_widget(Label(
                text=colis['numero'],
                font_size=dp(13), bold=True,
                color=get_color_from_hex("#C0392B"),
                size_hint_y=None, height=dp(30)))
            content.add_widget(Label(
                text=f"Dest : {colis.get('destinataire_nom','?')}",
                font_size=dp(11),
                color=get_color_from_hex("#2C3E50"),
                size_hint_y=None, height=dp(24)))
            content.add_widget(Label(
                text=f"Action : [{txt_s}]  ->  [{txt_n}]",
                font_size=dp(12), bold=True,
                color=get_color_from_hex(hex_n),
                size_hint_y=None, height=dp(28)))

            popup = Popup(title="Confirmer le scan",
                          content=content,
                          size_hint=(0.88, None), height=dp(250))

            btns = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
            btn_non = Button(text="Annuler",
                background_color=get_color_from_hex("#BDC3C7"),
                background_normal='')
            btn_non.bind(on_press=popup.dismiss)

            def _confirmer(*a):
                ok, msg = colis_manager.changer_statut(
                    colis['id'], nouveau,
                    agence_id=auth.agence_id,
                    description=desc)
                if ok and nouveau == 'ARRIVE':
                    try:
                        from utils.sms_manager import envoyer_sms_arrivee
                        envoyer_sms_arrivee(
                            colis.get('destinataire_tel', ''),
                            colis.get('numero', ''),
                            colis.get('destinataire_nom', ''))
                    except Exception:
                        pass
                popup.dismiss()
                self._rechercher()
                self.label_nb.text = msg

            btn_oui = Button(
                text="Confirmer",
                background_color=get_color_from_hex("#27AE60"),
                background_normal='', color=(1, 1, 1, 1))
            btn_oui.bind(on_press=_confirmer)
            btns.add_widget(btn_non)
            btns.add_widget(btn_oui)
            content.add_widget(btns)
            popup.open()

        ouvrir_scanner("Scanner QR - Transit / Arrivee", _sur_scan)

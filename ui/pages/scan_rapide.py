"""
Page Scan Rapide v2.5 - Interface coherente avec retour et notifications
"""
import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from kivy.uix.boxlayout  import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label      import Label
from kivy.uix.button     import Button
from kivy.uix.popup      import Popup
from kivy.graphics       import Color, Rectangle
from kivy.utils          import get_color_from_hex
from kivy.metrics        import dp
from kivy.app            import App

from modules.colis_manager import colis_manager
from modules.auth_manager  import auth
from config.config         import STATUTS
from ui.widgets import SectionHeader, BoutonPrimaire, BoutonSucces, Separateur
from ui.notif   import toast, confirmer, HeaderPage


class ScanRapidePage(BoxLayout):

    def __init__(self, **kw):
        kw.setdefault('orientation', 'vertical')
        super().__init__(**kw)
        self._historique = []
        self._build()

    def _build(self):
        # En-tete avec retour
        self.add_widget(HeaderPage('[CAM] Scan Rapide QR', '#27AE60'))

        sv = ScrollView(do_scroll_x=False)
        body = BoxLayout(orientation='vertical', size_hint_y=None,
                         padding=dp(12), spacing=dp(10))
        body.bind(minimum_height=body.setter('height'))

        # Info
        info_box = BoxLayout(orientation='vertical',
                             size_hint_y=None, height=dp(72),
                             padding=[dp(12), dp(8)])
        with info_box.canvas.before:
            Color(*get_color_from_hex('#EAF6FF'))
            r = Rectangle(pos=info_box.pos, size=info_box.size)
        info_box.bind(pos=lambda w,v: setattr(r,'pos',v),
                      size=lambda w,v: setattr(r,'size',v))

        for txt, col in [
            ('Action automatique selon le statut du colis scanne :', '#2C3E50'),
            ('Depose->Transit  |  Transit->Arrive  |  Arrive->Retrait', '#27AE60'),
        ]:
            info_box.add_widget(Label(
                text=txt, font_size=dp(10),
                color=get_color_from_hex(col),
                halign='left', size_hint_y=None, height=dp(24)))
        body.add_widget(info_box)

        # Bouton scanner
        btn = Button(
            text='SCANNER UN COLIS',
            font_size=dp(15), bold=True,
            background_color=get_color_from_hex('#27AE60'),
            background_normal='', color=(1,1,1,1),
            size_hint_y=None, height=dp(60))
        btn.bind(on_press=self._scanner)
        body.add_widget(btn)

        # Statut dernier scan
        body.add_widget(SectionHeader('Dernier scan', '#2C3E50'))
        self.lbl_resultat = Label(
            text='Aucun scan effectue.',
            font_size=dp(12),
            color=get_color_from_hex('#7F8C8D'),
            size_hint_y=None, height=dp(40),
            halign='center')
        body.add_widget(self.lbl_resultat)

        # Historique session
        body.add_widget(SectionHeader('Historique session', '#3498DB'))
        self.frame_hist = BoxLayout(orientation='vertical',
                                    size_hint_y=None, spacing=dp(2))
        self.frame_hist.bind(minimum_height=self.frame_hist.setter('height'))
        body.add_widget(self.frame_hist)

        sv.add_widget(body)
        self.add_widget(sv)

    def _scanner(self, *a):
        from utils.scanner_qr import ouvrir_scanner
        ouvrir_scanner('Scanner QR - Action automatique', self._traiter)

    def _traiter(self, numero: str):
        res = colis_manager.rechercher_colis(terme=numero, limite=1)
        if not res or res[0]['numero'] != numero:
            toast(f'Colis {numero} introuvable.', 'erreur')
            self.lbl_resultat.text  = f'Non trouve : {numero}'
            self.lbl_resultat.color = get_color_from_hex('#C0392B')
            return

        colis  = res[0]
        statut = colis['statut']
        self._ajouter_hist(numero, statut)

        actions = {
            'DEPOSE':     ('EN_TRANSIT', 'Mettre en transit'),
            'EN_TRANSIT': ('ARRIVE',     'Marquer Arrive'),
        }

        if statut == 'ARRIVE':
            self._popup_aller_retrait(colis)
            return
        if statut == 'RETIRE':
            toast(f'Colis {numero} deja retire.', 'info')
            self.lbl_resultat.text  = f'{numero} : deja retire'
            self.lbl_resultat.color = get_color_from_hex('#7F8C8D')
            return
        if statut not in actions:
            toast(f'Statut {statut} : aucune action.', 'attention')
            return

        nouveau, label_ac = actions[statut]

        def _faire():
            ok, msg = colis_manager.changer_statut(
                colis['id'], nouveau,
                agence_id=auth.agence_id,
                description=f'Scan QR : {label_ac}')
            if ok:
                if nouveau == 'ARRIVE':
                    try:
                        from utils.sms_manager import envoyer_sms_arrivee
                        envoyer_sms_arrivee(
                            colis.get('destinataire_tel',''),
                            numero,
                            colis.get('destinataire_nom',''))
                    except Exception:
                        pass
                toast(f'{numero} -> {label_ac} OK', 'succes')
                txt_n = STATUTS.get(nouveau, (nouveau,))[0]
                self.lbl_resultat.text  = f'{numero} : {txt_n}'
                self.lbl_resultat.color = get_color_from_hex('#27AE60')
                self._ajouter_hist(numero, nouveau)
            else:
                toast(msg, 'erreur')

        txt_s = STATUTS.get(statut, (statut,))[0]
        txt_n = STATUTS.get(nouveau, (nouveau,))[0]
        confirmer(
            'Confirmer action',
            f'Colis : {numero}\n{txt_s}  ->  {txt_n}',
            cb_oui=_faire,
            texte_oui=label_ac)

    def _popup_aller_retrait(self, colis):
        def _aller():
            app  = App.get_running_app()
            main = app.sm.get_screen('main')
            main._naviguer('retrait')
            from kivy.clock import Clock
            def _pre(dt):
                try:
                    page = main.zone_contenu.children[0]
                    page.champ_recherche.text = colis['numero']
                    page._faire_recherche()
                except Exception:
                    pass
            Clock.schedule_once(_pre, 0.4)

        confirmer(
            'Colis pret au retrait',
            f"Colis {colis['numero']}\n"
            f"Dest : {colis.get('destinataire_nom','?')}\n"
            f"Aller vers la procedure de retrait ?",
            cb_oui=_aller,
            texte_oui='Aller au retrait')

    def _ajouter_hist(self, numero, statut):
        from datetime import datetime
        heure  = datetime.now().strftime('%H:%M:%S')
        txt_s, hex_s = STATUTS.get(statut, (statut, '#95A5A6'))
        row = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(6))
        row.add_widget(Label(
            text=heure, font_size=dp(9),
            color=get_color_from_hex('#7F8C8D'),
            size_hint_x=None, width=dp(60), halign='left'))
        row.add_widget(Label(
            text=numero, font_size=dp(10), bold=True,
            color=get_color_from_hex('#2C3E50'), halign='left'))

        badge = Label(
            text=f' {txt_s} ', font_size=dp(8), bold=True,
            color=(1,1,1,1),
            size_hint=(None,None), size=(dp(80), dp(20)))
        with badge.canvas.before:
            Color(*get_color_from_hex(hex_s))
            rb = Rectangle(pos=badge.pos, size=badge.size)
        badge.bind(pos=lambda w,v: setattr(rb,'pos',v),
                   size=lambda w,v: setattr(rb,'size',v))
        row.add_widget(badge)

        self._historique.insert(0, row)
        self.frame_hist.clear_widgets()
        for r in self._historique[:8]:
            self.frame_hist.add_widget(r)

"""
Scanner QR Code v2.5 - Sans opencv, sans app specifique
Supporte :
  1. Lecteur physique (USB/Bluetooth) -> saisie clavier automatique
  2. N importe quelle app QR Android  -> intent generique
  3. Saisie manuelle                  -> toujours disponible
"""

import os, sys, threading
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from kivy.uix.boxlayout  import BoxLayout
from kivy.uix.label      import Label
from kivy.uix.button     import Button
from kivy.uix.textinput  import TextInput
from kivy.uix.popup      import Popup
from kivy.graphics       import Color, Rectangle
from kivy.utils          import get_color_from_hex
from kivy.metrics        import dp
from kivy.clock          import Clock


def est_android() -> bool:
    try:
        from jnius import autoclass; return True
    except ImportError: pass
    try:
        import android; return True
    except ImportError: pass
    return False


def valider_qr_colis(qr_data: str) -> tuple:
    if not qr_data: return False, ""
    numero = qr_data.strip().upper()
    if numero.startswith("FV-"):
        try:
            from modules.colis_manager import colis_manager
            c = colis_manager.get_colis_par_numero(numero)
            if c: return True, numero
        except Exception: pass
        return True, numero
    return False, numero


# ─── Android : intent QR generique (fonctionne avec toutes les apps) ─────────

def _scanner_android(callback_succes, callback_erreur):
    """
    Lance un intent QR generique. Android propose toutes les apps
    installees capables de scanner. Pas besoin d une app specifique.
    """
    try:
        from jnius import autoclass, PythonJavaClass, java_method

        Intent         = autoclass('android.content.Intent')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity       = PythonActivity.mActivity
        REQUEST_CODE   = 49374

        # Intent generique : Android proposera toutes les apps QR installees
        intent = Intent()
        intent.setAction("com.google.zxing.client.android.SCAN")
        intent.putExtra("SCAN_MODE", "QR_CODE_MODE")
        # Pas de setPackage() -> Android choisit ou propose un selecteur

        class ResultListener(PythonJavaClass):
            __javainterfaces__ = [
                'org/kivy/android/ActivityResultListener']

            @java_method('(IILandroid/content/Intent;)V')
            def onActivityResult(self, req, result, data):
                if req == REQUEST_CODE:
                    RESULT_OK = -1
                    if result == RESULT_OK and data:
                        contenu = data.getStringExtra('SCAN_RESULT')
                        if contenu:
                            Clock.schedule_once(
                                lambda dt, c=contenu:
                                callback_succes(c.strip()), 0)
                            return
                    Clock.schedule_once(
                        lambda dt: callback_erreur("annule"), 0)

        listener = ResultListener()
        activity.registerActivityResultListener(listener)

        # Essayer de lancer - si aucune app installee, proposer le Play Store
        try:
            activity.startActivityForResult(intent, REQUEST_CODE)
        except Exception:
            # Aucune app ne gere cet intent -> proposer d en installer une
            Clock.schedule_once(
                lambda dt: callback_erreur("aucune_app"), 0)

    except Exception as e:
        Clock.schedule_once(
            lambda dt, err=str(e): callback_erreur(err), 0)


# ─── Widget Scanner Universel ─────────────────────────────────────────────────

class ScannerWidget(BoxLayout):
    """
    Widget scanner QR :
    - Mode lecteur physique : champ texte avec focus permanent
    - Mode app Android     : lance un intent generique
    - Mode manuel          : saisie libre toujours disponible
    """

    def __init__(self, callback_succes, titre="Scanner QR",
                 cb_fermer=None, **kw):
        kw.setdefault('orientation', 'vertical')
        super().__init__(**kw)
        self.callback_succes = callback_succes
        self.cb_fermer       = cb_fermer
        self._sur_android    = est_android()
        self._build()

    def _build(self):
        # ── En-tete vert avec bouton fermer ──────────────────────────
        hdr = BoxLayout(size_hint_y=None, height=dp(48))
        with hdr.canvas.before:
            Color(*get_color_from_hex('#27AE60'))
            r = Rectangle(pos=hdr.pos, size=hdr.size)
        hdr.bind(pos=lambda w,v: setattr(r,'pos',v),
                 size=lambda w,v: setattr(r,'size',v))

        if self.cb_fermer:
            btn_fermer = Button(
                text='X Fermer',
                font_size=dp(11),
                size_hint=(None, None), size=(dp(90), dp(44)),
                background_color=get_color_from_hex('#C0392B'),
                background_normal='', color=(1,1,1,1))
            btn_fermer.bind(on_press=lambda a: self.cb_fermer())
            hdr.add_widget(btn_fermer)

        hdr.add_widget(Label(
            text='Scanner un QR code',
            font_size=dp(13), bold=True, color=(1,1,1,1)))
        self.add_widget(hdr)

        # ── Mode lecteur physique ─────────────────────────────────────
        sec1 = BoxLayout(orientation='vertical',
                         size_hint_y=None, height=dp(130),
                         padding=[dp(12), dp(8)], spacing=dp(6))
        with sec1.canvas.before:
            Color(*get_color_from_hex('#EAF6FF'))
            r1 = Rectangle(pos=sec1.pos, size=sec1.size)
        sec1.bind(pos=lambda w,v: setattr(r1,'pos',v),
                  size=lambda w,v: setattr(r1,'size',v))

        sec1.add_widget(Label(
            text='LECTEUR PHYSIQUE (USB/Bluetooth)',
            font_size=dp(11), bold=True,
            color=get_color_from_hex('#2C3E50'),
            size_hint_y=None, height=dp(22),
            halign='left'))
        sec1.add_widget(Label(
            text='Cliquez dans le champ ci-dessous puis\n'
                 'scannez avec votre lecteur. Le code s\'envoie automatiquement.',
            font_size=dp(10),
            color=get_color_from_hex('#7F8C8D'),
            size_hint_y=None, height=dp(36),
            halign='left'))

        self.champ_physique = TextInput(
            hint_text='Cliquez ici puis scannez avec le lecteur...',
            font_size=dp(13),
            multiline=False,
            size_hint_y=None, height=dp(42),
            background_color=(1,1,1,1),
            foreground_color=get_color_from_hex('#2C3E50'))
        self.champ_physique.bind(
            on_text_validate=self._valider_physique)
        sec1.add_widget(self.champ_physique)
        self.add_widget(sec1)

        # ── Mode app Android ──────────────────────────────────────────
        if self._sur_android:
            sec2 = BoxLayout(orientation='vertical',
                             size_hint_y=None, height=dp(120),
                             padding=[dp(12), dp(8)], spacing=dp(6))
            with sec2.canvas.before:
                Color(*get_color_from_hex('#EAFAF1'))
                r2 = Rectangle(pos=sec2.pos, size=sec2.size)
            sec2.bind(pos=lambda w,v: setattr(r2,'pos',v),
                      size=lambda w,v: setattr(r2,'size',v))

            sec2.add_widget(Label(
                text='APP CAMERA TELEPHONE',
                font_size=dp(11), bold=True,
                color=get_color_from_hex('#2C3E50'),
                size_hint_y=None, height=dp(22),
                halign='left'))
            sec2.add_widget(Label(
                text='Android proposera toutes vos apps\n'
                     'de scan installees (QR Scanner, etc.)',
                font_size=dp(10),
                color=get_color_from_hex('#7F8C8D'),
                size_hint_y=None, height=dp(34),
                halign='left'))

            self.btn_app = Button(
                text='Ouvrir le scanner camera',
                font_size=dp(12), bold=True,
                background_color=get_color_from_hex('#27AE60'),
                background_normal='', color=(1,1,1,1),
                size_hint_y=None, height=dp(42))
            self.btn_app.bind(on_press=self._lancer_app)
            sec2.add_widget(self.btn_app)
            self.add_widget(sec2)

        # ── Statut ────────────────────────────────────────────────────
        self.lbl_statut = Label(
            text='',
            font_size=dp(11), bold=True,
            color=get_color_from_hex('#F39C12'),
            size_hint_y=None, height=dp(0),
            halign='center')
        self.add_widget(self.lbl_statut)

        # ── Saisie manuelle ───────────────────────────────────────────
        sec3 = BoxLayout(orientation='vertical',
                         size_hint_y=None, height=dp(110),
                         padding=[dp(12), dp(8)], spacing=dp(6))
        with sec3.canvas.before:
            Color(*get_color_from_hex('#FDFEFE'))
            r3 = Rectangle(pos=sec3.pos, size=sec3.size)
        sec3.bind(pos=lambda w,v: setattr(r3,'pos',v),
                  size=lambda w,v: setattr(r3,'size',v))

        sec3.add_widget(Label(
            text='SAISIE MANUELLE',
            font_size=dp(11), bold=True,
            color=get_color_from_hex('#7F8C8D'),
            size_hint_y=None, height=dp(22),
            halign='left'))

        self.champ_manuel = TextInput(
            hint_text='Ex: FV-FVCOT-20260526-0001',
            font_size=dp(12), multiline=False,
            size_hint_y=None, height=dp(40),
            background_color=(1,1,1,1),
            foreground_color=get_color_from_hex('#2C3E50'))
        self.champ_manuel.bind(
            on_text_validate=lambda e: self._valider_manuel())
        sec3.add_widget(self.champ_manuel)

        btn_ok = Button(
            text='Valider la saisie',
            font_size=dp(12),
            background_color=get_color_from_hex('#2C3E50'),
            background_normal='', color=(1,1,1,1),
            size_hint_y=None, height=dp(38))
        btn_ok.bind(on_press=lambda a: self._valider_manuel())
        sec3.add_widget(btn_ok)
        self.add_widget(sec3)

        # Focus auto sur le champ physique
        Clock.schedule_once(
            lambda dt: setattr(self.champ_physique, 'focus', True), 0.3)

    def _valider_physique(self, instance):
        texte = instance.text.strip().upper()
        if texte:
            instance.text = ''
            self._traiter(texte)

    def _lancer_app(self, *a):
        self.btn_app.disabled = True
        self._set_statut('Lancement de l application scanner...', '#F39C12')
        _scanner_android(
            callback_succes=self._traiter,
            callback_erreur=self._sur_erreur_app)

    def _sur_erreur_app(self, msg: str):
        self.btn_app.disabled = False
        if msg == 'aucune_app':
            self._set_statut(
                'Aucune app scanner trouvee.\n'
                'Installez "QR & Barcode Scanner" sur le Play Store.',
                '#C0392B')
        elif msg == 'annule':
            self._set_statut('Scan annule.', '#F39C12')
        else:
            self._set_statut(
                'Erreur app. Utilisez le lecteur physique\n'
                'ou la saisie manuelle.', '#F39C12')

    def _valider_manuel(self):
        texte = self.champ_manuel.text.strip().upper()
        if not texte:
            self._set_statut('Veuillez saisir un numero.', '#C0392B')
            return
        self.champ_manuel.text = ''
        self._traiter(texte)

    def _traiter(self, qr_data: str):
        valide, numero = valider_qr_colis(qr_data)
        if valide:
            self._set_statut(f'Colis detecte : {numero}', '#27AE60')
            Clock.schedule_once(
                lambda dt: self.callback_succes(numero), 0.2)
        else:
            self._set_statut(
                f'Code non reconnu : {qr_data}\n'
                f'Reessayez ou saisissez manuellement.', '#C0392B')

    def _set_statut(self, msg: str, couleur: str):
        self.lbl_statut.text   = msg
        self.lbl_statut.color  = get_color_from_hex(couleur)
        self.lbl_statut.height = dp(44) if msg else dp(0)


def ouvrir_scanner(titre: str, callback_succes) -> Popup:
    """Ouvre le scanner dans un popup avec bouton Fermer."""
    popup_ref = [None]

    def _fermer():
        if popup_ref[0]:
            popup_ref[0].dismiss()

    def _succes(numero: str):
        if popup_ref[0]:
            popup_ref[0].dismiss()
        callback_succes(numero)

    widget = ScannerWidget(
        callback_succes=_succes,
        titre=titre,
        cb_fermer=_fermer)

    popup = Popup(
        title=titre,
        content=widget,
        size_hint=(0.95, 0.88),
        auto_dismiss=False)

    popup_ref[0] = popup
    popup.open()
    return popup

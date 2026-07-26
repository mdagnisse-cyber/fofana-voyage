"""
Scanner QR Code v3.0 - Camera integree (lecture directe, sans appli tierce)
Supporte :
  1. Camera du telephone/PC (lecture QR en direct)       <- mode principal
  2. Lecteur physique (USB/Bluetooth) -> saisie clavier automatique
  3. Saisie manuelle                  -> toujours disponible
"""

import os, sys
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


# ─── Camera : lecture QR en direct (telephone ou PC) ─────────────────────────

class CameraScanWidget(BoxLayout):
    """
    Affiche le flux de la camera et decode les QR codes automatiquement,
    plusieurs fois par seconde, sans que l'utilisateur ait besoin de
    cliquer sur quoi que ce soit.
    """

    INTERVALLE = 0.35  # secondes entre deux analyses d'image

    def __init__(self, callback_succes, **kw):
        kw.setdefault('orientation', 'vertical')
        super().__init__(**kw)
        self.callback_succes = callback_succes
        self._actif          = True
        self._derniere_lecture = None
        self._event           = None
        self.camera           = None
        self._detecteur       = None
        self._build()

    def _build(self):
        try:
            from kivy.uix.camera import Camera
            import cv2
            self._detecteur = cv2.QRCodeDetector()

            self.camera = Camera(play=True, resolution=(640, 480))
            self.add_widget(self.camera)

            self.lbl_aide = Label(
                text='Visez le QR code du colis avec la camera...',
                font_size=dp(11),
                color=get_color_from_hex('#7F8C8D'),
                size_hint_y=None, height=dp(30))
            self.add_widget(self.lbl_aide)

            self._event = Clock.schedule_interval(self._analyser, self.INTERVALLE)

        except Exception as e:
            self.camera = None
            self.add_widget(Label(
                text=f'Camera indisponible sur cet appareil.\n({e})\n'
                     f'Utilisez le lecteur physique ou la saisie manuelle ci-dessous.',
                font_size=dp(11),
                color=get_color_from_hex('#C0392B'),
                size_hint_y=None, height=dp(70),
                halign='center'))

    def _analyser(self, dt):
        if not self._actif or not self.camera or not self.camera.texture:
            return
        try:
            import cv2
            import numpy as np

            tex    = self.camera.texture
            largeur, hauteur = tex.size
            canaux = {'rgba': 4, 'rgb': 3, 'luminance': 1, 'bgr': 3}.get(tex.colorfmt, 4)

            arr = np.frombuffer(tex.pixels, dtype=np.uint8)
            arr = arr.reshape(hauteur, largeur, canaux)
            arr = np.flipud(arr)  # la texture Kivy est inversee verticalement

            if canaux == 4:
                gris = cv2.cvtColor(arr, cv2.COLOR_RGBA2GRAY)
            elif canaux == 3:
                gris = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
            else:
                gris = arr[:, :, 0]

            data, points, _ = self._detecteur.detectAndDecode(gris)

            if data:
                data = data.strip()
                if data != self._derniere_lecture:
                    self._derniere_lecture = data
                    self._arreter()
                    self.callback_succes(data)

        except ModuleNotFoundError:
            # opencv absent (ne devrait pas arriver si buildozer.spec est a jour)
            self._arreter()
            self.lbl_aide.text  = "Module de lecture QR manquant sur cet appareil."
            self.lbl_aide.color = get_color_from_hex('#C0392B')
        except Exception:
            pass  # image transitoire non decodable, on reessaie a la prochaine frame

    def _arreter(self):
        self._actif = False
        if self._event:
            self._event.cancel()
        if self.camera:
            try:
                self.camera.play = False
            except Exception:
                pass


# ─── Widget Scanner Universel ─────────────────────────────────────────────────

class ScannerWidget(BoxLayout):
    """
    Widget scanner QR :
    - Camera en direct   : lecture automatique (mode principal)
    - Lecteur physique   : champ texte avec focus permanent
    - Mode manuel        : saisie libre toujours disponible
    """

    def __init__(self, callback_succes, titre="Scanner QR",
                 cb_fermer=None, **kw):
        kw.setdefault('orientation', 'vertical')
        super().__init__(**kw)
        self.callback_succes = callback_succes
        self.cb_fermer       = cb_fermer
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
            btn_fermer.bind(on_press=lambda a: self._fermer())
            hdr.add_widget(btn_fermer)

        hdr.add_widget(Label(
            text='Scanner un QR code',
            font_size=dp(13), bold=True, color=(1,1,1,1)))
        self.add_widget(hdr)

        # ── Camera en direct (mode principal) ─────────────────────────
        cam_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(300))
        self.cam_widget = CameraScanWidget(callback_succes=self._traiter)
        cam_box.add_widget(self.cam_widget)
        self.add_widget(cam_box)

        # ── Statut ────────────────────────────────────────────────────
        self.lbl_statut = Label(
            text='',
            font_size=dp(11), bold=True,
            color=get_color_from_hex('#F39C12'),
            size_hint_y=None, height=dp(0),
            halign='center')
        self.add_widget(self.lbl_statut)

        # ── Mode lecteur physique ─────────────────────────────────────
        sec1 = BoxLayout(orientation='vertical',
                         size_hint_y=None, height=dp(96),
                         padding=[dp(12), dp(6)], spacing=dp(4))
        with sec1.canvas.before:
            Color(*get_color_from_hex('#EAF6FF'))
            r1 = Rectangle(pos=sec1.pos, size=sec1.size)
        sec1.bind(pos=lambda w,v: setattr(r1,'pos',v),
                  size=lambda w,v: setattr(r1,'size',v))

        sec1.add_widget(Label(
            text='LECTEUR PHYSIQUE (USB/Bluetooth) - optionnel',
            font_size=dp(10), bold=True,
            color=get_color_from_hex('#2C3E50'),
            size_hint_y=None, height=dp(20),
            halign='left'))

        self.champ_physique = TextInput(
            hint_text='Cliquez ici puis scannez avec le lecteur...',
            font_size=dp(12),
            multiline=False,
            size_hint_y=None, height=dp(40),
            background_color=(1,1,1,1),
            foreground_color=get_color_from_hex('#2C3E50'))
        self.champ_physique.bind(
            on_text_validate=self._valider_physique)
        sec1.add_widget(self.champ_physique)
        self.add_widget(sec1)

        # ── Saisie manuelle ───────────────────────────────────────────
        sec3 = BoxLayout(orientation='vertical',
                         size_hint_y=None, height=dp(100),
                         padding=[dp(12), dp(6)], spacing=dp(4))
        with sec3.canvas.before:
            Color(*get_color_from_hex('#FDFEFE'))
            r3 = Rectangle(pos=sec3.pos, size=sec3.size)
        sec3.bind(pos=lambda w,v: setattr(r3,'pos',v),
                  size=lambda w,v: setattr(r3,'size',v))

        sec3.add_widget(Label(
            text='SAISIE MANUELLE (si la camera ne fonctionne pas)',
            font_size=dp(10), bold=True,
            color=get_color_from_hex('#7F8C8D'),
            size_hint_y=None, height=dp(20),
            halign='left'))

        self.champ_manuel = TextInput(
            hint_text='Ex: FV-FVCOT-20260526-0001',
            font_size=dp(12), multiline=False,
            size_hint_y=None, height=dp(38),
            background_color=(1,1,1,1),
            foreground_color=get_color_from_hex('#2C3E50'))
        self.champ_manuel.bind(
            on_text_validate=lambda e: self._valider_manuel())
        sec3.add_widget(self.champ_manuel)

        btn_ok = Button(
            text='Valider la saisie',
            font_size=dp(11),
            background_color=get_color_from_hex('#2C3E50'),
            background_normal='', color=(1,1,1,1),
            size_hint_y=None, height=dp(34))
        btn_ok.bind(on_press=lambda a: self._valider_manuel())
        sec3.add_widget(btn_ok)
        self.add_widget(sec3)

        # Focus auto sur le champ physique (pour lecteurs USB/BT)
        Clock.schedule_once(
            lambda dt: setattr(self.champ_physique, 'focus', True), 0.3)

    def _valider_physique(self, instance):
        texte = instance.text.strip().upper()
        if texte:
            instance.text = ''
            self._traiter(texte)

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

    def _fermer(self):
        if self.cam_widget:
            self.cam_widget._arreter()
        if self.cb_fermer:
            self.cb_fermer()


def ouvrir_scanner(titre: str, callback_succes) -> Popup:
    """Ouvre le scanner (camera + lecteur physique + saisie manuelle) dans un popup."""
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
        size_hint=(0.95, 0.92),
        auto_dismiss=False)

    def _on_dismiss(*a):
        widget._fermer()

    popup.bind(on_dismiss=_on_dismiss)
    popup_ref[0] = popup
    popup.open()
    return popup

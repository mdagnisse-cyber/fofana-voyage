"""
Point d'entrée — Fofana Voyage Colis Manager (Kivy)
Compatible Pydroid 3 / Android
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# ── 1. Base de données ──────────────────────────────────────────────
print("=" * 50)
print("  FOFANA VOYAGE — Gestion des Colis v2.0")
print("=" * 50)
print("\n[1/2] Initialisation base de donnees...")
from database.db_manager import init_database, seed_initial_data
init_database()
seed_initial_data()
print("      OK\n")
print("[2/2] Lancement interface...")

# ── 2. Kivy config AVANT tout import kivy ──────────────────────────
os.environ['KIVY_NO_ENV_CONFIG'] = '1'
from kivy.config import Config
Config.set('graphics', 'width',  '400')
Config.set('graphics', 'height', '700')
Config.set('kivy', 'keyboard_mode', 'system')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.core.window import Window
from kivy.utils import get_color_from_hex

Window.clearcolor = get_color_from_hex("#F5F5F5")

from ui.login_screen import LoginScreen
from ui.main_screen  import MainScreen


class FofanaApp(App):
    title = "Fofana Voyage"

    def build(self):
        self.sm = ScreenManager(transition=SlideTransition())
        self.sm.add_widget(LoginScreen(name='login'))
        self.sm.add_widget(MainScreen(name='main'))
        self.sm.current = 'login'
        return self.sm


if __name__ == '__main__':
    FofanaApp().run()

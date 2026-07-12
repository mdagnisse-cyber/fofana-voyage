"""Page Rapports simplifiée - Kivy (tableaux texte)"""
from kivy.uix.boxlayout  import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label      import Label
from kivy.uix.button     import Button
from kivy.graphics       import Color, Rectangle
from kivy.utils          import get_color_from_hex
from kivy.metrics        import dp
from datetime            import datetime, timedelta
from database.db_manager import get_connection
from modules.auth_manager import auth
from config.config        import STATUTS
from ui.widgets import SectionHeader, BoutonPrimaire, Separateur

class RapportsPage(BoxLayout):
    def __init__(self, **kw):
        kw.setdefault('orientation', 'vertical')
        super().__init__(**kw)
        self._build()

    def _build(self):
        self.add_widget(SectionHeader("[RAP]  Rapports & Statistiques","#2C3E50"))

        # Filtres période
        filtres = BoxLayout(size_hint_y=None, height=dp(42),
                            padding=[dp(8),dp(4)], spacing=dp(6))
        self._periode = "30j"
        for lb, val in [("Auj.","auj"),("7j","7j"),("30j","30j"),("Tout","tout")]:
            btn = Button(text=lb, font_size=dp(11),
                background_color=get_color_from_hex(
                    "#C0392B" if val==self._periode else "#BDC3C7"),
                background_normal='', color=(1,1,1,1),
                size_hint_y=None, height=dp(36),
            )
            btn.bind(on_press=lambda a, v=val: self._changer_periode(v))
            filtres.add_widget(btn)
        self.add_widget(filtres)
        self.btn_filtres = filtres

        self.scroll = ScrollView(do_scroll_x=False)
        self.body   = BoxLayout(orientation='vertical', size_hint_y=None,
                                padding=dp(12), spacing=dp(10))
        self.body.bind(minimum_height=self.body.setter('height'))
        self.scroll.add_widget(self.body)
        self.add_widget(self.scroll)
        self._afficher()

    def _changer_periode(self, val):
        self._periode = val
        self._afficher()

    def _get_dates(self):
        fin = datetime.now().strftime("%Y-%m-%d")
        deltas = {"auj":0,"7j":7,"30j":30,"tout":3650}
        debut  = (datetime.now()-timedelta(days=deltas.get(self._periode,30))).strftime("%Y-%m-%d")
        return debut, fin

    def _stats(self):
        debut, fin = self._get_dates()
        s = {}
        try:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("""SELECT statut, COUNT(*) n, SUM(frais_total) ca
                FROM colis WHERE date(date_depot) BETWEEN date(?) AND date(?)
                GROUP BY statut""", (debut, fin))
            s['par_statut'] = {r['statut']:{'n':r['n'],'ca':r['ca'] or 0}
                               for r in cur.fetchall()}
            cur.execute("""SELECT COUNT(*) n, SUM(frais_total) ca
                FROM colis WHERE date(date_depot) BETWEEN date(?) AND date(?)""",
                (debut, fin))
            row = cur.fetchone()
            s['total'] = row['n'] or 0
            s['ca']    = row['ca'] or 0
            cur.execute("SELECT COUNT(*) FROM alertes WHERE resolue=0")
            s['alertes'] = cur.fetchone()[0]
            conn.close()
        except Exception: pass
        return s

    def _afficher(self):
        self.body.clear_widgets()
        s = self._stats()

        # KPIs
        kpis = [
            ("[COL] Total colis",     s.get('total',0),      "#2C3E50"),
            ("[CA] CA total",        f"{s.get('ca',0):,.0f} F","#27AE60"),
            ("[ALE] Alertes actives", s.get('alertes',0),     "#C0392B"),
        ]
        for lb, val, hc in kpis:
            row = BoxLayout(size_hint_y=None, height=dp(44),
                            padding=[dp(12),dp(4)])
            with row.canvas.before:
                Color(*get_color_from_hex("#FFFFFF"))
                r = Rectangle(pos=row.pos, size=row.size)
            row.bind(pos=lambda w,v,rr=r: setattr(rr,'pos',v),
                     size=lambda w,v,rr=r: setattr(rr,'size',v))
            row.add_widget(Label(text=lb, font_size=dp(12), bold=True,
                color=get_color_from_hex("#2C3E50"), halign='left'))
            row.add_widget(Label(text=str(val), font_size=dp(14), bold=True,
                color=get_color_from_hex(hc), halign='right'))
            self.body.add_widget(row)

        self.body.add_widget(Separateur())
        self.body.add_widget(SectionHeader("Par statut","#2C3E50"))

        total_n = s.get('total',1) or 1
        for statut, info in s.get('par_statut',{}).items():
            txt_s, hex_s = STATUTS.get(statut,(statut,"#95A5A6"))
            row = BoxLayout(size_hint_y=None, height=dp(40),
                            padding=[dp(8),dp(4)], spacing=dp(8))
            badge = Label(text=f" {txt_s} ", font_size=dp(9), bold=True,
                color=(1,1,1,1), size_hint=(None,None), size=(dp(80),dp(24)))
            with badge.canvas.before:
                Color(*get_color_from_hex(hex_s))
                rb = Rectangle(pos=badge.pos, size=badge.size)
            badge.bind(pos=lambda w,v,r=rb: setattr(r,'pos',v),
                       size=lambda w,v,r=rb: setattr(r,'size',v))
            row.add_widget(badge)
            row.add_widget(Label(text=f"{info['n']} colis",
                font_size=dp(12), color=get_color_from_hex("#2C3E50")))
            row.add_widget(Label(text=f"{info['ca']:,.0f} F",
                font_size=dp(12), color=get_color_from_hex("#27AE60"),
                halign='right'))
            row.add_widget(Label(
                text=f"{info['n']*100//total_n}%",
                font_size=dp(11), color=get_color_from_hex("#7F8C8D"),
                size_hint_x=None, width=dp(36),
            ))
            self.body.add_widget(row)
            self.body.add_widget(Separateur())

        # Bouton export PDF
        btn_pdf = BoutonPrimaire(text="[PDF]  Exporter rapport PDF")
        btn_pdf.bind(on_press=self._exporter)
        self.body.add_widget(btn_pdf)

    def _exporter(self, *a):
        try:
            from utils.pdf_generator import generer_recu_retrait
            # Rapport simplifié en PDF
            pass
        except Exception as e:
            pass

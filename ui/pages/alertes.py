"""Page Alertes - Kivy"""
from kivy.uix.boxlayout  import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label      import Label
from kivy.uix.button     import Button
from kivy.graphics       import Color, Rectangle
from kivy.utils          import get_color_from_hex
from kivy.metrics        import dp
from database.db_manager import get_connection
from modules.auth_manager import auth
from ui.widgets import SectionHeader, BoutonPrimaire, Separateur
from ui.notif import toast

TYPE_ALERTES = {
    "NON_RETIRE": ("[RET+]", "#F39C12", "Non retiré"),
    "LITIGE":     ("[LIT]",  "#8E44AD", "Litige"),
    "ANOMALIE":   ("[!]",  "#E67E22", "Anomalie"),
    "PERTE":      ("[X]",  "#C0392B", "Perte"),
}

class AlertesPage(BoxLayout):
    def __init__(self, **kw):
        kw.setdefault('orientation', 'vertical')
        super().__init__(**kw)
        self._gen_alertes_auto()
        self._build()

    def _gen_alertes_auto(self):
        try:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("""
                SELECT id, numero FROM colis
                WHERE statut='ARRIVE'
                AND date_arrivee_reelle IS NOT NULL
                AND julianday('now','localtime')-julianday(date_arrivee_reelle)>7
                AND id NOT IN (
                    SELECT colis_id FROM alertes
                    WHERE type_alerte='NON_RETIRE' AND resolue=0)
            """)
            for c in cur.fetchall():
                cur.execute("""INSERT INTO alertes (colis_id,type_alerte,message)
                    VALUES(?,'NON_RETIRE',?)""",
                    (c['id'], f"Colis {c['numero']} non retiré depuis +7 jours"))
            conn.commit(); conn.close()
        except Exception: pass

    def _build(self):
        self.add_widget(SectionHeader("[ALE]  Alertes actives", "#C0392B"))
        btn_refresh = BoutonPrimaire(text="[MAJ] Actualiser",
            size_hint_y=None, height=dp(38))
        btn_refresh.bind(on_press=lambda a: self._recharger())
        self.add_widget(btn_refresh)

        self.scroll = ScrollView(do_scroll_x=False)
        self.frame  = BoxLayout(orientation='vertical', spacing=dp(6),
                                size_hint_y=None, padding=[dp(8),dp(6)])
        self.frame.bind(minimum_height=self.frame.setter('height'))
        self.scroll.add_widget(self.frame)
        self.add_widget(self.scroll)
        self._recharger()

    def _recharger(self):
        self.frame.clear_widgets()
        try:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("""
                SELECT a.id, a.type_alerte, a.message, a.created_at,
                       c.numero,
                       cd.nom||' '||cd.prenom AS dest,
                       cd.telephone AS dest_tel
                FROM alertes a
                JOIN colis c ON a.colis_id=c.id
                JOIN clients cd ON c.destinataire_id=cd.id
                WHERE a.resolue=0
                ORDER BY a.created_at DESC
            """)
            alertes = [dict(r) for r in cur.fetchall()]
            conn.close()
        except Exception: alertes = []

        if not alertes:
            self.frame.add_widget(Label(
                text="[RET]  Aucune alerte active !",
                font_size=dp(14), color=get_color_from_hex("#27AE60"),
                size_hint_y=None, height=dp(60),
            ))
            return

        self.frame.add_widget(Label(
            text=f"[!]  {len(alertes)} alerte(s) non résolue(s)",
            font_size=dp(12), bold=True,
            color=get_color_from_hex("#C0392B"),
            size_hint_y=None, height=dp(30),
        ))

        for al in alertes:
            ic, hc, lb = TYPE_ALERTES.get(al['type_alerte'],
                                           ("[ALE]","#F39C12","Alerte"))
            card = BoxLayout(orientation='horizontal',
                             size_hint_y=None, height=dp(72),
                             padding=[0, dp(4)])

            # Barre gauche colorée
            barre = BoxLayout(size_hint_x=None, width=dp(6))
            with barre.canvas.before:
                Color(*get_color_from_hex(hc))
                r = Rectangle(pos=barre.pos, size=barre.size)
            barre.bind(pos=lambda w,v,rr=r: setattr(rr,'pos',v),
                       size=lambda w,v,rr=r: setattr(rr,'size',v))
            card.add_widget(barre)

            info = BoxLayout(orientation='vertical',
                             padding=[dp(8), dp(4)], spacing=dp(2))
            info.add_widget(Label(
                text=f"{ic} {lb}  -  Colis {al['numero']}",
                font_size=dp(11), bold=True,
                color=get_color_from_hex(hc), halign='left',
                size_hint_y=None, height=dp(22),
            ))
            info.add_widget(Label(
                text=al['message'][:50],
                font_size=dp(10), color=get_color_from_hex("#2C3E50"),
                halign='left', size_hint_y=None, height=dp(18),
            ))
            info.add_widget(Label(
                text=f"Dest: {al['dest']}  |  {al['dest_tel']}",
                font_size=dp(9), color=get_color_from_hex("#7F8C8D"),
                halign='left', size_hint_y=None, height=dp(16),
            ))
            card.add_widget(info)

            btn = Button(text="OK", font_size=dp(16),
                background_color=get_color_from_hex("#27AE60"),
                background_normal='', color=(1,1,1,1),
                size_hint=(None, None), size=(dp(44), dp(44)),
            )
            btn.bind(on_press=lambda a, aid=al['id']:
                     self._resoudre(aid))
            card.add_widget(btn)

            self.frame.add_widget(card)
            self.frame.add_widget(Separateur())

    def _resoudre(self, alerte_id):
        try:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("""UPDATE alertes SET resolue=1, resolue_par=?,
                resolue_at=datetime('now','localtime') WHERE id=?""",
                (auth.user_id, alerte_id))
            conn.commit(); conn.close()
            self._recharger()
        except Exception: pass

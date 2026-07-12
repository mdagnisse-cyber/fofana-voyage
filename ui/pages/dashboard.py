"""Dashboard - Kivy"""

from kivy.uix.boxlayout  import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label      import Label
from kivy.uix.scrollview import ScrollView
from kivy.graphics       import Color, Rectangle
from kivy.utils          import get_color_from_hex
from kivy.metrics        import dp
from datetime            import datetime

from database.db_manager import get_connection
from modules.auth_manager import auth
from config.config        import STATUTS
from ui.widgets           import Card, SectionHeader, Separateur


def _kpi_card(icone, valeur, label, hex_c):
    card = BoxLayout(orientation='vertical',
                     padding=dp(10), spacing=dp(4))
    with card.canvas.before:
        Color(*get_color_from_hex("#FFFFFF"))
        r = Rectangle(pos=card.pos, size=card.size)
    card.bind(pos=lambda w, v: setattr(r, 'pos', v),
              size=lambda w, v: setattr(r, 'size', v))

    # Barre couleur haut
    barre = BoxLayout(size_hint_y=None, height=dp(5))
    with barre.canvas.before:
        Color(*get_color_from_hex(hex_c))
        rb = Rectangle(pos=barre.pos, size=barre.size)
    barre.bind(pos=lambda w, v: setattr(rb, 'pos', v),
               size=lambda w, v: setattr(rb, 'size', v))
    card.add_widget(barre)

    card.add_widget(Label(
        text=str(icone), font_size=dp(22),
        size_hint_y=None, height=dp(30)))
    card.add_widget(Label(
        text=str(valeur), font_size=dp(20), bold=True,
        color=get_color_from_hex(hex_c),
        size_hint_y=None, height=dp(28)))
    card.add_widget(Label(
        text=label, font_size=dp(9),
        color=get_color_from_hex("#7F8C8D"),
        size_hint_y=None, height=dp(18)))
    return card


class DashboardPage(BoxLayout):

    def __init__(self, **kw):
        kw.setdefault('orientation', 'vertical')
        super().__init__(**kw)
        self._build()

    def _build(self):
        scroll = ScrollView(do_scroll_x=False)
        contenu = BoxLayout(
            orientation='vertical',
            padding=dp(12), spacing=dp(12),
            size_hint_y=None,
        )
        contenu.bind(minimum_height=contenu.setter('height'))

        user = auth.utilisateur
        prenom = user['prenom'] if user else ''

        # Salutation
        contenu.add_widget(Label(
            text=f"Bonjour, {prenom} ",
            font_size=dp(16), bold=True,
            color=get_color_from_hex("#2C3E50"),
            size_hint_y=None, height=dp(32),
            halign='left',
        ))
        contenu.add_widget(Label(
            text=datetime.now().strftime("%A %d %B %Y"),
            font_size=dp(11),
            color=get_color_from_hex("#7F8C8D"),
            size_hint_y=None, height=dp(22),
            halign='left',
        ))

        contenu.add_widget(Separateur())

        # KPIs
        stats = self._stats()
        kpis = [
            ("[COL]", stats["total"],      "Total colis",    "#2C3E50"),
            ("[ATT]", stats["en_attente"], "En attente",     "#F39C12"),
            ("[TRNS]", stats["transit"],    "En transit",     "#3498DB"),
            ("[RET]", stats["a_retirer"], "À retirer",      "#27AE60"),
            ("[DEST]", stats["retires"],    "Retirés auj.",   "#9B59B6"),
            ("[ALE]", stats["alertes"],   "Alertes",        "#C0392B"),
        ]

        grille = GridLayout(
            cols=3, spacing=dp(8),
            size_hint_y=None,
            height=dp(210),
        )
        for ic, val, lb, hc in kpis:
            grille.add_widget(_kpi_card(ic, val, lb, hc))
        contenu.add_widget(grille)

        contenu.add_widget(Separateur())

        # Derniers colis
        contenu.add_widget(SectionHeader(
            "[LIST]  Derniers colis enregistrés", "#2C3E50"))

        derniers = self._derniers_colis()
        if not derniers:
            contenu.add_widget(Label(
                text="Aucun colis enregistré.",
                font_size=dp(12),
                color=get_color_from_hex("#7F8C8D"),
                size_hint_y=None, height=dp(40),
            ))
        else:
            for colis in derniers:
                row = BoxLayout(
                    orientation='horizontal',
                    size_hint_y=None, height=dp(54),
                    padding=[dp(8), dp(4)], spacing=dp(8),
                )
                with row.canvas.before:
                    Color(*get_color_from_hex("#FAFAFA"))
                    rr = Rectangle(pos=row.pos, size=row.size)
                row.bind(pos=lambda w, v, r=rr: setattr(r, 'pos', v),
                         size=lambda w, v, r=rr: setattr(r, 'size', v))

                # Infos
                info = BoxLayout(orientation='vertical')
                info.add_widget(Label(
                    text=colis['numero'],
                    font_size=dp(11), bold=True,
                    color=get_color_from_hex("#C0392B"),
                    halign='left',
                ))
                info.add_widget(Label(
                    text=f"{colis['dest']}  |  {colis['ville']}",
                    font_size=dp(10),
                    color=get_color_from_hex("#7F8C8D"),
                    halign='left',
                ))
                row.add_widget(info)

                # Badge statut
                txt_s, hex_s = STATUTS.get(
                    colis['statut'], (colis['statut'], "#95A5A6"))
                badge = Label(
                    text=f" {txt_s} ",
                    font_size=dp(9), bold=True,
                    color=(1, 1, 1, 1),
                    size_hint=(None, None),
                    size=(dp(80), dp(24)),
                )
                with badge.canvas.before:
                    Color(*get_color_from_hex(hex_s))
                    rb2 = Rectangle(pos=badge.pos, size=badge.size)
                badge.bind(pos=lambda w, v, r=rb2: setattr(r, 'pos', v),
                           size=lambda w, v, r=rb2: setattr(r, 'size', v))
                row.add_widget(badge)

                contenu.add_widget(row)
                contenu.add_widget(Separateur())

        scroll.add_widget(contenu)
        self.add_widget(scroll)

    def _stats(self) -> dict:
        s = dict(total=0, en_attente=0, transit=0,
                 a_retirer=0, retires=0, alertes=0)
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM colis")
            s["total"] = cur.fetchone()[0]
            for statut, cle in [
                ("DEPOSE", "en_attente"),
                ("EN_TRANSIT", "transit"),
                ("ARRIVE", "a_retirer"),
            ]:
                cur.execute(
                    "SELECT COUNT(*) FROM colis WHERE statut=?",
                    (statut,))
                s[cle] = cur.fetchone()[0]
            cur.execute("""
                SELECT COUNT(*) FROM colis WHERE statut='RETIRE'
                AND date(date_retrait)=date('now','localtime')
            """)
            s["retires"] = cur.fetchone()[0]
            cur.execute(
                "SELECT COUNT(*) FROM alertes WHERE resolue=0")
            s["alertes"] = cur.fetchone()[0]
            conn.close()
        except Exception:
            pass
        return s

    def _derniers_colis(self) -> list:
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("""
                SELECT c.numero, c.statut,
                       cd.nom||' '||cd.prenom AS dest,
                       aa.ville
                FROM colis c
                JOIN clients cd ON c.destinataire_id=cd.id
                JOIN agences aa ON c.agence_arrivee_id=aa.id
                ORDER BY c.created_at DESC LIMIT 6
            """)
            res = [dict(r) for r in cur.fetchall()]
            conn.close()
            return res
        except Exception:
            return []

"""
Configuration globale — Fofana Voyage Colis Manager (Kivy)
"""

APP_NAME    = "Fofana Voyage — Colis"
APP_VERSION = "2.0.0"

# Couleurs Kivy : format (R, G, B, A) entre 0 et 1
def hex_to_kivy(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16)/255 for i in (0,2,4)) + (1,)

COLORS = {
    "primary":       hex_to_kivy("#C0392B"),
    "primary_dark":  hex_to_kivy("#922B21"),
    "secondary":     hex_to_kivy("#2C3E50"),
    "success":       hex_to_kivy("#27AE60"),
    "warning":       hex_to_kivy("#F39C12"),
    "danger":        hex_to_kivy("#C0392B"),
    "accent":        hex_to_kivy("#F39C12"),
    "bg_gray":       hex_to_kivy("#F5F5F5"),
    "bg_white":      hex_to_kivy("#FFFFFF"),
    "text_dark":     hex_to_kivy("#2C3E50"),
    "text_gray":     hex_to_kivy("#7F8C8D"),
    "text_light":    hex_to_kivy("#FFFFFF"),
    "border":        hex_to_kivy("#BDC3C7"),
    "sidebar":       hex_to_kivy("#2C3E50"),
    "sidebar_hover": hex_to_kivy("#34495E"),
    "blue":          hex_to_kivy("#3498DB"),
    "purple":        hex_to_kivy("#8E44AD"),
}

# Statuts des colis
STATUTS = {
    "DEPOSE":     ("Déposé",      "#F39C12"),
    "EN_TRANSIT": ("En transit",  "#3498DB"),
    "ARRIVE":     ("Arrivé",      "#27AE60"),
    "RETIRE":     ("Retiré",      "#95A5A6"),
    "PERDU":      ("Perdu",       "#C0392B"),
    "LITIGE":     ("En litige",   "#8E44AD"),
}

# Rôles
ROLES = {
    "ADMIN":   "Administrateur",
    "AGENT":   "Agent",
    "MANAGER": "Manager",
}

# Accès par rôle
ACCES_ROLES = {
    "dashboard":  ["ADMIN","MANAGER","AGENT"],
    "depot":      ["ADMIN","MANAGER","AGENT"],
    "suivi":      ["ADMIN","MANAGER","AGENT"],
    "retrait":    ["ADMIN","MANAGER","AGENT"],
    "alertes":    ["ADMIN","MANAGER","AGENT"],
    "rapports":   ["ADMIN","MANAGER"],
    "agents":     ["ADMIN"],
    "agences":    ["ADMIN","MANAGER"],
    "parametres": ["ADMIN"],
    "fichiers":   ["ADMIN","MANAGER","AGENT"],
    "scan":       ["ADMIN","MANAGER","AGENT"],
}

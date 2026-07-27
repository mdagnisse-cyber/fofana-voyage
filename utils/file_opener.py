"""
Ouverture automatique de fichiers - Fofana Voyage
Ouvre un PDF (ou autre fichier) avec l'application par defaut du systeme.
Ne plante jamais : en cas d'echec, retourne un message informatif
avec l'emplacement du fichier au lieu de faire planter l'application.
"""

import os
from kivy.utils import platform


def ouvrir_fichier(chemin: str) -> tuple:
    """
    Ouvre un fichier avec le lecteur/l'application par defaut du systeme
    (l'utilisateur peut ensuite l'imprimer depuis cette application).
    Retourne (succes: bool, message: str).
    """
    if not chemin or not os.path.exists(chemin):
        return False, "Fichier introuvable."

    try:
        if platform == 'android':
            from jnius import autoclass
            Intent         = autoclass('android.content.Intent')
            FileProvider   = autoclass('androidx.core.content.FileProvider')
            File           = autoclass('java.io.File')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')

            activite  = PythonActivity.mActivity
            fichier   = File(chemin)
            autorite  = activite.getPackageName() + ".fileprovider"
            uri       = FileProvider.getUriForFile(activite, autorite, fichier)

            intent = Intent(Intent.ACTION_VIEW)
            intent.setDataAndType(uri, "application/pdf")
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            activite.startActivity(intent)
            return True, "Ouverture du document..."

        elif platform == 'win':
            os.startfile(chemin)
            return True, "Ouverture du document..."

        elif platform in ('linux', 'macosx'):
            import subprocess
            opener = 'open' if platform == 'macosx' else 'xdg-open'
            subprocess.Popen([opener, chemin])
            return True, "Ouverture du document..."

        else:
            return False, f"Document enregistré : {chemin}"

    except Exception:
        # Ne jamais planter l'appli : on retombe sur un message informatif
        return False, f"Document enregistré ici : {chemin}"

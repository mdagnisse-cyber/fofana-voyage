"""
SMS Manager v2.5 - Envoi automatique via Africa's Talking en priorite
Cascade : Africa's Talking -> Android SMS -> TextBelt -> Manuel
"""

import os, sys, json
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)


def _config() -> dict:
    try:
        from database.db_manager import select
        rows = select("parametres", filters={"cle": "like.sms_*"},
                      select_cols="cle,valeur")
        return {r['cle']: r['valeur'] for r in rows}
    except Exception:
        return {}


def _format_tel(telephone: str) -> str:
    """Formate le numero en international +229XXXXXXXX."""
    tel = telephone.strip().replace(' ','').replace('-','').replace('.','')
    if tel.startswith('00'):
        tel = '+' + tel[2:]
    if not tel.startswith('+'):
        if tel.startswith('229'):
            tel = '+' + tel
        else:
            tel = '+229' + tel
    return tel


# ── Africa's Talking ─────────────────────────────────────────────────────────

def _at_send(telephone: str, message: str, cfg: dict) -> tuple:
    try:
        import urllib.request, urllib.parse
        username = cfg.get('sms_at_username', '').strip()
        api_key  = cfg.get('sms_at_apikey',  '').strip()

        if not username or not api_key:
            return False, "Cle API Africa's Talking non configuree"

        url = ("https://api.sandbox.africastalking.com/version1/messaging"
               if username == 'sandbox'
               else "https://api.africastalking.com/version1/messaging")

        data = urllib.parse.urlencode({
            'username': username,
            'to':       _format_tel(telephone),
            'message':  message,
            'from':     cfg.get('sms_sender_id', 'FofanaVoy'),
        }).encode('utf-8')

        req = urllib.request.Request(url, data=data, method='POST')
        req.add_header('apiKey',       api_key)
        req.add_header('Accept',       'application/json')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')

        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            recipients = result.get('SMSMessageData',{}).get('Recipients',[])
            if recipients and recipients[0].get('status') == 'Success':
                return True, "SMS envoye via Africa's Talking"
            err = recipients[0].get('status','Erreur') if recipients else str(result)
            return False, f"AT: {err}"
    except Exception as e:
        return False, f"AT erreur: {e}"


# ── TextBelt ─────────────────────────────────────────────────────────────────

def _textbelt_send(telephone: str, message: str) -> tuple:
    try:
        import urllib.request, urllib.parse
        data = urllib.parse.urlencode({
            'phone':   _format_tel(telephone),
            'message': message,
            'key':     'textbelt',
        }).encode('utf-8')
        req = urllib.request.Request(
            'https://textbelt.com/text', data=data, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            if result.get('success'):
                return True, f"SMS envoye (TextBelt, {result.get('quotaRemaining','?')} restant)"
            return False, result.get('error', 'TextBelt echec')
    except Exception as e:
        return False, f"TextBelt erreur: {e}"


# ── Android SMS Intent ────────────────────────────────────────────────────────

def _android_sms(telephone: str, message: str) -> tuple:
    """
    Ouvre l app SMS du telephone avec le message pre-rempli.
    L agent appuie sur Envoyer.
    """
    try:
        import urllib.parse
        from jnius import autoclass
        Intent         = autoclass('android.content.Intent')
        Uri            = autoclass('android.net.Uri')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')

        sms_uri = f"sms:{_format_tel(telephone)}"
        intent  = Intent(Intent.ACTION_VIEW)
        intent.setData(Uri.parse(sms_uri))
        intent.putExtra("sms_body", message)

        PythonActivity.mActivity.startActivity(intent)
        return True, "App SMS ouverte - appuyez sur Envoyer"
    except ImportError:
        return False, "Android non disponible (PC)"
    except Exception as e:
        return False, f"Android SMS erreur: {e}"


# ── Fonction principale ───────────────────────────────────────────────────────

def envoyer_sms_otp(telephone: str, otp: str,
                     nom: str = '') -> tuple:
    """Envoie le code OTP par SMS. Cascade automatique."""
    if not telephone:
        return False, "Numero de telephone manquant"

    cfg     = _config()
    nom_txt = f"Bonjour {nom}, " if nom else "Bonjour, "
    message = (
        f"Fofana Voyage: {nom_txt}"
        f"votre code de retrait est: {otp}. "
        f"Valide 15 minutes. Ne le communiquez a personne."
    )

    return _envoyer_cascade(telephone, message, cfg)


def envoyer_sms_arrivee(telephone: str, numero_colis: str,
                         nom: str = '') -> tuple:
    """Notifie le destinataire que son colis est arrive."""
    if not telephone:
        return False, "Numero de telephone manquant"

    cfg     = _config()
    nom_txt = f"Bonjour {nom}, " if nom else "Bonjour, "
    message = (
        f"Fofana Voyage: {nom_txt}"
        f"votre colis {numero_colis} est arrive. "
        f"Presentez-vous avec votre piece d'identite pour le retirer."
    )

    return _envoyer_cascade(telephone, message, cfg)


def _envoyer_cascade(telephone: str, message: str, cfg: dict) -> tuple:
    """
    Essaie les methodes dans l ordre :
    1. Africa's Talking (si cle API configuree)
    2. TextBelt (internet)
    3. Android SMS intent (ouverture app)
    """
    strategie = cfg.get('sms_strategie', 'auto')
    api_key   = cfg.get('sms_at_apikey', '').strip()

    # --- Africa's Talking en priorite si cle presente ---
    if api_key and strategie in ('africas_talking', 'auto'):
        ok, msg = _at_send(telephone, message, cfg)
        if ok:
            _log(telephone, 'africas_talking', True, msg)
            return True, msg
        print(f"[SMS] AT echec: {msg}")

    # --- TextBelt ---
    if strategie in ('textbelt', 'auto'):
        ok, msg = _textbelt_send(telephone, message)
        if ok:
            _log(telephone, 'textbelt', True, msg)
            return True, msg
        print(f"[SMS] TextBelt echec: {msg}")

    # --- Android SMS intent ---
    ok, msg = _android_sms(telephone, message)
    if ok:
        _log(telephone, 'android_intent', True, msg)
        return True, msg

    _log(telephone, 'echec', False, "Toutes les methodes ont echoue")
    return False, "SMS non envoye. Toutes les methodes ont echoue."


def _log(telephone, methode, succes, details):
    try:
        from database.db_manager import insert
        insert("sessions", {
            "utilisateur_id": 1,
            "action": "SMS",
            "details": f"{'OK' if succes else 'ECHEC'} -> {telephone}: {details}",
            "ip_machine": methode,
        })
    except Exception:
        pass

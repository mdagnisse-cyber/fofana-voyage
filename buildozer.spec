[app]

title = Fofana Voyage - Colis
package.name = fofanavoyage
package.domain = org.fofanavoyage

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,db

version = 2.0.0

requirements = python3==3.10.13,hostpython3==3.10.13,kivy,pillow,reportlab,qrcode,plyer,requests

orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/assets/icons/accueil.png

android.permissions = CAMERA,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,INTERNET,SEND_SMS

android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a,armeabi-v7a

# Ne pas embarquer les dossiers de build/artefacts
source.exclude_dirs = .github,packaging_pc,.kivy,bin,.buildozer

[buildozer]
log_level = 2
warn_on_root = 1

[app]
title = fq
package.name = noveldownloader
package.domain = org.example
source.dir = .
source.include_exts = py
version = 2.0
requirements = python3
orientation = portrait
android.permissions = INTERNET
android.api = 30
android.minapi = 21
android.ndk = 25b
android.sdk = 30
android.arch = armeabi-v7a
android.accept_sdk_license = 1
icon.filename = %(source.dir)s/icon.png
p4a.branch = master
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1

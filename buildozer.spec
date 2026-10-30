[app]
title = War Shooter
package.name = warshooter
package.domain = org.mahmoud
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,otf,wav,ogg,mp3
version = 1.0
requirements = python3,pygame
orientation = landscape
fullscreen = 1

# Android settings
android.permissions = INTERNET
android.api = 35
android.minapi = 23
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1

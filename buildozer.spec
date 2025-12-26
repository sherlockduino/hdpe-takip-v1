[app]
title = HDPE Takip
package.name = hdpetakip
package.domain = org.boruisleri
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db
version = 1.0
requirements = python3,kivy,plyer
orientation = portrait
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 31
android.minapi = 21
p4a.presplash_color = #FFFFFF

[buildozer]
log_level = 2

warn_on_root = 1

import sqlite3
import csv
import shutil
import threading
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os

os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.properties import BooleanProperty, ListProperty, StringProperty, ObjectProperty
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview import RecycleView
from kivy.clock import Clock, mainthread
from kivy.core.window import Window

# --- AYARLAR ---
DB_ADI = "finans_ultimate_v19.db"
# Renkler (R, G, B, A) - 0-1 aralığında
RENK_SIDEBAR = (0.26, 0.37, 0.52, 1)  # #445F85
RENK_BG = (0.95, 0.96, 0.96, 1)      # #F3F4F6
RENK_MAVI = (0.23, 0.51, 0.96, 1)    # #3B82F6
RENK_YESIL = (0.06, 0.72, 0.50, 1)   # #10B981
RENK_KIRMIZI = (0.93, 0.26, 0.26, 1) # #EF4444
RENK_TURUNCU = (0.96, 0.62, 0.04, 1)  # #F59E0B

Window.size = (900, 600)
Window.clearcolor = RENK_BG

# --- KV LANGUAGE (TASARIM KATMANI) ---
KV = """
#:import hex kivy.utils.get_color_from_hex

<CustomPopup>:
    size_hint: .8, .4
    auto_dismiss: False
    title: root.title_text
    BoxLayout:
        orientation: 'vertical'
        padding: 10
        Label:
            text: root.message
            text_size: self.width, None
            size_hint_y: None
            height: self.texture_size[1] + 20
            halign: 'center'
        Button:
            text: "Tamam"
            size_hint_y: None
            height: 40
            on_release: root.dismiss()

# --- TABLO SATIR GÖRÜNÜMÜ ---
<IslemRow>:
    orientation: 'horizontal'
    canvas.before:
        Color:
            rgba: (1, 1, 1, 1) if self.index % 2 == 0 else (0.9, 0.9, 0.9, 1)
        Rectangle:
            pos: self.pos
            size: self.size
    Label:
        text: root.tarih
        color: 0,0,0,1
        size_hint_x: 0.2
    Label:
        text: root.tur
        color: root.renk
        bold: True
        size_hint_x: 0.15
    Label:
        text: root.kategori
        color: 0,0,0,1
        size_hint_x: 0.2
    Label:
        text: root.tutar
        color: 0,0,0,1
        bold: True
        size_hint_x: 0.2
    Button:
        text: "Sil"
        size_hint_x: 0.1
        background_color: (1, 0, 0, 0.8)
        on_release: root.sil_tetikle()

# --- GİRİŞ EKRANI ---
<LoginScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: 50
        spacing: 15
        canvas.before:
            Color:
                rgba: (0.26, 0.37, 0.52, 1)
            Rectangle:
                pos: self.pos
                size: self.size
        
        Label:
            text: "💎 ULTIMATE ERP"
            font_size: '32sp'
            bold: True
            size_hint_y: None
            height: 80
        
        TextInput:
            id: kadi
            hint_text: "Kullanıcı Adı"
            multiline: False
            size_hint_y: None
            height: 40
            
        TextInput:
            id: sifre
            hint_text: "Şifre"
            password: True
            multiline: False
            size_hint_y: None
            height: 40
            
        Button:
            text: "GİRİŞ YAP"
            background_color: (0.23, 0.51, 0.96, 1)
            size_hint_y: None
            height: 50
            bold: True
            on_release: root.giris_yap()
            
        Button:
            text: "KAYIT OL"
            background_color: (0.06, 0.72, 0.50, 1)
            size_hint_y: None
            height: 50
            bold: True
            on_release: root.kayit_ol()

# --- ANA UYGULAMA EKRANI ---
<MainScreen>:
    BoxLayout:
        orientation: 'horizontal'
        
        # SIDEBAR
        BoxLayout:
            orientation: 'vertical'
            size_hint_x: None
            width: 200
            canvas.before:
                Color:
                    rgba: (0.26, 0.37, 0.52, 1)
                Rectangle:
                    pos: self.pos
                    size: self.size
            
            Label:
                text: "Ultimate ERP"
                font_size: '20sp'
                bold: True
                size_hint_y: None
                height: 60
            
            Button:
                text: "📊 Genel Bakış"
                background_normal: ''
                background_color: (0.26, 0.37, 0.52, 1)
                on_release: root.sayfa_degis('dashboard')
            Button:
                text: "➕ İşlem Ekle"
                background_normal: ''
                background_color: (0.26, 0.37, 0.52, 1)
                on_release: root.sayfa_degis('ekle')
            Button:
                text: "📄 Raporlar"
                background_normal: ''
                background_color: (0.26, 0.37, 0.52, 1)
                on_release: root.sayfa_degis('rapor')
            Button:
                text: "⚙️ Yönetici"
                background_normal: ''
                background_color: (0.26, 0.37, 0.52, 1)
                on_release: root.admin_popup_ac()
            
            Widget: # Boşluk

            # Döviz Bilgisi
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: 120
                padding: 10
                canvas.before:
                    Color:
                        rgba: (0.2, 0.25, 0.3, 1)
                    Rectangle:
                        pos: self.pos
                        size: self.size
                Label:
                    text: root.doviz_usd
                    font_size: '12sp'
                    halign: 'left'
                    text_size: self.size
                Label:
                    text: root.doviz_eur
                    font_size: '12sp'
                    halign: 'left'
                    text_size: self.size
                Label:
                    text: root.doviz_altin
                    font_size: '12sp'
                    halign: 'left'
                    text_size: self.size
                Label:
                    text: root.doviz_gumus
                    font_size: '12sp'
                    halign: 'left'
                    text_size: self.size

            Button:
                text: "Çıkış"
                size_hint_y: None
                height: 40
                background_color: (0.9, 0.1, 0.1, 1)
                on_release: app.stop()

        # İÇERİK ALANI
        ScreenManager:
            id: sm_content
            
            Screen:
                name: 'dashboard'
                BoxLayout:
                    orientation: 'vertical'
                    padding: 20
                    spacing: 10
                    
                    Label:
                        text: "Finansal Özet"
                        font_size: '24sp'
                        color: 0,0,0,1
                        size_hint_y: None
                        height: 40
                        bold: True
                        halign: 'left'
                        text_size: self.size

                    # KARTLAR
                    BoxLayout:
                        size_hint_y: None
                        height: 100
                        spacing: 10
                        InfoCard:
                            baslik: "NET DURUM"
                            deger: root.txt_net
                            renk: (0.23, 0.51, 0.96, 1)
                        InfoCard:
                            baslik: "GELİR"
                            deger: root.txt_gelir
                            renk: (0.06, 0.72, 0.50, 1)
                        InfoCard:
                            baslik: "GİDER"
                            deger: root.txt_gider
                            renk: (0.93, 0.26, 0.26, 1)

                    Label:
                        text: root.txt_durum
                        color: root.renk_durum
                        font_size: '18sp'
                        size_hint_y: None
                        height: 40
                        bold: True

                    # BASİT GRAFİK (PROGRESS BARS)
                    Label:
                        text: "Harcama Dağılımı (Top 5)"
                        color: 0.3, 0.3, 0.3, 1
                        size_hint_y: None
                        height: 30
                        halign: 'left'
                        text_size: self.size
                    
                    ScrollView:
                        GridLayout:
                            id: chart_area
                            cols: 1
                            size_hint_y: None
                            height: self.minimum_height
                            spacing: 5

            Screen:
                name: 'ekle'
                BoxLayout:
                    orientation: 'vertical'
                    padding: 30
                    spacing: 15
                    canvas.before:
                        Color:
                            rgba: 1,1,1,1
                        Rectangle:
                            pos: self.pos
                            size: self.size

                    Label:
                        text: "İşlem Ekle / Düzenle"
                        font_size: '24sp'
                        color: 0,0,0,1
                        size_hint_y: None
                        height: 40
                    
                    GridLayout:
                        cols: 2
                        spacing: 10
                        size_hint_y: None
                        height: 250
                        
                        Label:
                            text: "Tür:"
                            color: 0,0,0,1
                        Spinner:
                            id: sp_tur
                            text: 'Gider'
                            values: ('Gelir', 'Gider', 'Borç', 'Alacak')
                            background_color: (0.23, 0.51, 0.96, 1)
                            on_text: root.tur_degisti(self.text)
                        
                        Label:
                            text: "Kategori:"
                            color: 0,0,0,1
                        Spinner:
                            id: sp_kat
                            text: 'Seçiniz'
                            values: []
                            background_color: (0.5, 0.5, 0.5, 1)
                        
                        Label:
                            text: "Tutar:"
                            color: 0,0,0,1
                        TextInput:
                            id: ti_tutar
                            multiline: False
                            input_filter: 'float'
                            
                        Label:
                            text: "Tarih (GG/AA/YYYY):"
                            color: 0,0,0,1
                        TextInput:
                            id: ti_tarih
                            text: root.bugun_tarih()
                            multiline: False
                            
                        Label:
                            text: "Açıklama:"
                            color: 0,0,0,1
                        TextInput:
                            id: ti_desc
                            multiline: False
                    
                    Button:
                        text: "KAYDET"
                        background_color: (0.06, 0.72, 0.50, 1)
                        size_hint_y: None
                        height: 50
                        on_release: root.kaydet()
                    
                    Widget: # Boşluk doldurucu

            Screen:
                name: 'rapor'
                BoxLayout:
                    orientation: 'vertical'
                    padding: 10
                    spacing: 5
                    
                    BoxLayout:
                        size_hint_y: None
                        height: 40
                        spacing: 10
                        TextInput:
                            id: search_box
                            hint_text: "Ara..."
                            multiline: False
                            on_text_validate: root.arama_yap()
                        Button:
                            text: "Ara"
                            size_hint_x: 0.2
                            on_release: root.arama_yap()
                        Button:
                            text: "Excel Aktar"
                            size_hint_x: 0.3
                            background_color: (0.1, 0.6, 0.2, 1)
                            on_release: root.excel_aktar()

                    # BAŞLIKLAR
                    BoxLayout:
                        size_hint_y: None
                        height: 30
                        canvas.before:
                            Color:
                                rgba: 0.8, 0.8, 0.8, 1
                            Rectangle:
                                pos: self.pos
                                size: self.size
                        Label:
                            text: "Tarih"
                            color: 0,0,0,1
                            size_hint_x: 0.2
                        Label:
                            text: "Tür"
                            color: 0,0,0,1
                            size_hint_x: 0.15
                        Label:
                            text: "Kategori"
                            color: 0,0,0,1
                            size_hint_x: 0.2
                        Label:
                            text: "Tutar"
                            color: 0,0,0,1
                            size_hint_x: 0.2
                        Label:
                            text: "İşlem"
                            color: 0,0,0,1
                            size_hint_x: 0.1
                    
                    # LİSTE
                    RecycleView:
                        id: rv_liste
                        viewclass: 'IslemRow'
                        RecycleBoxLayout:
                            default_size: None, dp(40)
                            default_size_hint: 1, None
                            size_hint_y: None
                            height: self.minimum_height
                            orientation: 'vertical'

<InfoCard@BoxLayout>:
    orientation: 'vertical'
    baslik: ""
    deger: ""
    renk: (1,1,1,1)
    padding: 10
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: root.renk
        Rectangle:
            pos: self.pos
            size: 5, self.height
            
    Label:
        text: root.baslik
        color: 0.5, 0.5, 0.5, 1
        font_size: '12sp'
        halign: 'left'
        text_size: self.size
    Label:
        text: root.deger
        color: 0,0,0,1
        font_size: '18sp'
        bold: True
        halign: 'left'
        text_size: self.size

<BarChartItem@BoxLayout>:
    kategori: ""
    tutar: ""
    oran: 0
    renk: (0.2, 0.2, 0.2, 1)
    size_hint_y: None
    height: 30
    Label:
        text: root.kategori
        size_hint_x: 0.3
        color: 0,0,0,1
        halign: 'right'
        valign: 'middle'
        text_size: self.size
    BoxLayout:
        size_hint_x: 0.7
        padding: [10, 5, 10, 5]
        canvas:
            Color:
                rgba: root.renk
            Rectangle:
                pos: self.pos[0] + 10, self.pos[1] + 5
                size: (self.width * root.oran) - 20, self.height - 10
        Label:
            text: root.tutar
            pos: self.pos[0] + 20, self.pos[1]
"""

# --- YARDIMCI SINIFLAR ---

class CustomPopup(Popup):
    title_text = StringProperty("")
    message = StringProperty("")

def show_popup(title, msg):
    p = CustomPopup(title_text=title, message=msg)
    p.open()

class IslemRow(BoxLayout, RecycleView):
    id = 0
    tarih = StringProperty("")
    tur = StringProperty("")
    kategori = StringProperty("")
    tutar = StringProperty("")
    renk = ListProperty([0, 0, 0, 1])
    index = 0

    def sil_tetikle(self):
        # Callback to MainScreen via App
        App.get_running_app().root.get_screen('main').islem_sil(self.id)

class LoginScreen(Screen):
    def db_baglan(self):
        return sqlite3.connect(DB_ADI)

    def giris_yap(self):
        kadi = self.ids.kadi.text
        sifre = self.ids.sifre.text
        
        conn = self.db_baglan()
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS kullanicilar (id INTEGER PRIMARY KEY, kadi TEXT UNIQUE, sifre TEXT)")
        cur.execute("SELECT * FROM kullanicilar WHERE kadi=? AND sifre=?", (kadi, sifre))
        user = cur.fetchone()
        conn.close()
        
        if user:
            self.manager.current = 'main'
            # Verileri yükle
            self.manager.get_screen('main').dashboard_guncelle()
        else:
            show_popup("Hata", "Kullanıcı adı veya şifre yanlış!")

    def kayit_ol(self):
        kadi = self.ids.kadi.text
        sifre = self.ids.sifre.text
        
        if not kadi or not sifre:
            show_popup("Uyarı", "Alanları doldurunuz.")
            return

        conn = self.db_baglan()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO kullanicilar (kadi, sifre) VALUES (?,?)", (kadi, sifre))
            conn.commit()
            show_popup("Başarılı", "Kayıt olundu. Giriş yapabilirsiniz.")
        except sqlite3.IntegrityError:
            show_popup("Hata", "Bu kullanıcı adı zaten var.")
        finally:
            conn.close()

class MainScreen(Screen):
    doviz_usd = StringProperty("USD: ...")
    doviz_eur = StringProperty("EUR: ...")
    doviz_altin = StringProperty("ALTIN: ...")
    doviz_gumus = StringProperty("Gümüş:...")
    
    txt_net = StringProperty("0.00 ₺")
    txt_gelir = StringProperty("0.00 ₺")
    txt_gider = StringProperty("0.00 ₺")
    txt_durum = StringProperty("Hesaplanıyor...")
    renk_durum = ListProperty([0,0,0,1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.calisiyor = True
        self.veritabani_kur()
        self.tur_degisti("Gelir") # Default kategori yükle
        threading.Thread(target=self.doviz_motoru, daemon=True).start()

    def veritabani_kur(self):
        self.conn = sqlite3.connect(DB_ADI, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS islemler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tarih TEXT,
                vade_tarihi TEXT,
                tur TEXT,
                hesap_turu TEXT,
                kategori TEXT,
                tutar REAL,
                para_birimi TEXT,
                aciklama TEXT,
                durum TEXT DEFAULT 'Aktif',
                tekrar_eden INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()

    def bugun_tarih(self):
        return datetime.now().strftime("%d/%m/%Y")

    def sayfa_degis(self, sayfa_adi):
        self.ids.sm_content.current = sayfa_adi
        if sayfa_adi == 'dashboard':
            self.dashboard_guncelle()
        elif sayfa_adi == 'rapor':
            self.arama_yap()

    # --- CRUD İŞLEMLERİ ---
    def tur_degisti(self, tur_degeri):
        sp_kat = self.ids.sp_kat
        if tur_degeri == "Gelir":
            sp_kat.values = ["Maaş", "Satış", "Ek Gelir"]
        elif tur_degeri == "Gider":
            sp_kat.values = ["Market", "Kira", "Fatura", "Eğlence", "Ulaşım"]
        else:
            sp_kat.values = ["Şahıs", "Banka"]
        sp_kat.text = sp_kat.values[0] if sp_kat.values else ""

    def kaydet(self):
        tur = self.ids.sp_tur.text
        kat = self.ids.sp_kat.text
        tutar_str = self.ids.ti_tutar.text
        tarih = self.ids.ti_tarih.text
        aciklama = self.ids.ti_desc.text
        
        try:
            tutar = float(tutar_str)
        except ValueError:
            show_popup("Hata", "Tutar sayı olmalıdır.")
            return

        self.cursor.execute("""
            INSERT INTO islemler (tarih, tur, kategori, tutar, para_birimi, aciklama) 
            VALUES (?,?,?,?,'TL',?)
        """, (tarih, tur, kat, tutar, aciklama))
        self.conn.commit()
        
        show_popup("Başarılı", "İşlem Kaydedildi.")
        # Formu temizle
        self.ids.ti_tutar.text = ""
        self.ids.ti_desc.text = ""
        self.sayfa_degis('dashboard')

    def dashboard_guncelle(self):
        # SQL Toplamlar
        self.cursor.execute("SELECT SUM(tutar) FROM islemler WHERE tur='Gelir'")
        res = self.cursor.fetchone()[0]
        gelir = res if res else 0.0

        self.cursor.execute("SELECT SUM(tutar) FROM islemler WHERE tur='Gider'")
        res = self.cursor.fetchone()[0]
        gider = res if res else 0.0

        net = gelir - gider

        self.txt_gelir = f"+{gelir:,.2f} ₺"
        self.txt_gider = f"-{gider:,.2f} ₺"
        self.txt_net = f"{net:,.2f} ₺"

        if net >= 0:
            self.txt_durum = "Durum İyi: Gelir Fazlası"
            self.renk_durum = RENK_YESIL
        else:
            self.txt_durum = "Dikkat: Gider Fazlası"
            self.renk_durum = RENK_KIRMIZI

        # Grafik (ProgressBar benzeri) oluştur
        self.grafik_ciz(gider)

    def grafik_ciz(self, toplam_gider):
        chart_area = self.ids.chart_area
        chart_area.clear_widgets()
        
        self.cursor.execute("SELECT kategori, SUM(tutar) FROM islemler WHERE tur='Gider' GROUP BY kategori ORDER BY SUM(tutar) DESC LIMIT 5")
        rows = self.cursor.fetchall()
        
        # KV dosyasındaki dinamik class'ı import etmeye gerek yok, Factory ile otomatik
        from kivy.factory import Factory
        
        colors = [RENK_MAVI, RENK_YESIL,RENK_TURUNCU, RENK_KIRMIZI, (0.5, 0, 0.5, 1)]
        
        for i, (kat, tutar) in enumerate(rows):
            oran = (tutar / toplam_gider) if toplam_gider > 0 else 0
            # BarChartItem KV stringinde tanımlandı
            bar = Factory.BarChartItem()
            bar.kategori = kat
            bar.tutar = f"{tutar:.0f} ₺"
            bar.oran = oran
            bar.renk = colors[i % len(colors)]
            chart_area.add_widget(bar)

    def arama_yap(self):
        keyword = self.ids.search_box.text.lower()
        self.cursor.execute("SELECT id, tarih, tur, kategori, tutar FROM islemler ORDER BY id DESC")
        rows = self.cursor.fetchall()
        
        data_list = []
        renk_map = {"Gelir": RENK_YESIL, "Gider": RENK_KIRMIZI, "Borç": RENK_MAVI}
        
        for i, r in enumerate(rows):
            # Arama filtresi
            full_str = f"{r[1]} {r[2]} {r[3]}".lower()
            if keyword in full_str:
                data_list.append({
                    'id': r[0],
                    'tarih': r[1],
                    'tur': r[2],
                    'kategori': r[3],
                    'tutar': f"{r[4]:.2f} ₺",
                    'renk': renk_map.get(r[2], (0,0,0,1)),
                    'index': i
                })
        
        self.ids.rv_liste.data = data_list

    def islem_sil(self, islem_id):
        # RecycleView içindeki butondan çağrılır
        # Emin misin pop-up'ı yapılabilir ama basite indirgiyoruz
        self.cursor.execute("DELETE FROM islemler WHERE id=?", (islem_id,))
        self.conn.commit()
        self.arama_yap()
        show_popup("Bilgi", "Kayıt Silindi.")

    def excel_aktar(self):
        path = "finans_raporu.csv"
        try:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                w = csv.writer(f, delimiter=';')
                w.writerow(["ID", "Tarih", "Tür", "Kategori", "Tutar", "Açıklama"])
                self.cursor.execute("SELECT id, tarih, tur, kategori, tutar, aciklama FROM islemler")
                w.writerows(self.cursor.fetchall())
            show_popup("Başarılı", f"Rapor oluşturuldu:\n{os.path.abspath(path)}")
        except Exception as e:
            show_popup("Hata", str(e))

    # --- ADMIN ---
    def admin_popup_ac(self):
        # Basit bir admin popup
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        t_user = TextInput(hint_text="Kullanıcı Adı", multiline=False)
        t_pass = TextInput(hint_text="Şifre", password=True, multiline=False)
        btn = Button(text="Giriş", size_hint_y=None, height=40)
        
        popup = Popup(title="Yönetici Girişi", content=content, size_hint=(None, None), size=(300, 200))
        
        def check(instance):
            if t_user.text == "sherlockduino" and t_pass.text == "571453":
                popup.dismiss()
                show_popup("Admin Paneli", "Tebrikler! Admin yetkisi doğrulandı.\n(Buraya admin fonksiyonları eklenebilir)")
            else:
                show_popup("Hata", "Yetkisiz Erişim")

        btn.bind(on_release=check)
        content.add_widget(t_user)
        content.add_widget(t_pass)
        content.add_widget(btn)
        popup.open()

    # --- DÖVİZ MOTORU ---
    def doviz_motoru(self):
        headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/xml"
        }
        while self.calisiyor:
            try:
                # --- USD ve EUR (TCMB) ---
                r_xml = requests.get("https://www.tcmb.gov.tr/kurlar/today.xml", timeout=10)
                tree = ET.fromstring(r_xml.content)
                usd = tree.find("./Currency[@CurrencyCode='USD']/ForexSelling").text
                eur = tree.find("./Currency[@CurrencyCode='EUR']/ForexSelling").text
                
                # --- ALTIN ve GÜMÜŞ (GenelPara API) ---
                # Bu kaynak genelde daha hızlıdır ve kesilmez.
                r_json = requests.get("https://finans.truncgil.com/v4/today.json", timeout=10)
                data = r_json.json()
                
                # GenelPara'da anahtarlar farklıdır:
                # GA = Gram Altın, GAG = Gümüş
                altin = data.get("GRA", {}).get("Selling", "0")
                gumus = data.get("GUMUS", {}).get("Selling", "0")

                self.ui_doviz_guncelle(usd, eur, altin, gumus)
            
            except Exception as e:
                print("Veri çekilemedi, tekrar deneniyor...", e)
            
            time.sleep(60)

    # 3. GÜNCELLEME FONKSİYONUNA GÜMÜŞ'Ü EKLE
    @mainthread
    def ui_doviz_guncelle(self, usd, eur, altin, gumus):
        self.doviz_usd = f"USD: {usd} ₺"
        self.doviz_eur = f"EUR: {eur} ₺"
        self.doviz_altin = f"Altın: {altin} ₺"
        self.doviz_gumus = f"Gümüş: {gumus} ₺"

class FinansApp(App):
    def build(self):
        self.title = "Ultimate ERP v19 - Kivy Edition"
        Builder.load_string(KV)
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(MainScreen(name='main'))
        return sm

if __name__ == "__main__":
    FinansApp().run()
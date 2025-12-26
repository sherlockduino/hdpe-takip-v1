import os
import sqlite3
import csv
import traceback
from datetime import datetime

# --- KIVY AYARLARI ---
from kivy.config import Config
Config.set('graphics', 'multisamples', '0')
Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '640')
Config.set('graphics', 'resizable', '0')

from kivy.utils import platform
from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.metrics import dp

Window.clearcolor = (0.95, 0.95, 0.95, 1)

# --- VERİ TABANI YOLU AYARLAMA (KRİTİK DÜZELTME) ---
def get_db_path():
    db_name = "boruisleri.db"
    if platform == 'android':
        # Android'de yazılabilir özel klasöre kaydet
        app_klasoru = App.get_running_app().user_data_dir
        return os.path.join(app_klasoru, db_name)
    else:
        # Bilgisayarda mevcut klasöre kaydet
        return os.path.join(os.getcwd(), db_name)

def veritabani_kur():
    conn = sqlite3.connect(get_db_path()) # Düzeltildi
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kayitlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarih TEXT,
            cap TEXT,
            metraj REAL,
            urun_tipi TEXT
        )
    """)
    cursor.execute("PRAGMA table_info(kayitlar)")
    sutunlar = [info[1] for info in cursor.fetchall()]
    if 'urun_tipi' not in sutunlar:
        cursor.execute("ALTER TABLE kayitlar ADD COLUMN urun_tipi TEXT DEFAULT 'HDPE Boru'")
    conn.commit()
    conn.close()

def veri_kaydet(urun_tipi, cap, metraj):
    conn = sqlite3.connect(get_db_path()) # Düzeltildi
    cursor = conn.cursor()
    zaman = datetime.now().strftime("%d.%m.%Y %H:%M")
    cursor.execute("INSERT INTO kayitlar (tarih, cap, metraj, urun_tipi) VALUES (?, ?, ?, ?)", (zaman, cap, metraj, urun_tipi))
    conn.commit()
    conn.close()

def veri_sil(kayit_id):
    conn = sqlite3.connect(get_db_path()) # Düzeltildi
    cursor = conn.cursor()
    cursor.execute("DELETE FROM kayitlar WHERE id=?", (kayit_id,))
    conn.commit()
    conn.close()

def veri_guncelle(kayit_id, yeni_cap, yeni_metraj):
    conn = sqlite3.connect(get_db_path()) # Düzeltildi
    cursor = conn.cursor()
    cursor.execute("UPDATE kayitlar SET cap=?, metraj=? WHERE id=?", (yeni_cap, yeni_metraj, kayit_id))
    conn.commit()
    conn.close()

def verileri_getir():
    conn = sqlite3.connect(get_db_path()) # Düzeltildi
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM kayitlar ORDER BY id DESC")
    veriler = cursor.fetchall()
    conn.close()
    return veriler

def toplam_metraj_getir():
    conn = sqlite3.connect(get_db_path()) # Düzeltildi
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(metraj) FROM kayitlar WHERE urun_tipi = 'HDPE Boru'")
    sonuc = cursor.fetchone()[0]
    conn.close()
    return sonuc if sonuc else 0

# --- EXCEL / CSV OLUŞTURMA ---
def excele_aktar():
    try:
        conn = sqlite3.connect(get_db_path()) # Düzeltildi
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM kayitlar")
        veriler = cursor.fetchall()
        conn.close()
        
        dosya_adi = f"Rapor_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        
        if platform == 'android':
            app_klasoru = App.get_running_app().user_data_dir
            kayit_yolu = os.path.join(app_klasoru, dosya_adi)
        else:
            kayit_yolu = os.path.join(os.getcwd(), dosya_adi)

        with open(kayit_yolu, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['ID', 'Tarih', 'Çap/Tip', 'Miktar', 'Ürün Tipi'])
            
            for v in veriler:
                u_tip = v[4] if len(v) > 4 and v[4] else 'HDPE Boru'
                miktar_ham = v[3]
                
                if u_tip == 'HDPE Boru':
                    miktar_str = str(miktar_ham).replace('.', ',')
                else:
                    miktar_str = str(int(miktar_ham))
                
                writer.writerow([v[0], v[1], v[2], miktar_str, u_tip])
        
        return kayit_yolu, None 

    except Exception as e:
        return None, str(traceback.format_exc())

# --- TASARIM (KV) ---
kv_design = """
ScreenManager:
    LoginScreen:
    WorkScreen:
    HistoryScreen:

<SpinnerOptionStyle@SpinnerOption>:
    background_normal: ''
    background_color: 0.2, 0.2, 0.2, 1
    height: dp(50)

<LoginScreen>:
    name: 'login'
    BoxLayout:
        orientation: 'vertical'
        padding: dp(40)
        spacing: dp(20)
        canvas.before:
            Color:
                rgba: 1, 1, 1, 1
            Rectangle:
                pos: self.pos
                size: self.size
        Widget: 
            size_hint_y: 0.2
        Label:
            text: 'HDPE TAKİP SİSTEMİ'
            font_size: '26sp'
            bold: True
            color: 0, 0.2, 0.5, 1
            size_hint_y: None
            height: dp(50)
        TextInput:
            id: username
            hint_text: 'Kullanıcı Adı'
            multiline: False
            size_hint_y: None
            height: dp(50)
            write_tab: False
        TextInput:
            id: password
            hint_text: 'Şifre'
            password: True
            multiline: False
            size_hint_y: None
            height: dp(50)
            write_tab: False
        Button:
            text: 'GİRİŞ YAP'
            bold: True
            background_normal: ''
            background_color: 0, 0.5, 1, 1
            size_hint_y: None
            height: dp(55)
            on_release: root.giris_yap()
        Label:
            id: login_msg
            text: ''
            color: 1, 0, 0, 1
            size_hint_y: None
            height: dp(30)
        Widget: 
            size_hint_y: 0.3

<WorkScreen>:
    name: 'work'
    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(15)
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            Label: 
                text: 'Şantiye Kayıt' 
                color: 0,0,0,1 
                bold: True
                font_size: '20sp'
                size_hint_x: 0.7
                text_size: self.size
                halign: 'left'
                valign: 'middle'
            Button:
                text: 'ÇIKIŞ'
                size_hint_x: 0.3
                background_normal: ''
                background_color: 0.8, 0, 0, 1
                on_release: app.stop()
        BoxLayout:
            size_hint_y: None
            height: dp(90)
            padding: dp(15)
            canvas.before:
                Color:
                    rgba: 0.9, 0.95, 1, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [15,]
            BoxLayout:
                orientation: 'vertical'
                Label:
                    text: 'TOPLAM BORU METRAJI'
                    color: 0.4, 0.4, 0.4, 1
                    font_size: '14sp'
                Label:
                    id: toplam_etiket
                    text: '0.00 m'
                    color: 0, 0.3, 0.8, 1
                    bold: True
                    font_size: '32sp'
        Label:
            text: 'Yeni İş / Parça Ekle'
            color: 0,0,0,1
            bold: True
            size_hint_y: None
            height: dp(30)
            text_size: self.size
            halign: 'left'
        Spinner:
            id: urun_tipi_secici
            text: 'HDPE Boru'
            values: ('HDPE Boru', 'EF Manşon', 'Dirsek (90°)', 'Dirsek (45°)', 'Eşit Te', 'İnegal Te', 'Redüksiyon', 'Flanş Adaptörü', 'Kör Tapa', 'Sürgülü Vana', 'Kelebek Vana', 'Vantuz', 'Servis Te')
            size_hint_y: None
            height: dp(55)
            background_normal: ''
            background_color: 0.1, 0.1, 0.4, 1
            option_cls: 'SpinnerOptionStyle'
            on_text: root.urun_degisti(self.text)
        Spinner:
            id: boru_capi_secici
            text: 'Çap Seçiniz'
            values: [] 
            size_hint_y: None
            height: dp(55)
            background_normal: ''
            background_color: 0.3, 0.3, 0.3, 1
            option_cls: 'SpinnerOptionStyle'
        TextInput:
            id: yapilan_metraj
            hint_text: 'Metraj Giriniz (m)'
            input_filter: 'float'
            multiline: False
            size_hint_y: None
            height: dp(55)
            write_tab: False
        Button:
            text: 'KAYDET'
            bold: True
            font_size: '18sp'
            size_hint_y: None
            height: dp(60)
            background_normal: ''
            background_color: 0, 0.7, 0, 1 
            on_release: root.kaydet()
        Label:
            id: save_msg
            text: ''
            color: 0, 0.6, 0, 1
            size_hint_y: None
            height: dp(30)
        Button:
            text: 'GEÇMİŞ & RAPORLAMA'
            bold: True
            size_hint_y: None
            height: dp(60)
            background_normal: ''
            background_color: 0.9, 0.5, 0, 1
            on_release: app.root.current = 'history'
        Widget:
            size_hint_y: 1

<HistoryScreen>:
    name: 'history'
    BoxLayout:
        orientation: 'vertical'
        BoxLayout:
            size_hint_y: None
            height: dp(60)
            padding: dp(5)
            spacing: dp(5)
            canvas.before:
                Color:
                    rgba: 0.2, 0.2, 0.2, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Button:
                text: '< Geri'
                size_hint_x: 0.2
                background_normal: ''
                background_color: 0.4, 0.4, 0.4, 1
                on_release: app.root.current = 'work'
            Spinner:
                id: filtre_secici
                text: 'Tümü'
                values: ('Tümü', 'Bugün', 'Bu Ay')
                size_hint_x: 0.35
                background_normal: ''
                background_color: 0.2, 0.5, 0.7, 1
                on_text: root.filtrele(self.text)
            Button:
                text: 'RAPOR PAYLAŞ'
                bold: True
                size_hint_x: 0.45
                background_normal: ''
                background_color: 0, 0.6, 0.2, 1
                on_release: root.rapor_al()
        BoxLayout:
            size_hint_y: None
            height: dp(30)
            padding: dp(5)
            canvas.before:
                Color:
                    rgba: 0.9, 0.9, 0.9, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Label:
                text: 'Ürün/Tarih'
                color: 0,0,0,1
                bold: True
                size_hint_x: 0.4
                font_size: '13sp'
            Label:
                text: 'Çap'
                color: 0,0,0,1
                bold: True
                size_hint_x: 0.15
                font_size: '13sp'
            Label:
                text: 'Miktar'
                color: 0,0,0,1
                bold: True
                size_hint_x: 0.2
                font_size: '13sp'
            Label:
                text: 'İşlem'
                color: 0,0,0,1
                bold: True
                size_hint_x: 0.25
                font_size: '13sp'
        ScrollView:
            GridLayout:
                id: history_list
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                padding: dp(5)
                spacing: dp(5)
"""

# --- MANTIK ---
class GuncellemePopup(Popup):
    def __init__(self, kayit_data, yenileme_fonksiyonu, **kwargs):
        super().__init__(**kwargs)
        self.title = "Kaydı Düzenle"
        self.size_hint = (0.9, 0.5)
        self.kayit_id = kayit_data[0]
        self.yenileme_fonksiyonu = yenileme_fonksiyonu
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        urun_adi = kayit_data[4] if len(kayit_data) > 4 and kayit_data[4] else "HDPE Boru"
        layout.add_widget(Label(text=f"Ürün: {urun_adi}", size_hint_y=None, height=30))
        layout.add_widget(Label(text="Çap/Tip:", size_hint_y=None, height=30))
        self.input_cap = TextInput(text=str(kayit_data[2]), multiline=False, size_hint_y=None, height=40)
        layout.add_widget(self.input_cap)
        layout.add_widget(Label(text="Miktar:", size_hint_y=None, height=30))
        self.input_metraj = TextInput(text=str(kayit_data[3]), multiline=False, input_filter='float', size_hint_y=None, height=40)
        layout.add_widget(self.input_metraj)
        btn_kaydet = Button(text="GÜNCELLE", background_color=(0, 1, 0, 1), size_hint_y=None, height=50)
        btn_kaydet.bind(on_release=self.guncelle)
        layout.add_widget(btn_kaydet)
        self.content = layout

    def guncelle(self, instance):
        if self.input_cap.text and self.input_metraj.text:
            veri_guncelle(self.kayit_id, self.input_cap.text, self.input_metraj.text)
            self.dismiss()
            self.yenileme_fonksiyonu()

class LoginScreen(Screen):
    def giris_yap(self):
        if self.ids.username.text == "admin" and self.ids.password.text == "1234":
            self.manager.current = 'work'
            self.ids.login_msg.text = ""
        else:
            self.ids.login_msg.text = "Kullanıcı adı: admin / Şifre: 1234"

class WorkScreen(Screen):
    STD_CAPLAR_LIST = [20, 25, 32, 40, 50, 63, 75, 90, 110, 125, 140, 160, 180, 200, 225, 250, 280, 315, 355, 400, 450, 500, 560, 630]
    STD_CAPLAR_TUPLE = tuple(map(str, STD_CAPLAR_LIST))
    VANA_CAPLAR = ('50', '80', '100', '125', '150', '200', '250', '300', '350', '400')
    REDUKSIYON_CAPLAR = ('50-40', '63-50', '75-63', '90-75', '110-90', '125-110', '140-125', '160-140', '180-160', '200-180', '225-200', '250-225', '280-250', '315-280', '355-315', '400-355', '450-400', '500-450')
    ANA_BORULAR = [50, 63, 75, 90, 110, 125, 160, 180, 200, 225, 250, 280, 315]
    CIKISLAR = [20, 25, 32, 40, 50, 63]
    SERVIS_TE_CAPLAR = []
    for ana in ANA_BORULAR:
        for cikis in CIKISLAR:
            SERVIS_TE_CAPLAR.append(f"{ana}-{cikis}")
    INEGAL_TE_CAPLAR = []
    for ana in STD_CAPLAR_LIST:
        for cikis in STD_CAPLAR_LIST:
            if ana > cikis and cikis >= 63:
                INEGAL_TE_CAPLAR.append(f"{ana}-{cikis}")
    ESIT_TE_CAPLAR = [f"{c}-{c}" for c in STD_CAPLAR_LIST]

    def on_enter(self):
        self.toplami_guncelle()
        self.ids.boru_capi_secici.values = self.STD_CAPLAR_TUPLE

    def toplami_guncelle(self):
        toplam = toplam_metraj_getir()
        self.ids.toplam_etiket.text = f"{toplam:.2f} m"

    def urun_degisti(self, yeni_urun):
        spinner = self.ids.boru_capi_secici
        if yeni_urun == 'HDPE Boru':
            self.ids.yapilan_metraj.hint_text = 'Metraj Giriniz (m)'
        else:
            self.ids.yapilan_metraj.hint_text = 'Adet Giriniz (Sayı)'
        
        if yeni_urun == 'Redüksiyon': spinner.values = self.REDUKSIYON_CAPLAR
        elif yeni_urun in ['Sürgülü Vana', 'Kelebek Vana', 'Vantuz']: spinner.values = self.VANA_CAPLAR
        elif yeni_urun == 'Servis Te': spinner.values = self.SERVIS_TE_CAPLAR
        elif yeni_urun == 'İnegal Te': spinner.values = self.INEGAL_TE_CAPLAR 
        elif yeni_urun == 'Eşit Te': spinner.values = self.ESIT_TE_CAPLAR
        else: spinner.values = self.STD_CAPLAR_TUPLE
        spinner.text = 'Çap Seçiniz'

    def kaydet(self):
        urun_tipi = self.ids.urun_tipi_secici.text
        cap_secim = self.ids.boru_capi_secici.text
        miktar = self.ids.yapilan_metraj.text
        if "Seçiniz" in cap_secim:
            self.ids.save_msg.text = "Lütfen Çap Seçin!"
            self.ids.save_msg.color = (1, 0, 0, 1)
            return
        if miktar:
            veri_kaydet(urun_tipi, cap_secim, miktar)
            self.toplami_guncelle()
            self.ids.save_msg.text = "Kayıt Başarılı!"
            self.ids.save_msg.color = (0, 0.6, 0, 1)
            self.ids.yapilan_metraj.text = ""
        else:
            self.ids.save_msg.text = "Miktar Girilmedi!"
            self.ids.save_msg.color = (1, 0, 0, 1)

class HistoryScreen(Screen):
    def on_enter(self):
        filtre_modu = self.ids.filtre_secici.text
        self.filtrele(filtre_modu)
    def filtrele(self, mod):
        tum_kayitlar = verileri_getir()
        filtrelenmis = []
        bugun = datetime.now().strftime("%d.%m.%Y")
        bu_ay = datetime.now().strftime("%m.%Y")
        if mod == 'Tümü': filtrelenmis = tum_kayitlar
        elif mod == 'Bugün': filtrelenmis = [k for k in tum_kayitlar if k[1].startswith(bugun)]
        elif mod == 'Bu Ay': filtrelenmis = [k for k in tum_kayitlar if bu_ay in k[1]]
        self.listeyi_ciz(filtrelenmis)
    def listeyi_ciz(self, kayitlar):
        grid = self.ids.history_list
        grid.clear_widgets()
        if not kayitlar:
            grid.add_widget(Label(text="Kayıt yok.", color=(0.5,0.5,0.5,1), size_hint_y=None, height=dp(40)))
            return
        for k in kayitlar:
            urun_adi = k[4] if len(k) > 4 and k[4] else "HDPE Boru"
            satir = BoxLayout(size_hint_y=None, height=dp(55))
            bilgi_kutu = BoxLayout(orientation='vertical', size_hint_x=0.4)
            bilgi_kutu.add_widget(Label(text=urun_adi, color=(0,0.2,0.6,1), bold=True, font_size='12sp', text_size=(self.width*0.4, None), halign='left'))
            bilgi_kutu.add_widget(Label(text=str(k[1]), color=(0.4,0.4,0.4,1), font_size='10sp', text_size=(self.width*0.4, None), halign='left'))
            satir.add_widget(bilgi_kutu)
            satir.add_widget(Label(text=f"{k[2]}", color=(0,0,0,1), bold=True, size_hint_x=0.15, font_size='11sp'))
            miktar_str = f"{k[3]} m" if urun_adi == 'HDPE Boru' else f"{int(k[3])} ad."
            satir.add_widget(Label(text=miktar_str, color=(0,0,0,1), size_hint_x=0.2, font_size='12sp'))
            buton_kutusu = BoxLayout(size_hint_x=0.25, spacing=dp(2))
            btn_duzenle = Button(text='D', background_normal='', background_color=(0.2, 0.6, 1, 1), font_size='12sp')
            btn_duzenle.bind(on_release=lambda x, data=k: self.popup_ac(data))
            btn_sil = Button(text='X', background_normal='', background_color=(1, 0.2, 0.2, 1), font_size='12sp')
            btn_sil.bind(on_release=lambda x, kid=k[0]: self.silme_islemi(kid))
            buton_kutusu.add_widget(btn_duzenle)
            buton_kutusu.add_widget(btn_sil)
            satir.add_widget(buton_kutusu)
            grid.add_widget(satir)
            grid.add_widget(Widget(size_hint_y=None, height=dp(5)))
    def popup_ac(self, kayit_data):
        current_filter = self.ids.filtre_secici.text
        pop = GuncellemePopup(kayit_data, lambda: self.filtrele(current_filter))
        pop.open()
    def silme_islemi(self, kayit_id):
        veri_sil(kayit_id)
        current_filter = self.ids.filtre_secici.text
        self.filtrele(current_filter)

    # --- HATA YAKALAMA VE RAPORLAMA ---
    def rapor_al(self):
        dosya_yolu, hata = excele_aktar()
        
        # HATA VARSA EKRANA BAS
        if hata:
            self.hata_goster(f"HATA:\n{hata}")
            return

        if dosya_yolu:
            if platform == 'android':
                try:
                    # DÜZELTME: Plyer'ı sadece butona basınca çağırıyoruz
                    from plyer import share 
                    share.share(file_attachment=dosya_yolu)
                except Exception as e:
                    self.hata_goster(f"Paylaşım Hatası: {str(e)}")
            else:
                self.hata_goster(f"Dosya Oluşturuldu:\n{dosya_yolu}")
                try: os.startfile(os.path.dirname(dosya_yolu))
                except: pass
        else:
            self.hata_goster("Dosya oluşturulamadı.")

    def hata_goster(self, mesaj):
        content = TextInput(text=mesaj, readonly=True)
        popup = Popup(title='Bilgi / Hata', content=content, size_hint=(0.9, 0.6))
        popup.open()

class BoruApp(App):
    def build(self):
        veritabani_kur()
        return Builder.load_string(kv_design)

# --- EN ALT KISIM (BUNU KOPYALA YAPIŞTIR) ---
if __name__ == '__main__':
    try:
        BoruApp().run()
    except Exception:
        # Hata olursa, hatayı bir dosyaya yaz (Çökme sebebini anlamak için)
        import traceback
        hata_metni = traceback.format_exc()
        
        try:
            # Android veya PC için güvenli yol
            from kivy.app import App
            import os
            
            # Uygulama henüz başlatılamadıysa App.get_running_app() None dönebilir
            # Bu yüzden manuel bir yol deniyoruz
            if platform == 'android':
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity = PythonActivity.mActivity
                dosya_yolu = os.path.join(activity.getExternalFilesDir(None).getAbsolutePath(), 'hata_logu.txt')
            else:
                dosya_yolu = "hata_logu.txt"
                
            with open(dosya_yolu, "w") as f:
                f.write(hata_metni)
                
        except:
            pass

    BoruApp().run()

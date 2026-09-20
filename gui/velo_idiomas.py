"""Idiomas de Velo: cuáles hay, cómo se llaman y qué claves del tema cambian.

Los idiomas disponibles son los que SDDM trae instalados en el sistema (más inglés, que es
su idioma de origen). Al elegir uno se ajusta el idioma de las fechas (Qt lo conoce) y los
textos propios del tema. Los textos de SDDM (Contraseña, Apagar...) dependen del idioma
del propio SDDM y no se tocan desde aquí.
"""
from pathlib import Path

DIR_SDDM = Path('/usr/share/sddm/translations-qt6')

NOMBRES = {
    'ar': 'العربية', 'bg': 'Български', 'bn': 'বাংলা', 'ca': 'Català', 'cs': 'Čeština', 'da': 'Dansk',
    'de': 'Deutsch', 'en': 'English', 'es': 'Español', 'et': 'Eesti', 'eu': 'Euskara', 'fa': 'فارسی',
    'fi': 'Suomi', 'fr': 'Français', 'gl': 'Galego', 'he': 'עברית', 'hi_IN': 'हिन्दी', 'hu': 'Magyar',
    'ie': 'Interlingue', 'is': 'Íslenska', 'it': 'Italiano', 'ja': '日本語', 'ka': 'ქართული',
    'kk': 'Қазақша', 'ko': '한국어', 'lt': 'Lietuvių', 'lv': 'Latviešu', 'nb': 'Norsk bokmål',
    'nl': 'Nederlands', 'nn': 'Norsk nynorsk', 'oc': 'Occitan', 'pl': 'Polski',
    'pt_BR': 'Português (Brasil)', 'pt_PT': 'Português (Portugal)', 'ro': 'Română', 'ru': 'Русский',
    'sk': 'Slovenčina', 'sr': 'Српски', 'sv': 'Svenska', 'tr': 'Türkçe', 'uk': 'Українська',
    'zh_CN': '简体中文', 'zh_TW': '繁體中文',
}

# Textos del tema. Orden: mensaje de bloqueo, "iniciando sesión", 4 globos del menú y 2 del usuario.
CLAVES_TEXTO = [
    ('LockScreen.Message', 'text'),
    ('LoginScreen.LoginArea.Spinner', 'text'),
    ('Tooltips', 'session-text'),
    ('Tooltips', 'layout-text'),
    ('Tooltips', 'virtual-keyboard-text'),
    ('Tooltips', 'power-text'),
    ('Tooltips', 'select-user-text'),
    ('Tooltips', 'close-user-selection-text'),
]
CLAVES_FECHA = [('LockScreen.Date', 'locale'), ('LoginScreen.Date', 'locale')]

TEXTOS = {
    'en': ['Press any key', 'Logging in', 'Change session', 'Change keyboard layout',
           'Toggle virtual keyboard', 'Power options', 'Select user', 'Close user selection'],
    'es': ['Pulse cualquier tecla', 'Iniciando sesión', 'Cambiar sesión', 'Cambiar distribución del teclado',
           'Mostrar u ocultar el teclado virtual', 'Opciones de energía', 'Elegir usuario',
           'Cerrar la selección de usuario'],
    'eu': ['Sakatu edozein tekla', 'Saioa hasten', 'Aldatu saioa', 'Aldatu teklatuaren diseinua',
           'Erakutsi edo ezkutatu teklatu birtuala', 'Energia-aukerak', 'Hautatu erabiltzailea',
           'Itxi erabiltzaile-hautaketa'],
    'fr': ['Appuyez sur une touche', 'Connexion en cours', 'Changer de session',
           'Changer la disposition du clavier', 'Afficher ou masquer le clavier virtuel',
           "Options d'alimentation", "Choisir l'utilisateur", "Fermer la sélection d'utilisateur"],
    'de': ['Beliebige Taste drücken', 'Anmeldung läuft', 'Sitzung wechseln', 'Tastaturbelegung ändern',
           'Bildschirmtastatur ein-/ausblenden', 'Energieoptionen', 'Benutzer auswählen',
           'Benutzerauswahl schließen'],
    'it': ['Premi un tasto qualsiasi', 'Accesso in corso', 'Cambia sessione',
           'Cambia layout della tastiera', 'Mostra o nascondi la tastiera virtuale',
           'Opzioni di alimentazione', 'Seleziona utente', 'Chiudi la selezione utente'],
    'pt_BR': ['Pressione qualquer tecla', 'Entrando', 'Alterar sessão', 'Alterar layout do teclado',
              'Mostrar ou ocultar o teclado virtual', 'Opções de energia', 'Selecionar usuário',
              'Fechar seleção de usuário'],
    'pt_PT': ['Prima qualquer tecla', 'A iniciar sessão', 'Alterar sessão', 'Alterar disposição do teclado',
              'Mostrar ou ocultar o teclado virtual', 'Opções de energia', 'Selecionar utilizador',
              'Fechar seleção de utilizador'],
    'ca': ['Premeu qualsevol tecla', "S'està iniciant la sessió", 'Canvia la sessió',
           'Canvia la disposició del teclat', 'Mostra o amaga el teclat virtual', "Opcions d'energia",
           "Selecciona l'usuari", "Tanca la selecció d'usuari"],
    'gl': ['Preme calquera tecla', 'Iniciando a sesión', 'Cambiar a sesión',
           'Cambiar a disposición do teclado', 'Amosar ou agochar o teclado virtual',
           'Opcións de enerxía', 'Seleccionar usuario', 'Pechar a selección de usuario'],
    'ar': ['اضغط أي مفتاح', 'جارٍ تسجيل الدخول', 'تغيير الجلسة', 'تغيير تخطيط لوحة المفاتيح', 'إظهار لوحة المفاتيح الافتراضية أو إخفاؤها', 'خيارات الطاقة', 'اختيار المستخدم', 'إغلاق اختيار المستخدم'],
    'bg': ['Натиснете произволен клавиш', 'Влизане', 'Смяна на сесията', 'Смяна на клавиатурната подредба', 'Показване или скриване на виртуалната клавиатура', 'Опции за захранването', 'Избор на потребител', 'Затваряне на избора на потребител'],
    'bn': ['যেকোনো কী চাপুন', 'লগ ইন হচ্ছে', 'সেশন পরিবর্তন করুন', 'কিবোর্ড লেআউট পরিবর্তন করুন', 'ভার্চুয়াল কিবোর্ড দেখান বা লুকান', 'পাওয়ার বিকল্প', 'ব্যবহারকারী নির্বাচন করুন', 'ব্যবহারকারী নির্বাচন বন্ধ করুন'],
    'cs': ['Stiskněte libovolnou klávesu', 'Přihlašování', 'Změnit relaci', 'Změnit rozložení klávesnice', 'Zobrazit nebo skrýt virtuální klávesnici', 'Možnosti napájení', 'Vybrat uživatele', 'Zavřít výběr uživatele'],
    'da': ['Tryk på en vilkårlig tast', 'Logger ind', 'Skift session', 'Skift tastaturlayout', 'Vis eller skjul det virtuelle tastatur', 'Strømindstillinger', 'Vælg bruger', 'Luk brugervalg'],
    'et': ['Vajutage suvalist klahvi', 'Sisselogimine', 'Vaheta seanssi', 'Vaheta klaviatuuripaigutust', 'Kuva või peida virtuaalne klaviatuur', 'Toitesuvandid', 'Vali kasutaja', 'Sulge kasutajavalik'],
    'fa': ['هر کلیدی را فشار دهید', 'در حال ورود', 'تغییر نشست', 'تغییر چیدمان صفحه\u200cکلید', 'نمایش یا پنهان کردن صفحه\u200cکلید مجازی', 'گزینه\u200cهای توان', 'انتخاب کاربر', 'بستن انتخاب کاربر'],
    'fi': ['Paina mitä tahansa näppäintä', 'Kirjaudutaan sisään', 'Vaihda istuntoa', 'Vaihda näppäimistöasettelua', 'Näytä tai piilota virtuaalinäppäimistö', 'Virranhallinta', 'Valitse käyttäjä', 'Sulje käyttäjän valinta'],
    'he': ['לחצו על מקש כלשהו', 'מתחבר', 'החלפת הפעלה', 'החלפת פריסת מקלדת', 'הצגה או הסתרה של המקלדת הווירטואלית', 'אפשרויות צריכת חשמל', 'בחירת משתמש', 'סגירת בחירת המשתמש'],
    'hi_IN': ['कोई भी कुंजी दबाएँ', 'लॉग इन हो रहा है', 'सत्र बदलें', 'कीबोर्ड लेआउट बदलें', 'वर्चुअल कीबोर्ड दिखाएँ या छिपाएँ', 'पावर विकल्प', 'उपयोगकर्ता चुनें', 'उपयोगकर्ता चयन बंद करें'],
    'hu': ['Nyomjon meg egy tetszőleges billentyűt', 'Bejelentkezés', 'Munkamenet váltása', 'Billentyűzetkiosztás váltása', 'Virtuális billentyűzet megjelenítése vagy elrejtése', 'Energiaellátási lehetőségek', 'Felhasználó kiválasztása', 'Felhasználóválasztó bezárása'],
    'ie': ['Presse quelcunc clave', 'Intrant', 'Changear session', 'Changear li disposition del tastatura', 'Monstrar o celar li virtual tastatura', 'Optiones de energie', 'Selecter usator', 'Clúder li selection de usator'],
    'is': ['Ýttu á einhvern takka', 'Skrái inn', 'Skipta um setu', 'Skipta um lyklaborðsuppsetningu', 'Sýna eða fela sýndarlyklaborð', 'Aflvalkostir', 'Velja notanda', 'Loka notandavali'],
    'ja': ['いずれかのキーを押してください', 'ログイン中', 'セッションを切り替える', 'キーボードレイアウトを切り替える', '仮想キーボードの表示/非表示', '電源オプション', 'ユーザーを選択', 'ユーザー選択を閉じる'],
    'ka': ['დააჭირეთ ნებისმიერ ღილაკს', 'შესვლა მიმდინარეობს', 'სესიის შეცვლა', 'კლავიატურის განლაგების შეცვლა', 'ვირტუალური კლავიატურის ჩვენება ან დამალვა', 'კვების პარამეტრები', 'მომხმარებლის არჩევა', 'მომხმარებლის არჩევის დახურვა'],
    'kk': ['Кез келген пернені басыңыз', 'Жүйеге кіру', 'Сеансты ауыстыру', 'Пернетақта орналасуын өзгерту', 'Виртуалды пернетақтаны көрсету немесе жасыру', 'Қуат опциялары', 'Пайдаланушыны таңдау', 'Пайдаланушыны таңдауды жабу'],
    'ko': ['아무 키나 누르세요', '로그인 중', '세션 변경', '키보드 배열 변경', '가상 키보드 표시/숨기기', '전원 옵션', '사용자 선택', '사용자 선택 닫기'],
    'lt': ['Paspauskite bet kurį klavišą', 'Prisijungiama', 'Keisti seansą', 'Keisti klaviatūros išdėstymą', 'Rodyti arba slėpti virtualiąją klaviatūrą', 'Maitinimo parinktys', 'Pasirinkti naudotoją', 'Uždaryti naudotojo pasirinkimą'],
    'lv': ['Nospiediet jebkuru taustiņu', 'Notiek pieteikšanās', 'Mainīt sesiju', 'Mainīt tastatūras izkārtojumu', 'Rādīt vai slēpt virtuālo tastatūru', 'Barošanas opcijas', 'Izvēlēties lietotāju', 'Aizvērt lietotāja izvēli'],
    'nb': ['Trykk på en tast', 'Logger inn', 'Bytt økt', 'Bytt tastaturoppsett', 'Vis eller skjul det virtuelle tastaturet', 'Strømalternativer', 'Velg bruker', 'Lukk brukervalg'],
    'nl': ['Druk op een willekeurige toets', 'Inloggen', 'Sessie wijzigen', 'Toetsenbordindeling wijzigen', 'Schermtoetsenbord tonen of verbergen', 'Energieopties', 'Gebruiker kiezen', 'Gebruikerskeuze sluiten'],
    'nn': ['Trykk på ein tast', 'Loggar inn', 'Byt økt', 'Byt tastaturoppsett', 'Vis eller skjul det virtuelle tastaturet', 'Straumval', 'Vel brukar', 'Lukk brukarval'],
    'oc': ['Quichatz una tòca qualsevol', 'Connexion en cors', 'Cambiar de session', 'Cambiar la disposicion del clavièr', 'Afichar o amagar lo clavièr virtual', 'Opcions d’alimentacion', 'Causir l’utilizaire', 'Barrar la seleccion d’utilizaire'],
    'pl': ['Naciśnij dowolny klawisz', 'Logowanie', 'Zmień sesję', 'Zmień układ klawiatury', 'Pokaż lub ukryj klawiaturę wirtualną', 'Opcje zasilania', 'Wybierz użytkownika', 'Zamknij wybór użytkownika'],
    'ro': ['Apăsați orice tastă', 'Se autentifică', 'Schimbă sesiunea', 'Schimbă aranjamentul tastaturii', 'Afișează sau ascunde tastatura virtuală', 'Opțiuni de alimentare', 'Selectați utilizatorul', 'Închide selecția utilizatorului'],
    'ru': ['Нажмите любую клавишу', 'Вход в систему', 'Сменить сеанс', 'Сменить раскладку клавиатуры', 'Показать или скрыть виртуальную клавиатуру', 'Параметры питания', 'Выбрать пользователя', 'Закрыть выбор пользователя'],
    'sk': ['Stlačte ľubovoľný kláves', 'Prihlasovanie', 'Zmeniť reláciu', 'Zmeniť rozloženie klávesnice', 'Zobraziť alebo skryť virtuálnu klávesnicu', 'Možnosti napájania', 'Vybrať používateľa', 'Zavrieť výber používateľa'],
    'sr': ['Притисните било који тастер', 'Пријављивање', 'Промени сесију', 'Промени распоред тастатуре', 'Прикажи или сакриј виртуелну тастатуру', 'Опције напајања', 'Изабери корисника', 'Затвори избор корисника'],
    'sv': ['Tryck på valfri tangent', 'Loggar in', 'Byt session', 'Byt tangentbordslayout', 'Visa eller dölj det virtuella tangentbordet', 'Energialternativ', 'Välj användare', 'Stäng användarval'],
    'tr': ['Herhangi bir tuşa basın', 'Oturum açılıyor', 'Oturumu değiştir', 'Klavye düzenini değiştir', 'Sanal klavyeyi göster veya gizle', 'Güç seçenekleri', 'Kullanıcı seç', 'Kullanıcı seçimini kapat'],
    'uk': ['Натисніть будь-яку клавішу', 'Вхід у систему', 'Змінити сеанс', 'Змінити розкладку клавіатури', 'Показати або сховати віртуальну клавіатуру', 'Параметри живлення', 'Вибрати користувача', 'Закрити вибір користувача'],
    'zh_CN': ['按任意键', '正在登录', '切换会话', '切换键盘布局', '显示或隐藏虚拟键盘', '电源选项', '选择用户', '关闭用户选择'],
    'zh_TW': ['按任意鍵', '正在登入', '切換工作階段', '切換鍵盤配置', '顯示或隱藏虛擬鍵盤', '電源選項', '選擇使用者', '關閉使用者選擇'],
}


def base(codigo):
    """'es_ES' -> 'es'; 'pt_BR' se queda igual porque tiene texto propio."""
    return codigo if codigo in TEXTOS else codigo.split('_')[0]


def tiene_textos(codigo):
    return codigo in TEXTOS or base(codigo) in TEXTOS


def textos(codigo):
    """Los textos del tema en ese idioma; si no están traducidos, en inglés."""
    return TEXTOS.get(codigo) or TEXTOS.get(base(codigo)) or TEXTOS['en']


def disponibles(directorio=DIR_SDDM):
    """[(código, nombre)] de los idiomas que SDDM tiene instalados, más inglés."""
    codigos = {'en'}
    try:
        codigos |= {f.stem for f in Path(directorio).glob('*.qm') if '@' not in f.stem}
    except OSError:
        pass
    return sorted(((c, NOMBRES.get(c, c)) for c in codigos), key=lambda x: x[1].lower())


def elegir_en_lista(codigo_sistema, lista):
    """Código de la lista que corresponde al idioma del sistema (es_ES -> es), o 'en'."""
    codigos = [c for c, _n in lista]
    for candidato in (codigo_sistema, base(codigo_sistema), codigo_sistema.split('_')[0]):
        if candidato in codigos:
            return candidato
    return 'en'


def claves(codigo_fecha, codigo_textos):
    """[(sección, clave, valor)] que hay que escribir en el .conf para ese idioma.

    codigo_fecha: el que entiende Qt para las fechas (es_ES, eu...).
    codigo_textos: el que se usa para buscar los textos del tema.
    """
    salida = [(s, k, codigo_fecha) for s, k in CLAVES_FECHA]
    salida += [(s, k, t) for (s, k), t in zip(CLAVES_TEXTO, textos(codigo_textos))]
    return salida

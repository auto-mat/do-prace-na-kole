from django.conf import settings
urls = {
    # Admin
    'admin':                        "/django/admin/",

    # Registrace
    'chci_slapat':                  "/chci-slapat/",
    'registrace':                   "/registrace/",
    'pozvanky':                     '/registrace/pozvanky',
    'zaslat_zadost_clenstvi':       "/registrace/zaslat-zadost-o-clenstvi-v-tymu",
    'typ_platby':                   "/registrace/typ-platby",
    'platba':                       "/registrace/platba",
    'platba_uspesna':               "/registrace/platba-uspesna",
    'platba_neuspesna':             "/registrace/platba-neuspesna",

    # Profil
    "profil":                       "/profil",
    "profil_pristup":               "/profil",
    'login':                        "/profil/login",
    'logout':                       "/profil/logout",
    'zapomenute_heslo':             "/profil/zapomenute-heslo",
    'zapomenute_heslo_odeslano':    "/profil/zapomenute-heslo-odeslano",
    'zapomenute_heslo_dokonceno':   "/profil/zapomenute-heslo-dokonceno",
    'zapomenute_heslo_zmena':       "/profil/zapomenute-heslo-zmena",
    'zmena_hesla':                  "/profil/zmena-hesla",
    'zmena_hesla_hotovo':           "/profil/zmena-hesla-hotovo",
    "upravit_profil":               "/profil/upravit-profil",
    'team_admin':                   "/profil/team-admin",
    'vysledky':                     "/profil/vysledky",
    'vysledky_souteze':             "/profil/vysledky_souteze",

    # Company admin
    'edit_company':                 "/fa/editovat_spolecnost",
    'zadost_firemni_spravce':       "/fa/zadost",
    'company_admin':                "/fa",

    # Zastarale nebo odlozeno na pozdeji
    'kratke_vysledky':              "kratke_vysledky.html",
    'cyklozamestnavatel_roku':      "cyklozamestnavatel_roku.html",
    'otazka':                       "otazka.html",
    'otazky':                       "otazky.html",
    'cyklozamestnavatel_firmy':     "cyklozamestnavatel_firmy.html",
    'cyklozamestnavatel_odpovedi':  "cyklozamestnavatel_odpovedi.html",
    'odpovedi':                     "odpovedi.html",

}

if hasattr(settings, 'TESTING_URLS') and settings.TESTING_URLS:
    import wp_urls_testing
    urls = wp_urls_testing.urls

def wp_reverse(name):
    return urls[name]

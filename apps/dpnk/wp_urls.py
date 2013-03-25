urls = {
    # Registrace
    'registrace':                   "/registrace/",
    'pozvanky':                     '/registrace/pozvanky',
    'zaslat_zadost_clenstvi':       "/registrace/zaslat-zadost-o-clenstvi-v-tymu",
    'typ_platby':                   "/registrace/typ-platby",
    'platba':                       "/registrace/platba",
    'platba_uspesna':               "/registrace/platba-uspesna",
    'platba_neuspesna':             "/registrace/platba-neuspesna",

    # Profil
    "profil":                       "/profil",
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

    # Zastarale nebo odlozeno na pozdeji
    'kratke_vysledky':              "kratke_vysledky.html",
    'cyklozamestnavatel_roku':      "cyklozamestnavatel_roku.html",
    'otazka':                       "otazka.html",
    'otazky':                       "otazky.html",
    'cyklozamestnavatel_firmy':     "cyklozamestnavatel_firmy.html",
    'cyklozamestnavatel_odpovedi':  "cyklozamestnavatel_odpovedi.html",
    'odpovedi':                     "odpovedi.html",

}

def wp_reverse(name):
    return urls[name]

# This file serves testing purposes if used instead of wp_urls.py
# and together with dpnk-wp HTML files tree
urls = {
    # Admin
    'admin':                        "/admin/",

    'chci_slapat':                  "chci_slapat.html",
    "upravit_profil":               "upravit_profil.html",
    "profil":                       "profil.html",
    "profil_pristup":               "profil.html",
    'registrace':                   "registrace.html",
    'pozvanky':                     'pozvanky.html',
    'zaslat_zadost_clenstvi':       "zaslat_zadost_clenstvi.html",
    'login':                        "login.html",
    'zmena_hesla':                  "zmena_hesla.html",
    'zmena_hesla_hotovo':           "zmena_hesla_hotovo",
    'team_admin':                   "team_admin.html",
    'vysledky':                     "vysledky.html",
    'kratke_vysledky':              "kratke_vysledky.html",
    'otazka':                       "otazka.html",
    'cyklozamestnavatel_roku':      "cyklozamestnavatel_roku.html",
    'logout':                       "logout.html",
    'typ_platby':                   "typ_platby.html",
    'platba':                       "platba.html",
    'platba_uspesna':               "platba_uspesna.html",
    'platba_neuspesna':             "platba_uspesna.html",
    'platba_status':                "platba_status.html",
    'zapomenute_heslo':             "zapomenute_heslo.html",
    'zapomenute_heslo_odeslano':    "zapomenute_heslo_odeslano.html",
    'zapomenute_heslo_dokonceno':   "zapomenute_heslo_dokonceno.html",
    'zapomenute_heslo_zmena':       "zapomenute_heslo_zmena.html",
    'otazky':                       "otazky.html",
    'cyklozamestnavatel_firmy':     "cyklozamestnavatel_firmy.html",
    'cyklozamestnavatel_odpovedi':  "cyklozamestnavatel_odpovedi.html",
    'odpovedi':                     "odpovedi.html",
    'vysledky_souteze':             "vysledky_souteze.html",

    # Company admin
    'edit_company':                 "fa/editovat_spolecnost",
    'company_admin':                "fa",
}

def wp_reverse(name):
    return urls[name]

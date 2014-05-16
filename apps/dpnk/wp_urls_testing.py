# -*- coding: utf-8 -*-
# This file serves testing purposes if used instead of wp_urls.py
# and together with dpnk-wp HTML files tree
urls = {
    # Registrace
    'chci_slapat':                  "chci_slapat.html",
    'registrace':                   "registrace.html",
    'pozvanky':                     'pozvanky.html',
    'team_invitation':              'tym-pozvanka.html',
    'zaslat_zadost_clenstvi':       "zaslat_zadost_clenstvi.html",
    'typ_platby':                   "typ_platby.html",
    'platba':                       "platba.html",
    'platba_uspesna':               "platba_uspesna.html",
    'platba_neuspesna':             "platba_uspesna.html",

    # Profil
    "profil":                       "profil.html",
    "profil_pristup":               "profil.html",
    'login':                        "login.html",
    'logout':                       "logout.html",
    'zapomenute_heslo':             "zapomenute_heslo.html",
    'zapomenute_heslo_odeslano':    "zapomenute_heslo_odeslano.html",
    'zapomenute_heslo_dokonceno':   "zapomenute_heslo_dokonceno.html",
    'zapomenute_heslo_zmena':       "zapomenute_heslo_zmena.html",
    'zmena_hesla':                  "zmena_hesla.html",
    'zmena_hesla_hotovo':           "zmena_hesla_hotovo",
    "upravit_profil":               "upravit_profil.html",
    'team_admin':                   "team_admin.html",
    'vysledky':                     "vysledky.html",
    'vysledky_souteze':             "vysledky_souteze.html",
    'otazka':                       "otazka.html",
    'zmenit_triko':                 "zmenit_triko.html",
    'zmenit_tym':                   "tým.html",
    'dalsi_clenove':                "clenove_tymu",
    'souteze':                      "souteze",
    'balicek':                      "balicek",

    # Competition
    'competition_profile':          "soutezni_profil",


    # Company admin
    'pay_for_company_competitors':  "/fa/zaplatit_za_uzivatele/",
    'edit_company':                 "fa/editovat_spolecnost",
    'create_invoice':               "fa/vytvorit_fakturu",
    'zadost_firemni_spravce':       "fa/zadost",
    'soutez':                       "fa/soutez",
    'company_admin':                "fa",

    # Other
    'bike_repair':                  "/cykloservis",
    'pravidla':                     "/pravidla",
    'firma':                        "/firma",

    # Zastarale nebo odlozeno na pozdeji
    'kratke_vysledky':              "kratke_vysledky.html",
    'platba_status':                "platba_status.html",
    'otazky':                       "otazky.html",

    # Company admin
}

for url in urls:
    urls[url] = "/~petr/dpnk-wp/%s" % urls[url]

urls['dotaznik']="/admin/dotaznik/"
urls['odpovedi']="/admin/odpovedi/"
urls['dotaznik_odpovedi']="/admin/dotaznik_odpovedi/"
urls['otazky']="/admin/otazky/"

urls['admin'] = "/admin/"

# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils import translation

urls = {
    # Admin
    'admin':                        "/django/admin/",

    # Registrace
    'chci_slapat':                  "/chci-slapat/",
    'registrace':                   "/registrace/",
    'pozvanky':                     '/registrace/pozvanky/',
    'team_invitation':              '/registrace/tym-pozvanka/',
    'zaslat_zadost_clenstvi':       "/registrace/zaslat-zadost-o-clenstvi-v-tymu/",
    'typ_platby':                   "/registrace/typ-platby/",
    'platba':                       "/registrace/platba/",
    'platba_uspesna':               "/registrace/platba-uspesna/",
    'platba_neuspesna':             "/registrace/platba-neuspesna/",

    # Profil
    "profil":                       "/profil/",
    "profil_pristup":               "",
    'login':                        "/prihlasit/",
    'logout':                       "/odhlasit/",
    'zapomenute_heslo':             "/profil/zapomenute-heslo/",
    'zapomenute_heslo_odeslano':    "/profil/zapomenute-heslo-odeslano/",
    'zapomenute_heslo_dokonceno':   "/profil/zapomenute-heslo-dokonceno/",
    'zapomenute_heslo_zmena':       "/profil/zapomenute-heslo-zmena/",
    'zmena_hesla':                  "/profil/zmena-hesla/",
    'zmena_hesla_hotovo':           "/profil/zmena-hesla-hotovo/",
    "upravit_profil":               "/profil/upravit-profil/",
    'team_admin':                   "/profil/team-admin/",
    'vysledky':                     "/profil/vysledky/",
    'vysledky_souteze':             "/profil/vysledky_souteze/",
    'dotaznik':                     "/django/admin/dotaznik/",
    'odpovedi':                     "/django/admin/odpovedi/",
    'dotaznik_odpovedi':            "/django/admin/dotaznik_odpovedi/",
    'otazky':                       "/django/admin/otazky/",
    'otazka':                       "/profil/dotaznik/",
    'zmenit_triko':                 "/profil/zmenit-triko/",
    'zmenit_tym':                   "/profil/zmenit-tym/",
    'dalsi_clenove':                "/profil/dalsi-clenove/",
    'souteze':                      "/profil/souteze/",
    'balicek':                      "/profil/balicek/",

    # Competition
    'competition_profile':          "soutezni_profil",

    # Company admin
    'pay_for_company_competitors':  "/fa/zaplatit_za_uzivatele/",
    'create_invoice':               "/fa/vytvorit_fakturu/",
    'edit_company':                 "/fa/editovat_spolecnost/",
    'zadost_firemni_spravce':       "/fa/zadost/",
    'soutez':                       "/fa/soutez/",
    'company_admin':                "/fa/",

    # Other
    'bike_repair':                  "/cykloservis/",
    'pravidla':                     "/pravidla/",
    'firma':                        "/firma/",

    # Zastarale nebo odlozeno na pozdeji
    'kratke_vysledky':              "kratke_vysledky.html",

}

if hasattr(settings, 'TESTING_URLS') and settings.TESTING_URLS:
    import wp_urls_testing
    urls = wp_urls_testing.urls

def wp_reverse(name):
    if name == "":
        return ""
    prefix = ""
    if not (hasattr(settings, 'TESTING_URLS') and settings.TESTING_URLS) and translation.get_language() != settings.LANGUAGE_CODE:
        prefix = "/" + translation.get_language()
    return prefix + urls[name]

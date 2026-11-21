from django.conf import settings
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _


class CampaignType(models.Model):
    name = models.CharField(
        unique=True,
        verbose_name=_("Jméno typu kampaně"),
        max_length=60,
        null=False,
    )
    slug = models.SlugField(
        unique=True,
        verbose_name="Identifikátor typu kampaně",
        blank=True,
    )
    web = models.URLField(
        verbose_name=_("Web kampáně"),
        default="http://www.dopracenakole.cz",
        blank=True,
    )
    contact_email = models.CharField(
        verbose_name=_("Kontaktní e-mail"),
        default="kontakt@dopracenakole.cz",
        max_length=80,
        blank=False,
    )
    sitetree_postfix = models.CharField(
        verbose_name=_("Postfix pro menu"),
        max_length=60,
        null=False,
        blank=True,
        default="",
    )
    LANGUAGE_PREFIXES = [
        ("dpnk", _("Do práce na kole")),
        ("dsnk", _("Do školy na kole")),
    ]
    language_prefixes = models.CharField(
        verbose_name=_("Jazyková sada"),
        choices=LANGUAGE_PREFIXES,
        max_length=16,
        null=False,
        blank=False,
        default="dpnk",
    )
    wp_api_url = models.URLField(
        default="http://www.dopracenakole.cz",
        verbose_name=_("Adresa pro Wordpress API se články"),
        null=True,
        blank=True,
    )
    frontend_url = models.URLField(
        default="https://dpnk-frontend.s3-eu-west-1.amazonaws.com/2021.10/",
        verbose_name=_("Adresa pro statické frontendové soubory"),
    )
    tagline = models.TextField(
        default="Na kole, pěšky či poklusem. Celostátní výzva v lednu %s",
    )
    organization_coordinator_contact_email = models.CharField(
        verbose_name=_("Kontaktní e-mail koordinátora organizace"),
        default="firmy@dopracenakole.cz",
        max_length=80,
        blank=False,
    )
    city_coordinator_contact_email = models.CharField(
        verbose_name=_("Kontaktní e-mail koordinátora města"),
        default="mesta@dopracenakole.cz",
        max_length=80,
        blank=False,
    )
    billing_details = models.CharField(
        verbose_name=_("Fakturační údaje"),
        default=(
            "Auto*Mat, z. s., Slezská 2033/11, 120 00 Praha 2,"
            " IČ: 22670319 / DIČ: CZ22670319, Číslo účtu: 2601085491/2010 (Fio Banka),"
            " IBAN: CZ57 2010 0000 0026 0108 5491, BIC/SWIFT: FIOBCZPPXXX"
        ),
        max_length=350,
        blank=False,
    )
    faq_url = models.URLField(
        verbose_name=_("Často kladené dotazy"),
        default="https://dopracenakole.cz/o-vyzve/faq",
        blank=False,
    )
    faq_organization_coordinator_url = models.URLField(
        verbose_name=_("Často kladené dotazy koordinátorů organizacií"),
        default="https://dopracenakole.cz/casto-kladene-dotazy-firemnich-koordinatoru-faq",
        blank=False,
    )

    def __str__(self):
        return self.name

    def get_language_prefix(self):
        if self.language_prefixes == "dpnk":
            return ""
        return self.language_prefixes

    def get_available_languages(self):
        if self.language_prefixes == "dpnk":
            return ((k, v) for k, v in settings.LANGUAGES if len(k) == 2)
        return (
            (k, v)
            for k, v in settings.LANGUAGES
            if k.startswith(self.get_language_prefix())
        )

    def sitetree_maintree(self):
        if self.sitetree_postfix:
            return "maintree_%s" % self.sitetree_postfix
        else:
            return "maintree"

    def sitetree_about_us(self):
        if self.sitetree_postfix:
            return "about_us_%s" % self.sitetree_postfix
        else:
            return "about_us"

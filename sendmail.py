# -*- coding: utf-8 -*-

from dpnk.models import Payment, Voucher
from django.core.mail import EmailMessage

def send_mails():

    for p in Payment.objects.filter(status='99', user__in=(669, 811)):
        print p.user
        v = Voucher.objects.filter(user__isnull=True)[0]
        v.user = p.user
        v.save()

        v = Voucher.objects.filter(user=p.user)[0]
        # Send user email confirmation and a voucher
        email = EmailMessage(subject=u"Startovné Do práce na kole a slevový kupon",
                             body=u"""Dobrý den,

zasíláme Vám nový slevový kupon na nákup trika, protože jsme zjistili,
že původně zaslaný kupon se Vám může hlásit jako již použitý. Pokud
jste si triko ještě neobjednali, použijte prosím tento kupon. V opačném
případě si tohoto emailu nemusíte všímat.

Zaplacením startovného získáváte poukaz na designové triko kampaně Do
práce na kole 2012 (včetně poštovného a balného). Objednávku můžete
uskutečnit na adrese:

http://www.coromoro.com/designova_trika/detail/139-do-prace-na-kole-2012

Váš slevový kód pro zaslání trička z obchodu Čoromoro je %s.

K jeho zadání budete vyzváni poté, co si vyberete velikost a přejdete
na svůj nákupní košík.

S pozdravem
Auto*Mat
""" % v.code,
                             from_email = u'Do práce na kole <kontakt@dopracenakole.net>',
                             to = [p.user.email()]
                             )
        print email.body
        email.send(fail_silently=True)

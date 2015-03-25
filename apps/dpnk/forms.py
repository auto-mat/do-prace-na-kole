# -*- coding: utf-8 -*-
from smart_selects.form_fields import ChainedModelChoiceField
from django.contrib.auth.models import User
from django import forms
import settings
# Registration imports
import registration.forms
import models
from django.utils import formats
from models import UserProfile, Company, Subsidiary, Team, UserAttendance
from django.db.models import Q
from dpnk.widgets import SelectOrCreate, SelectChainedOrCreate
from dpnk.fields import WorkingScheduleField
from django.forms.widgets import HiddenInput
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, MinLengthValidator
from django.contrib.gis.forms import OSMWidget
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, HTML
from django.core.urlresolvers import reverse
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import string_concat


def team_full(data):
    if len(UserAttendance.objects.filter(Q(approved_for_team='approved') | Q(approved_for_team='undecided'), team=data, userprofile__user__is_active=True)) >= 5:
        raise forms.ValidationError(_(u"Tento tým již má pět členů a je tedy plný"))


class SubmitMixin(object):
    def __init__(self, url_name="", *args, **kwargs):
        self.helper = FormHelper()
        if url_name:
            self.url_name = url_name
            self.helper.form_class = url_name + "_form"
        self.helper.add_input(Submit('submit', _(u'Odeslat')))
        super(SubmitMixin, self).__init__(*args, **kwargs)


class PrevNextMixin(object):
    def __init__(self, url_name="", *args, **kwargs):
        self.helper = FormHelper()
        if url_name:
            self.url_name = url_name
            self.helper.form_class = url_name + "_form"
        if not hasattr(self, 'no_prev'):
            self.helper.add_input(Submit('prev', _(u'Předchozí')))
        if not hasattr(self, 'no_next'):
            self.helper.add_input(Submit('next', _(u'Další')))
        return super(PrevNextMixin, self).__init__(*args, **kwargs)


class AuthenticationFormDPNK(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        ret_val = super(AuthenticationFormDPNK, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "login-form"
        self.helper.layout = Layout(
            'username', 'password',
            HTML(_(u"""<a href="%(password_reset_address)s">Zapomněli jste své přihlašovací údaje?</a>
                <br/><br/>
                Ještě nemáte účet? <a href="%(registration_address)s">Registrujte se</a> do soutěže Do práce na kole.<br/><br/>
            """ % { 'password_reset_address': reverse("password_reset"), 'registration_address': reverse("registration_access")} )),
            )
        self.helper.add_input(Submit('submit', _(u'Přihlásit')))
        self.fields['username'].label = _(u"Email (uživatelské jméno)")


class RegisterCompanyForm(forms.ModelForm):
    required_css_class = 'required'
    error_css_class = 'error'

    class Meta:
        model = Company
        fields = ('name', )


class AdressForm(forms.ModelForm):
    required_css_class = 'required'
    error_css_class = 'error'

    address_psc = forms.CharField(
        label=_(u"PSČ"),
        help_text=_(u"Např.: 130 00"),
    )

    def clean_address_psc(self):
        address_psc = self.cleaned_data['address_psc']
        try:
            address_psc = int(address_psc.replace(' ', ''))
        except (TypeError, ValueError):
            raise ValidationError('PSČ musí být pěticiferné číslo')
        if address_psc > 99999 or address_psc < 10000:
            raise ValidationError('PSČ musí být pěticiferné číslo')
        return address_psc

    def __init__(self, *args, **kwargs):
        campaign = kwargs.pop('campaign', None)
        super(AdressForm, self).__init__(*args, **kwargs)
        if campaign:
            self.fields['city'].queryset = models.City.objects.filter(cityincampaign__campaign=campaign)
        # self.fields['city'].label_from_instance = lambda obj: obj.city.name

    class Meta:
        model = Subsidiary
        fields = ('city', 'address_recipient', 'address_street', 'address_street_number', 'address_psc', 'address_city')


class RegisterSubsidiaryForm(AdressForm):
    pass


class RegisterTeamForm(forms.ModelForm):
    required_css_class = 'required'
    error_css_class = 'error'

    campaign = forms.ModelChoiceField(
        label=_(u"Kampaň"),
        queryset=models.Campaign.objects.all(),
        widget=HiddenInput(),
    )

    class Meta:
        model = Team
        fields = ('name', 'campaign')


class WorkingScheduleForm(forms.ModelForm):
    schedule = WorkingScheduleField(
        label=_(u"Pracovní rozvrh"),
        required=False,
    )

    def save(self, *args, **kwargs):
        ret_val = super(WorkingScheduleForm, self).save(*args, **kwargs)
        trips = self.cleaned_data['schedule']
        for trip in trips:
            if trip.can_edit_working_schedule():
                trip.save()
        return ret_val

    def __init__(self, url_name="", *args, **kwargs):
        self.helper = FormHelper()
        if url_name:
            self.url_name = url_name
            self.helper.form_class = url_name + "_form"
        self.helper.layout = Layout(
            'schedule',
            HTML(_(u"""Jak postupovat ve speciálních případech:  <ul>
               <li>při práci na krátký dlouhý týden zadejte ve dnech, které pracujete cestu tam i zpět</li>
               <li>pokud pracujete přes noc, zadejte první den pouze cestu tam a druhý den pouze cestu zpět</li>
               </ul>""")),
        )
        ret_val = super(WorkingScheduleForm, self).__init__(*args, **kwargs)
        self.helper.add_input(Submit('prev', _(u'Předchozí')))
        entered_competition = self.instance.entered_competition()
        if not entered_competition:
            tasks = []
            if not self.instance.userprofile.profile_complete():
                tasks.append(_(u"<a href='%s'>vyplnit</a>") % reverse('upravit_profil'))
            if not self.instance.team_complete():
                tasks.append(_(u"<a href='%s'>být ověřeným členem týmu</a>") % reverse('zmenit_tym'))
            if not self.instance.track_complete():
                tasks.append(_(u"<a href='%s'>vyplnit trasu</a>") % reverse('upravit_trasu'))
            if not self.instance.payment_complete():
                tasks.append(_(u"<a href='%s'>mít dokončenou platbu</a>") % reverse('typ_platby'))
            if not self.instance.tshirt_complete():
                tasks.append(_(u"<a href='%s'>vyplnit tričko</a>") % reverse('zmenit_triko'))
            self.helper.layout.extend([HTML(string_concat('<div class="alert alert-warning">', _(u'Před vstupem do profilu budete ještě muset %s') % ", ".join(tasks), '</div>'))])
            self.helper.add_input(Submit('submit', _(u'Uložit')))
        self.helper.add_input(Submit('next', _(u'Přejít do profilu'), **({} if entered_competition else {'disabled': 'True'})))
        self.fields['schedule'].initial = self.instance.get_all_trips()
        return ret_val

    class Meta:
        model = UserAttendance
        fields = ('schedule', )


class ChangeTeamForm(PrevNextMixin, forms.ModelForm):
    company = forms.ModelChoiceField(
        label=_(u"Společnost"),
        queryset=Company.objects.all(),
        widget=SelectOrCreate(RegisterCompanyForm, prefix="company", new_description=_(u"Společnost v seznamu není, chci založit novou")),
        required=True)
    subsidiary = ChainedModelChoiceField(
        chain_field="company",
        app_name="dpnk",
        model_name="Subsidiary",
        model_field="company",
        show_all=False,
        auto_choose=True,
        label=_(u"Adresa pobočky/společnosti"),
        widget=SelectChainedOrCreate(
            RegisterSubsidiaryForm, view_name='', prefix="subsidiary", new_description=_(u"Adresa v seznamu není, chci založit novou"),
            chain_field="company",
            app_name="dpnk",
            model_name="SubsidiaryInCampaign",
            model_field="company",
            show_all=False,
            auto_choose=True,
        ),
        queryset=Subsidiary.objects.all(),
        required=True)
    team = ChainedModelChoiceField(
        chain_field="subsidiary",
        app_name="dpnk",
        model_name="Team",
        model_field="subsidiary",
        show_all=False,
        auto_choose=False,
        widget=SelectChainedOrCreate(
            RegisterTeamForm, view_name='', prefix="team", new_description=_(u"Můj tým v seznamu není, vytvořit nový"),
            chain_field="subsidiary",
            app_name="dpnk",
            model_name="TeamInCampaign",
            model_field="subsidiary",
            show_all=False,
            auto_choose=False,
        ),
        label=_(u"Tým"),
        queryset=Team.objects.all(),
        required=True)

    def clean(self):
        cleaned_data = super(ChangeTeamForm, self).clean()
        if self.instance.payment_status() == 'done' and self.instance.team:
            if 'team' in cleaned_data and cleaned_data['team'].subsidiary != self.instance.team.subsidiary:
                raise forms.ValidationError(mark_safe(_(u"Po zaplacení není možné měnit tým mimo pobočku")))
        return cleaned_data

    def clean_team(self):
        data = self.cleaned_data['team']
        if not data:
            return self.instance.team
        if type(data) != RegisterTeamForm:
            if data != self.instance.team:
                team_full(data)
        return data

    def __init__(self, request=None, *args, **kwargs):
        initial = kwargs.get('initial', {})
        instance = kwargs.get('instance', False)

        if instance:
            previous_user_attendance = instance.previous_user_attendance()
            if previous_user_attendance and previous_user_attendance.team:
                initial['subsidiary'] = previous_user_attendance.team.subsidiary
                initial['company'] = previous_user_attendance.team.subsidiary.company

        if instance and instance.team:
            initial['team'] = instance.team
            initial['subsidiary'] = instance.team.subsidiary
            initial['company'] = instance.team.subsidiary.company

        if request:
            if request.GET.get('team', None):
                initial['team'] = request.GET['team']

        kwargs['initial'] = initial

        super(ChangeTeamForm, self).__init__(*args, **kwargs)

        if instance and 'team' not in initial:
            previous_user_attendance = instance.previous_user_attendance()
            if previous_user_attendance:
                self.fields["team"].widget.create = True

        if self.instance.payment_status() == 'done' and self.instance.team:
            self.fields["subsidiary"].widget = HiddenInput()
            self.fields["company"].widget = HiddenInput()
            self.fields["team"].queryset = Team.objects.filter(subsidiary__company=self.instance.team.subsidiary.company)

    class Meta:
        model = UserAttendance
        fields = ('company', 'subsidiary', 'team')


class RegistrationAccessFormDPNK(SubmitMixin, forms.Form):
    email = forms.CharField(
        required=True,
        label=_(u"E-mail (uživatelské jméno)"),
        help_text=_(u"Zadejte váš email. Pokud jste se účastnili v minulém roce, zadejte stejný email jako v minulém roce."),
    )


class RegistrationFormDPNK(registration.forms.RegistrationFormUniqueEmail):
    required_css_class = 'required'

    username = forms.CharField(widget=forms.HiddenInput, required=False)

    def clean_username(self):
        "This function is required to overwrite an inherited username clean"
        return self.cleaned_data['username']

    def clean(self):
        if not self.errors:
            self.cleaned_data['username'] = '%s%s' % (self.cleaned_data['email'].split('@', 1)[0], User.objects.count())
        super(RegistrationFormDPNK, self).clean()
        return self.cleaned_data

    def __init__(self, request=None, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', _(u'Odeslat')))

        if request:
            initial = kwargs.get('initial', {})
            if request.GET.get('team', None):
                initial['team'] = request.GET['team']
            kwargs['initial'] = initial

        super(RegistrationFormDPNK, self).__init__(*args, **kwargs)

        self.fields['email'].help_text = _(u"Pro informace v průběhu kampaně, k zaslání zapomenutého loginu")

    def clean_email(self):
        if User.objects.filter(email__iexact=self.cleaned_data['email']):
            raise forms.ValidationError(mark_safe(_(u"Tato e-mailová adresa se již používá. Pokud je vaše, buď se rovnou <a href='%(login)s'>přihlašte</a>, nebo použijte <a href='%(password)s'> obnovu hesla</a>.") % {'password': reverse('password_reset'), 'login': reverse('login')}))
        return self.cleaned_data['email']

    def clean_team(self):
        data = self.cleaned_data['team']
        team_full(data)
        return data

    class Meta:
        model = UserProfile
        fields = ('email', 'password1', 'password2')


class InviteForm(SubmitMixin, forms.Form):
    required_css_class = 'required'
    error_css_class = 'error'

    email1 = forms.EmailField(
        label=_(u"Email kolegy 1"),
        required=False)

    email2 = forms.EmailField(
        label=_(u"Email kolegy 2"),
        required=False)

    email3 = forms.EmailField(
        label=_(u"Email kolegy 3"),
        required=False)

    email4 = forms.EmailField(
        label=_(u"Email kolegy 4"),
        required=False)


class TeamAdminForm(SubmitMixin, forms.ModelForm):
    required_css_class = 'required'
    error_css_class = 'error'
    campaign = forms.ModelChoiceField(
        label=_(u"Kampaň"),
        queryset=models.Campaign.objects.all(),
        widget=HiddenInput(),
    )

    class Meta:
        model = Team
        fields = ('name', 'campaign')


class PaymentTypeForm(PrevNextMixin, forms.Form):
    CHOICES = [
        ('pay', _(u"Účastnický poplatek si platím sám.")),
        ('member', _(u"Jsem členem Klubu přátel Auto*Matu.")),
        ('member_wannabe', _(u"Chci se stát členem Klubu přátel Auto*Matu.")),
        ('company', _(u"Účastnický poplatek za mě zaplatí zaměstnavatel, mám to domluvené.")),
        ('free', _(u"Je mi poskytováno startovné zdarma."))
    ]

    payment_type = forms.ChoiceField(
        label=_(u"Typ platby"),
        choices=CHOICES,
        widget=forms.RadioSelect(),
    )

    def clean_payment_type(self):
        payment_type = self.cleaned_data['payment_type']
        company = self.user_attendance.team.subsidiary.company
        company_admin = self.user_attendance.get_asociated_company_admin()
        if payment_type == 'company' and not company_admin:
            raise forms.ValidationError(mark_safe(_(u"Váš zaměstnavatel %(employer)s nemá zvoleného koordinátor společnosti.<ul><li><a href='%(url)s'>Chci se stát koordinátorem mé společnosti</a></li></ul>") % {'employer': self.user_attendance.team.subsidiary.company, 'url': reverse('company_admin_application')}))
        elif payment_type == 'company' and not company_admin.can_confirm_payments:
           raise forms.ValidationError(mark_safe(_(u"Koordinátor vašeho zaměstnavatele nemá možnost povolovat platby fakturou.<ul><li>Kontaktujte koordinátora %(company_admin)s vašeho zaměstnavatele %(employer)s na emailu %(email)s</li><li>Koordinátor bude muset nejprve dohodnout spolupráci na adrese <a href='mailto:kontakt@dopracenakole.net?subject=Žádost o povolení firemních plateb'>kontakt@dopracenakole.net</a>.net</li></ul>") % {'company_admin': company_admin, 'employer': company, 'email': company_admin.user.email}))
        return payment_type


class ConfirmDeliveryForm(forms.ModelForm):
    CHOICES = [
        (models.PackageTransaction.Status.PACKAGE_DELIVERY_CONFIRMED, _(u"Startovní balíček mi již byl doručen.")),
        (models.PackageTransaction.Status.PACKAGE_DELIVERY_DENIED, _(u"Startovní balíček mi ještě nebyl doručen.")),
    ]

    status = forms.ChoiceField(
        label=_(u"Doručení balíčku"),
        choices=CHOICES,
        widget=forms.RadioSelect(),
    )

    class Meta:
        model = models.PackageTransaction
        fields = ('status',)


class ConfirmTeamInvitationForm(SubmitMixin, forms.Form):
    question = forms.BooleanField(
        label=_(u"Chci být zařazen do nového týmu"),
    )


class BikeRepairForm(SubmitMixin, forms.ModelForm):
    user_attendance = forms.CharField(
        label=_(u"Uživatelské jméno zákazníka"),
        help_text=_(u"Uživatelské jméno, které vám sdělí zákazník"),
        max_length=100)
    description = forms.CharField(
        label=_(u"Poznámka"),
        max_length=500,
        required=False)

    def clean_user_attendance(self):
        campaign = self.initial['campaign']
        try:
            user_attendance = UserAttendance.objects.get(userprofile__user__username=self.cleaned_data.get('user_attendance'), campaign=campaign)
        except UserAttendance.DoesNotExist:
            raise forms.ValidationError(_(u"Takový uživatel neexistuje"))

        other_user_attendances = user_attendance.other_user_attendances(campaign)
        if other_user_attendances.count() > 0:
            raise forms.ValidationError(_(u"Tento uživatel není nováček, soutěžil již v předcházejících kampaních: %s") % ", ".join([u.campaign.name for u in other_user_attendances]))

        return user_attendance

    def clean(self):
        try:
            transaction = models.CommonTransaction.objects.get(user_attendance=self.cleaned_data.get('user_attendance'), status=models.CommonTransaction.Status.BIKE_REPAIR)
        except models.CommonTransaction.DoesNotExist:
            transaction = None
        if transaction:
            created_formated_date = formats.date_format(transaction.created, "SHORT_DATETIME_FORMAT")
            raise forms.ValidationError(_(u"Tento uživatel byl již %(time)s v cykloservisu %(bike_shop)s (poznámka: %(note)s).") % {
                'time': created_formated_date, 'bike_shop': transaction.author.get_full_name(), 'note': transaction.description
            })
        return super(BikeRepairForm, self).clean()

    def save(self, *args, **kwargs):
        self.instance.status = models.CommonTransaction.Status.BIKE_REPAIR
        return super(BikeRepairForm, self).save(*args, **kwargs)

    class Meta:
        model = models.CommonTransaction
        fields = ('user_attendance', 'description')


class TShirtUpdateForm(PrevNextMixin, models.UserAttendanceForm):
    telephone = forms.CharField(
        label=_(u"Telefon"),
        validators=[RegexValidator(r'^[0-9+ ]*$', _(u'Telefon musí být složen s čísel, mezer a znaku plus.')), MinLengthValidator(9)],
        help_text=_(u"Telefon je pro kurýra, který Vám přiveze soutěžní triko, pro HelpDesk"),
        max_length=30)

    def save(self, *args, **kwargs):
        ret_val = super(TShirtUpdateForm, self).save(*args, **kwargs)
        self.instance.userprofile.telephone = self.cleaned_data.get('telephone')
        self.instance.userprofile.save()
        return ret_val

    def __init__(self, *args, **kwargs):
        ret_val = super(TShirtUpdateForm, self).__init__(*args, **kwargs)
        self.fields['telephone'].initial = self.instance.userprofile.telephone
        return ret_val

    class Meta:
        model = UserAttendance
        fields = ('t_shirt_size', 'telephone', )


class TrackUpdateForm(PrevNextMixin, forms.ModelForm):
    def clean(self):
        cleaned_data = super(TrackUpdateForm, self).clean()
        if cleaned_data['dont_want_insert_track'] == True:
            cleaned_data['track'] = None
        else:
            if cleaned_data['track'] == None:
                raise forms.ValidationError(_(u"Zadejte trasu, nebo zaškrtněte, že trasu nechcete zadávat."))
        return cleaned_data

    class Meta:
        model = UserAttendance
        fields = ('track', 'dont_want_insert_track', 'distance')

    def __init__(self, *args, **kwargs):
        instance = kwargs['instance']
        super(TrackUpdateForm, self).__init__(*args, **kwargs)

        location = None
        if instance.team:
            location = instance.team.subsidiary.city.location
        if not location:
            location = settings.DEFAULT_MAPWIDGET_LOCATION
            default_zoom = settings.DEFAULT_MAPWIDGET_ZOOM
        default_zoom = 13
        self.fields['track'].widget = OSMWidget(attrs={
            'geom_type': 'LINESTRING',
            'default_lat_custom': location.y,
            'default_lon_custom': location.x,
            'default_zoom': default_zoom,
        })
        self.fields['track'].widget.template_name = "gis/openlayers-osm-custom.html"


class ProfileUpdateForm(PrevNextMixin, forms.ModelForm):
    no_prev = True

    first_name = forms.CharField(
        label=_(u"Jméno"),
        max_length=30,
        required=True)
    last_name = forms.CharField(
        label=_(u"Příjmení"),
        max_length=30,
        required=True)

    email = forms.EmailField(
        help_text=_(u"Email slouží jako přihlašovací jméno"),
        required=False)
    dont_show_name = forms.BooleanField(
        label=_(u"Nechci, aby moje skutečné jméno bylo veřejně zobrazováno"),
        required=False,
    )

    def save(self, *args, **kwargs):
        ret_val = super(ProfileUpdateForm, self).save(*args, **kwargs)
        self.instance.user.email = self.cleaned_data.get('email')
        self.instance.user.first_name = self.cleaned_data.get('first_name')
        self.instance.user.last_name = self.cleaned_data.get('last_name')
        self.instance.user.save()
        return ret_val

    def clean_nickname(self):
        nickname = self.cleaned_data['nickname']
        if self.cleaned_data['dont_show_name'] == True:
            if nickname:
                return nickname
            else:
                raise forms.ValidationError(_(u"Pokud si nepřejete zobrazovat své jméno, zadejte, co se má zobrazovat místo něj"))
        else:
            return None

    def clean_email(self):
        """
        Validate that the email is not already in use.
        """
        if User.objects.filter(email__iexact=self.cleaned_data['email']).exclude(pk=self.instance.user.pk).exists():
            raise forms.ValidationError(_(u"Tento email již je v našem systému zanesen."))
        else:
            return self.cleaned_data['email']

    def clean_sex(self):
        if self.cleaned_data['sex'] == 'unknown':
            raise forms.ValidationError(_(u"Zadejte pohlaví"))
        else:
            return self.cleaned_data['sex']

    def __init__(self, *args, **kwargs):
        ret_val = super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        self.fields['email'].initial = self.instance.user.email
        self.fields['first_name'].initial = self.instance.user.first_name
        self.fields['last_name'].initial = self.instance.user.last_name
        self.fields['dont_show_name'].initial = self.instance.nickname != None

        self.helper.layout = Layout(
            'language', 'sex', 'first_name', 'last_name', 'dont_show_name', 'nickname', 'email',
            HTML(_(u'Odesláním tohoto formuláře souhlasím s tím, aby poskytnuté údaje (osobní údaje ve smyslu paragrafu 4 pís. a zákona 101/200 Sb., O ochraně osobních údajů), byly až do odvolání zpracovány občanským sdružením Auto*Mat, o. s. a místně příslušným organizátorem kampaně uvedeným u každého města na tomto webu pro účely kampaně Do práce na kole. ')),
        )
        return ret_val

    class Meta:
        model = UserProfile
        fields = ('language', 'sex', 'first_name', 'last_name', 'dont_show_name', 'nickname', 'email')


class CreateGpxFileForm(SubmitMixin, forms.ModelForm):
    trip_date = forms.DateField(
        label=_(u"Datum cesty"),
    )
    CHOICES = [
        ('trip_to', _(u"Tam")),
        ('trip_from', _(u"Zpět")),
    ]
    direction = forms.ChoiceField(
        label=_(u"Typ platby"),
        choices=CHOICES,
    )

    def clean_user_attendance(self):
        print self.request

    def save(self, *args, **kwargs):
        print args, kwargs
        print self.request

    def __init__(self, request=None, *args, **kwargs):
        ret_val = super(CreateGpxFileForm, self).__init__(*args, **kwargs)
        self.resuest = request
        #    if request:
        #        self.fields['trip'].queryset = models.Trip.objects.filter(user_attendance)
        return ret_val

    class Meta:
        model = models.GpxFile
        fields = ('file', 'trip_date', 'direction')


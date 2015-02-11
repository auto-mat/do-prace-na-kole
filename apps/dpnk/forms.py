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
from crispy_forms.layout import Submit
from django.core.urlresolvers import reverse
from django.contrib.auth.forms import AuthenticationForm


def team_full(data):
    if len(UserAttendance.objects.filter(Q(approved_for_team='approved') | Q(approved_for_team='undecided'), team=data, userprofile__user__is_active=True)) >= 5:
        raise forms.ValidationError(_(u"Tento tým již má pět členů a je tedy plný"))


class SubmitMixin(object):
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', _(u'Odeslat')))
        super(SubmitMixin, self).__init__(*args, **kwargs)


class PrevNextMixin(object):
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        if not hasattr(self, 'no_prev'):
            self.helper.add_input(Submit('prev', _(u'Předchozí')))
        if not hasattr(self, 'no_next'):
            self.helper.add_input(Submit('next', _(u'Další')))
        super(PrevNextMixin, self).__init__(*args, **kwargs)


class AuthenticationFormDPNK(SubmitMixin, AuthenticationForm):
    pass


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


class WorkingScheduleForm(PrevNextMixin, forms.ModelForm):
    schedule = WorkingScheduleField(
        label=_(u"Pracovní rozvrh"),
        required=False,
        )

    def save(self, *args, **kwargs):
        ret_val = super(WorkingScheduleForm, self).save(*args, **kwargs)
        trips = self.cleaned_data['schedule']
        for trip in trips:
            if trip.can_edit:
                trip.save()
        return ret_val

    def __init__(self, *args, **kwargs):
        ret_val = super(WorkingScheduleForm, self).__init__(*args, **kwargs)
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
        instance = kwargs.get('instance', {})
        if instance and instance.team:
            initial['team'] = instance.team
            initial['subsidiary'] = instance.team.subsidiary
            initial['company'] = instance.team.subsidiary.company

        if request:
            if request.GET.get('team', None):
                initial['team'] = request.GET['team']

        kwargs['initial'] = initial

        super(ChangeTeamForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = [
            'company',
            'subsidiary',
            'team',
            ]

    class Meta:
        model = UserAttendance
        fields = ('team',)


class RegistrationAccessFormDPNK(SubmitMixin, forms.Form):
    email = forms.CharField(
        required=True,
        label=_(u"E-mail"),
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
        self.fields.keyOrder = [
            'email',
            'password1',
            'password2'
            ]

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


class InviteForm(forms.Form):
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


class TeamAdminForm(forms.ModelForm):
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


class ConfirmTeamInvitationForm(forms.Form):
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
    class Meta:
        model = UserAttendance
        fields = ('track', 'distance')

    def __init__(self, *args, **kwargs):
        instance = kwargs['instance']
        super(TrackUpdateForm, self).__init__(*args, **kwargs)

        location = instance.team.subsidiary.city.location
        default_zoom = 14
        if not location:
           location = settings.DEFAULT_MAPWIDGET_LOCATION
           default_zoom = settings.DEFAULT_MAPWIDGET_ZOOM
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

    def save(self, *args, **kwargs):
        ret_val = super(ProfileUpdateForm, self).save(*args, **kwargs)
        self.instance.user.email = self.cleaned_data.get('email')
        self.instance.user.first_name = self.cleaned_data.get('first_name')
        self.instance.user.last_name = self.cleaned_data.get('last_name')
        self.instance.user.save()
        return ret_val

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
        return ret_val

    class Meta:
        model = UserProfile
        fields = ('language', 'sex', 'first_name', 'last_name', 'email')

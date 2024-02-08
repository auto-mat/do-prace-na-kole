from import_export import resources
from import_export.fields import Field, widgets

from dpnk.models import UserAttendance

from .models import TShirtSize


class UserAttendanceResource(resources.ModelResource):
    team__subsidiary__address_city = Field()
    name = Field()
    team__subsidiary = Field()
    payment_created = Field()

    class Meta:
        model = UserAttendance
        fields = [
            "id",
            "name",
            "t_shirt_size__name",
            "t_shirt_size__code",
            "team__subsidiary",
            "team__subsidiary__address_city",
            "team__subsidiary__address_psc",
            "payment_created",
            "representative_payment__realized",
        ]
        export_order = fields
        use_natural_foreign_keys = False

    def dehydrate_team__subsidiary__address_city(self, userattendance):
        return str(userattendance.team.subsidiary.city.name)

    def dehydrate_name(self, userattendance):
        return userattendance.userprofile.user.get_full_name()

    def dehydrate_team__subsidiary(self, userattendance):
        return str(userattendance.team.subsidiary)

    def dehydrate_payment_created(self, userattendance):
        return (
            userattendance.payment_created
            if hasattr(userattendance, "payment_created")
            else ""
        )

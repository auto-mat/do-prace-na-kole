import notifications.base.models as n


class DpnkNotificationTemplate(n.AbstractNotification):
    class Meta(n.AbstractNotification.Meta):
        abstract = False
        app_label = "dpnk"

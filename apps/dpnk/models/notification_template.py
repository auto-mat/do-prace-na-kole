import notifications.base.models as n


class DpnkNotificationTemplate(n.AbstractNotificationTemplate):
    class Meta(n.AbstractNotificationTemplate.Meta):
        abstract = False
        app_label = 'dpnk'

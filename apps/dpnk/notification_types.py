from notifications.notification_types import NotificationType


class AloneInTeam(NotificationType):
    slug = "alone-in-team"

    def populate(self, template):
        template.verb = "Jsi sám v týmu."
        template.verb_en = "You are the only person in your team."

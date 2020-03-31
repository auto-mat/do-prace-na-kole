from django.urls import reverse_lazy

from notifications.notification_types import NotificationType


class AloneInTeam(NotificationType):
    slug = "alone-in-team"

    def populate(self, template):
        template.verb = "Jsi sám v týmu."
        template.verb_en = "You are the only person in your team."


def questionnaire_factory(q):
    class Questionnaire(NotificationType):
        slug = "questionnaire-" + q.slug
        questionnaire = q

        def populate(self, template):
            template.verb = "Nezapomeňte výplnit '" + self.questionnaire.name + "'"
            template.verb_en = "Don't forget to fill out '" + self.questionnaire.name + "'"
            template.url = reverse_lazy("questionnaire", kwargs={"questionnaire_slug": q.slug})

        def check_condition(self, recipient):
            return recipient.unanswered_questionnaires().filter(pk=self.questionnaire.pk).exists()

    return Questionnaire()

from django.urls import reverse_lazy

from notifications.notification_types import NotificationType


class RegistrationPhaseNotification(NotificationType):
    def __init__(self, phase):
        self.phase = phase
        super().__init__()

    def in_registration_phase(self, recipient):
        return recipient.campaign.phase('registration').is_actual()


class AloneInTeam(RegistrationPhaseNotification):
    slug = "alone-in-team"

    def populate(self, template):
        template.verb = "Jsi sám v týmu. Pozvěte další členové."
        template.verb_en = "You are the only person in your team."

    def check_condition(self, recipient):
        if self.in_registration_phase(recipient) and \
           recipient.is_libero() and \
           recipient.team and \
           recipient.team.unapproved_member_count == 0:
            return True
        return False


class UnapprovedMembersInTeam(RegistrationPhaseNotification):
    slug = "unapproved-team-members"

    def populate(self, template):
        template.verb = 'Ve Vašem týmu jsou neschválení členové, prosíme, posuďte jejich členství.'
        template.verb_en = "Someone has requested membership in your team."
        template.url = reverse_lazy("team_members")

    def check_condition(self, recipient):
        if self.in_registration_phase(recipient):
            if recipient.approved_for_team == 'approved' and \
                    recipient.team and \
                    recipient.team.unapproved_member_count and \
                    recipient.team.unapproved_member_count > 0:
                return True
        return False


class Questionnaire(NotificationType):
    def __init__(self, q):
        self.slug = "questionnaire-" + q.slug
        self.questionnaire = q
        super().__init__()

    def populate(self, template):
        template.verb = "Nezapomeňte výplnit '" + self.questionnaire.name + "'"
        template.verb_en = "Don't forget to fill out '" + self.questionnaire.name + "'"
        template.url = reverse_lazy("questionnaire", kwargs={"questionnaire_slug": self.questionnaire.slug})

    def check_condition(self, recipient):
        return recipient.unanswered_questionnaires().filter(pk=self.questionnaire.pk).exists()

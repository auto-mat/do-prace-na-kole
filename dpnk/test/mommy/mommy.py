from .answers import Answers
from .campaigns import Campaigns
from .campaign_types import CampaignTypes
from .choices import Choices
from .choice_types import ChoiceTypes
from .cities_in_campaign import CitiesInCampaign
from .cities import Cities
from .commute_modes import CommuteModes
from .companies import Companies
from .company_admins import CompanyAdmins
from .competition_results import CompetitionResults
from .competitions import Competitions
from .groups import Groups
from .invoices import Invoices
from .payments import Payments
from .permissions import Permissions
from .phases import Phases
from .price_levels import PriceLevels
from .questions import Questions
from .subsidiaries import Subsidiaries
from .teams import Teams
from .test_results_data import TestResultsData
from .trips import Trips
from .user_attendances import UserAttendances
from .users import Users

from . import transactions

from .t_shirt_delivery.deliverybatches import DeliveryBatches
from .t_shirt_delivery.packagetransactions import PackageTransactions
from .t_shirt_delivery.subsidiaryboxes import SubsidiaryBoxes
from .t_shirt_delivery.teampackages import TeamPackages
from .t_shirt_delivery.tshirt_sizes import TshirtSizes



target_dag = {
    "answers": (Answers, {"userattendances", "questions", "choices"}),
    "campaigns": (Campaigns, {"campaign_types"}),
    "campaign_types": (CampaignTypes, set()),
    "choices": (Choices, {"choice_types"}),
    "choice_types": (ChoiceTypes, {"competitions"}),
    "cities_in_campaign": (CitiesInCampaign, {"campaigns", "cities"}),
    "cities": (Cities, set()),
    "commute_modes": (CommuteModes, set()),
    "companies": (Companies, {"commute_modes"}),
    "company_admins": (CompanyAdmins, {"users", "campaigns", "companies"}),
    "competition_results": (CompetitionResults, {"competitions", "teams"}),
    "competitions": (Competitions, {"campaigns", "companies", "commute_modes"}),
    "groups": (Groups, {"permissions"}),
    "invoices": (Invoices, {"campaigns", "companies"}),
    "payments": (Payments, {"transactions"}),
    "permissions": (Permissions, set()),
    "phases": (Phases, {"campaigns"}),
    "price_levels": (PriceLevels, {"campaings"}),
    "questions": (Questions, {"competitions"}),
    "subsidiaries": (Subsidiaries, {"cities", "companies"}),
    "teams": (Teams, {"campaigns", "subsidiaries"}),
    "trips": (Trips, {"userattendances", "commutemodes"}),
    "users": (Users, {"groups", "cities", "companies"}),
    "tshirt_sizes": (TshirtSizes, {"campaigns"}),
    "userattendances": (UserAttendances, {"users", "teams", "tshirt_sizes", "campaigns"}),

    "transactions_package_transactions": (transactions.PackageTransactions, {"userattendances"}),
    "transactions_payment_transactions": (transactions.PaymentTransactions, {"userattendances"}),

    #tshirt_delivery
    "deliverybatches": (DeliveryBatches, {"campaigns"}),
    "packagetransactions": (PackageTransactions, {"transactions_package_transactions"}),
    "subsidiaryboxes": (SubsidiaryBoxes, {"deliverybatches"}),
    "teampackages": (TeamPackages, {"subsidiaryboxes"}),
    "tshirt_sizes": (TshirtSizes, {"campaigns"}),

    "test_results_data": (TestResultsData, {"campaigns"}),
}

class Fixtures:
    """
    Sets up a set of testing objects which are used throughout the test suit.

    Assumes that the commute_mode.json fixture is loaded.
    """
    def __init__(self, targets):
        self.sets = {}
        while targets != set(self.sets.keys()):
            print(targets)
            print(self.sets.keys())
            for target_name in list(targets):
                if target_name in self.sets:
                    continue
                target = target_dag[target_name]
                if target_dag[target_name][1].issubset(set(self.sets.keys())):
                    try:
                        self.sets[target_name] = target[0](**self.sets)
                    except Exception as e:
                        raise TypeError(target_name + str(e))
                else:
                    for new_target in target[1]:
                        if new_target not in targets:
                            targets.add(new_target)

    def __getattribute__(self, attr):
        try:
            return super().__getattribute__("sets")[attr]
        except KeyError:
            return super().__getattribute__(attr)

from model_mommy import mommy


class PackageTransactions:
    def __init__(self, transactions, **kwargs):
        self.basic = mommy.make(  # was pk=8
            "t_shirt_delivery.packagetransaction",
            transaction_ptr = 8,
            team_package_id = 7,
            tracking_number = 13112117,
        )
    {
        "fields": {
           "transaction_ptr": 6,
           "team_package_id": 7,
           "tracking_number": 11111117
        },
        "model": "t_shirt_delivery.packagetransaction",
        "pk": 6
    }

    {
        "fields": {
           "transaction_ptr": 7,
           "team_package_id": 7,
           "tracking_number": 11112117
        },
        "model": "t_shirt_delivery.packagetransaction",
        "pk": 7
    },


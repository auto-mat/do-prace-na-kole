from model_mommy import mommy


class PackageTransactions:
    def __init__(self, transactions_package_transactions, **kwargs):
        self.transaction_6 = mommy.make(  # was pk=6
            "t_shirt_delivery.packagetransaction",
            transaction_ptr=6,
            team_package_id=7,
            tracking_number=11111117,
        )
        self.transaction_7 = mommy.make(  # was pk=7
            "t_shirt_delivery.packagetransaction",
            transaction_ptr=7,
            team_package_id=7,
            tracking_number=11112117,
        )
        self.transaction_8 = mommy.make(  # was pk=8
            "t_shirt_delivery.packagetransaction",
            transaction_ptr=8,
            team_package_id=7,
            tracking_number=13112117,
        )

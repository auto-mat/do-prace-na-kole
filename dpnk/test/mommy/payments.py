from model_mommy import mommy


class Payments:
    def __init__(self, transactions, **kwargs):
        self.klub_pratel = mommy.make(  # was pk=9
            "dpnk.payment",
            amount = 150,
            pay_type = "am",
            transaction_ptr = 9,
        )
    {
        "fields": {
            "amount": 150,
            "pay_type": "fc",
            "trans_id": "2055-1",
            "session_id": "2075-1J1455206453",
            "transaction_ptr": 5
        },
        "model": "dpnk.payment",
        "pk": 5
    },
    {
        "fields": {
            "amount": 150,
            "trans_id": "2075-1",
            "session_id": "2075-1J1455206433",
            "transaction_ptr": 3
        },
        "model": "dpnk.payment",
        "pk": 3
    },
    {
        "fields": {
            "amount": 145,
            "pay_type": "fc",
            "trans_id": "2075-2",
            "session_id": "2075-1J1455206444",
            "transaction_ptr": 4
        },
        "model": "dpnk.payment",
        "pk": 4
    },
    {
        "fields": {
            "amount": 145,
            "pay_type": "fc",
            "trans_id": "2075-2",
            "session_id": "2075-1J145520666",
            "transaction_ptr": 16
        },
        "model": "dpnk.payment",
        "pk": 16
    },
    {
        "fields": {
            "amount": 145,
            "pay_type": "fc",
            "trans_id": "2075-3",
            "session_id": "2075-1J145520667",
            "transaction_ptr": 17
        },
        "model": "dpnk.payment",
        "pk": 17
	},
    {
        "fields": {
            "amount": 145,
            "pay_type": "fc",
            "trans_id": "2075-3",
            "session_id": "2075-1J145520668",
            "transaction_ptr": 18
        },
        "model": "dpnk.payment",
        "pk": 18
	}


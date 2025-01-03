"""PayU payment system"""

import requests
import logging

from django.conf import time

from . import models
from .models import Payment, PayUOrderedProduct

logger = logging.getLogger(__name__)


class PayU:
    """Create new PayU order and save it as new Payment model"""

    def __init__(self, payu_conf):
        """Initializer

        :param dict_payu_conf: PayU config, see Django settings conf file
                               PAYU_CONF global var
        {
          "PAYU_REST_API_CLIENT_ID": <SET>,
          "PAYU_REST_API_CLIENT_SECRET": <SET>,
          "PAYU_REST_API_SECOND_KEY_MD5": <SET>,
          "PAYU_REST_API_AUTH_URL": <SET>,
          "PAYU_REST_API_CREATE_ORDER_URL": <SET>,
          "PAYU_REST_API_CREATE_ORDER_CURRENCY_CODE": <SET>,
        }
        """
        self._payu_conf = payu_conf

    def _delete_payment(self, order_id):
        """Delete PayU order from DB Payment model

        :param str order_id: Unique RTWBB internal app order id

        :return None
        """
        Payment.object.filter(
            order_id=order_id,
            status=models.Status.CANCELED,
        ).delete()

    def _save_payment(
        self,
        amount,
        order_id,
        product_name,
        products,
        payment_subject,
        payment_category,
        user_attendance,
    ):
        """Save PayU new order into DB as new Payment model

        :param int amount: Order PayU amount
        :param str order_id: Unique RTWBB internal app order id
        :param str product_name: Product name(s) which you buy
        :param list products: PayU ordered products
                              [
                                {
                                  "name": "RTWBB challenge entry fee",
                                  "unitPrice": 400,
                                  "quantity": 1,
                                },
                                {
                                  "name": "RTWBB donation",
                                  "unitPrice": 500,
                                  "quantity": 1,
                                }
                              ]
        :param str payment_subject: Payment subject, see Payment model
                                    PAYMENT_SUBJECT constant
        :param str payment_category: Payment category, see Payment model
                                     PAYMENT_CATEGORY constant
        :param UserAttendance user_attendance: UserAttendace model instance

        :return None
        """
        payu_ordered_products = []
        for product in products:
            payu_ordered_product, created = PayUOrderedProduct.objects.get_or_create(
                name=product["name"],
                unit_price=product["unitPrice"],
                quantity=product["quantity"],
            )
            payu_ordered_products.append(payu_ordered_product)

        payment = Payment(
            session_id=f"{order_id}J{int(time.time())}",
            user_attendance=user_attendance,
            order_id=order_id,
            amount=amount,
            pay_subject=payment_subject,
            pay_category=payment_category,
            status=models.Status.NEW,
            description=product_name,
        ).save()
        payment.payu_ordered_product.set(payu_ordered_products)
        logger.info(
            "PayU create order, save new payment model order_id <%s>",
            order_id,
        )

    def authorize(self):
        """Get PayU authorization Bearer token

        :return dict response_data: PayU authorization successfull/error
                                    response data

        Successfull response data:

        {
          "access_token":"xxxx-xxxx-xxxx-xxxx-xxxx",
          "token_type":"bearer",
          "expires_in":43199,
          "grant_type":"client_credentials"
        }

        Error response data:

        {
          "error":"invalid_client",
          "error_description":"Bad client credentials"
        }
        """

        # PayU authorization
        data = {
            "grant_type": "client_credentials",
            "client_id": self._payu_conf["PAYU_REST_API_CLIENT_ID"],
            "client_secret": self._payu_conf["PAYU_REST_API_CLIENT_SECRET"],
        }
        try:
            response = requests.post(
                url=self._payu_conf["PAYU_REST_API_AUTH_URL"],
                data=data,
            )
            response_data = response.json()
        except requests.exceptions.RequestException as error:
            response_data = {"error": str(error)}

        access_token = response_data.get("access_token")
        if not access_token:
            response_data["error_part"] = "authorization"
        return response_data

    def create_order(
        self, access_token, data, product_name="RTWBB challenge entry fee"
    ):
        """Create new PayU order and save it as new Payment model

        :param str access_token: PayU Bearer authorization access token
        :param dict data: Input data dict required for creation new Pay
                          order
        {
          "amount": 300,
          "products": [
            {
              "name": "RTWBB challenge entry fee",
              "unitPrice": 400,
              "quantity": 1,
            },
            {
              "name": "RTWBB donation",
              "unitPrice": 500,
              "quantity": 1,
            }
          ]
          "customerIp": "127.0.0.1",
          "extOrderId": "1-10",
          "userAttendance": <UserAttendance: Test Test>,
          "buyer": {
                     "email": "test@test.org",
                     "phone": "0000000000",
                     "firstName": "Test",
                     "lastName": "Test",
                     "language": "cs"
          }
        }
        :param str product_name: PayU order product name, with default value
                                'RTWBB challenge entry fee'

        :return dict response_data: Successfully newly PayU created order
                                    response data or error data

        Sucessfull response data:

        {
          "status": {
            "statusCode": "SUCCESS"
          },
          "redirectUri": "https://merch-prod.snd.payu.com/pay/?orderId=QB8N27RXGZ241125GUEST000P01...,
          "orderId": "QB8N27RXGZ241125GUEST000P01",
          "extOrderId": "1-9"
        }

        Error response data:

        {
          "status": {
            "statusCode": "ERROR_ORDER_NOT_UNIQUE",
            "code": "110",
            "codeLiteral": "ORDER_NOT_UNIQUE",
            "statusDesc": "Order with given extOrderId already exists"
        },
          "orderId": "HM8M9WX7J8241125GUEST000P01",
          "extOrderId": "1-10",
          "error_part": "create_order"
        }

        """
        sucess_status = "SUCCESS"
        # PayU create order
        headers = {
            "Authorization": f"Bearer {access_token}",
        }
        order_data = {
            "notifyUrl": data["notifyUrl"],
            "extOrderId": data["extOrderId"],
            "customerIp": data["customerIp"],
            "merchantPosId": self._payu_conf["PAYU_REST_API_CLIENT_ID"],
            "description": product_name,
            "currencyCode": self._payu_conf["PAYU_REST_API_CREATE_ORDER_CURRENCY_CODE"],
            "totalAmount": data["amount"],
            "buyer": data["buyer"],
            "products": data["products"],
        }
        logger.info("PayU create order data <%s>.", order_data)
        try:
            # Disable allow redirects fix returning JSON response data instead of HTML content
            response = requests.post(
                url=self._payu_conf["PAYU_REST_API_CREATE_ORDER_URL"],
                json=order_data,
                headers=headers,
                allow_redirects=False,
            )
            response_data = response.json()
        except requests.exceptions.RequestException as error:
            response_data = {"error": str(error)}

        # Save new successfully create PayU order as Payment model
        if (
            response_data.get("status")
            and response_data["status"].get("statusCode") == sucess_status
        ):
            self._save_payment(
                order_id=data["extOrderId"],
                product_name=" + ".join(
                    [product["name"] for product in data["products"]]
                ),
                products=data["products"],
                payment_subject=data["paymentSubject"],
                payment_category=data["paymentCategory"],
                amount=data["amount"],
                user_attendance=data["userAttendance"],
            )

        if (
            response_data.get("status")
            and response_data["status"].get("statusCode") != sucess_status
        ) or (not response_data.get("status")):
            response_data["error_part"] = "create_order"
        return response_data

    def delete_order(self, access_token, payu_order_id):
        """Delete PayU order according PayU order ID

        :param str access_token: PayU Bearer authorization access token
        :param str payu_order_id: PayU order ID

        :return dict response_data: Successfully canceled order response
                                    data or error data

        Sucessfull response data:

        {'extOrderId': '1-12',
         'orderId': '8QVBS5HG5X241126GUEST000P01',
         'status': {'statusCode': 'SUCCESS',
                    'statusDesc': 'Request processing successful'}}


        Error response data:

        {'status': {'severity': 'INFO',
                    'statusCode': 'DATA_NOT_FOUND',
                    'statusDesc': 'Could not find user order '
                                  '[orderId=8QVBS5HG5X241126GUEST000P01e]'}}
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.delete(
                url=f"{self._payu_conf['PAYU_REST_API_CREATE_ORDER_URL']}/{payu_order_id}",
                headers=headers,
            )
            response_data = response.json()
        except requests.exceptions.RequestException as error:
            response_data = {"error": str(error)}

        # Delete order from DB Payment model
        if (
            response_data.get("status")
            and response_data.get("status")["statusCode"] == "SUCCESS"
        ):
            self._delete_payment(order_id=response_data.get("extOrderId"))

        return response_data

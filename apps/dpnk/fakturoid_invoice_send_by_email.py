"""Send Fakturoid HTML invoice by email"""

import logging
import requests

from django.conf import settings

logger = logging.getLogger(__name__)


def send_invoice_by_email(invoice, fa):
    """Send invoce by email

    :param class instance fa: fakturoid.Fakturoid class instance
    :param class instance: Invoice model class instance
    """
    email_base_url = (
        "{base_rest_api_url}/accounts/{fakturoid_user_account_slug}"
        "/invoices/{invoice_custom_id}/message.json"
    )
    error_message = (
        "Sending Fakturoid invoice with custom_id={invoice_custom_id}"
        " by email wasn't succesfull with Fakturoid testing account"
        " '{fakturoid_user_account_slug}' due error: '{error}'"
    )
    data = f'{{"email": "{fa.email}"}}'
    post_data(
        invoice=invoice,
        fa=fa,
        url=email_base_url,
        error_message=error_message,
        data=data,
    )


def post_data(invoice, fa, url, error_message, data):
    """
    Post JSON data

    :param class instance fa: fakturoid.Fakturoid class instance
    :param class instance: Invoice model class instance
    :param str url: URL
    :param str error_messsage: base error message
    :param str data: JSON data string
    """
    try:
        response = requests.post(
            url.format(
                base_rest_api_url=settings.FAKTUROID["base_rest_api_url"],
                fakturoid_user_account_slug=fa.slug,
                invoice_custom_id=invoice.id,
            ),
            headers={
                "User-Agent": fa.user_agent,
                "Content-Type": "application/json",
            },
            auth=requests.auth.HTTPBasicAuth(
                fa.email,
                fa.api_key,
            ),
            data=data,
        )
        if not response.ok:
            logger.error(
                error_message.format(
                    invoice_custom_id=invoice.id,
                    fakturoid_user_account_slug=fa.slug,
                    error=response.status_code,
                )
            )
    except (
        requests.RequestException,
        requests.ConnectionError,
        requests.HTTPError,
        requests.URLRequired,
        requests.TooManyRedirects,
        requests.Timeout,
    ) as error:
        logger.error(
            error_message.format(
                invoice_custom_id=invoice.id,
                fakturoid_user_account_slug=fa.slug,
                error=error,
            )
        )

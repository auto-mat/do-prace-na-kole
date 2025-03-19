"""Create Fakturoid invoice using API V3"""

import decimal
import logging
import re
import requests
import json
import base64
from datetime import datetime

from django.conf import settings

logger = logging.getLogger(__name__)


def get_invoice(session, base_url, invoice_id):
    """Get Fakturoid invoice by custom ID using API V3

    :param session: requests session with authentication
    :param str base_url: Base URL for API calls
    :param str/int invoice_id: ID of the invoice to retrieve

    :return dict/None: Fakturoid Invoice data or None
    """
    error_message = (
        "Getting Fakturoid invoice with ID {invoice_id}"
        " wasn't successful with Fakturoid account"
        " '{fakturoid_account}' due error: '{error}'"
    )

    try:
        # Get invoice by ID
        response = session.get(f"{base_url}/invoices.json?custom_id={invoice_id}")
        response.raise_for_status()
        return response.json()[0]
    except requests.RequestException as error:
        logger.error(
            error_message.format(
                invoice_id=invoice_id,
                fakturoid_account=base_url.split("/")[-2],
                error=error,
            )
        )
        return None


def delete_invoice(session, base_url, invoice_id):
    """Delete Fakturoid invoice by ID using API V3

    :param session: requests session with authentication
    :param str base_url: Base URL for API calls
    :param str/int invoice_id: ID of the invoice to delete

    :return bool: True if successful, False otherwise
    """
    error_message = (
        "Deleting Fakturoid invoice with ID {invoice_id}"
        " wasn't successful with Fakturoid account"
        " '{fakturoid_account}' due error: '{error}'"
    )

    try:
        fakturoid_id = get_invoice(session, base_url, invoice_id)["id"]
        # Delete invoice by ID
        response = session.delete(f"{base_url}/invoices/{fakturoid_id}.json")

        # If successfully deleted, the server will respond with status 204 No Content
        if response.status_code == 204:
            return True

        # If invoice cannot be deleted, the server will respond with status 422 Unprocessable Entity
        if response.status_code == 422:
            logger.error(
                f"Invoice with ID {invoice_id} cannot be deleted. "
                "This may be because it's a proforma with connected paid invoice, "
                "an invoice with correction invoice, a proforma with tax documents, "
                "a tax document with connected invoice, or the document is locked."
            )
            return False

        # Handle other error responses
        response.raise_for_status()
        return True

    except requests.RequestException as error:
        logger.error(
            error_message.format(
                invoice_id=invoice_id,
                fakturoid_account=base_url.split("/")[-2],
                error=error,
            )
        )
        return False

def delete_subject(session, base_url, subject_id):
    """Delete Fakturoid subject by ID using API V3

    :param session: requests session with authentication
    :param str base_url: Base URL for API calls
    :param str/int subject_id: ID of the subject to delete

    :return bool: True if successful, False otherwise
    """
    error_message = (
        "Deleting Fakturoid subject with ID {subject_id}"
        " wasn't successful with Fakturoid account"
        " '{fakturoid_account}' due error: '{error}'"
    )

    try:
        # Delete subject by ID
        response = session.delete(f"{base_url}/subjects/{subject_id}.json")

        # If successfully deleted, the server will respond with status 204 No Content
        if response.status_code == 204:
            return True

        # If subject cannot be deleted because it contains documents, 
        # the server will respond with status 403 Forbidden
        if response.status_code == 403:
            logger.error(
                f"Subject with ID {subject_id} cannot be deleted. "
                "This is likely because the subject contains documents."
            )
            return False

        # Handle other error responses
        response.raise_for_status()
        return True

    except requests.RequestException as error:
        logger.error(
            error_message.format(
                subject_id=subject_id,
                fakturoid_account=base_url.split("/")[-2],
                error=error,
            )
        )
        return False


def create_or_update_subject(session, base_url, invoice):
    """Create or update Fakturoid subject using API V3

    :param session: requests session with authentication
    :param str base_url: Base URL for API calls
    :param class instance invoice: Invoice model class instance

    :return dict/None: Fakturoid Subject data or None
    """
    error_message = (
        "{state} Fakturoid subject {subject_custom_id}"
        " wasn't successful with Fakturoid account"
        " '{fakturoid_account}' due error: '{error}'"
    )

    # Subject data
    pattern = re.compile(r"\s+")
    fa_subject_data = {
        "custom_id": str(invoice.company.id),
        "name": invoice.company_name,
        "street": (
            f"{invoice.company.address.street or ''} "
            f"{invoice.company.address.street_number or ''}"
        ).strip(),
        "zip": invoice.company_address_psc,
        "country": invoice.country or "CZ",
        "registration_no": invoice.company_ico,
        "vat_no": invoice.company_dic,
        "city": invoice.company_address_city,
        "phone": re.sub(
            pattern,
            "",
            invoice.company_admin_telephones().split(",")[0],
        ),
        "note": invoice.client_note,
    }

    fa_subject_emails = invoice.company_admin_emails().split(",")
    fa_subject_data["email"] = fa_subject_emails[0]
    if len(fa_subject_emails) == 2:
        fa_subject_data["email_copy"] = fa_subject_emails[1]

    # Check if subject exists
    try:
        response = session.get(f"{base_url}/subjects.json", params={"custom_id": invoice.company.id})
        response.raise_for_status()
        subjects = response.json()

        if subjects:
            # Update existing subject
            subject_id = subjects[0]["id"]
            state = "Update"
            subject_custom_id = f"with custom_id = {invoice.company.id}"
            response = session.patch(
                f"{base_url}/subjects/{subject_id}.json",
                json=fa_subject_data
            )
            response.raise_for_status()
            return response.json()
        else:
            # Create new subject
            state = "Create"
            subject_custom_id = ""
            response = session.post(
                f"{base_url}/subjects.json",
                json=fa_subject_data
            )
            response.raise_for_status()
            return response.json()
    except requests.RequestException as error:
        logger.error(
            error_message.format(
                state=state,
                subject_custom_id=subject_custom_id,
                fakturoid_account=base_url.split("/")[-2],
                error=error,
            )
        )
        return None


def create_invoice_lines(invoice):
    """Make Fakturoid invoice lines

    :param class instance invoice: Invoice model class instance

    :return list lines: list of invoice line dictionaries
    """
    lines = []
    for payment in invoice.payment_set.order_by(
        "user_attendance__userprofile__user__last_name",
        "user_attendance__userprofile__user__first_name",
    ):
        if invoice.company_pais_benefitial_fee:
            amount = invoice.campaign.benefitial_admission_fee_company
        else:
            amount = payment.amount
        user_name = (
            "" if invoice.anonymize else payment.user_attendance.name_for_trusted()
        )
        description = f"Platba za soutěžící/ho {user_name}"
        lines.append({
            "name": description,
            "quantity": 1,
            "unit_price": str(decimal.Decimal(amount)),
            "vat_rate": 0
        })
    return lines


def create_or_update_invoice(session, base_url, subject, invoice):
    """Create or update Fakturoid invoice using API V3

    :param session: requests session with authentication
    :param str base_url: Base URL for API calls
    :param dict subject: Fakturoid subject data
    :param class instance invoice: Invoice model class instance

    :return dict/None: Fakturoid Invoice data or None
    """
    error_message = (
        "{state} Fakturoid invoice {invoice_custom_id}"
        " wasn't successful with Fakturoid account"
        " '{fakturoid_account}' due error: '{error}'"
    )

    # Check if invoice exists
    try:
        response = session.get(f"{base_url}/invoices.json", params={"custom_id": invoice.id})
        response.raise_for_status()
        invoices = response.json()

        fa_invoice_data = {
            "custom_id": str(invoice.id),
            "subject_id": subject["id"],
            "order_number": invoice.order_number,
            "lines": create_invoice_lines(invoice=invoice)
        }

        if invoices:
            # Update existing invoice
            invoice_id = invoices[0]["id"]
            state = "Update"
            invoice_custom_id = f"with custom_id = {invoice.id}"

            # First, clear existing lines
            response = session.patch(
                f"{base_url}/invoices/{invoice_id}.json",
                json={"lines": []}
            )
            response.raise_for_status()

            # Then update with new data
            response = session.patch(
                f"{base_url}/invoices/{invoice_id}.json",
                json=fa_invoice_data
            )
            response.raise_for_status()
            return response.json()
        else:
            # Create new invoice
            state = "Create"
            invoice_custom_id = ""
            response = session.post(
                f"{base_url}/invoices.json",
                json=fa_invoice_data
            )
            response.raise_for_status()
            return response.json()
    except requests.RequestException as error:
        logger.error(
            error_message.format(
                state=state,
                invoice_custom_id=invoice_custom_id,
                fakturoid_account=base_url.split("/")[-2],
                error=error,
            )
        )
        return None


def obtain_access_token(client_id, client_secret):
    """Obtain or refresh OAuth access token for Fakturoid API V3

    :param str account: Fakturoid account type "production" or "test"

    :return str/None: Access token or None if failed
    """
    error_message = (
        "Obtaining access token wasn't successful with Fakturoid"
        " client_id '{client_id}' due error: '{error}'"
    )

    # Create the authorization header using HTTP Basic auth
    auth_string = f"{client_id}:{client_secret}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')

    # Common headers for all requests
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Basic {auth_b64}'
    }

    data = {
        'grant_type': "client_credentials",
    }

    # Try with JSON content type first
    json_headers = headers.copy()
    json_headers['Content-Type'] = 'application/json'

    response = requests.post(
        settings.FAKTUROID["base_rest_api_url"] + '/oauth/token',
        json=data,
        headers=json_headers
    )

    try:
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(
            error_message.format(
                client_id=client_id,
                error=str(e)
            )
        )
        return None

    token_data = response.json()

    return token_data['access_token']


def create_api_session(account):
    """Create authenticated session for Fakturoid API V3 using OAuth

    :param str account: Fakturoid account type "production" or "test"

    :return tuple: (session, base_url) or (None, None)
    """
    error_message = (
        "Creating Fakturoid API session wasn't successful with Fakturoid"
        " account '{fakturoid_account}' due error: '{error}'"
    )

    try:
        # Get access token
        access_token = obtain_access_token(
            client_id=settings.FAKTUROID[account]["client_id"],
            client_secret=settings.FAKTUROID[account]["client_secret"],
        )
        
        if not access_token:
            return None, None

        # Create session with OAuth Bearer token
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        })

        slug = settings.FAKTUROID[account]["user_account"]
        fa_base_url = settings.FAKTUROID["base_rest_api_url"]
        base_url = f"{fa_base_url}/accounts/{slug}"

        # Test the connection
        response = session.get(f"{base_url}/account.json")
        response.raise_for_status()

        return session, base_url
    except requests.RequestException as error:
        logger.error(
            error_message.format(
                fakturoid_account=settings.FAKTUROID[account]["user_account"],
                error=error,
            )
        )
        return None, None


def send_invoice_by_email(session, base_url, invoice_data, fakturoid_account):
    """Send invoice by email using API V3

    :param session: requests session with authentication
    :param str base_url: Base URL for API calls
    :param dict invoice_data: Fakturoid invoice data
    :param str fakturoid_account: Fakturoid account type
    """
    error_message = (
        "Sending Fakturoid invoice with id={invoice_id}"
        " by email wasn't successful with Fakturoid account"
        " '{fakturoid_account}' due error: '{error}'"
    )

    try:
        data = {}
        if fakturoid_account == "test":
            data = {"email": settings.FAKTUROID[fakturoid_account]["user_email"]}

        response = session.post(
            f"{base_url}/invoices/{invoice_data['id']}/message.json",
            json=data
        )
        response.raise_for_status()
    except requests.RequestException as error:
        logger.error(
            error_message.format(
                invoice_id=invoice_data["id"],
                fakturoid_account=base_url.split("/")[-2],
                error=error,
            )
        )


def generate_invoice(invoice, fakturoid_account=None):
    """Generate Fakturoid invoice using API V3

    :param class instance invoice: Invoice model class instance
    :param str fakturoid_account: Fakturoid account type "production" or "test"

    :return dict/None: Fakturoid Invoice data or None
    """
    fa_invoice = None
    date_from_create_invoices = settings.FAKTUROID["date_from_create_invoices"]

    if not fakturoid_account:
        if not date_from_create_invoices or not invoice.generate_fakturoid_invoice:
            fakturoid_account = "test"
        else:
            fakturoid_account = "production"

    if settings.FAKTUROID[fakturoid_account]["user_account"]:
        session, base_url = create_api_session(account=fakturoid_account)

        if session and base_url:
            # Subject
            fa_subject = create_or_update_subject(
                session=session, 
                base_url=base_url, 
                invoice=invoice
            )

            if fa_subject:
                # Invoice
                fa_invoice = create_or_update_invoice(
                    session=session,
                    base_url=base_url,
                    invoice=invoice,
                    subject=fa_subject,
                )

                # Send email
                if fa_invoice:
                    send_invoice_by_email(
                        session=session,
                        base_url=base_url,
                        invoice_data=fa_invoice,
                        fakturoid_account=fakturoid_account,
                    )

    return fa_invoice

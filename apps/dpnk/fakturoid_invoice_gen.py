"""Create Fakturoid invoice"""

import decimal
import logging
import requests

from django.conf import settings

from fakturoid import Fakturoid, Invoice, InvoiceLine, Subject

from .fakturoid_invoice_send_by_email import send_invoice_by_email

logger = logging.getLogger(__name__)


def create_or_update_subject(fa, invoice):
    """Create or update Fakturoid subject

    :param class instance fa: fakturoid.Fakturoid class instance
    :param class instance: Invoice model class instance

    :return Fakturoid Subject class instance/None fa_subject: Fakturoid
                                                              Subject class
                                                              instance
                                                              or None
    """
    error_message = (
        "{state} Fakturoid subject {subject_custom_id}"
        " wasn't succesfull with Fakturoid account"
        " '{fakturoid_user_account_slug}' due error: '{error}'"
    )
    # Subject
    fa_subject_data = {
        "custom_id": invoice.company.id,
        "name": invoice.company_name,
        "street": (
            f"{invoice.company.address.street or ''} "
            f"{invoice.company.address.street_number or ''}",
        ),
        "zip": invoice.company_address_psc,
        "country": invoice.country or "CZ",
        "registration_no": invoice.company_ico,
        "vat_no": invoice.company_dic,
        "city": invoice.company_address_city,
        "phone": invoice.company_admin_telephones(),
        "note": invoice.client_note,
    }
    fa_subject_emails = invoice.company_admin_emails().split(",")
    fa_subject_data["email"] = fa_subject_emails[0]
    if len(fa_subject_emails) == 2:
        fa_subject_data["email_copy"] = fa_subject_emails[1]

    fa_subject = fa.subjects(custom_id=invoice.company.id)
    if not fa_subject:
        fa_subject = Subject(**fa_subject_data)
        state = "Create"
        subject_custom_id = ""
    else:
        fa_subject = fa_subject[0]
        fa_subject.update(fa_subject_data)
        state = "Update"
        subject_custom_id = f"with custom_id = {fa_subject.custom_id}"
    try:
        fa.save(fa_subject)
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
                state=state,
                subject_custom_id=subject_custom_id,
                invoice_custom_id=invoice.id,
                fakturoid_user_account_slug=fa.slug,
                error=error,
            )
        )
        fa_subject = None
    return fa_subject


def create_invoice_lines(invoice):
    """Make Fakturoiud invoice lines

    :param class instance invoice: Invoice model class instance

    :return list lines: list of InvoiceLine class model instaces
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
        lines.append(
            # https://fakturoid.docs.apiary.io/#reference/lines
            InvoiceLine(
                name=description,
                quantity=1,
                unit_price=decimal.Decimal(amount),
                vat_rate=21,
            )
        )
    return lines


def create_or_update_invoice(fa, subject, invoice):
    """Create or update Fakturoid invoice

    :param class instance fa: fakturoid.Fakturoid class instance
    :param class instance subject: fakturoid.Subject model class instance
    :param class instance: Invoice model class instance

    :return Fakturoid Invoice class instance/None fa_invoice: Fakturoid
                                                              Invoice
                                                              class instance
                                                              or None
    """
    error_message = (
        "{state} Fakturoid invoice {subject_custom_id}"
        " wasn't succesfull with Fakturoid account"
        " '{fakturoid_user_account_slug}' due error: '{error}'"
    )
    # Invoice
    fa_invoice = fa.invoices(custom_id=invoice.id)
    try:
        fa_invoice = list(fa_invoice)[0]
    except IndexError:
        fa_invoice = None
    fa_invoice_data = {
        "custom_id": invoice.id,
        "subject_id": subject.id,
        "number": (
            f"{invoice.exposure_date.year}D"
            f"{invoice.sequence_number:0{settings.FAKTUROID['invoice_number_width']}d}"
        ),  # #yyyy#D#dddd#
        "order_number": invoice.order_number,
        "lines": [],
    }
    if not fa_invoice:
        fa_invoice_data["lines"] = create_invoice_lines(invoice=invoice)
        fa_invoice = Invoice(**fa_invoice_data)
        state = "Create"
        subject_custom_id = ""
    else:
        fa_invoice.lines = []
        fa.save(fa_invoice)
        fa_invoice_data["lines"] = create_invoice_lines(invoice=invoice)
        fa_invoice.update(fa_invoice_data)
        state = "Update"
        subject_custom_id = f"with custom_id = {fa_invoice.custom_id}"
    try:
        fa.save(fa_invoice)
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
                state=state,
                subject_custom_id=subject_custom_id,
                fakturoid_user_account_slug=fa.slug,
                error=error,
            )
        )
        fa_invoice = None
    return fa_invoice


def get_fakturoid_api(account):
    """Get Fakturoid API class instance

    :param str account: Fakturoid account type "production" or "test"

    :return class instance fakturoid.Fakturoid/None fa: Fakturoid API class
                                                        instance or None
    """
    error_message = (
        "Get Fakturoid API instance wasn't succesfull with Fakturoid"
        " account '{fakturoid_user_account_slug}' due error: '{error}'"
    )
    try:
        fa = Fakturoid(
            slug=settings.FAKTUROID[account]["user_account"],
            email=settings.FAKTUROID[account]["user_email"],
            api_key=settings.FAKTUROID[account]["api_key"],
            user_agent=settings.FAKTUROID[account]["user_agent_header"],
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
                fakturoid_user_account_slug=fa.slug,
                error=error,
            )
        )
        fa = None
    return fa


def generate_invoice(invoice, fakturoid_account=None):
    """Generate Fakturoid invoice

    :param class instance: Invoice model class instance
    :param str account: Fakturoid account type "production" or "test"

    :return Fakturoid Invoice class instance/None fa_invoice: Fakturoid
                                                              Invoice or
                                                              None
    """
    fa_invoice = None
    date_from_create_invoices = settings.FAKTUROID["date_from_create_invoices"]
    if not fakturoid_account:
        if not date_from_create_invoices or not invoice.generate_fakturoid_invoice:
            fakturoid_account = "test"
        else:
            fakturoid_account = "production"
    if settings.FAKTUROID[fakturoid_account]["user_account"]:
        fa = get_fakturoid_api(account=fakturoid_account)
        if fa:
            # Subject
            fa_subject = create_or_update_subject(fa=fa, invoice=invoice)
            if fa_subject:
                # Invoice
                fa_invoice = create_or_update_invoice(
                    fa=fa,
                    invoice=invoice,
                    subject=fa_subject,
                )
                # Send email
                send_invoice_by_email(invoice=fa_invoice, fa=fa)
        return fa_invoice

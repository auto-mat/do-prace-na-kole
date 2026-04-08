import csv
import logging
import subprocess
from subprocess import PIPE, Popen

from bs4 import BeautifulSoup

from django.conf import settings
from django.utils import timezone

# from dpnk.test.util import print_response

import requests

from .mygls import MyGLS
from ..tasks import update_subsidiary_box

logger = logging.getLogger(__name__)


def get_mygls_parcel_label_data(csv_file):
    """Get MyGLS create parcel data

    :param file object csv_file: Opened file object

    :return tuple (list, list, list, list, list) delivery_address,
           parcel_property, content, reference, count: Tuple of lists of parcel label
                                                       delivery address, property,
                                                       content, reference, and count
    """
    # Delivery address
    delivery_address = []
    # Parcel property
    parcel_property = []
    # Parcel content
    content = []
    # Parcel count
    count = []
    # Parcel reference
    reference = []

    sep = ";"
    csv_reader = csv.reader(csv_file, delimiter=sep)
    for line in csv_reader:
        header = line
        break
    for line in csv_reader:
        address = {}
        parcel_prop = {}

        # Delivery address
        city_idx = header.index("Příjemce - Město")
        city = line[city_idx]
        address["City"] = city

        contact_email_idx = header.index("Příjemce - kontaktní email")
        contact_email = line[contact_email_idx]
        address["ContactEmail"] = contact_email

        contact_name_idx = header.index("Přijemce - kontaktní osoba")
        contact_name = line[contact_name_idx]
        address["ContactName"] = contact_name

        contact_phone_idx = header.index("Přijemce - kontaktní telefon")
        contact_phone = line[contact_phone_idx]
        address["ContactPhone"] = contact_phone

        country_iso_code_idx = header.index("Příjemce - Stát")
        country_iso_code = line[country_iso_code_idx]
        address["CountryIsoCode"] = country_iso_code

        house_number_idx = header.index("Příjemce - Číslo ulice")
        house_number = line[house_number_idx]
        address["HouseNumber"] = house_number

        name_idx = header.index("Příjemce - Název")
        name = line[name_idx]
        address["Name"] = name

        street_idx = header.index("Příjemce - Ulice")
        street = line[street_idx]
        address["Street"] = street

        zip_code_idx = header.index("Příjemce - PSČ")
        zip_code = line[zip_code_idx]
        address["ZipCode"] = zip_code

        address["HouseNumberInfo"] = ""

        delivery_address.append(address)

        # Parcel property
        parcel_prop["PackageType"] = 2  # Box

        package_length_idx = header.index("Délka")
        package_length = line[package_length_idx]
        parcel_prop["Length"] = package_length

        package_width_idx = header.index("Šířka")
        package_width = line[package_width_idx]
        parcel_prop["Width"] = package_width

        package_height_idx = header.index("Výška")
        package_height = line[package_height_idx]
        parcel_prop["Height"] = package_height

        package_weight_idx = header.index("Hmotnost")
        package_weight = line[package_weight_idx]
        parcel_prop["Weight"] = round(float(package_weight), 2)

        parcel_property.append(parcel_prop)

        # Parcel content
        content_idx = header.index("Popis zboží")
        content.append(line[content_idx])

        # Parcel count
        count_idx = header.index("Počet")
        count.append(int(line[count_idx]))

        # Parcel reference
        reference_idx = header.index("Variabilní symbol")
        reference.append(line[reference_idx])

    return delivery_address, parcel_property, content, reference, count


def handle_prepare_labels_errors(csv_error_file, prepare_labels_errors):
    """Handle prepare labels errors

    :param str csv_error_file: CSV prepare labels error file path
    :param list prepare_labels_errors: List of prepare labels errors

    :return tuple (bytes, str): Tuple of CSV byte file content contains
                                prepare labels validation errors and CSV
                                format postfix
    """
    err_code = "Error code"
    err_desc = "Error description"
    client_ref_list = "Client reference list (variable symbol)"
    with open(csv_error_file, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                err_code,
                err_desc,
                client_ref_list,
            ],
        )
        writer.writeheader()

        for err in prepare_labels_errors:
            writer.writerow(
                {
                    err_code: err.ErrorCode,
                    err_desc: err.ErrorDescription,
                    client_ref_list: "; ".join(err.ClientReferenceList),
                }
            )
    return csv_error_file, "csv"


def generate_mygls_pdf_part(csv_file, batch, pdf_file):
    """Generate partial print labels PDF file via MyGLS REST API

    :param file object csv_file: Opened file object
    :param DeliveryBatch batch: DeliveryBatch model instance
    :param str pdf_file: Printed labels PDF file path

    :return tuple (bytes, str): Tuple of CSV byte file content contains
                                prepare labels validation errors and CSV
                                format postfix, default value is (None, None)
                                if no prepare labels validation errors are appear
    """
    # Get MyGLScreate parcel data
    (
        delivery_address,
        parcel_property,
        content,
        reference,
        count,
    ) = get_mygls_parcel_label_data(csv_file)

    mygls = MyGLS()
    datetime_before = timezone.datetime.now()

    # Create parcel
    mygls.create_parcel(
        delivery_address=delivery_address,
        pickup_date=timezone.datetime.combine(
            batch.pickup_date, timezone.datetime.min.time()
        ),
        parcel_property=parcel_property,
        content=content,
        reference=reference,
        count=count,
    )
    # Handle prepare labels validation errors
    prepare_lables_response = mygls.prepare_labels()
    if prepare_lables_response.PrepareLabelsError:
        return handle_prepare_labels_errors(
            csv_error_file=csv_file.name.replace(".csv", "_err.csv"),
            prepare_labels_errors=prepare_lables_response.PrepareLabelsError,
        )
    # Print labels
    parcel_ids = mygls.print_labels(pdf_path=pdf_file)
    datetime_after = timezone.datetime.now()

    update_subsidiary_box.delay(
        print_from=datetime_before.timestamp(),
        print_to=datetime_after.timestamp(),
    )
    return None, None


def generate_pdf_part(csv_file, batch):
    print("generating PDF from GLS")
    print(f"File: {csv_file}")
    gls_url = settings.GLS_BASE_URL
    session = requests.Session()

    login_data = {
        "password": settings.GLS_PASSWORD,
        "username": settings.GLS_USERNAME,
        "lessersecurity": "on",
    }
    response0 = session.post(gls_url + "/login.php", data=login_data)
    # print_response(response0)
    if "Database connection error" in response0.content.decode("utf-8"):
        return response0.content, ".error.txt"

    # ----------remove uploaded file-------------------------
    data = {
        "module": "preparedparcel",
        "controller": "listPage",
        "cmd": "prepareNewFile",
        "pkey": "",
        "version": "18050702",
        "MAX_FILE_SIZE": "1048576",
        "targetpnum": "",
        "frompage": "1",
        "isheader": "on",
        "separator": ";",
        "importfile_encoding": "UTF-8",
    }

    response1a = session.post(gls_url + "/subindex.php", data=data)
    # print_response(response1a, filename="response1a.html")

    # ----------choose preset----------------------------

    data = {
        "module": "preparedparcel",
        "controller": "listPage",
        "cmd": "importPage",
        "pkey": "",
        "version": "18050702",
        "targetpnum": "1",
        "frompage": "0",
        "assignment_id": "0",
    }

    response1 = session.post(gls_url + "/subindex.php", data=data)
    # print_response(response1, filename="response1.html")

    # -----------upload new file---------------------

    data = {
        "module": "preparedparcel",
        "controller": "listPage",
        "cmd": "importPage",
        "pkey": "",
        "version": "18050702",
        "MAX_FILE_SIZE": "1048576",
        "targetpnum": "2",
        "frompage": "1",
        "isheader": "off",
        "separator": ";",
        "importfile_encoding": "UTF-8",
    }

    files = {"importfile": ("test_batch.csv", csv_file, "text/csv")}

    response2 = session.post(gls_url + "/subindex.php", files=files, data=data)
    # print_response(response2, filename="response2.html")

    # -----------------------------------------------

    data = {
        "module": "preparedparcel",
        "controller": "listPage",
        "cmd": "importPage",
        "pkey": "",
        "version": "18091802",
        "targetpnum": "3",
        "frompage": "2",
        "assignname": "",
        "senderid_const": "on",
        "senderid": "050013079",
        "gapid": "0",
        "from_name_const": "on",
        "from_name": "AutoMat, Do práce na kole",
        "from_address_const": "on",
        "from_address": "Slezská 11",
        "from_zip_const": "on",
        "from_zip": "120 00",
        "from_city_const": "on",
        "from_city": "Praha 2",
        "from_ctrcode_const": "on",
        "from_ctrcode": "CZ",
        "from_contact_const": "on",
        "from_contact": "AutoMat",
        "from_phone_const": "on",
        "from_phone": "212 240 666",
        "from_email_const": "on",
        "from_email": "kontakt@dopracenakole.cz",
        "to_name": 2,
        "to_address": "5",
        "to_zip": "6",
        "to_city": "4",
        "to_ctrcode": "3",
        "to_contact": "7",
        "to_phone": "9",
        "to_email": "8",
        "pickupd_const": "on",
        "pickupd": batch.pickup_date.strftime("%d.%m.%Y"),
        "pcount_const": "on",
        "pcount": "1",
        "pinfo": "19",
        "codamount": "0",
        "codref": "0",
        "clientref": "15",
        "services": "0",
        "saveParcelImportTemplate": "",
    }

    response3 = session.post(gls_url + "/subindex.php", data=data)
    # print_response(response3, filename="response3.html")

    # -----------download failed pages-------------------------

    data = {
        "module": "preparedparcel",
        "controller": "listPage",
        "cmd": "downloadFailedCsv",
        "pkey": "",
        "version": "18050702",
        "filterrad": "off",
        "do_search": "0",
        "searchtxt": "",
        "frompage": "-1",
        "targetpnum": "0",
    }

    response4 = session.post(gls_url + "/subindex.php", data=data)
    # print_response(response4, filename="response4.html")

    try:
        error_csv_filename = (
            response4.content.decode("utf8")
            .split("\n")[0]
            .split('value="')[1]
            .split('"')[0]
        )
        error_csv = session.get(gls_url + "/" + error_csv_filename)
    except IndexError:
        error_csv = None

    # -----------------------------------------------

    data = {
        "module": "preparedparcel",
        "controller": "listPage",
        "cmd": "printAll",
        "pkey": "",
        "version": "18050702",
        "filterrad": "off",
        "do_search": "0",
        "searchtxt": "",
        "frompage": "-1",
        "targetpnum": "0",
    }

    response5 = session.post(gls_url + "/subindex.php", data=data)

    if error_csv:
        # In case when there is error CSV, we want it to be the only output.
        # But we need to print PDF to clear the package queue.
        return error_csv.content, ".error.csv"

    # print_response(response5, filename="response5.html")
    soup = BeautifulSoup(response5.text, features="lxml")
    try:
        addr = gls_url + "/" + soup.find("body").find("iframe").attrs["src"]
    except AttributeError:
        logger.exception(
            "Failed to communicate with GLS website",
            extra={
                "response0": response0.text,
                "response1": response1.text,
                "response1a": response1a.text,
                "response2": response2.text,
                "response3": response3.text,
                "response4": response4.text,
                "response5": response5.text,
            },
        )
    """
    If caling this URL addr var return error message: URL not found 404 error
    You must manually login into web page https://online.gls-czech.com/index.php#
    and check "Importování údajů o štítcích" page list. There is a limit for
    500 rows. If limit is exceeded you should delete all rows from the web
    page and execute Admin action "Nahrát data do GLS a vytvořit PDF" again.
    """
    response = session.get(addr)
    # with open("batch.pdf", "wb") as f:
    #     f.write(response.content)
    print("Generating PDF from GLS completed")
    return response.content, "pdf"


def generate_pdf(csv_file, batch):
    subprocess.call(["rm", "tmp_gls", "-R"])
    subprocess.call(["mkdir", "tmp_gls"])
    from .. import tasks

    csv_filename = tasks.save_filefield(csv_file, "tmp_gls")
    subprocess.call(["scripts/batch_generation/split_csv.sh", csv_filename, "500"])
    p = Popen(
        ["bash", "-c", "ls tmp_gls/delivery_batch_splitted_*"],
        stdin=PIPE,
        stdout=PIPE,
        stderr=PIPE,
    )
    output, err = p.communicate()
    for csv_file_part in output.decode("utf-8").split("\n"):
        if csv_file_part:
            with open(csv_file_part) as f:
                pdf_part, pdf_ext = generate_pdf_part(f, batch)
            with open(csv_file_part + ".pdf", "wb+") as f:
                f.write(pdf_part)
            if ".error." in pdf_ext:  # We return errors after first occurrence
                return csv_file_part + ".pdf", pdf_ext
    subprocess.call(
        ["bash", "-c", "pdftk tmp_gls/*.pdf cat output tmp_gls/gls_sheet.pdf"]
    )
    return "tmp_gls/gls_sheet.pdf", "pdf"


def generate_mygls_pdf(csv_file, batch):
    subprocess.call(["rm", "tmp_gls", "-R"])
    subprocess.call(["mkdir", "tmp_gls"])
    from .. import tasks

    csv_filename = tasks.save_filefield(csv_file, "tmp_gls")
    # 99 is max number of parcels for the printing labels via MyGLS REST API URL endpoint
    subprocess.call(["scripts/batch_generation/split_csv.sh", csv_filename, "99"])
    p = Popen(
        ["bash", "-c", "ls tmp_gls/delivery_batch_splitted_*"],
        stdin=PIPE,
        stdout=PIPE,
        stderr=PIPE,
    )
    output, err = p.communicate()
    for csv_file_part in output.decode("utf-8").split("\n"):
        if csv_file_part:
            with open(csv_file_part) as f:
                try:
                    csv_error_part, csv_ext = generate_mygls_pdf_part(
                        f,
                        batch,
                        pdf_file=f"{csv_file_part}.pdf",
                    )
                    if csv_error_part:
                        return csv_error_part, csv_ext
                except Exception as e:
                    if hasattr(e, "message"):
                        logger.exception(e.message)
                    else:
                        logger.exception(e)

    p = Popen(
        ["bash", "-c", "pdftk tmp_gls/*.pdf cat output tmp_gls/gls_sheet.pdf"],
        stdin=PIPE,
        stdout=PIPE,
        stderr=PIPE,
    )
    output, err = p.communicate()
    if p.returncode != 0:
        logger.exception(f"Concatenate GLS labels PDFs files error <{err}>.")
    return "tmp_gls/gls_sheet.pdf", "pdf"

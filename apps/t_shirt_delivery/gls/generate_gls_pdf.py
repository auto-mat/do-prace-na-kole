import datetime
import logging
import subprocess
from subprocess import PIPE, Popen

from bs4 import BeautifulSoup

from django.conf import settings

# from dpnk.test.util import print_response

import requests

logger = logging.getLogger(__name__)


def generate_pdf_part(csv_file):
    gls_url = settings.GLS_BASE_URL
    session = requests.Session()

    login_data = {
        'password': settings.GLS_PASSWORD,
        'username': settings.GLS_USERNAME,
        'lessersecurity': "on",
    }
    response0 = session.post(gls_url + '/login.php', data=login_data)
    # print_response(response)

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

    response1a = session.post(gls_url + '/subindex.php', data=data)
    # print_response(response, filename="response1a.html")

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

    response1 = session.post(gls_url + '/subindex.php', data=data)
    # print_response(response, filename="response1.html")

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

    files = {'importfile': ('test_batch.csv', csv_file, 'text/csv')}

    response2 = session.post(gls_url + '/subindex.php', files=files, data=data)
    # print_response(response, filename="response2.html")

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
        "from_address": "Vodičkova 36",
        "from_zip_const": "on",
        "from_zip": "110 00",
        "from_city_const": "on",
        "from_city": "Praha",
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
        "pickupd": datetime.date.today().strftime("%d.%m.%Y"),
        "pcount_const": "on",
        "pcount": "1",
        "pinfo": "19",
        "codamount": "0",
        "codref": "0",
        "clientref": "15",
        "services": "0",
        "saveParcelImportTemplate": "",
    }

    response3 = session.post(gls_url + '/subindex.php', data=data)
    # print_response(response, filename="response3.html")

    # -----------download failed pages-------------------------

    data = {
        "module": "preparedparcel",
        "controller": "listPage",
        "cmd": "downloadFailedCsv",
        "pkey": "",
        "version": "18050702",
        "filterrad": "off",
        "frompage": "-1",
        "targetpnum": "0",
        "do_search": "0",
        "searchtxt": "",
        "frompage": "-1",
        "targetpnum": "0",
    }

    response4 = session.post(gls_url + '/subindex.php', data=data)
    # print_response(response, filename="response4.html")

    # -----------------------------------------------

    data = {
        "module": "preparedparcel",
        "controller": "listPage",
        "cmd": "printAll",
        "pkey": "",
        "version": "18050702",
        "filterrad": "off",
        "frompage": "-1",
        "targetpnum": "0",
        "do_search": "0",
        "searchtxt": "",
        "frompage": "-1",
        "targetpnum": "0",
    }

    response5 = session.post(gls_url + '/subindex.php', data=data)
    # print_response(response, filename="response5.html")
    soup = BeautifulSoup(response5.text, features="lxml")
    try:
        addr = gls_url + "/" + soup.find('body').find('iframe').attrs['src']
    except AttributeError:
        logger.exception(
            'Failed to communicate with GLS website',
            extra={
                'response0': response0.text,
                'response1': response1.text,
                'response1a': response1a.text,
                'response2': response2.text,
                'response3': response3.text,
                'response4': response4.text,
                'response5': response5.text,
            },
        )
    response = session.get(addr)
    # with open("batch.pdf", "wb") as f:
    #     f.write(response.content)
    return response.content


def generate_pdf(csv_file):
    subprocess.call(["rm", "tmp_gls", "-R"])
    subprocess.call(["mkdir", "tmp_gls"])
    from .. import tasks
    csv_filename = tasks.save_filefield(csv_file, "tmp_gls")
    subprocess.call(["scripts/batch_generation/split_csv.sh", csv_filename, "500"])
    p = Popen(['bash', '-c', 'ls tmp_gls/delivery_batch_splitted_*'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output, err = p.communicate()
    for csv_file_part in output.decode("utf-8").split("\n"):
        if csv_file_part:
            with open(csv_file_part) as f:
                pdf_part = generate_pdf_part(f)
            with open(csv_file_part + ".pdf", "wb+") as f:
                f.write(pdf_part)
    subprocess.call(["bash", "-c", "pdftk tmp_gls/*.pdf cat output tmp_gls/gls_sheet.pdf"])
    return "tmp_gls/gls_sheet.pdf"

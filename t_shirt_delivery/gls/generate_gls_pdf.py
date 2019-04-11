from bs4 import BeautifulSoup

from django.conf import settings

from dpnk.test.util import print_response  # noqa

import requests


def generate_pdf(csv_file):
    gls_url = settings.GLS_BASE_URL
    session = requests.Session()

    login_data = {
        'password': settings.GLS_PASSWORD,
        'username': settings.GLS_USERNAME,
        'lessersecurity': "on",
    }
    response = session.post(gls_url + '/login.php', data=login_data)
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

    response = session.post(gls_url + '/subindex.php', data=data)
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
        "assignment_id": "1047",
    }

    response = session.post(gls_url + '/subindex.php', data=data)
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

    response = session.post(gls_url + '/subindex.php', files=files, data=data)
    # print_response(response, filename="response2.html")

    # -----------------------------------------------

    data = {
        "module": "preparedparcel",
        "controller": "listPage",
        "cmd": "importPage",
        "pkey": "",
        "version": "18050702",
        "targetpnum": "3",
        "frompage": "2",
        "assignname": "Auto*Mat",
        "senderid_const": "on",
        "senderid": "050013079",
        "gapid": "1",
        "from_name_const": "on",
        "from_name": "Auto*Mat, Do práce na kole",
        "from_address_const": "on",
        "from_address": "Vodičkova 36",
        "from_zip_const": "on",
        "from_zip": "110 00",
        "from_city_const": "on",
        "from_city": "Praha",
        "from_ctrcode_const": "on",
        "from_ctrcode": "CZ",
        "from_contact_const": "on",
        "from_contact": "Auto*mat",
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
        "pickupd": "09.04.2019",
        "pcount_const": "on",
        "pcount": "1",
        "pinfo_const": "on",
        "pinfo": "Nezastihnete-li adresáta, volejte Auto*Mat: 212 240 666",
        "codamount": "0",
        "codref": "0",
        "clientref": "15",
        "services": "0",
        "saveParcelImportTemplate": "",
    }

    response = session.post(gls_url + '/subindex.php', data=data)
    # print_response(response, filename="response3.html")

    # -----------------------------------------------

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
        "searchtxt": "frompage: -1",
        "targetpnum": "0",
    }

    response = session.post(gls_url + '/subindex.php', data=data)
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

    response = session.post(gls_url + '/subindex.php', data=data)
    # print_response(response, filename="response5.html")
    soup = BeautifulSoup(response.text, features="lxml")
    addr = "http://online.gls-czech.com/" + soup.find('body').find('iframe').attrs['src']
    response = session.get(addr)
    # with open("batch.pdf", "wb") as f:
    #     f.write(response.content)
    return response.content

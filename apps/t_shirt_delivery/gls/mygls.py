import gls

from enum import Enum

from django.conf import settings
from django.utils import timezone
from gls import (
    Address,
    CountryCode,
    GLS,
    Parcel,
    ParcelProperty,
    PrinterType,
    Settings,
)


class MyGLS:
    """Communicating with MyGLS REST API https://api.mygls.hu/index_en.html

    Usage Python mygls-lib https://github.com/adamkornafeld/mygls-python

    MyGLS REST API doc:

    https://api.mygls.hu/index_en.html
    https://api.mygls.hu/docs/MyGLS_API.pdf

    :param str webshop_engine: Webshop engine, default value is
                              'Auto*Mat RTWBB web app'
    :param int timeout_seconds: Request timeout in seconds, default
                                value120 second
    """

    class GetParcelStatusLangIsoCode(Enum):
        EN = "EN"
        HR = "HR"
        CS = "CS"
        HU = "HU"
        RO = "RO"
        SK = "SK"
        SL = "SL"

    def __init__(self, webshop_engine="Auto*Mat RTWBB web app", timeout_seconds=120):
        self._parcels = []
        self._gls = gls.GLS(
            client_number=settings.MYGLS_API["client_number"],
            username=settings.MYGLS_API["username"],
            password=settings.MYGLS_API["password"],
            webshop_engine=webshop_engine,
            settings=Settings(
                country=getattr(CountryCode, settings.MYGLS_API["country_code"]),
                test=settings.MYGLS_API["use_test_account"],
                timeout_seconds=timeout_seconds,
            ),
        )

    def create_parcel(
        self,
        delivery_address=[],
        pickup_from_address=[],
        parcel_property=[],
        count=1,
        content="",
        pickup_date=None,
        reference="",
    ):
        """Create parcel

        :param list delivery_address: Delivery address list
        :param list pickup_from_address: Pickup from address list
        :param list parcel_property: Parcel property list
        :param list|int count: Parcel count list
        :param list|str content: Parcel content list, default value is
                                 empty string
        :param datetime|None pickup_date: Parcel pickup date time, default
                                          value is None (if None actual date
                                          time will be used)
        :param list reference|str: Parcel reference list, default value is
                                   empty string

        :return None
        """
        if not pickup_from_address:
            pickup_from_address = settings.MYGLS_API["pickup_address"]
        if not pickup_date:
            pickup_date = timezone.datetime.now()

        for idx, delivery_addr in enumerate(delivery_address):

            if isinstance(pickup_from_address, (list, tuple)):
                pickup_addr = pickup_from_address[idx]
            else:
                pickup_addr = pickup_from_address

            if isinstance(parcel_property, (list, tuple)):
                parcel_prop = parcel_property[idx]
            else:
                parcel_prop = parcel_property

            parcel = self._gls.create_parcel(
                pickup_from=Address(**pickup_addr),
                deliver_to=Address(**delivery_addr),
                parcel_property=ParcelProperty(**parcel_prop),
                pickup_date=pickup_date,
                reference=reference[idx]
                if isinstance(reference, (list, tuple))
                else reference,
                content=content[idx] if isinstance(content, (list, tuple)) else content,
                count=count[idx] if isinstance(count, (list, tuple)) else count,
            )
            self._parcels.append(parcel)

    def print_labels(self, pdf_path=None, printer_type=None, additional_parcels=[]):
        """Print parcel labels

        :param str|None pdf_path: PDF label file path, default value
                                  is None (if None temporary PDF file path
                                  will be used)
        :param str|None printer_type: Printer type according PrinterType enum,
                                      default value is None (if None global
                                      printer type settings MYGLS_API["printer_type"]
                                      will be used)
        :param list additional_parcels: Additional parcels object list, default value is empty
                                        list

        :return str pdf_path|None: PDF label file path or None if input parcels is
                                   empty list
        """
        if not pdf_path:
            import tempfile

            pdf_path = f"{tempfile.TemporaryDirectory().name}/labels.pdf"

        if not printer_type:
            printer_type = getattr(
                PrinterType, settings.MYGLS_API["printer_type"], PrinterType.THERMO
            )

        if not self._parcels + additional_parcels:
            return

        return self._gls.print_labels(
            pdf_path=pdf_path,
            parcels=self._parcels + additional_parcels,
            printer_type=printer_type,
        )
        return pdf_path

    def get_parcels(
        self, print_from=None, print_to=None, pickup_from=None, pickup_to=None
    ):
        """Get parcels

        :param datetime|None print_from: Parcel datetime print from,
                                         default value is None
        :param datetime|None print_to: Parcel datetime print to,
                                       default value is None
        :param datetime|None pickup_from: Parcel datetime pickup from,
                                          default value is None
        :param datetime|None pickup_to: Parcel datetime pickup to,
                                        default value is None

        :return None
        """
        return self._gls.get_parcels(
            print_from=print_from,
            print_to=print_to,
            pickup_from=pickup_from,
            pickup_to=pickup_to,
        )

    def delete_labels(self, parcel_id=[]):
        """Delete labels

        :param list|None parcel_id: Parcel id list, default value
                                    is empty list (if empty list,
                                    internal list of parcels will
                                    be used)
        :return None
        """
        return self._gls.delete_labels(self._parcels if not parcel_id else parcel_id)

    def parcel_status(
        self,
        parcel_number,
        return_pod=False,
        language_iso_code=None,
    ):
        """Get parcel status

        :param int parcel_number: Parcel number
        :paran bool return_pod: Return PDF file byte arrey (POD field),
                                default value is False
        :param str language_iso_code: Language ISO 639-1 code, default
                                      value is None (if None global get
                                      parcel status lang ISO code setting
                                      MYGLS_API["get_parcel_status_lang_iso_code"]
                                      will be used, allowed options are
                                      EN, HR, CS, HU, RO, SK, SL)

        :return object: ParcelStatusResponse object wih ParcelStatusList key
                        which contains parcel status list
        """
        if not language_iso_code:
            language_iso_code = getattr(
                self.GetParcelStatusLangIsoCode,
                settings.MYGLS_API["get_parcel_status_lang_iso_code"],
                self.GetParcelStatusLangIsoCode.EN,
            )

        return self._gls.parcel_status(
            parcel_id=parcel_number,
            return_pod=return_pod,
            language_iso_code=language_iso_code,
        )

    def prepare_labels(
        self,
        parcels=[],
    ):
        """Prepare labels

        :param list parcel: List of parcels

        :return object: PrepareLabelsResponse object
        """
        return self._gls.prepare_labels(
            parcels=self._parcels if not parcels else parcels,
        )

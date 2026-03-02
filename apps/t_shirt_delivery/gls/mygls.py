import gls

from django.conf import settings
from django.utils import timezone
from gls import (
    Address,
    CountryCode,
    GLS,
    Parcel,
    ParcelProperty,
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

    def __init__(self, webshop_engine="Auto*Mat RTWBB web app", timeout_seconds=120):
        self._parcels = []
        self._gls = gls.GLS(
            client_number=setting.MYGLS_API["client_number"],
            username=setting.MYGLS_API["username"],
            password=setting.MYGLS_API["password"],
            webshop_engine=webshop_engine,
            settings=Settings(
                country=getattr(CountryCode, setting.MYGLS_API["country_code"]),
                test=setting.MYGLS_API["test"],
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
            pickup_date = timezone.now()

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

    def print_label(self, pdf_path=None):
        """Print parcel label

        :param str|None pdf_path: PDF label file path, default value
                                  is None (if None temporary PDF file path
                                  will be used)

        :return str pdf_path: PDF label file path
        """
        if not pdf_path:
            import tempfile

            pdf_path = f"{tempfile.TemporaryDirectory().name}/labels.pdf"

        return self._gls.print_labels(
            pdf_path=pdf_path,
            parcels=self._parcels,
        )
        return pdf_path

    def get_parcel(self, print_from=None, print_to=None):
        """Get parcel

        :param datetime|None print_from: Parcel datetime print from,
                                         default value is None (if None
                                         actual datetime is used)
        :param datetime|None print_to: Parcel datetime print to,
                                       default value is None (if None
                                       actual datetime is used)
        :return None
        """
        if not print_from:
            print_from = timezone.now()
        if not print_to:
            print_to = timezone.now()

        return self._gls.get_parcels(
            print_from=print_from,
            print_to=print_to,
        )

    def delete_label(self, parcel_id=[]):
        """Delete label

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
        language_iso_code="EN",
    ):
        """Get parcel status

        :param int parcel_number: Parcel number
        :paran bool return_pod: Return PDF file byte arrey (POD field),
                                default value is False
        :param str language_iso_code: Language ISO 639-1 code, default
                                      value is 'EN' (allowed options are
                                      HR, CS, HU, RO, SK, SL)

        :return dict: Dict wih ParcelStatusList key which contains
                      parcel status list
        """
        return self._gls.parcel_status(
            parcel_number,
            return_pods,
            language_iso_code,
        )

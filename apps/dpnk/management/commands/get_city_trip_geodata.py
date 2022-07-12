import argparse
import os
import tempfile
import subprocess

from django.db import connection
from django.conf import settings
from django.core.management import BaseCommand, CommandError
from django.utils import timezone
from django.utils.translation import gettext as _

import osmnx as ox


def float_range_validator(min_val, max_val):
    """Float range type validator

    :param int min_val: min value
    :param int max_val: max value

    :return func validator: validator func
    """

    def validator(arg):
        """Validator

        :param str|int|float arg: arg

        :return float f: float arg
        """
        try:
            f = float(arg)
        except ValueError:
            raise argparse.ArgumentTypeError(_("Must be a floating point number"))
        if f <= min_val or f >= max_val:
            raise argparse.ArgumentTypeError(
                _(
                    "Argument {val} must be < {max_val} and > {min_val}".format(
                        val=f,
                        min_val=min_val,
                        max_val=max_val,
                    )
                )
            )
        return f

    return validator


class Command(BaseCommand):
    """Get city user defined buffer clipped trip geodata as GPKG format"""

    help = (
        "Get city user defined buffer clipped trip line geodata"
        " as GPKG format"  # noqa
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--city",
            dest="city",
            required=True,
            help=_("Czechia city name e.g 'Brandýs nad Labem'"),
        )
        parser.add_argument(
            "--buffer",
            dest="buffer",
            type=float_range_validator(0, 40000),
            required=True,
            help=_("Buffer around city district, use meter unit"),
        )
        parser.add_argument(
            "--aws_s3_gpkg_dir",
            dest="aws_s3_gpkg_dir",
            type=str,
            default="exported_trip_gpkg",
            help=_("AWS S3 Bucket GPKG geodata directory"),
        )

    def _get_clip_trip_sql(
        self,
        pg_city_buffer,
        pg_city,
        buffer,
        pg_input_clipped,
        pg_input,
    ):
        """Get SQL for create buffer and clip input table by buffer

        :param str pg_city_buffer: output PG city buffer table name
        :param str pg_city: PG city table name
        :param float buffer: buffer around PG city table in meter unit
        :param str pg_input_clipped: output PG clipped table name
        :param str pg_input: input PG table name which will be clipped

        :return str: return SQL
        """
        # Create buffer
        sql = (
            "CREATE TABLE %s AS ("
            "SELECT ST_Buffer(%s.the_geom::geography, %s) FROM %s);"
            % (
                pg_city_buffer,
                pg_city,
                buffer,
                pg_city,
            )
        )
        # Clip input by buffer
        sql += (
            "CREATE TABLE %s AS (SELECT ST_Intersection(input.the_geom,"
            " clip.st_buffer)"
            " AS clipped FROM %s as clip,"
            " %s as input"
            " WHERE ST_Intersects(clip.st_buffer, input.the_geom));"
            % (
                pg_input_clipped,
                pg_city_buffer,
                pg_input,
            )
        )
        return sql

    def _get_ogr_pg_conn(self, db_settings):
        """Get ogr2ogr PostGIS connection string

        :param dict db_settings: django DB setings

        :return str: ogr2ogr PG connection string
        """
        return (
            f" PG:\"dbname='{db_settings['NAME']}'"
            f" host='{db_settings['HOST']}'"
            f" port='{5432 if not db_settings['PORT'] else db_settings['PORT']}'"
            f" user='{db_settings['USER']}'"
            f" password='{db_settings['PASSWORD']}'\""
        )

    def _upload_shp_to_pg(self, city_shp, db_settings, pg_city, shp_suffix):
        """Upload city shapefile to PostGIS

        :param str city_shp: city shapefile path
        :param dict db_settings: django DB setings
        :param str pg_city: PG city table name
        :param str shp_suffix: shapefile suffix ".shp"

        :return None
        """

        # Upload city district shapefile to PostGIS DB
        subprocess.check_output(
            "ogr2ogr -f PostgreSQL"
            f"{self._get_ogr_pg_conn(db_settings)}"
            f" -nln {pg_city}"  # PG table name
            " -sql 'SELECT osm_id AS osm_id, geometry AS the_geom FROM"  # rename columns
            f" {os.path.basename(city_shp).removesuffix(shp_suffix)}'"
            " -dialect SQLite"
            f" {city_shp}",
            shell=True,
        )

    def _export_pg_table_to_gpkg(
        self,
        exported_gpkg,
        db_settings,
        pg_city,
        pg_input_clipped,
    ):
        """Upload city shapefile to PostGIS

        :param str exported_gpkg: exported clipped PG trip table to GPKG
                                  format path
        :param dict db_settings: django DB setings
        :param str pg_city: PG city table name
        :param str pg_input_clipped: PG input clipped trip table name

        :return None
        """
        # Export clipped trip to GPKG format
        subprocess.check_output(
            "ogr2ogr -f GPKG"
            f" {exported_gpkg}"
            f"{self._get_ogr_pg_conn(db_settings)}"
            f" -nln {pg_city}"  # GPKG table name
            f" -sql 'SELECT * FROM {pg_input_clipped}'",
            shell=True,
        )

    def _drop_pg_tables(
        self,
        cursor,
        tables,
    ):
        """Drop PostGIS tables

        :param django.db.backends.utils.CursorDebugWrapper cursor: Django DB connection
                                                                   cursor
        :param list tables: list of tables for dropping

        :return None
        """

        # Drop tables
        cursor.execute("DROP TABLE IF EXISTS %s" % (", ".join(tables)))

    def handle(self, *args, **options):
        city = options.get("city")
        buffer = options.get("buffer")
        aws_s3_bucket_exported_gpkgs_dir = options.get("aws_s3_gpkg_dir")

        db_settings = settings.DATABASES["default"]
        shp_suffix = ".shp"

        try:
            city_boundary = ox.geocode_to_gdf(f"Czechia, {city}")
        except ValueError:
            raise CommandError(
                _(
                    "'{city}' city was not found."
                    " Try again with correct name, please.".format(city=city),
                )
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            city_shp = os.path.join(temp_dir, "city.shp")

            pg_input = "dpnk_trip_anonymized"
            pg_city = os.path.basename(city_shp).removesuffix(shp_suffix)
            pg_city_buffer = f"{pg_city}_buffer"
            pg_input_clipped = "trip"

            aws_s3_bucket_mnt_dir = os.path.join(
                os.path.expanduser("~"),
                "mnt",
            )

            exported_gpkg = os.path.join(
                aws_s3_bucket_mnt_dir,
                aws_s3_bucket_exported_gpkgs_dir,
                f"trip_{timezone.now().strftime('%Y-%m-%d-%H-%M')}.gpkg",
            )
            if not os.path.exists(aws_s3_bucket_mnt_dir):
                os.mkdir(aws_s3_bucket_mnt_dir)

            with connection.cursor() as cursor:
                self._drop_pg_tables(
                    cursor,
                    tables=[pg_city, pg_city_buffer, pg_input_clipped],
                )
                # Export city distric to the shapefile
                city_boundary.to_file(city_shp)
                # Upload shapefile to PostGIS DB
                self._upload_shp_to_pg(
                    city_shp,
                    db_settings,
                    pg_city,
                    shp_suffix,
                )
                # Clip trip table by city buffer
                cursor.execute(
                    self._get_clip_trip_sql(
                        pg_city_buffer,
                        pg_city,
                        buffer,
                        pg_input_clipped,
                        pg_input,
                    )
                )
                # Mount AWS S3 Bucket
                mnt_s3_sh_script = os.path.join(
                    os.path.dirname(__file__),
                    "mount_aws_s3_bucket.sh",
                )
                cmd = (
                    f"{mnt_s3_sh_script} {temp_dir}"
                    f" {aws_s3_bucket_mnt_dir}"
                    f" {aws_s3_bucket_exported_gpkgs_dir}"
                )
                subprocess.check_output(
                    cmd,
                    shell=True,
                )
                # Export clipped trip table to GPKG format
                self._export_pg_table_to_gpkg(
                    exported_gpkg,
                    db_settings,
                    pg_city,
                    pg_input_clipped,
                )
                # Umount AWS S3 bucket
                subprocess.check_output(
                    f"fusermount -u {aws_s3_bucket_mnt_dir}",
                    shell=True,
                )
                self._drop_pg_tables(
                    cursor,
                    tables=[pg_city, pg_city_buffer, pg_input_clipped],
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        _(
                            "Result city <{city}> trip geodata GPKG file"
                            " <{gpkg}> with buffer distance <{buffer} m>"
                            " was uploaded into AWS S3 Bucket <{s3_bucket}>"
                            " into destination dir <{dest_dir}/>.".format(
                                buffer=buffer,
                                s3_bucket=os.getenv("DPNK_AWS_STORAGE_BUCKET_NAME"),
                                dest_dir=aws_s3_bucket_exported_gpkgs_dir,
                                city=city,
                                gpkg=os.path.basename(exported_gpkg),
                            )
                        )
                    )
                )

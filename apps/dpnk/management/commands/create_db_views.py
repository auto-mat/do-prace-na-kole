#!/usr/bin/env python

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    materialized_views = ("data_core_reporting",)
    views = ("data_dpnk_core_reporting",)
    all_views = materialized_views + views
    help = f"Creates, refreshes, dropes the DB {', '.join(all_views)} views."

    def add_arguments(self, parser):
        parser.add_argument(
            "--refresh",
            action="store_true",
            help=f"Refresh existing views <{', '.join(self.all_views)}> instead of recreating it.",
        )
        parser.add_argument(
            "--drop",
            action="store_true",
            help=f"Drop the views <{', '.join(self.all_views)}> before creating it.",
        )
        parser.add_argument(
            "--concurrently",
            action="store_true",
            help=f"Refresh views <{', '.join(self.all_views)}> concurrently (requires unique index).",
        )

    def handle(self, *args, **options):
        try:
            if options["drop"]:
                self.drop_all_views()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Views <{', '.join(self.all_views)}> dropped successfully."
                    )
                )

            elif options["refresh"]:
                self.refresh_materialized_views(concurrently=options["concurrently"])
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Views <{', '.join(self.all_views)}> refreshed successfully."
                    )
                )
            else:
                self.create_all_views()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Views <{', '.join(self.all_views)}> created successfully."
                    )
                )

            self.stdout.write(
                self.style.WARNING(
                    f"Last update: {timezone.now().isoformat(timespec='seconds')}"
                )
            )
        except Exception as e:
            raise CommandError(f"Error managing DB views: {str(e)}")

    def create_all_views(self):
        self.create_materialized_views()
        self.create_views()

    def create_views(self):
        """Create the views"""
        self.create_data_core_reporting_materialized_view()
        self.create_data_core_reporting_view()

    def create_data_core_reporting_view(self, view="data_dpnk_core_reporting"):
        """Create the data_dpnk_core_reporting view"""
        sql = f"""
        CREATE VIEW {view} AS
        SELECT au_id,
               up_id,
               gender,
               campaign_id,
               campaign_year,
               ua_id,
               team_id,
               branch_id,
               org_id,
               city_id
        FROM data_core_reporting dcr
        WHERE true AND slug::text = 'dpnk'::text AND team_id IS NOT NULL;
        """

        with connection.cursor() as cursor:
            cursor.execute(sql)
            logger.info(f"View <{view}> created successfully.")

    def create_materialized_views(self):
        """Create the materialized views"""
        self.create_data_core_reporting_materialized_view()

    def create_data_core_reporting_materialized_view(self, view="data_core_reporting"):
        """Create the data_core_reporting materialized view"""
        sql = f"""
        CREATE MATERIALIZED VIEW IF NOT EXISTS {view} AS
         SELECT
                CASE
                    WHEN c.slug::text = 'dpnk'::text AND c.year::integer::double precision >= date_part('year'::text, now()) THEN true
                    ELSE false
                END AS current_campaign,
                CASE
                    WHEN ct.slug::text = 'dpnk'::text AND ct.name::text = 'Lednová výzva'::text THEN 'leden'::character varying
                    WHEN ct.slug::text = 'dpnk'::text AND ct.name::text = 'Zářijová výzva'::text THEN 'vyzva'::character varying
                    WHEN ct.slug::text = 'dpnk'::text AND ct.name::text = 'Do práce na kole'::text THEN 'dpnk'::character varying
                    ELSE ct.slug
                END AS slug,
            au.id AS au_id,
            up.id AS up_id,
            COALESCE(up.nickname, ((au.first_name::text || ' '::text) || au.last_name::text)::character varying) AS user_name,
                CASE
                    WHEN up.sex::text = 'male'::text THEN 'm'::text
                    WHEN up.sex::text = 'female'::text THEN 'f'::text
                    ELSE NULL::text
                END AS gender,
            c.id AS campaign_id,
            c.year::integer AS campaign_year,
            ua.id AS ua_id,
            t.id AS team_id,
            s.id AS branch_id,
            s.company_id AS org_id,
            dc.id AS city_id,
            now() AS "current_time"
           FROM auth_user au
             JOIN dpnk_userprofile up ON up.user_id = au.id
             JOIN dpnk_userattendance ua ON ua.userprofile_id = up.id
             JOIN dpnk_campaign c ON ua.campaign_id = c.id
             JOIN dpnk_campaigntype ct ON ct.id = c.campaign_type_id
             LEFT JOIN dpnk_team t ON ua.team_id = t.id
             LEFT JOIN dpnk_subsidiary s ON t.subsidiary_id = s.id
             LEFT JOIN dpnk_city dc ON dc.id = s.city_id
          WHERE true AND (ua.payment_status::text = ANY (ARRAY['done'::character varying::text, 'no_admission'::character varying::text]));
        """

        with connection.cursor() as cursor:
            cursor.execute(sql)
            logger.info(f"Materialized view <{view}> created successfully.")

    def create_unique_indexes(self):
        """Create a unique indexes for concurrent refresh (optional but recommended)"""

        sql = ""
        for view in self.materialized_views:
            if view == "data_core_reporting":
                sql += f"""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_{view}_unique
                ON {view} (au_id, campaign_id);
                """

        with connection.cursor() as cursor:
            cursor.execute(sql)
            logger.info(
                f"Unique views <{', '.join(self.materialized_views)}> index created for concurrent refresh."
            )

    def drop_all_views(self):
        """Drop all DB views"""
        self.drop_materialized_views()
        self.drop_views()

    def drop_materialized_views(self):
        """Drop the materialized views"""
        sql = ""
        for view in self.materialized_views:
            sql += f"DROP MATERIALIZED VIEW IF EXISTS {view} CASCADE;"

        with connection.cursor() as cursor:
            cursor.execute(sql)
            logger.info(
                f"Materialized views <{', '.join(self.materialized_views)}> dropped successfully."
            )

    def drop_views(self):
        """Drop DB views"""
        sql = ""
        for view in self.views:
            sql += f"DROP VIEW IF EXISTS {view} CASCADE;"

        with connection.cursor() as cursor:
            cursor.execute(sql)
            logger.info(f"Views <{', '.join(self.views)}> dropped successfully.")

    def refresh_materialized_views(self, concurrently=False):
        """Refresh the materialized views"""

        concurrently_str = "CONCURRENTLY" if concurrently else ""
        sql = ""
        for view in self.materialized_views:
            sql += f"REFRESH MATERIALIZED VIEW {concurrently_str} {view};"
            if concurrently_str:
                self.create_unique_index()

        with connection.cursor() as cursor:
            cursor.execute(sql)
            logger.info(
                f"Materialized views <{', '.join(self.materialized_views)}> refreshed successfully (concurrently={concurrently})."
            )

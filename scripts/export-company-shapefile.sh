#/bin/bash
pgsql2shp -p 25061 -f $COMPANY_NAME.shp -h $DB_HOST -u dpnk -P $DB_PASS dpnk-pool 'select track, date, direction, id from dpnk_trip where user_attendance_id in (select id from dpnk_userattendance where team_id in (select id from dpnk_team where subsidiary_id in (select id from dpnk_subsidiary where company_id = $COMPANY_ID))) and track is not null'

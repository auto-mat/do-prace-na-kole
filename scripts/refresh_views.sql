CREATE OR REPLACE FUNCTION has_longer_section_than(line geometry, max_length integer) RETURNS boolean as $$
    DECLARE
       cur_length integer;
    BEGIN
    FOR i IN 1..ST_NPoints(line)-1
    LOOP
       cur_length := ST_distance(ST_PointN(line, i)::geography, ST_PointN(line, i+1)::geography);
       IF cur_length>max_length THEN
           RETURN True;
       END IF;
    END LOOP;
    RETURN False;
END;
$$ LANGUAGE plpgsql;

drop table  dpnk_trip_anonymized;
CREATE TABLE dpnk_trip_anonymized as select * from (
   select a.id, a.campaign_id, age_group, sex, commute_mode, city, occupation_id, ST_LineSubstring(a.track, 100/st_length(a.track::geography), 1 - 100/st_length(a.track::geography)) as the_geom from (
   SELECT dpnk_trip.id, dpnk_userattendance.campaign_id, dpnk_userprofile.age_group, dpnk_userprofile.sex, dpnk_commutemode.slug as commute_mode, dpnk_city.slug as city, dpnk_userprofile.occupation_id, (ST_Dump(dpnk_trip.track::geometry)).geom AS track from dpnk_trip
      join dpnk_userattendance on (dpnk_trip.user_attendance_id = dpnk_userattendance.id)
      join dpnk_userprofile on (dpnk_userattendance.userprofile_id = dpnk_userprofile.id)
      join dpnk_team on (dpnk_userattendance.team_id = dpnk_team.id)
      join dpnk_subsidiary on (dpnk_team.subsidiary_id = dpnk_subsidiary.id)
      join dpnk_city on (dpnk_subsidiary.city_id = dpnk_city.id)
      join dpnk_commutemode on (dpnk_trip.commute_mode_id = dpnk_commutemode.id)
   ) as a
      where a.track is not null and st_numpoints(a.track::geometry) > 15 and st_length(a.track::geography)<100000 and st_length(a.track::geography)>200 and not has_longer_section_than(a.track::geometry, 1000)
) as b where st_numpoints(b.the_geom)>15;
GRANT ALL PRIVILEGES ON TABLE dpnk_trip_anonymized TO dpnk;
CREATE INDEX dpnk_trip_anonymized_idx ON dpnk_trip_anonymized USING GIST (the_geom);

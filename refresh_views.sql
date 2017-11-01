
drop table  dpnk_gpxfile_anonymized;
CREATE TABLE dpnk_gpxfile_anonymized as select * from (select a.id, a.campaign_id, ST_LineSubstring(a.track, 100/st_length(a.track::geography), 1 - 100/st_length(a.track::geography)) as the_geom from (SELECT dpnk_gpxfile.id, dpnk_userattendance.campaign_id, (ST_Dump(dpnk_gpxfile.track::geometry)).geom AS track from dpnk_gpxfile join dpnk_userattendance on (dpnk_gpxfile.user_attendance_id = dpnk_userattendance.id)) as a where a.track is not null and st_numpoints(a.track::geometry) > 15 and st_length(a.track::geography)<100000 and st_length(a.track::geography)>200) as b where st_numpoints(b.the_geom)>15;
GRANT ALL PRIVILEGES ON TABLE dpnk_gpxfile_anonymized TO dpnk;
CREATE INDEX dpnk_gpxfile_anonymized_idx ON dpnk_gpxfile_anonymized USING GIST (the_geom);

drop table dpnk_track_anonymized;
create table dpnk_track_anonymized as select * from (select id, campaign_id, st_numpoints((st_dump(track::geometry)).geom) as numpoints, ST_LineSubstring(track::geometry, 100/st_length(track), 1 - 100/st_length(track)) as the_geom from dpnk_userattendance where track is not null and st_length(track)<100000 and st_length(track)>200) as a where numpoints>15;
GRANT ALL PRIVILEGES ON TABLE dpnk_track_anonymized TO dpnk;
CREATE INDEX dpnk_track_anonymized_idx ON dpnk_track_anonymized USING GIST (the_geom);


CREATE OR REPLACE FUNCTION max_length_between_points(line geometry) RETURNS integer as $$
    DECLARE
       max_length integer;
       cur_length integer;
    BEGIN
    max_length := 0;
    FOR i IN 1..ST_NPoints(line)-1
    LOOP
       cur_length := ST_distance(ST_PointN(line, i)::geography, ST_PointN(line, i+1)::geography);
       IF cur_length>max_length THEN
           max_length := cur_length;
       END IF;
    END LOOP;
    RETURN max_length;
END;
$$ LANGUAGE plpgsql;


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

create table dpnk_gpxfile_anonymized_avg as select the_geom, st_length(the_geom::geography), st_numpoints(the_geom) campaign_id, id from dpnk_gpxfile_anonymized where not has_longer_section_than(the_geom, 1000);


drop table  dpnk_gpxfile_anonymized;
CREATE TABLE dpnk_gpxfile_anonymized as select * from (select a.id, ST_Line_SubString(a.track, 100/st_length(a.track::geography), 1 - 100/st_length(a.track::geography)) as the_geom from (SELECT id, (ST_Dump(track::geometry)).geom AS track from dpnk_gpxfile) as a where a.track is not null and st_numpoints(a.track::geometry) > 2 and st_length(a.track::geography)<100000 and st_length(a.track::geography)>200) as b where st_numpoints(b.the_geom)>4;
GRANT ALL PRIVILEGES ON TABLE dpnk_gpxfile_anonymized TO dpnk;

drop table dpnk_track_anonymized;
create table dpnk_track_anonymized as select * from (select id, ST_Line_SubString(track::geometry, 100/st_length(track), 1 - 100/st_length(track)) as the_geom from dpnk_userattendance where track is not null and st_length(track)<100000 and st_length(track)>200) as a where st_numpoints(a.the_geom)>4;
GRANT ALL PRIVILEGES ON TABLE dpnk_track_anonymized TO dpnk;

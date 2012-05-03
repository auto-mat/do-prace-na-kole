
create or replace view dpnk_v_user_results as select p.id as id, p.firstname, p.surname, t.id as team_id, t.name as team, t.company as company, t.city as city, p.trips, p.trips*p.distance as distance from dpnk_userprofile as p left join dpnk_team as t on p.team_id = t.id order by trips desc, distance desc;

create or replace view dpnk_v_team_results as select t.id as id, t.name as name, t.company as company, t.city as city, sum(p.trips) as trips, sum(p.trips)/count(p.id) as trips_per_person, count(p.id) as persons, sum(p.trips*p.distance) as distance from dpnk_userprofile as p left join dpnk_team as t on p.team_id = t.id where p.active=true group by team_id order by trips_per_person desc, distance desc;

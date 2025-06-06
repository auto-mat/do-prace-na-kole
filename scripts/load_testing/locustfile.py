from locust import HttpUser, task, between, TaskSet, events
import threading
import random
import datetime
import random

NUMBER_OF_SUBSIDIARIES_IN_COMPANY = 3
NUMBER_OF_TEAMS_IN_SUBSIDIARY = 25
NUMBER_OF_MEMBERS_IN_TEAM = 5
number_of_teams = None
number_of_subsidiaries = None
number_of_companies = None

number = 1

from locust import HttpUser, task, between, events

import logging
from locust import HttpUser, task, between

# Configure the logger
logger = logging.getLogger("locust")
logger.setLevel(logging.INFO)  # Set the desired log level


def ceil_div(a, b):
    return -(-a // b)


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    global number_of_teams
    global number_of_subsidiaries
    global number_of_companies
    if environment.runner:
        print(f"Total (target) users at start: {environment.runner.target_user_count}")
        number_of_teams = ceil_div(
            environment.runner.target_user_count, NUMBER_OF_MEMBERS_IN_TEAM
        )
        number_of_subsidiaries = ceil_div(
            number_of_teams, NUMBER_OF_TEAMS_IN_SUBSIDIARY
        )
        number_of_companies = ceil_div(
            number_of_subsidiaries, NUMBER_OF_SUBSIDIARIES_IN_COMPANY
        )


class ApiUserBehavior(TaskSet):

    lock = threading.Lock()
    members_in_team = []

    test_data = {
        "first_name": ["Jaroslav", "Petr", "Jan", "Martin", "Jakub"],
        "last_name": ["Novák", "Svoboda", "Dvořák", "Černý", "Procházka"],
        "payment_subject": ["company", "individual", "voucher", "school"],
        "personal_data_opt_in": [True, False],
        "nickname": ["user1", "user2", "user3", "user4"],
        "telephone": ["+420123456789", "+420987654321", "+420555555555"],
        "language": ["cs", "en"],
        "occupation": ["Lékař", "Právník", "Chemik", "Lékárník"],
        "newsletter": [
            "challenge",
            "events",
            "mobility",
            "challenge-events",
            "challenge-mobility",
            "events-mobility",
            "challenge-events-mobility",
            "",
        ],
        "user_ids": [],
        "team_ids": [],
        "competition_slugs": ["vyzva1"],
        "city_slugs": ["praha", "brno", "ostrava"],
        "address_street": ["Hlavní ulice", "Ježková", "Jindřišská"],
        "address_street_number": ["1447", "7852", "145/8"],
        "address_psc": ["11000", "60200", "70200"],
        "address_city": ["Praha", "Brno", "Ostrava"],
        "address_recipient": ["Jan Novák", "Petr Svoboda", "Martin Černý"],
        "organization_ids": [],
        "city_id": None,
        "active": [True, False],
        "box_addressee_name": ["Jan Novák", "Petr Svoboda", "Martin Černý"],
        "box_addressee_telephone": ["+420123456789", "+420987654321", "+420555555555"],
        "box_addressee_email": ["a@seznam.cz", "b@seznam.cz", "c@seznam.cz"],
        "name": ["Team A", "Team B", "Team C"],
        "subsidiary_ids": [],
        "organization_name": ["Organization A", "Organization B", "Organization C"],
        "ico": ["1234567890", "9876543210", "1357924680"],
        "dic": ["123456789", "98765432", "13579246"],
        "note": ["Note A", "Note B", "Note C"],
        "organization_type": ["company", "family", "school"],
        "photos": [],
    }

    def get_city_ids(self):
        response = self.client.get(f"/rest/city/", name="GetCity", headers=self.headers)

        if response.status_code == 200:
            try:
                data = response.json()
                results = data.get("results", [])
                ids = [item.get("id") for item in results]
            except Exception as e:
                response.failure(f"Failed to parse JSON: {str(e)}")
        else:
            response.failure(f"Request failed with status {response.status_code}")

        return ids

    def get_subsidiary_ids(self):
        response = self.client.get(
            f"/rest/subsidiary/", name="GetSubsidiary", headers=self.headers
        )

        if response.status_code == 200:
            try:
                data = response.json()
                results = data.get("results", [])
                ids = [item.get("id") for item in results]
            except Exception as e:
                response.failure(f"Failed to parse JSON: {str(e)}")
        else:
            response.failure(f"Request failed with status {response.status_code}")

        return ids

    def create_subsidiary(self, organizationId):
        post_data = {
            "address": {
                "street": random.choice(
                    ApiUserBehavior.test_data.get("address_street")
                ),
                "street_number": random.choice(
                    ApiUserBehavior.test_data.get("address_street_number")
                ),
                "psc": random.choice(ApiUserBehavior.test_data.get("address_psc")),
                "city": random.choice(ApiUserBehavior.test_data.get("address_city")),
                "recipient": random.choice(
                    ApiUserBehavior.test_data.get("address_recipient")
                ),
            },
            "city_id": random.choice(self.get_city_ids()),
            "active": random.choice(ApiUserBehavior.test_data.get("active")),
            "box_addressee_name": random.choice(
                ApiUserBehavior.test_data.get("box_addressee_name")
            ),
            "box_addressee_telephone": random.choice(
                ApiUserBehavior.test_data.get("box_addressee_telephone")
            ),
            "box_addressee_email": random.choice(
                ApiUserBehavior.test_data.get("box_addressee_email")
            ),
        }
        response = self.client.post(
            f"/rest/organizations/{organizationId}/subsidiaries/",
            json=post_data,
            name="CreateSubsidiary",
            headers=self.headers,
        )
        return response.json().get("id")

    def create_team(self, subsidiaryId):
        post_data = {
            "name": f"{random.choice(ApiUserBehavior.test_data.get("name"))}{random.randint(1000, 9999)}",
            "subsidiary_id": subsidiaryId,
        }
        response = self.client.post(
            f"/rest/subsidiaries/{subsidiaryId}/teams/",
            json=post_data,
            name="CreateTeam",
            headers=self.headers,
        )
        return response.json().get("id")

    def create_organization(self):
        post_data = {
            "name": f"{random.choice(ApiUserBehavior.test_data.get("organization_name"))}{random.randint(1000, 9999)}",
            "note": random.choice(ApiUserBehavior.test_data.get("note")),
            "address": {
                "street": random.choice(
                    ApiUserBehavior.test_data.get("address_street")
                ),
                "street_number": random.choice(
                    ApiUserBehavior.test_data.get("address_street_number")
                ),
                "psc": random.choice(ApiUserBehavior.test_data.get("address_psc")),
                "city": random.choice(ApiUserBehavior.test_data.get("address_city")),
                "recipient": random.choice(
                    ApiUserBehavior.test_data.get("address_recipient")
                ),
            },
            "organization_type": random.choice(
                ApiUserBehavior.test_data.get("organization_type")
            ),
        }
        response = self.client.post(
            f"/rest/organizations/",
            json=post_data,
            name="CreateOrganization",
            headers=self.headers,
        )
        return response.json().get("id")

    def on_start(self):

        self.trip_ids = []

        # global number
        number = random.randint(1, 1000000000)
        self.test_email = f"loadtest_{number}@example.com"
        # number += 1
        register_payload = {
            "email": self.test_email,
            "password1": "locustPass123!",
            "password2": "locustPass123!",
        }
        with self.client.post(
            "/rest/auth/registration/",
            json=register_payload,
            catch_response=True,
            name="Registration",
        ) as reg_response:
            if reg_response.status_code != 201:
                reg_response.failure(
                    f"Registration failed ({reg_response.status_code}): {reg_response.text}"
                )
                return

            self._store_auth_details(reg_response)
        while True:
            teamIdx = random.randint(0, number_of_teams - 1)
            with ApiUserBehavior.lock:
                if teamIdx < len(ApiUserBehavior.test_data["team_ids"]):
                    if ApiUserBehavior.members_in_team != NUMBER_OF_MEMBERS_IN_TEAM:
                        ApiUserBehavior.members_in_team[teamIdx] += 1
                        teamId = ApiUserBehavior.test_data["team_ids"][teamIdx]
                    else:
                        continue
                else:
                    subsidiaryIdx = random.randint(0, number_of_subsidiaries - 1)
                    if subsidiaryIdx < len(ApiUserBehavior.test_data["subsidiary_ids"]):
                        subsidiaryId = ApiUserBehavior.test_data["subsidiary_ids"][
                            subsidiaryIdx
                        ]
                    else:
                        organizationIdx = random.randint(0, number_of_companies - 1)
                        if organizationIdx < len(
                            ApiUserBehavior.test_data["organization_ids"]
                        ):
                            organizationId = ApiUserBehavior.test_data[
                                "organization_ids"
                            ][organizationIdx]
                        else:
                            organizationId = self.create_organization()
                            ApiUserBehavior.test_data["organization_ids"].append(
                                organizationId
                            )
                        subsidiaryId = self.create_subsidiary(organizationId)
                        ApiUserBehavior.test_data["subsidiary_ids"].append(subsidiaryId)

                    teamId = self.create_team(subsidiaryId)
                    ApiUserBehavior.test_data["team_ids"].append(teamId)
                    ApiUserBehavior.members_in_team.append(1)
            break

        post_data = {
            "personal_details": {
                "first_name": random.choice(
                    ApiUserBehavior.test_data.get("first_name")
                ),
                "last_name": random.choice(ApiUserBehavior.test_data.get("last_name")),
                "nickname": random.choice(ApiUserBehavior.test_data.get("nickname")),
                "telephone": random.choice(ApiUserBehavior.test_data.get("telephone")),
                "language": random.choice(ApiUserBehavior.test_data.get("language")),
                "occupation": random.choice(
                    ApiUserBehavior.test_data.get("occupation")
                ),
                "age_group": random.randint(1950, 2000),
                "newsletter": random.choice(
                    ApiUserBehavior.test_data.get("newsletter")
                ),
                "personal_data_opt_in": random.choice(
                    ApiUserBehavior.test_data.get("personal_data_opt_in")
                ),
                "discount_coupon": "",
                "payment_subject": random.choice(
                    ApiUserBehavior.test_data.get("payment_subject")
                ),
                "payment_amount": random.randint(100, 2500),
            },
            "team_id": teamId,
            "t_shirt_size_id": 1,
        }
        response = self.client.post(
            "/rest/register-challenge/",
            json=post_data,
            name="RegisterChallenge",
            headers=self.headers,
        )

        if (
            "personal_details" in response.json()
            and "id" in response.json()["personal_details"]
        ):
            self.user_attendance_id = response.json()["personal_details"]["id"]

    def _perform_login(self):
        return self.client.post(
            "/rest/auth/login/",
            json={"email": self.test_email, "password": "LoadTestPass123!"},
            catch_response=True,
        )

    def _store_auth_details(self, login_response):
        self.auth_token = login_response.json().get("access")
        self.headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }

        if "user" in login_response.json() and "pk" in login_response.json()["user"]:
            self.user_id = login_response.json()["user"]["pk"]

    def generate_gpx(self):
        base_lat = 50.0 + random.random() * 0.5
        base_lon = 14.0 + random.random() * 0.5
        num_points = random.randint(50, 100)
        track_points = []
        start_time = datetime.datetime.now() - datetime.timedelta(minutes=num_points)
        for i in range(num_points):
            point_time = start_time + datetime.timedelta(minutes=i)
            lat = base_lat + random.uniform(-0.001, 0.001) * i
            lon = base_lon + random.uniform(-0.001, 0.001) * i
            track_points.append(
                f"""
	  <trkpt lat="{lat:.6f}" lon="{lon:.6f}">
		<time>{point_time.strftime("%Y-%m-%dT%H:%M:%SZ")}</time>
	  </trkpt>"""
            )
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1">
  <trk>
	<trkseg>
{"".join(track_points)}
	</trkseg>
  </trk>
</gpx>"""

    @task(5)
    def create_trip(self):
        files = {"file": ("track.gpx", self.generate_gpx(), "application/gpx+xml")}
        date_offset = random.randint(-6, 0)
        trip_date = (
            datetime.datetime.now() + datetime.timedelta(days=date_offset)
        ).date()
        data = {
            "trip_date": trip_date.isoformat(),
            "direction": random.choice(["trip_to", "trip_from"]),
            "commuteMode": random.choice(["bicycle", "by_foot", "by_other_vehicle"]),
            "sourceApplication": "load-test",
        }
        headers_copy = self.headers.copy()
        del headers_copy["Content-Type"]
        with self.client.post(
            "/rest/gpx/",
            data=data,
            files=files,
            name="CreateTripWithGPX",
            headers=headers_copy,
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                trip_id = response.json().get("id")
                if trip_id:
                    self.trip_ids.append(trip_id)

    @task(5)
    def delete_trip(self):
        if self.trip_ids:
            id = random.choice(self.trip_ids)
            self.client.delete(
                f"/rest/gpx/{id}/", name="DeleteTrip", headers=self.headers
            )
            self.trip_ids.remove(id)

    @task(5)
    def get_user_profile(self):
        id = self.user_attendance_id
        self.client.get(
            f"/rest/register-challenge/{id}/",
            name="GetUserProfile",
            headers=self.headers,
        )

    @task(1)
    def update_user_profile(self):
        payload = {
            "telephone": f"+420{random.randint(100000000, 999999999)}",
            "newsletter": random.choice(self.test_data["newsletter"]),
            "language": random.choice(["cs", "en"]),
            "nickname": f"user{random.randint(1, 1000)}",
            "occupation": random.choice(self.test_data["occupation"]),
        }
        id = self.user_attendance_id
        response = self.client.put(
            f"/rest/register-challenge/{id}/",
            json=payload,
            name="UpdateUserProfile",
            headers=self.headers,
        )

    @task(5)
    def get_competition(self):
        competition = random.choice(self.test_data["competition_slugs"])
        self.client.get(
            f"/rest/result/{competition}/",
            name="CompetitionResult",
            headers=self.headers,
        )

    @task(2)
    def list_trips_with_filters(self):
        base_date = datetime.datetime.now() - datetime.timedelta(days=6)
        start_offset = random.randint(0, 6)
        date_from = (base_date + datetime.timedelta(days=start_offset)).strftime(
            "%Y-%m-%d"
        )
        date_to = (
            base_date + datetime.timedelta(days=start_offset + random.randint(0, 6))
        ).strftime("%Y-%m-%d")
        filters = {
            "start": date_from,
            "end": date_to,
            "direction": random.choice(["trip_to", "trip_from", ""]),
            "commuteMode": random.choice(
                ["bicycle", "by_foot", "by_other_vehicle", ""]
            ),
        }
        self.client.get(
            "/rest/trips/",
            params=filters,
            name="ListTripsWithFilters",
            headers=self.headers,
        )

    @task(2)
    def get_trip_detail(self):
        if self.trip_ids:
            trip_id = random.choice(self.trip_ids)
            self.client.get(
                f"/rest/trips/{trip_id}/", name="GetTripDetail", headers=self.headers
            )

    @task(10)
    def logout_and_login(self):
        self.client.post("/rest/auth/logout/", name="Logout", headers=self.headers)

        login_payload = {"username": self.test_email, "password": "locustPass123!"}
        login_response = self.client.post(
            "/rest/auth/login/", name="Login", json=login_payload
        )

        if login_response.status_code == 200:
            self.auth_token = login_response.json().get("token")
            self.headers["Authorization"] = f"Bearer {self.auth_token}"

    @task(3)
    def get_notifications(self):
        self.client.get(
            "/rest/notification/", name="GetNotifications", headers=self.headers
        )

    @task(1)
    def get_notification_detail(self):
        resp = self.client.get(
            "/rest/notification/", name="GetNotificationDetail", headers=self.headers
        )
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            if results:
                notif_id = results[0].get("id")
                if notif_id:
                    self.client.get(
                        f"/rest/notification/{notif_id}/", headers=self.headers
                    )

    @task(3)
    def get_photo_list(self):
        self.client.get("/rest/photo/", name="GetPhotoList", headers=self.headers)

    @task(5)
    def get_team(self):
        if self.test_data["team_ids"]:
            team_id = random.choice(self.test_data["team_ids"])
            subsidiary_id = random.choice(self.test_data["subsidiary_ids"])
            self.client.get(
                f"/rest/subsidiaries/{subsidiary_id}/teams/{team_id}",
                name="GetTeam",
                headers=self.headers,
            )

    @task(1)
    def get_discount_coupon(self):
        code = "DP-SXQEFH"
        self.client.get(
            f"/rest/discount-coupon/{code}/",
            name="GetDiscountCoupon",
            headers=self.headers,
        )

    @task(2)
    def get_photo(self):
        if self.test_data["photos"]:
            path = random.choice(self.test_data["photos"])
            self.client.get(path, name="GetPhoto", headers=self.headers)

    @task(1)
    def get_merchandise(self):
        self.client.get(
            "/rest/merchandise/", name="GetMerchandise", headers=self.headers
        )

    @task(1)
    def get_commute_mode(self):
        self.client.get(
            "/rest/commute_mode/", name="GetCommuteMode", headers=self.headers
        )

    @task(1)
    def get_city_list(self):
        self.client.get(
            "/rest/city_in_campaign/", name="GetCityList", headers=self.headers
        )

    @task(1)
    def get_campaigns(self):
        self.client.get("/rest/campaign/", name="GetCampaigns", headers=self.headers)

    @task(1)
    def get_campaign_type(self):
        self.client.get(
            "/rest/campaign_type/", name="GetCampaignType", headers=self.headers
        )

    @task(5)
    def get_my_team(self):
        self.client.get("/rest/my_team/", name="GetMyTeam", headers=self.headers)

    @task(5)
    def get_my_company(self):
        self.client.get("/rest/my_company/", name="GetMyCompany", headers=self.headers)

    @task(5)
    def get_my_subsidiary(self):
        self.client.get(
            "/rest/my_subsidiary/", name="GetMySubsidiary", headers=self.headers
        )

    @task(5)
    def get_my_city(self):
        self.client.get("/rest/my_city/", name="GetMyCity", headers=self.headers)

    @task(1)
    def get_strava_account(self):
        self.client.get(
            "/rest/strava_account/", name="GetStravaAccount", headers=self.headers
        )

    @task(10)
    def post_photo(self):

        with open("DSC00002.JPG", "rb") as photofile:
            data = {"caption": "masozravka"}
            files = {"image": ("DSC00002.JPG", photofile, "image/jpeg")}
            headers_copy = self.headers.copy()
            del headers_copy["Content-Type"]
            response = self.client.post(
                "/rest/photo/",
                data=data,
                files=files,
                name="PostPhoto",
                headers=headers_copy,
            )
            if response.status_code == 201:
                image = response.json().get("image")
                if image:
                    self.test_data["photos"].append(image)

    @task(1)
    def get_colleague_trips(self):
        self.client.get(
            "/rest/colleague_trips/", name="GetColleaguesTrips", headers=self.headers
        )


class ApiUser(HttpUser):
    tasks = [ApiUserBehavior]
    wait_time = between(10, 30)
    host = "http://api:8000"

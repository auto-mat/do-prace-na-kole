DPNK API
----------

The main part of the API is documented on the test server [under the rest enpoint](https://test2019.dopracenakole.cz/rest/).

Authentification
=====================

For mobile apps authentification is done via an auth token. Auth tokens can be aquired by one of two methods:

1) Username and password (JWT auth)
2) OAuth2 3rd party authentification

Here is an example of requesting an auth token at URL endpoint rest/auth/login/ by providing a username and password:

Request:

```
curl -i \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"username": "foo@bar.org", "password": "foobar"}' \
    http://test.lvh.me:8021/rest/auth/login/
```

Response:

```
HTTP/1.1 200 OK
Date: Mon, 16 Sep 2024 09:34:56 GMT
Server: WSGIServer/0.2 CPython/3.9.19
Content-Type: application/json
Vary: Accept, Accept-Language, Cookie, Origin
Allow: POST, OPTIONS
Content-Length: 540
Content-Language: cs
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Set-Cookie:  sessionid=bdrhssn6ygjrxvhiu250k18iu0dvs8le; expires=Mon, 30 Sep 2024 09:34:56 GMT; HttpOnly; Max-Age=1209600; Path=/
Set-Cookie:  csrftoken=tIYxxVwbgF1WUbAXP2hUrAJUpF7qqfaOFi0MqnZ829gGrm9VCLlORhSY4jOJnTnk; expires=Mon, 15 Sep 2025 09:34:56 GMT; Max-Age=31449600; Path=/; SameSite=Lax

{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzI2NDc5NTk2LCJqdGkiOiJlZWM5ODZhYTc1Mjk0MjA4YWRkNWE0NzI4ZDk0N2E2OCIsInVzZXJfaWQiOjF9.t1rO4HSOXhPGb81jP7zAdoiiVMT5nGj7Ic0DDfiQynE",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTcyNjU2NTY5NiwianRpIjoiOTJhMzI0ODY4NThkNDI5YWI5YzBiMzllNzk4M2M4OWIiLCJ1c2VyX2lkIjoxfQ.iARxyUr3hiWBgg4t8GgF6Xdi0LnL3J1CCeMdgrNO2pg",
  "user": {
    "pk": 1,
    "username": "foobar",
    "email": "foo@bar.org",
    "first_name": "Foo",
    "last_name": "Bar"
  }
}
```

You can refresh a token by using the rest/auth/refresh/tokens/ URL endpoint.

Request:

```
curl -i \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"refresh":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTcyNjU2NTY5NiwianRpIjoiOTJhMzI0ODY4NThkNDI5YWI5YzBiMzllNzk4M2M4OWIiLCJ1c2VyX2lkIjoxfQ.iARxyUr3hiWBgg4t8GgF6Xdi0LnL3J1CCeMdgrNO2pg"}' \
    http://test.lvh.me:8021/rest/auth/token/refresh/
```

Response:

```
HTTP/1.1 200 OK
Date: Mon, 16 Sep 2024 09:41:48 GMT
Server: WSGIServer/0.2 CPython/3.9.19
Content-Type: application/json
Vary: Accept, Accept-Language, Cookie, Origin
Allow: POST, OPTIONS
Content-Length: 273
Content-Language: cs
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block

{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzI2NDgwMDA4LCJqdGkiOiIzYjg5MjlhZTFkMDM0YmYwYmRmNTBiNWYxNTEyYzMwNSIsInVzZXJfaWQiOjF9.EchyE6QVe-DUyYbtpY2wo3vVqXckC3f60_ntAZtD9VQ",
  "access_token_expiration": "2024-09-16T11:46:48.551800"
}
```

Tokens authorization parameter must be included in the Bearer authorization scheme of the HTTP authorization header on all requests.

HTTP authorization header:

```
Authorization: Bearer <TOKEN>
```

Here is an example of how to use a token.

Request:

```
curl -i \
    -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzI2NDgwMDA4LCJqdGkiOiIzYjg5MjlhZTFkMDM0YmYwYmRmNTBiNWYxNTEyYzMwNSIsInVzZXJfaWQiOjF9.EchyE6QVe-DUyYbtpY2wo3vVqXckC3f60_ntAZtD9VQ" \
    http://test.lvh.me:8021/rest/gpx/
```

Response:

```
HTTP/1.1 200 OK
Date: Mon, 16 Sep 2024 10:06:27 GMT
Server: WSGIServer/0.2 CPython/3.9.19
Content-Type: application/json
Vary: Accept, Accept-Language, Cookie, Origin
Allow: GET, POST, HEAD, OPTIONS
Content-Length: 3583
Content-Language: cs
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block

{
  "count": 16,
  "next": null,
  "previous": null,
  "results": [
    {
      "distanceMeters": 1250,
      "durationSeconds": 0,
      "commuteMode": "by_other_vehicle",
      "sourceApplication": null,
      "trip_date": "2023-05-16",
      "sourceId": null,
      "file": null,
      "description": "",
      "id": 15,
      "direction": "trip_to",
      "track": null
    },
    {
      "distanceMeters": 997650,
      "durationSeconds": 0,
      "commuteMode": "bicycle",
      "sourceApplication": null,
      "trip_date": "2023-05-23",
      "sourceId": null,
      "file": null,
      "description": "",
      "id": 1,
      "direction": "trip_to",
      "track": {
        "type": "MultiLineString",
        "coordinates": [
          [
            [
              14.07589,
              50.234799
            ],
            [
              14.084558,
              50.230736
            ],
            [
              14.089193,
              50.230352
            ],
            [
              14.091253,
              50.230407
            ]
          ]
        ]
      }
    }
  ]
}
```

The OAuth2 workflow is slightly more complex, but it is still simple. It has three steps:

1. The mobile app opens a webview with a special URL which is meant for authenticating that app.
2. The user authenticates themselves using the third party OAuth provider's web interface.
3. The webview will redirect to a secial URL which must be registered with the mobile app. The mobile app can then extract the auth token from this URL.

Each third party OAuth2 provider has it's own webview URL for authentification. This makes it so that native "Log in with Facebook" buttons can be used in the mobile app.

The currently supported OAuth2 webview URLs are:

`https://dpnk.dopracenakole.cz/social/login/google-oauth2/?next=/open-app-with-rest-token/1/`

`https://dpnk.dopracenakole.cz/social/login/facebook/?next=/open-app-with-rest-token/1/`

`https://dpnk.dopracenakole.cz/social/login/apple-id/?next=/open-app-with-rest-token/1/`

Where 1 is the number for the redirect URL. A URL for Apple will be added shortly.

The redirect URLs must be explicitly configured in the DPNK backend and are refered to by number. This is for security reasons, if DPNK could be tricked into sending auth tokens via redirect to any random URL, then it would be very vulnerable to XXS attacks.

DPNK has a setting for these redirect URLs named `DPNK_MOBILE_APP_URLS`, this is a list of redirect url templates.  Here is an example of one such URL which is used to authenticate the "Na Kole Prahou" mobile app: `https://p29ek.app.goo.gl/?link=http://nakoleprahou.cz/competitions.php?c%3D{campaign_slug_identifier}%26u%3D{auth_token}&apn=com.umotional.ucpraha&utm_source={campaign_slug_identifier}&amv=202&isi=1213867293&ibi=com.umotional.ucpraha&at={campaign_slug_identifier}`

API endpoints outside of the REST api
================================================

Not all API endpoints are available and documented under `/rest`.

- `https://test2019.dopracenakole.cz/third_party_routes/` is an endpoint which returns activities from Strava in the same format as `/rest` serves and accepts Trips (In the future, other third party apps may be supported).

Loading web views
======================

Parts of mobile apps may be implemented via webviews to the main webpage. If the user logged into the app via an OAuth2 redirect webview, then the session will cary over to the webview without requiring the user to log in again. However, if an auth token was aquired via password authentification, the user may not be logged in in the webview. You can pass a session on to a webview by passing a sesame_token as a query arg (named `sesame`) in any URL. Sesame tokens can be aquired via the rest endpint `https://test2019.dopracenakole.cz/rest/userattendance/`. Keep in mind that sesame tokens have a life span of just 10 minutes. Here is an example of passing such a query arg: `https://test2019.dopracenakole.cz/strava/?sesame=AACC2QH04ezT_NHsst2hrfHK`.

Sesame will automatically redirect to remove the queryarg token from the URL. This is for secuirity reasons. Removing the query arg from the url prevents users from accidentally sharing session tokens when copying URLs. This security problem isn't an issue, however, when accessing the site programatically, and it can be convinient to prevent the redirect. For this reason, you can append another query arg `sesame-no-redirect=true` to prevent the redirect. Here is an example url accessing a page with a sesame token but no redirect: `test.lvh.me:8021/?sesame=AAAAAQIJcnmpWDBTcpksSr5X;sesame-no-redirect=true`

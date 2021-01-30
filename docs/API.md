DPNK API
----------

The main part of the API is documented on the test server [under the rest enpoint](https://test2019.dopracenakole.cz/rest/).

Authentification
=====================

For mobile apps authentification is done via an auth token. Auth tokens can be aquired by one of two methods:

1) Username and password
2) OAuth2 3rd party authentification

Tokens must be included in the `Token` field of the HTTP header on all requests. Here is an example of how to use a token.

```
http https://test2019.dopracenakole.cz/rest/trips/?end=2020-12-14\;start=2020-12-11 Authorization:'Token 392efcd9f387aff9f829aa8b7ff48661'
```

Here is an example of requesting an auth token by providing a username and password:

```
http post http://test.lvh.me:8021/api-token-auth/ username=foo@bar.cz password=foobarbaz
HTTP/1.1 200 OK
Allow: POST, OPTIONS
Content-Language: cs
Content-Length: 52
Content-Type: application/json
Date: Sun, 20 Dec 2020 23:39:37 GMT
Server: WSGIServer/0.2 CPython/3.6.10
Vary: Accept-Language, Cookie, Origin
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block

{
    "token": "a4ba6792079aa4c62fb9cb1c9f80218f955f74f7"
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

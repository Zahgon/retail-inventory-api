"""
Documentation views: the OpenAPI document and the interactive API browsers.

The home route advertises ``/docs`` and the README links to it, so these pages
are part of the published surface rather than a framework extra.
"""

from django.http import HttpResponse

from ..core.responses import json_response
from ..core.routing import route
from ..openapi import OPENAPI_SCHEMA

HTML_MEDIA_TYPE = "text/html; charset=utf-8"

FAVICON_URL = "https://www.djangoproject.com/favicon.ico"

SWAGGER_UI_HTML = """
    <!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link type="text/css" rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
    <link rel="shortcut icon" href="{favicon}">
    <title>Retail Inventory API - Swagger UI</title>
    </head>
    <body>
    <div id="swagger-ui">
    </div>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <!-- `SwaggerUIBundle` is now available on the page -->
    <script>
    const ui = SwaggerUIBundle({{
        url: '/openapi.json',
    "dom_id": "#swagger-ui",
"layout": "BaseLayout",
"deepLinking": true,
"showExtensions": true,
"showCommonExtensions": true,
"docExpansion": "none",
oauth2RedirectUrl: window.location.origin + '/docs/oauth2-redirect',
    presets: [
        SwaggerUIBundle.presets.apis,
        SwaggerUIBundle.SwaggerUIStandalonePreset
        ],
    }})
    </script>
    </body>
    </html>
    """.format(favicon=FAVICON_URL)

REDOC_HTML = """
    <!DOCTYPE html>
    <html>
    <head>
    <title>Retail Inventory API - ReDoc</title>
    <!-- needed for adaptive design -->
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
    
    <link rel="shortcut icon" href="{favicon}">
    <!--
    ReDoc doesn't change outer page styles
    -->
    <style>
      body {{
        margin: 0;
        padding: 0;
      }}
    </style>
    </head>
    <body>
    <noscript>
        ReDoc requires Javascript to function. Please enable it to browse the documentation.
    </noscript>
    <redoc spec-url="/openapi.json"></redoc>
    <script src="https://cdn.jsdelivr.net/npm/redoc@2/bundles/redoc.standalone.js"> </script>
    </body>
    </html>
    """.format(favicon=FAVICON_URL)

OAUTH2_REDIRECT_HTML = """
    <!doctype html>
    <html lang="en-US">
    <head>
        <title>Swagger UI: OAuth2 Redirect</title>
    </head>
    <body>
    <script>
        'use strict';
        function run () {
            var oauth2 = window.opener.swaggerUIRedirectOauth2;
            var sentState = oauth2.state;
            var redirectUrl = oauth2.redirectUrl;
            var isValid, qp, arr;

            if (/code|token|error/.test(window.location.hash)) {
                qp = window.location.hash.substring(1).replace('?', '&');
            } else {
                qp = location.search.substring(1);
            }

            arr = qp.split("&");
            arr.forEach(function (v,i,_arr) { _arr[i] = '"' + v.replace('=', '":"') + '"';});
            qp = qp ? JSON.parse('{' + arr.join() + '}',
                    function (key, value) {
                        return key === "" ? value : decodeURIComponent(value);
                    }
            ) : {};

            isValid = qp.state === sentState;

            if ((
              oauth2.auth.schema.get("flow") === "accessCode" ||
              oauth2.auth.schema.get("flow") === "authorizationCode" ||
              oauth2.auth.schema.get("flow") === "authorization_code"
            ) && !oauth2.auth.code) {
                if (!isValid) {
                    oauth2.errCb({
                        authId: oauth2.auth.name,
                        source: "auth",
                        level: "warning",
                        message: "Authorization may be unsafe, passed state was changed in server. The passed state wasn't returned from auth server."
                    });
                }

                if (qp.code) {
                    delete oauth2.state;
                    oauth2.auth.code = qp.code;
                    oauth2.callback({auth: oauth2.auth, redirectUrl: redirectUrl});
                } else {
                    let oauthErrorMsg;
                    if (qp.error) {
                        oauthErrorMsg = "["+qp.error+"]: " +
                            (qp.error_description ? qp.error_description+ ". " : "no accessCode received from the server. ") +
                            (qp.error_uri ? "More info: "+qp.error_uri : "");
                    }

                    oauth2.errCb({
                        authId: oauth2.auth.name,
                        source: "auth",
                        level: "error",
                        message: oauthErrorMsg || "[Authorization failed]: no accessCode received from the server."
                    });
                }
            } else {
                oauth2.callback({auth: oauth2.auth, token: qp, isValid: isValid, redirectUrl: redirectUrl});
            }
            window.close();
        }

        if (document.readyState !== 'loading') {
            run();
        } else {
            document.addEventListener('DOMContentLoaded', function () {
                run();
            });
        }
    </script>
    </body>
    </html>
        """


def _html_response(body: str) -> HttpResponse:
    """Serve a documentation page with an explicit content length."""
    payload = body.encode("utf-8")
    response = HttpResponse(payload, status=200, content_type=HTML_MEDIA_TYPE)
    del response["Content-Type"]
    response["Content-Length"] = str(len(payload))
    response["Content-Type"] = HTML_MEDIA_TYPE

    return response


def openapi_document(request):
    """Serve the OpenAPI document describing every endpoint."""
    return json_response(OPENAPI_SCHEMA)


def swagger_ui(request):
    """Serve the Swagger UI browser."""
    return _html_response(SWAGGER_UI_HTML)


def swagger_ui_oauth2_redirect(request):
    """Serve the Swagger UI OAuth2 redirect handshake page."""
    return _html_response(OAUTH2_REDIRECT_HTML)


def redoc_ui(request):
    """Serve the ReDoc browser."""
    return _html_response(REDOC_HTML)


GET_AND_HEAD = "GET, HEAD"

openapi = route(
    ("GET", openapi_document), ("HEAD", openapi_document), allow=GET_AND_HEAD
)
docs = route(("GET", swagger_ui), ("HEAD", swagger_ui), allow=GET_AND_HEAD)
oauth2_redirect = route(
    ("GET", swagger_ui_oauth2_redirect),
    ("HEAD", swagger_ui_oauth2_redirect),
    allow=GET_AND_HEAD,
)
redoc = route(("GET", redoc_ui), ("HEAD", redoc_ui), allow=GET_AND_HEAD)

"""
Dump `*/api/*` requests and responses to disk
"""

import datetime
import tempfile
import time
import json
import logging
import os
import traceback

logger = logging.getLogger(__name__)

DUMPING_FOLDER = "mygpo_dump"


class DumpingMiddleware:
    """Request/Response Logging Middleware."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if "/api/" in str(request.get_full_path()):
            start_time = time.monotonic()
            log_data = {
                "user_agent": request.headers["User-Agent"],
                "method": request.method,
                "path": request.get_full_path(),
            }

            log_data["request_body"] = self._parse_request_body(request)

            response = self.get_response(request)

            if response:
                log_data["status_code"] = response.status_code
                log_data["response_headers"] = {
                    k: str(v) for k, v in response.headers.items()
                }
                if response["content-type"] == "application/json":
                    response_body = json.loads(response.content.decode("utf-8"))
                else:
                    try:
                        response_body = response.content.decode("utf-8")
                    except Exception:
                        response_body = (
                            f"Unable to decode {len(response.content)} len response"
                        )
                log_data["response_body"] = response_body

            log_data["run_time"] = time.monotonic() - start_time

            self._save_data(request, log_data)
        else:
            response = self.get_response(request)

        return response

    def process_exception(self, request, exception):
        if "/api/" in str(request.get_full_path()):
            log_data = {
                "user_agent": request.headers["User-Agent"],
                "method": request.method,
                "path": request.get_full_path(),
            }

            log_data["request_body"] = self._parse_request_body(request)

            log_data["exception"] = traceback.format_exception(exception)

            self.save_data(request, log_data)
        return None  # will trigger the default django exception handling

    def _parse_request_body(self, request):
        req_body = None
        if request.content_type == "application/json":
            try:
                # parse as json because it's easier to query later
                req_body = (
                    json.loads(request.body.decode("utf-8")) if request.body else {}
                )
            except ValueError:
                req_body = None
        if req_body is None:
            req_body = (
                request.body.decode("utf-8", errors="replace") if request.body else ""
            )
        return req_body

    def _save_data(self, request, log_data):

        # dump data to disk in mygpo_dump/<first 2 letters in user id>/<user id>/<datetime>_<unique suffix>
        if request.user:
            dirname = os.path.join(
                DUMPING_FOLDER, str(request.user.id)[:2], str(request.user.id)
            )
        else:
            dirname = os.path.join(DUMPING_FOLDER, "unknown")

        os.makedirs(dirname, exist_ok=True)
        filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f_")
        fd, filepath = tempfile.mkstemp(prefix=filename, dir=dirname)
        with open(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(log_data))

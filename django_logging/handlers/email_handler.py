from logging import Handler, LogRecord
from typing import Optional

from django.conf import settings
from django.http import HttpRequest
from django.template import engines
from django.utils.timezone import now
from django_logging.utils.log_email_notifier.notifier import send_email_async
from django_logging.utils.get_conf import use_email_notifier_template
from django_logging.middleware import RequestLogMiddleware


class EmailHandler(Handler):
    def emit(self, record: LogRecord) -> None:
        try:
            request = getattr(record, "request", None)
            log_entry = self.format(record)

            if use_email_notifier_template():
                email_body = self.render_template(log_entry, request)
            else:
                email_body = log_entry

            subject = f"New Log Record: {record.levelname}"
            send_email_async(subject, email_body, [settings.ADMIN_EMAIL])

        except Exception as e:
            self.handleError(record)

    @staticmethod
    def render_template(
        log_entry: str, request: Optional[HttpRequest] = None, template_path: str = "email_notifier_template.html"
    ) -> str:
        django_engine = engines["django"]
        template = django_engine.get_template(template_path)

        # Fetch IP address and user agent using middleware methods
        ip_address = (
            RequestLogMiddleware.get_ip_address(request) if request else "Unknown"
        )
        user_agent = (
            RequestLogMiddleware.get_user_agent(request) if request else "Unknown"
        )

        context = {
            "message": log_entry,
            "time": now(),
            "browser_type": user_agent,
            "ip_address": ip_address,
        }

        return template.render(context)

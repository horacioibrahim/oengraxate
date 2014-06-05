from __future__ import absolute_import
import os

from celery import Celery
from django.conf import settings

from main.utils import send_simple_email, send_mail_text_and_html

# setup DJANGO_SETTINGS_MODULE
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings_dev')
app = Celery('tasks', broker='mongodb://localhost:27017/celery')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Tasks
@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

@app.task(bind=True)
def task_send_simple_email(self, subject, body, recipients, headers=None):
    return send_simple_email(subject, body, recipients, headers)

@app.task(bind=True)
def task_send_mail_text_and_html(self, subject, email_template_name, email_context,
                            recipients, sender=None, bcc=None, files=None):
    return send_mail_text_and_html(subject, email_template_name, email_context,
                                   recipients, sender, bcc, files)


from types import DictionaryType, ListType

from django_ses import SESBackend
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.conf import settings
from django.template import loader, Context
from django.utils.html import strip_tags


def send_simple_email(subject, body, recipients, headers=None):
    """ Send emails for many purposes
    """
    sender = settings.DEFAULT_FROM_EMAIL

    if headers is not None and isinstance(headers, DictionaryType):
        headers = headers
    else:
        # default
        headers = {'Reply-To': settings.AWS_SES_RETURN_PATH}

    assert isinstance(recipients, ListType)
    recipients = recipients

    message = EmailMessage(subject, body,
                           sender, recipients,
                           headers = headers)
    sender = SESBackend()
    result = sender.send_messages([message])

    return result

def send_mail_text_and_html(subject, email_template_name, email_context,
                            recipients, sender=None, bcc=None, files=None):
    """
    send_templated_mail() is a wrapper around Django's e-mail routines that
    allows us to easily send multipart (text/plain & text/html) e-mails using
    templates that are stored in the database. This lets the admin provide
    both a text and a HTML template for each message.

    email_template_name is the slug of the template to use for this message (see
        models.EmailTemplate)

    email_context is a dictionary to be used when rendering the template

    recipients can be either a string, eg 'a@b.com', or a list of strings.

    sender should contain a string, eg 'My Site <me@z.com>'. If you leave it
        blank, it'll use settings.DEFAULT_FROM_EMAIL as a fallback.

    bcc is an optional list of addresses that will receive this message as a
        blind carbon copy.

    fail_silently is passed to Django's mail routine. Set to 'True' to ignore
        any errors at send time.

    files can be a list of file paths to be attached, or it can be left blank.
        eg ('/tmp/file1.txt', '/tmp/image.png')
    """
    c = Context(email_context)
    if not sender:
        sender = settings.DEFAULT_FROM_EMAIL

    tpl_plain = email_template_name + '.txt'
    tpl_html = email_template_name + '.html'

    template_plain = loader.get_template(tpl_plain)
    template_html = loader.get_template(tpl_html)
    text_part = template_plain.render(c)
    html_part = template_html.render(c)

    if type(recipients) == str:
        if recipients.find(','):
            recipients = recipients.split(',')
    elif type(recipients) != list:
        recipients = [recipients,]

    message = EmailMultiAlternatives(subject, text_part, sender, recipients,
                                 bcc=bcc)
    message.attach_alternative(html_part, "text/html")

    if files:
        if type(files) != list:
            files = [files,]

        for file in files:
            message.attach_file(file)

    sender = SESBackend()
    result = sender.send_messages([message,])

    return result
__author__ = 'horacioibrahim'

import json
import os

from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter

# constrains fields to replace code content to html highlight
TOKEN_START_CODE = '#code'
TOKEN_END_CODE = '#endcode'

def zero_hour_tomorrow():
    """
    Return zero hour of next day
    """
    today = timezone.now()
    zero_hour_today = datetime.combine(today, datetime.min.time())
    tomorrow = zero_hour_today + timedelta(days=1)

    return tomorrow

def is_json(json_data):

    try:
        res_json = json.loads(json_data)
    except ValueError, e:
        return False
    return True

def upload_image_handler(f):
    # Save to path MEDIA_ROOT
    image_to_save = os.path.join(settings.MEDIA_ROOT, f.name)
    with open(image_to_save, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    image_url_relative = ''.join([settings.MEDIA_URL,
                                  os.path.basename(destination.name)])
    return image_url_relative

def do_syntax_html(content, fieldseparator=(TOKEN_START_CODE, TOKEN_END_CODE)):
    """
    Receive a string of html or plain text and returns highlighted html
    by pygments

    :type content: string
    :fieldseparator: tuple

    e.g: fieldseparator('#code', '#endcode')

    """
    # helpers must be same len(TOKEN_START_CODE)
    helpers_tokenizer = ('#here', '#endhere')

    if len(helpers_tokenizer[0]) != len(fieldseparator[0]) or \
        len(helpers_tokenizer[1]) != len(fieldseparator[1]):
        raise TypeError(u"Size (len) of helpers in "
                        u"helpers_tokenizer are different.")

    while True:
        # STEP 1: get first index of separator tag
        firstindex = content.find(fieldseparator[0])

        if firstindex == -1:
            break

        # After get index with find changes TOKEN to helpers
        # this changes is done to not find repeated tags
        content = content.replace(fieldseparator[0], helpers_tokenizer[0], 1)
        # STEP 2: get last index of separator tag
        lastindex = content.find(fieldseparator[1])

        if lastindex == -1:
            raise TypeError(u'Error importing block code. Consider '
                            u'adding fieldseparator[2] or TOKEN_END_CODE')

        # After get index with find changes TOKEN to helpers
        # this changes is done to not find repeated tags
        content = content.replace(fieldseparator[1], helpers_tokenizer[1], 1)

        start_cut_code = firstindex + len(fieldseparator[0])
        end_cut_code = lastindex + len(fieldseparator[1])
        code = content[start_cut_code:lastindex]
        code_syntax = highlight(code, PythonLexer(), HtmlFormatter())
        content = content.replace(content[firstindex:end_cut_code],
                                code_syntax)

    return content
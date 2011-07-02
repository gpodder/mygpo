from django import template

register = template.Library()


# see
# http://www.google.com/webmasters/+1/button/


@register.simple_tag
def google_plus_one_head():
    return """<script type="text/javascript" src="https://apis.google.com/js/plusone.js"></script>"""


@register.simple_tag
def google_plus_one_button():
    return """<g:plusone size="medium"></g:plusone>"""

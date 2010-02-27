from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
import hashlib
import math

register = template.Library()

@register.filter
def vertical_bar(value, max):
    ratio = float(value) / float(max) * 100
    s = '<div class="bar" style="width: %s">%s</div>' % (ratio, value)
    return mark_safe(s)

@register.filter
def format_diff(value):
    if value > 0:
        s = '<span class="pos">+%s</span>' % value
    elif value < 0:
        s = '<span class="neg">%s</span>' % value
    else:
        s = ''

    return mark_safe(s)

@register.filter
def timeline(data):
    s = '<script type="text/javascript" src="http://www.google.com/jsapi"></script>\n'
    s += '<script type="text/javascript">\n'
    s += 'google.load("visualization", "1", {"packages":["annotatedtimeline"]});\n'
    s += 'google.setOnLoadCallback(drawChart);\n'
    s += 'function drawChart() {\n'
    s += 'var data = new google.visualization.DataTable();\n'
    s += 'data.addColumn("date", "Date");\n'
    s += 'data.addColumn("number", "Listeners");\n'
    s += 'data.addColumn("string", "title1");\n'
    s += 'data.addColumn("string", "text1");\n'
    s += 'data.addRows([\n'

    for r in data:
        if 'episode' in r and r['episode']:
            episode = '"%s"' % r['episode'].title if r['episode'].title else '"Unnamed Episode"'
            episode_ = '"released"'
        else:
            episode = 'undefined'
            episode_ = 'undefined'

        s += '[new Date(%d, %d, %d), %d, %s, %s],\n' % (r['date'].year, r['date'].month-1, r['date'].day, r['listeners'], episode, episode_)

    s += ']);\n'
    s += 'var chart = new google.visualization.AnnotatedTimeLine(document.getElementById("chart_div"));\n'
    s += 'chart.draw(data, {displayAnnotations: true});\n'
    s += '}\n'
    s += '</script>\n'

    return mark_safe(s)


@register.filter
def pie_chart(parts):
    parts = [
        'cht=p',
        'chs=250x100',
        'chl=%s' % '|'.join(parts.iterkeys()),
        'chd=t:%s' % ','.join([ repr(x) for x in parts.itervalues() ])
        ]

    s = '<img src="http://chart.apis.google.com/chart?%s"' % '&'.join(parts)

    return mark_safe(s)


from django import template
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.contrib.staticfiles.storage import staticfiles_storage

from mygpo.utils import format_time
from mygpo.publisher.utils import colour_repr


register = template.Library()

@register.simple_tag
def vertical_bar(value, max_value, display=None):
    if not max_value:
        return ''

    if display == 'ratio':
        value_str = '%d/%d' % (value, max_value)
    else:
        value_str = str(value)

    # handle value == None
    value = value or 0

    try:
        ratio = min(float(value) / float(max_value), 1) * 100
    except ValueError:
        return ''

    if ratio > 40:
        left = format_html('<span>{}</span>', value_str)
        right = ''
    else:
        left = format_html('&nbsp;')
        right = format_html('<span>{}</span>', value_str)

    return format_html('<div class="barbg"><div class="bar" '
                       'style="width: {:.2d}%">{}</div>{}</div>',
                       ratio, left, right)
    return s

@register.filter
def timeline(data):
    s = '<script type="text/javascript" src="//www.google.com/jsapi"></script>\n'
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
        if r.episode:
            episode = '"%s"' % r.episode.display_title
            episode_ = '"released"'
        else:
            episode = 'undefined'
            episode_ = 'undefined'

        s += '[new Date(%d, %d, %d), %d, %s, %s],\n' % (r.date.year, r.date.month-1, r.date.day, r.playcount, episode, episode_)

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
        'chl=%s' % '|'.join(parts.keys()),
        'chd=t:%s' % ','.join([ repr(x) for x in parts.values() ])
        ]

    s = '<img src="http://chart.apis.google.com/chart?%s"' % '&'.join(parts)

    return mark_safe(s)


@register.simple_tag
def subscriber_change(change):

    if change > 1:
        change -= 1
        return '+{0:.1%}'.format(change)

    # we don't care about negative changes
    return ''

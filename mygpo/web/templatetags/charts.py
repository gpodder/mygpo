from django import template
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.contrib.staticfiles.storage import staticfiles_storage


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
                       'style="width: {:3.0}%">{}</div>{}</div>',
                       ratio, left, right)


@register.filter()
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

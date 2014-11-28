from django import template
from django.utils.safestring import mark_safe
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
        left, right = '<span>'+ value_str +'</span>', ''
    else:
        left, right = '&nbsp;', '<span>'+ value_str +'</span>'
    s = '<div class="barbg"><div class="bar" style="width: %.2d%%">%s</div>%s</div>' % (ratio, left, right)
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
        'chl=%s' % '|'.join(parts.iterkeys()),
        'chd=t:%s' % ','.join([ repr(x) for x in parts.itervalues() ])
        ]

    s = '<img src="http://chart.apis.google.com/chart?%s"' % '&'.join(parts)

    return mark_safe(s)


@register.filter
def episode_heatmap_visualization(heatmap):
    """
    display a visual heatmap using the Google Charts API

    heatmap_data is expected as an array of numbers of users that have
    played this part part of the episode. the length of the parts is
    indicated by step_length; the duration of the whole episode is
    therefore approximated by len(heatmap_data) * step_length
    """
    label_steps = 2

    max_plays = heatmap.max_plays

    if max_plays == 1:
        #              light blue       dark blue
        colours = ( (198, 217, 253), (77, 137, 249) )
    else:
        #               red            yellow         green
        colours = ( (210, 54, 28), (239, 236, 22), (15, 212, 18) )

    WIDTH=760

    # maximum number of labels that will be placed on the visualization
    MAX_LABELS=20

    axis_pos = []
    axis_label = []
    part_colours = []
    widths = []
    duration = max(heatmap.borders)

    last_label = None
    for start, end, plays in heatmap.sections:

        if last_label is None or (end-last_label) > (duration/MAX_LABELS):
            axis_pos.append(end)
            axis_label.append(format_time(end))
            last_label = end

        rgb = colour_repr(plays, max_plays, colours)
        part_colours.append('%02x%02x%02x' % rgb)
        start = start or 0
        widths.append( end-start )

    parts = [
        'cht=bhs',                            # bar chart
        'chco=%s' % ','.join(part_colours),   # colors
        'chs=%dx50' % WIDTH,                  # width corresponds to length, arbitrary height
        'chds=0,%s' % duration,               # axis scaling from 0 to maximum duration
        'chd=t:%s' % '|'.join([repr(w) for w in widths]),  # all block have the same width
        'chxt=x',                             # visible axes
        'chxr=0,0,%s' % duration,             # axis range for axis 0 (x): 0 - duration
        'chxl=0:|%s' % '|'.join(axis_label),  # axis labels
        'chxp=0,%s' % ','.join([repr(x) for x in axis_pos]),   # axis label positions
        ]

    s = '<img src="http://chart.apis.google.com/chart?%s" />' % '&'.join(parts)

    return mark_safe(s)



@register.simple_tag
def subscriber_change(change):

    if change > 1:
        change -= 1
        return '+{0:.1%}'.format(change)

    # we don't care about negative changes
    return ''

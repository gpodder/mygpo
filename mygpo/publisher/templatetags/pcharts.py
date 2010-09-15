from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from mygpo.publisher.utils import colour_repr
from mygpo.utils import format_time
import hashlib
import math

register = template.Library()

@register.filter
def bar_chart(parts):

    maxv = max([ int(x['y']) for x in parts ])
    bar_width = 15
    bar_space = 15
    group_space = 20

    parts = [
        'cht=bvg',     # Vertical bar chart with grouped bars.
        'chs=%dx100' % ((bar_space + group_space) * (len(parts) + 1)),
        'chl=%s' % '|'.join([x['x'] for x in parts]),
        'chd=t:%s' % ','.join([ repr(int(x['y'])) for x in parts ]),
        'chxt=x,y', # visible axes
        'chbh=%d,%d,%d' % (bar_width, bar_space, group_space),
        'chds=0,%d' % maxv, # avis scaling from 0 to max
        'chxr=1,0,%d' % maxv, # labeling for axis 1 (y) from 0 to max
        ]

    s = '<img src="http://chart.apis.google.com/chart?%s"' % '&'.join(parts)

    return mark_safe(s)

@register.filter
def episode_heatmap_visualization(heatmap_data, step_length):
    """
    display a visual heatmap using the Google Charts API

    heatmap_data is expected as an array of numbers of users that have
    played this part part of the episode. the length of the parts is
    indicated by step_length; the duration of the whole episode is
    therefore approximated by len(heatmap_data) * step_length
    """
    label_steps = 2
    #               red            yellow         green
    colours = ( (210, 54, 28), (239, 236, 22), (15, 212, 18) )

    max_val = max(heatmap_data)
    axis_pos = []
    axis_label = []
    part_colours = []
    duration = len(heatmap_data) * step_length

    n=0
    for part in heatmap_data:
        if n % label_steps == 0:
            axis_pos.append(n*step_length)
            axis_label.append(format_time(n*step_length))
        rgb = colour_repr(part, max_val, colours)
        part_colours.append('%02x%02x%02x' % rgb)
        n += 1

    parts = [
        'cht=bhs',                           #bar chart
        'chco=%s' % ','.join(part_colours),  #colors
        'chs=760x50',                        #width corresponds to length, arbitrary height
        'chds=0,%s' % duration,              #axis scaling from 0 to maximum duration
        'chd=t:%s' % '|'.join([repr(step_length)] * len(heatmap_data)),  # all block have the same width
        'chxt=x',                            #visible axes
        'chxr=0,0,%s' % duration,            #axis range for axis 0 (x): 0 - duration
        'chxl=0:|%s' % '|'.join(axis_label), #axis labels
        'chxp=0,%s' % ','.join([repr(x) for x in axis_pos]),             #axis label positions
        ]

    s = '<img src="http://chart.apis.google.com/chart?%s"' % '&'.join(parts)

    return mark_safe(s)



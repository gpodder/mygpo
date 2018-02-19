from django import template

register = template.Library()

@register.filter(is_safe=True)
def bar_chart(parts):

    maxv = max([ int(x['y']) for x in parts ])
    bar_width = 15
    bar_space = 15
    group_space = 20

    width = min(1000, ((bar_space + group_space) * (len(parts) + 1)))

    parts = [
        'cht=bvg',     # Vertical bar chart with grouped bars.
        'chs=%dx100' % width,
        'chl=%s' % '|'.join([x['x'] for x in parts]),
        'chd=t:%s' % ','.join([ repr(int(x['y'])) for x in parts ]),
        'chxt=x,y',  # visible axes
        'chbh=%d,%d,%d' % (bar_width, bar_space, group_space),
        'chds=0,%d' % maxv,  # avis scaling from 0 to max
        'chxr=1,0,%d' % maxv,  # labeling for axis 1 (y) from 0 to max
        ]

    return '<img src="//chart.apis.google.com/chart?%s" />' % '&'.join(parts)

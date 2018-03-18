from django import template

register = template.Library()

@register.filter(is_safe=True)
def google_analytics_async(property_id):
    s = """
    <script type="text/javascript">
        var _gaq = _gaq || [];
        _gaq.push(['_setAccount', '%s']);
        _gaq.push(['_trackPageview']);

        (function() {
            var ga = document.createElement('script');
            ga.type = 'text/javascript';
            ga.async = true;
            ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
            var s = document.getElementsByTagName('script')[0];
            s.parentNode.insertBefore(ga, s);
        })();
    </script>""" % property_id

    return s

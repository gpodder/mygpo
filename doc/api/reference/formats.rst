Formats
=======

Some resources are offered in several different formats

* OPML
* JSON
* JSONP with an option function name that wraps the result (since 2.8)
* plain text with one URL per line
* XML a custom XML format (see example, since 2.9)

JSON
----

JSON::

 [
  {
   "website": "http://sixgun.org",
   "description": "The hardest-hitting Linux podcast around",
   "title": "Linux Outlaws",
   "url": "http://feeds.feedburner.com/linuxoutlaws",
   "position_last_week": 1,
   "subscribers_last_week": 1943,
   "subscribers": 1954,
   "mygpo_link": "http://gpodder.net/podcast/11092",
   "logo_url": "http://sixgun.org/files/linuxoutlaws.jpg",
   "scaled_logo_url": "http://gpodder.net/logo/64/fa9fd87a4f9e488096e52839450afe0b120684b4.jpg"
  },
  # more podcasts here
 ]

XML
---

.. code-block:: xml

 <podcasts>
  <podcast>
   <title>Linux Outlaws</title>
   <url>http://feeds.feedburner.com/linuxoutlaws</url>
   <website>http://sixgun.org</website>
   <mygpo_link>http://gpodder.net/podcast/11092</mygpo_link>
   <description>The hardest-hitting Linux podcast around</description>
   <subscribers>1954</subscribers>
   <subscribers_last_week>1943</subscribers_last_week>
   <logo_url>http://sixgun.org/files/linuxoutlaws.jpg</logo_url>
   <scaled_logo_url>http://gpodder.net/logo/64/fa9fd87a4f9e488096e52839450afe0b120684b4.jpg</scaled_logo_url>
  </podcast>
 </podcasts>


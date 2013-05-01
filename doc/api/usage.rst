API Usage
=========


Client Registration
-------------------

Most API endpoints can only be accessed by registered clients using a client
key. Clients can be registered for free at LINK.

TODO: User-Agent?


Allowed Usage
-------------

**Open source clients** can issue an unlimited number of requests to the API.

**Closed source Clients** (this includes free-of-charge closed source clients)
have a quota of requests per day (UTC). The quota depends on the features
they implement (and activate/enable by default).

If there are open and closed sourced versions of a client, they need to have
two API keys.

The following table shows how the client quota is increased by implementing a
certain feature.

+------------------------+---------------+----------------+
| Features               | Open source   | Closed source  |
+========================+===============+================+
| Podcast Search         | unlimited     | unlimited      |
+------------------------+---------------+----------------+
| Podcast Toplist        | unlimited     | +1000          |
+------------------------+---------------+----------------+
| Top Tags               | unlimited     | +1000          |
+------------------------+---------------+----------------+
| Tag-Podcasts           | unlimited     | +1000          |
+------------------------+---------------+----------------+
| Subscriptions Download | unlimited     | +1000          |
+------------------------+---------------+----------------+
| Subscriptions Upload   | unlimited     | +5000          |
+------------------------+---------------+----------------+
| Device List and Config | unlimited     | +1000          |
+------------------------+---------------+----------------+
| Episode Favorites      | unlimited     | +1000          |
+------------------------+---------------+----------------+
| Authentication         | unlimited     | unlimited      |
+------------------------+---------------+----------------+
| Device Sync            | unlimited     | +1000          |
+------------------------+---------------+----------------+
| Events Upload          | unlimited     | +10000         |
+------------------------+---------------+----------------+
| Events Download        | unlimited     | +10000         |
+------------------------+---------------+----------------+
| Podcast Lists          | unlimited     | +1000          |
+------------------------+---------------+----------------+
| Settings               | unlimited     | +1000          |
+------------------------+---------------+----------------+


Misbehaving Clients
-------------------

Violations of rules that are given as *MUST* or *MUST NOT* are recorded. Any
client application may accumulate 100 of such violations per day (to accomodate
for bug fixing and debugging). Client applications that regularly
exceed this limit will be blocked. The status (and reports) of a client
application's violations can be viewed online. TODO: where?


TODO: distinguish between (individual) clients and client applications.

.. _api3:


API 3 (Draft)
=============

This is *a draft* for version 3 of the public API of gpodder.net.

Client Access
-------------

* Require client keys to identify clients, get a communication channel
  to developers
* Clients must send a valid User-Agent string
* API usage free for open source clients
* Quota for non-open clients -- higher quota if more features are
  implemented; paid quota increase

Proposed Changes to API 2
-------------------------
* The classification between Simple and Advanced API is dropped
* A separate domain name for API requests will be used (something like
  api.gpodder.net, see :ref:`api-parametrization`
* The ``/api/`` prefix has been dropped (in favor of a API domain name) and a
  version prefix (``/3/``) has been added for all endpoints
* Device-Data and Settings are updated with PUT instead of POST (because they
  overwrite existing data)
* Things to consider:
  `Evolving HTTP APIs <http://www.mnot.net/blog/2012/12/04/api-evolution>`_

Additional Ideas
----------------

* Use authentication protocol `OAuth2
  <https://tools.ietf.org/html/draft-ietf-oauth-v2-18>`_

Open Questions
--------------
* What's the best way of documenting a REST API?
  http://stackoverflow.com/questions/898321/standard-methods-for-documenting-a-restful-api
  http://answers.oreilly.com/topic/1390-how-to-document-restful-web-services/
* Specify deprecation guideline + timeline for when the old API will stop
  functioning


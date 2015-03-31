from math import ceil

from mygpo.directory.search import search_podcasts
from mygpo.api import APIView

RESULTS_PER_PAGE=20


class PodcastSearch(APIView):

    def get(self, request):

        if 'q' not in request.GET:
            return {
                'q': '',
                'results': [],
                'num_results': 0,
            }

        q = request.GET.get('q', '').encode('utf-8')

        try:
            page = int(request.GET.get('page', 1))
        except ValueError:
            page = 1

        start = RESULTS_PER_PAGE*(page-1)
        results = search_podcasts(q)
        total = len(results)
        num_pages = int(ceil(total / RESULTS_PER_PAGE))
        results = results[start:start+RESULTS_PER_PAGE]

        return {
            'q': q,
            'results': results,
        }

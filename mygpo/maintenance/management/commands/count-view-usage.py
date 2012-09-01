import gzip

from django.core.management.base import BaseCommand
from django.core.urlresolvers import resolve, Resolver404

from mygpo.counter import Counter



class Command(BaseCommand):
    """ Calculates the view-usage from CouchDB log files

    log files can be gzipped. Output is printed to stdout """

    def handle(self, *args, **options):

        handlers = Counter()

        show_max = None

        for f in self.open_files(args):
            for line in f:

                # assume standard Apache log format
                part = line.split(' ')[6]

                try:
                    match = resolve(part)
                except Resolver404:
                    pass

                mod = match.func.__module__
                key = (mod, match.func.__name__)
                handlers[key] += 1


        for (mod, funcname), n in handlers.most_common(show_max):
            fqname = '{}.{}'.format(mod, funcname)
            print '{:60} {:>7}'.format(fqname, n)


    def open_files(self, files):
        for filename in files:
            if '.gz' in filename:
                yield gzip.open(filename)
            else:
                yield open(filename)

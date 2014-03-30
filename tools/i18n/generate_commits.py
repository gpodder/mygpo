#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# generate_commits.py - Generate Git commits based on Transifex updates
# Thomas Perl <thp@gpodder.org>; 2012-08-16
#

import re
import glob
import subprocess
import os.path

filenames = []

pofiles = os.path.join(os.path.dirname(os.path.abspath(__file__)),
        '..', '..', '..', 'mygpo', 'locale', '*', 'LC_MESSAGES', 'django.po')

process = subprocess.Popen(['git', 'status', '--porcelain'] +
        glob.glob(pofiles), stdout=subprocess.PIPE)
stdout, stderr = process.communicate()
for line in stdout.splitlines():
    status, filename = line.strip().split()
    if status == 'M':
        filenames.append(filename)

for filename in filenames:
    in_translators = False
    translators = []
    language = None

    filename = os.path.join('..', '..', filename)
    for line in open(filename).read().splitlines():
        if line.startswith('# Translators:'):
            in_translators = True
        elif in_translators:
            match = re.match(r'# ([^<]* <[^>]*>)', line)
            if match:
                translators.append(match.group(1))
            else:
                in_translators = False

        match = re.search(r'Last-Translator: ([^<]* <[^>]*>)', line)
        if match:
            translators.append(match.group(1))

        match = re.match(r'"Language-Team: ([^\(]+) \(http://www.transifex.net/', line)
        if not match:
            match = re.match(r'"Language-Team: ([^\(]+).*\\n"', line, re.DOTALL)
        if match:
            language = match.group(1).strip()

    if translators and language is not None:
        if len(translators) != 1:
            print '# Warning: %d other translators' % (len(translators) - 1,)
        print 'git commit --author="%s" --message="Updated %s translation" %s' % (translators[0], language, filename)
    else:
        print '# FIXME (could not parse):', '!'*10, filename, '!'*10


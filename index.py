#!/usr/bin/python3
# © 2021 Cyril Brulebois <cyril@debamax.com>

import functools
import os
import re

import apt_pkg
import dominate
from dominate.tags import *
from dominate.util import text, raw


TITLE = 'aptly-webindex'

CSS = '''
h1 {
  text-align: center;
  color: #a80030;
  text-decoration: underline;
}
h4 {
  text-align: center;
}
table {
  width: 100%;
  border: 1px solid #333;
  border-collapse: collapse;
}
th {
  background-color: #a80030;
  color: #FFF;
}
th.distribution {
  background-color: #880020;
}
td {
  vertical-align: top;
  border: 1px solid black;
  padding: 2px 5px;
  white-space: nowrap;
}
td.centered {
  text-align: center;
}
td.versions {
  white-space: normal;
}
.mono {
  font-family: monospace;
}

/* Multi-dist support: try to align columns across tables */
.col1 { width: 15%; }
.col2 { width: 10%; }
.col3 { width:  5%; }
.col4 { width: 70%; }
'''


def render_dist_html(dist):
    archs = [re.sub(r'^binary-', '', x)
             for x in os.listdir('dists/%s/main' % dist)
             if x.startswith('binary')]

    # Store [source_arch, package, version, actual_arch, filename]:
    data = []
    for arch in archs:
        with open('dists/%s/main/binary-%s/Packages' % (dist, arch), 'r') as packages_fp:
            tagfile = apt_pkg.TagFile(packages_fp)
            for stanza in tagfile:
                fp = stanza['Package']
                fv = stanza['Version']
                fa = stanza['Architecture']
                ff = stanza['Filename']
                data.append([arch, fp, fv, fa, ff])

    packages = sorted(list(set([row[1] for row in data])))
    for package in packages:
        versions = sorted(list(set([row[2] for row in data if row[1] == package])),
                          reverse=True, key=functools.cmp_to_key(apt_pkg.version_compare))

        # Extract version information:
        newest_version = versions[0]
        older_versions = ' | '.join(versions[1:])

        # Filter lines matching newest version:
        newest_items = sorted([row for row in data if row[1] == package and row[2] == newest_version])

        # Extract the dirname of one of the Filename fields:
        pool_dir = re.sub(r'/[^/]+$', '', newest_items[0][4])

        # Prepare links to debs:
        newest_debs = sorted(list(set([(row[3], row[4]) for row in newest_items])))

        with tr():
            td(a(package, href=pool_dir))
            td(newest_version, _class='centered')
            with td(_class='centered'):
                # XXX: Maybe there's a way to implement join() in a better way:
                for i, row in enumerate(newest_debs):
                    if i != 0:
                        text(' | ')
                    a(row[0], href=row[1])
            td(older_versions, _class='versions')



if __name__ == '__main__':
    # XXX: Maybe error out if that doesn't return anything, or if
    #      dists/<item>/Release is missing
    dists = sorted(os.listdir('dists'))
    apt_pkg.init_system()

    doc = dominate.document(title=TITLE)

    with doc.head:
        style(CSS)

    with doc.body:
        h1(TITLE)
        with h4():
            text('Available distributions: ')
            for i, dist in enumerate(dists):
                if i != 0:
                    text(' | ')
                a(dist, href='#%s' % dist, _class='mono')

            text(' — ')
            text('direct access: ')
            a('dists', href='dists/', _class='mono')
            text(' | ')
            a('pool', href='pool/', _class='mono')

    for dist in dists:
        with doc.add(table()):
            with tr():
                attr(id=dist)
                th('Distribution: %s' % dist, colspan=4, _class='distribution')
            with tr():
                th(raw('Package<br>name'), _class='col1')
                th(raw('Newest<br>versions'), _class='col2')
                th(raw('Newest<br>debs'), _class='col3')
                th(raw('Older<br>versions'), _class='col4')
            render_dist_html(dist)
            br()

    print(doc)

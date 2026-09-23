"""One source of truth for the site header, mobile menu and footer.

The three blocks live in partials/. Running this script writes them into every
page in the repo, so a change to the nav or the footer is a one-file edit
followed by one command:

    uv run --python 3.14 python tools/sync-partials.py

    --check   report pages that have drifted, change nothing (exit 1 if any)

Two things vary per page and this script owns both of them, so the partials
themselves stay neutral:

  * the logo links to "#top" on the homepage and to index.html everywhere else
  * the nav item for the section a page belongs to carries "is-active"
"""
import os, re, sys, glob

ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTIALS = os.path.join(ROOT, 'partials')

BLOCKS = [
    ('header.html',      re.compile(r'<header class="nav">.*?</header>', re.S)),
    ('mobile-menu.html', re.compile(r'<div class="mobile-menu" id="mobileMenu">.*?\n</div>', re.S)),
    ('footer.html',      re.compile(r'<footer>.*?</footer>', re.S)),
]

HOME = 'index.html'

# page -> the nav item that should be underlined as the current section
ACTIVE = {
    'about.html': 'About',            'success-stories.html': 'About',
    'ati-360.html': 'ATI',            'ati-education-certification.html': 'ATI',
    'massage-therapy.html': 'Therapies', 'physiotherapy.html': 'Therapies',
    'personal-training.html': 'Services',
    'cardiovascular.html': 'Conditions', 'long-covid.html': 'Conditions',
    'neurological.html': 'Conditions',   'plantar-fasciitis.html': 'Conditions',
    'wei-water-exercise-institute.html': 'WEI',   # label is WEI + a trademark sign
}

def read(p):
    return open(p, encoding='utf-8', newline='').read().replace('\r\n', '\n')

def write(p, s):
    open(p, 'w', encoding='utf-8', newline='').write(s.replace('\n', '\r\n'))

def header_for(page, header):
    """The neutral header, adjusted for this page."""
    if page == HOME:
        header = header.replace('<a class="logo" href="index.html">',
                                '<a class="logo" href="#top">', 1)
    section = ACTIVE.get(page)
    if section:
        # mark the nav item whose label is `section`
        pat = re.compile(r'(<div class="nav-item(?: has-drop)?)(">\s*(?:<button[^>]*>|<a class="nav-top"[^>]*>)'
                         + re.escape(section) + r')')
        header, n = pat.subn(lambda m: m.group(1) + ' is-active' + m.group(2), header, count=1)
        if n != 1:
            raise SystemExit('%s: could not mark "%s" as the active nav item' % (page, section))
    return header

def main():
    check = '--check' in sys.argv
    partials = {}
    for name, _ in BLOCKS:
        path = os.path.join(PARTIALS, name)
        if not os.path.exists(path):
            raise SystemExit('missing partial: ' + path)
        partials[name] = read(path).rstrip('\n')

    pages = sorted(os.path.basename(p) for p in glob.glob(os.path.join(ROOT, '*.html')))
    changed, drifted = [], []
    for page in pages:
        path = os.path.join(ROOT, page)
        src = read(path)
        out = src
        for name, pattern in BLOCKS:
            block = partials[name]
            if name == 'header.html':
                block = header_for(page, block)
            found = pattern.findall(out)
            if len(found) != 1:
                raise SystemExit('%s: found %d copies of %s, expected 1' % (page, len(found), name))
            out = pattern.sub(lambda _m, b=block: b, out, count=1)   # pattern already carries re.S
        if out != src:
            (drifted if check else changed).append(page)
            if not check:
                write(path, out)

    if check:
        if drifted:
            print('out of sync with partials/ (%d):' % len(drifted))
            for p in drifted:
                print('  ' + p)
            return 1
        print('all %d pages match partials/' % len(pages))
        return 0

    print('synced %d pages, %d updated' % (len(pages), len(changed)))
    for p in changed:
        print('  ' + p)
    return 0

if __name__ == '__main__':
    sys.exit(main())

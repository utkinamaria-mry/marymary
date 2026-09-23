"""Parse the SDA citizenship test PDFs (text extracted by pypdf) into JSON."""
import json, re, sys, pypdf

GEO = 'აბგდ'
PAGE_HDR = re.compile(r'^ტესტები საქართველოს მოქალაქეობის მოპოვებისათვის')
OPT = re.compile(r'^\s*([აბგდ])[).]\s*(.*)$')

def lines_of(path):
    r = pypdf.PdfReader(path)
    out = []
    for pg in r.pages:
        ls = [l.rstrip() for l in (pg.extract_text() or '').split('\n')]
        # drop running header and page number
        clean = []
        skip_num = False
        for l in ls:
            if PAGE_HDR.match(l.strip()):
                skip_num = True; continue
            if skip_num and re.fullmatch(r'\s*\d+\s*', l):
                skip_num = False; continue
            clean.append(l)
        out += clean
    return out

# words the PDF text layer split with a stray space
SPLIT_WORDS = ['აირჩე ვა', 'საქართვე ლოს', 'უმრავლესობი ს', 'თანამდებობ ა', 'შემთხვევა ში',
               'გადაწყვეტილ ებას', 'ასე თი', 'მომსახურების ათვის', 'სა ხელმწიფოს', 'შ ემთხვევაში']

def tidy(t):
    t = re.sub(r'[ \t]+', ' ', t).strip()
    for w in SPLIT_WORDS:
        t = t.replace(w, w.replace(' ', ''))
    t = re.sub(r' +([,.;:!?])', r'\1', t)          # "word ," -> "word,"
    t = re.sub(r'(?<=[ა-ჰ]) ?- (?=მინისტრ)|(?<=[ა-ჰ]) -(?=[ა-ჰ])', '-', t)  # "პრემიერ -მინისტრი"
    t = re.sub(r'„ +', '„', t)
    t = re.sub(r'^„(?!.*“)', '', t)                    # unmatched opening quote
    return t.strip()

GLUED = re.compile(r'^(.*\S)\s{3,}((?:I|II|III)\.\d+\.\d+\.?\s*[-–]\s*[აბგდ]\)?)\s*$')

def split_glued(lines):
    for l in lines:
        m = GLUED.match(l)
        if m:
            yield m.group(1); yield m.group(2)
        else:
            yield l

def parse(path, kind):
    if kind == 'language':
        qhead = re.compile(r'^((?:I|II|III)\.\d+\.\d+)\.?\s+(.*)$')
        ans = re.compile(r'^((?:I|II|III)\.\d+\.\d+)\.?\s*[-–]\s*([აბგდ])\)?')
    else:
        qhead = re.compile(r'^(\d+)\.\s+(.*)$')
        ans = re.compile(r'^სწორი\s+პასუხი[ა]?\s*[:–-]?\s*([აბგდ])')
    qs, cur, topic, pending, major = [], None, '', [], ''
    state = None  # 'q' | 'opt'
    for l in split_glued(lines_of(path)):
        l = l.strip()
        if not l:
            continue
        m = ans.match(l)
        if m and cur:
            cur['c'] = GEO.index(m.group(m.lastindex))
            if kind == 'language' and m.group(1) != cur['id']:
                print('id mismatch', cur['id'], m.group(1), file=sys.stderr)
            qs.append(cur); cur = None; state = None; pending = []
            continue
        m = qhead.match(l)
        if m and (cur is None):
            for h in pending:
                if kind == 'language':
                    if re.match(r'^(I|II|III)\.\s', h): major = h
                    elif re.match(r'^\d\.\s', h): topic = major + ' / ' + h
                elif kind == 'history' and not re.search(r'[;.,:]$', h) and len(h) < 40:
                    topic = h
            cur = {'id': m.group(1), 'topic': topic, 'q': m.group(2), 'a': []}
            state = 'q'; pending = []
            continue
        if cur is None:
            pending.append(l)
            continue
        m = OPT.match(l)
        if m and (len(cur['a']) == GEO.index(m.group(1))):
            cur['a'].append(m.group(2)); state = 'opt'
            continue
        if state == 'q':
            cur['q'] += '\n' + l
        elif state == 'opt':
            cur['a'][-1] += ' ' + l
    if cur:
        print('unterminated', cur['id'], file=sys.stderr)
    for q in qs:
        # keep line breaks only where they are meaningful (after the prompt, before dialogue lines)
        parts = q['q'].split('\n')
        text = parts[0]
        for i, p in enumerate(parts[1:]):
            if i == 0 and re.search(r'[?:!.]$', text) or p.startswith(('–', '-')):
                text += '\n' + p
            elif re.search(r'[ა-ჰ]-$', text):
                text += p
            else:
                text += ' ' + p
        q['q'] = tidy(text)
        q['a'] = [tidy(a).rstrip(';.').strip() for a in q['a']]
        if len(q['a']) != 4:
            print('options', q['id'], len(q['a']), file=sys.stderr)
    if kind == 'language':
        mark_underlines(path, qs)
    return qs

def mark_underlines(path, qs):
    """Words underlined in the PDF ("ხაზგასმული სიტყვა") -> wrap as __word__."""
    import pdfplumber
    found = []
    with pdfplumber.open(path) as pdf:
        for pg in pdf.pages:
            if 'ხაზგასმ' not in (pg.extract_text() or ''):
                continue
            words = pg.extract_words()
            for r in sorted(pg.rects + pg.lines, key=lambda r: r['top']):
                if r['height'] >= 2.5 or r['width'] > 200 or r['width'] < 5:
                    continue
                w = [w['text'] for w in words if abs(w['bottom'] - r['top']) < 4
                     and w['x1'] > r['x0'] + 1 and w['x0'] < r['x1'] - 1]
                if w:
                    found.append(w[0])
    targets = [q for q in qs if 'ხაზგასმ' in q['q']]
    if len(found) != len(targets):
        print('underline mismatch', len(found), len(targets), file=sys.stderr)
    for q, w in zip(targets, found):
        head, _, body = q['q'].partition('\n')
        body = re.sub(r'(?<![ა-ჰ])' + re.escape(w) + r'(?![ა-ჰ])', '__' + w + '__', body, count=1)
        q['q'] = head + '\n' + body

if __name__ == '__main__':
    kind, path, out = sys.argv[1:4]
    qs = parse(path, kind)
    print(kind, len(qs), file=sys.stderr)
    json.dump(qs, open(out, 'w'), ensure_ascii=False, indent=1)

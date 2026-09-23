"""Convert data/ru/<subject>.txt (id|question|opt ## opt ## ...) to data/ru/<subject>.json and validate."""
import json, os, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for k in sys.argv[1:] or ('language', 'history', 'law'):
    src = f'{root}/data/ru/{k}.txt'
    if not os.path.exists(src):
        continue
    qs = {q['id']: q for q in json.load(open(f'{root}/data/{k}.json'))}
    out = {}
    for n, line in enumerate(open(src), 1):
        line = line.rstrip('\n')
        if not line.strip():
            continue
        qid, q, a = line.split('|')
        a = [x.strip() for x in a.split(' ## ')]
        q = q.replace(' / ', '\n')
        if qid not in qs: sys.exit(f'{k}:{n} unknown id {qid}')
        if len(a) != len(qs[qid]['a']): sys.exit(f'{k}:{n} {qid} has {len(a)} options, expected {len(qs[qid]["a"])}')
        if ('__' in qs[qid]['q']) != ('__' in q): sys.exit(f'{k}:{n} {qid} underline marker mismatch')
        out[qid] = {'q': q, 'a': a}
    json.dump(out, open(f'{root}/data/ru/{k}.json', 'w'), ensure_ascii=False, indent=1)
    missing = [i for i in qs if i not in out]
    print(k, len(out), 'translated; missing:', missing[:10], '...' if len(missing) > 10 else '')

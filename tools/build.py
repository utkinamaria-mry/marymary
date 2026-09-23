"""Build questions.js from data/<subject>.json, data/ru/<subject>.json (translations)
and data/notes/<subject>.txt (study notes: history id|note|mnemonic, law id|source|note|mnemonic)."""
import json, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = {}
for k in ('language', 'history', 'law'):
    qs = json.load(open(f'{root}/data/{k}.json'))
    ru_path = f'{root}/data/ru/{k}.json'
    ru = json.load(open(ru_path)) if os.path.exists(ru_path) else {}
    notes = {}
    notes_path = f'{root}/data/notes/{k}.txt'
    if os.path.exists(notes_path):
        for line in open(notes_path):
            p = line.rstrip('\n').split('|')
            if len(p) == 3:
                notes[p[0]] = {'note': p[1], 'mem': p[2]}
            elif len(p) == 4:
                notes[p[0]] = {'src': p[1], 'note': p[2], 'mem': p[3]}
    for q in qs:
        if q['id'] in notes:
            q['x'] = notes[q['id']]
        t = ru.get(q['id'])
        if t:
            q['q_ru'] = t['q']
            q['a_ru'] = t['a']
    out[k] = qs
with open(f'{root}/questions.js', 'w') as f:
    f.write('// Сгенерировано tools/build.py из официальных тестов SDA 2024 (sda.gov.ge). Не править вручную.\n')
    f.write('window.QUESTIONS = ' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';\n')
print({k: (len(v), sum('q_ru' in q for q in v), sum('x' in q for q in v)) for k, v in out.items()})

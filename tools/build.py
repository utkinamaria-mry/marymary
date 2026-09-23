"""Build questions.js from data/<subject>.json and data/ru/<subject>.json (translations)."""
import json, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = {}
for k in ('language', 'history', 'law'):
    qs = json.load(open(f'{root}/data/{k}.json'))
    ru_path = f'{root}/data/ru/{k}.json'
    ru = json.load(open(ru_path)) if os.path.exists(ru_path) else {}
    for q in qs:
        t = ru.get(q['id'])
        if t:
            q['q_ru'] = t['q']
            q['a_ru'] = t['a']
    out[k] = qs
with open(f'{root}/questions.js', 'w') as f:
    f.write('// Сгенерировано tools/build.py из официальных тестов SDA 2024 (sda.gov.ge). Не править вручную.\n')
    f.write('window.QUESTIONS = ' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';\n')
print({k: (len(v), sum('q_ru' in q for q in v)) for k, v in out.items()})

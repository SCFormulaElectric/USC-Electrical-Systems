import sys, re, pymupdf
sys.stdout.reconfigure(encoding='utf-8')
d = pymupdf.open(sys.argv[1]); t = [p.get_text() for p in d]
open(sys.argv[1] + '.txt', 'w', encoding='utf-8').write('\n=====PAGE\n'.join(t))
for kw in sys.argv[2:]:
    n = 0
    for i, p in enumerate(t):
        for m in re.finditer(kw, p):
            print(f'[{kw} p{i+1}]', p[max(0, m.start()-200):m.end()+350].replace('\n', ' '))
            n += 1
            if n >= 2: break
        if n >= 2: break

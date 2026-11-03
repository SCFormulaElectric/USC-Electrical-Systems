import re

TOK = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+')


def parse(t):
    st = [[]]
    for m in TOK.finditer(t):
        s = m.group()
        if s == '(':
            st.append([])
        elif s == ')':
            x = st.pop()
            st[-1].append(x)
        else:
            st[-1].append(s[1:-1] if s[0] == '"' else s)
    return st[0][0]


def load(p):
    return parse(open(p, encoding='utf-8').read())


def find(n, k):
    return [c for c in n if isinstance(c, list) and c and c[0] == k]


def one(n, k):
    r = find(n, k)
    return r[0] if r else None

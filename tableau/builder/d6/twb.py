"""Small Tableau .twb writer (from Dashboard #5), used for Dashboard #6 (Workforce Cost Bridge).

Calculations are written in plain names ([F Fills], [p_Period]); this module gives them ids, infers each one's
level (const, row, agg, tc) and data type, wraps row-level references inside aggregate formulas in MIN() (Tableau
refuses to mix them), and writes worksheets, the dashboard, actions and windows into a base workbook that holds
the Custom SQL and its extract.
"""
import re
import uuid

AGG = {'SUM', 'AVG', 'MIN', 'MAX', 'COUNT', 'COUNTD', 'PERCENTILE', 'ATTR', 'MEDIAN'}
TCF = {'RUNNING_SUM', 'RUNNING_AVG', 'RUNNING_MAX', 'RUNNING_MIN', 'WINDOW_SUM', 'WINDOW_AVG', 'WINDOW_MAX',
       'WINDOW_MIN', 'LAST', 'FIRST', 'INDEX', 'SIZE', 'LOOKUP', 'PREVIOUS_VALUE', 'RANK'}
TOKEN = re.compile(r'"(?:[^"]|"")*"|\[[^\[\]]+\]|[A-Za-z_][A-Za-z_0-9]*|\d+\.?\d*|<>|<=|>=|\S', re.S)


def esc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
             .replace("'", '&apos;').replace('\n', '&#10;'))


def xesc(s):
    """attribute escape without touching quotes inside CDATA-free plain text"""
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace("'", '&apos;')


def indent(s, n):
    return '\n'.join((' ' * n + l) if l.strip() else '' for l in s.split('\n')).replace('\n\n', '\n')


def uid():
    return '{' + str(uuid.uuid4()).upper() + '}'


def tokens(f):
    return [(m.group(0), m.start(), m.end()) for m in TOKEN.finditer(f)]


def single_arg(toks, i):
    """toks[i] is '(' : True if the call has one argument (no comma at depth 1)."""
    d = 0
    for t, _, _ in toks[i:]:
        if t in '({':
            d += 1
        elif t in ')}':
            d -= 1
            if d == 0:
                return True
        elif t == ',' and d == 1:
            return False
    return True


class Model:
    def __init__(self, ds, raw_types, params, id_prefix='06102729', caption='Workforce Cost Bridge'):
        self.ds = ds
        self.caption = caption
        self.raw = dict(raw_types)          # name -> local type
        self.params = dict(params)          # name -> dict(dtype, value, members)
        self.pid = {p: f'Parameter {id_prefix}0000{i:02d}' for i, p in enumerate(self.params, 1)}
        self.calcs = {}                     # name -> formula (plain names)
        self.order = []
        self.cid = {}
        self.meta = {}                      # name -> dict(level, dtype, fmt, role, typ)
        self.prefix = id_prefix
        self.raw_role = {}
        self.aliases = {}

    # ---------- registry ----------
    def add(self, name, formula, fmt=None, dtype=None, role=None):
        assert name not in self.calcs, name
        self.calcs[name] = formula.strip('\n')
        self.order.append(name)
        self.cid[name] = f'Calculation_{self.prefix}{len(self.order):08d}'
        self.meta[name] = {'fmt': fmt, 'dtype': dtype, 'role': role}

    def refs(self, f):
        return [t[1:-1] for t, _, _ in tokens(f) if t.startswith('[') and t[1:-1] in self.calcs or
                t.startswith('[') and (t[1:-1] in self.raw or t[1:-1] in self.params)]

    # ---------- inference ----------
    @staticmethod
    def scan(f):
        """yields (token, start, end, kind, inner): kind 'agg' / 'tc' for a call name, inner = inside an aggregate or LOD"""
        toks = tokens(f)
        stack = []
        for i, (t, a, b) in enumerate(toks):
            nxt = toks[i + 1][0] if i + 1 < len(toks) else ''
            inner = any(s in ('agg', 'lod') for s in stack)
            kind = None
            if t.upper() in TCF and nxt == '(':
                kind = 'tc'; stack.append('fn*')
            elif t.upper() in AGG and nxt == '(':
                is_agg = not (t.upper() in ('MIN', 'MAX') and not single_arg(toks, i + 1))
                kind = 'agg' if is_agg else None
                stack.append('agg*' if is_agg else 'fn*')
            elif t == '(':
                if stack and stack[-1].endswith('*'):
                    stack[-1] = stack[-1][:-1]
                else:
                    stack.append('p')
            elif t == '{':
                kind = 'lod'
                stack.append('lod')
            elif t in ')}':
                if stack:
                    stack.pop()
            yield t, a, b, kind, inner

    def level(self, name):
        m = self.meta[name]
        if 'level' in m:
            return m['level']
        rank = {'const': 0, 'row': 1, 'agg': 2, 'tc': 3}
        lv = 'const'
        for t, a, b, kind, inner in self.scan(self.calcs[name]):
            new = None
            if kind == 'tc':
                new = 'tc'
            elif kind == 'agg' and not inner:
                new = 'agg'
            elif kind == 'lod' and not inner:
                new = 'row'
            elif t.startswith('[') and not inner:
                n = t[1:-1]
                if n in self.calcs:
                    new = self.level(n)
                elif n in self.raw:
                    new = 'row'
            if new and rank[new] > rank[lv]:
                lv = new
        m['level'] = lv
        return lv

    def _branch(self, f):
        """the first result expression of an IF / CASE formula, else f"""
        s = f.strip()
        while s.startswith('(') and self._closing(s, 0) == len(s) - 1:
            s = s[1:-1].strip()
        if re.match(r'(IF|CASE)\b', s):
            toks = tokens(s)
            d = 0
            for i, (t, a, b) in enumerate(toks):
                if t in '({':
                    d += 1
                elif t in ')}':
                    d -= 1
                elif t == 'THEN' and d == 0:
                    start = b
                    dd = 0
                    nest = 0
                    for t2, a2, b2 in toks[i + 1:]:
                        if t2 in '({':
                            dd += 1
                        elif t2 in ')}':
                            dd -= 1
                        elif dd == 0 and t2 in ('IF', 'CASE'):
                            nest += 1
                        elif dd == 0 and t2 == 'END' and nest:
                            nest -= 1
                        elif dd == 0 and nest == 0 and t2 in ('ELSE', 'ELSEIF', 'WHEN', 'END'):
                            return self._branch(s[start:a2])
                    return self._branch(s[start:])
        return s

    def _closing(self, s, i):
        d = 0
        for j, (t, a, b) in enumerate(tokens(s[i:])):
            if t in '({':
                d += 1
            elif t in ')}':
                d -= 1
                if d == 0:
                    return i + a
        return -1

    def dtype(self, name):
        m = self.meta[name]
        if m.get('dtype'):
            return m['dtype']
        m['dtype'] = self._etype(self.calcs[name])
        return m['dtype']

    def _etype(self, e):
        s = self._branch(e)
        toks = tokens(s)
        if not toks:
            return 'string'
        d = 0
        top = []
        for t, a, b in toks:
            if t in '({':
                d += 1
            elif t in ')}':
                d -= 1
            elif d == 0:
                top.append(t)
        if any(t in ('=', '<>', '<', '>', '<=', '>=', 'AND', 'OR') for t in top) or (top and top[0] == 'NOT'):
            return 'boolean'
        if any(t.startswith('"') for t in top):
            return 'string'
        t = self._etype0(s, toks)
        if t in ('integer', 'real') and any(x in ('+', '-', '*', '/') for x in top):
            return 'real'
        return t

    def _etype0(self, s, toks):
        t0 = toks[0][0]
        if t0 in ('TRUE', 'FALSE'):
            return 'boolean'
        if t0.startswith('"'):
            return 'string'
        if re.match(r'\d', t0):
            return 'real' if '.' in t0 else 'integer'
        if t0 == '{':
            inner = s[1:self._closing(s, 0)]
            if ':' in inner and re.match(r'\s*(FIXED|INCLUDE|EXCLUDE)\b', inner):
                inner = inner.split(':', 1)[1]
            return self._num(self._etype(inner))
        if t0 == '(':
            return self._etype(s[1:self._closing(s, 0)])
        if t0.startswith('['):
            n = t0[1:-1]
            if n in self.calcs:
                return self.dtype(n)
            if n in self.params:
                return self.params[n]['dtype']
            return {'integer': 'integer', 'real': 'real', 'string': 'string', 'boolean': 'boolean', 'date': 'date'}[self.raw[n]]
        fn = t0.upper()
        if fn in ('STR', 'LEFT', 'RIGHT', 'REPLACE', 'REGEXP_REPLACE', 'UPPER', 'LOWER', 'TRIM', 'DATENAME'):
            return 'string'
        if fn in ('CONTAINS', 'ISNULL', 'STARTSWITH', 'ENDSWITH'):
            return 'boolean'
        if fn in ('COUNTD', 'COUNT', 'INT', 'DIV', 'DATEDIFF'):
            return 'integer'
        if fn in ('MIN', 'MAX', 'ATTR', 'WINDOW_MAX', 'WINDOW_MIN', 'ZN'):
            inner = s[s.index('(') + 1:self._closing(s, s.index('('))]
            return self._num(self._etype(inner)) if fn != 'ZN' else 'real'
        return 'real'

    @staticmethod
    def _num(t):
        return t

    # ---------- compile ----------
    def compiled(self, name):
        f = self.calcs[name]
        lv = self.level(name)
        out, last = [], 0
        for t, a, b, kind, inner in self.scan(f):
            if not t.startswith('['):
                continue
            n = t[1:-1]
            rep = None
            if n in self.calcs:
                rep = f'[{self.cid[n]}]'
                if lv in ('agg', 'tc') and not inner and self.level(n) in ('row', 'const'):
                    rep = f'MIN({rep})'
            elif n in self.params:
                rep = f'[Parameters].[{self.pid[n]}]'
            elif n in self.raw and lv in ('agg', 'tc') and not inner:
                rep = f'MIN({t})'
            if rep:
                out.append(f[last:a]); out.append(rep); last = b
        out.append(f[last:])
        return f'// {name}\n' + ''.join(out)

    def plain(self, name):
        """the formula with plain names, after MIN() wrapping (for the as-built guide)"""
        c = self.compiled(name)
        inv = {v: k for k, v in self.cid.items()}
        c = re.sub(r'\[(Calculation_\d+)\]', lambda m: f'[{inv[m.group(1)]}]', c)
        invp = {v: k for k, v in self.pid.items()}
        c = re.sub(r'\[Parameters\]\.\[(Parameter \d+)\]', lambda m: f'[{invp[m.group(1)]}]', c)
        return c.split('\n', 1)[1]

    def role(self, name):
        m = self.meta[name]
        lv, dt = self.level(name), self.dtype(name)
        if m.get('role'):
            return m['role']
        if dt in ('string', 'boolean'):
            return ('dimension', 'nominal') if lv in ('const', 'row') else ('measure', 'nominal')
        return ('measure', 'quantitative')

    def decl(self, name):
        dt = self.dtype(name)
        role, typ = self.role(name)
        fmt = self.meta[name]['fmt']
        fa = f" default-format='{xesc(fmt)}'" if fmt else ''
        body = f"<calculation class='tableau' formula='{esc(self.compiled(name))}'"
        if self.level(name) == 'tc':
            od = self.meta[name].get('order')
            if od:
                body += (">\n  <table-calc ordering-type='Field'>\n" + ''.join(
                    f"    <order field='[{self.ds}].[{self.cid.get(o, o)}]' />\n" for o in od) + "  </table-calc>\n</calculation>")
            else:
                body += ">\n  <table-calc ordering-type='Rows' />\n</calculation>"
        else:
            body += ' />'
        al = self.alias_xml(name)
        return (f"<column caption='{xesc(name)}' datatype='{dt}'{fa} name='[{self.cid[name]}]' role='{role}' type='{typ}'>\n"
                + indent(body, 2) + ('\n' + indent(al, 2) if al else '') + "\n</column>")

    def alias_xml(self, name):
        if name not in self.aliases:
            return ''
        return ("<aliases>\n" + '\n'.join(f"  <alias key='&quot;{xesc(k)}&quot;' value='{xesc(v)}' />"
                                          for k, v in self.aliases[name]) + "\n</aliases>")

    def raw_decl(self, n):
        t = self.raw[n]
        role, typ = self.raw_role.get(n, (None, None))
        if not role:
            role, typ = ('measure', 'quantitative') if t in ('integer', 'real') else ('dimension', 'nominal')
        extra = " semantic-role='[Country].[ISO3166_2]'" if n == 'country_name' else ''
        al = self.alias_xml(n)
        if al:
            return (f"<column datatype='{t}' name='[{n}]' role='{role}'{extra} type='{typ}'>\n" + indent(al, 2) + "\n</column>")
        return f"<column datatype='{t}' name='[{n}]' role='{role}'{extra} type='{typ}' />"

    def param_decl(self, p):
        d = self.params[p]
        dt, v = d['dtype'], d['value']
        typ = 'quantitative' if dt in ('integer', 'real') else 'nominal'
        vv = {'string': f'&quot;{v}&quot;', 'boolean': str(v).lower(), 'integer': str(v), 'real': str(v)}[dt]
        mem = d.get('members')
        dom = 'list' if mem else 'any'
        out = (f"<column caption='{p}' datatype='{dt}' name='[{self.pid[p]}]' param-domain-type='{dom}' role='measure' "
               f"type='{typ}' value='{vv}'>\n  <calculation class='tableau' formula='{vv}' />")
        if mem:
            out += "\n  <members>\n" + '\n'.join(f"    <member value='{m}' />" for m in mem) + "\n  </members>"
        return out + "\n</column>"

    def closure(self, names):
        calcs, params, raws, todo = set(), set(), set(), list(names)
        while todo:
            t = todo.pop()
            if t in self.calcs:
                if t in calcs:
                    continue
                calcs.add(t)
                todo.extend(self.refs(self.calcs[t]))
            elif t in self.params:
                params.add(t)
            elif t in self.raw:
                raws.add(t)
        return calcs, params, raws

    # ---------- field instances ----------
    def inst(self, name, how='auto'):
        """returns (instance name, mode)"""
        if how == 'auto':
            if name in self.calcs:
                lv, dt = self.level(name), self.dtype(name)
                if lv == 'tc':
                    how = 'tc'
                elif lv == 'agg':
                    how = 'agg'
                elif dt in ('string', 'boolean') or self.role(name)[0] == 'dimension':
                    how = 'dim'
                else:
                    how = 'min'
            else:
                how = 'dim' if self.raw[name] in ('string', 'boolean') else 'min'
        c = self.cid.get(name, name)
        if how == 'dim':
            return f'[none:{c}:nk]', how
        if how == 'ord':
            return f'[none:{c}:ok]', how
        if how == 'cont':
            return f'[none:{c}:qk]', how
        if how == 'min':
            return f'[min:{c}:qk]', how
        if how == 'sum':
            return f'[sum:{c}:qk]', how
        if how == 'attr':
            q = 'qk' if (self.dtype(name) if name in self.calcs else self.raw[name]) in ('integer', 'real') else 'nk'
            return f'[attr:{c}:{q}]', how
        if how == 'agg':
            q = 'qk' if self.dtype(name) in ('integer', 'real') else 'nk'
            return f'[usr:{c}:{q}]', how
        if how == 'tc':
            q = 'qk' if self.dtype(name) in ('integer', 'real') else 'nk'
            return f'[usr:{c}:{q}:1]', how
        raise ValueError(how)

    def ref(self, name, how='auto'):
        return f'[{self.ds}].' + self.inst(name, how)[0]

    def inst_decl(self, name, how='auto', order=None):
        i, how = self.inst(name, how)
        c = self.cid.get(name, name)
        if how in ('dim', 'ord', 'cont'):
            typ = {'dim': 'nominal', 'ord': 'ordinal', 'cont': 'quantitative'}[how]
            return f"<column-instance column='[{c}]' derivation='None' name='{i}' pivot='key' type='{typ}' />"
        if how == 'min':
            return f"<column-instance column='[{c}]' derivation='Min' name='{i}' pivot='key' type='quantitative' />"
        if how == 'sum':
            return f"<column-instance column='[{c}]' derivation='Sum' name='{i}' pivot='key' type='quantitative' />"
        if how == 'attr':
            typ = 'quantitative' if ':qk' in i else 'nominal'
            return f"<column-instance column='[{c}]' derivation='Attribute' name='{i}' pivot='key' type='{typ}' />"
        typ = 'quantitative' if ':qk' in i else 'nominal'
        if how == 'agg':
            return f"<column-instance column='[{c}]' derivation='User' name='{i}' pivot='key' type='{typ}' />"
        od = ''.join(f"\n    <order field='[{self.ds}].[{self.cid.get(o, o)}]' />" for o in (order or []))
        return (f"<column-instance column='[{c}]' derivation='User' name='{i}' pivot='key' type='{typ}'>\n"
                f"  <table-calc ordering-type='Field'>{od}\n  </table-calc>\n</column-instance>")


FONT = {'book': 'Tableau Book', 'bold': 'Tableau Bold', 'semi': 'Tableau Semibold', 'medium': 'Tableau Medium'}


class Sheet:
    """One worksheet. Fields are named plainly; text runs use {Field} placeholders."""

    def __init__(self, model, name):
        self.m, self.name = model, name
        self.used = {}             # inst -> (name, how, order)
        self.filters, self.slices = [], []
        self.panes = []
        self.rows = self.cols = ''
        self.styles = []           # extra table style rules (xml)
        self.tooltip_off = True
        self.deselect = False
        self.hide_labels = []      # header fields to hide
        self.refline_styles = []
        self.axis_rules = []
        self.extra_names = []
        self.cell_size = None
        self.refband_styles = []
        self.grid_rows = None      # colour of the row grid lines (None: off)
        self.zeroline = None       # colour of the zero line (None: off)
        self.row_dividers = None   # colour of the lines between rows (None: off)

    def f(self, name, how='auto', order=None):
        i, h = self.m.inst(name, how)
        if i not in self.used:
            self.used[i] = (name, h, order)
        return f'[{self.m.ds}].{i}'

    def text(self, s, order=None):
        """replace {Field} or {Field|how} with <ref>"""
        def sub(mm):
            nm, _, how = mm.group(1).partition('|')
            return '<' + self.f(nm, how or 'auto', order) + '>'
        return re.sub(r'\{([^{}]+)\}', sub, s)

    def formatted(self, lines, order=None, tag='customized-label'):
        """lines: list of lines; each line is a list of (text, font, size, colour)"""
        runs = []
        for k, line in enumerate(lines):
            if k:
                runs.append("<run>Æ&#10;</run>")
            for t, font, size, col in line:
                tt = self.text(t, order)
                fc = f"fontcolor='{col}' " if col else ''
                runs.append(f"<run {fc}fontname='{FONT[font]}' fontsize='{size}'><![CDATA[{tt}]]></run>")
        extra = " show-buttons='false'" if tag == 'customized-tooltip' else ''
        return f"<{tag}{extra}>\n  <formatted-text>\n" + indent('\n'.join(runs), 4) + f"\n  </formatted-text>\n</{tag}>"

    def filter_member(self, name, member, how='auto', order=None):
        r = self.f(name, how, order)
        i = r.split('].', 1)[1]
        mem = member if member in ('true', 'false') else f'&quot;{member}&quot;'
        self.filters.append(f"<filter class='categorical' column='{r}'>\n  <groupfilter function='member' level='{i}' "
                            f"member='{mem}' user:ui-domain='database' user:ui-enumeration='inclusive' user:ui-marker='enumerate' />\n</filter>")
        self.slices.append(r)

    def pane(self, mark, enc=(), label=None, tooltip=None, size=None, transparency=None, labels_show=None,
             align='left', valign='center', pane_id=None, y_axis=None, x_axis=None, refs=(), extra_mark_fmt='', order=None,
             color=None, stroke=None, cell_fmt=''):
        encs, have = [], set()
        for tag, name, *how in enc:
            hw = how[0] if how else 'auto'
            r = self.f(name, hw, order)
            encs.append(f"<{tag} column='{r}' />"); have.add(r)
        lab = self.formatted(label, order) if label else ''
        if tooltip:
            tip = self.formatted(tooltip, order, 'customized-tooltip')
            self.tooltip_off = False
        else:
            tip = "<customized-tooltip show-buttons='false'>\n  <formatted-text />\n</customized-tooltip>"
        pat = re.compile(r'<(\[' + re.escape(self.m.ds) + r'\]\.\[[^\]]+\])>')
        texts = {e.split("column='")[1][:-4] for e in encs if e.startswith('<text ')}
        for r in dict.fromkeys(pat.findall(lab)):
            if r not in texts:
                encs.append(f"<text column='{r}' />"); texts.add(r); have.add(r)
        for r in dict.fromkeys(pat.findall(tip if tooltip else '')):
            if r not in have:
                encs.append(f"<tooltip column='{r}' />"); have.add(r)
        ls = labels_show if labels_show is not None else bool(label)
        fm = [f"<format attr='mark-labels-show' value='{'true' if ls else 'false'}' />",
              "<format attr='mark-labels-cull' value='false' />"]
        if size is not None:
            fm.append(f"<format attr='size' value='{size}' />")
        if transparency is not None:
            fm.append(f"<format attr='mark-transparency' value='{transparency}' />")
        if color:
            fm.append(f"<format attr='mark-color' value='{color}' />")
        if stroke is not None:
            fm.append(f"<format attr='has-stroke' value='{stroke}' />")
        if extra_mark_fmt:
            fm.append(extra_mark_fmt)
        attrs = (f" id='{pane_id}'" if pane_id is not None else '') + " selection-relaxation-option='selection-relaxation-disallow'" \
            + (f" y-axis-name='{y_axis}'" if y_axis else '') + (f" x-axis-name='{x_axis}'" if x_axis else '')
        sizing = "\n  <mark-sizing mark-sizing-setting='marks-scaling-off' />" if mark in ('Square', 'Shape', 'Circle', 'GanttBar') else ''
        rl = '\n'.join(refs)
        p = (f"<pane{attrs}>\n  <view>\n    <breakdown value='auto' />\n  </view>\n  <mark class='{mark}' />{sizing}\n"
             "  <encodings>\n" + indent('\n'.join(encs), 4) + "\n  </encodings>\n"
             + (indent(rl, 2) + '\n' if rl else '') + indent(tip, 2) + '\n' + (indent(lab, 2) + '\n' if lab else '')
             + "  <style>\n    <style-rule element='cell'>\n"
             + (f"      <format attr='text-align' value='{align}' />\n" if align else '')
             + f"      <format attr='vertical-align' value='{valign}' />\n"
             + (f"      {cell_fmt}\n" if cell_fmt else '') +
             "    </style-rule>\n    <style-rule element='mark'>\n" + indent('\n'.join(fm), 6) + "\n    </style-rule>\n  </style>\n</pane>")
        self.panes.append(re.sub(r'\n\s*\n', '\n', p))

    def refline(self, idx, axis_ref, value_ref, colour, width=1, pattern='solid', label=None, scope='per-pane'):
        lab = f" label='{xesc(label)}' label-type='custom'" if label else " label-type='none'"
        x = (f"<reference-line axis-column='{axis_ref}' enable-instant-analytics='false' formula='max' id='refline{idx}'{lab} "
             f"scope='{scope}' tooltip-type='none' value-column='{value_ref}' z-order='{idx + 1}' />")
        self.refline_styles += [f"<format attr='fill-above' id='refline{idx}' value='#00000000' />",
                                f"<format attr='fill-below' id='refline{idx}' value='#00000000' />",
                                f"<format attr='stroke-size' id='refline{idx}' value='{width}' />",
                                f"<format attr='stroke-color' id='refline{idx}' value='{colour}' />",
                                f"<format attr='line-pattern-only' id='refline{idx}' value='{pattern}' />",
                                f"<format attr='line-visibility' id='refline{idx}' value='on' />"]
        return x

    def _cell_fmt(self):
        if not self.cell_size:
            return ''
        w, h, fld = (list(self.cell_size) + [None])[:3]
        fa = f" field='{fld}'" if fld else ''
        return ((f"  <format attr='width' value='{w}' />\n" if w else '') +
                (f"  <format attr='height'{fa} value='{h}' />\n" if h else ''))

    def refband(self, idx, axis_ref, lo, hi, fill, scope='per-pane'):
        """two paired reference lines; lo / hi are numbers (constants) or field refs"""
        out = []
        for k, (v, pair) in enumerate(((lo, idx + 1), (hi, idx))):
            i = idx + k
            if isinstance(v, (int, float)):
                val = f"formula='constant' id='refline{i}' label-type='none' paired-id='refline{pair}' scope='{scope}' symmetric='false' value='{float(v)}' value-column='{axis_ref}'"
            else:
                val = f"formula='max' id='refline{i}' label-type='none' paired-id='refline{pair}' scope='{scope}' symmetric='false' value-column='{v}'"
            out.append(f"<reference-line axis-column='{axis_ref}' enable-instant-analytics='false' {val} tooltip-type='none' z-order='{i + 1}' />")
        self.refband_styles.append(f"<format attr='fill-color' id='refline{idx}' value='{fill}' />")
        return out

    def xml(self):
        m = self.m
        names = [v[0] for v in self.used.values()] + self.extra_names
        calcs, params, raws = m.closure(names)
        dep_p = ''
        if params:
            dep_p = ("<datasource-dependencies datasource='Parameters'>\n" +
                     indent('\n'.join(m.param_decl(p) for p in m.params if p in params), 2) + "\n</datasource-dependencies>\n")
        decls = [m.decl(c) for c in m.order if c in calcs] + [m.raw_decl(r) for r in sorted(raws)]
        insts = [m.inst_decl(n, h, o) for n, h, o in self.used.values()]
        flt = list(self.filters)
        slices = list(self.slices)
        if self.deselect:
            flt.append(f"<filter class='categorical' column='[{m.ds}].[Action (zzFalse)]'>\n  <groupfilter function='level-members' "
                       f"level='[{m.cid['zzFalse']}]' user:ui-action-filter='{self.deselect}' "
                       f"user:ui-enumeration='all' user:ui-marker='enumerate' />\n</filter>")
            slices.append(f'[{m.ds}].[Action (zzFalse)]')
        sl = ("<slices>\n" + '\n'.join(f'  <column>{s}</column>' for s in dict.fromkeys(slices)) + "\n</slices>") if slices else ''
        view = (f"<view>\n  <datasources>\n    <datasource caption='{xesc(m.caption)}' name='{m.ds}' />\n"
                + ("    <datasource name='Parameters' />\n" if params else '') + "  </datasources>\n"
                + indent(dep_p, 2) + '\n'
                + f"  <datasource-dependencies datasource='{m.ds}'>\n" + indent('\n'.join(decls + insts), 4)
                + "\n  </datasource-dependencies>\n" + indent('\n'.join(flt), 2) + '\n'
                + indent(sl, 2) + "\n  <aggregation value='true' />\n</view>")
        view = re.sub(r'\n\s*\n', '\n', view)
        rules = []
        if self.axis_rules:
            rules.append("<style-rule element='axis'>\n" + indent('\n'.join(self.axis_rules), 2) + "\n</style-rule>")
        if self.hide_labels:
            rules.append("<style-rule element='label'>\n" + '\n'.join(
                f"  <format attr='display' field='{r}' value='false' />" for r in self.hide_labels) + "\n</style-rule>")
        rules += self.styles
        rules += [
            "<style-rule element='table'>\n  <format attr='background-color' value='#00000000' />\n"
            "  <format attr='show-null-value-warning' value='false' />\n</style-rule>",
            "<style-rule element='cell'>\n" + self._cell_fmt() + "  <format attr='border-width' value='0' />\n  <format attr='border-style' value='none' />\n</style-rule>",
            "<style-rule element='header'>\n  <format attr='band-color' scope='rows' value='#00000000' />\n"
            "  <format attr='border-width' value='0' />\n  <format attr='border-style' value='none' />\n</style-rule>",
            "<style-rule element='pane'>\n  <format attr='band-color' scope='rows' value='#00000000' />\n"
            "  <format attr='border-width' value='0' />\n  <format attr='border-style' value='none' />\n</style-rule>",
            ("<style-rule element='gridline'>\n  <format attr='line-visibility' value='off' />\n"
             "  <format attr='line-visibility' scope='rows' value='off' />\n  <format attr='line-visibility' scope='cols' value='off' />\n</style-rule>"
             if not self.grid_rows else
             "<style-rule element='gridline'>\n  <format attr='line-visibility' scope='cols' value='off' />\n"
             f"  <format attr='stroke-size' scope='rows' value='1' />\n  <format attr='line-visibility' scope='rows' value='on' />\n"
             f"  <format attr='stroke-color' scope='rows' value='{self.grid_rows}' />\n  <format attr='line-pattern-only' scope='rows' value='solid' />\n</style-rule>"),
            ("<style-rule element='zeroline'>\n  <format attr='stroke-size' value='0' />\n  <format attr='line-visibility' value='off' />\n</style-rule>"
             if not self.zeroline else
             f"<style-rule element='zeroline'>\n  <format attr='stroke-size' value='1' />\n  <format attr='line-visibility' value='on' />\n"
             f"  <format attr='stroke-color' value='{self.zeroline}' />\n</style-rule>"),
            "<style-rule element='dropline'>\n  <format attr='stroke-size' value='0' />\n  <format attr='line-visibility' value='off' />\n</style-rule>",
            ("<style-rule element='table-div'>\n  <format attr='stroke-size' scope='rows' value='0' />\n  <format attr='line-visibility' scope='rows' value='off' />\n"
             "  <format attr='stroke-size' scope='cols' value='0' />\n  <format attr='line-visibility' scope='cols' value='off' />\n</style-rule>"
             if not self.row_dividers else
             "<style-rule element='table-div'>\n  <format attr='stroke-size' scope='rows' value='1' />\n  <format attr='line-visibility' scope='rows' value='on' />\n"
             f"  <format attr='stroke-color' scope='rows' value='{self.row_dividers}' />\n  <format attr='div-level' scope='rows' value='1' />\n"
             "  <format attr='stroke-size' scope='cols' value='0' />\n  <format attr='line-visibility' scope='cols' value='off' />\n</style-rule>"),
            "<style-rule element='header-div'>\n  <format attr='stroke-size' scope='rows' value='0' />\n  <format attr='line-visibility' scope='rows' value='off' />\n"
            "  <format attr='stroke-size' scope='cols' value='0' />\n  <format attr='line-visibility' scope='cols' value='off' />\n</style-rule>",
        ]
        rules.append("<style-rule element='refline'>\n" + indent('\n'.join(self.refline_styles), 2) + "\n</style-rule>"
                     if self.refline_styles else
                     "<style-rule element='refline'>\n  <format attr='stroke-size' value='0' />\n  <format attr='line-visibility' value='off' />\n</style-rule>")
        if self.refband_styles:
            rules.append("<style-rule element='refband'>\n" + indent('\n'.join(self.refband_styles), 2) + "\n</style-rule>")
        style = "<style>\n" + indent('\n'.join(rules), 2) + "\n</style>"
        rows = f'<rows>{self.rows}</rows>' if self.rows else '<rows />'
        cols = f'<cols>{self.cols}</cols>' if self.cols else '<cols />'
        tt = "<tooltip-style tooltip-mode='none' />\n" if self.tooltip_off else ''
        return (f"<worksheet name='{xesc(self.name)}'>\n  <table>\n" + indent(view, 4) + "\n" + indent(style, 4)
                + "\n    <panes>\n" + indent('\n'.join(self.panes), 6) + f"\n    </panes>\n    {rows}\n    {cols}\n"
                + indent(tt, 4) + f"  </table>\n  <simple-id uuid='{uid()}' />\n</worksheet>")

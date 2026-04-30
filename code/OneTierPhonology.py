from functools import reduce
from collections.abc import MutableMapping
import Featurizer #only for Transcriber.from_featurizer function

class Segment(dict):
    """A segment is defined as a partial function from features to +/-"""
    _minus = '-–—'
    _plus = '+123456789'
    def __str__(self):
        return '[' + ', '.join([('+' if self[x] else '-') + x for x in sorted(self.keys())]) + ']'
    def __repr__(self):
        return 'Segment:' + str(self)
    def __init__(self, text = ""):
        super().__init__()
        if text is not None:
            text = str(text).replace('syll','syllabic').replace('syllabicabic','syllabic')
            text = [x.strip() for x in text.replace('[','').replace(']','').strip().split(',') if x.strip() != '']
            text = [x for x in text if x[0] in Segment._plus + Segment._minus]
            for x in text:
                if x.lower() == 'segmental':
                    raise KeyError("Segments cannot be valued for [segmental].")
                self[x[1:]] = x[0] in Segment._plus
    def feature_value(self, feat: str):
        if str(feat) in self:
            return '+' if self[feat] else '-'
        return '0'
    def is_boundary(self):
        return 'WB' in self
    def is_structural(self):
        return len(self) == 0
    def is_phonological(self):
        return len(self) > 0 and not is_boundary(self)
    def is_syllabic(self):
        return self.get('syllabic', False)
    def correct_to(self, desc: SegmentDescription):
        if len(desc) == 0:
            return None
        ans = Segment(str(self))
        for f in desc:
            if f.lower() == 'segmental':
                if desc[f] == '0':
                    return Segment(None)
                if 'WB' in desc: #[segmental] value is vacuous or self-contradictory
                    continue
                if desc[f] in Segment._minus:
                    if 'syllabic' in ans:
                        minussyll = True
                    ans = Segment(None)
                    ans['WB'], ans['syllabic'] = True, minussyll
                    return ans
                if 'WB' in ans: #only fires if none of the previous did
                    del ans['WB']
            if desc[f] in Segment._plus:
                ans[f] = True
            elif desc[f] in Segment._minus:
                ans[f] = False
            elif desc[f] == '0':
                if f in ans:
                    del ans[f]
            else: #Should never fire
                currvar = desc[f][-1]
                print("Assigning + to variable {0} as default.".format(currvar))
                return self.correct_to(desc.value_variable(currvar, True))
        return ans
                

class SegmentDescription(dict):
    """A segment description allows for 0 and variables as values and "segmental" as key, unlike segment"""
    _greek = 'αβγδεϛϝζηθικλμνξοπϙϟρσςτυφχψω'
    def __init__(self, text = ""):
        if (text == 'Ø') or (text is None):
            super().__init__()
        else:
            text = str(text).replace('syll','syllabic').replace('syllabicabic','syllabic').replace('[','').replace(']','').strip()
            text = dict() if len(text) == 0 else [(x[2:], '-'+x[1])
                if (len(x) > 2) and (x[0] in Segment._minus) and (x[1].lower() in SegmentDescription._greek)
                else (x[1:], '-' if x[0] in Segment._minus else x[0]) for x in [y.strip() for y in text.split(',')]]
            super().__init__(text)
    def __str__(self):
        if len(self) == 0:
            return 'Ø'
        return '[' + ', '.join([str(self[x]) + x for x in sorted(self.keys())]) + ']'
    def vars_used(self):
        return {x[-1] for x in self.values() if x[-1] not in Segment._plus + Segment._minus + '0'}
    def value_variable(self, variable: str, value: bool):
        ans = SegmentDescription(str(self))
        if str(variable).strip() in Segment._plus + Segment._minus + '0':
            return ans
        for x in ans:
            if ans[x][-1] == str(variable).strip():
                ans[x] = '+' if (value if len(x) == 1 else -value) else '-'
        return ans
    def match(self, segm: Segment):
        if len(self) == 0:
            return False
        if len(self.vars_used()) > 0: #Consistency of vars, shouldn't fire in rule application
            first_var = tuple(self.vars_used())[0]
            print('Matching variable {0} of unknown value.'.format(first_var))
            return (self.value_variable(first_var, True).match(segm)
                or self.value_variable(first_var, False).match(segm))
        for f in self:
            if f.lower() == 'segmental':
                if self[f] in Segment._plus:
                    if not segm.is_phonological():
                        return False
                elif self[f] in Segment._minus:
                    if not segm.is_boundary():
                        return False
                elif self[f] == '0':
                    if not segm.is_structural():
                        return False
                elif segm.is_structural(): #should never fire
                    return False
            elif self[f] == '0':
                if f in segm:
                    return False
            elif f not in segm:
                return False
            elif self[f] in Segment._plus:
                if not segm[f]:
                    return False
            elif self[f] in Segment._minus:
                if segm[f]:
                    return False
        return True


class Context(list):
    """String of segment descriptions, with possible asterisks and parentheses."""
    def __init__(self, text = ""):
        if isinstance(text, list):
            super().__init__(text)
        elif text is None:
            super().__init__()
        else:
            super().__init__()
            text = str(text).replace('(', ' ( ').replace(')', ' ) ').replace('][', '] [').replace('*', ' * ').replace(', ',',')
            self.extend(' '.join(text.split()).replace('* *','*').split())
            for i in range(len(self)):
                if self[i] not in ('(',')','*'):
                    self[i] = SegmentDescription(self[i])
    def __str__(self):
        return ' '.join([str(x) for x in self])
    def vars_used(self):
        return reduce(lambda x, y: x.union(y.vars_used()),
                      [x for x in self if isinstance(x, SegmentDescription)], set())
    def value_variable(self, variable: str, value: bool):
        ans = Context(self[:])
        for i in range(len(ans)):
            if isinstance(ans[i], SegmentDescription):
                ans[i] = ans[i].value_variable(str(variable), bool(value))
        return ans
    def match(self, string: list):
        variables = tuple(self.vars_used())
        if len(variables) > 0:
            first_var = variables[0]
            return (self.value_variable(first_var, True).match(string)
                or self.value_variable(first_var, False).match(string))            
        _asterisk_depth = 5
        if '(' in self:
            start, depth = self.index('(') + 1, 1
            if self[start] == ')': #Should never fire because () disallowed
                return Context(self[:start-1] + [SegmentDescription()] + self[start+1:]).match(string)
            for i in range(start + 1, len(self)):
                if self[i] == '(':
                    depth += 1
                elif self[i] == ')':
                    depth -= 1
                    if depth == 0:
                        stop = i + 1
                        break
            intContext = Context(self[start:stop - 1])
            start -= 1
            if stop == len(self):
                return Context(self[:start] + intContext).match(string) or Context(self[:start]).match(string)
            elif self[stop] == '*':
                ans = False
                for j in range(_asterisk_depth):
                    ans = ans or Context(self[:start] + intContext * j + self[stop + 1:]).match(string)
                    if ans:
                        break
                return ans
            else:
                return (Context(self[:start] + intContext + self[stop:]).match(string)
                        or Context(self[:start] + self[stop:]).match(string))
        else:
            for i in range(len(self)):
                if len(self[i]) == 0:
                    if i + 1 == len(self):
                        return Context(self[:-1]).match(string)
                    elif self[i+1] == '*':
                        return Context(self[:i] + self[i+2:]).match(string)
                    else:
                        return Context(self[:i] + self[i+1:]).match(string)
                elif self[i] == '*':
                    ans = False
                    for j in range(_asterisk_depth):
                        ans = ans or Context(self[:i-1] + self[i-1:i] * j + self[i+1:]).match(string)
                        if ans:
                            break
                    return ans
            if len(self) != len(string):
                return False
            for i in range(len(self)):
                if not self[i].match(string[i]):
                    return False
            return True
    def mirror(self):
        total_len = len(self)
        bracket_num = 0
        stack = []
        for i in range(total_len):
            if self[i] == '(':
                self[i] = ('(', bracket_num)
                stack.append(bracket_num)
                bracket_num += 1
            elif self[i] == ')':
                self[i] = (')', stack.pop())
        ans = Context(self[::-1])
        stack.clear()
        for i in range(total_len - 1):
            if ans[i] == '*':
                if isinstance(ans[i+1], tuple):
                    ans[i], ans[i+1] = (')*', ans[i+1][1]), ''
                    stack.append(ans[i][1])
                else:
                    ans[i], ans[i+1] = ans[i+1], ans[i]
        for i in range(total_len):
            if isinstance(self[i], tuple):
                self[i] = self[i][0] #Fixing the original
            if isinstance(ans[i], tuple):
                if ans[i][1] in stack:
                    if ans[i][0] == ')*':
                        ans[i] = '('
                    else:
                        ans[i] = ')'
                        ans.insert(i+1, '*')
                        ans.remove('') #The check of the * will be skipped but that's alright
                else:
                    ans[i] = '(' if ans[i][0] == ')' else ')'
        return ans
    def plus(self):
        ans = Context(self[:])
        for i in range(1, len(ans)):
            if ans[i] == '*':
                if ans[i-1] != ')':
                    ans[i], ans[i-1] = ')*', '(' + str(ans[i-1])
        return Context(str(ans).replace('] ', '] [-WB,0syllabic]* '))

class Rule:
    """Single-tier phonological rule, supports mirror rules, repeating rules, and metatheses."""
    target: SegmentDescription
    result: SegmentDescription
    left: Context
    right: Context
    met: bool
    mir: bool
    rep: bool
    _rep_marker = ' (repeating)'
    _rightward_arrow = '→'
    def __init__(self, target, result, left, right, metathesis = False, mirror = False, repeating = False):
        self.target, self.result = SegmentDescription(target), SegmentDescription(result)
        self.left, self.right = Context(left), Context(right)
        self.met, self.mir, self.rep = map(bool, (metathesis, mirror, repeating))
        if len(self.target) + int(not self.met) == 0:
            raise ValueError("Insertion rules cannot be metathesis rules.")
            self.met = False
        elif len(self.result) + int(not self.met) == 0:
            raise ValueError("Deletion rules cannot be metathesis rules.")
            self.met = False
    def __str__(self):
        has_context = len(self.left) + len(self.right) > 0
        divisor = '%' if self.mir else ('/' if has_context else '')
        ans = ('{0}{1} → {1}{0}' if self.met else '{0} → {1}').format(str(self.target), str(self.result))
        ans += ' {0} {1}{2}{3}'.format(divisor, str(self.left), '_' if has_context else '', str(self.right)).rstrip()
        if self.rep:
            ans += Rule._rep_marker
        return ans
    def __repr__(self):
        return str(self)
    def parse(s: str):
        target, rest = map(str.strip, str(s).split(Rule._rightward_arrow))
        rep = rest[-len(Rule._rep_marker):] == Rule._rep_marker
        if rep:
            rest = rest[:-len(Rule._rep_marker)]
        target = target.replace(' ','')
        metathesis, mirror, rest = '][' in target, '%' in rest, rest.replace('%','/')
        if '/' not in rest:
            rest = rest + '/'
        rest = rest.split('/')
        if metathesis:
            target, result = target.replace('][', ']] [[').split('] [')
        else:
            result = rest[0].replace(' ','')
        rest = rest[1]
        if '_' not in rest:
            left, right = '', ''
        else:
            left, right = map(str.strip, rest.split('_'))
        return Rule(target, result, left, right, metathesis, mirror, rep)
    def targetstring(self):
        if self.met:
            return Context(self.left + [self.target, self.result] + self.right).plus()
        return Context(self.left + [self.target] + self.right).plus()
    def vars_used(self):
        return self.targetstring().vars_used().union(self.result.vars_used())
    def applyonce(self, segmstr: list):
        #ignores mirroring, repeating and wider context, that is in the wrapper
        variables = tuple(self.vars_used())
        if len(variables) > 0:
            value_var_plus = lambda x: x.value_variable(variables[0], True)
            rule_plus = Rule(*map(value_var_plus, (self.target, self.result, self.left, self.right)))
            rule_plus.met = self.met            
            apply_plus = rule_plus.applyonce(segmstr)            
            if apply_plus != segmstr:
                return apply_plus
            value_var_minus = lambda x: x.value_variable(variables[0], False)
            rule_minus = Rule(*map(value_var_minus, (self.target, self.result, self.left, self.right)))
            rule_minus.met = self.met
            return rule_minus.applyonce(segmstr)
        ans = segmstr[:]
        if self.targetstring().match(ans):
            curr = -1
            for i in range(len(ans)):
                if self.left.plus().match(ans[:i]):
                    curr = i
                    break
            if self.met:
                if len(self.target) == 0:
                    raise ValueError("Insertion rules cannot be metathesis rules.")
                if len(self.result) == 0:
                    raise ValueError("Deletion rules cannot be metathesis rules.")
                for currcurr in range(curr+1, len(ans)):
                    if self.result.match(ans[currcurr]):
                        ans = ans[:curr] + ans[currcurr] + ans[curr+1:currcurr] + ans[curr] + ans[currcurr+1:]
                        break
            else:
                if len(self.target) > 0:
                    while not self.target.match(ans[curr]): # e.g. for pluses before targets
                        curr += 1
                        if curr == len(ans):
                            break
                    result_insert = [] if len(self.result) == 0 else [ans[curr].correct_to(self.result)]
                else:
                    result_insert = [] if len(self.result) == 0 else [Segment('').correct_to(self.result)]
                ans = ans[:curr] + result_insert + ans[curr if (len(self.target) == 0) else curr+1:]
        return ans
    def apply(self, segmstr: list):
        repeat = True
        ans = segmstr[:]
        while repeat:
            for i in range(len(segmstr)):
                for j in range(i+1, len(ans)+1):
                    curr = ans[i:j]
                    targetstr = self.targetstring()
                    if targetstr.match(curr):
                        ans = ans[:i] + self.applyonce(curr) + ans[j:]
                    elif self.mir:
                        if targetstr.mirror().match(curr):
                            ans = ans[:i] + Rule(self.target, self.result, self.right.mirror(), self.left.mirror(), self.met, False).applyonce(curr) + ans[j:]
            repeat = self.rep and (ans != segmstr)
            segmstr = ans[:]
        return segmstr

class Transcriber(MutableMapping):
    """Transcribing from segments/descriptions to their names and back."""
    __segment_dict = dict()
    def __init__(self, dictionary = None):
        self.__segment_dict = dict() if dictionary is None else dict(dictionary)
        cleanup_items = tuple(self.__segment_dict.items())
        for key, value in cleanup_items:
            self.set(key, value)
    def __iter__(self):
        return self.__segment_dict.__iter__()
    def __str__(self):
        return '\n'.join(sorted([': \t'.join((x, self.__segment_dict[x])) for x in self.__segment_dict]))
    def set(self, s: str, segm: Segment):
        self.__segment_dict = {x: self.__segment_dict[x] for x in self.__segment_dict
                               if self.__segment_dict[x] != str(segm)}
        self.__segment_dict[str(s)] = str(segm)
    def __setitem__(self, s, val):
        self.set(s, val)
    def __len__(self):
        return len(self.__segment_dict)
    def __getitem__(self, s):
        return self.__segment_dict[str(s)]
    def items(self):
        return self.__segment_dict.items()
    def __contains__(self, item):
        if isinstance(item, dict):
            return str(item) in self.__segment_dict.values()
        return str(item) in self.__segment_dict
    def remove(self, item):
        if isinstance(item, dict):
            self.__segment_dict = {k: v for k, v in self.__segment_dict.items() if v != str(item)}
        else:
            self.__segment_dict = {k: self.__segment_dict[k] for k in self.__segment_dict if k != str(item)}
    def __delitem__(self, item):
        self.remove(item)
    def clear(self):
        self.__segment_dict.clear()
    def text_to_segment(self, s: str, sep = ' '):
        sep = ' ' if (sep is None) or (sep == '') else str(sep)[0]
        ans, depth, s = "", 0, [str(x) for x in s if str(x) != sep]
        for symbol in s:
            if symbol == '[':
                depth += 1
            elif symbol == ']':
                depth -= 1
                ans += ']' + sep
                continue
            elif depth == 0:
                ans += str(self.__segment_dict.get(symbol, symbol)).replace(sep,'')
                ans += sep
                continue
            ans += symbol
        return [Segment(x) if '[' in x else x for x in ans.strip().split(sep) if x != '']
    def segment_to_text(self, l: list, sep = ' '):
        ans = []
        for x in l:
            if str(x) in self.__segment_dict.values():
                ans.append([k for k, v in self.__segment_dict.items() if v == str(x)][0])
            else:
                ans.append(str(x))
        return sep.join(ans)
    def segments_from_features(d: dict):
        ans = dict()
        for feature in d:
            for x in d[feature]:
                if x in ans:
                    ans[x].append(feature)
                else:
                    ans[x] = [feature]
        return Transcriber({x: Segment(", ".join(ans[x])) for x in ans})
    def from_featurizer(classes, class_names, verbose=False):
        alphabet = reduce(set.union, classes, set())
        f = Featurizer.Featurizer(classes, set(alphabet), Featurizer.Specification.INFERENTIAL_COMPLEMENTARY, verbose=verbose)
        f.get_features_from_classes()
        feats = [dict(f.segment_features)] + list(class_names)
        for x in feats[0]:
            feats[0][x] = Segment(','.join([y[1] + feats[y[0]] for y in feats[0][x]]))
        return Transcriber(feats[0])
    def transcribe_and_parse_rule(self, s: str):
        if self is None:
            return Rule.parse(str(s))
        return Rule.parse(' '.join([str(x) for x in tr.text_to_segment(str(s))]))

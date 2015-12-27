#! /usr/local/bin/python3
# loosewire text compiler
# fileTypes: .lwtx
# output: .lwtx.html
# requires:
# python 3+

VERSION = '1.0'

from sys import argv, exit
import re

from contencoder import Contencoder

_stnr = ' \t\n\r'

def strip_comments(line, openflag=False):
    line = line.rstrip(_stnr)

    previous_comment = None
    previous_ended = False

    # match and separate previous comment
    if openflag:
        comment_end_match = exp_comment_end.match(line)
        if comment_end_match:
            previous_comment = comment_end_match.group(1)
            line = line[comment_end_match.span()[1]:]
            previous_ended = True
        else:
            previous_comment = line
            line = ''

    line_comment = None
    ignorechar = False

    # match and separate line comment
    for ch in exp_comment_enter.finditer(line):
        enter_position = ch.span()[0]
        if ignorechar:
            if '*' == line[max(0, enter_position - 1)]:
                ignorechar = False
            
            continue

        try:
            if '*' == line[enter_position + 1]:
                ignorechar = True
        except: 
            pass

        if not ignorechar:
            line_comment = line[enter_position + 1:]
            line = line[:enter_position]
            break

    # match and separate inline comments
    inline_comments = exp_comment_inline.findall(line)
    line = exp_comment_inline.sub(' ', line)

    next_comment = None

    # match and separate next comment
    comment_begin_match = exp_comment_begin.search(line)
    if comment_begin_match:
        next_comment = comment_begin_match.group(1)
        line = line[:comment_begin_match.span()[0]]

    newopenflag = False

    if next_comment != None:
        newopenflag = True

    elif previous_comment != None and not previous_ended:
        newopenflag = True

    endflag = False

    if previous_ended:
        endflag = True

    return line + '\n', newopenflag, {
        'prev': previous_comment,
        'endflag': endflag,
        'next': next_comment,
        'inline': inline_comments,
        'line': line_comment,
    } 

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class ImmutableRegisterError(Exception):
    pass

class EmptyRegisterError(Exception):
    pass

class Pair:
    def __init__(self, key, value):
        self.key = key
        self.value = value

class Register:
    def __init__(self, mutable=True):
        # public
        self.meta = {}
        # private
        self._register = []
        self._last_index = 0
        self._mutable = mutable

    def set(self, key, value):
        pair = self.get(key)
        if pair:
            if self._mutable:
                pair.value = value
            else:
                raise ImmutableRegisterError()

        new_pair = Pair(key, value)
        self._register.append(new_pair)
        return new_pair

    def get(self, key):
        for pair in self._register:
            if pair.key == key:
                return pair
        return None

    def count(self):
        return len(self._register)

    def last(self):
        try:
            return self._register[-1]
        except:
            raise EmptyRegisterError()

    def __iter__(self):
        self._last_index = 0
        return self

    def __next__(self):
        try:
            value = self._register[self._last_index]
            self._last_index += 1
            return value
        except:
            raise StopIteration

class ScreenRegister:
    def __init__(self):
        self.comments = []
        self.screens = Register(False)
        self.name = None
        self.description = None
        self.specialvars = {}

        # self.last_screenid = None
        # self.last_elemid = None
        self.has_unknowns = None
        self.comm_buff = []

    def exit_with(self, msg):
        print(msg + '\n')
        exit()

    def raise_error(self, errstr, line=None):
        linestr = ' line no: ' + str(line) if line else ''
        self.exit_with('Error: ' + bcolors.FAIL + errstr + bcolors.ENDC + \
            linestr)

    def success(self, msg):
        self.exit_with(bcolors.OKGREEN + msg + bcolors.ENDC)

    def register_screen(self, screenid, line_number=None):
        screenid = screenid.strip(_stnr)
        try:
            screen = self.screens.set(screenid, Register(False))
            screen.value.meta['descriptions'] = []
            screen.value.meta['comments'] = []

        except ImmutableRegisterError:
            self.raise_error(
                'duplicate screen definition: ' + screenid,
                line_number
            )

        # self.last_screenid = screenid
        self.end_line()

    def register_element(self, elemid, line_number=None):
        elemid = elemid.strip(_stnr)
        elemtype = None
        if re.match(r'^:', elemid):
            elemtype = 'data'
        elif re.match(r'^\.', elemid):
            elemtype = 'form'
        else:
            elemtype = 'action'

        elem = elemid.split('->')
        elem = [str(x).strip(_stnr) for x in elem]

        try:
            self.screens.last().value.set(elem[0], {
                'elemtype': elemtype,
                'comments': [],
                'mutable': True
            })
        except EmptyRegisterError:
            self.raise_error(
                'no screens defined: ' + elem[0],
                line_number
            )
        except ImmutableRegisterError:
            self.raise_error(
                'duplicate element definition: ' + elem[0],
                line_number
            )

        if len(elem) > 1:
            results = [(x.strip(_stnr), 'obj') for x in elem[1].split('|')]
            real_results = []
            for res, restype in results:
                _result_set = []
                _res = [x.strip(_stnr) for x in res.split('#')]
                _custom = [(x, 'custom') for x in _res[1:] if len(x)]

                if len(_res[0]):
                    _result_set += [(_res[0], restype)]
                _result_set += _custom
                real_results += [_result_set]
            
            self.screens.last().value.last().value['results'] = real_results

        self.end_line()

    def end_line(self):
        if self.comm_buff:
            if not self.screens.count():
                if not self.name:
                    self.name = '\n'.join(self.comm_buff)
                elif not self.description:
                    self.description = '\n'.join(self.comm_buff)
                else:
                    self.comments += self.comm_buff

            elif not self.screens.last().value.count():
                self.screens.last().value.meta['descriptions'] += \
                    self.comm_buff

            elif not self.screens.last().value.last().value['mutable']:
                self.screens.last().value.meta['comments'] += \
                    self.comm_buff

            else:
                self.screens.last().value.last().value['comments'] += \
                    self.comm_buff

            self.comm_buff = []
        try:
            self.screens.last().value.last().value['mutable'] = False
        except:
            pass

    def register_comment(self, comment, multiline=False):
        if type(comment) == tuple:
            comment = list(comment)
        elif type(comment) != list:
            comment = [comment]

        comment = [x.strip() for x in comment]

        # process and remove special vars
        for index, commentpart in enumerate(comment):
            comment[index] = re.sub(
                r'%{((?:(?!}%).)+):((?:(?!}%).)+)}%', 
                self.repl_spl, 
                commentpart
            )

        if multiline:
            # process *s
            _comment = [x.strip(' *') for x in comment]
            _comment = [x for x in _comment if x.strip(_stnr) != '']
            self.comm_buff += ['<br />\n'.join(_comment)]
        else:
            self.comm_buff += comment

    def repl_spl(self, match):
        self.specialvars[match.group(1).strip(_stnr)] = \
            match.group(2).strip(_stnr)
        return ''

    def link_objects(self):
        self.unknowns = []
        for screen in self.screens:
            for elem in screen.value:
                # check partials
                if self.is_partial(elem.key):
                    if self.screens.get(elem.key):
                        pass
                    else:
                        if elem.key not in self.unknowns:
                            self.unknowns.append(elem.key)
                # check results
                if 'results' in elem.value:
                    for result_set in elem.value['results']:
                        for result in result_set:
                            if result[1] == 'custom':
                                pass
                            elif self.screens.get(result[0]):
                                pass
                            else:
                                if result[0] not in self.unknowns:
                                    self.unknowns.append(result[0])

        if len(self.unknowns):
            self.has_unknowns = True

        if self.has_unknowns:
            self.exit_with('Undefined Objects: \n' + bcolors.FAIL + \
                '\n'.join(self.unknowns) + bcolors.ENDC)

    def is_partial(self, key):
        return True if re.search(r'\[.+\]', key) else False

    def render_output(self, filename):
        # mkp = open('index.html', 'r')
        # mkp_str = mkp.read()
        # mkp.close()

        # get self contained template markup
        mkp_str = Contencoder.get_template()

        body = ''

        for screen in self.screens:
            __body = ''
            for elem in screen.value:
                elem_body = ''
                __comments = ''
                for comment in elem.value['comments']:
                    __comments += markup.comment % {'comment': comment}

                if elem.value['elemtype'] == 'data':
                        elem_body += markup.elem_data % {
                            'elemid': elem.key.lstrip(':'),
                            'comments': __comments
                        }
                elif elem.value['elemtype'] == 'form':
                    elem_body += markup.elem_form % {
                        'elemid': elem.key.lstrip('.'),
                        'comments': __comments
                    }
                else:
                    __results = ''
                    if 'results' in elem.value:
                        for result_set in elem.value['results']:
                            for result in result_set:
                                if result[1] == 'obj':
                                    _res0 = result[0]
                                    if self.is_partial(_res0):
                                        _res0 = markup.partial % {'partial': _res0}

                                    _res0 = re.sub(
                                        r'(@[\w\s\t\(\)\+,]+)', 
                                        markup.dyndata % {'dyndata': r'\1'}, 
                                        _res0
                                    )
                                    __results += markup.elem_action_result_objpointer % {
                                        '_result': result[0],
                                        'result': _res0
                                    }
                                else:
                                    __results += markup.elem_action_result_custom % {
                                        'custom': result[0]
                                    }
                            __results += markup.elem_action_result_group_sep

                    _elemid = elem.key
                    if self.is_partial(_elemid):
                        _elemid = markup.partial % {'partial': _elemid}
                    elem_body += markup.elem_action % {
                        'elemid': _elemid,
                        'extras': __results + __comments
                    }

                __body += elem_body 

            __descriptions = ''
            if screen.value.meta['descriptions']:
                __descriptions = '\n'.join([markup.span % {
                    'content': x
                } for x in screen.value.meta['descriptions']])

            if screen.value.meta['comments']:
                __notes = '\n'.join([markup.elem_notes_note % {
                    'note': x
                } for x in screen.value.meta['comments']])
                __body += markup.elem_notes % {
                    'notes': __notes
                }

            _screenid = screen.key
            if self.is_partial(_screenid):
                _screenid = markup.partial % {'partial': _screenid}
            _screenid = re.sub(r'(\*)', markup.keyword % {'keyword': r'\1'}, _screenid)
            _screenid = re.sub(r'(@[\w\s\t\(\)\+,]+)', markup.dyndata % {'dyndata': r'\1'}, _screenid)

            body += markup.obj % {
                '_screenid': screen.key,
                'screenid': _screenid,
                'description': __descriptions,
                'contents': __body
            }

        project_comments = ''
        if self.comments:
            project_comments += '\n'.join([markup.project_comment % {
                'comment': str(x)
            } for x in self.comments])
            project_comments = markup.project_comments % {
                'comments': project_comments
            }

        if 'start_screen' in self.specialvars:
            project_comments += markup.project_comments % {
                'comments': markup.clickable_pointer % {
                    'ref': self.specialvars['start_screen'],
                    'label': self.specialvars['start_screen_label'] \
                        if 'start_screen_label' in self.specialvars \
                        else 'jump to ' + self.specialvars['start_screen']
                }

            } + '\n'

        mkp_ren = re.sub(
            r'{{\s*((?:(?!}}|\s).)*)\s*}}', 
            lambda x: self.repl_handlebars(x, {
                    'version': VERSION,
                    'project_name': self.name if self.name else '',
                    'project_description': self.description if self.description else '',
                    'project_comments': project_comments,
                    'project_body': body
                }), 
            mkp_str
        )

        # mkp_ren = mkp_str % {
        #     'version': VERSION,
        #     'project_name': self.name if self.name else '',
        #     'project_description': self.description if self.description else '',
        #     'project_comments': project_comments,
        #     'project_body': body
        # }

        outfile = filename + '.html'
        output = open(outfile, 'w')
        output.write(mkp_ren)
        output.close()
        return outfile

    def repl_handlebars(self, match, data):
        varname = match.group(1)
        if varname in data:
            return data[varname]
        return match.group(0)

def match_line(exp, line, indent='', match_deeper=False):
    indent = re.escape(indent)
    if match_deeper:
        indent += r'[\s\t]+'
    return re.match(indent + exp, line, re.IGNORECASE)

class markup:
    span = '<span>%(content)s</span>'
    obj = """\
<div class="obj" data-screen-id="%(_screenid)s">
<div class="obj-inner-wrapper clickable" data-collapse-toggle>
<div class="obj-name">%(screenid)s</div>
<div class="obj-description">%(description)s</div>
</div>
<div class="obj-inner-wrapper" data-collapsible>
<div class="obj-contents">%(contents)s</div>
</div>
</div>
"""
    comment = '<span class="comm">%(comment)s</span>'
    partial = '<span class="obj-partial">%(partial)s</span>'
    keyword = '<span class="obj-keyword">%(keyword)s</span>'
    dyndata = '<span class="obj-dyndata">%(dyndata)s</span>'
    elem_data = """\
<div class="elem elem-data"><span>%(elemid)s</span>%(comments)s</div>\
"""
    elem_form = """\
<div class="elem elem-form"><span>%(elemid)s</span>%(comments)s</div>\
"""
    elem_action = """\
<div class="elem elem-action">
<span class="action-name">%(elemid)s</span>%(extras)s</div>
"""
    elem_action_result_custom = """\
<span class="action-result custom">%(custom)s</span>\
"""
    elem_action_result_objpointer = """\
<span class="action-result obj-pointer" data-obj-ref="%(_result)s">%(result)s</span>\
"""
    elem_action_result_group_sep = '<span class="result-sep"></span>'
    elem_notes = '<div class="elem elem-notes">%(notes)s</div>'
    elem_notes_note = '<div class="selem-note">%(note)s</div>'
    project_comments = '<div class="project-comments">%(comments)s</div>'
    project_comment = '<div class="project-comment">%(comment)s</div>'
    clickable_pointer = '<span class="clickable-u" data-obj-ref="%(ref)s">%(label)s</span>'

# define exps
exp_indent = re.compile(r'^[\s\t]*')
exp_comment_enter = re.compile(r'\!')
exp_comment_begin = re.compile(r'\!\*((?:(?!\*\!).)*)$')
exp_comment_end = re.compile(r'^((?:(?!\*\!).)*)\*\!')
exp_comment_inline = re.compile(r'\!\*((?:(?!\*\!).)*)\*\!')

exp_object_raw = r'(?:[a-z*\/].*|\[.+\])'
exp_elem_raw = r'[.:#]?.+'

# start program
if __name__ == '__main__':

    print(bcolors.HEADER + 'Loosewire Text ' + VERSION + bcolors.ENDC)

    try:
        script, filename = argv
    except:
        print('Usage: ' + __file__ + ' [filename]\n')
        exit()

    # print(filename)

    project = open(filename, 'r')
    project_lines = [x for x in project]
    project.close()

    reg = ScreenRegister()

    # project_comments = []
    project_indent = None

    comm_buff = []
    openflag = False

    for index, line in enumerate(project_lines):
        # strip comments
        line, openflag, stripped = strip_comments(line, openflag)

        if stripped['prev']:
            comm_buff.append(stripped['prev'])

        if stripped['endflag']:
            reg.register_comment(comm_buff, True)
            # project_comments.append(''.join([str(x) for x in comm_buff]))
            comm_buff = []

        if stripped['next']:
            comm_buff.append(stripped['next'])

        if stripped['inline']:
            reg.register_comment(stripped['inline'])
            # project_comments += stripped['inline']

        if stripped['line']:
            reg.register_comment(stripped['line'])
            # project_comments += [stripped['line']]

        # skip empty lines
        if not len(line.strip(_stnr)):
            reg.end_line()
            continue

        # set base indent
        if project_indent == None:
            project_indent = exp_indent.match(line).group(0)

        obj = match_line(exp_object_raw, line, \
            indent=project_indent, match_deeper=False)

        if obj:
            reg.register_screen(line, index + 1)

        else:
            elem = match_line(exp_elem_raw, line, \
                indent=project_indent, match_deeper=True)

            if elem:
                reg.register_element(line, index + 1)

        # print(line, end='')

    reg.link_objects()
    outfile = reg.render_output(filename)
    reg.success('Successfully compiled to ' + outfile)




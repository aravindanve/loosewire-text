# loosewire text contencoder
# generates a single file template for output
# requires:
# python 3+ with rjsmin module
# node.js with less package (lessc) installed

import re
import base64
from subprocess import Popen, PIPE

from rjsmin import jsmin

BASEDIR = re.sub(r'/[^/]*$', '/', __file__).rstrip('/') + '/'

class Contencoder:
    # relative paths only
    templatefile = 'index.html'
    tempdir = 'temp/'
    exp_attr = r'%s\s*=\s*[\'"]([^\'"]*)[\'"]'

    @classmethod
    def repl_cssurl(cls, match, filepath):
        #  url(application/x-font-truetype;charset=utf-8;base64,...)
        url = match.group(1)
        basedir = re.sub(r'/[^/]*$', '/', filepath)
        filetype = re.search(r'\.([^\.]+)$', url)
        if not filetype:
            raise Exception('unrecognized filetype: ' + url)

        data_url = 'data:'
        if filetype.group(1) == 'ttf':
            data_url += 'application/x-font-truetype'
        else:
            raise Exception('unrecognized filetype: ' + filetype.group(1))

        data_url += ';charset=utf-8;base64,'

        urlfile = open(BASEDIR + basedir + url, 'rb')
        urlcontent = urlfile.read()
        urlfile.close()

        encoded_file = base64.b64encode(urlcontent)

        data_url += encoded_file.decode(encoding='utf-8')

        return 'url(%s)' % data_url

    @classmethod
    def repl_link(cls, match):
        attrs = match.group(1)
        link_rel = re.search(cls.exp_attr % 'rel', attrs)
        link_href = re.search(cls.exp_attr  % 'href', attrs)

        if link_rel.group(1) == 'stylesheet/less':
            proc = Popen(['lessc', BASEDIR + link_href.group(1)], stdout=PIPE)
            csstext = proc.stdout.read().decode(encoding='utf-8')
            try:
                proc.kill
            except:
                raise
        else:
            cssfile = open(BASEDIR + link_href.group(1), 'r')
            csstext = cssfile.read()
            cssfile.close()

        # remove comments
        csstext = re.sub(r'/\*(?:(?!\*/)(?:.|\n))*\*/', ' ', csstext)
        # remove spaces and newlines
        csstext = re.sub(r'[\s\t\n\r]+', ' ', csstext)

        # embed urls 
        csstext = re.sub(
            r'url\s*\(([^\)]*)\)', 
            lambda x: cls.repl_cssurl(x, link_href.group(1)), 
            csstext
        )
        return '<style type="text/css">%s</style>' % csstext

    @classmethod
    def repl_script(cls, match):
        attrs = match.group(1)
        script_src = re.search(cls.exp_attr % 'src', attrs)
        if script_src.group(1) == None:
            return match.group(0)
        if re.match(r'^.*\bless(?:(?:\b|_).*)?.js$', script_src.group(1)):
            return ''
        jsfile = open(BASEDIR + script_src.group(1), 'r')
        jstext = jsfile.read()
        jsfile.close()

        # remove indents
        # jstext = re.sub(r'\n\s+', '\n', jstext)
        jstext = jsmin(jstext)
        return '<script type="text/javascript">%s</script>\n' % jstext

    @classmethod
    def get_template(cls, writetemp=False):
        tmpfile = open(BASEDIR + cls.templatefile, 'r')
        template = tmpfile.read()
        tmpfile.close()

        # remove comments, double spaces and indents
        template = re.sub(r'<\!--(?:(?!-->)(?:.|\n))*-->', '', template)
        template = re.sub(r'(?:(?!\n)\s)+', ' ', template)
        template = re.sub(r'\n\s+', '\n', template)

        # embed css and compiled less
        template = re.sub(
            r'<link\s+([^>]*)>', cls.repl_link, template
        )

        # embed scripts and remove less.js clientside include
        template = re.sub(
            r'<script\s+([^>]*)>\s*</script>\n?', cls.repl_script, template
        )

        if writetemp:
            outfile = open(BASEDIR + cls.tempdir + cls.templatefile, 'w')
            outfile.write(template)
            outfile.close()

        return template


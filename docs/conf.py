#!/usr/bin/env python3
# vim:fileencoding=utf-8
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# https://www.sphinx-doc.org/en/master/config

import os
import re
import subprocess
import sys
import time
from functools import partial
from typing import (
    Any, Callable, Dict, Iterable, List, Match, Optional, Sequence, Tuple,
    Union
)

from docutils import nodes
from docutils.parsers.rst.roles import set_classes
from pygments.lexer import RegexLexer, bygroups  # type: ignore
from pygments.token import (  # type: ignore
    Comment, Keyword, Literal, Name, Number, String, Whitespace
)
from sphinx import addnodes, version_info  # type: ignore
from sphinx.environment.adapters.toctree import TocTree  # type: ignore
from sphinx.util.logging import getLogger  # type: ignore

kitty_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if kitty_src not in sys.path:
    sys.path.insert(0, kitty_src)

from kitty.conf.definition import Option, Shortcut  # noqa
from kitty.constants import str_version  # noqa


# config {{{
# -- Project information -----------------------------------------------------

project = 'kitty'
copyright = time.strftime('%Y, Kovid Goyal, KittyPatch')
author = 'Kovid Goyal, KittyPatch'
building_man_pages = 'man' in sys.argv

# The short X.Y version
version = str_version
# The full version, including alpha/beta/rc tags
release = str_version
logger = getLogger(__name__)


# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
needs_sphinx = '1.7'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.ifconfig',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language: Optional[str] = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path .
exclude_patterns = [
    '_build', 'Thumbs.db', '.DS_Store',
    'generated/cli-*.rst', 'generated/conf-*.rst'
]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

rst_prolog = '''
.. |kitty| replace:: *kitty*
.. |version| replace:: VERSION
.. _tarball: https://github.com/KittyPatch/kitty/releases/download/vVERSION/kitty-VERSION.tar.xz
.. role:: green
.. role:: italic
.. role:: bold
.. role:: cyan
.. role:: title
.. role:: env

'''.replace('VERSION', str_version)


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'alabaster'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
html_theme_options = {
    'logo': 'kitty.png',
    'show_powered_by': False,
    'fixed_sidebar': True,
    'sidebar_collapse': True,
    'github_button': False,
    'github_banner': True,
    'github_user': 'KittyPatch',
    'github_repo': 'kitty',
    # increase contrast of link color with text color
    'link': '#00587d',
    'link_hover': 'green',
}


# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static', '../logo/kitty.png']
html_favicon = '../logo/kitty.png'

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# The default sidebars (for documents that don't match any pattern) are
# defined by theme itself.  Builtin themes are using these templates by
# default: ``['localtoc.html', 'relations.html', 'sourcelink.html',
# 'searchbox.html']``.
#
html_sidebars = {
    '**': [
        'about.html',
        'support.html',
        'searchbox.html',
        'localtoc.html',
        'relations.html',
    ]
}
html_show_sourcelink = False


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    ('invocation', 'kitty', 'kitty Documentation', [author], 1),
    ('conf', 'kitty.conf', 'kitty.conf Documentation', [author], 5)
]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'kitty', 'kitty Documentation',
     author, 'kitty', 'Cross-platform, fast, feature-rich, GPU based terminal',
     'Miscellaneous'),
]
# }}}


# GitHub linking inline roles {{{

def num_role(which: str, name: str, rawtext: str, text: str, lineno: int, inliner: Any, options: Any = {}, content: Any = []) -> Tuple[List, List]:
    ' Link to a github issue '
    try:
        issue_num = int(text)
        if issue_num <= 0:
            raise ValueError
    except ValueError:
        msg = inliner.reporter.error(
            'GitHub issue number must be a number greater than or equal to 1; '
            '"%s" is invalid.' % text, line=lineno)
        prb = inliner.problematic(rawtext, rawtext, msg)
        return [prb], [msg]
    url = f'https://github.com/kovidgoyal/kitty/{which}/{issue_num}'
    set_classes(options)
    node = nodes.reference(rawtext, f'#{issue_num}', refuri=url, **options)
    return [node], []


def commit_role(name: str, rawtext: str, text: str, lineno: int, inliner: Any, options: Any = {}, content: Any = []) -> Tuple[List, List]:
    ' Link to a github commit '
    try:
        commit_id = subprocess.check_output(
            f'git rev-list --max-count=1 --skip=# {text}'.split()).decode('utf-8').strip()
    except Exception:
        msg = inliner.reporter.error(
            f'GitHub commit id "{text}" not recognized.', line=lineno)
        prb = inliner.problematic(rawtext, rawtext, msg)
        return [prb], [msg]
    url = f'https://github.com/KittyPatch/kitty/commit/{commit_id}'
    set_classes(options)
    short_id = subprocess.check_output(
        f'git rev-list --max-count=1 --abbrev-commit --skip=# {commit_id}'.split()).decode('utf-8').strip()
    node = nodes.reference(rawtext, f'commit: {short_id}', refuri=url, **options)
    return [node], []
# }}}


# Sidebar ToC {{{
def create_toc(app: Any, pagename: str) -> Optional[Any]:
    tt = TocTree(app.env)
    toctree = tt.get_toc_for(pagename, app.builder)
    if toctree is not None:
        subtree = toctree[toctree.first_child_matching_class(nodes.list_item)]
        bl = subtree.first_child_matching_class(nodes.bullet_list)
        if bl is None:
            return None  # Empty ToC
        subtree = subtree[bl]
        # for li in subtree.traverse(nodes.list_item):
        #     modify_li(li)
        # subtree['ids'] = [ID]
        return app.builder.render_partial(subtree)['fragment']


def add_html_context(app: Any, pagename: str, templatename: str, context: Any, *args: Any) -> None:
    if 'toc' in context:
        context['toc'] = create_toc(app, pagename) or context['toc']
# }}}


# CLI docs {{{
def write_cli_docs(all_kitten_names: Iterable[str]) -> None:
    from kitty.launch import options_spec as launch_options_spec
    from kitty.cli import option_spec_as_rst
    with open('generated/launch.rst', 'w') as f:
        f.write(option_spec_as_rst(
            appname='launch', ospec=launch_options_spec, heading_char='_',
            message='''\
Launch an arbitrary program in a new kitty window/tab. Note that
if you specify a program-to-run you can use the special placeholder
:code:`@selection` which will be replaced by the current selection.
'''
        ))
    with open('generated/cli-kitty.rst', 'w') as f:
        f.write(option_spec_as_rst(appname='kitty').replace(
            'kitty --to', 'kitty @ --to'))
    as_rst = partial(option_spec_as_rst, heading_char='_')
    from kitty.rc.base import all_command_names, command_for_name
    from kitty.remote_control import global_options_spec, cli_msg
    with open('generated/cli-kitty-at.rst', 'w') as f:
        p = partial(print, file=f)
        p('kitty @\n' + '-' * 80)
        p('.. program::', 'kitty @')
        p('\n\n' + as_rst(
            global_options_spec, message=cli_msg, usage='command ...', appname='kitty @'))
        from kitty.rc.base import cli_params_for
        for cmd_name in sorted(all_command_names()):
            func = command_for_name(cmd_name)
            p(f'.. _at_{func.name}:\n')
            p('kitty @', func.name + '\n' + '-' * 120)
            p('.. program::', 'kitty @', func.name)
            p('\n\n' + as_rst(*cli_params_for(func)))
    from kittens.runner import get_kitten_cli_docs
    for kitten in all_kitten_names:
        data = get_kitten_cli_docs(kitten)
        if data:
            with open(f'generated/cli-kitten-{kitten}.rst', 'w') as f:
                p = partial(print, file=f)
                p('.. program::', f'kitty +kitten {kitten}')
                p('\n\n' + option_spec_as_rst(
                    data['options'], message=data['help_text'], usage=data['usage'], appname=f'kitty +kitten {kitten}',
                    heading_char='^'))

# }}}


def write_remote_control_protocol_docs() -> None:  # {{{
    from kitty.rc.base import all_command_names, command_for_name, RemoteCommand
    field_pat = re.compile(r'\s*([a-zA-Z0-9_+]+)\s*:\s*(.+)')

    def format_cmd(p: Callable, name: str, cmd: RemoteCommand) -> None:
        p(name)
        p('-' * 80)
        lines = (cmd.__doc__ or '').strip().splitlines()
        fields = []
        for line in lines:
            m = field_pat.match(line)
            if m is None:
                p(line)
            else:
                fields.append((m.group(1), m.group(2)))
        if fields:
            p('\nFields are:\n')
            for (name, desc) in fields:
                if '+' in name:
                    title = name.replace('+', ' (required)')
                else:
                    title = name
                    defval = cmd.get_default(name.replace('-', '_'), cmd)
                    if defval is not cmd:
                        title = f'{title} (default: {defval})'
                    else:
                        title = f'{title} (optional)'
                p(f':code:`{title}`')
                p(' ', desc), p()
        p(), p()

    with open('generated/rc.rst', 'w') as f:
        p = partial(print, file=f)
        for name in sorted(all_command_names()):
            cmd = command_for_name(name)
            if not cmd.__doc__:
                continue
            name = name.replace('_', '-')
            format_cmd(p, name, cmd)
# }}}


# config file docs {{{

class ConfLexer(RegexLexer):
    name = 'Conf'
    aliases = ['conf']
    filenames = ['*.conf']

    tokens = {
        'root': [
            (r'#.*?$', Comment.Single),
            (r'\s+$', Whitespace),
            (r'\s+', Whitespace),
            (r'(include)(\s+)(.+?)$', bygroups(Comment.Preproc, Whitespace, Name.Namespace)),
            (r'(map)(\s+)(\S+)(\s+)', bygroups(
                Keyword.Declaration, Whitespace, String, Whitespace), 'action'),
            (r'(symbol_map)(\s+)(\S+)(\s+)(.+?)$', bygroups(
                Keyword.Declaration, Whitespace, String, Whitespace, Literal)),
            (r'([a-zA-Z_0-9]+)(\s+)', bygroups(
                Name.Variable, Whitespace), 'args'),
        ],
        'action': [
            (r'[a-z_0-9]+$', Name.Function, 'root'),
            (r'[a-z_0-9]+', Name.Function, 'args'),
        ],
        'args': [
            (r'\s+', Whitespace, 'args'),
            (r'\b(yes|no)\b$', Number.Bin, 'root'),
            (r'\b(yes|no)\b', Number.Bin, 'args'),
            (r'[+-]?[0-9]+\s*$', Number.Integer, 'root'),
            (r'[+-]?[0-9.]+\s*$', Number.Float, 'root'),
            (r'[+-]?[0-9]+', Number.Integer, 'args'),
            (r'[+-]?[0-9.]+', Number.Float, 'args'),
            (r'#[a-fA-F0-9]{3,6}\s*$', String, 'root'),
            (r'#[a-fA-F0-9]{3,6}\s*', String, 'args'),
            (r'.+', String, 'root'),
        ],
    }


class SessionLexer(RegexLexer):
    name = 'Session'
    aliases = ['session']
    filenames = ['*.session']

    tokens = {
        'root': [
            (r'#.*?$', Comment.Single),
            (r'[a-z][a-z0-9_]+', Name.Function, 'args'),
        ],
        'args': [
            (r'.*?$', Literal, 'root'),
        ]
    }


def link_role(name: str, rawtext: str, text: str, lineno: int, inliner: Any, options: Any = {}, content: Any = []) -> Tuple[List, List]:
    m = re.match(r'(.+)\s+<(.+?)>', text)
    if m is None:
        msg = inliner.reporter.error(f'link "{text}" not recognized', line=lineno)
        prb = inliner.problematic(rawtext, rawtext, msg)
        return [prb], [msg]
    text, url = m.group(1, 2)
    set_classes(options)
    node = nodes.reference(rawtext, text, refuri=url, **options)
    return [node], []


def expand_opt_references(conf_name: str, text: str) -> str:
    conf_name += '.'

    def expand(m: Match) -> str:
        ref = m.group(1)
        if '<' not in ref and '.' not in ref:
            full_ref = conf_name + ref
            return ':opt:`{} <{}>`'.format(ref, full_ref)
        return str(m.group())

    return re.sub(r':opt:`(.+?)`', expand, text)


opt_aliases: Dict[str, str] = {}
shortcut_slugs: Dict[str, Tuple[str, str]] = {}


def parse_opt_node(env: Any, sig: str, signode: Any) -> str:
    """Transform an option description into RST nodes."""
    count = 0
    firstname = ''
    for potential_option in sig.split(', '):
        optname = potential_option.strip()
        if count:
            signode += addnodes.desc_addname(', ', ', ')
        text = optname.split('.', 1)[-1]
        signode += addnodes.desc_name(text, text)
        if not count:
            firstname = optname
            signode['allnames'] = [optname]
        else:
            signode['allnames'].append(optname)
            opt_aliases[optname] = firstname
        count += 1
    if not firstname:
        raise ValueError('{} is not a valid opt'.format(sig))
    return firstname


def parse_shortcut_node(env: Any, sig: str, signode: Any) -> str:
    """Transform a shortcut description into RST nodes."""
    conf_name, text = sig.split('.', 1)
    signode += addnodes.desc_name(text, text)
    return sig


def render_conf(conf_name: str, all_options: Iterable[Union['Option', Sequence['Shortcut']]]) -> str:
    from kitty.conf.definition import merged_opts, Option, Group
    ans = ['.. default-domain:: conf', '']
    a = ans.append
    current_group: Optional[Group] = None
    all_options_ = list(all_options)
    kitty_mod = 'kitty_mod'

    def render_group(group: Group) -> None:
        a('')
        a(f'.. _conf-{conf_name}-{group.name}:')
        a('')
        a(group.short_text)
        heading_level = '+' if '.' in group.name else '^'
        a(heading_level * (len(group.short_text) + 20))
        a('')
        if group.start_text:
            a(group.start_text)
            a('')

    def handle_group_end(group: Group) -> None:
        if group.end_text:
            assert current_group is not None
            a(''), a(current_group.end_text)

    def handle_group(new_group: Group, new_group_is_shortcut: bool = False) -> None:
        nonlocal current_group
        if new_group is not current_group:
            if current_group:
                handle_group_end(current_group)
            current_group = new_group
            render_group(current_group)

    def handle_option(i: int, opt: Option) -> None:
        nonlocal kitty_mod
        if not opt.long_text or not opt.add_to_docs:
            return
        handle_group(opt.group)
        if opt.name == 'kitty_mod':
            kitty_mod = opt.defval_as_string
        mopts = list(merged_opts(all_options_, opt, i))
        a('.. opt:: ' + ', '.join(conf_name + '.' + mo.name for mo in mopts))
        a('.. code-block:: conf')
        a('')
        sz = max(len(x.name) for x in mopts)
        for mo in mopts:
            a(('    {:%ds} {}' % sz).format(mo.name, mo.defval_as_string))
        a('')
        if opt.long_text:
            a(expand_opt_references(conf_name, opt.long_text))
            a('')

    def handle_shortcuts(shortcuts: Sequence[Shortcut]) -> None:
        sc = shortcuts[0]
        handle_group(sc.group, True)
        sc_text = f'{conf_name}.{sc.short_text}'
        a('.. shortcut:: ' + sc_text)
        shortcuts = [s for s in shortcuts if s.add_to_default]
        shortcut_slugs[f'{conf_name}.{sc.name}'] = (sc_text, sc.key.replace('kitty_mod', kitty_mod))
        if shortcuts:
            a('.. code-block:: conf')
            a('')
            for x in shortcuts:
                if x.add_to_default:
                    a('    map {} {}'.format(x.key.replace('kitty_mod', kitty_mod), x.action_def))
        a('')
        if sc.long_text:
            a(expand_opt_references(conf_name, sc.long_text))
            a('')

    for i, opt in enumerate(all_options_):
        if isinstance(opt, Option):
            handle_option(i, opt)
        else:
            handle_shortcuts(opt)

    if current_group:
        handle_group_end(current_group)
    return '\n'.join(ans)


def process_opt_link(env: Any, refnode: Any, has_explicit_title: bool, title: str, target: str) -> Tuple[str, str]:
    conf_name, opt = target.partition('.')[::2]
    if not opt:
        conf_name, opt = 'kitty', conf_name
    full_name = conf_name + '.' + opt
    return title, opt_aliases.get(full_name, full_name)


def process_shortcut_link(env: Any, refnode: Any, has_explicit_title: bool, title: str, target: str) -> Tuple[str, str]:
    conf_name, slug = target.partition('.')[::2]
    if not slug:
        conf_name, slug = 'kitty', conf_name
    full_name = conf_name + '.' + slug
    try:
        target, stitle = shortcut_slugs[full_name]
    except KeyError:
        logger.warning('Unknown shortcut: {}'.format(target), location=refnode)
    else:
        if not has_explicit_title:
            title = stitle
    return title, target


def write_conf_docs(app: Any, all_kitten_names: Iterable[str]) -> None:
    app.add_lexer('conf', ConfLexer() if version_info[0] < 3 else ConfLexer)
    app.add_object_type(
        'opt', 'opt',
        indextemplate="pair: %s; Config Setting",
        parse_node=parse_opt_node,
    )
    # Warn about opt references that could not be resolved
    opt_role = app.registry.domain_roles['std']['opt']
    opt_role.warn_dangling = True
    opt_role.process_link = process_opt_link

    app.add_object_type(
        'shortcut', 'sc',
        indextemplate="pair: %s; Keyboard Shortcut",
        parse_node=parse_shortcut_node,
    )
    sc_role = app.registry.domain_roles['std']['sc']
    sc_role.warn_dangling = True
    sc_role.process_link = process_shortcut_link

    def generate_default_config(all_options: Dict[str, Union[Option, Sequence[Shortcut]]], name: str) -> None:
        from kitty.conf.definition import as_conf_file
        with open(f'generated/conf-{name}.rst', 'w', encoding='utf-8') as f:
            print('.. highlight:: conf\n', file=f)
            f.write(render_conf(name, all_options.values()))

        conf_name = re.sub(r'^kitten-', '', name) + '.conf'
        with open(f'generated/conf/{conf_name}', 'w', encoding='utf-8') as f:
            text = '\n'.join(as_conf_file(all_options.values()))
            print(text, file=f)

    from kitty.config_data import all_options
    generate_default_config(all_options, 'kitty')

    from kittens.runner import get_kitten_conf_docs
    for kitten in all_kitten_names:
        all_options = get_kitten_conf_docs(kitten)
        if all_options:
            generate_default_config(all_options, f'kitten-{kitten}')
# }}}


def setup(app: Any) -> None:
    os.makedirs('generated/conf', exist_ok=True)
    from kittens.runner import all_kitten_names
    kn = all_kitten_names()
    write_cli_docs(kn)
    write_remote_control_protocol_docs()
    write_conf_docs(app, kn)
    app.add_css_file('custom.css')
    app.add_lexer('session', SessionLexer() if version_info[0] < 3 else SessionLexer)
    app.add_role('link', link_role)
    app.add_role('iss', partial(num_role, 'issues'))
    app.add_role('pull', partial(num_role, 'pull'))
    app.add_role('commit', commit_role)
    app.connect('html-page-context', add_html_context)

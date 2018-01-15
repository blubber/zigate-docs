import os
import sys

from jinja2 import Template, Environment, FileSystemLoader
import yaml


DOCS = {
    'zigbee': (28, 'Spec.', 'http://www.zigbee.org/wp-content/uploads/2014/11/docs-05-3474-20-0csg-zigbee-specification.pdf'),
    'zcl': (0, 'ZCL', 'http://www.zigbee.org/~zigbeeor/wp-content/uploads/2014/10/07-5123-06-zigbee-cluster-library-specification.pdf'),
}


def f_href(value):
    return value.replace(' ', '_')


def f_spec(page, doc='zigbee', label=None, title=None):
    offset, title_, url = DOCS[doc]
    label = label or page

    if title is None:
        title = title_

    if not f_spec._template:
        t = '''<span class="text-nowrap">{{ title }}{% if page %}, p.{% endif %}
               <a href="{{ url }}{% if page %}#page={{ page }}{% endif %}" target="_blank">{{ label }}</a></span>'''
        f_spec._template = env.from_string(t)

    page = page + offset if page else None
    return f_spec._template.render(title=title, url=url, page=page, label=label)

f_spec._template = None


def f_column(item, column):
    if 'template' in column:
        t = column['template']
    else:
        t = '{{ %s }}' % column['column']

    if t in f_column._cache:
        template = f_column._cache[t]
    else:
        template = env.from_string(t)
        f_column._cache[t] = template

    return template.render(**item)

f_column._cache = {}


def f_render(fmt, **context):
    if fmt not in f_render._cache:
        f_render._cache[fmt] = env.from_string(fmt)
    return f_render._cache[fmt].render(**context)

f_render._cache = {}


packets = {}

for fn in os.listdir('packets'):
    if fn.endswith('.yml'):
        with open('packets/%s' % fn) as fp:
            packet = yaml.load(fp)
        packets.setdefault(packet['category'], []).append(packet)

env = Environment(loader=FileSystemLoader('.'))
env.filters['href'] = f_href
env.filters['spec'] = f_spec
env.filters['column'] = f_column
env.filters['render'] = f_render


categories = []
for category, items in packets.items():
    items = sorted(items, key=lambda i: i['type'])
    categories.append({
        'category': category,
        'items': items,
        'order': items[0]['type']
    })

categories = [(c['category'], c['items']) for c in sorted(categories, key=lambda c: c['order'])] 

context = {'categories': categories, 'tables': []}

for fn in sorted(os.listdir('tables')):
    if fn.endswith('.yml'):
        with open('tables/%s' % fn) as fp:
            table = yaml.load(fp)

        if 'description' in table:
            template = env.from_string(table['description'])
            table['description'] = template.render(**table)
        context['tables'].append(table)

template = env.get_template('template.html')

with open('index.html', 'w') as fp:
    fp.write(template.render(**context))

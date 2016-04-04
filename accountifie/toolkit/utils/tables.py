from django.template import Context
from django.template.loader import get_template


def get_bstrap_table(data_url, row_defs, pagination="true", pagination_num=25):
    context = {}

    context['data_url'] = data_url
    context['row_defs'] = row_defs
    context['pagination'] = pagination
    context['pagination_num'] = pagination_num

    tmpl = get_template('bstrap_table.html')
    return tmpl.render(Context(context))

from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.shortcuts import render
from django.template import RequestContext, Context
from django.core.serializers.json import DjangoJSONEncoder

from accountifie.cal.models import Year
from accountifie.common.api import api_func
import accountifie.query.query_manager
import accountifie.toolkit.utils as utils
import accountifie.reporting.rptutils as rptutils

import logging

logger = logging.getLogger('default')



ACCT_DEF = {
    'id': {'link': lambda x: "/api/reporting/transaction/%s" % x},
    'date': {},
    'comment': {},
    'account_id': {'link': lambda x: "/reporting/history/account/%s" % x},
    'contra_accts': {'link': lambda x: "/reporting/history/account/%s" % x},
    'counterparty': {'link': lambda x: "/reporting/history/creditor/%s" % x},
    'amount': {'fmt': lambda x: "{:,.2f}".format(x)},
    'balance': {'fmt': lambda x: "{:,.2f}".format(x)}
}

def create_entry(value, fmtr):
    entry = {'text': fmtr['fmt'](value) if 'fmt' in fmtr else value}
    if 'link' in fmtr:
        entry['link'] = fmtr['link'](value)
    return entry


def create_row(row, col_order, fmtr=ACCT_DEF):
    return [create_entry(row[i], fmtr[i]) for i in col_order]

@login_required
def history(request, type, id):
    config = rptutils.history_prep(request)
    start_date = config.get('from', settings.DATE_EARLY)
    end_date = config.get('to', settings.DATE_LATE)
    company_id = config['company_id']

    if type == 'account':
        cp = request.GET.get('cp',None)
        acct = api_func('gl', 'account', id)

        display_name = '%s: %s' %(acct['id'], acct['display_name'])
        history = accountifie.query.query_manager.QueryManager().pd_history(company_id, 'account', acct['id'], from_date=start_date, to_date=end_date, cp=cp)

        if cp and not history.empty:
            history = history[history['counterparty']==cp]
            history['balance'] = history['amount'].cumsum()
            display_name += ' -- %s' % cp

        column_titles = ['id', 'date', 'comment', 'contra_accts', 'counterparty', 'amount', 'balance']
    elif type == 'path':
        ref = id.replace('_','.')
        display_name = 'path: %s' % ref
        excl = request.GET['excl'].split(',') if request.GET.has_key('excl') else None
        incl = request.GET['incl'].split(',') if request.GET.has_key('incl') else None
        if excl:
            excl = [x.replace('_','.') for x in excl]
            display_name += '  -- excl %s' % ','.join(excl)
        if incl:
            incl = [x.replace('_','.') for x in incl]
            display_name += '  -- incl %s' % ','.join(incl)
        history = accountifie.query.query_manager.QueryManager().pd_history(company_id, type, ref, from_date=start_date, to_date=end_date, excl_contra=excl, incl=incl)
        column_titles = ['id', 'date', 'comment', 'account_id', 'contra_accts', 'counterparty', 'amount', 'balance']
    elif type == 'creditor':
        cp = request.GET.get('cp',None)
        cp_info = api_func('gl', 'counterparty', id)
        
        display_name = '%s: %s' %(cp_info['id'], cp_info['name'])
        history = accountifie.query.query_manager.QueryManager().pd_history(company_id, 'account', '3000', from_date=start_date, to_date=end_date, cp=id)
        history = history[history['counterparty']==id]
        history['balance'] = history['amount'].cumsum()

        column_titles = ['id', 'date', 'comment', 'contra_accts', 'amount', 'balance']
    else:
        raise ValueError('This type of history is not supported')

    years = Year.objects.all()
    entries = []

    if (history is not None) and (history.empty is False):
        unused_history = history[history['date'] < start_date]
        used_history = history[history['date'] >= start_date]

        if len(unused_history) > 0:
            start_row = unused_history.iloc[-1]
            start_row['id'] = 'None'
            start_row['date'] = start_date
            start_row['comment'] = 'Opening Balance'
            start_row['contra_accts'] = 'None'
            start_row['counterparty'] = 'None'
            start_row['amount'] = 0
            entries.append(create_row(start_row, column_titles))
        
        for i in used_history.index:
            entries.append(create_row(history.loc[i], column_titles))
    
    context = {}
    context['display_name'] = display_name
    context['column_titles'] = column_titles
    context['history'] = entries
    context['years'] = years
    context['by_date_cleared'] = False
    context['from_date'] = start_date
    context['to_date'] = end_date

    return render(request, 'history.html', context)

@login_required
def balance_history(request, type, id):
    config = rptutils.history_prep(request)
    from_date = config.get('from', settings.DATE_EARLY)
    to_date = config.get('to', settings.DATE_LATE)
    company_id = config['company_id']

    if type == 'account':
        cp = request.GET.get('cp',None)
        acct = api_func('gl', 'account', id)
        display_name = '%s: %s' %(acct['id'], acct['display_name'])
        history = accountifie.query.query_manager.QueryManager().pd_history(company_id, 'account', acct['id'], from_date=from_date, to_date=to_date, cp=cp)

        if cp and not history.empty:
            history = history[history['counterparty']==cp]
            display_name += ' -- %s' % cp
        
        balance_history = history[['amount','date']].groupby('date').sum().cumsum().reset_index()
        column_titles = ['date', 'amount']
    elif type == 'path':
        ref = id.replace('_','.')
        display_name = 'path: %s' % ref
        excl = request.GET['excl'].split(',') if request.GET.has_key('excl') else None
        incl = request.GET['incl'].split(',') if request.GET.has_key('incl') else None
        if excl:
            excl = [x.replace('_','.') for x in excl]
            display_name += '  -- excl %s' % ','.join(excl)
        if incl:
            incl = [x.replace('_','.') for x in incl]
            display_name += '  -- incl %s' % ','.join(incl)
        history = accountifie.query.query_manager.QueryManager().pd_history(company_id, type, ref, from_date=from_date, to_date=to_date, excl_contra=excl, incl=incl)
        balance_history = history[['amount','date']].groupby('date').sum().cumsum().reset_index()
        column_titles = ['date', 'amount']
    elif type == 'creditor':
        cp = request.GET.get('cp',None)
        cp_info = api_func('gl', 'counterparty', id)
        
        display_name = '%s: %s' %(cp_info['id'], cp_info['name'])
        history = accountifie.query.query_manager.QueryManager().pd_history(company_id, 'account', '3000', from_date=from_date, to_date=to_date, cp=id)
        history = history[history['counterparty']==id]
        balance_history = history[['amount','date']].groupby('date').sum().cumsum().reset_index()
        column_titles = ['date', 'amount']
    else:
        raise ValueError('This type of history is not supported')

    years = Year.objects.all()
    entries = []
    if balance_history is not None:
        for i in balance_history.index:
            entries.append(create_row(balance_history.loc[i], column_titles))
    
    context = {}
    context['display_name'] = display_name
    context['column_titles'] = column_titles
    context['history'] = entries
    context['years'] = years
    context['by_date_cleared'] = False
    context['from_date'] = from_date
    context['to_date'] = to_date

    return render(request, 'bal_history.html', context)

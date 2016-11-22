import csv

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.conf import settings

import accountifie.reporting.api
from accountifie.common.api import api_func
import accountifie.reporting.rptutils as rptutils


@login_required
def download_ledger(request):
    config = rptutils.history_prep(request)
    from_date = config.get('from', settings.DATE_EARLY)
    to_date = config.get('to', settings.DATE_LATE)
    company_id = config['company_id']

    accts = api_func('gl', 'accounts')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="ledger.csv"'
    writer = csv.writer(response)

    header_row = ['id', 'date', 'comment', 'contra_accts', 'counterparty', 'amount', 'balance']

    for acct in accts:
        history = accountifie.reporting.api.history({'type': 'account', 'from_date': from_date, 'to_date': to_date, 'company_id': company_id, 'id': acct['id']})
        if len(history) > 0:
            writer.writerow([])
            writer.writerow([acct['id'], acct['display_name'], acct['path']])
            writer.writerow([])
            writer.writerow(header_row)
            for idx in history.index:
                writer.writerow([history.loc[idx, col] for col in header_row])
    
    return response


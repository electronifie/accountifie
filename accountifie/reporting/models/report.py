"""Mini-framework for generating banded reports


A Report is initialised with a list of time identifiers for the columns,
and a list of bands running vertically.   A Band can be a piece of text,
or a row for an account, or a group of rows involving some kind of
drill-down.

When executed, a report returns a list of rows.  Each row is a dictionary
containing information to be formatted.   The possible entries are...

    id:  optional. logical identifier to be used in calculations or as
        a target for links
    type: required. 'text' or 'account'

    values:  required for non-text rows.
        the numbers to be drawn in each numeric cell.  Reports do a last minute
        pass over all the values formatting them as strings (accounting format)

    css_class:  the main typographic class we will use for its text

    indent:  default 0, 1 or 2 indent it further across to allow nesting

    line_above:  False or True or 0 or 1 or 2 (for double)
    line_below:  False or True or 0 or 1 or 2 (for double)




"""
from dateutil.parser import parse
import datetime


from bands import TextBand, BasicBand
from reportdef import ReportDef

import accountifie.query.query_manager
from accountifie.common.api import api_func
import accountifie.toolkit.utils as utils





ITEM = {'css_class': 'minor', 'indent': 1, 'type': 'group_item'}
MINOR_TOTAL = {'css_class': 'minor', 'indent': 0, 'type': 'group_total'}
MAJOR_TOTAL = {'css_class': 'major', 'indent': 0, 'type': 'group_total2'}
WARNING = {'css_class': 'warning', 'indent': 0, 'type': 'normal'}
ROW_FORMATS = {'item': ITEM, 'minor_total': MINOR_TOTAL, 'major_total': MAJOR_TOTAL, 'warning': WARNING}



class Report(object):
    def __init__(self, company_id, description='', title='', subtitle='', footer='', bands = [], columns={}, calc_type='as_of'):
        self.description = description
        self.title = title
        self.subtitle = subtitle
        self.footer = footer
        self.dflt_title = title
        self.company_id = company_id
        self.bands = bands
        self.columns = columns
        self.calc_type = calc_type
        
        self.set_company()
        self.by_id = {}



    def set_company(self):
        self.company_name = api_func('gl', 'company', self.company_id)['name']


    def set_columns(self, columns, column_order=None):
        self.columns = columns
        self.column_order = column_order

    def set_gl_strategy(self, gl_strategy):
        self.query_manager = accountifie.query.query_manager.QueryManager(gl_strategy=gl_strategy)

    def configure(self, as_of=None, col_tag=None, path=None):
        if as_of:
            self.config_fromdate(as_of)
        elif col_tag:
            self.config_fromtag(col_tag)
        else:
            self.config_fromdate('today')
        if path:
            self.path = path


    def config_fromdate(self, as_of):
        # depends on report.calc_type = 'as_of' or 'diff'
        if as_of == 'today':
            as_of = datetime.datetime.now().date()    
        else:
            as_of = parse(as_of).date()
        
        if self.calc_type == 'as_of':
            as_of_col = {as_of.strftime('%d-%b-%y'): as_of.isoformat()}
        else:
            as_of_col = {str(as_of.year), str(as_of.year)}
        
        self.set_columns(as_of_col, column_order=as_of_col.keys())
        self.title = '%s, %s' % (self.description, as_of.strftime('%d-%b-%y'))
        self.date = as_of.isoformat()

    def config_fromtag(self,col_tag):
        config = utils.config_fromcoltag(col_tag, self.description, self.calc_type)
        self.title = config['title']
        self.set_columns(config['columns'], column_order=config['column_order'])

    
    def set_title(self, override=None):
        if override:
            self.title = override
        else:
            self.title = self.description

    def get_row(self, df_row):
        
        if 'fmt_tag' in df_row:
            if df_row['fmt_tag'] == 'header':
                return TextBand(df_row['label'], css_class='normal').get_rows(self)
            else:
                values = [utils.entry(df_row[col_label]['text'] , link=df_row[col_label]['link']) for col_label in self.column_order]
                fmt_tag = df_row['fmt_tag']
                _css_class = ROW_FORMATS[fmt_tag]['css_class']
                _indent  = ROW_FORMATS[fmt_tag]['indent']
                _type  = ROW_FORMATS[fmt_tag]['type']
                return BasicBand(df_row['label'], css_class=_css_class, values=values, indent=_indent, type=_type).get_rows(self)
        else:
            values = [utils.entry(df_row[col_label]['text'] , link=df_row[col_label]['link']) for col_label in self.column_order]
            return BasicBand(df_row['label'], css_class=df_row['css_class'], values=values, \
                                indent=df_row['indent'], type=df_row['type']).get_rows(self)


    def html_report_context(self):
        if self.column_order:
            column_titles = self.column_order
        else:
            column_titles = self.columns.keys()

        columns = [self.columns[x] for x in column_titles]
        
        context = dict(
                report=self,
                columns=columns,
                column_titles=column_titles,
                title=self.title,
                colcount = 2+len(self.columns),
                italic_styles = ['group_header', 'group_total'],
                no_space_before_styles = ['group_item', 'group_total'],
                numeric_column_indices = range(2, len(self.columns) + 2),
                )

        return context

    def pdf_report_context(self):
        if self.column_order:
            column_titles = self.column_order
        else:
            column_titles = self.columns.keys()

        columns = [self.columns[x] for x in column_titles]
        
        context = dict(
                report=self,
                columns=columns,
                column_titles=column_titles,
                title=self.title,
                colcount = 2+len(self.columns),
                italic_styles = ['group_header', 'group_total'],
                no_space_before_styles = ['group_item', 'group_total'],
                numeric_column_indices = range(2, len(self.columns) + 2),
                )

        return context

    def report_content(self):
        output = self.get_content()
        #assume html format
        if self.column_order:
            column_titles = self.column_order
        else:
            column_titles = self.columns.keys()

        columns = [self.columns[x] for x in column_titles]
        
        context = dict(
                report=self,
                rows=output,
                columns=columns,
                column_titles=column_titles,
                title=self.title,
                #hacking around django template language limitations.
                #this should be replaced entirely by CSS
                colcount = 2+len(self.columns),
                italic_styles = ['group_header', 'group_total'],
                no_space_before_styles = ['group_item', 'group_total'],
                #used by jquery.column-align.js
                numeric_column_indices = range(2, len(self.columns) + 2),
                )

        return context



    def get_content(self):
        "Returns list of dictionaries with info to format"
        self.by_id = {}
        content = []

        for band in self.bands:
            this_content = band.get_rows(self)
            content.extend(this_content)

            #allow next few rows to have access to wwhat we worked out
            if band.id and this_content:
                last_row = this_content[-1]
                #last row has values for maths
                if last_row.has_key('values'):
                    self.by_id[band.id] = last_row['values']
        #at the end, walk through formatting
        for row in content:
            if row.has_key('values'):
                if row['values'] != '':
                    row['values'] = [{'text': utils.fmt(c['text']), 'link': c['link']} if c != '' else '' for c in row['values']]
                    
        return content

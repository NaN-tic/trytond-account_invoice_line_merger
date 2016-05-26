# This file is part of the account_invoice_line_merger module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from itertools import groupby
from trytond.model import ModelView, fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.wizard import Button, StateAction, StateView, Wizard


__all__ = ['InvoiceLine', 'InvoiceLineMergerStart', 'InvoiceLineMerger']


class InvoiceLine:
    __metaclass__ = PoolMeta
    __name__ = 'account.invoice.line'

    @classmethod
    def _group_invoice_line_key(cls, line):
        try:
            grouping = super(InvoiceLine, cls)._group_invoice_line_key(line)
        except AttributeError:
            grouping = []
        grouping.extend([
                ('invoice', line.invoice),
                ('company', line.company),
                ('invoice_type', line.invoice_type),
                ('party', line.party),
                ('currency', line.currency),
                ('product', line.product),
                ('unit', line.unit),
                ('type', line.type),
                ('unit_price', line.unit_price),
                ])
        return grouping

    @classmethod
    def _merge_lines(cls, grouped_lines):
        quantity = 0.0
        description = None
        note = None
        for line in reversed(grouped_lines):
            quantity += line.quantity
            if not description:
                description = line.description
            else:
                description += '\n' + line.description
            if not note:
                note = line.note
            elif line.note:
                note += '\n' + line.note
        line.quantity = quantity
        line.description = description
        line.note = note


class InvoiceLineMergerStart(ModelView):
    'Invoice Line Merger Start'
    __name__ = 'account.invoice.line.merger.start'
    invoices = fields.Char('Invoices', readonly=True)


class InvoiceLineMerger(Wizard):
    'Invoice Line Merger'
    __name__ = 'account.invoice.line.merger'
    start = StateView('account.invoice.line.merger.start',
        'account_invoice_line_merger.account_invoice_line_merger_start_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Merge', 'merge', 'tryton-ok', default=True),
            ])
    merge = StateAction('account_invoice.act_invoice_form')

    def default_start(self, fields):
        return {
            'invoices': ', '.join([str(invoice_id)
                for invoice_id in Transaction().context['active_ids']])
            }

    def do_merge(self, action):
        pool = Pool()
        Invoice = pool.get('account.invoice')
        InvoiceLine = pool.get('account.invoice.line')

        invoices = Invoice.browse(Transaction().context['active_ids'])
        lines = sorted([l for i in invoices
                if i.state == 'draft'
                for l in i.lines],
            key=InvoiceLine._group_invoice_line_key)

        to_update = []
        to_delete = []
        for _, grouped_lines in groupby(lines,
                key=InvoiceLine._group_invoice_line_key):
            grouped_lines = list(grouped_lines)
            if len(grouped_lines) == 1:
                continue

            InvoiceLine._merge_lines(grouped_lines)

            to_update.append(grouped_lines[0])
            to_delete.extend(grouped_lines[1:])

        with Transaction().set_user(0, set_context=True):
            if to_update:
                InvoiceLine.save(to_update)
            if to_delete:
                InvoiceLine.delete(to_delete)

        data = {'res_id': [i.id for i in invoices]}
        action['views'].reverse()
        return action, data

# This file is part of the account_invoice_line_merger module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .invoice import *


def register():
    Pool.register(
        InvoiceLine,
        InvoiceLineMergerStart,
        module='account_invoice_line_merger', type_='model')
    Pool.register(
        InvoiceLineMerger,
        module='account_invoice_line_merger', type_='wizard')

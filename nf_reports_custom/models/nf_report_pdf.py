# -*- coding: utf-8 -*-
import json
from odoo import models


class NfReportWizardPdfReport(models.AbstractModel):
    _name = 'report.nf_reports_custom.report_nf_wizard_pdf'
    _description = 'PDF Report Generator for NF Wizard'

    def _get_report_values(self, docids, data=None):
        wizards = self.env['nf.report.wizard'].browse(docids)
        reports = []
        for wizard in wizards:
            cols = json.loads(wizard.result_cols or '[]')
            rows = json.loads(wizard.result_data or '[]')
            reports.append({
                'wizard': wizard,
                'cols': cols,
                'rows': rows,
                'report_name': wizard.report_id.name or 'Reporte',
                'total_rows': wizard.total_rows,
                'execution_time': wizard.execution_time,
            })
        return {
            'doc_ids': docids,
            'doc_model': 'nf.report.wizard',
            'docs': wizards,
            'reports': reports,
        }

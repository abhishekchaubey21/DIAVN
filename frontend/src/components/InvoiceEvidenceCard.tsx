import React from 'react';
import { 
  FileText, 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  Hash, 
  Building2, 
  User, 
  Receipt, 
  Sparkles, 
  Download,
  AlertTriangle
} from 'lucide-react';

interface LineItem {
  id?: string;
  product_name?: string;
  description?: string;
  hsn_code?: string;
  quantity?: number;
  unit_price?: number;
  taxable_amount?: number;
  tax_rate?: number;
  tax_amount?: number;
  total_amount?: number;
  serial_numbers?: string[];
}

interface InvoiceEvidenceProps {
  invoice: {
    id: string;
    original_filename?: string;
    invoice_number?: string;
    invoice_date?: string;
    dealer_name?: string;
    dealer_gstin?: string;
    customer_name?: string;
    total_amount?: number;
    tax_amount?: number;
    status: 'uploaded' | 'processing' | 'completed' | 'failed' | string;
    verification_status?: string;
    extraction_confidence?: number;
    extraction?: any;
    line_items?: LineItem[];
    download_url?: string;
    error_message?: string;
  };
}

export const InvoiceEvidenceCard: React.FC<InvoiceEvidenceProps> = ({ invoice }) => {
  const isCompleted = invoice.status === 'completed' || invoice.extraction != null;
  const isProcessing = invoice.status === 'processing';
  const isFailed = invoice.status === 'failed';

  const items = invoice.line_items && invoice.line_items.length > 0 
    ? invoice.line_items 
    : invoice.extraction?.items || [];

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-5 backdrop-blur-md space-y-4 shadow-xl">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-800 pb-3.5">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-indigo-950/60 border border-indigo-500/30 text-indigo-400">
            <Receipt className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-bold text-slate-100">
                {invoice.invoice_number ? `Invoice #${invoice.invoice_number}` : (invoice.original_filename || 'Invoice Document')}
              </h4>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                {invoice.original_filename}
              </span>
            </div>
            <div className="flex items-center gap-2 mt-1">
              <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-400 bg-amber-950/40 border border-amber-500/30 px-2 py-0.5 rounded">
                <Sparkles className="h-3 w-3" />
                AI-Extracted Evidence
              </span>
              <span className="inline-flex items-center text-[11px] font-medium text-slate-400 bg-slate-800/80 border border-slate-700 px-2 py-0.5 rounded">
                Not Yet Verified
              </span>
            </div>
          </div>
        </div>

        {/* Extraction Status & Confidence */}
        <div className="flex items-center gap-2.5">
          {isCompleted && (
            <div className="text-right">
              <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-400 block">
                Model Confidence
              </span>
              <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-950/60 border border-emerald-500/30 px-2 py-0.5 rounded">
                {((invoice.extraction_confidence ?? 0.95) * 100).toFixed(0)}%
              </span>
            </div>
          )}

          {isProcessing && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono text-cyan-300 bg-cyan-950/60 border border-cyan-500/40 animate-pulse">
              <Clock className="h-3.5 w-3.5" />
              Processing (Gemini Free Tier)...
            </span>
          )}

          {isFailed && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono text-rose-300 bg-rose-950/60 border border-rose-500/40">
              <AlertCircle className="h-3.5 w-3.5" />
              Extraction Unavailable
            </span>
          )}
        </div>
      </div>

      {/* Extracted Metadata Grid */}
      {isCompleted && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
            <span className="text-slate-500 block">Invoice Date</span>
            <span className="font-mono text-slate-200 font-medium mt-0.5 block">
              {invoice.invoice_date || invoice.extraction?.invoice_date || 'N/A'}
            </span>
          </div>

          <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
            <span className="text-slate-500 block">Dealer GSTIN</span>
            <span className="font-mono text-cyan-300 font-medium mt-0.5 block">
              {invoice.dealer_gstin || invoice.extraction?.dealer_gstin || 'N/A'}
            </span>
          </div>

          <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
            <span className="text-slate-500 block">Customer Name</span>
            <span className="text-slate-200 font-medium mt-0.5 block truncate">
              {invoice.customer_name || invoice.extraction?.customer_name || 'N/A'}
            </span>
          </div>

          <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
            <span className="text-slate-500 block">Invoiced Total</span>
            <span className="font-mono text-slate-100 font-bold text-sm mt-0.5 block">
              ₹{(invoice.total_amount || invoice.extraction?.total_amount || 0).toLocaleString('en-IN')}
            </span>
          </div>
        </div>
      )}

      {/* Line Items Table */}
      {isCompleted && items.length > 0 && (
        <div className="space-y-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block font-mono">
            Itemized Equipment & Serials ({items.length})
          </span>
          <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-950/60">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-900/80 text-[11px] uppercase font-semibold text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-3 py-2">Product / Description</th>
                  <th className="px-3 py-2">HSN</th>
                  <th className="px-3 py-2 text-right">Qty</th>
                  <th className="px-3 py-2 text-right">Unit Rate</th>
                  <th className="px-3 py-2 text-right">Line Total</th>
                  <th className="px-3 py-2">Extracted Serial(s)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {items.map((item: any, idx: number) => {
                  const serials = item.serial_numbers || (item.serial_number ? [item.serial_number] : []);
                  return (
                    <tr key={idx} className="hover:bg-slate-900/40">
                      <td className="px-3 py-2.5 font-sans font-medium text-slate-200">
                        {item.product_name || item.description || 'Equipment Item'}
                      </td>
                      <td className="px-3 py-2.5 text-slate-400">{item.hsn_code || '—'}</td>
                      <td className="px-3 py-2.5 text-right text-slate-300">{item.quantity ?? 1}</td>
                      <td className="px-3 py-2.5 text-right text-slate-200">
                        ₹{(item.unit_price || 0).toLocaleString('en-IN')}
                      </td>
                      <td className="px-3 py-2.5 text-right font-bold text-slate-100">
                        ₹{(item.total_amount || (item.unit_price || 0) * (item.quantity || 1)).toLocaleString('en-IN')}
                      </td>
                      <td className="px-3 py-2.5 font-mono text-purple-300">
                        {serials.length > 0 ? (
                          serials.map((s: string) => (
                            <span key={s} className="inline-block bg-purple-950/60 border border-purple-500/40 rounded px-1.5 py-0.5 text-[10px] mr-1">
                              {s}
                            </span>
                          ))
                        ) : (
                          <span className="text-slate-500 italic font-sans text-[11px]">None visible</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Error state if failed */}
      {isFailed && (
        <div className="p-3 bg-rose-950/30 border border-rose-500/30 rounded-lg text-xs text-rose-300 flex items-start gap-2">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-400 mt-0.5" />
          <div>
            <span className="font-semibold block">Extraction Notice:</span>
            {invoice.error_message || 'Invoice extraction unavailable. Original document preserved in storage.'}
          </div>
        </div>
      )}

      {/* Footer Info */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-800 text-[11px] text-slate-500">
        <span>* Fact extraction performed via Gemini Free Tier. Deterministic verification occurs in subsequent rules.</span>
        {invoice.download_url && (
          <a
            href={invoice.download_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-indigo-400 hover:text-indigo-300 transition-colors font-medium"
          >
            <Download className="h-3.5 w-3.5" />
            View Original Document
          </a>
        )}
      </div>
    </div>
  );
};

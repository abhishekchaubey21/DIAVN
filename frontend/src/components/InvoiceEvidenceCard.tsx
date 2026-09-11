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
    <div className="rounded-2xl border border-[#E5E9F2] bg-white p-6 shadow-xs space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-[#E5E9F2] pb-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-[#4F6EF7]/10 border border-[#4F6EF7]/20 text-[#4F6EF7] flex items-center justify-center font-bold">
            <Receipt className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-bold text-[#182033]">
                {invoice.invoice_number ? `Invoice #${invoice.invoice_number}` : (invoice.original_filename || 'Invoice Document')}
              </h4>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-[#F1F4FA] text-[#68738A] border border-[#E5E9F2]">
                {invoice.original_filename}
              </span>
            </div>
            <div className="flex items-center gap-2 mt-1">
              <span className="inline-flex items-center gap-1 text-[10px] font-bold text-[#B45309] bg-[#FFFBEB] border border-[#FDE68A] px-2 py-0.5 rounded-md uppercase">
                <Sparkles className="h-3 w-3" />
                AI-Extracted Evidence
              </span>
              <span className="inline-flex items-center text-[10px] font-bold text-[#68738A] bg-[#F8FAFD] border border-[#E5E9F2] px-2 py-0.5 rounded-md">
                Deterministic Audit Required
              </span>
            </div>
          </div>
        </div>

        {/* Extraction Status & Confidence */}
        <div className="flex items-center gap-2.5">
          {isCompleted && (
            <div className="text-right">
              <span className="text-[10px] uppercase tracking-wider font-bold text-[#8E99AD] block">
                Model Confidence
              </span>
              <span className="text-xs font-mono font-bold text-[#065F46] bg-[#ECFDF5] border border-[#A7F3D0] px-2.5 py-0.5 rounded-md">
                {((invoice.extraction_confidence ?? 0.95) * 100).toFixed(0)}%
              </span>
            </div>
          )}

          {isProcessing && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono text-[#0369A1] bg-[#E0F2FE] border border-[#BAE6FD] animate-pulse">
              <Clock className="h-3.5 w-3.5" />
              Processing (Gemini)...
            </span>
          )}

          {isFailed && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono text-[#991B1B] bg-[#FEF2F2] border border-[#FECACA]">
              <AlertCircle className="h-3.5 w-3.5" />
              Extraction Unavailable
            </span>
          )}
        </div>
      </div>

      {/* Extracted Metadata Grid */}
      {isCompleted && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="p-3 rounded-xl bg-[#F8FAFD] border border-[#E5E9F2]">
            <span className="text-[#8E99AD] font-bold uppercase text-[10px] tracking-wider block">Invoice Date</span>
            <span className="font-mono text-[#182033] font-bold mt-1 block">
              {invoice.invoice_date || invoice.extraction?.invoice_date || 'N/A'}
            </span>
          </div>

          <div className="p-3 rounded-xl bg-[#F8FAFD] border border-[#E5E9F2]">
            <span className="text-[#8E99AD] font-bold uppercase text-[10px] tracking-wider block">Dealer GSTIN</span>
            <span className="font-mono text-[#4F6EF7] font-bold mt-1 block">
              {invoice.dealer_gstin || invoice.extraction?.dealer_gstin || 'N/A'}
            </span>
          </div>

          <div className="p-3 rounded-xl bg-[#F8FAFD] border border-[#E5E9F2]">
            <span className="text-[#8E99AD] font-bold uppercase text-[10px] tracking-wider block">Customer Name</span>
            <span className="text-[#182033] font-semibold mt-1 block truncate">
              {invoice.customer_name || invoice.extraction?.customer_name || 'N/A'}
            </span>
          </div>

          <div className="p-3 rounded-xl bg-[#F8FAFD] border border-[#E5E9F2]">
            <span className="text-[#8E99AD] font-bold uppercase text-[10px] tracking-wider block">Declared Total</span>
            <span className="font-mono text-[#182033] font-extrabold text-sm mt-1 block">
              ₹{(invoice.total_amount || invoice.extraction?.total_amount || 0).toLocaleString('en-IN')}
            </span>
          </div>
        </div>
      )}

      {/* Extracted Line Items Table */}
      {items && items.length > 0 && (
        <div className="space-y-2 pt-1">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold uppercase tracking-wider text-[#8E99AD] text-[10px]">
              Extracted Line Items ({items.length})
            </span>
          </div>

          <div className="overflow-x-auto rounded-xl border border-[#E5E9F2]">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#F8FAFD] text-[10px] uppercase tracking-wider text-[#68738A] font-bold border-b border-[#E5E9F2]">
                <tr>
                  <th className="px-4 py-2.5">Item Description</th>
                  <th className="px-4 py-2.5">HSN Code</th>
                  <th className="px-4 py-2.5 text-center">Qty</th>
                  <th className="px-4 py-2.5 text-right">Unit Price</th>
                  <th className="px-4 py-2.5 text-right">Total Amount</th>
                  <th className="px-4 py-2.5">Extracted Serials</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E5E9F2] bg-white">
                {items.map((item: LineItem, idx: number) => (
                  <tr key={idx} className="hover:bg-[#F8FAFD]">
                    <td className="px-4 py-3 font-semibold text-[#182033]">
                      {item.product_name || item.description || `Item #${idx + 1}`}
                    </td>
                    <td className="px-4 py-3 font-mono text-[#68738A]">
                      {item.hsn_code || '—'}
                    </td>
                    <td className="px-4 py-3 text-center font-mono font-bold text-[#182033]">
                      {item.quantity ?? 1}
                    </td>
                    <td className="px-4 py-3 text-right font-mono font-semibold text-[#182033]">
                      ₹{(item.unit_price ?? item.total_amount ?? 0).toLocaleString('en-IN')}
                    </td>
                    <td className="px-4 py-3 text-right font-mono font-bold text-[#182033]">
                      ₹{(item.total_amount ?? 0).toLocaleString('en-IN')}
                    </td>
                    <td className="px-4 py-3">
                      {item.serial_numbers && item.serial_numbers.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {item.serial_numbers.map((sn, sIdx) => (
                            <span key={sIdx} className="font-mono text-[10px] font-bold bg-[#F1F4FA] text-[#4F6EF7] px-1.5 py-0.5 rounded border border-[#E5E9F2]">
                              {sn}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-[#8E99AD] text-[11px]">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

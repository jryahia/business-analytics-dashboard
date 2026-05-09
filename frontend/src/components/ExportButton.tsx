import { useState, useRef, useEffect } from "react";
import { Download, FileText, Table, FileImage, ChevronDown, Loader2 } from "lucide-react";
import { exportApi } from "@/lib/api";
import { downloadBlob } from "@/lib/utils";
import { cn } from "@/lib/utils";

interface ExportButtonProps {
  onExportCsv?: () => void | Promise<void>;
  onExportExcel?: () => void | Promise<void>;
  onExportPdf?: () => void | Promise<void>;
  datasetId?: string;
  dashboardId?: string;
  label?: string;
}

interface Option {
  key: string;
  label: string;
  icon: React.ReactNode;
  handler: () => Promise<void>;
}

export default function ExportButton({
  onExportCsv,
  onExportExcel,
  onExportPdf,
  datasetId,
  dashboardId,
  label = "Export",
}: ExportButtonProps) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState<string | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function handleClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  async function run(key: string, fn: () => Promise<void>) {
    setLoading(key);
    setOpen(false);
    try {
      await fn();
    } finally {
      setLoading(null);
    }
  }

  const csvHandler = onExportCsv
    ? () => Promise.resolve(onExportCsv())
    : datasetId
    ? async () => {
        const res = await exportApi.datasetCsv(datasetId);
        downloadBlob(res.data as Blob, `export-${datasetId}.csv`);
      }
    : null;

  const excelHandler = onExportExcel
    ? () => Promise.resolve(onExportExcel())
    : datasetId
    ? async () => {
        const res = await exportApi.datasetExcel(datasetId);
        downloadBlob(res.data as Blob, `export-${datasetId}.xlsx`);
      }
    : null;

  const pdfHandler = onExportPdf
    ? () => Promise.resolve(onExportPdf())
    : dashboardId
    ? async () => {
        const res = await exportApi.dashboardPdf(dashboardId);
        downloadBlob(res.data as Blob, `dashboard-${dashboardId}.pdf`);
      }
    : null;

  const options: Option[] = [
    csvHandler && {
      key: "csv",
      label: "Export as CSV",
      icon: <Table className="w-4 h-4" />,
      handler: () => run("csv", csvHandler),
    },
    excelHandler && {
      key: "excel",
      label: "Export as Excel",
      icon: <FileText className="w-4 h-4" />,
      handler: () => run("excel", excelHandler),
    },
    pdfHandler && {
      key: "pdf",
      label: "Export as PDF",
      icon: <FileImage className="w-4 h-4" />,
      handler: () => run("pdf", pdfHandler),
    },
  ].filter(Boolean) as Option[];

  if (options.length === 0) return null;

  if (options.length === 1) {
    const opt = options[0];
    return (
      <button
        className="btn-secondary flex items-center gap-2 text-sm"
        onClick={opt.handler}
        disabled={loading !== null}
      >
        {loading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Download className="w-4 h-4" />
        )}
        {label}
      </button>
    );
  }

  return (
    <div className="relative" ref={menuRef}>
      <button
        className={cn(
          "btn-secondary flex items-center gap-2 text-sm",
          loading && "opacity-70 pointer-events-none"
        )}
        onClick={() => setOpen((o) => !o)}
        disabled={loading !== null}
      >
        {loading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Download className="w-4 h-4" />
        )}
        {label}
        <ChevronDown className={cn("w-3.5 h-3.5 transition-transform", open && "rotate-180")} />
      </button>

      {open && (
        <div className="absolute right-0 mt-1 w-48 bg-dark-800 border border-dark-700 rounded-lg shadow-xl z-20 py-1 overflow-hidden">
          {options.map((opt) => (
            <button
              key={opt.key}
              className="w-full flex items-center gap-3 px-3 py-2 text-sm text-dark-200 hover:bg-dark-700 hover:text-dark-100 transition-colors"
              onClick={opt.handler}
            >
              <span className="text-dark-400">{opt.icon}</span>
              {opt.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

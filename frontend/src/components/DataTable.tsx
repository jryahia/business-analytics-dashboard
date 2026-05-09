import { useState, useMemo } from "react";
import { ChevronUp, ChevronDown, ChevronsUpDown, ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

type Row = Record<string, unknown>;

interface ColumnDef {
  key: string;
  label: string;
  sortable?: boolean;
  render?: (value: unknown, row: Row) => React.ReactNode;
}

type ColumnInput = string | ColumnDef;

interface DataTableProps {
  columns: ColumnInput[];
  data?: Row[];
  rows?: Row[];
  pageSize?: number;
}

function normalizeColumns(cols: ColumnInput[]): ColumnDef[] {
  return cols.map((col) =>
    typeof col === "string"
      ? { key: col, label: col, sortable: true }
      : { sortable: true, ...col }
  );
}

function cellValue(raw: unknown): string {
  if (raw === null || raw === undefined) return "—";
  if (typeof raw === "boolean") return raw ? "true" : "false";
  if (typeof raw === "object") return JSON.stringify(raw);
  return String(raw);
}

type SortDir = "asc" | "desc" | null;

export default function DataTable({ columns, data, rows, pageSize = 20 }: DataTableProps) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>(null);
  const [page, setPage] = useState(0);

  const cols = useMemo(() => normalizeColumns(columns), [columns]);
  const allRows = data ?? rows ?? [];

  const sorted = useMemo(() => {
    if (!sortKey || !sortDir) return allRows;
    return [...allRows].sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      const an = typeof av === "number" ? av : NaN;
      const bn = typeof bv === "number" ? bv : NaN;
      let cmp: number;
      if (!isNaN(an) && !isNaN(bn)) {
        cmp = an - bn;
      } else {
        cmp = String(av ?? "").localeCompare(String(bv ?? ""));
      }
      return sortDir === "asc" ? cmp : -cmp;
    });
  }, [allRows, sortKey, sortDir]);

  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize));
  const safePage = Math.min(page, totalPages - 1);
  const pageRows = sorted.slice(safePage * pageSize, safePage * pageSize + pageSize);

  function handleSort(key: string) {
    if (sortKey !== key) {
      setSortKey(key);
      setSortDir("asc");
    } else if (sortDir === "asc") {
      setSortDir("desc");
    } else if (sortDir === "desc") {
      setSortKey(null);
      setSortDir(null);
    }
    setPage(0);
  }

  function SortIcon({ col }: { col: ColumnDef }) {
    if (!col.sortable) return null;
    if (sortKey !== col.key)
      return <ChevronsUpDown className="w-3.5 h-3.5 text-dark-600 group-hover:text-dark-400" />;
    if (sortDir === "asc") return <ChevronUp className="w-3.5 h-3.5 text-brand-400" />;
    return <ChevronDown className="w-3.5 h-3.5 text-brand-400" />;
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="overflow-x-auto rounded-lg border border-dark-700">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-dark-700 bg-dark-900/60">
              {cols.map((col) => (
                <th
                  key={col.key}
                  className={cn(
                    "px-3 py-2.5 text-left text-xs font-semibold text-dark-400 uppercase tracking-wide whitespace-nowrap",
                    col.sortable && "cursor-pointer select-none group hover:text-dark-200 transition-colors"
                  )}
                  onClick={() => col.sortable && handleSort(col.key)}
                >
                  <span className="flex items-center gap-1">
                    {col.label}
                    <SortIcon col={col} />
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.length === 0 ? (
              <tr>
                <td
                  colSpan={cols.length}
                  className="px-3 py-8 text-center text-dark-500 text-sm"
                >
                  No data
                </td>
              </tr>
            ) : (
              pageRows.map((row, i) => (
                <tr
                  key={i}
                  className="border-b border-dark-700/50 hover:bg-dark-700/30 transition-colors"
                >
                  {cols.map((col) => (
                    <td
                      key={col.key}
                      className="px-3 py-2 text-dark-200 whitespace-nowrap max-w-[240px] truncate"
                      title={cellValue(row[col.key])}
                    >
                      {col.render ? col.render(row[col.key], row) : cellValue(row[col.key])}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between px-1 text-sm text-dark-400">
          <span>
            Showing {safePage * pageSize + 1}–{Math.min(safePage * pageSize + pageSize, sorted.length)} of{" "}
            {sorted.length.toLocaleString()} rows
          </span>
          <div className="flex items-center gap-1">
            <button
              className="p-1.5 rounded-md hover:bg-dark-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={safePage === 0}
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            {Array.from({ length: Math.min(7, totalPages) }, (_, i) => {
              let pageNum: number;
              if (totalPages <= 7) {
                pageNum = i;
              } else if (safePage < 4) {
                pageNum = i < 5 ? i : i === 5 ? -1 : totalPages - 1;
              } else if (safePage > totalPages - 5) {
                pageNum = i === 0 ? 0 : i === 1 ? -1 : totalPages - 7 + i;
              } else {
                pageNum =
                  i === 0 ? 0 : i === 1 ? -1 : i === 5 ? -1 : i === 6 ? totalPages - 1 : safePage + i - 3;
              }
              if (pageNum === -1)
                return (
                  <span key={`ellipsis-${i}`} className="px-1 text-dark-600">
                    …
                  </span>
                );
              return (
                <button
                  key={pageNum}
                  className={cn(
                    "min-w-[28px] h-7 px-1 rounded-md text-xs font-medium transition-colors",
                    pageNum === safePage
                      ? "bg-brand-500 text-white"
                      : "hover:bg-dark-700 text-dark-400 hover:text-dark-100"
                  )}
                  onClick={() => setPage(pageNum)}
                >
                  {pageNum + 1}
                </button>
              );
            })}
            <button
              className="p-1.5 rounded-md hover:bg-dark-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={safePage === totalPages - 1}
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

interface KPICardProps {
  title: string;
  value: string | number;
  prefix?: string;
  suffix?: string;
  trend?: number;
  icon?: string;
  color?: "brand" | "success" | "warning" | "danger" | "default";
}

const colorMap = {
  brand: { bg: "bg-brand-500/10", text: "text-brand-400", border: "border-brand-500/20" },
  success: { bg: "bg-success/10", text: "text-success", border: "border-success/20" },
  warning: { bg: "bg-warning/10", text: "text-warning", border: "border-warning/20" },
  danger: { bg: "bg-danger/10", text: "text-danger", border: "border-danger/20" },
  default: { bg: "bg-dark-700", text: "text-dark-100", border: "border-dark-600" },
} as const;

export default function KPICard({
  title,
  value,
  prefix,
  suffix,
  trend,
  icon,
  color = "brand",
}: KPICardProps) {
  const colors = colorMap[color] ?? colorMap.default;
  const hasTrend = trend !== undefined;
  const isPositive = hasTrend && trend > 0;
  const isNegative = hasTrend && trend < 0;

  return (
    <div
      className={cn(
        "bg-dark-800/60 backdrop-blur-sm border rounded-xl p-4 hover:bg-dark-800/80 transition-all",
        colors.border
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          {icon && (
            <div
              className={cn(
                "w-11 h-11 rounded-xl flex items-center justify-center text-xl shrink-0",
                colors.bg
              )}
            >
              {icon}
            </div>
          )}
          <div className="min-w-0">
            <p className="text-sm text-dark-400 font-medium truncate">{title}</p>
            <p className={cn("text-2xl font-bold mt-0.5 leading-none", colors.text)}>
              {prefix && (
                <span className="text-base font-semibold text-dark-300 mr-0.5">{prefix}</span>
              )}
              {typeof value === "number" ? value.toLocaleString() : value}
              {suffix && (
                <span className="text-base font-semibold text-dark-300 ml-0.5">{suffix}</span>
              )}
            </p>
          </div>
        </div>

        {hasTrend && (
          <div
            className={cn(
              "flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-full shrink-0",
              isPositive && "bg-success/10 text-success",
              isNegative && "bg-danger/10 text-danger",
              !isPositive && !isNegative && "bg-dark-700 text-dark-400"
            )}
          >
            {isPositive ? (
              <TrendingUp className="w-3 h-3" />
            ) : isNegative ? (
              <TrendingDown className="w-3 h-3" />
            ) : (
              <Minus className="w-3 h-3" />
            )}
            <span>{Math.abs(trend).toFixed(1)}%</span>
          </div>
        )}
      </div>
    </div>
  );
}

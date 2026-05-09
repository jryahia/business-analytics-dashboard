import { useState } from "react";
import Plot from "react-plotly.js";
import { Maximize2, X } from "lucide-react";
import type { Chart } from "@/lib/api";

interface ChartCardProps {
  chart: Chart;
}

const CHART_TYPE_LABELS: Record<string, string> = {
  bar: "Bar",
  line: "Line",
  pie: "Pie",
  scatter: "Scatter",
  area: "Area",
  heatmap: "Heatmap",
  histogram: "Histogram",
  box: "Box Plot",
};

const darkBase = {
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
  font: { color: "#94a3b8", family: "Inter, system-ui, sans-serif", size: 11 },
  xaxis: {
    gridcolor: "#334155",
    linecolor: "#475569",
    zerolinecolor: "#334155",
    tickcolor: "#475569",
  },
  yaxis: {
    gridcolor: "#334155",
    linecolor: "#475569",
    zerolinecolor: "#334155",
    tickcolor: "#475569",
  },
  legend: { bgcolor: "rgba(0,0,0,0)", bordercolor: "#334155", font: { color: "#94a3b8" } },
};

function buildLayout(
  base: Record<string, unknown>,
  margin: { t: number; r: number; b: number; l: number }
): Record<string, unknown> {
  const incoming = (base as Record<string, unknown>) ?? {};
  return {
    ...darkBase,
    ...incoming,
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    margin,
    font: { ...darkBase.font, ...((incoming.font as object) ?? {}) },
    xaxis: { ...darkBase.xaxis, ...((incoming.xaxis as object) ?? {}) },
    yaxis: { ...darkBase.yaxis, ...((incoming.yaxis as object) ?? {}) },
    legend: { ...darkBase.legend, ...((incoming.legend as object) ?? {}) },
  };
}

export default function ChartCard({ chart }: ChartCardProps) {
  const [fullscreen, setFullscreen] = useState(false);

  const plotData = ((chart.plotly_json?.data as unknown[]) ?? []) as Parameters<
    typeof Plot
  >[0]["data"];
  const rawLayout = (chart.plotly_json?.layout ?? {}) as Record<string, unknown>;
  const typeLabel = CHART_TYPE_LABELS[chart.chart_type] ?? chart.chart_type;

  const cardLayout = buildLayout(rawLayout, { t: 16, r: 8, b: 36, l: 42 });
  const fullLayout = buildLayout(rawLayout, { t: 24, r: 16, b: 48, l: 56 });

  return (
    <>
      <div className="card flex flex-col h-80">
        <div className="flex items-center justify-between mb-2 shrink-0">
          <div className="flex items-center gap-2 min-w-0">
            <h3 className="font-semibold text-dark-100 text-sm truncate">{chart.title}</h3>
            <span className="text-xs bg-brand-500/10 text-brand-400 px-2 py-0.5 rounded-full border border-brand-500/20 shrink-0">
              {typeLabel}
            </span>
          </div>
          <button
            className="p-1.5 text-dark-400 hover:text-dark-100 hover:bg-dark-700 rounded-md transition-colors shrink-0"
            onClick={() => setFullscreen(true)}
            title="Fullscreen"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 min-h-0">
          <Plot
            data={plotData}
            layout={cardLayout as Parameters<typeof Plot>[0]["layout"]}
            config={{ responsive: true, displayModeBar: false }}
            style={{ width: "100%", height: "100%" }}
            useResizeHandler
          />
        </div>
      </div>

      {fullscreen && (
        <div
          className="fixed inset-0 z-50 bg-dark-950/90 backdrop-blur-sm flex items-center justify-center p-6"
          onClick={(e) => e.target === e.currentTarget && setFullscreen(false)}
        >
          <div
            className="bg-dark-800 border border-dark-700 rounded-xl flex flex-col w-full max-w-5xl"
            style={{ height: "82vh" }}
          >
            <div className="flex items-center justify-between px-5 py-3 border-b border-dark-700 shrink-0">
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-dark-100">{chart.title}</h3>
                <span className="text-xs bg-brand-500/10 text-brand-400 px-2 py-0.5 rounded-full border border-brand-500/20">
                  {typeLabel}
                </span>
              </div>
              <button
                className="p-1.5 text-dark-400 hover:text-dark-100 hover:bg-dark-700 rounded-md transition-colors"
                onClick={() => setFullscreen(false)}
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="flex-1 min-h-0 p-4">
              <Plot
                data={plotData}
                layout={fullLayout as Parameters<typeof Plot>[0]["layout"]}
                config={{ responsive: true, displayModeBar: true, displaylogo: false }}
                style={{ width: "100%", height: "100%" }}
                useResizeHandler
              />
            </div>
          </div>
        </div>
      )}
    </>
  );
}

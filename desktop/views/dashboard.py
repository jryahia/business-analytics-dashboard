import flet as ft
from api_client import APIClient, APIError
from widgets.kpi_card import build_kpi_card
from widgets.chart_card import build_chart_card, build_empty_chart_state

BG = "#0d1117"
SURFACE = "#161b22"
TEXT = "#e6edf3"
TEXT_DIM = "#8b949e"
PRIMARY = "#58a6ff"
SUCCESS = "#3fb950"
WARNING = "#d29922"
ERROR = "#f85149"
BORDER = "#21262d"

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
CATEGORIES = ["Electronics", "Clothing", "Home", "Sports"]
CAT_COLORS = [PRIMARY, SUCCESS, WARNING, ERROR]


def _build_revenue_line_chart(series: list) -> ft.Control:
    max_val = max(p["value"] for p in series) if series else 100000
    data_points = [
        ft.LineChartDataPoint(x=float(i), y=float(p["value"]))
        for i, p in enumerate(series)
    ]
    return ft.LineChart(
        expand=True,
        min_y=0,
        max_y=float(max_val * 1.15),
        min_x=0,
        max_x=float(len(series) - 1),
        tooltip_bgcolor=ft.colors.with_opacity(0.85, "#1e2130"),
        data_series=[
            ft.LineChartData(
                data_points=data_points,
                stroke_width=2.5,
                color=PRIMARY,
                curved=True,
                stroke_cap_round=True,
                below_line_bgcolor=ft.colors.with_opacity(0.08, PRIMARY),
            )
        ],
        left_axis=ft.ChartAxis(
            labels_size=40,
            labels=[
                ft.ChartAxisLabel(
                    value=float(max_val * i / 4),
                    label=ft.Text(f"${int(max_val * i / 4 / 1000)}k", size=10, color=TEXT_DIM),
                )
                for i in range(5)
            ],
        ),
        bottom_axis=ft.ChartAxis(
            labels_size=28,
            labels=[
                ft.ChartAxisLabel(value=float(i), label=ft.Text(p["month"], size=10, color=TEXT_DIM))
                for i, p in enumerate(series)
            ],
        ),
        grid_data=ft.ChartGridData(
            horizontal_interval=float(max_val / 4),
            horizontal_color=ft.colors.with_opacity(0.12, "#ffffff"),
        ),
    )


def _build_category_bar_chart(data: list) -> ft.Control:
    max_val = max(d["value"] for d in data) if data else 100
    return ft.BarChart(
        expand=True,
        max_y=float(max_val * 1.2),
        groups_space=20,
        bar_groups=[
            ft.BarChartGroup(
                x=i,
                bar_rods=[
                    ft.BarChartRod(
                        from_y=0,
                        to_y=float(d["value"]),
                        width=32,
                        color=CAT_COLORS[i % len(CAT_COLORS)],
                        border_radius=ft.border_radius.only(top_left=4, top_right=4),
                        tooltip=f'{d["category"]}: {d["value"]}%',
                    )
                ],
            )
            for i, d in enumerate(data)
        ],
        bottom_axis=ft.ChartAxis(
            labels_size=30,
            labels=[
                ft.ChartAxisLabel(value=float(i), label=ft.Text(d["category"][:6], size=10, color=TEXT_DIM))
                for i, d in enumerate(data)
            ],
        ),
        left_axis=ft.ChartAxis(
            labels_size=36,
            labels=[
                ft.ChartAxisLabel(value=float(max_val * i / 4), label=ft.Text(f"{int(max_val * i / 4)}%", size=10, color=TEXT_DIM))
                for i in range(5)
            ],
        ),
        grid_data=ft.ChartGridData(
            horizontal_interval=float(max_val / 4),
            horizontal_color=ft.colors.with_opacity(0.12, "#ffffff"),
        ),
    )


def _build_distribution_pie_chart(data: list) -> ft.Control:
    total = sum(d["value"] for d in data)
    return ft.PieChart(
        expand=True,
        sections_space=3,
        center_space_radius=50,
        sections=[
            ft.PieChartSection(
                value=float(d["value"]),
                title=f'{int(d["value"] / total * 100)}%',
                title_style=ft.TextStyle(size=12, color="#ffffff", weight=ft.FontWeight.BOLD),
                color=CAT_COLORS[i % len(CAT_COLORS)],
                radius=80,
            )
            for i, d in enumerate(data)
        ],
    )


def _fetch_data(api: APIClient):
    try:
        kpis = api.get_kpis()
    except APIError:
        kpis = api.get_mock_kpis()

    try:
        revenue = api.get_mock_revenue_series()
    except APIError:
        revenue = api.get_mock_revenue_series()

    try:
        categories = api.get_mock_category_sales()
    except APIError:
        categories = api.get_mock_category_sales()

    return kpis, revenue, categories


class DashboardView:
    def __init__(self, api: APIClient, page: ft.Page):
        self.api = api
        self.page = page

    def build(self) -> ft.Control:
        kpis, revenue, categories = _fetch_data(self.api)

        kpi_icon_map = {"attach_money": "attach_money", "people": "people", "trending_up": "trending_up", "shopping_cart": "shopping_cart"}
        kpi_row = ft.Row(
            wrap=True,
            spacing=16,
            run_spacing=16,
            controls=[
                build_kpi_card(
                    title=k["title"],
                    value=k["value"],
                    change=k["change"],
                    trend=k["trend"],
                    icon_name=kpi_icon_map.get(k.get("icon", "bar_chart"), "bar_chart"),
                )
                for k in kpis
            ],
        )

        revenue_chart = build_chart_card(
            title="Revenue Over Time",
            subtitle="Monthly revenue for the past year",
            chart=_build_revenue_line_chart(revenue),
            height=260,
            expand=True,
        )

        sales_chart = build_chart_card(
            title="Sales by Category",
            subtitle="Distribution across product categories",
            chart=_build_category_bar_chart(categories),
            height=260,
            expand=True,
        )

        dist_chart = build_chart_card(
            title="Category Share",
            subtitle="Percentage breakdown",
            chart=_build_distribution_pie_chart(categories),
            height=260,
        )

        recent_rows = []
        for ds in self.api.get_mock_datasets()[:4]:
            status_color = SUCCESS if ds["status"] == "active" else WARNING if ds["status"] == "syncing" else ERROR
            recent_rows.append(
                ft.Container(
                    padding=ft.padding.symmetric(vertical=10, horizontal=4),
                    border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.icons.TABLE_CHART_OUTLINED, size=16, color=PRIMARY),
                            ft.Text(ds["name"], size=13, color=TEXT, expand=True),
                            ft.Text(f'{ds["rows"]:,} rows', size=12, color=TEXT_DIM),
                            ft.Container(width=8),
                            ft.Container(
                                width=8, height=8, border_radius=4, bgcolor=status_color,
                            ),
                        ],
                    ),
                )
            )

        recent_datasets = ft.Container(
            padding=ft.padding.all(20),
            border_radius=12,
            bgcolor="#1e2130",
            border=ft.border.all(1, "#2d3250"),
            width=320,
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Text("Recent Datasets", size=15, color=TEXT, weight=ft.FontWeight.W_600),
                    ft.Container(height=12),
                    *recent_rows,
                ],
            ),
        )

        return ft.Container(
            expand=True,
            bgcolor=BG,
            padding=ft.padding.all(28),
            content=ft.Column(
                scroll=ft.ScrollMode.AUTO,
                spacing=24,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=4,
                                controls=[
                                    ft.Text("Dashboard", size=24, color=TEXT, weight=ft.FontWeight.BOLD),
                                    ft.Text("Welcome back. Here's what's happening.", size=13, color=TEXT_DIM),
                                ],
                            ),
                            ft.Text("May 9, 2026", size=13, color=TEXT_DIM),
                        ],
                    ),
                    kpi_row,
                    ft.Row(
                        spacing=16,
                        alignment=ft.MainAxisAlignment.START,
                        controls=[revenue_chart, sales_chart],
                        expand=True,
                    ),
                    ft.Row(
                        spacing=16,
                        controls=[dist_chart, recent_datasets],
                    ),
                ],
            ),
        )

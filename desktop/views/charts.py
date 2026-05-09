"""Charts view for the Flet desktop app."""

import flet as ft
from typing import Callable

from desktop.api_client import ApiClient
from desktop.widgets.chart_card import ChartCard


class ChartsView(ft.Container):
    """View for creating, editing, and managing charts."""

    def __init__(self, api_client: ApiClient, navigate: Callable):
        super().__init__()
        self.api_client = api_client
        self.navigate = navigate
        self.charts = []
        self.datasets = []
        self.loading = ft.ProgressRing(visible=False)

        self.chart_name = ft.TextField(
            label="Chart Name",
            hint_text="e.g. Monthly Revenue",
            border_color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
            color=ft.Colors.WHITE,
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
        )
        self.chart_type = ft.Dropdown(
            label="Chart Type",
            options=[
                ft.dropdown.Option("line", "Line Chart"),
                ft.dropdown.Option("bar", "Bar Chart"),
                ft.dropdown.Option("pie", "Pie Chart"),
                ft.dropdown.Option("scatter", "Scatter Plot"),
                ft.dropdown.Option("area", "Area Chart"),
                ft.dropdown.Option("heatmap", "Heatmap"),
            ],
            value="bar",
            border_color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
            color=ft.Colors.WHITE,
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
        )
        self.dataset_select = ft.Dropdown(
            label="Dataset",
            border_color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
            color=ft.Colors.WHITE,
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
        )
        self.x_axis = ft.TextField(
            label="X-Axis Column",
            hint_text="e.g. date",
            border_color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
            color=ft.Colors.WHITE,
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
        )
        self.y_axis = ft.TextField(
            label="Y-Axis Column",
            hint_text="e.g. revenue",
            border_color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
            color=ft.Colors.WHITE,
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
        )
        self.group_by = ft.TextField(
            label="Group By (optional)",
            hint_text="e.g. region",
            border_color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
            color=ft.Colors.WHITE,
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
        )
        self.status_text = ft.Text("", color=ft.Colors.GREEN_400, size=14)

        self.chart_grid = ft.GridView(
            runs_count=3,
            max_extent=380,
            spacing=15,
            run_spacing=15,
            padding=0,
        )

        # Create dialog
        self.create_dialog = ft.AlertDialog(
            title=ft.Text("Create Chart", color=ft.Colors.WHITE),
            bgcolor=ft.Colors.with_opacity(0.95, ft.Colors.GREY_900),
            content=ft.Container(
                width=500,
                padding=20,
                content=ft.Column(
                    spacing=15,
                    controls=[
                        self.chart_name,
                        self.chart_type,
                        self.dataset_select,
                        self.x_axis,
                        self.y_axis,
                        self.group_by,
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancel", on_click=self._close_dialog),
                ft.FilledButton(
                    "Create",
                    style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE),
                    on_click=self._create_chart,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.content = ft.Container(
            padding=30,
            content=ft.Column(
                spacing=20,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("📊 Charts", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ft.Container(expand=True),
                            ft.FilledButton(
                                "New Chart",
                                icon=ft.Icons.ADD,
                                style=ft.ButtonStyle(
                                    color=ft.Colors.WHITE,
                                    bgcolor=ft.Colors.BLUE_700,
                                ),
                                on_click=self._open_create_dialog,
                            ),
                            self.loading,
                        ]
                    ),
                    ft.Text(
                        "Create and manage visualizations for your dashboards.",
                        size=14,
                        color=ft.Colors.GREY_400,
                    ),
                    self.status_text,
                    ft.Divider(color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
                    self.chart_grid,
                ],
            ),
        )

    def did_mount(self):
        self._load_datasets()
        self._load_charts()

    def _load_datasets(self):
        try:
            result = self.api_client.get("/api/datasets")
            self.datasets = result if isinstance(result, list) else []
            self.dataset_select.options = [
                ft.dropdown.Option(d.get("id"), d.get("name", f"Dataset {i+1}"))
                for i, d in enumerate(self.datasets)
            ]
        except Exception:
            self.datasets = []

    def _load_charts(self):
        self.loading.visible = True
        self.update()
        try:
            result = self.api_client.get("/api/charts")
            self.charts = result if isinstance(result, list) else []
        except Exception:
            self.charts = []
        self.loading.visible = False
        self._render_charts()
        self.update()

    def _render_charts(self):
        self.chart_grid.controls.clear()
        if not self.charts:
            self.chart_grid.controls.append(
                ft.Container(
                    padding=40,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                        controls=[
                            ft.Icon(ft.Icons.BAR_CHART, size=48, color=ft.Colors.GREY_600),
                            ft.Text("No charts yet.", size=16, color=ft.Colors.GREY_500),
                            ft.Text("Click 'New Chart' to create your first visualization.", size=13, color=ft.Colors.GREY_600),
                        ],
                    ),
                )
            )
            return
        for chart in self.charts:
            self.chart_grid.controls.append(
                ChartCard(
                    chart=chart,
                    on_delete=lambda c=chart: self._delete_chart(c),
                    on_edit=lambda c=chart: self._edit_chart(c),
                )
            )

    def _open_create_dialog(self, e):
        self.page.dialog = self.create_dialog
        self.create_dialog.open = True
        self.page.update()

    def _close_dialog(self, e):
        self.create_dialog.open = False
        self.page.update()

    def _create_chart(self, e):
        data = {
            "name": self.chart_name.value.strip(),
            "chart_type": self.chart_type.value,
            "dataset_id": self.dataset_select.value,
            "x_axis": self.x_axis.value.strip(),
            "y_axis": self.y_axis.value.strip(),
            "group_by": self.group_by.value.strip() or None,
        }
        if not data["name"] or not data["x_axis"] or not data["y_axis"]:
            self.status_text.value = "❌ Name, X-Axis, and Y-Axis are required"
            self.status_text.color = ft.Colors.RED_400
            self.update()
            return
        try:
            self.api_client.post("/api/charts", data)
            self._clear_form()
            self.create_dialog.open = False
            self.status_text.value = "✅ Chart created!"
            self.status_text.color = ft.Colors.GREEN_400
            self._load_charts()
        except Exception as ex:
            self.status_text.value = f"❌ Error: {str(ex)}"
            self.status_text.color = ft.Colors.RED_400
        self.update()

    def _delete_chart(self, chart):
        try:
            self.api_client.delete(f"/api/charts/{chart.get('id')}")
            self._load_charts()
        except Exception as ex:
            self.status_text.value = f"❌ Delete failed: {str(ex)}"
            self.status_text.color = ft.Colors.RED_400
            self.update()

    def _edit_chart(self, chart):
        self.chart_name.value = chart.get("name", "")
        self.chart_type.value = chart.get("chart_type", "bar")
        self.dataset_select.value = chart.get("dataset_id")
        self.x_axis.value = chart.get("x_axis", "")
        self.y_axis.value = chart.get("y_axis", "")
        self.group_by.value = chart.get("group_by", "")
        self._open_create_dialog(None)

    def _clear_form(self):
        self.chart_name.value = ""
        self.chart_type.value = "bar"
        self.dataset_select.value = None
        self.x_axis.value = ""
        self.y_axis.value = ""
        self.group_by.value = ""

import flet as ft
import os
import json
from api_client import APIClient, APIError

BG = "#0d1117"
SURFACE = "#161b22"
CARD = "#1e2130"
BORDER = "#2d3250"
BORDER_LIGHT = "#21262d"
TEXT = "#e6edf3"
TEXT_DIM = "#8b949e"
PRIMARY = "#58a6ff"
SUCCESS = "#3fb950"
WARNING = "#d29922"
ERROR = "#f85149"


def _status_badge(status: str) -> ft.Container:
    color_map = {"active": SUCCESS, "syncing": WARNING, "error": ERROR}
    color = color_map.get(status, TEXT_DIM)
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=8, vertical=3),
        border_radius=20,
        bgcolor=f"{color}22",
        border=ft.border.all(1, f"{color}55"),
        content=ft.Row(
            spacing=5,
            controls=[
                ft.Container(width=6, height=6, border_radius=3, bgcolor=color),
                ft.Text(status.capitalize(), size=11, color=color),
            ],
        ),
    )


def _row_action_buttons(dataset: dict, on_delete, on_export) -> ft.Row:
    return ft.Row(
        spacing=4,
        controls=[
            ft.IconButton(
                icon=ft.icons.DOWNLOAD_OUTLINED,
                icon_color=PRIMARY,
                icon_size=16,
                tooltip="Export CSV",
                on_click=lambda e, d=dataset: on_export(d),
            ),
            ft.IconButton(
                icon=ft.icons.DELETE_OUTLINE,
                icon_color=ERROR,
                icon_size=16,
                tooltip="Delete dataset",
                on_click=lambda e, d=dataset: on_delete(d),
            ),
        ],
    )


class DatasetsView:
    def __init__(self, api: APIClient, page: ft.Page):
        self.api = api
        self.page = page
        self._datasets = []
        self._search_query = ""
        self._table_ref = ft.Ref[ft.DataTable]()
        self._status_ref = ft.Ref[ft.Text]()

    def _load_datasets(self) -> list:
        try:
            return self.api.get_datasets()
        except APIError:
            return self.api.get_mock_datasets()

    def _filtered(self) -> list:
        q = self._search_query.lower()
        if not q:
            return self._datasets
        return [d for d in self._datasets if q in d["name"].lower() or q in d["source"].lower()]

    def _rebuild_rows(self) -> list[ft.DataRow]:
        rows = []
        for ds in self._filtered():
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Row(spacing=8, controls=[
                                ft.Icon(ft.icons.TABLE_CHART_OUTLINED, size=16, color=PRIMARY),
                                ft.Text(ds["name"], size=13, color=TEXT),
                            ])
                        ),
                        ft.DataCell(ft.Text(f'{ds["rows"]:,}', size=13, color=TEXT_DIM)),
                        ft.DataCell(ft.Text(str(ds["columns"]), size=13, color=TEXT_DIM)),
                        ft.DataCell(ft.Text(ds["source"], size=13, color=TEXT_DIM)),
                        ft.DataCell(ft.Text(ds["updated"], size=13, color=TEXT_DIM)),
                        ft.DataCell(_status_badge(ds["status"])),
                        ft.DataCell(
                            _row_action_buttons(
                                ds,
                                on_delete=self._on_delete,
                                on_export=self._on_export,
                            )
                        ),
                    ],
                )
            )
        return rows

    def _on_search(self, e):
        self._search_query = e.control.value or ""
        self._refresh_table()

    def _on_delete(self, dataset: dict):
        def confirm(e):
            dlg.open = False
            self.page.update()
            try:
                self.api.delete_dataset(dataset["id"])
            except APIError:
                pass
            self._datasets = [d for d in self._datasets if d["id"] != dataset["id"]]
            self._refresh_table()

        def cancel(e):
            dlg.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Delete Dataset", color=TEXT),
            content=ft.Text(f'Are you sure you want to delete "{dataset["name"]}"?', color=TEXT_DIM),
            bgcolor=CARD,
            actions=[
                ft.TextButton("Cancel", on_click=cancel, style=ft.ButtonStyle(color=TEXT_DIM)),
                ft.TextButton("Delete", on_click=confirm, style=ft.ButtonStyle(color=ERROR)),
            ],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _on_export(self, dataset: dict):
        try:
            data = self.api.export_dataset(dataset["id"], "csv")
            path = os.path.expanduser(f'~/Downloads/{dataset["name"].replace(" ", "_")}.csv')
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                f.write(data)
            self._show_snack(f'Exported to {path}', color=SUCCESS)
        except APIError:
            mock_rows = [
                "id,name,value,date",
                "1,Sample A,1234,2025-01-01",
                "2,Sample B,5678,2025-01-02",
            ]
            path = os.path.expanduser(f'~/Downloads/{dataset["name"].replace(" ", "_")}.csv')
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write("\n".join(mock_rows))
            self._show_snack(f'Exported mock data to {path}', color=WARNING)

    def _show_snack(self, message: str, color: str = SUCCESS):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color="#ffffff"),
            bgcolor=color,
            duration=3000,
        )
        self.page.snack_bar.open = True
        self.page.update()

    def _on_import(self, e):
        def pick_result(res: ft.FilePickerResultEvent):
            if res.files:
                name = res.files[0].name
                self._show_snack(f'Imported: {name}', color=SUCCESS)
                new_ds = {
                    "id": str(len(self._datasets) + 1),
                    "name": name.rsplit(".", 1)[0],
                    "rows": 0,
                    "columns": 0,
                    "source": "CSV Upload",
                    "updated": "Just now",
                    "status": "syncing",
                }
                self._datasets.append(new_ds)
                self._refresh_table()

        picker = ft.FilePicker(on_result=pick_result)
        self.page.overlay.append(picker)
        self.page.update()
        picker.pick_files(allowed_extensions=["csv", "xlsx", "json"])

    def _refresh_table(self):
        if self._table_ref.current:
            self._table_ref.current.rows = self._rebuild_rows()
            self._table_ref.current.update()

    def build(self) -> ft.Control:
        self._datasets = self._load_datasets()

        table = ft.DataTable(
            ref=self._table_ref,
            border_radius=8,
            column_spacing=20,
            heading_row_color=ft.colors.with_opacity(0.05, "#ffffff"),
            heading_row_height=44,
            data_row_min_height=52,
            data_row_max_height=56,
            divider_thickness=0.5,
            columns=[
                ft.DataColumn(ft.Text("Name", size=12, color=TEXT_DIM, weight=ft.FontWeight.W_600)),
                ft.DataColumn(ft.Text("Rows", size=12, color=TEXT_DIM, weight=ft.FontWeight.W_600), numeric=True),
                ft.DataColumn(ft.Text("Cols", size=12, color=TEXT_DIM, weight=ft.FontWeight.W_600), numeric=True),
                ft.DataColumn(ft.Text("Source", size=12, color=TEXT_DIM, weight=ft.FontWeight.W_600)),
                ft.DataColumn(ft.Text("Updated", size=12, color=TEXT_DIM, weight=ft.FontWeight.W_600)),
                ft.DataColumn(ft.Text("Status", size=12, color=TEXT_DIM, weight=ft.FontWeight.W_600)),
                ft.DataColumn(ft.Text("Actions", size=12, color=TEXT_DIM, weight=ft.FontWeight.W_600)),
            ],
            rows=self._rebuild_rows(),
        )

        return ft.Container(
            expand=True,
            bgcolor=BG,
            padding=ft.padding.all(28),
            content=ft.Column(
                spacing=24,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=4,
                                controls=[
                                    ft.Text("Datasets", size=24, color=TEXT, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"{len(self._datasets)} datasets available", size=13, color=TEXT_DIM),
                                ],
                            ),
                            ft.Row(
                                spacing=10,
                                controls=[
                                    ft.ElevatedButton(
                                        text="Import",
                                        icon=ft.icons.UPLOAD_OUTLINED,
                                        on_click=self._on_import,
                                        style=ft.ButtonStyle(
                                            bgcolor=SURFACE,
                                            color=TEXT,
                                            side=ft.BorderSide(1, BORDER),
                                            shape=ft.RoundedRectangleBorder(radius=8),
                                        ),
                                    ),
                                    ft.ElevatedButton(
                                        text="New Dataset",
                                        icon=ft.icons.ADD,
                                        style=ft.ButtonStyle(
                                            bgcolor=PRIMARY,
                                            color="#ffffff",
                                            shape=ft.RoundedRectangleBorder(radius=8),
                                        ),
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        border_radius=8,
                        bgcolor=SURFACE,
                        border=ft.border.all(1, BORDER_LIGHT),
                        content=ft.Row(
                            spacing=8,
                            controls=[
                                ft.Icon(ft.icons.SEARCH, size=16, color=TEXT_DIM),
                                ft.TextField(
                                    hint_text="Search datasets...",
                                    border=ft.InputBorder.NONE,
                                    expand=True,
                                    height=30,
                                    text_size=13,
                                    color=TEXT,
                                    hint_style=ft.TextStyle(color=TEXT_DIM),
                                    cursor_color=PRIMARY,
                                    on_change=self._on_search,
                                    content_padding=ft.padding.all(0),
                                ),
                            ],
                        ),
                    ),
                    ft.Container(
                        expand=True,
                        border_radius=12,
                        bgcolor=CARD,
                        border=ft.border.all(1, BORDER),
                        padding=ft.padding.all(0),
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                        content=ft.Column(
                            scroll=ft.ScrollMode.AUTO,
                            controls=[table],
                        ),
                    ),
                ],
            ),
        )

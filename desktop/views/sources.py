"""Data Sources management view for the Flet desktop app."""

import flet as ft
from typing import Callable

from desktop.api_client import ApiClient


class SourcesView(ft.Container):
    """View for managing external database connections."""

    def __init__(self, api_client: ApiClient, navigate: Callable):
        super().__init__()
        self.api_client = api_client
        self.navigate = navigate
        self.sources = []
        self.loading = ft.ProgressRing(visible=False)

        self.source_name = ft.TextField(
            label="Source Name",
            hint_text="e.g. Production DB",
            border_color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
            color=ft.Colors.WHITE,
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
        )
        self.db_type = ft.Dropdown(
            label="Database Type",
            options=[
                ft.dropdown.Option("postgresql", "PostgreSQL"),
                ft.dropdown.Option("mysql", "MySQL"),
                ft.dropdown.Option("sqlite", "SQLite"),
                ft.dropdown.Option("mssql", "SQL Server"),
            ],
            value="postgresql",
            border_color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
            color=ft.Colors.WHITE,
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
        )
        self.host = ft.TextField(
            label="Host",
            hint_text="localhost",
            border_color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
            color=ft.Colors.WHITE,
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
        )
        self.port = ft.TextField(
            label="Port",
            hint_text="5432",
            width=120,
            border_color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
            color=ft.Colors.WHITE,
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
        )
        self.database = ft.TextField(
            label="Database Name",
            hint_text="mydb",
            border_color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
            color=ft.Colors.WHITE,
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
        )
        self.username = ft.TextField(
            label="Username",
            border_color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
            color=ft.Colors.WHITE,
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
        )
        self.password = ft.TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            border_color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
            color=ft.Colors.WHITE,
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
        )
        self.status_text = ft.Text("", color=ft.Colors.GREEN_400, size=14)

        self.source_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)

        self.content = ft.Container(
            padding=30,
            content=ft.Column(
                spacing=20,
                controls=[
                    ft.Text("🔗 Data Sources", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text(
                        "Connect external databases to pull live data into your dashboards.",
                        size=14,
                        color=ft.Colors.GREY_400,
                    ),
                    ft.Divider(color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
                    ft.Text("Add New Source", size=18, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
                    ft.ResponsiveRow(
                        controls=[
                            self.source_name,
                            self.db_type,
                        ]
                    ),
                    ft.ResponsiveRow(
                        controls=[
                            self.host,
                            self.port,
                            self.database,
                        ]
                    ),
                    ft.ResponsiveRow(
                        controls=[
                            self.username,
                            self.password,
                        ]
                    ),
                    ft.Row(
                        controls=[
                            ft.ElevatedButton(
                                "Test Connection",
                                icon=ft.Icons.ELECTRIC_BOLT,
                                style=ft.ButtonStyle(
                                    color=ft.Colors.WHITE,
                                    bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.AMBER),
                                ),
                                on_click=self._test_connection,
                            ),
                            ft.FilledButton(
                                "Save Source",
                                icon=ft.Icons.SAVE,
                                style=ft.ButtonStyle(
                                    color=ft.Colors.WHITE,
                                    bgcolor=ft.Colors.BLUE_700,
                                ),
                                on_click=self._save_source,
                            ),
                            self.loading,
                        ]
                    ),
                    self.status_text,
                    ft.Divider(color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
                    ft.Text("Saved Sources", size=18, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
                    self.source_list,
                ],
            ),
        )

    def did_mount(self):
        self._load_sources()

    def _load_sources(self):
        self.loading.visible = True
        self.update()
        try:
            result = self.api_client.get("/api/datasources")
            self.sources = result if isinstance(result, list) else []
        except Exception:
            self.sources = []
        self.loading.visible = False
        self._render_source_list()
        self.update()

    def _render_source_list(self):
        self.source_list.controls.clear()
        if not self.sources:
            self.source_list.controls.append(
                ft.Container(
                    padding=20,
                    content=ft.Text("No data sources configured yet.", color=ft.Colors.GREY_500, italic=True),
                )
            )
            return
        for src in self.sources:
            status_color = ft.Colors.GREEN_400 if src.get("status") == "connected" else ft.Colors.RED_400
            self.source_list.controls.append(
                ft.Container(
                    padding=15,
                    border=ft.border.all(1, ft.Colors.with_opacity(0.15, ft.Colors.WHITE)),
                    border_radius=10,
                    bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                    content=ft.Row(
                        controls=[
                            ft.Icon(
                                ft.Icons.STORAGE,
                                color=ft.Colors.BLUE_400,
                                size=24,
                            ),
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text(src.get("name", "Unnamed"), size=16, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
                                    ft.Text(f"{src.get('db_type', '?')}://{src.get('host', '?')}:{src.get('port', '?')}/{src.get('database', '?')}", size=12, color=ft.Colors.GREY_500),
                                ],
                                expand=True,
                            ),
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=10, vertical=4),
                                border_radius=12,
                                bgcolor=ft.Colors.with_opacity(0.15, status_color),
                                content=ft.Text(
                                    src.get("status", "unknown").capitalize(),
                                    size=12,
                                    color=status_color,
                                ),
                            ),
                            ft.IconButton(
                                ft.Icons.DELETE_OUTLINE,
                                icon_color=ft.Colors.RED_400,
                                tooltip="Delete",
                                on_click=lambda _, s=src: self._delete_source(s),
                            ),
                        ]
                    ),
                )
            )

    def _test_connection(self, e):
        self.loading.visible = True
        self.status_text.value = "Testing connection..."
        self.status_text.color = ft.Colors.YELLOW_400
        self.update()
        try:
            config = self._build_source_config()
            result = self.api_client.post("/api/datasources/test", config)
            if result.get("success"):
                self.status_text.value = "✅ Connection successful!"
                self.status_text.color = ft.Colors.GREEN_400
            else:
                self.status_text.value = f"❌ Connection failed: {result.get('error', 'Unknown error')}"
                self.status_text.color = ft.Colors.RED_400
        except Exception as ex:
            self.status_text.value = f"❌ Error: {str(ex)}"
            self.status_text.color = ft.Colors.RED_400
        self.loading.visible = False
        self.update()

    def _save_source(self, e):
        self.loading.visible = True
        self.status_text.value = "Saving..."
        self.status_text.color = ft.Colors.YELLOW_400
        self.update()
        try:
            config = self._build_source_config()
            self.api_client.post("/api/datasources", config)
            self.status_text.value = "✅ Source saved!"
            self.status_text.color = ft.Colors.GREEN_400
            self._clear_form()
            self._load_sources()
        except Exception as ex:
            self.status_text.value = f"❌ Error: {str(ex)}"
            self.status_text.color = ft.Colors.RED_400
        self.loading.visible = False
        self.update()

    def _delete_source(self, source):
        try:
            self.api_client.delete(f"/api/datasources/{source.get('id')}")
            self._load_sources()
        except Exception as ex:
            self.status_text.value = f"❌ Delete failed: {str(ex)}"
            self.status_text.color = ft.Colors.RED_400
            self.update()

    def _build_source_config(self):
        return {
            "name": self.source_name.value.strip(),
            "db_type": self.db_type.value,
            "host": self.host.value.strip() or "localhost",
            "port": int(self.port.value.strip() or 5432),
            "database": self.database.value.strip(),
            "username": self.username.value.strip(),
            "password": self.password.value,
        }

    def _clear_form(self):
        self.source_name.value = ""
        self.db_type.value = "postgresql"
        self.host.value = ""
        self.port.value = ""
        self.database.value = ""
        self.username.value = ""
        self.password.value = ""

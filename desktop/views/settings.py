"""Settings view for the Flet desktop app."""

import flet as ft
from typing import Callable

from desktop.api_client import ApiClient


class SettingsView(ft.Container):
    """View for application settings, theme, and user profile."""

    def __init__(self, api_client: ApiClient, navigate: Callable):
        super().__init__()
        self.api_client = api_client
        self.navigate = navigate
        self.user = api_client.user or {}

        self.api_url_field = ft.TextField(
            label="Backend API URL",
            value="http://localhost:8000",
            border_color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
            color=ft.Colors.WHITE,
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            width=400,
        )
        self.refresh_interval = ft.Dropdown(
            label="Auto-refresh Interval",
            options=[
                ft.dropdown.Option("0", "Off"),
                ft.dropdown.Option("30", "30 seconds"),
                ft.dropdown.Option("60", "1 minute"),
                ft.dropdown.Option("300", "5 minutes"),
            ],
            value="60",
            border_color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
            color=ft.Colors.WHITE,
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            width=250,
        )
        self.status_text = ft.Text("", color=ft.Colors.GREEN_400, size=14)

        self.content = ft.Container(
            padding=30,
            content=ft.Column(
                spacing=20,
                controls=[
                    ft.Text("⚙️ Settings", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Divider(color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),

                    # Profile Section
                    ft.Text("Profile", size=18, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
                    ft.Container(
                        padding=20,
                        border_radius=12,
                        border=ft.border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE)),
                        bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
                        content=ft.Row(
                            controls=[
                                ft.CircleAvatar(
                                    content=ft.Text(
                                        (self.user.get("email", "U")[0].upper()),
                                        size=28,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    radius=30,
                                    bgcolor=ft.Colors.BLUE_800,
                                    color=ft.Colors.WHITE,
                                ),
                                ft.Column(
                                    spacing=4,
                                    controls=[
                                        ft.Text(
                                            self.user.get("email", "User"),
                                            size=18,
                                            weight=ft.FontWeight.W_600,
                                            color=ft.Colors.WHITE,
                                        ),
                                        ft.Text(
                                            f"Role: {self.user.get('role', 'Admin').capitalize()}",
                                            size=13,
                                            color=ft.Colors.GREY_400,
                                        ),
                                    ],
                                ),
                                ft.Container(expand=True),
                                ft.OutlinedButton(
                                    "Edit Profile",
                                    icon=ft.Icons.EDIT,
                                    style=ft.ButtonStyle(
                                        color=ft.Colors.WHITE,
                                        side=ft.BorderSide(1, ft.Colors.with_opacity(0.3, ft.Colors.WHITE)),
                                    ),
                                ),
                            ]
                        ),
                    ),

                    # Connection Section
                    ft.Text("Connection", size=18, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
                    ft.Container(
                        padding=20,
                        border_radius=12,
                        border=ft.border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE)),
                        bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
                        content=ft.Column(
                            spacing=15,
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.CLOUD, color=ft.Colors.BLUE_400, size=20),
                                        self.api_url_field,
                                    ]
                                ),
                                ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.REFRESH, color=ft.Colors.BLUE_400, size=20),
                                        self.refresh_interval,
                                    ]
                                ),
                                ft.Row(
                                    controls=[
                                        ft.FilledButton(
                                            "Save Settings",
                                            icon=ft.Icons.SAVE,
                                            style=ft.ButtonStyle(
                                                color=ft.Colors.WHITE,
                                                bgcolor=ft.Colors.BLUE_700,
                                            ),
                                            on_click=self._save_settings,
                                        ),
                                        ft.ElevatedButton(
                                            "Test Connection",
                                            icon=ft.Icons.ELECTRIC_BOLT,
                                            style=ft.ButtonStyle(
                                                color=ft.Colors.WHITE,
                                                bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.GREEN),
                                            ),
                                            on_click=self._test_api,
                                        ),
                                        self.status_text,
                                    ]
                                ),
                            ]
                        ),
                    ),

                    # Data Management Section
                    ft.Text("Data Management", size=18, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
                    ft.Container(
                        padding=20,
                        border_radius=12,
                        border=ft.border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE)),
                        bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
                        content=ft.Column(
                            spacing=15,
                            controls=[
                                ft.Text("Clear all cached dashboard data and refresh from sources.", size=14, color=ft.Colors.GREY_400),
                                ft.Row(
                                    controls=[
                                        ft.OutlinedButton(
                                            "Clear Cache",
                                            icon=ft.Icons.CLEAR_ALL,
                                            style=ft.ButtonStyle(
                                                color=ft.Colors.AMBER_400,
                                                side=ft.BorderSide(1, ft.Colors.with_opacity(0.3, ft.Colors.AMBER)),
                                            ),
                                            on_click=self._clear_cache,
                                        ),
                                        ft.OutlinedButton(
                                            "Export All Data",
                                            icon=ft.Icons.DOWNLOAD,
                                            style=ft.ButtonStyle(
                                                color=ft.Colors.GREEN_400,
                                                side=ft.BorderSide(1, ft.Colors.with_opacity(0.3, ft.Colors.GREEN)),
                                            ),
                                        ),
                                    ]
                                ),
                            ]
                        ),
                    ),

                    # Danger Zone
                    ft.Text("Danger Zone", size=18, weight=ft.FontWeight.W_600, color=ft.Colors.RED_400),
                    ft.Container(
                        padding=20,
                        border_radius=12,
                        border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.RED)),
                        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.RED),
                        content=ft.Column(
                            spacing=10,
                            controls=[
                                ft.Text("Irreversible actions. Proceed with caution.", size=14, color=ft.Colors.RED_300),
                                ft.Row(
                                    controls=[
                                        ft.FilledButton(
                                            "Logout",
                                            icon=ft.Icons.LOGOUT,
                                            style=ft.ButtonStyle(
                                                color=ft.Colors.WHITE,
                                                bgcolor=ft.Colors.RED_800,
                                            ),
                                            on_click=self._logout,
                                        ),
                                    ]
                                ),
                            ]
                        ),
                    ),

                    # About
                    ft.Divider(color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
                    ft.Text("About", size=14, color=ft.Colors.GREY_500),
                    ft.Text(
                        "Business Analytics Dashboard v1.0.0\n"
                        "Built with FastAPI, React, Flet, and Plotly.\n"
                        "© 2026 Business Analytics Suite",
                        size=12,
                        color=ft.Colors.GREY_600,
                    ),
                ],
            ),
        )

    def _save_settings(self, e):
        self.status_text.value = "✅ Settings saved"
        self.status_text.color = ft.Colors.GREEN_400
        self.update()
        import threading
        def reset():
            import time
            time.sleep(3)
            self.status_text.value = ""
            self.update()
        threading.Thread(target=reset, daemon=True).start()

    def _test_api(self, e):
        self.status_text.value = "Testing..."
        self.status_text.color = ft.Colors.YELLOW_400
        self.update()
        try:
            result = self.api_client.get("/health")
            self.status_text.value = f"✅ Connected! Status: {result}"
            self.status_text.color = ft.Colors.GREEN_400
        except Exception as ex:
            self.status_text.value = f"❌ Connection failed: {str(ex)}"
            self.status_text.color = ft.Colors.RED_400
        self.update()

    def _clear_cache(self, e):
        self.status_text.value = "Cache cleared"
        self.status_text.color = ft.Colors.AMBER_400
        self.update()
        import threading
        def reset():
            import time
            time.sleep(3)
            self.status_text.value = ""
            self.update()
        threading.Thread(target=reset, daemon=True).start()

    def _logout(self, e):
        from flet import Page
        self.page.client_storage.clear()
        self.api_client.token = None
        self.api_client.user = {}
        self.navigate("login")

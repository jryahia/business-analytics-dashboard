"""Business Analytics Dashboard — Flet Desktop App."""

import flet as ft
import os

from desktop.api_client import ApiClient
from desktop.views.dashboard import DashboardView
from desktop.views.datasets import DatasetsView
from desktop.views.sources import SourcesView
from desktop.views.charts import ChartsView
from desktop.views.settings import SettingsView
from desktop.widgets.sidebar import Sidebar


API_URL = os.environ.get("API_URL", "http://localhost:8000")


class AnalyticsApp:
    """Main Flet application."""

    def __init__(self):
        self.api_client = ApiClient(API_URL)
        self.sidebar = None
        self.content_area = ft.Container(expand=True, padding=0)
        self.views = {}
        self.current_view = None

    def run(self, page: ft.Page):
        self.page = page
        page.title = "Business Analytics Dashboard"
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = ft.Colors.GREY_900
        page.padding = 0
        page.spacing = 0

        # Dark theme
        page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=ft.Colors.BLUE_400,
                secondary=ft.Colors.BLUE_700,
                surface=ft.Colors.GREY_900,
                surface_tint=ft.Colors.GREY_800,
                on_surface=ft.Colors.WHITE,
                on_surface_variant=ft.Colors.GREY_400,
                outline=ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
            ),
        )

        page.window.width = 1280
        page.window.height = 800
        page.window.min_width = 900
        page.window.min_height = 600

        # Check auth
        token = page.client_storage.get("auth_token")
        if token:
            self.api_client.token = token

        self.sidebar = Sidebar(
            on_navigate=self._navigate,
            api_client=self.api_client,
        )

        page.add(
            ft.Row(
                spacing=0,
                controls=[
                    self.sidebar,
                    ft.VerticalDivider(width=0, color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
                    self.content_area,
                ],
                expand=True,
            )
        )

        if not self.api_client.token:
            self._navigate("login")
        else:
            self._navigate("dashboard")

    def _navigate(self, route: str):
        if route == "login":
            self._show_login()
            return

        self.current_view = route
        self.sidebar.set_active(route)

        if route not in self.views:
            self.views[route] = self._create_view(route)

        if route in self.views:
            view = self.views[route]
            self.content_area.content = view
            self.content_area.update()
            if hasattr(view, "did_mount"):
                view.did_mount()

    def _create_view(self, route: str):
        creators = {
            "dashboard": lambda: DashboardView(self.api_client, self._navigate),
            "datasets": lambda: DatasetsView(self.api_client, self._navigate),
            "sources": lambda: SourcesView(self.api_client, self._navigate),
            "charts": lambda: ChartsView(self.api_client, self._navigate),
            "settings": lambda: SettingsView(self.api_client, self._navigate),
        }
        creator = creators.get(route)
        if creator:
            view = creator()
            view.expand = True
            return view
        return ft.Container(
            padding=30,
            content=ft.Text(f"View not found: {route}", color=ft.Colors.RED_400),
        )

    def _show_login(self):
        email = ft.TextField(
            label="Email",
            hint_text="admin@example.com",
            border_color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
            color=ft.Colors.WHITE,
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            width=320,
        )
        password = ft.TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            border_color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
            color=ft.Colors.WHITE,
            label_style=ft.TextStyle(color=ft.Colors.GREY_400),
            width=320,
        )
        error_text = ft.Text("", color=ft.Colors.RED_400, size=14)
        loading = ft.ProgressRing(visible=False, width=20, height=20)

        def do_login(e):
            if not email.value or not password.value:
                error_text.value = "Please enter email and password"
                error_text.update()
                return
            loading.visible = True
            loading.update()
            try:
                result = self.api_client.login(email.value, password.value)
                if result and "access_token" in result:
                    self.api_client.token = result["access_token"]
                    self.page.client_storage.set("auth_token", result["access_token"])
                    self._navigate("dashboard")
                else:
                    error_text.value = "Invalid credentials"
                    error_text.color = ft.Colors.RED_400
            except Exception as ex:
                error_text.value = f"Connection failed: {str(ex)}"
                error_text.color = ft.Colors.RED_400
            loading.visible = False
            error_text.update()

        login_card = ft.Container(
            padding=40,
            border_radius=16,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
            border=ft.border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
            width=400,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
                controls=[
                    ft.Icon(ft.Icons.ANALYTICS, size=48, color=ft.Colors.BLUE_400),
                    ft.Text(
                        "Business Analytics",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE,
                    ),
                    ft.Text(
                        "Sign in to your dashboard",
                        size=14,
                        color=ft.Colors.GREY_400,
                    ),
                    ft.Divider(color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
                    email,
                    password,
                    error_text,
                    ft.FilledButton(
                        "Sign In",
                        style=ft.ButtonStyle(
                            color=ft.Colors.WHITE,
                            bgcolor=ft.Colors.BLUE_700,
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                        width=320,
                        height=44,
                        on_click=do_login,
                    ),
                    loading,
                ],
            ),
        )

        self.content_area.content = ft.Container(
            expand=True,
            alignment=ft.alignment.center,
            content=login_card,
        )
        self.content_area.update()


def main():
    app = AnalyticsApp()
    ft.app(target=app.run, assets_dir="assets")


if __name__ == "__main__":
    main()

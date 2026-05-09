import flet as ft
from typing import Callable

SIDEBAR_WIDTH = 230
SIDEBAR_BG = "#0d1117"
ITEM_ACTIVE_BG = "#1a2744"
ITEM_HOVER_BG = "#161b22"
PRIMARY = "#58a6ff"
TEXT = "#e6edf3"
TEXT_DIM = "#8b949e"
BORDER = "#21262d"

NAV_ITEMS = [
    {"route": "/", "icon": ft.icons.DASHBOARD_OUTLINED, "active_icon": ft.icons.DASHBOARD, "label": "Dashboard"},
    {"route": "/datasets", "icon": ft.icons.TABLE_CHART_OUTLINED, "active_icon": ft.icons.TABLE_CHART, "label": "Datasets"},
    {"route": "/sources", "icon": ft.icons.STORAGE_OUTLINED, "active_icon": ft.icons.STORAGE, "label": "Data Sources"},
    {"route": "/charts", "icon": ft.icons.BAR_CHART_OUTLINED, "active_icon": ft.icons.BAR_CHART, "label": "Charts"},
    {"route": "/settings", "icon": ft.icons.SETTINGS_OUTLINED, "active_icon": ft.icons.SETTINGS, "label": "Settings"},
]


def _nav_item(
    icon: str,
    active_icon: str,
    label: str,
    route: str,
    is_active: bool,
    on_navigate: Callable[[str], None],
) -> ft.Container:
    color = PRIMARY if is_active else TEXT_DIM
    bg = ITEM_ACTIVE_BG if is_active else "transparent"

    def clicked(e):
        on_navigate(route)

    return ft.Container(
        bgcolor=bg,
        border_radius=8,
        padding=ft.padding.symmetric(horizontal=12, vertical=10),
        margin=ft.margin.symmetric(horizontal=8, vertical=2),
        on_click=clicked,
        ink=True,
        content=ft.Row(
            spacing=12,
            controls=[
                ft.Container(
                    width=4,
                    height=24,
                    border_radius=4,
                    bgcolor=PRIMARY if is_active else "transparent",
                ),
                ft.Icon(active_icon if is_active else icon, size=20, color=color),
                ft.Text(label, size=14, color=TEXT if is_active else TEXT_DIM, weight=ft.FontWeight.W_500 if is_active else ft.FontWeight.NORMAL),
            ],
        ),
    )


def build_sidebar(
    on_navigate: Callable[[str], None],
    current_route: str,
    api_status: bool = False,
) -> ft.Container:
    status_color = "#3fb950" if api_status else "#f85149"
    status_label = "Connected" if api_status else "Offline"

    nav_controls = [
        _nav_item(
            item["icon"],
            item["active_icon"],
            item["label"],
            item["route"],
            current_route == item["route"],
            on_navigate,
        )
        for item in NAV_ITEMS
    ]

    return ft.Container(
        width=SIDEBAR_WIDTH,
        bgcolor=SIDEBAR_BG,
        border=ft.border.only(right=ft.BorderSide(1, BORDER)),
        content=ft.Column(
            spacing=0,
            controls=[
                # Logo / app name
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=20, vertical=24),
                    content=ft.Row(
                        spacing=10,
                        controls=[
                            ft.Container(
                                width=32,
                                height=32,
                                border_radius=8,
                                bgcolor=PRIMARY,
                                content=ft.Icon(ft.icons.ANALYTICS, size=18, color="#ffffff"),
                            ),
                            ft.Column(
                                spacing=0,
                                controls=[
                                    ft.Text("Hermes", size=15, color=TEXT, weight=ft.FontWeight.BOLD),
                                    ft.Text("Analytics", size=11, color=TEXT_DIM),
                                ],
                            ),
                        ],
                    ),
                ),
                ft.Divider(height=1, color=BORDER),
                ft.Container(height=8),
                # Navigation items
                *nav_controls,
                ft.Container(expand=True),
                ft.Divider(height=1, color=BORDER),
                # API status indicator
                ft.Container(
                    padding=ft.padding.all(16),
                    content=ft.Row(
                        spacing=8,
                        controls=[
                            ft.Container(
                                width=8,
                                height=8,
                                border_radius=4,
                                bgcolor=status_color,
                            ),
                            ft.Text(f"API: {status_label}", size=12, color=TEXT_DIM),
                        ],
                    ),
                ),
            ],
        ),
    )

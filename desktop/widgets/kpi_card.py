import flet as ft

# Dark theme palette
BG_CARD = "#1e2130"
BORDER_COLOR = "#2d3250"
PRIMARY = "#58a6ff"
SUCCESS = "#3fb950"
ERROR = "#f85149"
TEXT = "#e6edf3"
TEXT_DIM = "#8b949e"


def build_kpi_card(
    title: str,
    value: str,
    change: float,
    trend: str = "up",
    icon_name: str = "bar_chart",
    width: int = 220,
) -> ft.Container:
    is_positive = trend == "up"
    change_color = SUCCESS if is_positive else ERROR
    arrow_icon = ft.icons.ARROW_UPWARD if is_positive else ft.icons.ARROW_DOWNWARD
    change_sign = "+" if is_positive else ""

    return ft.Container(
        width=width,
        padding=ft.padding.all(20),
        border_radius=12,
        bgcolor=BG_CARD,
        border=ft.border.all(1, BORDER_COLOR),
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(title, size=13, color=TEXT_DIM, weight=ft.FontWeight.W_500),
                        ft.Container(
                            padding=ft.padding.all(8),
                            border_radius=8,
                            bgcolor=f"{PRIMARY}22",
                            content=ft.Icon(icon_name, size=18, color=PRIMARY),
                        ),
                    ],
                ),
                ft.Text(value, size=28, color=TEXT, weight=ft.FontWeight.BOLD),
                ft.Row(
                    spacing=4,
                    controls=[
                        ft.Icon(arrow_icon, size=14, color=change_color),
                        ft.Text(
                            f"{change_sign}{abs(change):.1f}% vs last period",
                            size=12,
                            color=change_color,
                        ),
                    ],
                ),
            ],
        ),
    )

import flet as ft

BG_CARD = "#1e2130"
BORDER_COLOR = "#2d3250"
TEXT = "#e6edf3"
TEXT_DIM = "#8b949e"
PRIMARY = "#58a6ff"


def build_chart_card(
    title: str,
    chart: ft.Control,
    subtitle: str = "",
    actions: list[ft.Control] | None = None,
    height: int = 300,
    expand: bool = False,
) -> ft.Container:
    header_controls: list[ft.Control] = [
        ft.Column(
            spacing=2,
            controls=[
                ft.Text(title, size=15, color=TEXT, weight=ft.FontWeight.W_600),
                ft.Text(subtitle, size=12, color=TEXT_DIM) if subtitle else ft.Container(),
            ],
        )
    ]
    if actions:
        header_controls.append(
            ft.Row(controls=actions, spacing=8)
        )

    return ft.Container(
        expand=expand,
        padding=ft.padding.all(20),
        border_radius=12,
        bgcolor=BG_CARD,
        border=ft.border.all(1, BORDER_COLOR),
        content=ft.Column(
            spacing=16,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=header_controls,
                ),
                ft.Divider(height=1, color=BORDER_COLOR),
                ft.Container(
                    height=height,
                    content=chart,
                ),
            ],
        ),
    )


def build_empty_chart_state(message: str = "No data available") -> ft.Container:
    return ft.Container(
        expand=True,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.icons.INSERT_CHART_OUTLINED, size=48, color=TEXT_DIM),
                ft.Text(message, size=14, color=TEXT_DIM),
            ],
        ),
    )

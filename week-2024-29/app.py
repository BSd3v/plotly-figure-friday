### import libraries
import traceback

import dash
from dash import *
import pandas as pd
import dash_ag_grid as dag
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

### import data
owner = "BSd3v"
data = {}
week = "29"
year = "2024"
base_url = (
    f"https://raw.githubusercontent.com/plotly/Figure-Friday/main/{year}/week-{week}/"
)
attribution = """The English Women's Football (EWF) Database, May 2024, https://github.com/probjects/ewf-database."""

files = ["ewf_appearances.csv", "ewf_matches.csv", "ewf_standings.csv"]
for f in files:
    if ".csv" in f.lower():
        data[f] = pd.read_csv(f"{base_url}/{files[0]}")
    else:
        data[f] = pd.read_excel(f"{base_url}/{files[0]}")


### dash app
stylesheets = [
    "https://unpkg.com/@mantine/dates@7/styles.css",
    "https://unpkg.com/@mantine/code-highlight@7/styles.css",
    "https://unpkg.com/@mantine/charts@7/styles.css",
    "https://unpkg.com/@mantine/carousel@7/styles.css",
    "https://unpkg.com/@mantine/notifications@7/styles.css",
    "https://unpkg.com/@mantine/nprogress@7/styles.css",
]

dash._dash_renderer._set_react_version("18.2.0")

app = Dash(__name__, use_pages=True, pages_folder="", external_stylesheets=stylesheets)


### visualizations

for f in files:
    data[f]["attendance"] = data[f]["attendance"].map(
        lambda x: int(str(x).replace(",", "")) if x and str(x) != "nan" else None
    )

default_layout = {"margin": {"r": 0, "l": 0, "b": 0, "t": 35}}

home_team = data[files[1]][data[files[1]]["home_team"] == 1].copy()
away_team = data[files[1]][data[files[1]]["away_team"] == 1].copy()
home_team["date"] = pd.to_datetime(home_team["date"])

## fix names
for i, row in home_team.iterrows():
    home_team.loc[i, "team_name"] = home_team[
        home_team["team_id"] == row["team_id"]
    ].iloc[-1]["team_name"]
    home_team.loc[i, "opponent_name"] = home_team[
        home_team["opponent_id"] == row["opponent_id"]
    ].iloc[-1]["opponent_name"]

figures = dmc.Grid(
    [
        dmc.GridCol(
            [
                dcc.Graph(figure=go.Figure(), id="home_attendance_treemap"),
            ]
        ),
        dmc.GridCol(
            [
                "Match Attendance Range",
                dmc.RangeSlider(
                    value=[
                        home_team["attendance"].min(),
                        home_team["attendance"].max(),
                    ],
                    min=home_team["attendance"].min(),
                    max=home_team["attendance"].max(),
                    id="attendance_range",
                ),
                dmc.DatePicker(
                    label="Match Date Range",
                    value=[home_team["date"].min(), home_team["date"].max()],
                    minDate=home_team["date"].min(),
                    maxDate=home_team["date"].max(),
                    id="date_range",
                    type="range",
                    numberOfColumns=2,
                ),
                dmc.RadioGroup(
                    children=dmc.Group(
                        [dmc.Radio(k, value=k) for k in ["All", "1", "2"]], my=10
                    ),
                    id="match_tier",
                    value="All",
                    label="Match Tier",
                    size="sm",
                    mb=10,
                ),
                dmc.MultiSelect(
                    id="home_teams",
                    data=sorted(home_team["team_name"].unique().tolist()),
                    clearable=True,
                    label="Home Teams",
                ),
                dmc.MultiSelect(
                    id="away_teams",
                    data=sorted(home_team["opponent_name"].unique().tolist()),
                    clearable=True,
                    label="Away Teams",
                ),
            ],
            span=2,
            className="filter-card",
            style={"padding": "15px"},
        ),
        dmc.GridCol(
            [
                dmc.Group(
                    [
                        dcc.Graph(
                            figure=go.Figure(),
                            id="attendance_time",
                            style={"height": "100%"},
                        ),
                        html.Div(
                            [
                                dcc.Graph(
                                    figure=go.Figure(),
                                    id="most_attendance",
                                    style={"height": "100%"},
                                )
                            ],
                            style={
                                "display": "flex",
                                "flexDirection": "column",
                                "height": "100%",
                            },
                        ),
                    ],
                    style={
                        "height": "300px",
                        "maxHeight": "300px",
                        "overflow": "hidden",
                        "padding": "15px",
                    },
                )
            ],
            span=10,
        ),
    ]
)


@callback(
    Output("home_attendance_treemap", "figure"),
    Output("attendance_time", "figure"),
    Output("most_attendance", "figure"),
    Input("attendance_range", "value"),
    Input("date_range", "value"),
    Input("match_tier", "value"),
    Input("home_teams", "value"),
    Input("away_teams", "value"),
    Input("mode", "checked"),
)
def updateTreemap(v, v2, v3, v4, v5, c):
    if ctx.triggered_id == "mode":
        newTemplate = pio.templates[
            "plotly_white" if not c else "plotly_dark"
        ].to_plotly_json()
        fig = Patch()
        fig["layout"]["template"] = newTemplate
        return [fig] * len(ctx.outputs_list)
    if len(v) == 2 and len(v2) == 2:
        try:
            team_ids = home_team["team_name"].drop_duplicates().tolist()
            opponent_ids = home_team["opponent_name"].unique().tolist()
            mask = home_team[
                (
                    home_team["team_name"].isin(v4 if len((v4 or [])) > 0 else team_ids)
                    & home_team["opponent_name"].isin(
                        v5 if len((v5 or [])) > 0 else opponent_ids
                    )
                    & home_team["attendance"].between(v[0], v[1], inclusive="both")
                    & home_team["date"].between(v2[0], v2[1], inclusive="both")
                    & home_team["tier"].isin([int(v3)] if not v3 == "All" else [1, 2])
                )
            ].dropna(subset=["attendance"])
            fig = Patch()
            newTree = px.treemap(
                mask,
                path=["team_name", "opponent_name", "date"],
                values="attendance",
                color="attendance",
                template="plotly_white" if not c else "plotly_dark",
                title="Home Team Attendance Distribution",
                range_color=[
                    home_team["attendance"].min(),
                    home_team["attendance"].max(),
                ],
            ).update_layout(default_layout)
            fig["data"] = newTree.data
            fig2 = Patch()
            newScatter = px.scatter(
                mask,
                x="date",
                y="attendance",
                title="Attendance Over Time",
                template="plotly_white" if not c else "plotly_dark",
            ).update_layout(default_layout)
            fig2["data"] = newScatter.data
            fig3 = Patch()
            sorted_df = mask.sort_values("attendance", ascending=False)
            newMax = go.Figure(
                go.Indicator(
                    value=mask["attendance"].max(),
                    title=f"{sorted_df.iloc[0].loc['match_name']}<br>"
                    + f"({str(sorted_df.iloc[0].loc['date']).split(' ')[0]})",
                )
            ).update_layout(
                {
                    **default_layout,
                    "template": "plotly_white" if not c else "plotly_dark",
                }
            )
            fig3["data"] = newMax.data
            fig2["layout"] = newScatter.layout
            fig["layout"] = newTree.layout
            fig3["layout"] = newMax.layout
            return [fig, fig2, fig3]
        except:
            print(traceback.format_exc())
            pass
    return [no_update] * len(ctx.outputs_list)


register_page("Visualizations", path="/visualizations", layout=figures)

### defaults


raw_data = [
    html.H2("Raw Data"),
    dcc.Markdown(attribution),
    dmc.TextInput(
        label="Quick Filter Text",
        id="filter_raw_data",
        placeholder="Type to filter all data sets",
    ),
    html.Div(
        [
            html.Div(
                [
                    html.H4(f),
                    dag.AgGrid(
                        id={"index": f, "type": "information"},
                        rowData=data[f].to_dict("records"),
                        columnDefs=[{"field": x} for x in data[f].columns],
                        dashGridOptions={"quickFilterText": ""},
                    ),
                ]
            )
            for f in files
        ]
    ),
]


@callback(
    Output(
        {"index": ALL, "type": "information"}, "dashGridOptions", allow_duplicate=True
    ),
    Input("filter_raw_data", "value"),
    prevent_initial_call=True,
)
def filter_raw_data(v):
    options = Patch()
    options["quickFilterText"] = v
    return [options] * len(files)


register_page("Data", path="/data", layout=raw_data)

app.layout = dmc.MantineProvider(
    [
        dmc.AppShell(
            [
                dmc.AppShellHeader(
                    html.Div(
                        [
                            html.H2(f"{owner}"),
                            html.H1(
                                f"Figure Friday - Year {year} - Week {week}",
                                className="mantine-visible-from-md",
                            ),
                            html.H3(f"FF{year}{week}", className="mantine-hidden-from-md"),
                            dmc.Group(
                                [
                                    dmc.Anchor(
                                        DashIconify(icon="ion:logo-github", width=35),
                                        href=f"https://github.com/{owner}",
                                        style={
                                            "height": "100%",
                                            "display": "flex",
                                            "alignItems": "center",
                                        },
                                        target="_blank",
                                        className="mantine-visible-from-sm",
                                    ),
                                    dmc.Anchor(
                                        DashIconify(
                                            icon="skill-icons:discord", width=35
                                        ),
                                        href="https://discord.com/channels/1247975306472591470",
                                        style={
                                            "height": "100%",
                                            "display": "flex",
                                            "alignItems": "center",
                                        },
                                        target="_blank",
                                        className="mantine-visible-from-sm",
                                    ),
                                    dmc.Anchor(
                                        html.Img(
                                            src="https://dash.plotly.com/assets/images/plotly_logo_light.png",
                                            style={"width": "150px"},
                                            id="plotly_logo",
                                        ),
                                        href="https://dash.plotly.com/",
                                        style={
                                            "display": "flex",
                                            "alignItems": "center",
                                            "margin": "-15px",
                                        },
                                        target="_blank",
                                        className="mantine-visible-from-sm",
                                    ),
                                    dmc.Switch(
                                        offLabel=DashIconify(
                                            icon="radix-icons:moon", width=20
                                        ),
                                        onLabel=DashIconify(
                                            icon="radix-icons:sun", width=20
                                        ),
                                        size="xl",
                                        id="mode",
                                        style={"cursor": "pointer"},
                                    ),
                                    dmc.Burger(className="mantine-hidden-from-sm", id="display-nav"),
                                    dcc.Store(id="theme-switch", storage_type="local"),
                                ],
                                gap=5,
                                style={"height": "100%"},
                            ),
                        ],
                        style={
                            "display": "flex",
                            "justifyContent": "space-between",
                            "alignItems": "center",
                            "paddingLeft": "25px",
                            "paddingRight": "25px",
                            "height": "100%",
                        },
                    )
                ),
                dmc.AppShellNavbar(
                    dmc.Stack(
                        [
                            dmc.Anchor(
                                pg["title"],
                                href=pg["path"],
                                style={"paddingLeft": "30px", "width": "100%"},
                            )
                            for pg in page_registry.values()
                        ],
                        align="center",
                    )
                ),
                dmc.AppShellMain(page_container),
            ],
            header={"height": 70},
            padding="xl",
            zIndex=1400,
            navbar={
                "width": 300,
                "breakpoint": "sm",
                "collapsed": {"mobile": True},
            },
            styles={
                "main": {
                    "paddingTop": "var(--app-shell-header-height)",
                    "paddingBottom": "25px",
                }
            },
        ),
        dmc.Drawer(
            dmc.Stack(
                [
                    html.Div(
                        dmc.Anchor(
                            pg["title"],
                            href=pg["path"],
                            style={"paddingLeft": "30px", "width": "100%", "display": "block"},
                        ),
                        id={"index": pg["title"], "type": "mobile-nav"},
                        style={"width": "100%"},
                    )
                    for pg in page_registry.values()
                ],
                style={"top": "80px", "position": "absolute", "width": "100%"},
            ),
            id="nav-drawer",
        ),
    ],
    defaultColorScheme="auto",
    id="mantine-provider",
)

clientside_callback(
    """(n) => {
        return n
    }""",
    Output("nav-drawer", "opened"),
    Input("display-nav", "opened"),
)

clientside_callback(
    """(_) => {
        return false
    }""",
    Output("display-nav", "opened"),
    Input({"index": ALL, "type": "mobile-nav"}, "n_clicks"),
    prevent_initial_call=True,
)


@callback(
    Output({"index": ALL, "type": "information"}, "className"), Input("mode", "checked")
)
def updateClassNames(c):
    return ["ag-theme-alpine-dark" if c else "ag-theme-alpine"] * len(files)


clientside_callback(
    """(c) => {
        trg = c ? 'dark' : 'light'
        document.body.classList = [trg]
        return [trg, `https://dash.plotly.com/assets/images/plotly_logo_${trg}.png`, c]
    }""",
    Output("mantine-provider", "forceColorScheme"),
    Output("plotly_logo", "src"),
    Output("theme-switch", "data", allow_duplicate=True),
    Input("mode", "checked"),
    prevent_initial_call=True,
)

clientside_callback(
    """
        (_, data) => {
            if (data !== null) {
                return [data, data]
            }
           return [
            window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light',
            window.dash_clientside.no_update
            ]
        }
    """,
    Output("mode", "checked"),
    Output("theme-switch", "data"),
    Input("theme-switch", "id"),
    State("theme-switch", "data"),
)

app.run(debug=True)

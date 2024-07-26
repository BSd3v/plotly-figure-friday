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
import dash_chart_editor as dce

### import data
owner = "BSd3v"
data = {}
week = "30"
year = "2024"
base_url = (
    f"https://raw.githubusercontent.com/plotly/Figure-Friday/main/{year}/week-{week}/"
)
attribution = """"""

files = ["rural-investments.csv"]
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
    "https://unpkg.com/@mantine/nprogress@7/styles.css"
]

dash._dash_renderer._set_react_version("18.2.0")

app = Dash(__name__, use_pages=True, pages_folder="", external_stylesheets=stylesheets)


### visualizations
cols_int = ['Investment Dollars', 'Number of Investments']
main_file = files[0]
for f in files:
    for col in cols_int:
        if col in data[f].columns:
            data[f][col] = data[f][col].map(
                    lambda x: int(str(x).replace(",", "")) if x and str(x) != "nan" else None
                )
data[main_file]['County FIPS'] = data[main_file]['County FIPS'].astype(str).str.replace("'", "").str.zfill(5)

chart_editor_modal = dmc.Modal(
            title="Customizing Charts",
            children=[
                dcc.Input(id="chartId"),
                dce.DashChartEditor(
                    dataSources=data[main_file].to_dict("list"),
                    id="editor",
                    style={"height": "60vh"},
                ),
                dmc.Group(
                    [
                        dmc.Button("Reset", id="resetEditor"),
                        dmc.Button("Save", id="saveEditor"),
                        dmc.Button("Save & Close", id="saveCloseEditor", color="green", variant="outline"),
                    ]
                ),
            ],
    id="editorMenu",
    fullScreen=True,
    zIndex=3000,
    style={'display': 'flex', 'flexDirection': 'column'}
)

def make_card(n_clicks, figure=None):
    return dmc.Card(
        [
            dbc.CardHeader(
                [
                    f"Figure {n_clicks + 1} ",
                    dmc.Button(
                        "Edit",
                        id={"type": "dynamic-edit", "index": n_clicks},
                        n_clicks=0,
                        color=""
                    ),
                    dmc.Button(
                        "X",
                        id={"type": "dynamic-delete", "index": n_clicks},
                        n_clicks=0,
                        color="red",
                        variant="outline"
                    ),
                ],
                className="text-end",
            ),
            dcc.Graph(
                id={"type": "dynamic-output", "index": n_clicks},
                style={"height": "100%"},
                figure=figure or go.Figure(),

            ),
        ],
        style={
            "width": 800,
            "display": "inline-block",
        },
        className="graph-cards",
        id={"type": "dynamic-card", "index": n_clicks},
    )


@app.callback(
    Output("grid-charts", "children"),
    Input("pattern-match-add-chart", "n_clicks"),
)
def add_card(n_clicks):
    patched_children = Patch()
    new_card = make_card(n_clicks)
    patched_children.append(new_card)
    return patched_children


@app.callback(
    Output("grid-charts", "children", allow_duplicate=True),
    Input({"type": "dynamic-delete", "index": ALL}, "n_clicks"),
    State({"type": "dynamic-card", "index": ALL}, "id"),
    prevent_initial_call=True,
)
def remove_card(_, ids):
    cards = Patch()
    if ctx.triggered[0]["value"] > 0:
        for i in range(len(ids)):
            if ids[i]["index"] == ctx.triggered_id["index"]:
                del cards[i]
                return cards
    return no_update


@app.callback(
    Output("editorMenu", "opened"),
    Output("editor", "loadFigure"),
    Output("chartId", "value"),
    Output("oldSum", "data"),
    Input({"type": "dynamic-edit", "index": ALL}, "n_clicks"),
    State({"type": "dynamic-output", "index": ALL}, "figure"),
    State("oldSum", "data"),
    State({"type": "dynamic-card", "index": ALL}, "id"),
    prevent_initial_call=True,
)
def edit_card(edit, figs, oldSum, ids):
    if sum(edit) < oldSum:
        oldSum = sum(edit)
    if sum(edit) > 0 and sum(edit) > oldSum:
        oldSum = sum(edit)
        if ctx.triggered[0]["value"] > 0:
            for i in range(len(ids)):
                if ids[i]["index"] == ctx.triggered_id["index"]:
                    if figs[i]["data"]:
                        return True, figs[i], ctx.triggered_id["index"], oldSum
                    return (
                        True,
                        {"data": [], "layout": {}},
                        ctx.triggered_id["index"],
                        oldSum,
                    )
    return no_update, no_update, no_update, oldSum


@app.callback(
    Output("editor", "loadFigure", allow_duplicate=True),
    Input("resetEditor", "n_clicks"),
    State({"type": "dynamic-output", "index": ALL}, "figure"),
    State("chartId", "value"),
    State({"type": "dynamic-card", "index": ALL}, "id"),
    prevent_initial_call=True,
)
def reset_figure(reset, figs, chartId, ids):
    for i in range(len(ids)):
        if ids[i]["index"] == chartId:
            if figs[i]["data"]:
                return figs[i]
    return {"data": [], "layout": {}}


@app.callback(
    Output("editor", "saveState"),
    Input("saveEditor", "n_clicks"),
    Input("saveCloseEditor", "n_clicks"),
)
def save_figure(n, n1):
    if n or n1:
        return True


@app.callback(
    Output("editorMenu", "opened", allow_duplicate=True),
    Input("saveCloseEditor", "n_clicks"),
    prevent_initial_call=True,
)
def close_editor(n):
    if n:
        return False
    return no_update


@app.callback(
    Output("grid-charts", "children", allow_duplicate=True),
    Input("editor", "figure"),
    State("chartId", "value"),
    State({"type": "dynamic-card", "index": ALL}, "id"),
    prevent_initial_call=True,
)
def save_to_card(f, v, ids):
    if f:
        figs = Patch()
        for i in range(len(ids)):
            if ids[i]["index"] == v:
                figs[i]["props"]["children"][1]["props"]["figure"] = f
                return figs
    return no_update


figures = html.Div(
    [
        dmc.Tabs([
                dmc.TabsList([
                    dmc.TabsTab("Charts", value="charts"),
                    dmc.TabsTab("Filters", value="filters"),
                    dmc.TabsTab("Filtered Data", value="filtered")
                ]),
                dmc.TabsPanel(dag.AgGrid(id={"index": 'filter-data', "type": "viz-information"}, rowData=data[main_file].to_dict('records'),
                                         columnDefs=[{'field': x} for x in data[main_file].columns],
                                         style={'height': '100%'}),
                              value='filtered', style={'height': '100%'}),
                dmc.TabsPanel([
                        dmc.Button("Add Chart", id="pattern-match-add-chart", n_clicks=0),
                        dmc.Button("Load Saved Charts", id="load-charts", n_clicks=0, color='red'),
                        dmc.Button("Save Chart Layout", id="save-charts", n_clicks=0, color='green'),
                        dmc.Group(id='grid-charts',
                                       style={'height': '100%', 'overflow': 'auto', 'padding': '10px'}),
                        chart_editor_modal,
                        dcc.Store(id="oldSum", data=0)], value='charts', style={"height": "100%"}),
                        dcc.Store(id='saved-charts', storage_type='local')

              ],
                value='charts',
                style={'height': 'calc(100vh + -150px)'}
            )
    ],
)

@callback(
    Output({"index": ALL, "type": "viz-information"}, "className"), Input("mode", "checked")
)
def updateClassNames(c):
    return ["ag-theme-alpine-dark" if c else "ag-theme-alpine"] * len(files)

@callback(
    Output('saved-charts', 'data'),
    Input('save-charts', 'n_clicks'),
    State({"type": "dynamic-output", "index": ALL}, 'figure'),
    prevent_initial_call=True
)
def saveCharts(_, c):
    figs = []
    for fig in c:
        figs.append(dce.cleanDataFromFigure(fig))
    return figs

@callback(
    Output('grid-charts', 'children', allow_duplicate=True),
    Output("pattern-match-add-chart", "n_clicks"),
    Input('load-charts', 'n_clicks'),
    State('saved-charts', 'data'),
    prevent_initial_call=True
)
def loadCharts(_, c):
    children = []
    clicks = 1
    for fig in c:
        children.append(make_card(clicks, dce.chartToPython(fig, data[main_file])))
        clicks += 1

    return children, clicks


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
    withCssVariables=True,
    withGlobalClasses=True,
    withStaticClasses=True
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

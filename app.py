import json
import math
from datetime import datetime, timedelta
from pathlib import Path

import folium
import geopandas as gpd
import pandas as pd
import pydeck as pdk
import streamlit as st

from folium.plugins import Draw
from streamlit_folium import st_folium

from src.fortyguard import run_heatmap
from src.live_analysis import analyze_heatmap_result

from policy_comparison import (
    POLICIES,
    compare_policies,
)

from budget_scenario_v2 import (
    run_budget_scenarios,
    calculate_marginal_benefit,
    get_next_intervention_value,
    recommend_policy,
)


# ============================================================
# CONFIG
# ============================================================

CACHED_GEOJSON_FILE = "tract_cooling_priority.geojson"

# Validated pilot area that worked previously.
PILOT_POLYGON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-74.0170, 40.7050],
                    [-74.0030, 40.7050],
                    [-74.0030, 40.7180],
                    [-74.0170, 40.7180],
                    [-74.0170, 40.7050],
                ]],
            },
        }
    ],
}

# Minimum practical AOI size for the first interactive test.
# This is a project safeguard, not a FortyGuard official limit.
MIN_AOI_KM2 = 0.02


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="CoolPriority",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# STYLE
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 0;
    }

    .subtitle {
        font-size: 18px;
        opacity: 0.72;
        margin-bottom: 24px;
    }

    .decision-box {
        padding: 20px;
        border-radius: 14px;
        border: 1px solid rgba(128,128,128,0.20);
        background: rgba(128,128,128,0.06);
        margin-bottom: 18px;
    }

    .allocation-card {
        padding: 16px;
        border-radius: 12px;
        border: 1px solid rgba(128,128,128,0.20);
        margin-bottom: 10px;
    }

    .policy-card {
        padding: 16px;
        border-radius: 12px;
        border: 1px solid rgba(128,128,128,0.20);
        min-height: 150px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "live_result": None,
    "live_activity_id": None,
    "live_error": None,
    "live_raw_response": None,
    "allocation_result": None,
    "comparison_result": None,
    "budget_scenario_result": None,
    "selected_polygon": PILOT_POLYGON,
    "area_mode": "Pilot Area",
}

for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# CACHED GEOJSON
# ============================================================

@st.cache_data
def load_cached_geojson():

    path = Path(
        CACHED_GEOJSON_FILE
    )

    if not path.exists():

        raise FileNotFoundError(
            f"{CACHED_GEOJSON_FILE} was not found."
        )

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


# ============================================================
# GEOJSON -> DATAFRAME
# ============================================================

def cached_geojson_to_dataframe(
    geojson,
):

    records = []

    for feature in geojson.get(
        "features",
        [],
    ):

        properties = feature.get(
            "properties",
            {},
        )

        records.append(
            {
                "GEOID":
                    properties.get(
                        "GEOID"
                    ),

                "TRACT_NAME":
                    properties.get(
                        "TRACT_NAME"
                    ),

                "cooling_priority_score":
                    properties.get(
                        "cooling_priority_score"
                    ),

                "priority_label":
                    properties.get(
                        "priority_label"
                    ),

                "heat_exposure_score":
                    properties.get(
                        "heat_exposure_score"
                    ),

                "social_vulnerability_score":
                    properties.get(
                        "social_vulnerability_score"
                    ),

                "heat_contribution":
                    properties.get(
                        "heat_contribution"
                    ),

                "vulnerability_contribution":
                    properties.get(
                        "vulnerability_contribution"
                    ),

                "geometry":
                    feature.get(
                        "geometry"
                    ),
            }
        )

    return pd.DataFrame(
        records
    )


# ============================================================
# COLORS
# ============================================================

def priority_color(
    label,
):

    if label == "Critical Priority":
        return [220, 38, 38, 185]

    if label == "High Priority":
        return [249, 115, 22, 180]

    if label == "Moderate Priority":
        return [234, 179, 8, 175]

    return [34, 197, 94, 165]


# ============================================================
# DATAFRAME -> GEOJSON
# ============================================================

def dataframe_to_geojson(
    df,
    selected_geoids=None,
):

    if selected_geoids is None:
        selected_geoids = set()

    features = []

    for _, row in df.iterrows():

        geoid = str(
            row["GEOID"]
        )

        is_selected = (
            geoid in selected_geoids
        )

        properties = {}

        for column in df.columns:

            if column == "geometry":
                continue

            value = row[column]

            if hasattr(
                value,
                "item",
            ):
                value = value.item()

            properties[column] = value

        if is_selected:

            properties["fill_color"] = [
                20,
                120,
                255,
                230,
            ]

            properties["selected"] = True

        else:

            properties["fill_color"] = (
                priority_color(
                    row["priority_label"]
                )
            )

            properties["selected"] = False

        geometry = row.get(
            "geometry"
        )

        if geometry is not None:

            if hasattr(
                geometry,
                "__geo_interface__",
            ):

                geometry = (
                    geometry
                    .__geo_interface__
                )

        features.append(
            {
                "type": "Feature",
                "properties": properties,
                "geometry": geometry,
            }
        )

    return {
        "type": "FeatureCollection",
        "features": features,
    }


# ============================================================
# POPULATION
# ============================================================

@st.cache_data
def load_population_data():

    svi_path = Path(
        "data/SVI_2022_US.csv"
    )

    if not svi_path.exists():
        return {}

    svi = pd.read_csv(
        svi_path,
        dtype={
            "FIPS": str
        },
    )

    svi["FIPS"] = (
        svi["FIPS"]
        .astype(str)
        .str.replace(
            ".0",
            "",
            regex=False,
        )
        .str.zfill(11)
    )

    svi_ny = svi[
        svi["ST_ABBR"] == "NY"
    ][
        [
            "FIPS",
            "E_TOTPOP",
        ]
    ].copy()

    return {
        row["FIPS"]:
            int(row["E_TOTPOP"])
        for _, row in svi_ny.iterrows()
    }


# ============================================================
# PERCENTILE
# ============================================================

def percentile_rank(
    values,
    value,
):

    if not values:
        return 0.0

    less_or_equal = sum(
        item <= value
        for item in values
    )

    return (
        (
            less_or_equal - 1
        )
        /
        max(
            len(values) - 1,
            1,
        )
    ) * 100.0


# ============================================================
# PREPARE POPULATION
# ============================================================

def prepare_population(
    df,
):

    df = df.copy()

    population_map = (
        load_population_data()
    )

    df["population"] = (
        df["GEOID"]
        .astype(str)
        .str.zfill(11)
        .map(
            population_map
        )
    )

    populations = (
        df["population"]
        .fillna(0)
        .tolist()
    )

    df[
        "population_reach_score"
    ] = (
        df["population"]
        .fillna(0)
        .apply(
            lambda value:
            percentile_rank(
                populations,
                value,
            )
        )
    )

    return df


# ============================================================
# AOI GEOMETRY HELPERS
# ============================================================

def get_polygon_coordinates(
    polygon,
):

    if not isinstance(
        polygon,
        dict,
    ):
        return None

    features = polygon.get(
        "features",
        [],
    )

    if not features:
        return None

    geometry = (
        features[0]
        .get("geometry")
    )

    if not geometry:
        return None

    if geometry.get(
        "type"
    ) != "Polygon":

        return None

    coordinates = geometry.get(
        "coordinates",
        [],
    )

    if not coordinates:
        return None

    outer_ring = coordinates[0]

    return outer_ring


def approximate_polygon_area_km2(
    coordinates,
):

    if not coordinates:
        return 0.0

    points = list(
        coordinates
    )

    if (
        len(points) > 1
        and points[0] == points[-1]
    ):
        points = points[:-1]

    if len(points) < 3:
        return 0.0

    average_latitude = (
        sum(
            point[1]
            for point in points
        )
        /
        len(points)
    )

    meters_per_degree_lat = 111_320.0

    meters_per_degree_lon = (
        111_320.0
        *
        math.cos(
            math.radians(
                average_latitude
            )
        )
    )

    origin_lon = points[0][0]
    origin_lat = points[0][1]

    xy = []

    for lon, lat in points:

        x = (
            lon - origin_lon
        ) * meters_per_degree_lon

        y = (
            lat - origin_lat
        ) * meters_per_degree_lat

        xy.append(
            (
                x,
                y,
            )
        )

    area = 0.0

    for i in range(
        len(xy)
    ):

        x1, y1 = xy[i]

        x2, y2 = xy[
            (i + 1)
            % len(xy)
        ]

        area += (
            x1 * y2
            -
            x2 * y1
        )

    area = abs(area) / 2.0

    return area / 1_000_000.0


def validate_aoi(
    polygon,
):

    coordinates = (
        get_polygon_coordinates(
            polygon
        )
    )

    if not coordinates:

        return {
            "valid": False,
            "message":
                "No valid Polygon geometry was found.",
            "area_km2": 0.0,
        }

    if len(coordinates) < 4:

        return {
            "valid": False,
            "message":
                "Polygon has too few points.",
            "area_km2": 0.0,
        }

    if coordinates[0] != coordinates[-1]:

        return {
            "valid": False,
            "message":
                "Polygon ring is not closed.",
            "area_km2": 0.0,
        }

    area_km2 = (
        approximate_polygon_area_km2(
            coordinates
        )
    )

    if area_km2 < MIN_AOI_KM2:

        return {
            "valid": False,
            "message":
                (
                    "The selected polygon is too small "
                    f"({area_km2:.4f} km²). "
                    "Draw a larger area."
                ),
            "area_km2": area_km2,
        }

    return {
        "valid": True,
        "message":
            "Polygon is valid.",
        "area_km2": area_km2,
    }


# ============================================================
# CREATE DRAW MAP
# ============================================================

def create_draw_map():

    fmap = folium.Map(
        location=[
            40.713,
            -74.009,
        ],
        zoom_start=13,
        control_scale=True,
    )

    Draw(
        export=False,

        draw_options={
            "polyline": False,
            "rectangle": False,
            "circle": False,
            "circlemarker": False,
            "marker": False,
            "polygon": True,
        },

        edit_options={
            "edit": True,
            "remove": True,
        },
    ).add_to(
        fmap
    )

    return fmap


# ============================================================
# EXTRACT DRAWING
# ============================================================

def extract_drawn_polygon(
    map_state,
):

    if not map_state:
        return None

    drawings = map_state.get(
        "all_drawings"
    )

    if not drawings:
        return None

    drawing = drawings[-1]

    geometry = drawing.get(
        "geometry"
    )

    if not geometry:
        return None

    if geometry.get(
        "type"
    ) != "Polygon":

        return None

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": geometry,
            }
        ],
    }


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🌡️ CoolPriority</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "Heat Vulnerability & Cooling-Priority Decision System"
    "</div>",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="decision-box">
        <b>Decision Question</b><br>
        Which areas should receive limited cooling resources first?
        <br><br>
        CoolPriority combines <b>FortyGuard hyperlocal heat intelligence</b>,
        <b>community vulnerability</b>, and <b>population context</b>
        to support cooling-resource decisions.
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR — ANALYSIS AREA
# ============================================================

st.sidebar.header(
    "🗺️ Analysis Area"
)

area_mode = st.sidebar.radio(
    "Choose analysis mode",
    [
        "Pilot Area",
        "Draw Your Area",
    ],
)

st.session_state.area_mode = area_mode


if area_mode == "Pilot Area":

    st.sidebar.success(
        "Using the validated pilot area."
    )

    st.session_state.selected_polygon = (
        PILOT_POLYGON
    )

else:

    st.sidebar.info(
        "Draw one polygon on the map below."
    )

    st.sidebar.caption(
        "For the first live test, draw an area "
        "roughly similar in size to the pilot area."
    )


# ============================================================
# SIDEBAR — LIVE FORTYGUARD
# ============================================================

st.sidebar.header(
    "Live FortyGuard Analysis"
)

st.sidebar.caption(
    "Only the Live button sends a request to FortyGuard."
)

start_date = st.sidebar.date_input(
    "Start date",
    value=datetime(
        2024,
        7,
        15,
    ).date(),
)

start_time = st.sidebar.time_input(
    "Start time",
    value=datetime(
        2024,
        7,
        15,
        14,
        0,
    ).time(),
)

analysis_hours = st.sidebar.number_input(
    "Analysis duration (hours)",
    min_value=1,
    max_value=24,
    value=1,
)

granularity = st.sidebar.selectbox(
    "Heatmap granularity",
    options=[
        60,
        80,
        100,
    ],
    index=2,
)

run_live = st.sidebar.button(
    "🚀 Run Live FortyGuard Analysis",
    type="primary",
)


# ============================================================
# DRAW YOUR AREA
# ============================================================

if area_mode == "Draw Your Area":

    st.header(
        "✏️ Draw Your Analysis Area"
    )

    st.markdown(
        """
        Draw **one polygon** on the map.

        The polygon becomes the exact Area of Interest
        sent to FortyGuard.
        """
    )

    draw_map = create_draw_map()

    draw_state = st_folium(
        draw_map,
        width=None,
        height=550,
        returned_objects=[
            "all_drawings",
        ],
        key="draw_area_map",
    )

    drawn_polygon = (
        extract_drawn_polygon(
            draw_state
        )
    )

    if drawn_polygon:

        validation = validate_aoi(
            drawn_polygon
        )

        if validation[
            "valid"
        ]:

            st.session_state.selected_polygon = (
                drawn_polygon
            )

            st.success(
                "✅ Analysis area selected."
            )

            st.metric(
                "Approximate AOI Area",
                f"{validation['area_km2']:.3f} km²",
            )

            coordinates = (
                get_polygon_coordinates(
                    drawn_polygon
                )
            )

            with st.expander(
                "🔎 Selected Polygon Coordinates"
            ):

                st.json(
                    coordinates
                )

        else:

            st.session_state.selected_polygon = None

            st.error(
                validation[
                    "message"
                ]
            )

    else:

        st.warning(
            "Draw a polygon before running Live Analysis."
        )


# ============================================================
# CURRENT AOI
# ============================================================

with st.expander(
    "🔎 Current Analysis Area"
):

    current_aoi = (
        st.session_state.selected_polygon
    )

    if current_aoi is None:

        st.write(
            "No valid AOI selected."
        )

    else:

        validation = validate_aoi(
            current_aoi
        )

        st.write(
            f"Status: "
            f"{'Valid' if validation['valid'] else 'Invalid'}"
        )

        st.write(
            f"Approximate Area: "
            f"{validation['area_km2']:.4f} km²"
        )

        st.json(
            current_aoi
        )


# ============================================================
# LIVE REQUEST
# ============================================================

if run_live:

    polygon_aoi = (
        st.session_state.selected_polygon
    )

    # --------------------------------------------------------
    # Validate AOI
    # --------------------------------------------------------

    if polygon_aoi is None:

        st.error(
            "Please select a valid analysis area first."
        )

        st.stop()

    aoi_validation = validate_aoi(
        polygon_aoi
    )

    if not aoi_validation[
        "valid"
    ]:

        st.error(
            aoi_validation[
                "message"
            ]
        )

        st.stop()

    try:

        start_datetime = datetime.combine(
            start_date,
            start_time,
        )

        end_datetime = (
            start_datetime
            + timedelta(
                hours=int(
                    analysis_hours
                )
            )
        )

        if analysis_hours == 1:

            filter_type = 1

            end_time_string = None

        else:

            filter_type = 2

            end_time_string = (
                end_datetime
                .time()
                .strftime(
                    "%H:%M"
                )
            )

        st.session_state.live_error = None
        st.session_state.live_raw_response = None

        with st.spinner(
            "Running live FortyGuard Heatmap..."
        ):

            response = run_heatmap(
                polygon_aoi=polygon_aoi,

                start_date=start_date.strftime(
                    "%Y-%m-%d"
                ),

                start_time=start_time.strftime(
                    "%H:%M"
                ),

                end_time=end_time_string,

                filter_type=filter_type,

                granularity=granularity,
            )

            # Save raw response for debugging.
            st.session_state.live_raw_response = (
                response
            )

            st.session_state.live_activity_id = (
                response.get(
                    "activity_id"
                )
            )

            # ------------------------------------------------
            # Inspect raw result before our engine parses it.
            # ------------------------------------------------

            raw_result = response.get(
                "result",
                {},
            )

            map_data = raw_result.get(
                "map_data",
                {},
            )

            features = map_data.get(
                "features",
                [],
            )

            st.info(
                f"FortyGuard returned "
                f"{len(features)} heatmap features."
            )

            # ------------------------------------------------
            # Stop cleanly if no cells returned.
            # ------------------------------------------------

            if not features:

                st.error(
                    "FortyGuard completed the activity "
                    "but returned zero Heatmap cells for "
                    "this AOI."
                )

                with st.expander(
                    "🔧 FortyGuard Raw Response"
                ):

                    st.json(
                        response
                    )

                st.stop()

            # ------------------------------------------------
            # Run our intelligence pipeline.
            # ------------------------------------------------

            live_df = (
                analyze_heatmap_result(
                    raw_result
                )
            )

            st.session_state.live_result = (
                live_df
            )

            # Reset downstream decision layers.
            st.session_state.allocation_result = None
            st.session_state.comparison_result = None
            st.session_state.budget_scenario_result = None

    except Exception as exc:

        st.session_state.live_result = None

        st.session_state.live_error = (
            str(exc)
        )


# ============================================================
# LIVE RAW RESPONSE
# ============================================================

if st.session_state.live_raw_response is not None:

    with st.expander(
        "🔧 Last FortyGuard Raw Response"
    ):

        st.json(
            st.session_state.live_raw_response
        )


# ============================================================
# ERROR
# ============================================================

if st.session_state.live_error:

    st.error(
        "Live analysis failed:\n"
        + st.session_state.live_error
    )


# ============================================================
# DATA SOURCE
# ============================================================

if (
    st.session_state.live_result
    is not None
):

    df = (
        st.session_state.live_result
        .copy()
    )

    data_mode = "LIVE"

else:

    cached_geojson = (
        load_cached_geojson()
    )

    df = (
        cached_geojson_to_dataframe(
            cached_geojson
        )
    )

    data_mode = "CACHED"


# ============================================================
# STATUS
# ============================================================

if data_mode == "LIVE":

    st.success(
        "🔴 LIVE MODE — Generated from a real FortyGuard request."
    )

    if st.session_state.live_activity_id:

        st.caption(
            "Activity ID: "
            + str(
                st.session_state.live_activity_id
            )
        )

else:

    st.info(
        "🟡 DEMO MODE — Using the validated pilot dataset."
    )


# ============================================================
# KPI
# ============================================================

critical_count = (
    df[
        "priority_label"
    ]
    == "Critical Priority"
).sum()

high_count = (
    df[
        "priority_label"
    ]
    == "High Priority"
).sum()

highest_priority = (
    df[
        "cooling_priority_score"
    ].max()
)

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Areas Analyzed",
    len(df),
)

c2.metric(
    "Critical",
    int(
        critical_count
    ),
)

c3.metric(
    "High",
    int(
        high_count
    ),
)

c4.metric(
    "Highest Priority",
    f"{highest_priority:.2f}/100",
)


# ============================================================
# LIVE HEAT STRESS CONTEXT
# ============================================================

st.header(
    "🔥 Heat Stress Context"
)

st.caption(
    "Heat context is calculated from the currently analyzed "
    "dataset. Live mode uses the temperature fields returned "
    "by FortyGuard."
)

required_temperature_columns = {
    "average_temperature",
    "maximum_temperature",
    "thermal_range",
}

available_temperature_columns = (
    required_temperature_columns
    .intersection(
        set(df.columns)
    )
)

# ============================================================
# LIVE / ENRICHED DATA
# ============================================================

if (
    required_temperature_columns
    .issubset(
        set(df.columns)
    )
):

    average_temperature = (
        pd.to_numeric(
            df[
                "average_temperature"
            ],
            errors="coerce",
        )
        .dropna()
    )

    maximum_temperature = (
        pd.to_numeric(
            df[
                "maximum_temperature"
            ],
            errors="coerce",
        )
        .dropna()
    )

    thermal_range = (
        pd.to_numeric(
            df[
                "thermal_range"
            ],
            errors="coerce",
        )
        .dropna()
    )

    # --------------------------------------------------------
    # Mean temperature
    # --------------------------------------------------------

    mean_temperature = (
        average_temperature.mean()
        if not average_temperature.empty
        else None
    )

    # --------------------------------------------------------
    # Maximum temperature
    # --------------------------------------------------------

    max_temperature = (
        maximum_temperature.max()
        if not maximum_temperature.empty
        else None
    )

    # --------------------------------------------------------
    # Percentage of analyzed areas >= 30°C
    # --------------------------------------------------------

    if not average_temperature.empty:

        hot_count = int(
            (
                average_temperature
                >= 30.0
            ).sum()
        )

        total_count = len(
            average_temperature
        )

        hot_percentage = (
            hot_count
            /
            total_count
            *
            100.0
        )

    else:

        hot_percentage = 0.0

    # --------------------------------------------------------
    # Mean thermal range
    # --------------------------------------------------------

    mean_thermal_range = (
        thermal_range.mean()
        if not thermal_range.empty
        else None
    )

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    h1, h2, h3, h4 = st.columns(4)

    h1.metric(
        "Mean Temperature",
        (
            f"{mean_temperature:.2f} °C"
            if mean_temperature is not None
            else "N/A"
        ),
    )

    h2.metric(
        "Maximum Temperature",
        (
            f"{max_temperature:.2f} °C"
            if max_temperature is not None
            else "N/A"
        ),
    )

    h3.metric(
        "Areas ≥ 30°C",
        f"{hot_percentage:.1f}%",
    )

    h4.metric(
        "Mean Thermal Range",
        (
            f"{mean_thermal_range:.2f} °C"
            if mean_thermal_range is not None
            else "N/A"
        ),
    )

    # --------------------------------------------------------
    # Interpretation
    # --------------------------------------------------------

    if hot_percentage >= 75:

        st.error(
            "A large share of the analyzed area has "
            "average temperatures at or above 30°C."
        )

    elif hot_percentage >= 50:

        st.warning(
            "A substantial share of the analyzed area "
            "has average temperatures at or above 30°C."
        )

    elif hot_percentage >= 25:

        st.warning(
            "A meaningful portion of the analyzed area "
            "has average temperatures at or above 30°C."
        )

    else:

        st.info(
            "Most analyzed areas have average temperatures "
            "below 30°C."
        )

    with st.expander(
        "ℹ️ Heat Stress Metric Definition"
    ):

        st.markdown(
            """
### Current Heat Stress Context

**Areas ≥ 30°C** represents the percentage of analyzed
heatmap areas whose average temperature is at or above 30°C.

This is a spatial heat-stress context metric.

It is **not** the same as FortyGuard's hourly
Exceedance/Persistence analytics.

The earlier 7.12-hour value belongs specifically to the
pilot time-range experiment and is therefore not reused
for arbitrary user-drawn areas.
"""
        )

# ============================================================
# CACHED DATASET
# ============================================================

else:

    st.info(
        "Temperature-level fields are not stored in the "
        "current cached GeoJSON. Run a Live FortyGuard "
        "analysis to display dynamic heat-stress metrics."
    )

    with st.expander(
        "ℹ️ Why are these metrics unavailable?"
    ):

        st.write(
            "The cached pilot GeoJSON contains priority-level "
            "fields such as Cooling Priority, Heat Exposure, "
            "and Social Vulnerability, but not the raw "
            "temperature columns required for this section."
        )

        st.write(
            "The Live FortyGuard pipeline does return these "
            "temperature fields."
        )
# ============================================================
# POPULATION
# ============================================================

allocation_df = prepare_population(
    df
)


# ============================================================
# RESOURCE ALLOCATION
# ============================================================

st.header(
    "🎯 Resource Allocation Simulator"
)

st.markdown(
    """
Choose a policy and number of interventions.

The result changes according to the decision objective.
"""
)

policy_name = st.selectbox(
    "Decision Policy",
    options=[
        "Need-First",
        "Balanced",
        "Reach-First",
    ],
)

st.caption(
    POLICIES[
        policy_name
    ]["description"]
)

budget = st.slider(
    "Available interventions",
    min_value=1,
    max_value=max(
        1,
        len(allocation_df),
    ),
    value=min(
        3,
        len(allocation_df),
    ),
)


# ============================================================
# SINGLE POLICY OPTIMIZATION
# ============================================================

if st.button(
    "⚡ Optimize Allocation"
):

    policy = POLICIES[
        policy_name
    ]

    temp = allocation_df.copy()

    temp[
        "impact_score"
    ] = (
        temp[
            "cooling_priority_score"
        ]
        * policy[
            "need_weight"
        ]
        +
        temp[
            "population_reach_score"
        ]
        * policy[
            "reach_weight"
        ]
    )

    temp = (
        temp
        .sort_values(
            "impact_score",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )

    selected = temp.head(
        min(
            budget,
            len(temp),
        )
    ).copy()

    total_population = (
        temp[
            "population"
        ].sum()
    )

    selected_population = (
        selected[
            "population"
        ].sum()
    )

    total_priority = (
        temp[
            "cooling_priority_score"
        ].sum()
    )

    selected_priority = (
        selected[
            "cooling_priority_score"
        ].sum()
    )

    st.session_state.allocation_result = {
        "selected":
            selected,

        "ranked":
            temp,

        "population_coverage":
            (
                selected_population
                /
                total_population
                * 100
                if total_population
                else 0
            ),

        "priority_coverage":
            (
                selected_priority
                /
                total_priority
                * 100
                if total_priority
                else 0
            ),
    }


# ============================================================
# DISPLAY ALLOCATION
# ============================================================

if (
    st.session_state.allocation_result
    is not None
):

    allocation = (
        st.session_state.allocation_result
    )

    selected = allocation[
        "selected"
    ]

    st.subheader(
        "Recommended Allocation"
    )

    a, b, c = st.columns(3)

    a.metric(
        "Population Coverage",
        f"{allocation['population_coverage']:.2f}%",
    )

    b.metric(
        "Priority Coverage",
        f"{allocation['priority_coverage']:.2f}%",
    )

    c.metric(
        "Selected Areas",
        len(selected),
    )

    for rank, (_, row) in enumerate(
        selected.iterrows(),
        start=1,
    ):

        st.markdown(
            f"""
            <div class="allocation-card">

            <b>#{rank} — Tract {row['TRACT_NAME']}</b><br><br>

            Cooling Priority:
            <b>{row['cooling_priority_score']:.2f}</b><br>

            Population:
            <b>{int(row['population']):,}</b><br>

            Population Reach:
            <b>{row['population_reach_score']:.2f}</b><br>

            Impact:
            <b>{row['impact_score']:.2f}</b>

            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# POLICY WHAT-IF
# ============================================================

st.header(
    "🔄 Policy What-If Comparison"
)

st.markdown(
    """
Same intervention budget, three different decision policies.
"""
)

if st.button(
    "📊 Compare All Policies"
):

    comparison = compare_policies(
        allocation_df,
        budget,
    )

    st.session_state.comparison_result = (
        comparison
    )


if (
    st.session_state.comparison_result
    is not None
):

    comparison = (
        st.session_state.comparison_result
    )

    policy_order = [
        "Need-First",
        "Balanced",
        "Reach-First",
    ]

    cols = st.columns(3)

    for column, policy in zip(
        cols,
        policy_order,
    ):

        result = comparison[
            policy
        ]

        with column:

            st.markdown(
                f"""
                <div class="policy-card">

                <h3>{policy}</h3>

                Population Coverage:
                <b>
                {result['population_coverage']:.2f}%
                </b>

                <br><br>

                Priority Coverage:
                <b>
                {result['priority_coverage']:.2f}%
                </b>

                <br><br>

                Impact:
                <b>
                {result['impact_sum']:.2f}
                </b>

                </div>
                """,
                unsafe_allow_html=True,
            )

    comparison_rows = []

    for policy in policy_order:

        result = comparison[
            policy
        ]

        comparison_rows.append(
            {
                "Policy":
                    policy,

                "Population Coverage":
                    result[
                        "population_coverage"
                    ],

                "Priority Coverage":
                    result[
                        "priority_coverage"
                    ],

                "Impact":
                    result[
                        "impact_sum"
                    ],

                "Selected Areas":
                    ", ".join(
                        result[
                            "selected"
                        ][
                            "TRACT_NAME"
                        ]
                        .astype(str)
                        .tolist()
                    ),
            }
        )

    comparison_df = pd.DataFrame(
        comparison_rows
    )

    st.dataframe(
        comparison_df,
        use_container_width=True,
    )

    st.subheader(
        "Policy Trade-off"
    )

    chart_df = comparison_df[
        [
            "Policy",
            "Population Coverage",
            "Priority Coverage",
        ]
    ].set_index(
        "Policy"
    )

    st.bar_chart(
        chart_df
    )


# ============================================================
# BUDGET WHAT-IF + MARGINAL BENEFIT
# ============================================================

st.header(
    "💰 Budget What-If Simulator"
)

st.markdown(
    """
What happens if the city has fewer or more cooling interventions?
"""
)

budget_options = sorted(
    {
        1,
        2,
        3,
        4,
        5,
        min(
            6,
            len(allocation_df),
        ),
        min(
            7,
            len(allocation_df),
        ),
    }
)

budget_options = [
    value
    for value in budget_options
    if value >= 1
]

if st.button(
    "💰 Run Budget What-If Analysis"
):

    scenario_df = (
        run_budget_scenarios(
            allocation_df,
            budget_options,
        )
    )

    scenario_df = (
        calculate_marginal_benefit(
            scenario_df
        )
    )

    st.session_state.budget_scenario_result = (
        scenario_df
    )


if (
    st.session_state.budget_scenario_result
    is not None
):

    scenario_df = (
        st.session_state
        .budget_scenario_result
    )

    st.subheader(
        "Budget Scenario Comparison"
    )

    st.dataframe(
        scenario_df,
        use_container_width=True,
    )

    # --------------------------------------------------------
    # Population chart
    # --------------------------------------------------------

    st.subheader(
        "Population Coverage vs Interventions"
    )

    population_chart = (
        scenario_df[
            [
                "Budget",
                "Policy",
                "Population Coverage",
            ]
        ]
        .pivot(
            index="Budget",
            columns="Policy",
            values="Population Coverage",
        )
    )

    st.line_chart(
        population_chart
    )

    # --------------------------------------------------------
    # Priority chart
    # --------------------------------------------------------

    st.subheader(
        "Priority Coverage vs Interventions"
    )

    priority_chart = (
        scenario_df[
            [
                "Budget",
                "Policy",
                "Priority Coverage",
            ]
        ]
        .pivot(
            index="Budget",
            columns="Policy",
            values="Priority Coverage",
        )
    )

    st.line_chart(
        priority_chart
    )

    # --------------------------------------------------------
    # Value of one more intervention
    # --------------------------------------------------------

    st.subheader(
        "📈 Value of One More Intervention"
    )

    cols = st.columns(3)

    for column, policy in zip(
        cols,
        [
            "Need-First",
            "Balanced",
            "Reach-First",
        ],
    ):

        value = (
            get_next_intervention_value(
                scenario_df,
                policy,
                budget,
            )
        )

        with column:

            st.markdown(
                f"### {policy}"
            )

            if value is None:

                st.info(
                    "No next-budget scenario available."
                )

            else:

                st.metric(
                    "Population Gain",
                    f"+{value['population_gain']:.2f}%",
                )

                st.metric(
                    "Priority Gain",
                    f"+{value['priority_gain']:.2f}%",
                )

                st.metric(
                    "Impact Gain",
                    f"+{value['impact_gain']:.2f}",
                )

    # --------------------------------------------------------
    # Objective recommendation
    # --------------------------------------------------------

    st.subheader(
        "🧭 Best Policy for Different Objectives"
    )

    cols = st.columns(3)

    objective_settings = [
        (
            "priority",
            "Maximize Priority Coverage",
        ),
        (
            "population",
            "Maximize Population Reach",
        ),
        (
            "balanced",
            "Balanced Objective",
        ),
    ]

    for column, (
        objective,
        title,
    ) in zip(
        cols,
        objective_settings,
    ):

        recommendation = (
            recommend_policy(
                scenario_df,
                budget=budget,
                objective=objective,
            )
        )

        with column:

            st.markdown(
                f"### {title}"
            )

            st.success(
                recommendation[
                    "policy"
                ]
            )

            st.write(
                f"Population Coverage: "
                f"{recommendation['population_coverage']:.2f}%"
            )

            st.write(
                f"Priority Coverage: "
                f"{recommendation['priority_coverage']:.2f}%"
            )


# ============================================================
# MAP
# ============================================================

st.header(
    "🗺️ Cooling Priority Map"
)

selected_geoids = set()

if (
    st.session_state.allocation_result
    is not None
):

    selected_df = (
        st.session_state
        .allocation_result[
            "selected"
        ]
    )

    selected_geoids = {
        str(value)
        for value in
        selected_df[
            "GEOID"
        ].tolist()
    }


map_geojson = (
    dataframe_to_geojson(
        df,
        selected_geoids,
    )
)

layer = pdk.Layer(
    "GeoJsonLayer",
    map_geojson,
    pickable=True,
    stroked=True,
    filled=True,
    get_fill_color=(
        "properties.fill_color"
    ),
    get_line_color=[
        70,
        70,
        70,
        180,
    ],
    line_width_min_pixels=1,
)

tooltip = {
    "html": """
    <b>Tract:</b>
    {TRACT_NAME}<br/>

    <b>Priority:</b>
    {priority_label}<br/>

    <b>Cooling Priority:</b>
    {cooling_priority_score}<br/>

    <b>Heat Exposure:</b>
    {heat_exposure_score}<br/>

    <b>Social Vulnerability:</b>
    {social_vulnerability_score}
    """,
    "style": {
        "backgroundColor": "white",
        "color": "black",
    },
}

deck = pdk.Deck(
    layers=[
        layer
    ],
    initial_view_state=(
        pdk.ViewState(
            latitude=40.713,
            longitude=-74.009,
            zoom=12.8,
            pitch=0,
        )
    ),
    tooltip=tooltip,
)

st.pydeck_chart(
    deck,
    use_container_width=True,
)


# ============================================================
# PRIORITY RANKING
# ============================================================

st.header(
    "🏆 Priority Ranking"
)

ranking_df = (
    df[
        [
            "TRACT_NAME",
            "cooling_priority_score",
            "priority_label",
            "heat_exposure_score",
            "social_vulnerability_score",
        ]
    ]
    .sort_values(
        "cooling_priority_score",
        ascending=False,
    )
    .reset_index(
        drop=True
    )
)

ranking_df.index += 1

st.dataframe(
    ranking_df,
    use_container_width=True,
)


# ============================================================
# AREA DETAILS
# ============================================================

st.header(
    "🔍 Decision Details"
)

if not df.empty:

    selected_area = st.selectbox(
        "Choose a Census Tract",
        df[
            "TRACT_NAME"
        ]
        .astype(str)
        .tolist(),
    )

    selected = df[
        df[
            "TRACT_NAME"
        ].astype(str)
        == selected_area
    ].iloc[0]

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Cooling Priority",
        f"{selected['cooling_priority_score']:.2f}/100",
    )

    c2.metric(
        "Heat Exposure",
        f"{selected['heat_exposure_score']:.2f}/100",
    )

    c3.metric(
        "Social Vulnerability",
        f"{selected['social_vulnerability_score']:.2f}/100",
    )

    st.subheader(
        "Why is this area prioritized?"
    )

    heat = float(
        selected[
            "heat_exposure_score"
        ]
    )

    vulnerability = float(
        selected[
            "social_vulnerability_score"
        ]
    )

    if (
        heat >= 75
        and vulnerability >= 75
    ):

        st.success(
            "High heat exposure combined with "
            "high social vulnerability makes this "
            "a top cooling priority."
        )

    elif heat >= 75:

        st.warning(
            "Very high heat exposure is the main "
            "driver of this area's priority."
        )

    elif vulnerability >= 75:

        st.warning(
            "High social vulnerability increases "
            "this area's cooling priority."
        )

    else:

        st.info(
            "Priority is driven by the combined "
            "heat and vulnerability signals."
        )


# ============================================================
# METHODOLOGY
# ============================================================

with st.expander(
    "📘 Methodology & Limitations"
):

    st.markdown(
        """
### FortyGuard

FortyGuard is the primary hyperlocal heat intelligence source.

### Heat Exposure

Current project-specific model:

- Average temperature
- Maximum temperature
- Thermal range

### Heat Burden

FortyGuard exceedance is used as contextual duration information.

The pilot showed perfect rank correlation between
Heat Exposure and Exceedance, so exceedance is not
double-counted inside Cooling Priority.

### Vulnerability

CDC/ATSDR SVI 2022.

### Population

`E_TOTPOP` from SVI 2022.

### Cooling Priority

`70% Heat Exposure + 30% Social Vulnerability`

### Resource Policies

Need-First:
- 85% Need
- 15% Population Reach

Balanced:
- 70% Need
- 30% Population Reach

Reach-First:
- 40% Need
- 60% Population Reach

### Important limitations

- Cooling Priority is a project-specific relative metric.
- It is not a medical risk score.
- It is not an official CDC/FortyGuard score.
- Population is potential reach, not guaranteed intervention coverage.
- Current pilot map uses a fixed NYC-area fallback.
- User-drawn areas use the actual polygon sent to FortyGuard.
- Tile-to-tract matching currently uses representative points.
"""
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "CoolPriority • FortyGuard Hackathon Prototype"
)
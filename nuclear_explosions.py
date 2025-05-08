"""
Name:    Santiago Giraudo
CS230:   Section 5
Data:    Nuclear Explosions 1945–1998 (nuclear_explosions.csv)
URL:    https://cs-230-final-project-nxtjqhj6gj9zbbekhf2vcz.streamlit.app/
Description:
This Streamlit app lets users explore the nuclear_explosions.csv dataset with
interactive filters for year, month, hemisphere, location, yield, seismic
magnitude, test depth, purpose, and data source.  After filtering, it shows
the count of matching detonations and will display charts and maps to help
tell the story of test frequency, yield distributions, and geographic spread.
"""
# Import necessary libraries for the Streamlit application, data manipulation, plotting, and mapping.
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pydeck as pdk
from datetime import date

# Defines a function to load and preprocess the nuclear explosions data.
# Uses Streamlit's caching to improve performance by only reloading data if the underlying file changes.
@st.cache_data
def load_data():
    # [PY3]
    # Attempts to read the CSV file into a pandas DataFrame.
    try:
        df = pd.read_csv("nuclear_explosions.csv")
    # Handles the case where the CSV file is not found.
    except FileNotFoundError:
        st.error("Error: nuclear_explosions.csv not found. Please ensure the file is in the correct directory.")
        return pd.DataFrame() # Return empty DataFrame
    # Handles any other exceptions that might occur during data loading.
    except Exception as e:
       st.error(f"An error occurred while loading the data: {e}")
       return pd.DataFrame()

    # [DA1] Clean and manipulate data: Converting date parts to a single datetime object
    # [DA7] Add/create new column ('Date'), Drop columns, Select columns implicitly
    # [DA9] Add a new column ('Date') based on existing columns
    # Combines year, month, and day columns into a single 'Date' column of datetime objects.
    df["Date"] = pd.to_datetime({
    "year":  df["Date.Year"],
    "month": df["Date.Month"],
    "day":   df["Date.Day"]
})
    # Drops the original individual date component columns as they are now combined.
    df.drop(columns=["Date.Year", "Date.Month", "Date.Day"], inplace=True)   # [DA7] Drop columns
    # [DA1] Clean and manipulate data: Renaming columns for clarity
    # Renames latitude and longitude columns for easier use, especially with mapping libraries.
    df.rename(columns={"Location.Cordinates.Latitude": "latitude", "Location.Cordinates.Longitude": "longitude"}, inplace=True)
    # [DA7] Add/create new column ('Yield.Avg')
    # [DA9] Add a new column and perform calculations on DataFrame columns
    # Calculates the average yield from the lower and upper yield estimates and stores it in a new column.
    df["Yield.Avg"] = (df["Data.Yield.Lower"] + df["Data.Yield.Upper"]) / 2
    # Returns the processed DataFrame.
    return df

# Loads the data using the defined function. This DataFrame will be used throughout the app.
df = load_data()


# [PY1] Function with two or more parameters, one default (custom_name), called multiple ways
# [PY2] Function returns more than one value (returns a dictionary with multiple key-value pairs)
# Defines a function to prepare data and configuration for different types of visualizations.
def prepare_chart_data(category, visual_id, df, purposes, custom_name="no name"):
    # Cleans the custom name provided by the user.
    stripped_custom_name = custom_name.strip()
    # Sets a final display name for the visual, using the custom name if provided, otherwise a default.
    if stripped_custom_name and stripped_custom_name.lower() != "no name":
        final_display_name = stripped_custom_name
    else:
        final_display_name = f"Visual #{visual_id}"

    # [PY5] Dictionary: 'result' is a dictionary, and its keys/values are accessed and modified.
    # Initializes a dictionary to store the results of the data preparation.
    result = {
        "success": False,
        "message": "Visual category not recognized or data preparation failed.",
        "chart_type": None,
        "data": {},
        "labels": {},
        "chart_specific_props": {},
        "final_display_name": final_display_name
    }

    # Checks if the input DataFrame is empty or None, setting an appropriate message if so.
    if df is None or df.empty:
        result["message"] = "No data available after filtering to generate visual."

    # Prepares data for a detailed map of detonations using PyDeck.
    elif category == "Map of Filtered Detonations":
        # [MAP] At least one detailed map (PyDeck ScatterplotLayer) with hover text, custom colors
        result["chart_type"] = "pydeck_scatter_detailed"
        # Selects relevant columns for the map and creates a copy.
        points_df = df[['latitude', 'longitude', 'Data.Name', 'Date', 'Yield.Avg', 'WEAPON SOURCE COUNTRY']].copy()
        # [DA1] Clean or manipulate data: Coercing to numeric and filling NA for 'Yield.Avg'
        # Ensures 'Yield.Avg' is numeric and fills missing values with 0 for map rendering.
        points_df['Yield.Avg'] = pd.to_numeric(points_df['Yield.Avg'], errors='coerce').fillna(0)
        # Converts 'Date' column to string format for display in map tooltips.
        points_df['Date_str'] = points_df['Date'].dt.strftime('%Y-%m-%d')
        # [PY5] Dictionary: Using a dictionary for color mapping
        # Defines a color map for different weapon source countries.
        country_color_map = {
           "USA": [0, 0, 255, 180],    # Blue for USA
            "USSR": [255, 0, 0, 180],   # Red for USSR
            "FRANCE": [0, 255, 0, 180], # Green for FRANCE
            "UK": [255, 165, 0, 180], # Orange for UK
            "CHINA": [255, 255, 0, 180],# Yellow for CHINA
            "INDIA": [255, 105, 180, 180], # Pink for INDIA
            "PAKIST": [75, 0, 130, 180], # Indigo for PAKISTAN
        }

        # If data points are available, updates the result dictionary with map data and properties.
        if not points_df.empty:
            result.update({
                "success": True, "message": "Data prepared for detailed PyDeck map.",
                "data": {"points_df": points_df},
                "chart_specific_props": {"color_map": country_color_map}
            })
        # If no valid coordinate data, sets an appropriate message.
        else:
            result["message"] = "No valid coordinate data for map."

    # Prepares data for a histogram of average yields.
    elif category == "Histogram of Average Yields":
        # [VIZ1] Chart 1: Histogram with title, colors, labels
        result["chart_type"] = "hist"
        # Extracts and drops NaN values from the 'Yield.Avg' column for the histogram.
        data_values = df['Yield.Avg'].dropna()
        # If data values exist, updates the result dictionary with histogram data and properties.
        if not data_values.empty:
            result.update({
                "success": True,
                "message": "Data prepared for histogram.",
                "data": {"values": data_values},
                "labels": {"x_label": "Average Yield (kt)", "y_label": "Number of Detonations"},
                "chart_specific_props": {"bins": 20, "color": "skyblue", "edgecolor": "black"}
            })
        # If no yield data, sets an appropriate message.
        else:
            result["message"] = "No 'Yield.Avg' data (all NaN or empty) to display histogram."

    # Prepares data for a timeline plot of detonations by year.
    elif category == "Timeline: Detonations by Year":
        # [VIZ2] Chart 2: Line plot with title, colors, labels, markers
        result["chart_type"] = "plot"
        # Extracts the 'Date' column.
        temp_dates = df['Date']
        # [DA7] Group columns (effectively, by year then counting)
        # [DA2] Sort data (by index, which is the year)
        # Counts the number of detonations per year and sorts by year.
        detonations_by_year = temp_dates.dt.year.value_counts().sort_index()
        # If data exists, updates the result dictionary with timeline data and properties.
        if not detonations_by_year.empty:
            result.update({
                "success": True,
                "message": "Data prepared for timeline.",
                "data": {"x_values": detonations_by_year.index, "y_values": detonations_by_year.values},
                "labels": {"x_label": "Year", "y_label": "Number of Detonations"},
                "chart_specific_props": {"marker": "o", "linestyle": "-", "color": "green"}
            })
        # If no timeline data, sets an appropriate message.
        else:
            result["message"] = "No data to plot timeline by year after processing."

    # Prepares data for a bar chart of detonations by purpose.
    elif category == "Bar Chart: Detonations by Purpose":
        # [VIZ3] Chart 3: Bar chart with title, colors, labels
        result["chart_type"] = "barh" # Horizontal bar chart
        # [DA1] Manipulate data: Mapping purpose codes to full names
        # [PY5] Dictionary: Accessing 'purposes' dictionary with .get()
        # Maps purpose codes to their full names using the 'purposes' dictionary, then counts occurrences.
        purpose_series = df['Data.Purpose'].map(lambda x: purposes.get(x, str(x))).dropna()
        purpose_counts = purpose_series.value_counts()    # [DA7] Group columns (by purpose then counting)
        # If data exists, updates the result dictionary with bar chart data and properties.
        if not purpose_counts.empty:
            result.update({
                "success": True,
                "message": "Data prepared for bar chart.",
                "data": {"y_categories": purpose_counts.index.tolist(), "x_values": purpose_counts.values.tolist()},
                "labels": {"x_label": "Number of Detonations"},
                "chart_specific_props": {"color": "coral"}
            })
        # If no purpose data, sets an appropriate message.
        else:
            result["message"] = "No 'Data.Purpose' entries found or all are NaN after mapping."

    # Prepares data for a scatter plot of yield versus depth.
    elif category == "Scatter Plot: Yield vs. Depth":
        result["chart_type"] = "scatter"
        # Selects 'Yield.Avg' and 'Location.Cordinates.Depth' columns and drops rows with any NaN values.
        plot_df = df[['Yield.Avg', 'Location.Cordinates.Depth']].copy().dropna()  # [DA7] Select columns
        # If enough valid data points exist, updates the result dictionary.
        if not plot_df.empty and len(plot_df) > 1:
            result.update({
                "success": True,
                "message": "Data prepared for scatter plot.",
                "data": {"x_values": plot_df['Location.Cordinates.Depth'], "y_values": plot_df['Yield.Avg']},
                "labels": {"x_label": "Depth (km)", "y_label": "Average Yield (kt)"},
                "chart_specific_props": {"alpha": 0.6, "edgecolors": "w", "linewidth": 0.5}
            })
        # If not enough data, sets an appropriate message.
        else:
            result["message"] = "Not enough valid data points (Yield & Depth) for scatter plot after dropping NaNs."

    # Prepares data for a pie chart of detonations by supplier nation.
    elif category == "Pie Chart: Detonations by Supplier Nation":
        # [VIZ4] Chart 3: Pie Chart
        result["chart_type"] = "pie"
        # Counts detonations by 'WEAPON SOURCE COUNTRY'.
        supplier_counts = df['WEAPON SOURCE COUNTRY'].value_counts()  # [DA7] Group columns
        # If data exists, updates the result dictionary with pie chart data and properties.
        if not supplier_counts.empty:
            result.update({
                "success": True,
                "message": "Data prepared for pie chart.",
                "data": {"sizes": supplier_counts.values.tolist(), "labels": supplier_counts.index.tolist()},
                "labels": {},  # Pie chart labels are typically part of the data itself
                "chart_specific_props": {"autopct": "%.1f%%", "startangle": 90}
            })
        # If no supplier data, sets an appropriate message.
        else:
            result["message"] = "No 'WEAPON SOURCE COUNTRY' data to display pie chart."
    # Handles cases where the visual category is not recognized.
    else:
        result["message"] = f"The visual category '{category}' is not recognized or implemented."
    # Returns the dictionary containing all prepared information for the chart.
    return result   # [PY2] returning the 'result' dictionary

# [PY5] Dictionary: 'purpose_map' is a dictionary used for mapping codes to descriptions.
# Defines a dictionary to map abbreviated purpose codes to more descriptive text.
purpose_map = {
    "Combat": "Combat Test",
    "Fms": "Fission Material Safety",
    "Fms/Wr": "Fission Material Safety & Warhead Research",
    "Me": "Meteorological Experiment",
    "Nan": "Naval Accident",
    "Pne": "Peaceful Nuclear Explosion",
    "Pne/Wr": "Peaceful Nuc. Expl. & Warhead Research",
    "Pne:Plo": "Peaceful Expl. (Plowshare)",
    "Pne:V": "Peaceful Expl. (Vessel/Channel)",
    "Sam": "Surface Area Measurement",
    "Sb": "Seismic Benchmark",
    "Se": "Safety Experiment",
    "Se/Wr": "Safety & Warhead Research",
    "Transp": "Transportation Test",
    "We": "Weapon Experiment",
    "We/Sam": "Weapon & Surface Area",
    "We/Wr": "Weapon & Warhead Research",
    "Wr": "Warhead Research",
    "Wr/F/S": "Warhead, Fissile & Safety",
    "Wr/F/Sa": "Warhead, Fissile & Surface Area",
    "Wr/Fms": "Warhead & Fissile Material Safety",
    "Wr/P/S": "Warhead, Plowshare & Safety",
    "Wr/P/Sa": "Warhead, Plowshare & Surface Area",
    "Wr/Pne": "Warhead & Peaceful Expl.",
    "Wr/Sam": "Warhead & Surface Area",
    "Wr/Se": "Warhead & Safety",
    "Wr/We": "Warhead & Weapon",
    "Wr/We/S": "Warhead, Weapon & Safety"
}


# [ST4] Customized page design features (sidebar as a major design element)
# Configures the Streamlit sidebar for user inputs and filters.
with st.sidebar:
    # Adds a header to the sidebar.
    st.sidebar.header("🛠️ Filters")
    # Creates an empty placeholder in the sidebar to display the count of filtered detonations later.
    count_placeholder = st.empty()

    # Determines the minimum and maximum years from the 'Date' column for filter ranges.
    min_year, max_year = int(df["Date"].dt.year.min()), int(df["Date"].dt.year.max())
    # Defines the overall minimum and maximum possible dates for date pickers.
    min_date, max_date = date(min_year, 1, 1), date(max_year, 12, 31)

    # Adds a subheader for the date filter section.
    st.sidebar.header("📅 Date Filter")
    # Informs the user about the available date range.
    st.write(f"We have data on detonations from {min_year} to {max_year}.")
    # [ST1] Streamlit Widget 1: Checkbox
    # Adds a checkbox to allow users to switch between a year slider and an exact date range picker.
    use_exact = st.checkbox("Use exact date range", key="use_exact_date")
    # Initializes start and end dates for filtering with the full range.
    start, end = pd.Timestamp(min_date), pd.Timestamp(max_date)
    # If the user chooses to use an exact date range:
    if use_exact:
        # Creates a form for the date input to apply changes only upon submission.
        with st.form("date_filter_form"):
            # [ST2] Streamlit Widget 2: Date Input (within a form)
            # Adds a date input widget for selecting a start and end date.
            start_date, end_date = st.date_input(
                "Select exact date range:",
                value=(min_date, max_date),  # Default value spans all available dates.
                min_value=min_date,          # Minimum selectable date.
                max_value=max_date,          # Maximum selectable date.
                key="date_range"
            )
            # Adds a submit button to the form.
            apply = st.form_submit_button("Apply date filter")

            # Updates the working start and end timestamps if the form is submitted.
            if apply:
                st.caption(f"*Showing detonations from {start_date} to {end_date}*")
                start, end = pd.Timestamp(start_date), pd.Timestamp(end_date)

    # If the user chooses to use the year slider:
    else:
        # [ST3] Streamlit Widget 3: Slider
        # Adds a range slider for selecting a start and end year.
        start_y, end_y = st.slider(
            f"Select time window below:",
            min_year, max_year,            # Slider minimum and maximum values.
            (min_year, max_year),          # Default selection spans all years.
            key="year_range"
        )
        # Converts the selected years to full start and end timestamps for filtering.
        start, end = pd.Timestamp(year=start_y, month=1, day=1), pd.Timestamp(year=end_y,   month=12,day=31)

    # Adds a blank line for visual spacing in the sidebar.
    st.write("")

    # HEMISPHERE FILTER section.
    st.sidebar.header("🌐 Hemisphere")
    # Adds a selectbox for filtering detonations by hemisphere.
    hemisphere = st.selectbox(
        "Filter by the Detonation Hemisphere:",
        options=["All", "Northern", "Southern"], # Available options.
        index=0,  # Default to "All".
        key = "hemisphere"
    )

    # [DA4] Build numeric bounds for latitude filtering
    # Sets latitude boundaries based on the selected hemisphere.
    if hemisphere == "Northern":
        lat_low, lat_high = 0, 90    # Northern hemisphere latitude range.
    elif hemisphere == "Southern":
        lat_low, lat_high = -90, 0   # Southern hemisphere latitude range.
    else: # "All"
        lat_low, lat_high = -90, 90  # Full latitude range.

    # Adds spacing.
    st.write("")

    # COUNTRY OF DETONATION FILTER section.
    st.sidebar.header("🗺️ Countries of Detonation")
    # Calculates the total number of unique deployment locations.
    total_countries = df["WEAPON DEPLOYMENT LOCATION"].nunique()
    # Creates a placeholder to display the number of selected countries.
    count_slot_country = st.empty()

    # Uses an expander to make the multiselect for countries collapsible.
    with st.expander("🔽 Selected Countries"):
        # [ST3] Streamlit Widget 3: Multiselect
        # Adds a multiselect widget for choosing deployment locations.
        countries = st.multiselect(
            "", # No extra label needed.
            # [DA2] Sort data (sorting unique supplier names for the multiselect options)
            options=sorted(df["WEAPON DEPLOYMENT LOCATION"].unique()), # Options are sorted unique locations.
            default=sorted(df["WEAPON DEPLOYMENT LOCATION"].unique()),  # All locations selected by default.
            key = "country_sel"
        )
    # Updates the placeholder with the count of currently selected countries.
    count_slot_country.write(f"✅ {len(countries)} selected")
    # Displays the total number of available locations.
    st.caption(f"🌐 Total Locations: {total_countries}")

    # Adds spacing.
    st.write("")

    # SUPPLIER FILTER section.
    st.sidebar.header("🏭 Supplier Nations")
    # Creates a placeholder for the supplier count.
    count_slot_supplier = st.empty()

    # Uses an expander for the supplier multiselect.
    with st.expander("🔽 Selected Suppliers"):
        # Adds a multiselect for choosing weapon source countries.
        suppliers = st.multiselect(
            "", # No extra label.
            #[DA2]
            options=sorted(df["WEAPON SOURCE COUNTRY"].unique()), # Sorted unique supplier countries.
            default=sorted(df["WEAPON SOURCE COUNTRY"].unique()),  # All suppliers selected by default.
            key="supplier_sel"
        )
    # Displays the number of selected suppliers.
    count_slot_supplier.write(f"✅ {len(suppliers)} selected")
    # Displays the total number of unique suppliers.
    st.caption(f"🌐 Total suppliers: {df['WEAPON SOURCE COUNTRY'].nunique()}")

    # Adds spacing.
    st.write("")

    # YIELD FILTER section.
    st.sidebar.header("💥 Yield (kt)")
    # Determines the minimum and maximum average yields from the data.
    min_yield = float(df["Yield.Avg"].min())
    max_yield = float(df["Yield.Avg"].max())

    # Adds a range slider for filtering by average explosion yield.
    y_low, y_high = st.slider(
        "Filter by average estimated explosion yield in kilotons of TNT:", # Label for the slider.
        min_yield, max_yield,                 # Slider min and max values.
        (min_yield, max_yield),               # Default selection spans all yields.
        key = "yield_range"
    )
    # Displays the currently selected yield range with two-decimal precision.
    st.caption(f"Showing tests with average explosion yield between {y_low:.2f}kt and {y_high:.2f}kt")

    # Adds spacing.
    st.write("")

    # SEISMIC MAGNITUDE FILTERS section.
    st.sidebar.header("📈 Seismic Magnitudes")
    st.sidebar.write("Filter by recorded body & surface wave magnitudes:")
    # Computes the full min/max range for body wave magnitudes.
    min_body, max_body = float(df["Data.Magnitude.Body"].min()), float(df["Data.Magnitude.Body"].max())
    # Computes the full min/max range for surface wave magnitudes.
    min_surface, max_surface = float(df["Data.Magnitude.Surface"].min()), float(df["Data.Magnitude.Surface"].max())

    # Uses an expander to group the magnitude sliders.
    with st.sidebar.expander("🔽 Select Magnitude Ranges"):
        # Adds a range slider for body-wave magnitude.
        body_low, body_high = st.slider(
            "Body-wave magnitude",
            min_body, max_body,
            (min_body, max_body), # Default full range.
            key="body_mag"
        )
        # Adds a range slider for surface-wave magnitude.
        surface_low, surface_high = st.slider(
            "Surface-wave magnitude",
            min_surface, max_surface,
            (min_surface, max_surface), # Default full range.
            key="surface_mag"
        )

    # Adds spacing.
    st.write("")

    # TEST Type FILTER section.
    st.sidebar.header("🔧 Test Deployment Type")
    st.write("Filter by deployment types:")
    # Gets a sorted list of unique deployment types.
    all_modes = sorted(df["Data.Type"].unique())
    # Placeholder for selected types count.
    count_slot_mode = st.empty()

    # Expander for deployment type multiselect.
    with st.expander("🔽 Selected Types"):
        # Adds a multiselect for choosing deployment types.
        modes = st.multiselect(
            "",
            options=all_modes,    # All unique types as options.
            default=all_modes,    # All types selected by default.
            key = "mode_sel"
        )
    # Displays the number of selected deployment types.
    count_slot_mode.write(f"✅ {len(modes)} type(s) selected")
    # Displays the total number of unique types.
    st.caption(f"🌐 Total types: {len(all_modes)}")

    # TEST DEPTH FILTER section.
    st.write("") # Adds spacing.
    st.sidebar.header("📐 Test Depth")
    st.write("Filter by detonation depth (km):")
    # Computes the full min/max range for test depth.
    min_depth, max_depth = float(df["Location.Cordinates.Depth"].min()), float(df["Location.Cordinates.Depth"].max())

    # Adds a range slider for test depth.
    d_low, d_high = st.slider(
        "From Above Ground (-) to Below Ground (+)", # Label for the slider.
        min_depth, max_depth,                 # Slider min and max values.
        (min_depth, max_depth),               # Default full range.
        key = "depth_range"
    )
    # The caption for active depth window was commented out in original code, so not adding one here.

    # PURPOSE FILTER section.
    st.write("") # Adds spacing.
    st.sidebar.header("🎯 Purpose of Detonation")
    st.write("Pick one or more purposes:")
    # Counts the number of unique raw purpose codes.
    raw_purposes = df["Data.Purpose"].nunique()
    # Placeholder for selected purposes count.
    count_slot_purpose = st.empty()

    # Expander for purpose multiselect.
    with st.expander("🔽 Selected Purposes"):
        # Adds a multiselect for choosing test purposes.
        purposes = st.multiselect(
            "",
            options=sorted(df["Data.Purpose"].unique()), # Sorted unique purpose codes.
            default=sorted(df["Data.Purpose"].unique()), # All purposes selected by default.
            format_func = lambda code: purpose_map.get(code, code), # Displays full names from purpose_map.
            key="purpose_sel"
        )
    # Displays the number of selected purposes.
    count_slot_purpose.write(f"✅ {len(purposes)} selected")
    # Displays the total number of unique raw purpose codes.
    st.caption(f"🌐 Total purposes: {raw_purposes}")

    # Adds spacing.
    st.write("")

    #DATA SOURCE FILTER section.
    st.sidebar.header("📑 Data Source")
    st.sidebar.write("Filter by reporting agency:")
    # Gets a sorted list of unique data sources, dropping any NaNs.
    sources = sorted(df["Data.Source"].dropna().unique())
    # Placeholder for selected sources count.
    count_slot_source = st.empty()

    # Expander for data source multiselect.
    with st.expander("🔽 Selected Sources"):
        # Adds a multiselect for choosing data sources.
        selected_sources = st.multiselect(
            "",
            options=sources,    # All unique sources.
            default=sources,    # All sources selected by default.
            key="source_sel"
        )
    # Displays the number of selected data sources.
    count_slot_source.write(f"✅ {len(selected_sources)} selected")
    # Displays the total number of unique data sources.
    st.sidebar.caption(f"🌐 Total sources: {len(sources)}")

# [DA5] Filter data by two or more conditions with AND or OR
# Applies all selected filters to the main DataFrame to create a 'filtered_df'.
# Each condition is combined using the logical AND (&) operator.
filtered_df = df[
    df["Date"].between(start, end) &                                  # Date range filter.
    df["latitude"].between(lat_low, lat_high) &                       # Hemisphere (latitude) filter.
    df["WEAPON DEPLOYMENT LOCATION"].isin(countries) &                # Deployment location filter.
    df["WEAPON SOURCE COUNTRY"].isin(suppliers) &                     # Supplier nation filter.
    df["Yield.Avg"].between(y_low, y_high) &                          # Yield range filter.
    df["Data.Magnitude.Body"].between(body_low, body_high) &          # Body wave magnitude filter.
    df["Data.Magnitude.Surface"].between(surface_low, surface_high) & # Surface wave magnitude filter.
    df["Data.Type"].isin(modes) &                                     # Test type filter.
    df["Location.Cordinates.Depth"].between(d_low, d_high) &          # Test depth filter.
    df["Data.Purpose"].isin(purposes) &                               # Purpose filter.
    df["Data.Source"].isin(selected_sources)                          # Data source filter.
]
# Updates the placeholder in the sidebar to show the number of detonations after filtering.
count_placeholder.markdown(f"## 💥 Showing **{len(filtered_df)}** Detonations")

# [ST4] Customized page design features (using an image as a header)
# Defines the filename for the header image.
HEADER_IMG = "nuke_header.png"
# Displays the header image, making it fit the container width.
st.image(HEADER_IMG, use_container_width=True)
# Sets the main title of the Streamlit application.
st.title("🔬 Nuclear Explosions Explorer")

# Adds a horizontal rule for visual separation.
st.markdown("---")

# --- "Cool" Code Section ---
# This section manages dynamic visual generation using Streamlit's session state.
# It allows users to add multiple, configurable charts to the page one by one,
# and these charts persist across reruns until cleared or modified.
# This provides a flexible and interactive way for users to build their own
# data exploration dashboard.

# Adds a header for the custom visualizations section.
st.header("📊 Custom Visualizations")
# Provides instructions to the user.
st.write(" 🔍 You can use the sidebar to filter by year, yield, location, and more to tell the story of every detonation from 1945–1998.")
st.write("Select a type of visual and click 'Add' to create it based on current filters (max 10).")

# Initializes 'visuals_to_render' list in session state if it doesn't exist. This list stores specs for visuals to be displayed.
if 'visuals_to_render' not in st.session_state:
    st.session_state.visuals_to_render = []
# Initializes 'visual_id_counter' in session state if it doesn't exist. This counter ensures unique IDs for visuals.
if 'visual_id_counter' not in st.session_state:
    st.session_state.visual_id_counter = 0

# Defines the list of available visual categories for the user to choose from.
VISUAL_CATEGORY_OPTIONS = [
    "Map of Filtered Detonations",
    "Histogram of Average Yields",
    "Timeline: Detonations by Year",
    "Bar Chart: Detonations by Purpose",
    "Scatter Plot: Yield vs. Depth",
    "Pie Chart: Detonations by Supplier Nation"
]

# Adds a subheader for the "Add a New Visual" section.
st.subheader("Add a New Visual")

# Creates a form for adding a new visual. Using a form ensures that inputs are processed together on submission.
with st.form("add_visual_form", clear_on_submit=True): # Clears the form inputs after submission.
    # Creates two columns for layout: one for visual type selection, one for optional naming.
    col_type, col_name = st.columns([2,2])

    # Column for selecting the visual category.
    with col_type:
        visual_category = st.selectbox(
            "Choose visual category:",
            options=["Select a category..."] + VISUAL_CATEGORY_OPTIONS, # Adds a placeholder option.
            key="new_visual_category_selector_form"
        )
    # Column for optionally naming the visual.
    with col_name:
        visual_name = st.text_input(
            "Optional: Name this visual:",
            key="custom_visual_name_input_form"
        )
    # Submit button for the form.
    submitted = st.form_submit_button("➕ Add Visual")

# Adds another horizontal rule for separation.
st.markdown("---")
# Processes the form submission if the "Add Visual" button was clicked.
if submitted:
    # Checks if a valid visual category was selected.
    if visual_category != "Select a category...":
        # Checks if the maximum number of visuals (10) has not been reached.
        if st.session_state.visual_id_counter < 10:
            # Increments the visual ID counter.
            st.session_state.visual_id_counter += 1
            current_vis_id = st.session_state.visual_id_counter
            # Appends the specification for the new visual to the session state list.
            st.session_state.visuals_to_render.append({
                "id": current_vis_id,
                "type": visual_category,
                "user_input_name": visual_name
            })
            # Shows a success toast message.
            st.toast(f"Added '{visual_category}' request.", icon="✅")
        # If maximum visuals reached, shows a warning.
        else:
            st.warning("Maximum of 10 visuals reached.")
            st.toast("Maximum of 10 visuals reached.", icon="⚠️")
    # If no visual category was selected, shows a warning.
    else:
        st.warning("Please select a visual category before adding.")
        st.toast("Select a visual category first.", icon="👇")

# Checks if there are any visuals to render, stored in the session state.
if 'visuals_to_render' in st.session_state and st.session_state.visuals_to_render:
    # Iterates through each visual specification in the list.
    for visual_spec in st.session_state.visuals_to_render:
        current_id = visual_spec["id"]
        current_category = visual_spec["type"]
        user_input_name = visual_spec["user_input_name"]

        # Calling the function that has [PY1] (default param) and [PY2] (returns multiple values
        # Prepares the data for the current visual using the filtered DataFrame and other relevant info.
        chart_info = prepare_chart_data(
            category=current_category,
            visual_id=current_id,
            df=filtered_df,          # Passes the currently filtered DataFrame.
            purposes=purpose_map,    # Passes the purpose mapping dictionary.
            custom_name=user_input_name # Passes the user-defined name for the visual.
        )
        # Creates a container for each visual to group its elements and optionally add a border.
        with st.container(border= True, key=f"container_visual_{current_id}"):
            # Displays the final name of the visual as a subheader.
            st.markdown(f"#### 🖼️ {chart_info['final_display_name']}")
            # If data preparation was successful:
            if chart_info["success"]:
                # Extracts chart type, data, labels, and properties from the prepared chart information.
                chart_type = chart_info.get("chart_type")
                chart_data = chart_info.get("data", {})
                chart_labels = chart_info.get("labels", {})
                chart_props = chart_info.get("chart_specific_props", {})
                render_key = f"render_{chart_type}_{current_id}" # Unique key for rendering elements if needed.

                # Renders a detailed PyDeck scatter plot map if the chart type matches.
                if chart_type == "pydeck_scatter_detailed":
                    points_data = chart_data.get("points_df")
                    map_props = chart_info.get("chart_specific_props", {})
                    color_map = map_props.get("color_map")
                    # Defines how to get color for each point based on its source country.
                    def get_color(country):
                        lookup_key = str(country).strip().upper()
                        return color_map.get(lookup_key) # Uses the predefined country_color_map.

                    # Checks if there is data to plot on the map.
                    if points_data is not None and not points_data.empty:
                        # Applies the color mapping function to create a 'color' column in the points data.
                        points_data['color'] = points_data['WEAPON SOURCE COUNTRY'].apply(get_color)
                        # Defines the ScatterplotLayer for PyDeck.
                        layer = pdk.Layer(
                            "ScatterplotLayer",
                            data=points_data,
                            get_position=["longitude", "latitude"], # Specifies columns for coordinates.
                            get_fill_color="color",                # Uses the 'color' column for point colors.
                            get_radius= 35000,                     # Sets a fixed radius for points.
                            pickable=True,                         # Allows points to be hovered/clicked.
                            auto_highlight=True                    # Highlights points on hover.
                        )
                        # Defines the tooltip content and style for map interactivity.
                        tooltip = {
                            "html": "<b>Name:</b> {Data.Name}<br/>"
                                    "<b>Date:</b> {Date_str}<br/>"
                                    "<b>Avg Yield (kt):</b> {Yield.Avg}<br/>"
                                    "<b>Supplier:</b> {WEAPON SOURCE COUNTRY}<br/>"
                                    "<i>Lat: {latitude}, Lon: {longitude}</i>",
                            "style": {"backgroundColor": "steelblue", "color": "white"}
                        }
                        # Creates the PyDeck Deck object with the layer, map style, and tooltip.
                        deck = pdk.Deck(
                            layers=[layer],
                            map_style='mapbox://styles/mapbox/dark-v9', # Dark theme map.
                            tooltip=tooltip
                        )
                        # [MAP] is Displayed
                        # Renders the PyDeck chart in Streamlit.
                        st.pydeck_chart(deck, use_container_width=True)
                    # If no data for the map, displays a caption.
                    else: st.caption("No data available for current filters.")

                # Renders a histogram if the chart type matches. [VIZ1]
                elif chart_type == "hist":
                    values = chart_data.get("values")
                    # Checks if histogram data (values) is available.
                    if values is not None and not values.empty:
                        fig, ax = plt.subplots(figsize=(10,5)) # Creates a Matplotlib figure and axes.
                        # Plots the histogram using the provided values and properties.
                        ax.hist(values, bins=chart_props.get("bins", 20), color=chart_props.get("color", "skyblue"), edgecolor=chart_props.get("edgecolor", "black"))
                        ax.set_xlabel(chart_labels.get("x_label", "")) # Sets x-axis label.
                        ax.set_ylabel(chart_labels.get("y_label", "")) # Sets y-axis label.
                        ax.set_xlim(0, 11000) # Sets x-axis limits for yield.
                        plt.tight_layout()    # Adjusts plot to prevent labels from overlapping.
                        st.pyplot(fig)        # Displays the Matplotlib plot in Streamlit.
                        plt.close(fig)        # Closes the figure to free up memory.
                    # If no histogram data, displays a caption.
                    else:
                        st.caption("No hist data.")

                # Renders a line plot (timeline) if the chart type matches. [VIZ2]
                elif chart_type == "plot":
                    x_values = chart_data.get("x_values")
                    y_values = chart_data.get("y_values")
                    # Checks if x and y values are available and have the same length.
                    if x_values is not None and y_values is not None and len(x_values) == len(y_values):
                        fig, ax = plt.subplots(figsize=(10, 5)) # Creates Matplotlib figure and axes.
                        # Plots the line chart with specified markers, linestyle, and color.
                        ax.plot(x_values.astype(str), y_values, # Converts x_values (years) to string for categorical plotting.
                                marker=chart_props.get("marker"),
                                linestyle=chart_props.get("linestyle", "-"),
                                color=chart_props.get("color"))
                        ax.set_xlabel(chart_labels.get("x_label", "")) # Sets x-axis label.
                        ax.set_ylabel(chart_labels.get("y_label", "")) # Sets y-axis label.
                        plt.xticks(rotation=45, ha="right") # Rotates x-axis tick labels for better readability.
                        plt.tight_layout()
                        st.pyplot(fig)
                        plt.close(fig)
                    # If no timeline data, displays a caption.
                    else:
                        st.caption("No timeline data.")

                # Renders a horizontal bar chart if the chart type matches. [VIZ3]
                elif chart_type == "barh":
                    y_categories = chart_data.get("y_categories")
                    x_values = chart_data.get("x_values")
                    # Checks if categories and values are available and have the same length.
                    if y_categories and x_values and len(y_categories) == len(x_values):
                        # Dynamically adjusts figure height based on the number of categories.
                        fig_height = max(2, len(y_categories) * 0.4)
                        fig, ax = plt.subplots(figsize=(10, fig_height))
                        # Plots the horizontal bar chart.
                        ax.barh(y_categories, x_values,
                                color=chart_props.get("color"))
                        ax.set_xlabel(chart_labels.get("x_label", "")) # Sets x-axis label.
                        ax.invert_yaxis() # Inverts y-axis to show the highest bar at the top.
                        plt.tight_layout()
                        st.pyplot(fig)
                        plt.close(fig)
                    # If no bar chart data, displays a caption.
                    else:
                        st.caption("No bar chart data.")

                # Renders a scatter plot if the chart type matches.
                elif chart_type == "scatter":
                    x_values = chart_data.get("x_values")
                    y_values = chart_data.get("y_values")
                    # Checks if x and y values are available.
                    if x_values is not None and y_values is not None:
                        fig, ax = plt.subplots(figsize=(10, 6)) # Creates Matplotlib figure and axes.
                        # Plots the scatter chart with specified properties (alpha, edgecolors, linewidth).
                        ax.scatter(x_values, y_values, alpha=chart_props.get("alpha"),
                                   edgecolors=chart_props.get("edgecolors"),
                                   linewidth=chart_props.get("linewidth"))
                        ax.set_xlabel(chart_labels.get("x_label", "")) # Sets x-axis label.
                        ax.set_ylabel(chart_labels.get("y_label", "")) # Sets y-axis label.
                        ax.grid(True, linestyle='--', alpha=0.6) # Adds a grid for better readability.
                        plt.tight_layout()
                        st.pyplot(fig)
                        plt.close(fig)
                    # If no scatter plot data, displays a caption.
                    else:
                        st.caption("No scatter plot data.")

                # Renders a pie chart if the chart type matches.
                elif chart_type == "pie":
                    sizes = chart_data.get("sizes") # Values for each pie slice.
                    pie_labels = chart_data.get("labels") # Labels for each pie slice.

                    # Checks if sizes and labels are available and have the same length.
                    if sizes and pie_labels and len(sizes) == len(pie_labels):
                        fig, ax = plt.subplots(figsize=(8, 8)) # Creates Matplotlib figure and axes.
                                                    # [PY4] List comprehension to generate normalized values for pie chart colors
                        # Generates a list of colors using a Matplotlib colormap for the pie chart.
                        colors = plt.cm.viridis_r([i/len(sizes) for i in range(len(sizes))])
                        # Plots the pie chart with specified properties (autopct, startangle, colors).
                        ax.pie(sizes, labels=pie_labels,
                               autopct=chart_props.get("autopct", "%.1f%%"), # Format for percentage display.
                               startangle=chart_props.get("startangle", 90), # Start angle for the first slice.
                               colors=colors,
                               wedgeprops={'edgecolor': 'white'}) # Adds white edges to slices.

                        ax.axis('equal')  # Ensures the pie chart is circular.
                        plt.tight_layout()
                        st.pyplot(fig)
                        plt.close(fig)
                    # If no pie chart data, displays a caption.
                    else:
                        st.caption("No data available for pie chart with current filters.")
            # If data preparation failed for any reason, displays the error/failure message.
            else:
                st.caption(chart_info.get("message", "Could not generate visual."))


# Adds a horizontal rule.
st.markdown("---")
# Creates an expander section for looking up a detonation by its name.
with st.expander("🔎 Lookup a Detonation by Name"):
    # Provides a note about data availability and instructions.
    st.markdown(
        """
        **Note: 📝** Not every test in this dataset has an official name.  
        You can search for some of the most famous ones (e.g. Trinity,  
        Littleboy, Fatman)  by typing or choosing from the dropdown below 👇.
        """
    )
    # Prepares a list of valid detonation names for the selectbox.
    names_col = []
    for name in df['Data.Name']:
        if isinstance(name, str) and name.upper() != "NAN": # Includes strings that are not 'NAN'.
            names_col.append(name)
        elif pd.notna(name): # Includes other non-null, non-string names if any (e.g., numeric if they exist).
            names_col.append(name)

    # Adds a selectbox for choosing a detonation name.
    choice = st.selectbox("Type or choose the detonation you want to look into:", names_col)

    # Filters the DataFrame to get the row corresponding to the chosen detonation name.
    choice_df = df.loc[df["Data.Name"] == choice]
    # Extracts the first row (assuming names are unique or taking the first match).
    row = choice_df.iloc[0]

    # Extracts various details of the selected detonation from its row.
    choice_sup = row["WEAPON SOURCE COUNTRY"]
    choice_loc = row["WEAPON DEPLOYMENT LOCATION"]
    choice_source = row["Data.Source"]
    choice_coord_lat = row["latitude"]
    choice_coord_lon = row["longitude"]
    choice_mag_body = row["Data.Magnitude.Body"]
    choice_mag_surf = row["Data.Magnitude.Surface"]
    choice_depth = row["Location.Cordinates.Depth"]
    choice_lyield = row["Data.Yield.Lower"]
    choice_hyield = row["Data.Yield.Upper"]
    choice_purpose = purpose_map.get(row["Data.Purpose"], row["Data.Purpose"]) # Maps purpose code to full name.
    choice_type = row["Data.Type"]
    choice_date = row["Date"]

    # Displays the name and date of the selected detonation.
    st.subheader(f"{choice} **({choice_date:%Y-%m-%d})** 🗓️")
    # Displays supplier nation and location.
    st.write(f"**Supplier nation:** 🏭 {choice_sup}")
    st.write(f"**Location:** 📍 {choice_loc}")

    # Displays a simple map showing the location of the selected detonation.
    st.map(
        pd.DataFrame({
            "latitude": [choice_coord_lat],
            "longitude": [choice_coord_lon]
        }), height=250
    )

    # Uses columns to display metrics side-by-side.
    col1, col2, col3 = st.columns(3)
    col1.metric("Yield (kt): 🔥", f"{choice_lyield:.1f} – {choice_hyield:.1f}") # Yield range.
    col2.metric("Depth (km): ⬇", f"{choice_depth:.1f}")                     # Depth.
    col3.metric("Body / Surf mag: 📊", f"{choice_mag_body:.1f} / {choice_mag_surf:.1f}") # Seismic magnitudes.

    # Displays deployment type and purpose.
    st.write(f"**Deployment type:** 🚀 {choice_type}")
    st.write(f"**Purpose:** ⚙️ {choice_purpose}")


# Adds a horizontal rule.
st.markdown("---")

# Adds a header for the "Top 10 Detonations" section.
st.header("🏆 Top 10 Detonations by Highest Yield")
# Provides a description for this section.
st.write("""
    The table below lists the top 10 nuclear detonations with the highest average yield,
    based on your current filter settings.
""")

# Checks if the filtered DataFrame is not empty and contains the 'Yield.Avg' column.
if not filtered_df.empty and 'Yield.Avg' in filtered_df.columns:

    # [DA3] Find Top 10 largest values of 'Yield.Avg' column
    # Gets the top 10 detonations by 'Yield.Avg' from the filtered data.
    # Use .copy() to avoid potential SettingWithCopyWarning issues later.
    top_10_df = filtered_df.nlargest(10, 'Yield.Avg').copy()

    # Checks if any detonations were found for the top 10.
    if not top_10_df.empty:
        # Formats the 'Date' column for better readability.
        top_10_df['Formatted.Date'] = top_10_df['Date'].dt.strftime('%Y-%m-%d')

        # Maps purpose codes to full names using 'purpose_map'.
        if 'Data.Purpose' in top_10_df.columns:
            top_10_df['Purpose.Full'] = top_10_df['Data.Purpose'].map(purpose_map).fillna(top_10_df['Data.Purpose'])
        else:
            top_10_df['Purpose.Full'] = "N/A" # Placeholder if 'Data.Purpose' column is missing.

        # Ensures 'Data.Name' is present, provides a fallback if it's missing or all null.
        if 'Data.Name' not in top_10_df.columns or top_10_df['Data.Name'].isnull().all():
            top_10_df['Data.Name'] = "Unknown Detonation"

        # Defines columns to be used as the index for the pivot table.
        index_columns = ['Data.Name', 'Formatted.Date', 'WEAPON SOURCE COUNTRY', 'Purpose.Full']

        # [DA6] Analyze data with pivot tables (displaying top 10 detonations)
        # Attempts to create a pivot table for the top 10 yields.
        try:
            pivot_top_10_yields = pd.pivot_table(top_10_df,
                                                 index=index_columns,      # Rows of the pivot table.
                                                 values='Yield.Avg',       # Values to aggregate.
                                                 aggfunc='mean')          # Aggregation function (mean, though typically each row is unique here).

            # [DA3] Sort the resulting pivot table by 'Yield.Avg' in descending order for clear presentation
            pivot_top_10_yields_sorted = pivot_top_10_yields.sort_values(by='Yield.Avg', ascending=False)

            # Defines new, more readable names for the index levels of the pivot table.
            new_index_names = {'Data.Name': 'Bomb Name','Formatted.Date': 'Date of Detonation','WEAPON SOURCE COUNTRY': 'Sourced by','Purpose.Full': 'Purpose'}
            # Renames the index levels.
            pivot_top_10_yields_sorted.index.rename(new_index_names, inplace = True)

            # Displays the sorted pivot table as a Streamlit DataFrame.
            st.dataframe(pivot_top_10_yields_sorted)

        # Handles potential errors during pivot table creation.
        except Exception as e:
            st.error(f"An error occurred while creating the pivot table for top 10 yields: {e}")
            st.write("Displaying the top 10 yields as a simple list instead:") # Fallback display.
    # If no detonations in filtered data to make a top 10 list.
    else:
        st.caption("No detonations found in the filtered data to display top 10 yields.")
# If filtered data is empty or 'Yield.Avg' is missing.
else:
    st.caption("Filtered data is empty or 'Yield.Avg' column is missing, cannot determine top 10 yields.")


# Adds a blank line for spacing at the end of the page.
st.write("")
# Adds a caption attributing the app.
st.caption("App by Santiago Giraudo")

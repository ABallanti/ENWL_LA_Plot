import pandas as pd
import plotly.graph_objects as go
import json

# Load GeoJSON for local authorities
with open('INPUT/ENWL_LA.geojson', 'r') as response:
    la_geojson = json.load(response)

# Load GeoJSON for substations
with open('INPUT/ENWL_Sub_Location.geojson', 'r') as response:
    sub_geojson = json.load(response)

# Extract all local authorities from the first GeoJSON
local_authorities = [feature["properties"]["local_authority"] for feature in la_geojson["features"]]

# Create a DataFrame for all local authorities with a default value
data = {
    "local_authority": local_authorities,
    "value": [0] * len(local_authorities)  # Default value for areas without specific data
}
df = pd.DataFrame(data)

# Create the initial choropleth map
fig = go.Figure(go.Choroplethmapbox(
    geojson=la_geojson,
    featureidkey='properties.local_authority',
    locations=df['local_authority'],
    z=df['value'],
    colorscale="Blues",
    zmin=0, zmax=1,
    marker_opacity=0.6,
    hoverinfo="location"
))

# Set up mapbox layout
fig.update_layout(
    mapbox=dict(
        style="open-street-map",
        center={"lat": 53.483959, "lon": -2.244644},
        zoom=6,
    ),
    width=800,  # Set the desired width
    height=900  # Set the desired height
)

# Load PV data from Excel
df_less = pd.read_excel('MANUAL_DATASET/DGDB_less1MW_Cleansed.xlsx')
df_more = pd.read_excel('MANUAL_DATASET/DGDB_more1MW_Cleansed.xlsx')
df = pd.concat([df_less, df_more], ignore_index=True)

df = df.rename(columns={"Energy Source & Energy Conversion Technology 1 - Registered Capacity (MW)": "capacity"})

# Filter for PV and exclude capacities above 20
pv_df = df[df["Energy Source 1"] == "PV"].copy()
pv_df = pv_df[pv_df["Connection Status"] == "CONNECTED"].copy()
pv_df['POC Voltage (kV)'] = pd.to_numeric(pv_df['POC Voltage (kV)'], errors='coerce').fillna(-1)

# Filter for low voltage connected only (not need of size filter)
pv_df = pv_df[(pv_df['POC Voltage (kV)'] > 0) & (pv_df['POC Voltage (kV)'] <= 1)]
# pv_df = pv_df[(pv_df['capacity']<0.1)]

# Create Densitymapbox heatmap for PV
pv_trace = go.Densitymapbox(lat=pv_df['lat'], lon=pv_df['long'], z=pv_df['capacity'],
                             radius=30, colorscale="rainbow", opacity=0.7)

# Add the PV trace to the figure
fig.add_trace(pv_trace)

# ============ SUBSTATION PLOTTING ============

substation_lat = []
substation_lon = []
substation_names = []

# Add a scatter layer for filtered substations
for feature in sub_geojson['features']:
    if feature['properties'].get('infeed_voltage') == "33kV":  # Checking as a string
        substation_lon.append(feature['geometry']['coordinates'][0])
        substation_lat.append(feature['geometry']['coordinates'][1])
        substation_names.append(feature['properties'].get('spn', 'Unnamed Substation'))
#
# # Add a scatter layer for filtered substations
# fig.add_trace(go.Scattermapbox(
#     lat=substation_lat,
#     lon=substation_lon,
#     mode='markers',
#     marker=dict(size=10, color='red', opacity=0.8),
#     name='Substations',
#     text=substation_names,
#     hoverinfo='text'
# ))

# Set map layout properties
fig.update_layout(mapbox_style="open-street-map", mapbox_zoom=6, mapbox_center={"lat": 53.483959, "lon": -2.244644})
fig.update_layout(title="PV Energy Generation Heatmap with Substations")

# Display the final map
fig.show()

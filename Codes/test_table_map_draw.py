import numpy as np
import requests
import json
import pandas as pd
import plotly.express as px
# import plotly.io as pio
# pio.renderers.default = "browser"
# pio.renderers.default = "plotly_mimetype"


import plotly.express as px
import PySimpleGUI as sg
import pandas as pd

layout = [
    [sg.Button("Show")],
    [sg.Image(size=(600, 400), background_color='green', key='IMAGE')],
]

window = sg.Window('Title', layout)

while True:

    event, values = window.read()

    if event == sg.WIN_CLOSED:
        break

    elif event == 'Show':
        # df = px.data.iris()
        # fig = px.scatter(df, x="sepal_width", y="sepal_length", color="species")
        # file = 'C:/0_python_test/SETO_GUI_Prognostics/test.png'
        # fig.write_image(file, width=640, height=480)

        sites = pd.read_excel('test_site_location.xlsx')
        site = sites
        # site_lat = site['Latitude'][0:20].tolist()
        # site_lon = site['Longitude'][0:20].tolist()

        ### Visualize of inverters and corresponding stations
        fig_size = site['Latitude'].copy()
        fig_size[:] = 1
        fig_color = site['Latitude'].copy()
        fig_color[:] = 'green'
        # fig_color[0:2] = 'red'
        # fig_color[2:9] = 'yellow'
        # fig_color[9:20] = 'green'
        fig = px.scatter_mapbox(site,
                                lat="Latitude",
                                lon="Longitude",
                                color_discrete_sequence=[fig_color],
                                size=fig_size,
                                zoom=8)
        fig.update_layout(mapbox_style="open-street-map")
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        # fig.show()

        # img_bytes = fig.to_image(format="png", width=600, height=400)
        # window['IMAGE'].update(img_bytes)

        file = 'C:/0_python_test/SETO_GUI_Prognostics/test.png'
        fig.write_image(file, width=600, height=400)
        window['IMAGE'].update(file)


window.close()
























import matplotlib
# matplotlib.use("Agg")  # Set backend to Agg to prevent figure from appearing as a separate window
import matplotlib.pyplot as plt
import pandas as pd

table_RUL = [5, 9, 20, 30, 40, 50, 60, 70, 90, 240, 300, 400, 600, 800, 1000, 1100, 1200, 1300, 1400, 1500]
table_maint = [x - 3 for x in table_RUL]
table_invnum = [x for x in range(1,21)]
table_color = ['red']*20
for it in range(len(table_color)):
    if table_RUL[it] <=10:
        table_color[it] = 'red'
    elif table_RUL[it] <= 100:
        table_color [it] = 'yellow'
    else:
        table_color [it] = 'green'

df_table = pd.DataFrame(
    {'inv_num': table_invnum,
     'status': table_color,
     'RUL': table_RUL,
     'maint': table_maint
    })

#### test of table using ax ####
fig , ax = plt.subplots(figsize=[18,1])

cell_text = []
cell_text.append(df_table['inv_num'])
cell_text.append(df_table['status'])
cell_text.append(df_table['RUL'])
cell_text.append(df_table['maint'])

cellColours = cell_text.copy()
cellColours[0] = ['white']*20
cellColours[2] = ['white']*20
cellColours[3] = ['white']*20

cell_text[1] = ['']*20

table = ax.table(cellText=cell_text, rowLabels=df_table.columns, cellColours = cellColours, loc='center')
table.auto_set_font_size(False)
table.set_fontsize(10)
plt.axis('off')
fig.show()

'''
#### test using rowlabels ####
plt.figure(figsize=[12,1])
# plt.figure()

cell_text = []
cell_text.append(df_table['inv_num'])
cell_text.append(df_table['status'])
cell_text.append(df_table['RUL'])
cell_text.append(df_table['maint'])

cellColours = cell_text.copy()
cellColours[0] = ['white']*20
cellColours[2] = ['white']*20
cellColours[3] = ['white']*20

cell_text[1] = ['']*20

table = plt.table(cellText=cell_text, rowLabels=df_table.columns, cellColours = cellColours, loc='center')
table.auto_set_font_size(False)
table.set_fontsize(10)
plt.axis('off')






#### test using col-labels ####
plt.figure()


cell_color = cell_text
for row in range(len(cell_color)):
    if df_table['status'][row] == 'red':
        cell_color[row] = ['white', 'red', 'white', 'white']
    elif df_table['status'][row] == 'yellow':
        cell_color[row] = ['white', 'yellow', 'white', 'white']
    elif df_table['status'][row] == 'green':
        cell_color[row] = ['white', 'green', 'white', 'white']

plt.table(cellText=cell_text, colLabels=df_table.columns, cellColours= cell_color, loc='center')
plt.axis('off')


#### test using rowlabels ####
plt.figure(figsize=[6,1])
# plt.figure()

cell_text = []
cell_text.append(['ACTIONS: Inverter #20 PM at Day 98'])
cell_text.append(['SCHEDULE: Inverter #1 PM at Day 102'])
cell_text.append(['SCHEDULE: Inverter #2 PM at Day 106'])

cellColours = [['green'], ['white'], ['white']]

table = plt.table(cellText=cell_text, cellColours = cellColours, cellLoc = 'left', loc='center')
table.auto_set_font_size(False)
table.set_fontsize(10)
plt.axis('off')
'''








import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

site = pd.read_excel('test_site_location.xlsx')
site = site[0:20]

# Create a figure and axes
fig, ax = plt.subplots(subplot_kw={'projection': ccrs.PlateCarree()})

# Add features like coastlines, borders, etc.
ax.add_feature(cfeature.LAND)
ax.add_feature(cfeature.COASTLINE)
ax.add_feature(cfeature.BORDERS, linestyle=':')

# Sample latitude and longitude data
lats = [40.7128, 51.5074, 34.0522]
lons = [-74.0060, -0.1278, -118.2437]
lats = site['Latitude']
lons = site['Longitude']

# Plot the points
ax.scatter(lons, lats, color='red', transform=ccrs.PlateCarree())

# Show the plot
plt.show()
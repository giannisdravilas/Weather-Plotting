import os
import cartopy.crs as ccrs
import cartopy.feature as cf
import numpy as np

import matplotlib as mpl
from netCDF4 import Dataset as netcdf_dataset
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure

from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.image as mpimg

import PIL
PIL.Image.MAX_IMAGE_PIXELS = 233280000

# Get information from the dataset
fname = os.getcwd()+"/gfs_dataset.nc"
dataset = netcdf_dataset(fname)
pmsl = dataset.variables['prmsl'][:, :, :]
u10 = dataset.variables['u10'][:, :, :]
v10 = dataset.variables['v10'][:, :, :]

lats = dataset.variables['latitude'][:]
lons = dataset.variables['longitude'][:]
time = dataset.variables['time'][:]

# Reduce to hPa
pmsl /= 100

# Find area with minimum pressure for every time step
min_lat = [0 for i in range(len(time))]
min_lon = [0 for i in range(len(time))]

# netCDF file has a time step of 3 hours, but our plot of cyclone track
for time_step in range(0, len(time)):
    min_pmsl = 9999
    for i in range(0,57):
        for j in range(0,89):
            if pmsl[time_step][i][j] < min_pmsl:
                min_pmsl = pmsl[time_step][i][j]
                min_lat[time_step] = i
                min_lon[time_step] = j

# Convert to actual coordinates, according to the shape of the netCDF file
min_lat_converted = []
min_lon_converted = []

for i in min_lat:
    min_lat_converted.append(min(lats)+0.25*int(i))

for i in min_lon:
    min_lon_converted.append(min(lons)-360+0.25*int(i))

# A list containing wind speed data for every time step
ws_list = []

for time in range(len(time)):
    ws = np.sqrt(u10[time]**2 + v10[time]**2) # Wind speed calculation, according to u, v components
    ws *= 3.6 # Convertion to km/h
    ws_list.append(ws)

# A list containing maximum wind speed among all time steps, for every point of the grid
ws_final = [[0 for i in range(len(lons))] for j in range(len(lats))]

# For every poing of the grid
for i in range(0,len(lats)):
    for j in range(0,len(lons)):
        # Examine all time steps
        for k in range(len(ws_list)):
            ws = ws_list[k]
            if ws[i][j] > ws_final[i][j]:
                ws_final[i][j] = ws[i][j]

# Plot data
fig = figure(figsize=(30, 15))

os.environ["CARTOPY_USER_BACKGROUNDS"] = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.background_img(name='ETOPO', resolution='low')

ax.coastlines(linewidth=2)
ax.add_feature(cf.BORDERS, linewidth=2)

# Set map extent to the desired coordinates
ax.set_extent([-103, -72, 17, 43], crs=ccrs.PlateCarree())

# Cyclone image for every position of the cyclone's track (per 6 hours)
cyclon = mpimg.imread('cyclon_trans.png')
imagebox = OffsetImage(cyclon, zoom=0.04)

# Range of data is the range of min_lon or min_lat
# We annotate every 6 hours, but the data have a 3 hour time step, so we skip
# one annotation every time
for i in range(0, len(min_lon_converted), 2):
    # print(i, min_lon_converted[i], min_lat_converted[i])
    # Plot cyclone image on the coordinates of minimum mslp
    ab = AnnotationBbox(imagebox, (min_lon_converted[i], min_lat_converted[i]), frameon=False)
    ax.add_artist(ab)

# Levels of wind speed (km/h)
# 62 km/h for 8 beauforts, 170 km/h, higher of the dataset
levels = np.linspace(62, 170, 54)

# Contourf plot
plt.contourf(lons, lats, ws_final, levels=levels, transform=ccrs.PlateCarree(), cmap='turbo', alpha=0.9)

# Plot logo
logo = mpimg.imread('../logo.png')
imagebox = OffsetImage(logo, zoom=0.62)
ab = AnnotationBbox(imagebox, (-75.2, 18), frameon=False)
ax.add_artist(ab)

plt.title("GFS Hurricane IDA track and maximum wind speed\nvalid between Sat 28-08-2021 12:00 UTC and Tue 31-08-2021 12:00 UTC", fontsize=23)
plt.text(s="Init: Sat 28-08-2021 12z", fontsize=14, color='black', y=1.04, x=0.95, transform=ax.transAxes)
plt.text(s="Plot by Giannis Dravilas", fontsize=14, y=1.02, x=0.95, transform=ax.transAxes)

cbar = plt.colorbar(mpl.cm.ScalarMappable(norm=mpl.colors.Normalize(vmin=62, vmax=170), cmap='turbo'), pad=0.01)
cbar.ax.tick_params(labelsize=20) 
cbar.set_label(label='Wind speed (km/h)', fontsize=20)
cbar.ax.locator_params(nbins=13)

plot = plt.savefig('gfs_hurricane_ida_track.png', bbox_inches='tight')

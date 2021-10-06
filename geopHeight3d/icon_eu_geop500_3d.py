import requests
import os

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
from matplotlib.collections import LineCollection

import cartopy.feature
from cartopy.mpl.patch import geos_to_path
import cartopy.crs as ccrs

from netCDF4 import Dataset as netcdf_dataset

import itertools

import datetime
from datetime import date
from datetime import timedelta

from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm

import matplotlib.image as mpimg
from PIL import Image

run = input("Enter run (00 or 06 or 12 or 18): ")

hours_ahead = input("Enter hours ahead (0 to 77 or 78 to 120 with step 3, type = int): ")
hours_ahead = hours_ahead.zfill(3)

resolution = input("Enter preferred resolution multiple to be used (1 to 100, type = int): ")
resolution = int(resolution)

days_ago = input("Enter 1 for yesterday's run, 0 for today's run (according to your system's local time) : ")
days_ago = int(days_ago)

# Get today's date and create the appropriate format
today = date.today()
today = date.today() - timedelta(days=days_ago)
today_edited = today.strftime("%Y%m%d")
today_run = today_edited + run


# Download grib files from DWD and convert them to netCDF
url = "https://opendata.dwd.de/weather/nwp/icon-eu/grib/"+run+"/fi/icon-eu_europe_regular-lat-lon_pressure-level_"+today_run+"_"+hours_ahead+"_500_FI.grib2.bz2"
r = requests.get(url, allow_redirects=True)
open("geop.bz2", "wb").write(r.content)
os.system("bzip2 -d geop.bz2")
os.system("mv geop geop.grib2")
os.system("grib_to_netcdf -o geop_out.nc geop.grib2")

# Get information from the dataset
fname = os.getcwd()+"/geop_out.nc"
dataset = netcdf_dataset(fname)
gh = dataset.variables["z"][0, ::resolution, ::resolution]

lats = dataset.variables["latitude"][::resolution]
lons = dataset.variables["longitude"][::resolution]
time = dataset.variables["time"][:]

# Create a 3d plot with x, y limits the icon-eu maximum/minimum coordinates
# z limit results from the new variable possible values, see line 102
figure(figsize=(30, 15))

ax = plt.axes(projection="3d", xlim=[-23.5, 45], ylim=[29.5, 70.5], zlim=[0, 350])

#################################################################################
#################################################################################
# Create basemap of the plot, using some code from https://stackoverflow.com/questions/23785408/3d-cartopy-similar-to-matplotlib-basemap
target_projection = ccrs.PlateCarree()

feature = cartopy.feature.NaturalEarthFeature("physical", "coastline", "50m")
geoms = feature.geometries()

geoms = [target_projection.project_geometry(geom, feature.crs)
         for geom in geoms]

paths = list(itertools.chain.from_iterable(geos_to_path(geom) for geom in geoms))

# At this point, we start working around mpl3d's slightly broken interfaces.
# So we produce a LineCollection rather than a PathCollection.
segments = []
for path in paths:
    vertices = [vertex for vertex, _ in path.iter_segments()]
    vertices = np.asarray(vertices)
    segments.append(vertices)

lc = LineCollection(segments, color="black", zorder=0)

ax.add_collection3d(lc)
#################################################################################
#################################################################################

# Convert Geopotential to Geopotential Height
gh /= 9.80665

# Save Geopotential Height in gpdms
gh = gh/10

# Create a second variable with edited Geopotential Height for better 3d representation
gh_3d = gh/100
gh_3d = np.exp(gh_3d)

# Create meshgrid from lats, lons
x = lons
y = lats

x2 = np.append(0, x.flatten())
y2 = np.append(0, y.flatten())

x2, y2 = np.meshgrid(lons, lats)

# Create np array from the gh_3d array, flattened to one dimension and delete its first item (for better illustration)
z2 = np.append(0, gh_3d.flatten())
z2 = np.delete(z2, 0)

max_z2 = max(z2)

# Plot trisurf data (3d plot of Geopotential Height reduced to the 3d variable)
surf = ax.plot_trisurf(x2.flatten(), y2.flatten(), z2, cmap=cm.nipy_spectral, linewidth=0.1, vmin=min(z2), vmax=max_z2, alpha=0.6, antialiased=False)

# Find min and max Geopotential Height
min_gh = 1000
for i in range(len(gh)):
    for j in range(len(gh[i])):
        if gh[i][j] < min_gh:
            min_gh = gh[i][j]

max_gh = 0
for i in range(len(gh)):
    for j in range(len(gh[i])):
        if gh[i][j] > max_gh:
            max_gh = gh[i][j]

# Create levels for contour plotting on Basemap
levels_contourf = np.linspace(min_gh, max_gh, 1000)
levels_contour = np.linspace(min_gh, max_gh, 25)

# Create contour plots on level 0 of z axis
ax.contourf(x2, y2, gh, levels_contourf, zdir="z", offset=0, cmap="nipy_spectral", alpha=0.4, zorder=10, antialiased=False)
ax.contour(x2, y2, gh, levels_contour, zdir="z", offset=0, colors="black", linewidths=2, zorder=100)

# Colorbar has values from the actual Geopotential Height
cbar = plt.colorbar(mpl.cm.ScalarMappable(norm=mpl.colors.Normalize(vmin=min_gh, vmax=max_gh), cmap="nipy_spectral"), shrink=0.5, aspect=5, pad=0.0001)
cbar.ax.tick_params(labelsize=20) 
cbar.ax.locator_params(nbins=10)
cbar.set_label(label="Geopotential Height 500 hPa (gpdm)", fontsize=20)

# Set view angle
ax.view_init(25, 270)

# Plot where 3 european capitals are, for better understanding of the positions in the 3d plot
ax.plot([23.72,23.72],[37.98,37.98],[0,max_z2+40],"-",color="black", alpha=1, linewidth=2)
ax.text(s="Athens", x=23.72, y=37.98, z=max_z2+40, zorder=1000)

ax.plot([10.75,10.75],[59.91,59.91],[0,max_z2+20],"-",color="black", alpha=1, linewidth=2)
ax.text(s="Oslo", x=10.75, y=59.91, z=max_z2+20, zorder=1000)

ax.plot([-0.12,-0.12],[51.50,51.50],[0,max_z2+20],"-",color="black", alpha=1, linewidth=2)
ax.text(s="London", x=-0.12, y=51.50, z=max_z2+20, zorder=1000)

# Get time information from dataset
date = datetime.datetime(1900,1,1)+timedelta(hours=int(time[0]))
date_formatted = date.strftime("%d-%m-%Y %H:%M")
day = date.strftime("%A")

# Titles, subtitles and further labels
ax.set(xlabel="Longitude", ylabel="Latitude", zlabel="Height (exp(gpdm/1000))")
plt.title("ICON-EU Geopotential Height 500 hPa\nValid for "+day+" "+date_formatted+" UTC", y=0.93, fontsize=20)

# Change time to initialization date by subtracting ahead time
date = datetime.datetime(1900,1,1)+timedelta(hours=int(time[0]))-timedelta(hours=int(hours_ahead))
date_formatted = date.strftime("%d-%m-%Y %H")
day = date.strftime("%a")

plt.suptitle(t="Init: "+day+" "+date_formatted+"z\nPlot by Giannis Dravilas", x=0.8, y=0.73, fontsize=15)

# Print logo image
logo = Image.open("../logo.png")
logo = logo.resize((293,99))
plt.figimage(logo, 0, 0)

# Save figure
date_formatted = date.strftime("%Y%m%d%H")
plot = plt.savefig("icon_eu_geop500_3d_"+date_formatted+"_"+hours_ahead.zfill(3)+".png", bbox_inches="tight")

os.remove("geop_out.nc")
os.remove("geop.grib2")
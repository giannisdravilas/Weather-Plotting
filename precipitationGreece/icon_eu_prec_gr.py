import requests
import os
from cartopy import config
import cartopy.crs as ccrs
import cartopy.feature as cf
import numpy as np

import matplotlib as mpl
from netCDF4 import Dataset as netcdf_dataset
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure

from cartopy.io import shapereader
import geopandas
import cartopy.io.img_tiles as cimgt
from shapely.geometry import Polygon

import matplotlib.colors as mcolors
from matplotlib import ticker

import datetime
from datetime import date
from datetime import timedelta

import matplotlib.image as mpimg
from PIL import Image

run = input("Enter run (00 or 06 or 12 or 18): ")

hours_ahead = input("Enter hours ahead (0 to 77 or 78 to 120 with step 3, type = int): ")
hours_ahead = hours_ahead.zfill(3)

hours_of_accumulation = input("Enter hours of accumulation (1 to 120, depending on hours ahead, type = int): ")
hours_of_accumulation = str(hours_of_accumulation).zfill(3)
hours_init = str(int(hours_ahead)-int(hours_of_accumulation)).zfill(3)

days_ago = input("Enter 1 for yesterday's run, 0 for today's run (according to your system's local time) : ")
days_ago = int(days_ago)

# Get today's date and create the appropriate format
today = date.today()
today = date.today() - timedelta(days=days_ago)
today_edited = today.strftime("%Y%m%d")
today_run = today_edited + run

# Coordinates of the area we are interested in
lon_min = int((0.0625*int(19/0.0625)+23.5)/0.0625)
lon_max = int((0.0625*int(30/0.0625)+23.5)/0.0625)
lat_min = int((0.0625*int(34/0.0625)-29.5)/0.0625)
lat_max = int((0.0625*int(45/0.0625)-29.5)/0.0625)

# Download grib files from DWD and convert them to netCDF (end_of_accumulation_time)
url = "https://opendata.dwd.de/weather/nwp/icon-eu/grib/"+run+"/tot_prec/icon-eu_europe_regular-lat-lon_single-level_"+today_run+"_"+hours_ahead+"_TOT_PREC.grib2.bz2"
r = requests.get(url, allow_redirects=True)
open("rain.bz2", "wb").write(r.content)
os.system("bzip2 -d rain.bz2")
os.system("mv rain rain.grib2")
os.system("grib_to_netcdf -o rain_out.nc rain.grib2")

# Get information from the dataset
fname = os.getcwd()+"/rain_out.nc"
dataset = netcdf_dataset(fname)
rain = dataset.variables["tp"][0, lat_min:lat_max+2, lon_min:lon_max+2]

lats = dataset.variables["latitude"][lat_min:lat_max+2]
lons = dataset.variables["longitude"][lon_min:lon_max+2]
time = dataset.variables["time"][:]

# Download grib files from DWD and convert them to netCDF (init_of_accumulation_time)
url = "https://opendata.dwd.de/weather/nwp/icon-eu/grib/"+run+"/tot_prec/icon-eu_europe_regular-lat-lon_single-level_"+today_run+"_"+hours_init+"_TOT_PREC.grib2.bz2"
r = requests.get(url, allow_redirects=True)
open("rain.bz2", "wb").write(r.content)
os.system("bzip2 -d rain.bz2")
os.system("mv rain rain.grib2")
os.system("grib_to_netcdf -o rain_out.nc rain.grib2")

# Get information from the dataset
fname = os.getcwd()+"/rain_out.nc"
dataset = netcdf_dataset(fname)
rain_init = dataset.variables["tp"][0, lat_min:lat_max+2, lon_min:lon_max+2]

# Create the final dataset, containing precipitation amounts only for the desired time
rain -= rain_init

# Create a plot
figure(figsize=(30, 15))
ax = plt.axes(projection=ccrs.PlateCarree())

ax.coastlines(linewidth=2)
ax.add_feature(cf.BORDERS, linewidth=2)

# NWS precipitation colormap (https://unidata.github.io/python-gallery/examples/Precipitation_Map.html)
clevs = [0, 0.1, 1, 2.5, 5, 7.5, 10, 15, 20, 30, 40,
         50, 70, 100, 150, 200, 250, 300]
cmap_data = [(1, 0, 0, 0),
             (0.3137255012989044, 0.8156862854957581, 0.8156862854957581),
             (0.0, 1.0, 1.0),
             (0.0, 0.8784313797950745, 0.501960813999176),
             (0.0, 0.7529411911964417, 0.0),
             (0.501960813999176, 0.8784313797950745, 0.0),
             (1.0, 1.0, 0.0),
             (1.0, 0.6274510025978088, 0.0),
             (1.0, 0.0, 0.0),
             (1.0, 0.125490203499794, 0.501960813999176),
             (0.9411764740943909, 0.250980406999588, 1.0),
             (0.501960813999176, 0.125490203499794, 1.0),
             (0.250980406999588, 0.250980406999588, 1.0),
             (0.125490203499794, 0.125490203499794, 0.501960813999176),
             (0.125490203499794, 0.125490203499794, 0.125490203499794),
             (0.501960813999176, 0.501960813999176, 0.501960813999176),
             (0.8784313797950745, 0.8784313797950745, 0.8784313797950745),
             ]
cmap = mcolors.ListedColormap(cmap_data, "precipitation")
norm = mcolors.BoundaryNorm(clevs, cmap.N)

# Create levels for contour plotting
levels = np.linspace(0, 300, 3001)

# Create contourf plot
plt.contourf(lons, lats, rain, levels=levels, transform=ccrs.PlateCarree(), cmap=cmap, norm=norm)

# Create colorbar
cbar = plt.colorbar(mpl.cm.ScalarMappable(cmap=cmap, norm=norm),pad=0.01)
cbar.ax.tick_params(labelsize=20) 
cbar.set_label(label="Precipitation (mm/"+str(int(hours_of_accumulation)).zfill(1)+"hr)", fontsize=30)
cbar.set_ticks(clevs)

# Limit plot's extent to specific coordinates
ax.set_extent([19.35, 29.65, 34.75, 41.90], crs=ccrs.PlateCarree())

# Get time information from dataset
date = datetime.datetime(1900,1,1)+timedelta(hours=int(time[0]))
date_formatted = date.strftime("%d-%m-%Y %H:%M")
day = date.strftime("%A")

# Titles, subtitles and further labels
plt.title("ICON-EU "+str(int(hours_of_accumulation)).zfill(1)+"hr Accumulated Precipitation\nValid for "+day+" "+date_formatted+" UTC", fontsize=30)

# Change time to initialization date by subtracting ahead time
date = datetime.datetime(1900,1,1)+timedelta(hours=int(time[0]))-timedelta(hours=int(hours_ahead))
date_formatted = date.strftime("%d-%m-%Y %H")
day = date.strftime("%a")

plt.text(s="Init: "+day+" "+date_formatted+"z", fontsize=15, color="black", y=1.04, x=1, transform=ax.transAxes)
plt.text(s="Plot by Giannis Dravilas", fontsize=15, y=1.02, x=1, transform=ax.transAxes)

# Print logo image
logo = Image.open("../logo.png")
logo = logo.resize((293,99))
plt.figimage(logo, 1400, 20)

# Save figure
date_formatted = date.strftime("%Y%m%d%H")
plot = plt.savefig("icon_eu_precipitation_gr_"+date_formatted+"_"+hours_ahead.zfill(3)+".png", bbox_inches="tight")

os.remove("rain_out.nc")
os.remove("rain.grib2")
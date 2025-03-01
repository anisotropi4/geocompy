# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.15.2
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# # Making maps with Python {#sec-map-making}
#
# ## Prerequisites {.unnumbered}

#| echo: false
#| label: getdata
from pathlib import Path
data_path = Path("data")
if data_path.is_dir():
  pass
  # print("path exists") # directory exists
else:
  print("Attempting to get and unzip the data")
  import requests, zipfile, io
  r = requests.get("https://github.com/geocompx/geocompy/releases/download/0.1/data.zip")
  z = zipfile.ZipFile(io.BytesIO(r.content))
  z.extractall(".")

# This chapter requires importing the following packages:

import matplotlib.pyplot as plt
import geopandas as gpd
import rasterio
import rasterio.plot
import contextily as cx
import folium

#| echo: false
import pandas as pd
import matplotlib.pyplot as plt
pd.options.display.max_rows = 6
pd.options.display.max_columns = 6
pd.options.display.max_colwidth = 35
plt.rcParams['figure.figsize'] = (5, 5)

# It also relies on the following data files:

nz = gpd.read_file('data/nz.gpkg')
nz_height = gpd.read_file('data/nz_height.gpkg')
nz_elev = rasterio.open('data/nz_elev.tif')
tanzania = gpd.read_file('data/world.gpkg', where='name_long="Tanzania"')
tanzania_buf = tanzania.to_crs(32736).buffer(50000).to_crs(4326)
tanzania_neigh = gpd.read_file('data/world.gpkg', mask=tanzania_buf)

# ## Introduction
#
# <!-- - Geopandas explore has been used in previous chapters. -->
#
# <!-- - When to focus on visualisation? At the end of geographic data processing workflows. -->
#
# <!-- Input datasets: https://github.com/geocompx/spDatapy -->
#
# A satisfying and important aspect of geographic research is communicating the results.
# Map making---the art of cartography---is an ancient skill that involves communication, intuition, and an element of creativity.
# In addition to being fun and creative, cartography also has important practical applications.
# A carefully crafted map can be the best way of communicating the results of your work, but poorly designed maps can leave a bad impression.
# Common design issues include poor placement, size and readability of text and careless selection of colors, as outlined in the style guide of the Journal of Maps.
# Furthermore, poor map making can hinder the communication of results [@brewer_designing_2015]:
#
# > Amateur-looking maps can undermine your audience's ability to understand important information and weaken the presentation of a professional data investigation.
#
# Maps have been used for several thousand years for a wide variety of purposes.
# Historic examples include maps of buildings and land ownership in the Old Babylonian dynasty more than 3000 years ago and Ptolemy's world map in his masterpiece Geography nearly 2000 years ago [@talbert_ancient_2014].
#
# Map making has historically been an activity undertaken only by, or on behalf of, the elite.
# This has changed with the emergence of open source mapping software such as mapping packages in Python, R, and other languages, and the "print composer" in QGIS, which enable anyone to make high-quality maps, enabling "citizen science".
# Maps are also often the best way to present the findings of geocomputational research in a way that is accessible.
# Map making is therefore a critical part of geocomputation and its emphasis not only on describing, but also changing the world.
#
# Basic static display of vector layers in Python is done with the `.plot` method or the `rasterio.plot.show` function, for vector layers and rasters, as we saw in Sections @sec-vector-layers and @sec-using-rasterio, respectively.
# Other, more advanced uses of these methods, were also encountered in subsequent chapters, when demonstrating the various outputs we got.
# In this chapter, we provide a comprehensive summary of the most useful workflows of these two methods for creating static maps (@sec-static-maps).
# Static maps can be easily shared and viewed (whether digitally or in print), however they can only convey as much information as a static image can.
# Interactive maps provide much more flexibilty in terms of user experience and amount of information, however they often require more work to design and effectively share.
# Thus, in @sec-interactive-maps, we move on to elaborate on the `.explore` method for creating interactive maps, which was also briefly introduced earlier in @sec-vector-layers.
#
# ## Static maps {#sec-static-maps}
# <!-- jn: this intro can be improved/expanded -->
#
# Static maps are the most common type of visual output from geocomputation.
# When stored in a file, standard formats include `.png` and `.pdf` for graphical raster and vector outputs, respectively.
# <!-- jn: maybe it would be good to add a block here about the similarities and differences between spatial raster/vectors and graphical raster/vectors? -->
#
# <!-- Decision of whether to use static or interactive. -->
#
# <!-- Flow diagram? -->
#
# Let's move on to the basics of static mapping with Python.
#
# ### Minimal examples of static maps 
#
# A vector layer (`GeoDataFrame`) or a geometry column (`GeoSeries`) can be displayed using their `.plot` method (@sec-vector-layers).
# A minimal example of a vector layer map is obtained using `.plot` with nothing but the defaults (@fig-vector-minimal).

#| label: fig-vector-minimal
#| fig-cap: Minimal example of a static vector layer plot with `.plot`
nz.plot();

# A `rasterio` raster file connection, or a numpy `ndarray`, can be displayed using `rasterio.plot.show` (@sec-using-rasterio).
# @fig-raster-minimal shows a minimal example of a static raster map.

#| label: fig-raster-minimal
#| fig-cap: Minimal example of a static raster plot with `rasterio.plot.show`
rasterio.plot.show(nz_elev);

# ### Styling {#sec-static-styling}
#
# The most useful visual properties of the geometries, that can be specified in `.plot`, include `color`, `edgecolor`, and `markersize` (for points) (@fig-basic-plot).

#| label: fig-basic-plot
#| fig-cap: Setting `color` and `edgecolor` in static maps of a vector layer
#| fig-subcap: 
#| - Light grey fill
#| - No fill, blue edge
#| - Light grey fill, blue edge
#| layout-ncol: 3
nz.plot(color='lightgrey');
nz.plot(color='none', edgecolor='blue');
nz.plot(color='lightgrey', edgecolor='blue');

# The next example uses `markersize` to get larger points (@fig-basic-plot-markersize).
# It also demonstrates how to control the overall [figure size](https://matplotlib.org/stable/gallery/subplots_axes_and_figures/figure_size_units.html), such as $4 \times 4$ $in$ in this case, using [`plt.subplots`](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.subplots.html) to initialize the plot and its `figsize` parameter to specify dimensions.
# <!-- jn: I think that a longer explanation is needed... What's fig? What else can be achieved with plt.subplots? What's the unit of 4x4? Etc... -->

#| label: fig-basic-plot-markersize
#| fig-cap: Setting `markersize` in a static map of a vector layer
fig, ax = plt.subplots(figsize=(4,4))
nz_height.plot(markersize=100, ax=ax);

# ### Symbology {#sec-plot-symbology}
#
# We can set symbology in a `.plot` using the following parameters:
#
# -   `column`---a column name
# -   `legend`---whether to show a legend
# -   `cmap`---color map
# <!-- jn: what's color map? what does it mean? You use term color scale later... -->
#
# For example, @fig-plot-symbology shows the `nz` polygons colored according to the `'Median_income'` attribute (column), with a legend.

#| label: fig-plot-symbology
#| fig-cap: Symbology in a static map created with `.plot`
nz.plot(column='Median_income', legend=True);

# The default color scale which you see in @fig-plot-symbology is `cmap='viridis'`.
# The `cmap` ("color map") argument can be used to specify one of countless color scales.
# A first safe choice is often the [ColorBrewer](https://colorbrewer2.org/#type=sequential&scheme=BuGn&n=3) collection of color scales, specifically designed for mapping.
# Any color scale can be reversed, using the `_r` suffix.
# Finally, other color scales are available: see the **matplotlib** [colormaps article](https://matplotlib.org/stable/tutorials/colors/colormaps.html) for details.
# The following code sections demonstrates three color scale specifications other than the default (@fig-plot-symbology-colors).

#| label: fig-plot-symbology-colors
#| fig-cap: Symbology in a static map of a vector layer, created with `.plot`
#| fig-subcap: 
#| - The `'Reds'` color scale from ColorBrewer
#| - Reversed `'Reds'` color scale
#| - The `'spring'` color scale from **matplotlib**
#| layout-ncol: 3
nz.plot(column='Median_income', legend=True, cmap='Reds');
nz.plot(column='Median_income', legend=True, cmap='Reds_r');
nz.plot(column='Median_income', legend=True, cmap='spring');

# <!-- jn: spring does not look like a color blind friendly color scale... I would suggest to use a different one. (I would suggest avoiding giving bad examples, even if they are just examples...) -->
#
# Categorical symbology is also supported, such as when `column` points to an `str` attribute.
# For categorical variables, it makes sense to use a qualitative color scale, such as `'Set1'` from ColorBrewer.
# For example, the following expression sets symbology according to the `'Island'` column (@fig-plot-symbology-categorical).

#| label: fig-plot-symbology-categorical
#| fig-cap: Symbology for a categorical variable
nz.plot(column='Island', legend=True, cmap='Set1');

# In case the legend interferes with the contents (such as in @fig-plot-symbology-categorical), we can modify the legend position using the `legend_kwds` argument (@fig-plot-legend-pos).

#| label: fig-plot-legend-pos
#| fig-cap: Setting legend position in `.plot`
nz.plot(column='Island', legend=True, cmap='Set1', legend_kwds={'loc': 4});

# The `rasterio.plot.show` function is also based on **matplotlib**, and thus supports the same kinds of `cmap` arguments (@fig-plot-symbology-colors-r).

#| label: fig-plot-symbology-colors-r
#| fig-cap: Symbology in a static map of a raster, with `rasterio.plot.show`
#| layout-ncol: 3
#| fig-subcap: 
#| - The `'BrBG'` color scale from ColorBrewer
#| - Reversed `'BrBG_r'` color scale
#| - The `'nipy_spectral'` color scale from **matplotlib**
rasterio.plot.show(nz_elev, cmap='BrBG');
rasterio.plot.show(nz_elev, cmap='BrBG_r');
rasterio.plot.show(nz_elev, cmap='nipy_spectral');

# Unfortunately, there is no built-in option to display a legend in `rasterio.plot.show`.
# The following [workaround](https://stackoverflow.com/questions/61327088/rio-plot-show-with-colorbar), reverting to **matplotlib** methods, can be used to acheive it instead (@fig-plot-symbology-colors-r-scale).
# <!-- jn: a few sentence explanation of the code below is needed... -->

#| label: fig-plot-symbology-colors-r-scale
#| fig-cap: Adding a legend in `rasterio.plot.show`
fig, ax = plt.subplots()
i = ax.imshow(nz_elev.read(1), cmap='BrBG')
rasterio.plot.show(nz_elev, cmap='BrBG', ax=ax);
fig.colorbar(i, ax=ax);

# ### Labels {#sec-plot-static-labels}
#
# <!-- start here -->
#
# Labels are often useful to annotate maps and identify the location of specific features. 
# GIS software, as opposed to **matplotlib**, has specialized algorithms for label placement, e.g., to avoid overlaps between adjacent labels.
# Furthermore, editing in graphical editing software is sometimes used for fine tuning of label placement.
# Nevertheless, simple labels added within the Python environment can be a good starting point, both for interactive exploration and sharing analysis results.
#
# To demonstrate it, suppose that we have a layer `nz1` of regions comprising the New Zealand southern Island.

nz1 = nz[nz['Island'] == 'South']

# To add a label in **matplotlib**, we use the [`.annotate`](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.annotate.html) method where the important arguments are the label string and the placement (a `tuple` of the form `(x,y)`). 
# When labeling vector layers, we typically want to add numerous labels, based on (one or more) attribute of each feature. 
# To do that, we can run a `for` loop, or use the `.apply` method, to pass the label text and the coordinates of each feature to `.annotate`.
# In the following example, we use the `.apply` method the pass the region name (`'Name'` attribute) and the geometry centroid coordinates, for each region, to `.annotate`.
# We are also using `ha='center'`, short for `horizontalalignment` (@fig-labels-polygon).
# <!-- jn: what are other options for ha? maybe it would be worth mentioning them somewhere in this subsection? -->

#| label: fig-labels-polygon
#| fig-cap: Labels at polygon centroids
fig, ax = plt.subplots()
nz1.plot(ax=ax, color='lightgrey', edgecolor='grey')
nz1.apply(
    lambda x: ax.annotate(
        text=x['Name'], 
        xy=x.geometry.centroid.coords[0], 
        ha='center'
    ), 
    axis=1
);

# As another example, let's create a map of all regions of New Zealand, with labels for the island names. 
# First, we will calculate the island centroids, which will be the label placement positions.

ctr = nz[['Island', 'geometry']].dissolve(by='Island').reset_index()
ctr['geometry'] = ctr.centroid
ctr

# Then, we again use `.apply`, combined with `.annotate`, to add the text labels. 
# The main difference compared to the previous example (@fig-labels-polygon) is that we are directly passing the geometry coordinates (`.geometry.coords[0]`), since the geometries are points rather than polygons.
# We are also using the `weight='bold'` argument to use bold font (@fig-labels-points1).
# <!-- jn: what are other weight options? where to find them? -->

#| label: fig-labels-points1
#| fig-cap: Labels at points
fig, ax = plt.subplots()
nz.plot(ax=ax, color='none', edgecolor='lightgrey')
ctr.apply(
    lambda x: ax.annotate(
        text=x['Island'], 
        xy=x.geometry.coords[0], 
        ha='center',
        weight='bold'
    ), 
    axis=1
);

# It should be noted that sometimes we wish to add text labels "manually", one by one, rather than use a loop or `.apply`. 
# For example, we may want to add labels of specific locations not stored in a layer, or to have control over the specific properties of each label. 
# To add text labels manually, we can run the `.annotate` expressions one at a time, as shown in the code section below recreating the last result with the "manual" approach (@fig-labels-points2).
# <!-- jn: maybe for the "manual" approach example it would be better to specify coordinates by hand rather than using the centroid coordinates? -->

#| label: fig-labels-points2
#| fig-cap: Labels at points (manual)
fig, ax = plt.subplots()
nz.plot(ax=ax, color='none', edgecolor='lightgrey')
ax.annotate(
    ctr['Island'].iloc[0], 
    xy=(ctr.geometry.iloc[0].x, ctr.geometry.iloc[0].y),
    ha='center', weight='bold'
)
ax.annotate(
    ctr['Island'].iloc[1], 
    xy=(ctr.geometry.iloc[1].x, ctr.geometry.iloc[1].y),
    ha='center', weight='bold'
);

# ### Layers {#sec-plot-static-layers}
#
# To display more than one layer in the same static map, we need to:
#
# 1.   Store the first plot in a variable (e.g., `base`)
# 2.   Pass it as the `ax` argument of any subsequent plot(s) (e.g., `ax=base`)
#
# For example, here is how we can plot `nz` and `nz_height` together (@fig-two-layers).

#| label: fig-two-layers
#| fig-cap: Plotting two layers, `nz` (polygons) and `nz_height` (points)
base = nz.plot(color='none')
nz_height.plot(ax=base, color='red');

# We can combine rasters and vector layers in the same plot as well, which we already used earlier in the book, for example when explaining masking and cropping (@fig-raster-crop).
# The technique is to initialize a plot with `fig,ax=plt.subplots()`, then pass `ax` to any of the separate plots, making them appear together.
# <!-- jn: what is fig? what is ax? what is the relation between them? this should be explained somewhere in the book... -->
#
# For example, @fig-plot-raster-and-vector demonstrated plotting a raster with increasingly complicated additions:
#
# -   Panel (a) shows a raster (New Zealand elevation) and a vector layer (New Zealand administrative division)
# -   Panel (b) shows the raster with a buffer of 22.2 $km$ around the dissolved administrative borders, representing New Zealand's [territorial waters](https://en.wikipedia.org/wiki/Territorial_waters) (see @sec-global-operations-and-distances)
# -   Panel (c) shows the raster with two vector layers: the territorial waters (in red) and elevation measurement points (in yellow)

#| label: fig-plot-raster-and-vector
#| fig-cap: Combining a raster and vector layers in the same plot
#| fig-subcap: 
#| - Raster + vector layer
#| - Raster + computed vector layer
#| - Raster + two vector layers
#| layout-ncol: 3
# Raster + vector layer
fig, ax = plt.subplots(figsize=(5, 5))
rasterio.plot.show(nz_elev, ax=ax)
nz.to_crs(nz_elev.crs).plot(ax=ax, facecolor='none', edgecolor='red');
# Raster + computed vector layer
fig, ax = plt.subplots(figsize=(5, 5))
rasterio.plot.show(nz_elev, ax=ax)
gpd.GeoSeries(nz.unary_union, crs=nz.crs) \
    .to_crs(nz_elev.crs) \
    .buffer(22200) \
    .boundary \
    .plot(ax=ax, color='red');
# Raster + two vector layers
fig, ax = plt.subplots(figsize=(5, 5))
rasterio.plot.show(nz_elev, ax=ax)
gpd.GeoSeries(nz.unary_union, crs=nz.crs) \
    .to_crs(nz_elev.crs) \
    .buffer(22200) \
    .exterior \
    .plot(ax=ax, color='red')
nz_height.to_crs(nz_elev.crs).plot(ax=ax, color='yellow');

# <!-- jn: what's facecolor? -->
# <!-- jn: why one example uses .boundary and the other uses .exterior? --> -->
#
# ### Basemaps
#
# Basemaps, or background layers, are often useful to provide context to the displayed layers (which are in the "foreground").
# Basemaps are ubiquitous in interactive maps (see @sec-interactive-maps).
# However, they are often useful in static maps too.
#
# Basemaps can be added to **geopandas** static plots using the [**contextily**](https://contextily.readthedocs.io/en/latest/index.html) package.
# A preliminary step is to convert our layers to `EPSG:3857` (["Web Mercator"](https://en.wikipedia.org/wiki/Web_Mercator_projection)), to be in agreement with the basemaps, which are typically provided in this CRS.
# For example, let's take the small `"Nelson"` polygon from `nz`, and reproject it to `3857`.

nzw = nz[nz['Name'] == 'Nelson'].to_crs(epsg=3857)

# To add a basemap, we use the `contextily.add_basemap` function, similarly to the way we added multiple layers (@sec-plot-static-layers).
# The default basemap is "OpenStreetMap".
# You can specify a different basemap using the `source` parameter, with one of the values in `cx.providers` (@fig-basemap).

#| label: fig-basemap
#| fig-cap: Adding a basemap to a static map, using `contextily`
#| layout-ncol: 3
#| fig-subcap:
#|   - "'OpenStreetMap' basemap"
#|   - "'CartoDB Positron' basemap"
# OpenStreetMap
fig, ax = plt.subplots(figsize=(7, 7))
ax = nzw.plot(color='none', ax=ax)
cx.add_basemap(ax, source=cx.providers.OpenStreetMap.Mapnik);
# CartoDB.Positron
fig, ax = plt.subplots(figsize=(7, 7))
ax = nzw.plot(color='none', ax=ax)
cx.add_basemap(ax, source=cx.providers.CartoDB.Positron);

# Check out the [gallery](https://xyzservices.readthedocs.io/en/stable/gallery.html) for more possible basemaps.
# Custom basemaps (such as from your own raster tile server) can be  also specified using a [URL](https://contextily.readthedocs.io/en/latest/providers_deepdive.html#Manually-specifying-a-provider).
# Finally, you may read the [Adding a background map to plots](https://geopandas.org/en/stable/gallery/plotting_basemap_background.html) tutorial for more examples.
#
# ### Faceted maps
#
# Faceted maps are multiple maps displaying the same symbology for the same spatial layers, but with different data in each panel.
# The data displayed in the different panels typically refer to different properties, or time steps.
# For example, the `nz` layer has several different properties for each polygon, stored as separate attributes:

vars = ['Land_area', 'Population', 'Median_income', 'Sex_ratio']
nz[vars]

# We may want to plot them all in a faceted map, that is, four small maps of `nz` with the different variables.
# To do that, we initialize the plot with the expected number of panels, such as `ncols=len(vars)` if we wish to have one row and four columns, and then go over the variables in a `for` loop, each time plotting `vars[i]` into the `ax[i]` panel (@fig-faceted-map).
# <!-- jn: you mention ncols=len(vars) in the text but uses ncols=4 in the code... I think it should be unified -->

#| label: fig-faceted-map
#| fig-cap: Faceted map, four different variables of `nz`
fig, ax = plt.subplots(ncols=4, figsize=(9, 2))
for i in range(len(vars)):
    nz.plot(ax=ax[i], column=vars[i], legend=True)
    ax[i].set_title(vars[i])

# In case we prefer a specific layout, rather than one row or one column, we can initialize the required number or rows and columns, as in `plt.subplots(nrows,ncols)`, "flatten" `ax`, so that the facets are still accessible using a single index `ax[i]` (rather than the default `ax[i][j]`), and plot into `ax[i]`.
# For example, here is how we can reproduce the last plot, this time in a $2 \times 2$ layout, instead of a $1 \times 4$ layout (@fig-faceted-map2).
# One more modification we are doing here is hiding the axis ticks and labels, to make the map less "crowded", using `ax[i].xaxis.set_visible(False)` (and same for `.yaxis`).

#| label: fig-faceted-map2
#| fig-cap: 2D layout in a faceted map, using a `for` loop
fig, ax = plt.subplots(ncols=2, nrows=int(len(vars)/2), figsize=(6, 6))
ax = ax.flatten()
for i in range(len(vars)):
    nz.plot(ax=ax[i], column=vars[i], legend=True)
    ax[i].set_title(vars[i])
    ax[i].xaxis.set_visible(False)
    ax[i].yaxis.set_visible(False)

# It is also possible to "manually" specify the properties of each panel, and which row/column it goes in (e.g., @fig-spatial-aggregation-different-functions).
# This can be useful when the various panels have different components, or even completely different types of plots (e.g., @fig-zion-transect), making automation with a `for` loop less applicable.
# For example, here is a plot similar to @fig-faceted-map2, but specifying each panel using a separate expression instead of using a `for` loop (@fig-faceted-map3).

#| label: fig-faceted-map3
#| fig-cap: 2D layout in a faceted map, using "manual" specification of the panels 
fig, ax = plt.subplots(ncols=2, nrows=int(len(vars)/2), figsize=(6, 6))
nz.plot(ax=ax[0][0], column=vars[0], legend=True)
ax[0][0].set_title(vars[0])
nz.plot(ax=ax[0][1], column=vars[1], legend=True)
ax[0][1].set_title(vars[1])
nz.plot(ax=ax[1][0], column=vars[2], legend=True)
ax[1][0].set_title(vars[2])
nz.plot(ax=ax[1][1], column=vars[3], legend=True)
ax[1][1].set_title(vars[3]);

# See the first code chunk in the next section for another example of manual panel contents specification.
#
# ### Exporting static maps {#sec-exporting-static-maps}
#
# Static maps can be exported to a file using the [`matplotlib.pyplot.savefig`](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.savefig.html) function.
# For example, the following code section recreates @fig-read-shp-query (see previous Chapter), but this time the last expression saves the image to a JPG image named `plot_geopandas.jpg`.
# <!-- jn: the following code chunk is fairly long... maybe it would be good to replace it with some less complex example? -->

#| output: false
fig, axes = plt.subplots(ncols=2, figsize=(9,5))
tanzania.plot(ax=axes[0], color='lightgrey', edgecolor='grey')
tanzania_neigh.plot(ax=axes[1], color='lightgrey', edgecolor='grey')
tanzania_buf.plot(ax=axes[1], color='none', edgecolor='red')
axes[0].set_title('where')
axes[1].set_title('mask')
tanzania.apply(lambda x: axes[0].annotate(text=x['name_long'], xy=x.geometry.centroid.coords[0], ha='center'), axis=1)
tanzania_neigh.apply(lambda x: axes[1].annotate(text=x['name_long'], xy=x.geometry.centroid.coords[0], ha='center'), axis=1);
plt.savefig('output/plot_geopandas.jpg')

# Figures with rasters can be exported exactly the same way.
# For example, the following code section (@sec-plot-static-layers) creates an image of a raster and a vector layer, which is then exported to a file named `plot_rasterio.jpg`.

#| output: false
fig, ax = plt.subplots(figsize=(5, 5))
rasterio.plot.show(nz_elev, ax=ax)
nz.to_crs(nz_elev.crs).plot(ax=ax, facecolor='none', edgecolor='r');
plt.savefig('output/plot_rasterio.jpg')

# Image file properties can be controlled through the `plt.subplots` and `plt.savefig` parameters.
# For example, the following code section exports the same raster plot to a file named `plot_rasterio2.svg`, which has different dimensions (width = 5 $in$, height = 7 $in$), a different format (SVG), and different resolution (300 $DPI$).

#| output: false
fig, ax = plt.subplots(figsize=(5, 7))
rasterio.plot.show(nz_elev, ax=ax)
nz.to_crs(nz_elev.crs).plot(ax=ax, facecolor='none', edgecolor='r');
plt.savefig('output/plot_rasterio2.svg', dpi=300)

# <!-- ## Animated maps -->
#
# ## Interactive maps {#sec-interactive-maps}
#
# <!-- jn: an intro paragraph is missing -->
#
# ### Minimal example of interactive map
#
# An interactive map of a `GeoSeries` or `GeoDataFrame` can be created with `.explore` (@sec-vector-layers).

#| label: fig-explore
#| fig-cap: Minimal example of an interactive vector layer plot with `.explore`
nz.explore()

# ### Styling
#
# The `.explore` method has a `color` parameter which affects both the fill and outline color.
# Other styling properties are specified using a `dict` through `style_kwds` (for general properties) and the `marker_kwds` (point-layer specific properties), as follows.
#
# The `style_kwds` keys are mostly used to control the color and opacity of the outline and the fill:
#
# -   `stroke`---Whether to draw the outline
# -   `color`---Outline color
# -   `weight`---Outline width (in pixels)
# -   `opacity`---Outline opacity (from `0` to `1`)
# -   `fill`---Whether to draw fill
# -   `fillColor`---Fill color
# -   `fillOpacity`---Fill opacity (from `0` to `1`)
#
# For example, here is how we can set green fill color and 30% opaque black outline of `nz` polygons in `.explore` (@fig-explore-styling-polygons):

#| label: fig-explore-styling-polygons
#| fig-cap: Styling of polygons in `.explore`
nz.explore(color='green', style_kwds={'color':'black', 'opacity':0.3})

# The `dict` passed to `marker_kwds` controls the way that points are displayed:
#
# -   `radius`---Curcle radius (in $m$ for `circle`, see below) or in pixels (for `circle_marker`)
# -   `fill`---Whether to draw fill (for `circle` or `circle_marker`)
#
# Additionally, for points, we can set the `marker_type`, to one of:
#
# -   `'marker'`---A PNG image of a marker
# -   `'circle'`---A vector circle with radius specified in $m$
# -   `'circle_marker'`---A vector circle with radius specified in pixels (the default)
#
# For example, the following expression draws `'circe_marker`' points with 20 pixel radius, green fill, and black outline (@fig-explore-styling-points).

#| label: fig-explore-styling-points
#| fig-cap: Styling of points in `.explore` (using `circle_marker`)
nz_height.explore(
    color='green', 
    style_kwds={'color':'black', 'opacity':0.5, 'fillOpacity':0.1}, 
    marker_kwds={'color':'black', 'radius':20}
)

# @fig-explore-styling-points2 demonstrates the `'marker_type'` option.
# Note that the above-mentioned styling properties (other then `opacity`) are not applicable when using `marker_type='marker'`, because the markers are fixed PNG images.

#| label: fig-explore-styling-points2
#| fig-cap: Styling of points in `.explore` (using `marker`)
nz_height.explore(marker_type='marker')

# <!-- jn: can we use our own png images as well? -->
#
# ### Layers
#
# To display multiple layers, one on top of another, with `.explore`, we use the `m` argument, which stands for the previous map (@fig-explore-layers).

#| label: fig-explore-layers
#| fig-cap: Displaying multiple layers in an interactive map with `.explore`
map1 = nz.explore()
nz_height.explore(m=map1, color='red')

# One of the advantages of interactive maps is the ability to turn layers "on" and "off".
# This capability is implemented in [`folium.LayerControl`](https://python-visualization.github.io/folium/latest/user_guide/ui_elements/layer_control.html#LayerControl) from package **folium**, which the **geopandas** `.explore` method is a wrapper of.
# For example, this is how we can add a layer control for the `nz` and `nz_height` layers (@fig-explore-layers-controls).
# Note the `name` properties, used to specify layer names in the control, and the `collapsed` property, used to specify whether the control is fully visible at all times (`False`), or on mouse hover (`True`, the default).

#| label: fig-explore-layers-controls
#| fig-cap: Displaying multiple layers in an interactive map with `.explore`
m = nz.explore(name='Polygons (adm. areas)')
nz_height.explore(m=m, color='red', name='Points (elevation)')
folium.LayerControl(collapsed=False).add_to(m)
m

# ### Symbology {#sec-explore-symbology}
#
# Symbology can be specified in `.explore` using similar arguments as in `.plot` (@sec-plot-symbology).
# For example, @fig-explore-symbology is an interactive version of @fig-plot-symbology-colors (a).

#| label: fig-explore-symbology
#| fig-cap: 'Symbology in an interactive map of a vector layer, created with `.explore`'
nz.explore(column='Median_income', legend=True, cmap='Reds')

# Fixed styling (@sec-explore-symbology) can be combined with symbology settings.
# For example, polygon outline colors in @fig-explore-symbology are styled according to `'Median_income'`, however, this layer has overlapping outlines and their color is arbitrarily set according to the order of features (top-most features), which may be misleading and confusing.
# To specify fixed outline colors (e.g., black), we can use the `color` and `weight` properties of `style_kwds` (@fig-explore-symbology2):

#| label: fig-explore-symbology2
#| fig-cap: 'Symbology combined with fixed styling in `.explore`'
nz.explore(column='Median_income', legend=True, cmap='Reds', style_kwds={'color':'black', 'weight': 0.5})

# ### Basemaps
#
# The basemap in `.explore` can be specified using the `tiles` argument.
# Several popular built-in basemaps can be specified using a string:
#
# -   `'OpenStreetMap'`
# -   `'CartoDB positron'`
# -   `'CartoDB dark_matter'`
#
# Other basemaps are available through the **xyzservices** package, which needs to be installed (see `xyzservices.providers` for a list), or using a custom tile server URL.
# For example, the following expression displays the `'CartoDB positron'` tiles in an `.explore` map (@fig-explore-basemaps).

#| label: fig-explore-basemaps
#| fig-cap: Specifying the basemap in `.explore`
nz.explore(tiles='CartoDB positron')

# ### Exporting interactive maps
#
# An interactive map can be exported to an HTML file using the `.save` method of the `map` object.
# The HTML file can then be shared with other people, or published on a server and shared through a URL.
# A good free option for publishing a web map is through [GitHub Pages](https://pages.github.com/).
#
# For example, here is how we can export the map shown in @fig-explore-layers-controls, to a file named `map.html`.

#| output: false
m = nz.explore(name='Polygons (adm. areas)')
nz_height.explore(m=m, color='red', name='Points (elevation)')
folium.LayerControl(collapsed=False).add_to(m)
m.save('output/map.html')

# <!-- ### Linking geographic and non-geographic visualizations -->
#
# <!-- ## Mapping applications Streamlit? -->
#
# ## Exercises
#
# ## References

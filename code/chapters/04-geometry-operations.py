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

# # Geometry operations {#sec-geometric-operations}
#
# ## Prerequisites {.unnumbered}

#| echo: false
import pandas as pd
import matplotlib.pyplot as plt
pd.options.display.max_rows = 6
pd.options.display.max_columns = 6
pd.options.display.max_colwidth = 35
plt.rcParams['figure.figsize'] = (5, 5)

# This chapter requires importing the following packages:

import numpy as np
import shapely
import geopandas as gpd
import topojson as tp
import rasterio
import rasterio.warp
import rasterio.plot
import rasterio.mask
import sys

# It also relies on the following data files:

seine = gpd.read_file('data/seine.gpkg')
us_states = gpd.read_file('data/us_states.gpkg')
nz = gpd.read_file('data/nz.gpkg')
src = rasterio.open('data/dem.tif')
src_elev = rasterio.open('output/elev.tif')

# ## Introduction
#
# So far the book has explained the structure of geographic datasets (@sec-spatial-class), and how to manipulate them based on their non-geographic attributes (@sec-attr) and spatial relations (@sec-spatial-operations).
# This chapter focuses on manipulating the geographic elements of geographic objects, for example by simplifying and converting vector geometries, and by cropping raster datasets.
# After reading it you should understand and have control over the geometry column in vector layers and the extent and geographic location of pixels represented in rasters in relation to other geographic objects.
#
# @sec-geo-vec covers transforming vector geometries with 'unary' and 'binary' operations.
# Unary operations work on a single geometry in isolation, including simplification (of lines and polygons), the creation of buffers and centroids, and shifting/scaling/rotating single geometries using 'affine transformations' (@sec-simplification to @sec-affine-transformations).
# Binary transformations modify one geometry based on the shape of another, including clipping and geometry unions, covered in @sec-clipping and @sec-geometry-unions, respectively.
# Type transformations (from a polygon to a line, for example) are demonstrated in Section @sec-type-transformations.
#
# @sec-geo-ras covers geometric transformations on raster objects.
# This involves changing the size and number of the underlying pixels, and assigning them new values.
# It teaches how to change the extent and the origin of a raster "manually" (@sec-extent-and-origin), how to change the resolution in fixed "steps" through aggregation and disaggregation (@sec-raster-agg-disagg), and finally how to resample a raster into any existing template, which is the most general and often most practical approach (@sec-raster-resampling).
# These operations are especially useful if one would like to align raster datasets from diverse sources.
# Aligned raster objects share a one-to-one correspondence between pixels, allowing them to be processed using map algebra operations (@sec-raster-local-operations).
#
# In the next chapter (@sec-raster-vector), we deal with the special case of geometry operations that involve both a raster and a vector layer together.
# It shows how raster values can be 'masked' and 'extracted' by vector geometries.
# Importantly it shows how to 'polygonize' rasters and 'rasterize' vector datasets, making the two data models more interchangeable.
#
# ## Geometric operations on vector data {#sec-geo-vec}
#
# This section is about operations that in some way change the geometry of vector layers.
# It is more advanced than the spatial data operations presented in the previous chapter (in @sec-spatial-vec), because here we drill down into the geometry: the functions discussed in this section work on the geometric part (the geometry column, which is a `GeoSeries` object), either as standalone object or as part of a `GeoDataFrame`.
#
# ### Simplification {#sec-simplification}
#
# Simplification is a process for generalization of vector objects (lines and polygons) usually for use in smaller scale maps.
# Another reason for simplifying objects is to reduce the amount of memory, disk space and network bandwidth they consume: it may be wise to simplify complex geometries before publishing them as interactive maps.
# The **geopandas** package provides the [`.simplify`](https://geopandas.org/en/stable/docs/reference/api/geopandas.GeoSeries.simplify.html) method, which uses the GEOS implementation of the Douglas-Peucker algorithm to reduce the vertex count.
# `.simplify` uses the `tolerance` to control the level of generalization in map units [@douglas_algorithms_1973].
#
# For example, a simplified geometry of a `'LineString'` geometry, representing the river Seine and tributaries, using tolerance of `2000` meters, can be created using the `seine.simplify(2000)` command (@fig-simplify-lines).

#| label: fig-simplify-lines
#| fig-cap: Simplification of the `seine` line layer 
#| layout-ncol: 2
#| fig-subcap: 
#| - Original
#| - Simplified (tolerance = 2000 $m$)
seine_simp = seine.simplify(2000)
seine.plot();
seine_simp.plot();

# The resulting `seine_simp` object is a copy of the original `seine` but with fewer vertices.
# This is apparent, with the result being visually simpler (@fig-simplify-lines, right) and consuming about twice less memory than the original object, as shown in the comparison below.

print(f'Original: {sys.getsizeof(seine)} bytes')
print(f'Simplified: {sys.getsizeof(seine_simp)} bytes')

# Simplification is also applicable for polygons.
# This is illustrated using `us_states`, representing the contiguous United States.
# As we show in @sec-reproj-geo-data, for many calculations **geopandas** (through **shapely**, and, ultimately, GEOS) assumes that the data is in a projected CRS and this could lead to unexpected results when applying distance-related operators.
# Therefore, the first step is to project the data into some adequate projected CRS, such as US National Atlas Equal Area (EPSG:`9311`) (on the left in Figure @fig-simplify-polygons), using `.to_crs` (@sec-reprojecting-vector-geometries).
# <!-- jn: why not EPSG:2163 as in geocompr? -->
# <!-- md: it was deprecated, please see https://gis.stackexchange.com/questions/377099/deprecated-crs-epsg2163-gets-reinterpreted-as-another-crs-epsg9311-by-gdal -->
# <!-- jn: ref to CRS chapter? -->
# <!-- md: done -->

us_states9311 = us_states.to_crs(9311)

# The `.simplify` method from **geopandas** works the same way with a `'Polygon'`/`'MultiPolygon'` layer such as `us_states9311`:

us_states_simp1 = us_states9311.simplify(100000)

# A limitation with `.simplify`, however, is that it simplifies objects on a per-geometry basis.
# This means the "topology" is lost, resulting in overlapping and "holey" areal units as illustrated in @fig-simplify-polygons (b).
# The `.toposimplify` method from package **topojson** provides an alternative that overcomes this issue.
# By [default](https://mattijn.github.io/topojson/example/settings-tuning.html#simplify_algorithm) it uses the Douglas-Peucker algorithm like the `.simplify` method.
# However, another algorithm, known as Visvalingam-Whyatt, which overcomes some limitations of the Douglas-Peucker algorithm [@visvalingam_line_1993], is also available in `.toposimplify`.
# The main advanatage of `.toposimplify` is that it is topologically "aware": it simplifies the combined borders of the polygons (rather than each polygon on its own), thus ensuring that the overlap is maintained.
# The following code chunk uses `.toposimplify` to simplify `us_states9311`.
# Note that, when using the **topojson** package, we first need to calculate a "topology" object, using function `tp.Topology`, and then apply the sumplification function, such as `.toposimplify`, to obtain a simplified layer.
# We are also using the `.to_gdf` method to return a `GeoDataFrame`. 
# <!-- jn: add a sentence or two explaining the code chunk below -->
# <!-- md: added -->

topo = tp.Topology(us_states9311, prequantize=False)
us_states_simp2 = topo.toposimplify(100000).to_gdf()

# @fig-simplify-polygons compares the original input polygons and two simplification methods applied to `us_states9311`.

#| label: fig-simplify-polygons
#| fig-cap: Polygon simplification in action, comparing the original geometry of the contiguous United States with simplified versions, generated with functions from the **geopandas** (middle), and **topojson** (right), packages. 
#| layout-ncol: 3
#| fig-subcap: 
#| - Original
#| - Simplified using **geopandas**
#| - Simplified using **topojson**
us_states9311.plot(color='lightgrey', edgecolor='black');
us_states_simp1.plot(color='lightgrey', edgecolor='black');
us_states_simp2.plot(color='lightgrey', edgecolor='black');

# ### Centroids {#sec-centroids}
#
# Centroid operations identify the center of geographic objects.
# Like statistical measures of central tendency (including mean and median definitions of 'average'), there are many ways to define the geographic center of an object.
# All of them create single point representations of more complex vector objects.
#
# The most commonly used centroid operation is the geographic centroid.
# This type of centroid operation (often referred to as 'the centroid') represents the center of mass in a spatial object (think of balancing a plate on your finger).
# Geographic centroids have many uses, for example to create a simple point representation of complex geometries, to estimate distances between polygons, or to specify the location where polygon text labels are placed.
# Centroids of the geometries in a `GeoSeries` or a `GeoDataFrame` are accessible through the `.centroid` property, as demonstrated in the code below, which generates the geographic centroids of regions in New Zealand and tributaries to the River Seine (black points in @fig-centroid-pnt-on-surface).

nz_centroid = nz.centroid
seine_centroid = seine.centroid

# Sometimes the geographic centroid falls outside the boundaries of their parent objects (think of vector data in shape of a doughnut).
# In such cases 'point on surface' operations, created with the `.representative_point` method, can be used to guarantee the point will be in the parent object (e.g., for labeling irregular multipolygon objects such as island states), as illustrated by the red points in @fig-centroid-pnt-on-surface.
# Notice that these red points always lie on their parent objects.

nz_pos = nz.representative_point()
seine_pos = seine.representative_point()

# The centroids and points in surface are illustrated in @fig-centroid-pnt-on-surface.

#| label: fig-centroid-pnt-on-surface
#| fig-cap: Centroids (black) and points on surface (red) of New Zealand and Seine datasets.
#| layout-ncol: 2
#| fig-subcap: 
#| - New Zealand
#| - Seine
# New Zealand
base = nz.plot(color='white', edgecolor='lightgrey')
nz_centroid.plot(ax=base, color='None', edgecolor='black')
nz_pos.plot(ax=base, color='None', edgecolor='red');
# Seine
base = seine.plot(color='grey')
seine_pos.plot(ax=base, color='None', edgecolor='red')
seine_centroid.plot(ax=base, color='None', edgecolor='black');

# ### Buffers {#sec-buffers}
#
# Buffers are polygons representing the area within a given distance of a geometric feature: regardless of whether the input is a point, line or polygon, the output is a polygon (when using positive buffer distance).
# Unlike simplification, which is often used for visualization and reducing file size, buffering tends to be used for geographic data analysis.
# How many points are within a given distance of this line?
# Which demographic groups are within travel distance of this new shop?
# These kinds of questions can be answered and visualized by creating buffers around the geographic entities of interest.
#
# @fig-buffers illustrates buffers of two different sizes (5 and 50 $km$) surrounding the river Seine and tributaries.
# These buffers were created with commands below, using the `.buffer` method, applied to a `GeoSeries` or `GeoDataFrame`.
# The `.buffer` method requires one important argument: the buffer distance, provided in the units of the CRS, in this case, meters (@fig-buffers).

#| label: fig-buffers
#| fig-cap: Buffers around the Seine dataset of 5 km (left) and 50 km (right). Note the colors, which reflect the fact that one buffer is created per geometry feature.
#| layout-ncol: 2
#| fig-subcap: 
#| - 5 $km$ buffer
#| - 50 $km$ buffer
seine_buff_5km = seine.buffer(5000)
seine_buff_50km = seine.buffer(50000)
seine_buff_5km.plot(color='none', edgecolor=['c', 'm', 'y']);
seine_buff_50km.plot(color='none', edgecolor=['c', 'm', 'y']);

# Note that both `.centroid` and `.buffer` return a `GeoSeries` object, even when the input is a `GeoDataFrame`.

seine_buff_5km

# In the common scenario when the original attributes of the input features need to be retained, you can replace the existing geometry with the new `GeoSeries` by creating a copy of the original `GeoDataFrame` and assigning the new buffer `GeoSeries` to the `geometry` column.

seine_buff_5km = seine.copy()
seine_buff_5km.geometry = seine.buffer(5000)
seine_buff_5km

# Alternative option is to add a secondary geometry column directly to the original `GeoDataFrame`.

seine['geometry_5km'] = seine.buffer(5000)
seine

# You can then switch to either geometry column (i.e., make it the "active" geometry column) using `.set_geometry`, as in:

seine = seine.set_geometry('geometry_5km')

# Let's revert to the original state of `seine` before moving on to the next section.

seine = seine.set_geometry('geometry')
seine = seine.drop('geometry_5km', axis=1)

# ### Affine transformations {#sec-affine-transformations}
#
# Affine transformations include, among others, shifting (translation), scaling and rotation, or any combination of these.
# They preserves lines and parallelism, by angles and lengths are not necessarily preserved.
# These transformations are an essential part of geocomputation.
# For example, shifting is needed for labels placement, scaling is used in non-contiguous area cartograms, and many affine transformations are applied when reprojecting or improving the geometry that was created based on a distorted or wrongly projected map.
#
# The **geopandas** package implements affine transformation, for objects of classes `GeoSeries` and `GeoDataFrame`.
# In both cases, the method is applied on the `GeoSeries` part, returning a just the `GeoSeries` of transformed geometries.
# <!-- jn: and what if the input is a GeoDataFrame? what happens to the other columns? -->
# <!-- md: just the 'GeoSeries' part is returned. to make that more clear, the results are now printed  -->
#
# Affine transformations of `GeoSeries` can be done using the [`.affine_transform`](https://geopandas.org/en/stable/docs/reference/api/geopandas.GeoSeries.affine_transform.html) method, which is a wrapper around the `shapely.affinity.affine_transform` function.
# As [documented](https://shapely.readthedocs.io/en/stable/manual.html#shapely.affinity.affine_transform), a 2D affine transformation requires a six-parameter list `[a,b,d,e,xoff,yoff]` which represents the following equations for transforming the coordinates (@eq-affine1 and @eq-affine2)/
#
# $$
# x' = a x + b y + x_\mathrm{off}
# $$ {#eq-affine1}
#
# $$
# y' = d x + e y + y_\mathrm{off}
# $$ {#eq-affine2}
#
# There are also simplified `GeoSeries` [methods](https://geopandas.org/en/stable/docs/user_guide/geometric_manipulations.html#affine-transformations) for specific scenarios, such as:
#
# -   `.translate(xoff=0.0, yoff=0.0)`
# -   `.scale(xfact=1.0, yfact=1.0, origin='center')`
# -   `.rotate(angle, origin='center', use_radians=False)`
# -   `.skew(angle, origin='center', use_radians=False)`
#
# For example, *shifting* only requires the $x_{off}$ and $y_{off}$, using [`.translate`](https://geopandas.org/en/stable/docs/reference/api/geopandas.GeoSeries.translate.html).
# <!-- jn: and what with z_off? -->
# <!-- md: right! now added a note, and removed the z parameters to avoid confusion -->
# The code below shifts the y-coordinates of `nz` by 100 $km$ to the north, but leaves the x-coordinates untouched.

nz_shift = nz.translate(0, 100000)
nz_shift

# ::: callout-note
# **shapely**, and consequently **geopandas**, operations, typically [ignore](https://shapely.readthedocs.io/en/stable/manual.html#geometric-objects) the z-dimension of geometries in operations. For example, `shapely.LineString([(0,0,0),(0,0,1)]).length` returns `0` (and not `1`), since `.length` ignores the z-dimension. In this book (like in most real-world spatial analysis applications), we deal only with two-dimensional geometries.
# :::
#
# Scaling enlarges or shrinks objects by a factor, and can be applied either globally or locally.
# Global scaling increases or decreases all coordinates values in relation to the origin coordinates, while keeping all geometries topological relations intact.
# **geopandas** implements local scaling using the [`.scale`](https://geopandas.org/en/stable/docs/reference/api/geopandas.GeoSeries.scale.html) method.
# <!-- jn: what with global scaling? -->
# <!-- md: I think that global scaling can be acheived when passing a "center" that is the same for all geometries (rather than the centroid of each). I'm not 100% sure that's the definition of "global" scaling - will be happy if you can confirm and then will be happy to add it to the note below. -->
# Local scaling treats geometries independently and requires points around which geometries are going to be scaled, e.g., centroids.
# In the example below, each geometry is shrunk by a factor of two around the centroids (@fig-affine-transformations (b)).
# To achieve that, we pass the `0.5` and `0.5` scaling factors (for x and y, respectively), and the `'centroid'` option for the point of origin.
# <!-- jn: next sentence as a block? -->
# <!-- md: done -->

nz_scale = nz.scale(0.5, 0.5, origin='centroid')
nz_scale

# ::: callout-note
# When setting the `origin` in `.scale`, other than `'centroid'` it is possible to use `'center'`, for the bounding box center, or specific point coordinates, such as `(0,0)`.
# :::
#
# Rotating the geometries can be done using the [`.rotate`](https://geopandas.org/en/stable/docs/reference/api/geopandas.GeoSeries.rotate.html) method.
# When rotating, we need to specify the rotation angle (positive values imply clockwise rotation) and the `origin` points (using the same options as in `scale`).
# For example, the following expression rotates `nz` by 30 degrees counter-clockwise, around the geometry centroids.

nz_rotate = nz.rotate(-30, origin='centroid')
nz_rotate

# @fig-affine-transformations shows the original layer `nz`, and the shifting, scaling and rotation results.

#| label: fig-affine-transformations
#| fig-cap: 'Illustrations of affine transformations: shift, scale and rotate'
#| layout-ncol: 3
#| fig-subcap: 
#| - Shift
#| - Scale
#| - Rotate
# Shift
base = nz.plot(color='lightgrey', edgecolor='darkgrey')
nz_shift.plot(ax=base, color='red', edgecolor='darkgrey');
# Scale
base = nz.plot(color='lightgrey', edgecolor='darkgrey')
nz_scale.plot(ax=base, color='red', edgecolor='darkgrey');
# Rotate
base = nz.plot(color='lightgrey', edgecolor='darkgrey')
nz_rotate.plot(ax=base, color='red', edgecolor='darkgrey');

# <!-- jn: you also mentioned skew before -- why it is not shown here? -->
# <!-- md: these example follow geocompr (https://r.geocompx.org/geometry-operations#fig:affine-trans), where skew is also not shown. IMHO it's less useful, so maybe we can omit skew from the text? -->
#
# ### Pairwise geometry-generating operations {#sec-clipping}
#
# Spatial clipping is a form of spatial subsetting that involves changes to the geometry columns of at least some of the affected features.
# Clipping can only apply to features more complex than points: lines, polygons and their 'multi' equivalents.
# To illustrate the concept we will start with a simple example: two overlapping circles with a center point one unit away from each other and a radius of one (@fig-overlapping-circles).

#| label: fig-overlapping-circles
#| fig-cap: Overlapping polygon (circle) geometries `x` and `y`
x = shapely.Point((0, 0)).buffer(1)
y = shapely.Point((1, 0)).buffer(1)
shapely.GeometryCollection([x, y])

# Imagine you want to select not one circle or the other, but the space covered by both x and y.
# This can be done using the `.intersection` method from **shapely**, illustrated using objects named `x` and `y` which represent the left- and right-hand circles (@fig-intersection).

#| label: fig-intersection
#| fig-cap: Intersection between `x` and `y`
x.intersection(y)

# More generally, clipping is an example of a 'pairwise geometry-generating operation', where new geometries are generated from two inputs.
# Other than `.intersection` (@fig-intersection), there are three other standard pairwise operators: `.difference` (@fig-difference), `.union` (@fig-union), and `.symmetric_difference` (@fig-symmetric-difference).

#| label: fig-difference
#| fig-cap: Difference between `x` and `y` (namely, `x` "minus" `y`)
x.difference(y)

#| label: fig-union
#| fig-cap: Union of `x` and `y` 
x.union(y)

#| label: fig-symmetric-difference
#| fig-cap: Symmetric difference between `x` and `y`
x.symmetric_difference(y)

# Keep in mind that `x` and `y` are interchangeable in all predicates except for `.difference`, where `x.difference(y)` means `x` minus `y`, whereas `y.difference(x)` means `y` minus `x`.
#
# The latter examples demonstrate pairwise operations between individual `shapely` geometries.
# The **geopandas** package, as is often the case, contains wrappers of these **shapely** functions to be applied to multiple, or pairwise, use cases.
# For example, applying either of the pairwise methods on a `GeoSeries` or `GeoDataFrame`, combined with a `shapely` geometry, returns the pairwise (many-to-one) results (which is analogous to other operators, like `.intersects` or `.distance`, see @sec-spatial-subsetting-vector and @sec-distance-relations, respectively).
#
# Let's demonstrate the "many-to-one" scenario by calculating the difference between each geometry in a `GeoSeries` and a "fixed" `shapely` geometry.
# To create the latter, let's take `x` and combine it with itself translated (@sec-affine-transformations) to a distance of `1` and `2` units "upwards" on the y-axis.

geom1 = gpd.GeoSeries([x])
geom2 = geom1.translate(0, 1)
geom3 = geom1.translate(0, 2)
geom = pd.concat([geom1, geom2, geom3])
geom

# @fig-geom-intersection shows the `GeoSeries` `geom` with the `shapely` geometry (in red) that we will intersect with it.

#| label: fig-geom-intersection
#| fig-cap: A `GeoSeries` with three circles, and a `shapely` geometry that we will "subtract" from it (in red)
fig, ax = plt.subplots()
geom.plot(color='lightgrey', edgecolor='black', ax=ax)
gpd.GeoSeries(y).plot(color='#FF000040', edgecolor='black', ax=ax);

# Now, using `.intersection` automatically applies the **shapely** method of the same name on each geometry in `geom`, returning a new `GeoSeries`, which we name `geom_inter_y`, with the pairwise "intersections".
# Note the empty third geometry (can you explain the meaning of this result?).

geom_inter_y = geom.intersection(y)
geom_inter_y

# @fig-geom-intersection2 is a plot of the result `geom_inter_y`.

# +
#| label: fig-geom-intersection2
#| fig-cap: The output `GeoSeries`, after subtracting a `shapely` geometry using `.intersection`

geom_inter_y.plot(color='lightgrey', edgecolor='black');
# -

# The `.overlay` method (see @sec-joining-incongruent-layers) further extends this technique, making it possible to apply "many-to-many" pairwise geometry generations between all pairs of two `GeoDataFrame`s.
# The output is a new `GeoDataFrame` with the pairwise outputs, plus the attributes of both inputs which were the inputs of the particular pairwise output geometry.
# See the ["Set operations with overlay"](https://geopandas.org/en/stable/docs/user_guide/set_operations.html) article in the **geopandas** documentation for examples of `.overlay`.
#
# ### Subsetting vs. clipping {#sec-subsetting-vs-clipping}
#
# In the last two chapters we have introduced two types of spatial operators: boolean, such as `.intersects` (@sec-spatial-subsetting-vector), and geometry-generating, such as `.intersection` (@sec-clipping).
# Here, we illustrate the difference between them.
# We do this using the specific scenario of subsetting points by polygons, where (unlike in other cases) both methods can be used for the same purpose and giving the same result.
# <!-- Clipping objects can change their geometry but it can also subset objects, returning only features that intersect (or partly intersect) with a clipping/subsetting object.  -->
#
# To illustrate the point, we will subset points that cover the bounding box of the circles `x` and `y` from @fig-overlapping-circles.
# Some points will be inside just one circle, some will be inside both and some will be inside neither.
# The following code sections generates the sample data for this section, a simple random distribution of points within the extent of circles `x` and `y`, resulting in output illustrated in @fig-random-points.
# We create the sample points in two steps.
# First, we figure out the bounds where random points are to be generated.

bounds = x.union(y).bounds
bounds

# Second, we use `np.random.uniform` to calculate `n` random x- and y-coordinates within the given bounds.

np.random.seed(1)
n = 10
coords_x = np.random.uniform(bounds[0], bounds[2], n)
coords_y = np.random.uniform(bounds[1], bounds[3], n)
coords = list(zip(coords_x, coords_y))
coords

# Third, we transform the list of coordinates into a `list` of `shapely` points and then to a `GeoSeries`.

pnt = [shapely.Point(i) for i in coords]
pnt = gpd.GeoSeries(pnt)

# The result `pnt`, which `x` and `y` circles in the background, is shown in @fig-random-points.

#| label: fig-random-points
#| fig-cap: Randomly distributed points within the bounding box enclosing circles x and y. The point that intersects with both objects x and y are highlighted. 
base = pnt.plot(color='none', edgecolor='black')
gpd.GeoSeries([x]).plot(ax=base, color='none', edgecolor='darkgrey');
gpd.GeoSeries([y]).plot(ax=base, color='none', edgecolor='darkgrey');

# Now, we can get back to our question: how to subset the points to only return the point that intersects with both `x` and `y`?
# The code chunks below demonstrate two ways to achieve the same result.
# In the first approach, we can calculate a boolean `Series`, evaluating whether each point of `pnt` intersects with the intersection of `x` and `y` (see @sec-spatial-subsetting-vector) and then use it to subset `pnt` to get the result `pnt1`.

sel = pnt.intersects(x.intersection(y))
pnt1 = pnt[sel]
pnt1

# In the second approach, we can also find the intersection between the input points represented by `pnt`, using the intersection of `x` and `y` as the subsetting/clipping object.
# Since the second argument is an individual `shapely` geometry (`x.intersection(y)`), we get "pairwise" intersections of each `pnt` with it (see @sec-clipping):

pnt2 = pnt.intersection(x.intersection(y))
pnt2

# The subset `pnt2` is shown in @fig-intersection-points.

#| label: fig-intersection-points
#| fig-cap: Randomly distributed points within the bounding box enclosing circles x and y. The point that intersects with both objects x and y are highlighted. 
base = pnt.plot(color='none', edgecolor='black')
gpd.GeoSeries([x]).plot(ax=base, color='none', edgecolor='darkgrey');
gpd.GeoSeries([y]).plot(ax=base, color='none', edgecolor='darkgrey');
pnt2.plot(ax=base, color='red');

# The only difference between the two approaches is that `.intersection` returns all "intersections", even if they are empty.
# When these are filtered out, `pnt2` becomes identical to `pnt1`:

pnt2 = pnt2[~pnt2.is_empty]
pnt2

# <!-- This second approach will return features that partly intersect with `x.intersection(y)` but with modified geometries for spatially extensive features that cross the border of the subsetting object. The results are identical, but the implementation differs substantially. -->
#
# The example above is rather contrived and provided for educational rather than applied purposes.
# However, we encourage the reader to reproduce the results to deepen your understanding for handling geographic vector objects in Python. 
# <!-- as it raises an important question: which implementation to use? -->
# <!-- Generally, more concise implementations should be favored, meaning the first approach above. -->
# <!-- jn: is the first approach really more concise? why? -->
# <!-- md: sorry, this sentence comes from 'geocompr', and it's not transferable to the Python version, so now removed. -->
#
# ### Geometry unions {#sec-geometry-unions}
#
# Spatial aggregation can silently dissolve the geometries of touching polygons in the same group, as we saw in @sec-vector-attribute-aggregation.
# This is demonstrated in the code chunk below, in which 49 `us_states` are aggregated into 4 regions using the `.dissolve` method.

regions = us_states[['REGION', 'geometry', 'total_pop_15']] \
    .dissolve(by='REGION', aggfunc='sum').reset_index()
regions

# @fig-dissolve compares the original `us_states` layer with the aggregated `regions` layer.

#| label: fig-dissolve
#| fig-cap: "Spatial aggregation on contiguous polygons, illustrated by aggregating the population of 49 US states into 4 regions, with population represented by color. Note the operation automatically dissolves boundaries between states."
#| layout-ncol: 2
#| fig-subcap: 
#| - 49 States
#| - 4 Regions
# States
fig, ax = plt.subplots(figsize=(9, 2.5))
us_states.plot(ax=ax, edgecolor='black', column='total_pop_15', legend=True);
# Regions
fig, ax = plt.subplots(figsize=(9, 2.5))
regions.plot(ax=ax, edgecolor='black', column='total_pop_15', legend=True);

# What is happening with the geometries here?
# Behind the scenes, `.dissolve` combines the geometries and dissolve the boundaries between them using the [`.unary_union`](https://geopandas.org/en/stable/docs/reference/api/geopandas.GeoSeries.unary_union.html#geopandas.GeoSeries.unary_union) method per group.
# This is demonstrated in the code chunk below which creates a united western US using the standalone `unary_union` operation.
# Note that the result is a `shapely` geometry, as the individual attributes are "lost" as part of dissolving (@fig-dissolve2).

#| label: fig-dissolve2
#| fig-cap: Western US
us_west = us_states[us_states['REGION'] == 'West']
us_west_union = us_west.geometry.unary_union
us_west_union

# To dissolve two (or more) groups of a `GeoDataFrame` into one geometry, we can either (a) use a combined condition or  (b) concatenate the two separate subsets and then dissove using `.unary_union`.

# Approach 1
sel = (us_states['REGION'] == 'West') | (us_states['NAME'] == 'Texas')
texas_union = us_states[sel]
texas_union = texas_union.geometry.unary_union
# Approach 2
us_west = us_states[us_states['REGION'] == 'West']
texas = us_states[us_states['NAME'] == 'Texas']
texas_union = pd.concat([us_west, texas]).unary_union

# The result is identical in both cases, shown in @fig-dissolve3.

#| label: fig-dissolve3
#| fig-cap: Western US and Texas
texas_union

# ### Type transformations {#sec-type-transformations}
#
# <!-- jn: I do not fully understand the story(ies) in this section. Please think about it -- maybe it can be reordered or some connecting sentences could be added... -->
#
# Transformation of geometries, from one type to another, also known as "geometry casting", is often required to facilitate spatial analysis.
# Either the **geopandas** or the **shapely** packages can be used for geometry casting, depending on the type of transformation, and the way that the input is organized (whether and individual geometry, or a vector layer).
# Therefore, the exact expression(s) depend on the specific transformation we are interested in.
#
# In general, you need to figure out the required input of the respective construstor function according to the "destination" geometry (e.g., `shapely.LineString`, etc.), then reshape the input of the "source" geometry into the right form to be passed to that function.
# Or, when available, you can use a wrapper from **geopandas**.
#
# In this section we demonstrate several common scenarios. 
# We start with transformations of individual geometries from one type to another, using **shapely** methods:
#
# * `'MultiPoint'` to `'LineString'` (@fig-type-transform-linestring)
# * `'MultiPoint'` to `'Polygon'` (@fig-type-transform-polygon)
# * `'LineString'` to `'MultiPoint'` (@fig-type-transform-multipoint2)
# * `'LineString'` to `'Polygon'` (@fig-type-transform-polygon2)
# * `'Polygon'`s to `'MultiPolygon'` (@fig-type-transform-multipolygon)
# * `'MultiPolygon'`s to `'Polygon'`s (@fig-type-transform-multipolygon1, @fig-type-transform-multipolygon2)
#
# Then, we move on and demonstrate casting workflows on `GeoDataFrame`s, where we have further considerations, such as keeping track of geometry attributes, and the possibility of dissolving, rather than just combining, geometries. As we will see, these are done either by "manually" applying **shapely** methods on all geometries in the given layer, or using **geopandas** wrapper methods which do it automatically:
#
# * `'MultiLineString'` to `'LineString'`s (using `.explode`) (@fig-multilinestring-to-linestring)
# * `'LineString'` to `'MultiPoint'`s (using `.apply`) (@fig-linestring-to-multipoint)
# * `'LineString'`s to `'MultiLineString'` (using `.dissolve`)
# * `'Polygon'`s to `'MultiPolygon'` (using `.dissolve` or `.agg`) (@fig-combine-geoms)
# * `'Polygon'` to `'(Multi)LineString'` (using `.boundary` or `.exterior`) (demonstrated in a subsequent chapter, see @sec-rasterizing-lines-and-polygons)
#
# Let's start with the simple individual-geometry casting examples, to illustrate how geometry casting works on **shapely** geometry objects. 
# First, let's create a `'MultiPoint'` (@fig-type-transform-multipoint).

#| label: fig-type-transform-multipoint
#| fig-cap: A `'MultiPoint'` geometry used to demonstrate **shapely** type transformations
multipoint = shapely.MultiPoint([(1,1), (3,3), (5,1)])
multipoint

# A `'LineString'` can be created using `shapely.LineString` from a `list` of points.
# Thus, a `'MultiPoint'` can be converted to a `'LineString'` by extracting the individual points into a `list`, then passing them to `shapely.LineString` (@fig-type-transform-linestring).
# <!--jn: maybe it would be worth reexplaing .geoms here? -->

#| label: fig-type-transform-linestring
#| fig-cap: A `'LineString'` created from the `'MultiPoint'` in @fig-type-transform-multipoint
linestring = shapely.LineString(list(multipoint.geoms))
linestring

# Similarly, a `'Polygon'` can be created using function `shapely.Polygon`, which accepts a sequence of point coordinates.
# In principle, the last coordinate must be equal to the first, in order to form a closed shape.
# However, `shapely.Polygon` is able to complete the last coordinate automatically, and therefore we can pass all of the coordinates of the `'MultiPoint'` directly to `shapely.Polygon` (@fig-type-transform-polygon).

#| label: fig-type-transform-polygon
#| fig-cap: A `'Polygon'` created from the `'MultiPoint'` in @fig-type-transform-multipoint
polygon = shapely.Polygon([[p.x, p.y] for p in multipoint.geoms])
polygon

# The source `'MultiPoint'` geometry, and the derived `'LineString'` and `'Polygon'` geometries are shown in @fig-casting1.
# Note that we convert the `shapely` geometries to `GeoSeries` to be able to use the **geopandas** `.plot` method.

#| label: fig-casting1
#| fig-cap: Examples of `'LineString`' and `'Polygon'` casted from a `'MultiPoint'` geometry
#| layout-ncol: 3
#| fig-subcap: 
#| - 'MultiPoint'
#| - 'LineString'
#| - 'Polygon'
gpd.GeoSeries(multipoint).plot();
gpd.GeoSeries(linestring).plot();
gpd.GeoSeries(polygon).plot();

# Conversion from `'MultiPoint'` to `'LineString'` (@fig-type-transform-linestring) is a common operation that creates a line object from ordered point observations, such as GPS measurements or geotagged media.
# This allows spatial operations such as the length of the path traveled.
# Conversion from `'MultiPoint'` or `'LineString'` to `'Polygon'` (@fig-type-transform-polygon) is often used to calculate an area, for example from the set of GPS measurements taken around a lake or from the corners of a building lot.
#
# Our `'LineString'` geometry can be converted back to a `'MultiPoint'` geometry by passing its coordinates directly to `shapely.MultiPoint` (@fig-type-transform-multipoint2).

#| label: fig-type-transform-multipoint2
#| fig-cap: A `'MultiPoint'` created from the `'LineString'` in @fig-type-transform-linestring
shapely.MultiPoint(linestring.coords)

# A `'Polygon'` (exterior) coordinates can be passed to `shapely.MultiPoint`, to go back to a `'MultiPoint'` geometry, as well (@fig-type-transform-polygon2).

#| label: fig-type-transform-polygon2
#| fig-cap: A `'MultiPoint'` created from the `'Polygon'` in @fig-type-transform-polygon
shapely.MultiPoint(polygon.exterior.coords)

# Using these methods, we can transform between `'Point'`, `'LineString'`, and `'Polygon'` geometries, assuming there is a sufficient number of points (at least two to form a line, and at least three to form a polygon).
# When dealing with multi-part geometries using **shapely**, we can:
#
# -   Access single-part geometries (e.g., each `'Polygion'` in a `'MultiPolygon'` geometry) using `.geoms[i]`, where `i` is the index of the geometry
# -   Combine single-part geometries into a multi-part geometry, by passing a `list` of the latter to the constructor function
#
# For example, here is how we combine two `'Polygon'` geometries into a `'MultiPolygon'` (while also using a **shapely** affine function `shapely.affinity.translate`, which is underlying the **geopandas** `.translate` method used earlier, see @sec-affine-transformations) (@fig-type-transform-multipolygon):

# +
#| label: fig-type-transform-multipolygon
#| fig-cap: A `'MultiPolygon'` created from the `'Polygon'` in @fig-type-transform-polygon and another polygon

multipolygon = shapely.MultiPolygon([
    polygon, 
    shapely.affinity.translate(polygon.centroid.buffer(1.5), 3, 2)
])
multipolygon
# -

# Now, here is how we can get back the `'Polygon'` part 1 (@fig-type-transform-multipolygon1):

# +
#| label: fig-type-transform-multipolygon1
#| fig-cap: The 1^st^ "part" extracted from the `'MultiPolygon'` in @fig-type-transform-multipolygon

multipolygon.geoms[0]
# -

# and part 2 (@fig-type-transform-multipolygon2):

# +
#| label: fig-type-transform-multipolygon2
#| fig-cap: The 2^nd^ "part" extracted from the `'MultiPolygon'` in @fig-type-transform-multipolygon

multipolygon.geoms[1]
# -

# However, dealing with multi-part geometries can be easier with **geopandas**. Thanks to the fact that geometries in a `GeoDataFrame` are associated with attributes, we can keep track of the origin of each geometry: duplicating the attributes when going from multi-part to single-part (using `.explode`, see below), or "collapsing" the attributes through aggregation when going from single-part to multi-part (using `.dissolve`, see @sec-geometry-unions).
# <!-- jn: the above paragraph is dense and hard to read -->
# <!-- md: agree, now rephrased -->
#
# Let's demonstrate going from multi-part to single-part (@fig-multilinestring-to-linestring) and then back to multi-part (@sec-geometry-unions), using a small line layer.
# <!-- jn: demonstrate what? -->
# <!-- md: right, now added references -->
# As input, we will create a `'MultiLineString'` geometry composed of three lines (@fig-type-transform-multilinestring3).

#| label: fig-type-transform-multilinestring3
#| fig-cap: A `'MultiLineString'` geometry composed of three lines
l1 = shapely.LineString([(1, 5), (4, 3)])
l2 = shapely.LineString([(4, 4), (4, 1)])
l3 = shapely.LineString([(2, 2), (4, 2)])
ml = shapely.MultiLineString([l1, l2, l3])
ml

# Let's place it into a `GeoSeries`.

geom = gpd.GeoSeries([ml])
geom

# Then, put it into a `GeoDataFrame` with an attribute called `'id'`:

dat = gpd.GeoDataFrame(geometry=geom, data=pd.DataFrame({'id': [1]}))
dat

# You can imagine it as a road or river network.
# The above layer `dat` has only one row that defines all the lines.
# This restricts the number of operations that can be done, for example it prevents adding names to each line segment or calculating lengths of single lines.
# Using **shapely** methods with which we are already familiar with (see above), the individual single-part geometries (i.e., the "parts") can be accessed through the `.geoms` property.

list(ml.geoms)

# However, specifically for the "multi-part to single part" type transformation scenarios, there is also a method called `.explode`, which can convert an entire multi-part `GeoDataFrame` to a single-part one.
# The advantage is that the original attributes (such as `id`) are retained, so that we can keep track of the original multi-part geometry properties that each part came from.
# The `index_parts=True` argument also lets us keep track of the original multipart geometry indices, and part indices, named `level_0` and `level_1`, respectively.

dat1 = dat.explode(index_parts=True).reset_index()
dat1

# For example, here we see that all `'LineString'` geometries came from the same multi-part geometry (`level_0`=`0`), which had three parts (`level_1`=`0`,`1`,`2`).
# @fig-multilinestring-to-linestring demonstrates the effect of `.explode` in converting a layer with multi-part geometries into a layer with single part geometries.

#| label: fig-multilinestring-to-linestring
#| fig-cap: Transformation a `'MultiLineString'` layer with one feature, into a `'LineString'` layer with three features, using `.explode`
#| layout-ncol: 2
#| fig-subcap: 
#| - MultiLineString layer
#| - LineString layer, after applying `.explode`
dat.plot(column='id');
dat1.plot(column='level_1');

# As a side-note, let's demonstrate how the above **shapely** casting methods can be translated to **geopandas**. 
# Suppose that we want to transform `dat1`, which is a layer of type `'LineString'` with three features, to a layer of type `'MultiPoint'` (also with three features). 
# Recall that for a single geometry, we use the expression `shapely.MultiPoint(x.coords)`, where `x` is a `'LineString'` (@fig-type-transform-multipoint2). 
# When dealing with a `GeoDataFrame`, we wrap the conversion into `.apply`, to apply it on all geometries:

dat2 = dat1.copy()
dat2.geometry = dat2.geometry.apply(lambda x: shapely.MultiPoint(x.coords))
dat2

# The result is illustrated in @fig-linestring-to-multipoint.

#| label: fig-linestring-to-multipoint
#| fig-cap: Transformation a `'LineString'` layer with three features, into a `'MultiPoint'` layer (also with three features), using `.apply` and **shapely** methods
#| layout-ncol: 2
#| fig-subcap: 
#| - LineString layer
#| - MultiPoint layer
dat1.plot(column='level_1');
dat2.plot(column='level_1');

# The opposite transformation, i.e., "single-part to multi-part", is achieved using the `.dissolve` method (which we are already familiar with, see @sec-geometry-unions).
# For example, here is how we can get back to the `'MultiLineString'` geometry:

dat1.dissolve(by='id').reset_index()

# The next code chunk is another example, dissolving the `nz` north and south parts into `'MultiPolygon'` geometries.

nz_dis1 = nz[['Island', 'Population', 'geometry']] \
    .dissolve(by='Island', aggfunc='sum') \
    .reset_index()
nz_dis1

# Note that `.dissolve` not only combines single-part into multi-part geometries, but also dissolves any internal borders.
# So, in fact, the result may be single-part (in case when all parts touch each other, unlike in `nz`).
# If, for some reason, we want to combine geometries into multi-part *without* dissolving, we can fall back to the **pandas** `.agg` method (custom table aggregation), supplemented with a **shapely** function specifying how exactly we want to transform each group of geometries into a new single geometry.
# In the following example, for instance, we collect all `'Polygon'` and `'MultiPolygon'` parts of `nz` into a single `'MultiPolygon'` geometry with many separate parts (i.e., without dissolving), per group (`Island`).

#| warning: false
nz_dis2 = nz \
    .groupby('Island') \
    .agg({
        'Population': 'sum',
        'geometry': lambda x: shapely.MultiPolygon(x.explode().to_list())
    }) \
    .reset_index()
nz_dis2 = gpd.GeoDataFrame(nz_dis2).set_geometry('geometry').set_crs(nz.crs)
nz_dis2

# The difference between the last two results (with and without dissolving, respectively) is not evident in the printout: in both cases we got a layer with two features of type `'MultiPolygon'`.
# However, in the first case internal borders were dissolved, while in the second case they were not.
# This is illustrated in @fig-combine-geoms:

#| label: fig-combine-geoms
#| fig-cap: Combining New Zealand geometries into one, for each island, with and witout dissolving
#| layout-ncol: 2
#| fig-subcap: 
#| - Dissolving (using the **geopandas** `.dissolve` method)
#| - Combining into multi-part without dissolving (using `.agg` and a custom **shapely**-based function)
nz_dis1.plot(color='lightgrey', edgecolor='black');
nz_dis2.plot(color='lightgrey', edgecolor='black');

# It is also worthwhile to note the `.boundary` and `.exterior` properties of `GeoSeries`, which are used to cast polygons to lines, with or without interior rings, respectively (see @sec-rasterizing-lines-and-polygons). 
#
# ## Geometric operations on raster data {#sec-geo-ras}
#
# <!-- jn: raster intro is missing (vector has an intro) -->
#
# ### Geometric intersections {#sec-raster-geometric-intersections}
#
# <!-- jn: Michael, what is the difference between this section and the section about cropping and masking in the next chapter?  -->
# <!-- In geocompr, the difference is clean -- the first section is about cliping a raster with another raster; the second section is about cropping a raster with a vector. -->
# <!-- Here, the difference is not clear to me. -->
# <!-- If there is no difference, maybe we should either rewrite this section or remove it. -->
#
# In @sec-spatial-subsetting-raster we have shown how to extract values from a raster overlaid by coordinates or by a matching boolean mask.
# A different case is when the area of interest is defined by any general (possibly non-matching) raster B, to retrieve a spatial output of a (smaller) subset of raster A we can:
#
# -   Extract the bounding box polygon of B (hereby, `clip`)
# -   Mask and crop A (hereby, `elev.tif`) using B (@sec-raster-cropping)
#
# For example, suppose that we want to get a subset of the `elev.tif` raster using another, smaller, raster.
# To demonstrate this, let's create (see @sec-raster-from-scratch) that smaller raster, hereby named `clip`.
# First, we need to create a $3 \times 3$ array of raster values.

clip = np.array([1] * 9).reshape(3, 3)
clip

# Then, we define the transformation matrix, in such a way that `clip` intersects with `elev.tif` (@fig-raster-intersection).

new_transform = rasterio.transform.from_origin(
    west=0.9, 
    north=0.45, 
    xsize=0.3, 
    ysize=0.3
)
new_transform

# Now, for subsetting, we will derive a `shapely` geometry representing the `clip` raster extent, using [`rasterio.transform.array_bounds`](https://rasterio.readthedocs.io/en/latest/api/rasterio.transform.html#rasterio.transform.array_bounds).

bbox = rasterio.transform.array_bounds(
    clip.shape[1], # columns
    clip.shape[0], # rows
    new_transform
)
bbox

# The four numeric values can be transformed into a rectangular `shapely` geometry using `shapely.box` (@fig-raster-clip-bbox).

#| label: fig-raster-clip-bbox
#| fig-cap: '`shapely` geometry derived from a clipping raster bounding box coordinates, a preliminary step for geometric intersection between two rasters'
bbox = shapely.box(*bbox)
bbox

# @fig-raster-intersection shows the alignment of `bbox` and `elev.tif`.

#| label: fig-raster-intersection
#| fig-cap: The `elev.tif` raster, and the extent of another (smaller) raster `clip` which we use to subset it
fig, ax = plt.subplots()
rasterio.plot.show(src_elev, ax=ax)
gpd.GeoSeries([bbox]).plot(color='none', ax=ax);

# From here on, subsetting can be done using masking and cropping, just like with any vector layer other than `bbox`, regardless whether it is rectangular or not.
# We elaborate on masking and cropping in @sec-raster-cropping (check that section for details about `rasterio.mask.mask`), but, for completeness, here is the code for the last step of masking and cropping:

out_image, out_transform = rasterio.mask.mask(
    src_elev, 
    [bbox], 
    crop=True,
    all_touched=True,
    nodata=0
)

# The resulting subset array `out_image` contains all pixels intersecting with `clip` *pixels* (not necessarily with the centroids!).
# However, due to the `all_touched=True` argument, those pixels which intersect with `clip`, but their centroid does not, retain their original values (e.g., `17`, `23`) rather than turned into "No Data" (e.g., `0`).

out_image

# Therefore, in our case, subset `out_image` dimensions are $2 \times 2$ (@fig-raster-intersection2; also see @fig-raster-intersection).

#| label: fig-raster-intersection2
#| fig-cap: The resulting subset of the `elev.tif` raster
fig, ax = plt.subplots()
rasterio.plot.show(out_image, transform=out_transform, ax=ax)
gpd.GeoSeries([bbox]).plot(color='none', ax=ax);

# ### Extent and origin {#sec-extent-and-origin}
#
# When merging or performing map algebra on rasters, their resolution, projection, origin and/or extent have to match.
# Otherwise, how should we add the values of one raster with a resolution of `0.2` decimal degrees to a second raster with a resolution of `1` decimal degree?
# The same problem arises when we would like to merge satellite imagery from different sensors with different projections and resolutions.
# We can deal with such mismatches by aligning the rasters.
# Typically, raster alignment is done through resampling---that way, it is guaranteed that the rasters match exactly (@sec-raster-resampling).
# However, sometimes it can be useful to modify raster placement and extent "manually", by adding or removing rows and columns, or by modifying the origin, that is, slightly shifting the raster.
# Sometimes, there are reasons other than alignment with a second raster for manually modifying raster extent and placement.
# For example, it may be useful to add extra rows and columns to a raster prior to focal operations, so that it is easier to operate on the edges.
#
# Let's demostrate the first operation, raster padding.
# First, we will read the array with the `elev.tif` values:

r = src_elev.read(1)
r

# To pad an `ndarray`, we can use the `np.pad` function.
# The function accepts an array, and a tuple of the form `((rows_top,rows_bottom),(columns_left, columns_right))`.
# Also, we can specify the value that's being used for padding with `constant_values` (e.g., `18`).
# For example, here we pad `r` with one extra row and two extra columns, on both sides:

rows = 1
cols = 2
s = np.pad(r, ((rows,rows),(cols,cols)), constant_values=18)
s

# <!-- jn: why the object is named 's'? cannot we use a better name here? -->
# However, for `s` to be used in spatial operations, we also have to update its transformation matrix.
# Whenever we add extra columns on the left, or extra rows on top, the raster *origin* changes.
# To reflect this fact, we have to take to "original" origin and add the required multiple of pixel widths or heights (i.e., raster resolution steps).
# The transformation matrix of a raster is accessible from the raster file metadata (@sec-raster-from-scratch) or, as a shortcut, through the `.transform` property of the raster file connection.
# For example, the next code chunk shows the transformation matrix of `elev.tif`.

src_elev.transform 

# From the transformation matrix, we are able to extract the origin.

xmin, ymax = src_elev.transform[2], src_elev.transform[5]
xmin, ymax

# We can also get the resolution of the data, which is the distance between two adjacent pixels.

dx, dy = src_elev.transform[0], src_elev.transform[4]
dx, dy

# These two parts of information are enough to calculate the new origin (`xmin_new,ymax_new`) of the padded raster.

xmin_new = xmin - dx * cols
ymax_new = ymax - dy * rows
xmin_new, ymax_new

# Using the updated origin, we can update the transformation matrix (@sec-raster-from-scratch).
# Keep in mind that the meaning of the last two arguments is `xsize`, `ysize`, so we need to pass the absolute value of `dy` (since it is negative).

new_transform = rasterio.transform.from_origin(
    west=xmin_new, 
    north=ymax_new, 
    xsize=dx, 
    ysize=abs(dy)
)
new_transform

# @fig-raster-shift-origin shows the padded raster, with the outline of the original `elev.tif` (in red), demonstrating that the origin was shifted correctly and the `new_transform` works fine.

#| label: fig-raster-shift-origin
#| fig-cap: The padded `elev.tif` raster, and the extent of the original `elev.tif` raster (in red)
fig, ax = plt.subplots()
rasterio.plot.show(s, transform=new_transform, cmap='Greys', ax=ax)
elev_bbox = gpd.GeoSeries(shapely.box(*src_elev.bounds))
elev_bbox.plot(color='none', edgecolor='red', ax=ax);

# We can shift a raster origin not just when padding, but in any other use case, just by changing its transformation matrix.
# The effect is that the raster is going to be shifted (which is analogous to `.translate` for shifting a vector layer, see @sec-affine-transformations).
# Manually shifting a raster to arbitrary distance is rarely needed in real-life scenarios, but it is useful to know how to do it at least for better understanding the concept of *raster origin*.
# As an example, let's shift the origin of `elev.tif` by `(-0.25,0.25)`.
# First, we need to calculate the new origin.

xmin_new = xmin - 0.25  # shift xmin to the left
ymax_new = ymax + 0.25  # shift ymax upwards
xmin_new, ymax_new

# To shift the origin in other directions we should change the two operators (`-`, `+`) accordingly.
# <!-- jn: the above sentence as a block? -->
#
# Then, same as when padding (see above), we create an updated transformation matrix.

new_transform = rasterio.transform.from_origin(
    west=xmin_new, 
    north=ymax_new, 
    xsize=dx, 
    ysize=abs(dy)
)
new_transform

# @fig-raster-shift-origin2 shows the shifted raster and the outline of the original `elev.tif` raster (in red).

#| label: fig-raster-shift-origin2
#| fig-cap: The padded `elev.tif` raster (@fig-raster-shift-origin) further shifted by `(0.25,0.25)`, and the extent of the original `elev.tif` raster (in red)
fig, ax = plt.subplots()
rasterio.plot.show(r, transform=new_transform, cmap='Greys', ax=ax)
elev_bbox.plot(color='none', edgecolor='red', ax=ax);

# ### Aggregation and disaggregation {#sec-raster-agg-disagg}
#
# Raster datasets vary based on their resolution, from high resolution datasets that enable individual trees to be seen, to low resolution datasets covering large swaths of the Earth.
# Raster datasets can be transformed to either decrease (aggregate) or increase (disaggregate) their resolution, for a number of reasons.
# For example, aggregation can be used to reduce computational resource requirements of raster storage and subsequent steps, while disaggregation can be used to match other datasets, or to add detail.
# As an example, we here change the spatial resolution of `dem.tif` by a factor of `5` (@fig-raster-aggregate).
#
# Raster aggregation is, in fact, a special case of raster resampling (see @sec-raster-resampling), where the target raster grid is aligned with the original raster, only with coarser pixels.
# Conversely, raster resampling is the general case where the new grid is not necessarily an aggregation of the original one, but any other type of grid (such as a rotated and/or shifted one, etc.).
# <!-- jn: the above paragraph as a block? -->
#
# To aggregate a raster using **rasterio**, we go through [two steps](https://rasterio.readthedocs.io/en/stable/topics/resampling.html):
#
# -   Reading the raster values (using `.read`) into an `out_shape` that is different from the original `.shape`
# -   Updating the `transform` according to `out_shape`
#
# Let's demonstrate it, using the `dem.tif` file.
# Note the original shape of the raster; it has `117` rows and `117` columns.

src.read(1).shape

# Also note the transform, which tells us that the raster resolution is about 30.85 $m$.

src.transform

# To aggregate, instead of reading the raster values the usual way, as in `src.read(1)`, we can specify `out_shape` to read the values into a different shape.
# Here, we calculate a new shape which is downscaled by a factor of `5`, i.e., the number of rows and columns is multiplied by `0.2`.
# We must truncate any "partial" rows and columns, e.g., using `int`.
# Each new pixel is now obtained, or "resampled", from $\sim 5 \times 5 = \sim 25$ "old" raster values.
# We can choose the resampling method through the `resampling` parameter.
# Here we use [`rasterio.enums.Resampling.average`](https://rasterio.readthedocs.io/en/stable/api/rasterio.enums.html#rasterio.enums.Resampling), i.e., the new "large" pixel value is the average of all coinciding small pixels, which makes sense for our elevation data in `dem.tif`.

factor = 0.2
r = src.read(1,
    out_shape=(
        int(src.height * factor),
        int(src.width * factor)
        ),
    resampling=rasterio.enums.Resampling.average
)

# As expected, the resulting array `r` has \~5 times smaller dimensions, as shown below.

r.shape

# <!-- jn: maybe it is worth moving this list to the next section and connect them to some explanations? here you can just mention that more options are mentioned in the next section -->
# Other useful options for [`resampling`](https://rasterio.readthedocs.io/en/stable/api/rasterio.enums.html#rasterio.enums.Resampling) include:
#
# -   `rasterio.enums.Resampling.nearest`---Nearest neighbor resampling
# -   `rasterio.enums.Resampling.bilinear`---Bilinear resampling
# -   `rasterio.enums.Resampling.cubic`---Cubic resampling
# -   `rasterio.enums.Resampling.lanczos`---Lanczos windowed resampling
# -   `rasterio.enums.Resampling.mode`---Mode resampling (most common value)
# -   `rasterio.enums.Resampling.min`---Minimum resampling
# -   `rasterio.enums.Resampling.max`---Maximum resampling
# -   `rasterio.enums.Resampling.med`---Median resampling
# -   `rasterio.enums.Resampling.sum`---Median resampling
#
# See below (@sec-raster-resampling) for an explanation of these methods.
#
# What's left to be done is the second step, to update the transform, taking into account the change in raster shape.
# This can be done as follows, using `.transform.scale`.

new_transform = src.transform * src.transform.scale(
    (src.width / r.shape[1]),
    (src.height / r.shape[0])
)
new_transform

# @fig-raster-aggregate shows the original raster and the aggregated one.

#| label: fig-raster-aggregate
#| fig-cap: Aggregating a raster by a factor of 5, using average resampling
#| layout-ncol: 2
#| fig-subcap: 
#| - Original
#| - Aggregated (using average resampling)
rasterio.plot.show(src);
rasterio.plot.show(r, transform=new_transform);

# This is a good opportunity to demonstrate exporting a raster with modified dimensions and transformation matrix.
# We can update the raster metadata required for writing with the `update` method.

dst_kwargs = src.meta.copy()
dst_kwargs.update({
    'transform': new_transform,
    'width': r.shape[1],
    'height': r.shape[0],
})
dst_kwargs

# Then we can create a new file (`dem_agg5.tif`) in writing mode, and write the values from the aggregated array `r` into that file (see @sec-data-output-raster).
# <!-- jn: some explanation is needed here: (a) what are **? (b) what is the meaning of 1 here? -->

dst = rasterio.open('output/dem_agg5.tif', 'w', **dst_kwargs)
dst.write(r, 1)
dst.close()

# The opposite operation, namely disaggregation, is when we increase the resolution of raster objects.
# Either of the supported resampling methods (see above) can be used.
# <!-- jn: update the above sentence after moving the resampling methods list to the next section -->
# However, since we are not actually summarizing information but transferring the value of a large pixel into multiple small pixels, it makes sense to use either:
#
# -   Nearest neighbor resampling (`rasterio.enums.Resampling.nearest`), when want to keep the original values as-is, since modifying them would be incorrect (such as in categorical rasters)
# -   Smoothing techniques, such as bilinear resampling (`rasterio.enums.Resampling.bilinear`), when we would like the smaller pixels to reflect gradual change between the original values, e.g., when the disaggregated raster is used for visualization purposes
#
# To disaggregate a raster, we go through exactly the same workflow as for aggregation, only using a different scaling factor, such as `factor=5` instead of `factor=0.2`, i.e., *increasing* the number of raster pixels instead of decreasing.
# In the example below, we disaggregate using bilinear interpolation, to get a smoothed high-resolution raster.

factor = 5
r2 = src.read(1,
    out_shape=(
        int(src.height * factor),
        int(src.width * factor)
        ),
    resampling=rasterio.enums.Resampling.bilinear
)

# As expected, the dimensions of the disaggregated raster are this time \~5 times *bigger* than the original ones.

r2.shape

# To calculate the new transform, we use the same expression as for aggregation, only with the new `r2` shape.

new_transform2 = src.transform * src.transform.scale(
    (src.width / r2.shape[1]),
    (src.height / r2.shape[0])
)
new_transform2

# The original raster `dem.tif` was already quite detailed, so it would be difficult to see any difference when plotting it along with the disaggregation result.
# A zoom-in of a small section of the rasters works better.
# @fig-raster-disaggregate allows us to see the top-left corner of the original raster and the disaggregated one, demonstrating the increase in the number of pixels through disaggregation.

#| label: fig-raster-disaggregate
#| fig-cap: Disaggregating a raster by a factor of 5, using bilinear tresampling. Only the a small portion (top-left corner) of the rasters is shown, to zoom-in and demonstrate the effect of disaggregation.
#| layout-ncol: 2
#| fig-subcap: 
#| - Original
#| - Disaggregated (using bilinear resampling)
rasterio.plot.show(src.read(1)[:5, :5], transform=src.transform);
rasterio.plot.show(r2[:25, :25], transform=new_transform2);

# Code to export the disaggregated raster would be identical to the one used above for the aggregated raster.
#
# ### Resampling {#sec-raster-resampling}
#
# Raster aggregation and disaggregation (@sec-raster-agg-disagg) are only suitable when we want to change just the resolution of our raster by a fixed factor.
# However, what to do when we have two or more rasters with different resolutions and origins?
# This is the role of resampling---a process of computing values for new pixel locations.
# In short, this process takes the values of our original raster and recalculates new values for a target raster with custom resolution and origin (@fig-raster-resample).
#
# There are several methods for estimating values for a raster with different resolutions/origins (@fig-raster-resample).
# The main resampling methods include:
#
# -   Nearest neighbor: assigns the value of the nearest cell of the original raster to the cell of the target one. This is a fast simple technique that is usually suitable for resampling categorical rasters
# -   Bilinear interpolation: assigns a weighted average of the four nearest cells from the original raster to the cell of the target one. This is the fastest method that is appropriate for continuous rasters
# -   Cubic interpolation: uses values of the 16 nearest cells of the original raster to determine the output cell value, applying third-order polynomial functions. Used for continuous rasters and results in a smoother surface compared to bilinear interpolation, but is computationally more demanding
# -   Cubic spline interpolation: also uses values of the 16 nearest cells of the original raster to determine the output cell value, but applies cubic splines (piecewise third-order polynomial functions). Used for continuous rasters
# -   Lanczos windowed sinc resampling: uses values of the 36 nearest cells of the original raster to determine the output cell value. Used for continuous rasters
# -   Additionally, we can use straightforward summary methods, taking into account all pixels that coincide with the target pixel, such as average (@fig-raster-aggregate), minimum, maximum (@fig-raster-resample), median, mode, and sum
#
# The above explanation highlights that only nearest neighbor resampling is suitable for categorical rasters, while all remaining methods can be used (with different outcomes) for continuous rasters.
#
# <!-- jn: you explain here the "reproject" part of the name; maybe it would be also introduce the "warp" part of the name as well? -->
# With **rasterio**, resampling can be done using the [`rasterio.warp.reproject`](https://rasterio.readthedocs.io/en/stable/api/rasterio.warp.html#rasterio.warp.reproject) function .
# To clarify this naming convention, note that raster *reprojection* is not fundamentally different from *resampling*---the difference is just whether the target grid is in the same CRS as the origin (resampling) or in a different CRS (reprojection).
# In other words, reprojection is *resampling* into a grid that is in a different CRS.
# Accordingly, both resampling and reprojection are done using the same function `rasterio.warp.reproject`.
# We will demonstrate reprojection using `rasterio.warp.reproject` later in @sec-reprojecting-raster-geometries.
#
# The information required for `rasterio.warp.reproject`, whether we are resampling or reprojecting, is:
#
# -   The source and target *CRS*. These may be identical, when resampling, or different, when reprojecting
# -   The source and target *transform*
#
# Importantly, `rasterio.warp.reproject` can work with file connections, such as a connection to an output file in write (`'w'`) mode.
# This makes the function efficient for large rasters.
# <!-- jn: maybe the above sentence could be a block? -->
#
# The target and destination CRS are straightforward to specify, depending on our choice.
# The source transform is also available, e.g., through the `.transform` property of the source file connection.
# The only complicated part is to figure out the *destination transform*.
# When resampling, the transform is typically derived either from a *template* raster, such as an existing raster file that we would like our origin raster to match, or from a numeric specification of our target grid (see below).
# Otherwise, when the exact grid is not of importance, we can simply aggregate or disaggregate our raster as shown above (@sec-raster-agg-disagg).
# (Note that when *reprojecting*, the target transform is not as straightforward to figure out, therefore we further use the `rasterio.warp.calculate_default_transform` function to compute it, as will be shown in @sec-reprojecting-raster-geometries.)
#
# Let's demonstrate resampling into a destination grid which is specified through numeric constraints, such as the extent and resolution.
# These could have been specified manually (such as here), or obtained from a template raster metadata that we would like to match.
# Note that the resolution of the destination grid is \~10 times more coarse (300 $m$) than the original resolution of `dem.tif` (\~30 $m$) (@fig-raster-resample).

xmin = 794650
xmax = 798250
ymin = 8931750 
ymax = 8935350
res = 300

# The corresponding transform based on these constraints can be created using the `rasterio.transform.from_origin` function, as follows:

dst_transform = rasterio.transform.from_origin(
    west=xmin, 
    north=ymax, 
    xsize=res, 
    ysize=res
)
dst_transform

# Again, note that in case we needed to resample into a grid specified by an existing "template" raster, we could skip this step and simply read the transform from the template file, as in `rasterio.open('template.tif').transform`.
#
# Now, we can move on to creating the destination file connection.
# For that, we also have to know the raster dimensions that can be derived from the extent and the resolution.

width = int((xmax - xmin) / res)
height = int((ymax - ymin) / res)
width, height

# Now we can create the destination file connection.
# We are using the same metadata as the source file, except for the dimensions and the transform, which are going to be different and reflecting the resampling process.

dst_kwargs = src.meta.copy()
dst_kwargs.update({
    'transform': dst_transform,
    'width': width,
    'height': height
})
dst = rasterio.open('output/dem_resample_nearest.tif', 'w', **dst_kwargs)

# Finally, we reproject using function `rasterio.warp.reproject`.
# Note that the source and destination are specified using [`rasterio.band`](https://rasterio.readthedocs.io/en/latest/api/rasterio.html#rasterio.band) applied on either the file connection, reflecting the fact that we operate on a specific layer of the rasters.
# The resampling method being used here is nearest neighbor resampling (`rasterio.enums.Resampling.nearest`).

rasterio.warp.reproject(
    source=rasterio.band(src, 1),
    destination=rasterio.band(dst, 1),
    src_transform=src.transform,
    src_crs=src.crs,
    dst_transform=dst_transform,
    dst_crs=src.crs,
    resampling=rasterio.enums.Resampling.nearest
)

# In the end, we close the file and create a new file `output/dem_resample_nearest.tif` with the resampling result (@fig-raster-resample).
# <!-- jn: close the file or the file connection? -->

dst.close()

# Here is another code section just to demonstrate a different resampling method, the maximum resampling, i.e., every new pixel gets the maximum value of all the original pixels it coincides with.
# Note that the transform is identical (@fig-raster-resample), all arguments other than the resampling method are identical.
# <!-- jn: something is wrong with the above sentence... -->

#| eval: false
dst = rasterio.open('output/dem_resample_maximum.tif', 'w', **dst_kwargs)
rasterio.warp.reproject(
    source=rasterio.band(src, 1),
    destination=rasterio.band(dst, 1),
    src_transform=src.transform,
    src_crs=src.crs,
    dst_transform=dst_transform,
    dst_crs=src.crs,
    resampling=rasterio.enums.Resampling.max
)
dst.close()

# The original raster `dem.tif`, and the two resampling results `dem_resample_nearest.tif` and `dem_resample_maximum.tif`, are shown in @fig-raster-resample.

#| label: fig-raster-resample
#| fig-cap: Visual comparison of the original raster and two different resampling methods'
#| layout-ncol: 3
#| fig-subcap: 
#| - Input
#| - Nearest neighbor
#| - Maximum
# Input
fig, ax = plt.subplots(figsize=(4,4))
rasterio.plot.show(src, ax=ax);
# Nearest neighbor
fig, ax = plt.subplots(figsize=(4,4))
rasterio.plot.show(rasterio.open('output/dem_resample_nearest.tif'), ax=ax);
# Maximum
fig, ax = plt.subplots(figsize=(4,4))
rasterio.plot.show(rasterio.open('output/dem_resample_maximum.tif'), ax=ax);

# ## Exercises
#
# ## References

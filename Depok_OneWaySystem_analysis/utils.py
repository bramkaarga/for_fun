import pandas as pd
import geopandas as gpd
import numpy as np
import json
import urllib.request
import sys
import osmnx as ox
from shapely.geometry import Point, Polygon
import gmplot
import matplotlib.pyplot as plt
import seaborn as sns

'''
Retreived from https://github.com/nmonarizqa/weekly-viz/blob/master/jakarta-commute-time/here_drive.py
'''

def get_url(start_point,end_point, app_code, app_id, dep_hour=None,arr_hour=None,mode='car'):
    base='https://route.cit.api.here.com/routing/7.2/calculateroute.json?app_id='+app_id+'&app_code='+app_code
    start='&waypoint0='+str(start_point.y)+","+str(start_point.x)
    end='&waypoint1='+str(end_point.y)+","+str(end_point.x)
    if mode=='car':
        params='&mode=fastest;car;traffic:enabled&maneuverAttributes=sh'
        departure='&departure='+dep_hour
        url = base+start+end+params+departure
    else:
        params='&combineChange=true&mode=fastest;publicTransportTimeTable&maneuverAttributes=sh'
        arrival='&arrival='+arr_hour
        url = base+start+end+params+arrival
    return url

def get_result(data):
    distance = []
    travel_time = []
    shapes = []
    legs = data["response"]["route"][0]["leg"]
    for leg in legs:
        distance.append(leg["length"])
        travel_time.append(leg["travelTime"])
        for sh in leg["maneuver"]:
            shapes += sh["shape"]
    ln=ox.LineString(map(lambda x: (float(x.split(",")[1]),float(x.split(",")[0])), shapes))
    gdf=gpd.GeoDataFrame({'distance':distance,'time':travel_time,'geometry':[ln]})
    return gdf

def get_df(start,end,time,app_code,app_id, mode='car'):
    url = get_url(start,end,dep_hour=time,mode=mode,app_code=app_code,app_id=app_id)
    response=urllib.request.urlopen(url)
    data = json.load(response)
    gdf = get_result(data)
    return gdf

'''
from here on my code

'''

def get_isoline(start_point, dep_hour, app_code, app_id, input_range):
    url = get_url_isoline(start_point=start_point, dep_hour=dep_hour, app_code=app_code, app_id=app_id, 
                          input_range=input_range)
    response = urllib.request.urlopen(url)
    data = json.load(response)
    
    points_raw = data['response']['isoline'][0]['component'][0]['shape']
    points = []
    for point in points_raw:
        point_x = point.split(',')[1]
        point_y = point.split(',')[0]
        points.append(Point(float(point_x), float(point_y)))
    poly = Polygon([[p.x, p.y] for p in points])
    
    return poly

def get_url_isoline(start_point, app_code, app_id, dep_hour=None,arr_hour=None,mode='car',input_range=100):
    base='https://isoline.route.cit.api.here.com/routing/7.2/calculateisoline.json?app_id='+app_id+'&app_code='+app_code
    start='&start='+str(start_point.y)+","+str(start_point.x)
    modes='&rangetype=time'
    if mode=='car':
        params='&mode=fastest;car;traffic:enabled&maneuverAttributes=sh'
        range_='&range='+str(input_range)
        departure='&departure='+dep_hour
        url = base+params+modes+start+range_+departure
    else:
        params='&combineChange=true&mode=fastest;publicTransportTimeTable&maneuverAttributes=sh'
        range_='&range='+str(input_range)
        departure='&departure='+dep_hour
        url = base+params+modes+start+range_+departure
    return url
    
def draw_isoline(center, range_, poly):
    x_s, y_s = poly.exterior.coords.xy
    x_center, y_center = center.y, center.x
    gmap = gmplot.GoogleMapPlotter(x_center, y_center, range_)
    gmap.plot(y_s, x_s, 'cornflowerblue', edge_width=2)
    return gmap

def draw_isoline_compare(center, range_, poly1, poly2):
    x_s1, y_s1 = poly1.exterior.coords.xy
    x_s2, y_s2 = poly2.exterior.coords.xy
    x_center, y_center = center.y, center.x
    gmap = gmplot.GoogleMapPlotter(x_center, y_center, range_)
    gmap.plot(y_s1, x_s1, edge_color='red', edge_width=4, edge_alpha=1, face_color='black', face_alpha=0.5)
    gmap.plot(y_s2, x_s2, edge_color='green', edge_width=2, edge_alpha=1, face_color='black', face_alpha=0.5)
    return gmap
    
def plot_heatmap(df, title=None, cbarlabel='Seconds', fmt='g', cmap='YlGnBu'):
    f, ax = plt.subplots(figsize=(12,12))

    #create heatmap
    sns.heatmap(df, linewidth=.5, ax=ax, annot=True, cmap=cmap, fmt=fmt,
                cbar_kws={"label": cbarlabel}, annot_kws={"size":12})

    #configuring colorbar
    ax.figure.axes[-1].yaxis.label.set_size(22)
    cax = plt.gcf().axes[-1]
    cax.tick_params(labelsize=18)

    #configuring x axis and y axis
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)

    plt.xlabel('To', fontsize=20)
    plt.ylabel('From', fontsize=20)

    #title
    plt.title(title, fontsize=28)
    
    return f, ax
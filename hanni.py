#C:\Users\nataniz\AppData\Roaming\Python\Python311\Scripts\streamlit run C:\Users\nataniz\Desktop\Maasikim\hanni.py
import streamlit as st
import pandas as pd
import datetime
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import warnings
import folium
from itertools import cycle
from Levenshtein import distance
from matplotlib.colors import to_rgb
from shapely.geometry import MultiPolygon
from streamlit_folium import folium_static 
warnings.filterwarnings('ignore')

st.set_page_config(page_title = 'התאמות מעסיקים', layout = 'wide', page_icon = '💼')
st.markdown("""
    <h1 style="direction: rtl; text-align: center; font-size: 64px; font-weight: bold; 
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);  color: rgb(45, 47, 121); font-family: 'Arial', sans-serif;">
        התאמות מעסיקים
    </h1>""", unsafe_allow_html=True)


st.write("""
<div style="display: flex; justify-content: center;">
    <div style="border: 3px solid rgb(45, 47, 121); 
                border-radius: 15px; 
                padding: 15px 25px; 
                display: inline-block; 
                text-align: center; 
                background-color: white;">
        <p style="direction: rtl; 
                  font-weight: bold; 
                  font-size: 26px;
                  color: rgb(45, 47, 121);
                  font-family: 'Arial', sans-serif;
                  margin: 0;">
            מפות אלו מאפשרות לקבל ראייה גלובלית של מצב ההתאמות למעסיקים.
        </p>
    </div>
</div>
""", unsafe_allow_html=True)



yeshuv = pd.read_excel('Cities_Districts.xlsx')
map_mahoz = pd.read_excel('Maasikim_total_hanni.xlsx')
#map_mahoz = harmonize_city_names(map_mahoz, yeshuv, city_col1='CityName', city_col2='CityName')
map_mahoz['Difference'] = map_mahoz.Total_Employer_Number - map_mahoz.Employer_Number_metouam


map_mahoz_final = pd.merge(map_mahoz, yeshuv, on = 'CityName', how = 'inner')
map_mahoz_final = map_mahoz_final.drop_duplicates('CityName')


mahoz = map_mahoz_final.groupby('RegionNameLamas').sum()
mahoz['Percent_mahoz_OfMetouham'] = round((mahoz.Employer_Number_metouam / mahoz.Total_Employer_Number) * 100, 2)
mahoz = mahoz.sort_values(by = 'Percent_mahoz_OfMetouham', ascending = False)

geo = gpd.read_file('Polygons_Districts/ch107xc0728.shp').drop(['id_0', 'iso', 'name_0', 'id_1', 'hasc_1', 'ccn_1', 'cca_1',
       'type_1', 'engtype_1', 'nl_name_1', 'varname_1'], axis = 1)
geo = geo.rename(columns = {'name_1' : 'Mahoz_Name'})

dict_replace = {'HaZafon' : 'הצפון', 
                'Jerusalem' : 'ירושלים', 
                'HaDarom' : 'הדרום', 
                'HaMerkaz' : 'המרכז',
                'Haifa' : 'חיפה',
                'Tel Aviv' : 'תל אביב'}
geo.Mahoz_Name = geo.Mahoz_Name.replace(dict_replace)


mahoz_reset = mahoz.reset_index()
merged_data = mahoz_reset.merge(geo, left_on='RegionNameLamas', right_on='Mahoz_Name', how = 'inner')
merged_data = merged_data.drop(['Total_Employer_Number', 'Employer_Number_metouam', 'Mahoz_Name'], axis = 1)
geo = merged_data.copy()



# Création d'un GeoDataFrame à partir de 'geo'
geo_gdf = gpd.GeoDataFrame(geo, geometry='geometry')
#geo_gdf.crs

# Palette de couleurs spécifiée
colors = [
    (0/255, 117/255, 160/255), (108/255, 144/255, 161/255),
    (45/255, 47/255, 121/255), (235/255, 136/255, 17/255),
    (196/255, 206/255, 34/255)
]
color_cycle = cycle(colors)  # Pour réutiliser les couleurs si nécessaire

# Assignation de couleurs uniques pour chaque district
district_colors = {district: next(color_cycle) for district in geo_gdf['RegionNameLamas'].unique()}

# Création de la carte avec un niveau de zoom et une position ajustés
carte_markers = folium.Map(location=[32, 34.75], zoom_start=7.5, control_scale=True, tiles='CartoDB positron')

# Ajout des polygones et des marqueurs
for idx, row in geo_gdf.iterrows():
    district_name = row['RegionNameLamas']
    district_color = district_colors[district_name]
    color_rgb = f"rgb({int(district_color[0]*255)}, {int(district_color[1]*255)}, {int(district_color[2]*255)})"

    # Création du polygone
    folium.GeoJson(
        row['geometry'].__geo_interface__,
        style_function=lambda x, c=color_rgb: {'fillColor': c, 'color': 'black', 'weight': 0.5, 'fillOpacity': 0.7}
    ).add_to(carte_markers)

    # Ajout d'un marqueur avec le pourcentage de travailleurs
    percentage = row['Percent_mahoz_OfMetouham']  # Récupération du pourcentage de travailleurs

    # Ajustement de la position des marqueurs
    lat, lon = row['geometry'].centroid.y, row['geometry'].centroid.x
    if district_name == "תל אביב":
        lat -= 0.01  # Déplacement vers le bas
        lon -= 0.08  # Déplacement vers la gauche
    elif district_name == "המרכז":
        lat += 0.1  # Déplacement vers le haut
        lon += 0.02  # Déplacement vers la droite
        
    elif district_name == "חיפה":
        lat -= 0.01
        lon -= 0.1  # Déplacement vers la gauche

    folium.Marker(
        [lat, lon],
        icon=folium.DivIcon(
            html=f'<div style="width: 50px; font-size: 12px; color: black; background-color: whitesmoke; padding: 3px; border: 3px solid {color_rgb}; border-radius: 5px;">{percentage}%</div>'
        )
    ).add_to(carte_markers)

# Création de la légende avec une meilleure mise en forme
legend_html = """
<div style='position: fixed; 
     bottom: 50px; left: 20px; 
     width: 150px; height: auto; 
     border:2px solid #8F8F8F; 
     z-index:9999; 
     font-size:14px; 
     background-color: rgba(255, 255, 255, 0.8); 
     padding:5px; 
     border-radius: 5px;
     box-shadow: 0 0 15px rgba(0, 0, 0, 0.2);'>
     <b>מחוז</b><br>
"""

for district, color in district_colors.items():
    color_rgb = f"rgb({int(color[0]*255)}, {int(color[1]*255)}, {int(color[2]*255)})"
    legend_html += f"<div style='margin: 2px 0;'><span style='height: 10px; width: 10px; background-color: {color_rgb}; display: inline-block;'></span>&nbsp; {district}</div>"

legend_html += "</div>"
carte_markers.get_root().html.add_child(folium.Element(legend_html))

# st.markdown("Carte interactive:")
# folium_static(carte_markers)





# Cities----------------------------------------------------------------------------------------------------------------------------
# add percentage of maasikim hatamot for each city
yeshuv_percent = map_mahoz_final.copy()
yeshuv_percent['Percent_cities'] = round((yeshuv_percent.Employer_Number_metouam / yeshuv_percent.Total_Employer_Number) * 100, 2)


# import shp polygon cities
shp_file = 'Polygons/statistical_areas_2022.shp'
data = gpd.read_file(shp_file)
data = data[['SHEM_YISHU', 'YISHUV_STA','SHAPE_Leng', 'SHAPE_Area', 'geometry']]
data = data.rename(columns = {'YISHUV_STA' : 'CityID_Area'})
#data = harmonize_city_names(data, yeshuv, city_col1='SHEM_YISHU', city_col2='CityName')

# Regroupement des données par nom de ville et fusion des polygones
data_grouped = data.dissolve(by='SHEM_YISHU', as_index=False)

fusion = pd.merge(yeshuv_percent, data_grouped, left_on= 'CityName', right_on= 'SHEM_YISHU', how = 'inner')
fusion = fusion.drop(['Total_Employer_Number', 'Employer_Number_metouam', 'Difference', 'SHEM_YISHU', 'CityID_Area'], axis = 1)

# Création d'un GeoDataFrame à partir de 'fusion'
fusion = gpd.GeoDataFrame(fusion, geometry='geometry')
#fusion.crs


# Définition des palettes de couleurs pour chaque région
region_color_palettes = {
    'תל אביב': ['#3498db', '#85c1e9', '#2980b9'],  # Nuances de bleu
    'ירושלים': ['#e74c3c', '#f1948a', '#c0392b'],  # Nuances de rouge
    'חיפה': ['#2ecc71', '#58d68d', '#27ae60'],      # Nuances de vert
    'המרכז': ['#f39c12', '#f8c471', '#d35400'],    # Nuances d'orange
    'הדרום': ['#9b59b6', '#c39bd3', '#8e44ad'],     # Nuances de violet
    'הצפון': ['#5dade2', '#aed6f1', '#2e86c1'],    # Nuances de bleu clair
    'יהודה והשומרון': ['#f4d03f', '#f9e79f', '#d4ac0d']  # Nuances de jaune
}

region_color_cycles = {region: cycle(palettes) for region, palettes in region_color_palettes.items()}
city_colors_by_region = {}
for idx, row in fusion.iterrows():
    region = row['RegionNameLamas']
    if region not in city_colors_by_region:
        city_colors_by_region[region] = {}
    city_name = row['CityName']
    city_colors_by_region[region][city_name] = next(region_color_cycles[region])

# Création de la carte
carte_villes_par_region = folium.Map(location=[32, 34.75], zoom_start=8.2, control_scale=True, tiles='CartoDB positron')

# Ajout des polygones avec popups pour chaque ville
for idx, row in fusion.iterrows():
    city_name = row['CityName']
    region_name = row['RegionNameLamas']
    city_color = city_colors_by_region[region_name][city_name]
    color_rgb = f"rgb({int(to_rgb(city_color)[0]*255)}, {int(to_rgb(city_color)[1]*255)}, {int(to_rgb(city_color)[2]*255)})"

    # Création du HTML pour le popup
    popup_html = f"<div style='font-size: 12px; color: black; background-color: {city_color}; padding: 3px; border-radius: 5px;'><b>{city_name}</b><br>{row['Percent_cities']}%</div>"
    popup_content = folium.Popup(folium.Html(popup_html, script=True), max_width=300)

    # Création du polygone avec le popup
    folium.GeoJson(
        row['geometry'].__geo_interface__,
        style_function=lambda x, c=color_rgb: {'fillColor': c, 'color': 'black', 'weight': 0.5, 'fillOpacity': 0.7}
    ).add_child(popup_content).add_to(carte_villes_par_region)

# st.markdown("Carte interactive:")
# folium_static(carte_villes_par_region)


col1, col2 = st.columns(2)

# Ajoutez du contenu à la première colonne
with col1:
    st.markdown("""
    <div style="direction: rtl; text-align: center; background-color: rgb(235, 136, 17); padding: 10px; 
    border-radius: 5px; color: white; font-weight: bold; font-size: 28px; margin-top: 20px; margin-bottom: 30px ; font-family: 'Arial', sans-serif;">
        אחוזי התאמות מעסיקים לפי מחוז
    </div>
    """, unsafe_allow_html=True)
    carte_markers._parent.selector = '#map1'
    folium_static(carte_markers, width=870, height=600)


# Ajoutez du contenu à la deuxième colonne
with col2:
    st.markdown("""
    <div style="direction: rtl; text-align: center; background-color: rgb(235, 136, 17); padding: 10px; 
    border-radius: 5px; color: white; font-weight: bold; font-size: 28px; margin-top: 20px ; margin-bottom: 30px; font-family: 'Arial', sans-serif;">
        אחוזי התאמות מעסיקים לפי ישוב
    </div>
    """, unsafe_allow_html=True)
    carte_villes_par_region._parent.selector = '#map2'
    folium_static(carte_villes_par_region, width=870, height=600)



#Barre de progression---------------------------------------------------------------------------------------------------------------
def create_gradient_progress_bar(label, progress, start_color, end_color):
    return f"""
    <div style="display: flex; align-items: center; margin-bottom: 20px; font-family: Arial;">
        <div style="width: 120px; font-size: 20px; color: rgb(45, 47, 121); text-shadow: 1px 1px 2px grey;"><strong>{label}</strong></div>
        <div style="flex-grow: 1; margin-left: 20px; height: 25px; border-radius: 12px; background: linear-gradient(to right, {start_color}, {end_color});">
            <div style="height: 100%; width: {progress}%; background-color: rgba(255, 255, 255, 0.5); border-radius: 12px; display: flex; align-items: center; justify-content: flex-end; padding-right: 10px; box-shadow: 0 3px 6px rgba(0, 0, 0, 0.16);">
                <span style="color: white; font-weight: bold;">{progress}%</span>
            </div>
        </div>
    </div>
    """


yaad = round((mahoz.Employer_Number_metouam.sum() / mahoz.Total_Employer_Number.sum()) * 100,2)
devoirs = [("יעד מעסיקים", yaad)]
start_color = "#2d2f79"  # Bleu foncé (R=45 G=47 B=121)
end_color = "#6c90a1"    # Bleu clair (R=108 G=144 B=161)
for label, progress in devoirs:
    st.markdown(create_gradient_progress_bar(label, progress, start_color, end_color), unsafe_allow_html=True)
    
# Ajoutez une ligne de séparation entre les colonnes
st.write('<hr style="border-top: 4px solid  rgb(235, 136, 17);">', unsafe_allow_html=True)



# Largest, Smallest cities---------------------------------------------------------------------------------------------------------------
def create_data_card(city, percent, start_color, end_color):
    return f"""
    <div style="margin: 5px auto; padding: 10px; border-radius: 10px; background: linear-gradient(to right, {start_color}, {end_color}); box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.2); width: 250px; text-align: center;">
        <h3 style="font-family: Arial, sans-serif; color: white; font-size: 18px;">{city}</h3>
        <div style="font-family: Arial, sans-serif; color: white; font-size: 22px;">
            <strong>{percent}%</strong>
        </div>
    </div>
    """

# Exemple de couleurs que vous avez fournies
start_color_largest = "#76b852"  # Vert
end_color_largest = "#6dd5ed"    # Bleu

start_color_smallest = "#ff9a8b"  # Orange
end_color_smallest = "#ff7f0e"    # Orange plus foncé

shadow_color_largest = "rgba(118, 184, 82, 0.75)"  # Ombre verte plus foncée
shadow_color_smallest = "rgba(255, 154, 139, 0.75)" # Ombre orange plus foncée

# Modification des styles de titre pour inclure une ombre plus prononcée
title_style_largest = f"color: #fff; text-shadow: 4px 4px 8px {shadow_color_largest}; text-align: center; font-size: 42px;"
title_style_smallest = f"color: #fff; text-shadow: 4px 4px 8px {shadow_color_smallest}; text-align: center; font-size: 42px;"
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"<h2 style='{title_style_largest}'>ההתאמות הגבוהות</h2>", unsafe_allow_html=True)

with col2:
    st.markdown(f"<h2 style='{title_style_smallest}'>ההתאמות הנמוכות</h2>", unsafe_allow_html=True)


# Affichage du top 3 des villes avec le meilleur pourcentage
with col1:
    indices_largest = fusion['Percent_cities'].nlargest(3).index
    top_cities_largest = fusion.loc[indices_largest]
    for city, row in top_cities_largest.iterrows():
        st.markdown(create_data_card(row['CityName'], row['Percent_cities'], start_color_largest, end_color_largest), unsafe_allow_html=True)

# Affichage du top 3 des villes avec le plus faible pourcentage
with col2:
    indices_smallest = fusion['Percent_cities'].nsmallest(3).index
    top_cities_smallest = fusion.loc[indices_smallest]
    for city, row in top_cities_smallest.iterrows():
        st.markdown(create_data_card(row['CityName'], row['Percent_cities'], start_color_smallest, end_color_smallest), unsafe_allow_html=True)


    










































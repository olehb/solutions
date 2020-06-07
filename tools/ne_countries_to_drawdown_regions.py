import sys
import os
import admin_names
import geopandas

help_message = """
Usage:
python shapefile_to_geojson.py /path/to/shapefile.zip [/path/to/output.json]
    produces GeoJSON file from shapefile ZIP. If output path is not provided,
    it will use name of .zip file to create JSON output file in the python working dir.
"""

SPECIAL_COUNTRIES = [
    'China',
    'India',
    'EU',
    'United States of America'
]


def map_ne_admin_to_drawdown_region(row):
    ne_name = row['ADMIN']
    dd_name = admin_names.lookup(ne_name)

    if dd_name in SPECIAL_COUNTRIES:
        return dd_name
    else:
        dd_region = admin_names.region_mapping.get(dd_name)
        if dd_region is None:
            return None
        elif isinstance(dd_region, list):
            # TODO: What to do if length of the list is more than 1?
            return dd_region[0]
        else:
            # This should never happen, since it seems like all values in region_mapping are lists
            return dd_region


def map_ne_admin_counties_to_drawdown_regions(shapefile_zip_path):
    esri = geopandas.read_file(f"zip://{shapefile_zip_path}")
    esri['DRAWDOWN_REGION'] = esri.apply(lambda row: map_ne_admin_to_drawdown_region(row), axis=1)
    all_rows_region_only = esri[['DRAWDOWN_REGION', 'geometry']].dropna()
    region_only = all_rows_region_only.dissolve('DRAWDOWN_REGION')
    return region_only


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(help_message)

    shapefile_zip_path = sys.argv[1]
    if not os.path.exists(shapefile_zip_path):
        print(f"File not found: {shapefile_zip_path}")
        sys.exit(1)
    else:
        if len(sys.argv) == 3:
            output_json_path = sys.argv[2]
        else:
            shapefile_zip_name = shapefile_zip_path.rsplit("/", 1)[1]
            shapefile_base_name = shapefile_zip_name.rsplit(".", 1)[0]
            output_json_path = f"./{shapefile_base_name}.json"

        region_only = map_ne_admin_counties_to_drawdown_regions(shapefile_zip_path)

        region_only.to_file(output_json_path, driver='GeoJSON')

        print(f"TopoJSON saved to {output_json_path}")

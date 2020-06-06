import sys
import os
import admin_names
import geopandas
import topojson

help_message = """
"""

SPECIAL_COUNTRIES = [
    'China',
    'India',
    'EU',
    'USA'
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
            return dd_region[0]
        else:
            return dd_region


def convert_ne_shapefile_to_drawdown_topojson(shapefile_zip_path):
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

        region_only = convert_ne_shapefile_to_drawdown_topojson(shapefile_zip_path)
        tj = topojson.Topology(region_only,
                               prequantize=True,
                               topology=True,
                               presimplify=True,
                               toposimplify=True,
                               prevent_oversimplify=True)

        with open(output_json_path, "w") as f:
            f.write(tj.to_json())

        print(f"TopoJSON saved to {output_json_path}")


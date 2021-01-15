import argparse
import json

from osgeo import ogr

########################################################################################
parser = argparse.ArgumentParser(description="Process some integers.")
parser.add_argument(
    "-i",
    "--input_file",
    required=False,
    default=None,
    type=str,
    help="the input file containning the geometries as geojson",
)
parser.add_argument(
    "-g",
    "--group_size",
    required=False,
    default=50,
    type=int,
    help="the size of each group",
)
########################################################################################


def group_input_geometries(input_geometries_file, group_size):
    """
    The function to create groups of input geometries using the given size (number of
    features) per group

    Parameters
    ----------
    input_geometries_file : str
        the path to the GeoJSON file containing the input geometries
    group_size : int
        the maximum number of features per group

    Returns
    -------
    groups : dict
        the dictionary containing a list of "feature_ids" and a list of
        "feature_geometries" per group with given group id key
    """

    driver = ogr.GetDriverByName("GeoJSON")
    datasource = driver.Open(input_geometries_file, 0)
    layer = datasource.GetLayer()

    groups = {}

    # we will simply, we will start with min group id = 100
    group_id = 100
    group_id_string = f"g{group_id}"
    feature_count = 0
    for feature in layer:
        feature_count += 1
        # feature count starts at 1
        # assuming group size would be 10
        # when feature_count = 11 then we enter the next group
        if feature_count % (group_size + 1) == 0:
            group_id += 1
            group_id_string = f"g{group_id}"

        try:
            groups[group_id_string]
        except KeyError:
            groups[group_id_string] = {
                "feature_ids": [],
                "feature_geometries": [],
                "center_points": [],
                "reference": [],
                "screen": [],
            }

        # we use a new id here based on the count
        # since we are not sure that GetFID returns unique values
        groups[group_id_string]["feature_ids"].append(feature_count)
        groups[group_id_string]["feature_geometries"].append(
            json.loads(feature.GetGeometryRef().ExportToJson())
        )

        # from gdal documentation GetFieldAsDouble():
        # OFTInteger fields will be cast to double.
        # Other field types, or errors will result in a return value of zero.
        center_x = feature.GetFieldAsDouble("center_x")
        center_y = feature.GetFieldAsDouble("center_y")

        # check if center attribute has been provided in geojson
        # normal tasks will never have a center of 0.0, 0.0
        # this is just in the middle of the ocean
        if (center_x == 0.0) and (center_y == 0.0):
            groups[group_id_string]["center_points"].append(None)
        else:
            groups[group_id_string]["center_points"].append([center_x, center_y])

        # this is relevant for the tutorial
        reference = feature.GetFieldAsDouble("reference")
        screen = feature.GetFieldAsDouble("screen")
        groups[group_id_string]["reference"].append(reference)
        groups[group_id_string]["screen"].append(screen)

    return groups


########################################################################################
if __name__ == "__main__":

    args = parser.parse_args()

    groups = group_input_geometries(args.input_file, args.group_size)

    print(groups)

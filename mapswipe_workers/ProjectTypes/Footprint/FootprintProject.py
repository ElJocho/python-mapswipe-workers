import os
import logging
import ogr
import urllib.request
from typing import Union

from mapswipe_workers.basic import auth
from mapswipe_workers.basic.BaseProject import BaseProject
from mapswipe_workers.ProjectTypes.Footprint.FootprintGroup import FootprintGroup
from mapswipe_workers.ProjectTypes.Footprint import GroupingFunctions as g


########################################################################################################################
# A Footprint Project
class FootprintProject(BaseProject):
    """
    The subclass for a project of the type Footprint
    """

    project_type = 2

    ####################################################################################################################
    # INIT - Existing projects from id, new projects from import_key and import_dict                                   #
    ####################################################################################################################
    def __init__(self, project_id, firebase, postgres, import_key=None, import_dict=None):
        """
        The function to init a project

        Parameters
        ----------
        project_id : int
            The id of the project
        firebase : pyrebase firebase object
            initialized firebase app with admin authentication
        postgres : database connection class
            The database connection to postgres database
        import_key : str, optional
            The key of this import from firebase imports tabel
        import_dict : dict, optional
            The project information to be imported as a dictionary
        """

        super().__init__(project_id, firebase, postgres, import_key, import_dict)

        if not hasattr(self, 'contributors'):
            # we check if the super().__init__ was able to set the contributors attribute (was successful)
            return None

        elif hasattr(self, 'is_new'):
            # this is a new project, which have not been imported

            self.info = {}
            self.info['tileserver'] = import_dict['tileServer']

            try:
                self.info["tileserver_url"] = import_dict['tileserverUrl']
            except:
                self.info["tileserver_url"] = auth.get_tileserver_url(self.info['tileserver'])

            try:
                self.info["layer_name"] = import_dict['wmtsLayerName']
            except:
                self.info["layer_name"] = None

            try:
                self.info['api_key'] = import_dict['apiKey']
            except:
                try:
                    self.info['api_key'] = auth.get_api_key(self.info['tileserver'])
                except:
                    self.info['api_key'] = None

            # ToDO get groups size from import dict
            self.info["group_size"] = 50

            # we need to download the footprint geometries and store locally
            # make sure that we get a direct download link, make sure data is in geojson format

            url = import_dict['inputGeometries']
            file_name = 'data/input_geometries_{}.geojson'.format(self.id)
            urllib.request.urlretrieve(url, file_name)

            # we need to check if the footprint geometries are valid and remove invalid geometries
            valid_geometries_file = self.check_input_geometries(input_geometries_file=file_name)

            # if the check fails we need to delete the local file and stop the init

            # we need to set the "input geometries file" attribute
            self.info["input_geometries_file"] = valid_geometries_file

            del self.is_new
            logging.warning('%s - __init__ - init complete' % self.id)

    def check_input_geometries(self, input_geometries_file: str) -> Union[str, bool]:
        """
        The function to validate the input geometry

        Parameters
        ----------
        input_geometries_file: str
            String pointing to a geojson containing the geometries to validate

        Returns
        -------
        err : str or True
            A text based description why the check failed, or True if all tests passed
        """

        driver = ogr.GetDriverByName('GeoJSON')
        datasource = driver.Open(input_geometries_file, 0)
        layer = datasource.GetLayer()

        # Create the output Layer
        outfile = "data/valid_geometries_{}.geojson".format(self.id)
        outDriver = ogr.GetDriverByName("GeoJSON")

        # Remove output shapefile if it already exists
        if os.path.exists(outfile):
            outDriver.DeleteDataSource(outfile)

        # Create the output shapefile
        outDataSource = outDriver.CreateDataSource(outfile)
        outLayer = outDataSource.CreateLayer("geometries", geom_type=ogr.wkbMultiPolygon)

        # Add input Layer Fields to the output Layer
        inLayerDefn = layer.GetLayerDefn()
        for i in range(0, inLayerDefn.GetFieldCount()):
            fieldDefn = inLayerDefn.GetFieldDefn(i)
            outLayer.CreateField(fieldDefn)

        # Get the output Layer's Feature Definition
        outLayerDefn = outLayer.GetLayerDefn()

        # check if layer is empty
        if layer.GetFeatureCount() < 1:
            err = 'empty file. No geometries provided'
            logging.warning("%s - check_input_geometry - %s" % (self.id, err))
            return False

        # check if the input geometry is a valid polygon
        for feature in layer:
            feat_geom = feature.GetGeometryRef()
            geom_name = feat_geom.GetGeometryName()
            if not feat_geom.IsValid():
                layer.DeleteFeature(feature.GetFID())
                logging.warning("%s - check_input_geometries - deleted invalid feature %s" % (self.id, feature.GetFID()))
                # removed geometry from layer

            # we accept only POLYGON or MULTIPOLYGON geometries
            elif geom_name != 'POLYGON' and geom_name != 'MULTIPOLYGON':
                layer.DeleteFeature(feature.GetFID())
                logging.warning("%s - check_input_geometries - deleted non polygon feature %s" % (self.id, feature.GetFID()))
                # removed geometry from layer

            else:
                # Create output Feature
                outFeature = ogr.Feature(outLayerDefn)
                # Add field values from input Layer
                for i in range(0, outLayerDefn.GetFieldCount()):
                    outFeature.SetField(outLayerDefn.GetFieldDefn(i).GetNameRef(), feature.GetField(i))
                outFeature.SetGeometry(feat_geom)
                outLayer.CreateFeature(outFeature)
                outFeature = None

        # check if layer is empty
        if layer.GetFeatureCount() < 1:
            err = 'no geometries left after checking validity and geometry type.'
            logging.warning("%s - check_input_geometry - %s" % (self.id, err))
            return False

        del datasource
        del outDataSource
        del layer

        logging.warning('%s - check_input_geometry - filtered correct input geometries' % self.id)
        return outfile

    ####################################################################################################################
    # IMPORT - We define a bunch of functions related to importing new projects                                        #
    ####################################################################################################################

    def create_groups(self) -> dict:
        """
        The function to create groups of footprint geometries

        Returns
        -------
        groups : dict
            The group information containing task information
        """

        raw_groups = g.group_input_geometries(self.info["input_geometries_file"], self.info["group_size"])

        groups = {}
        for group_id, item in raw_groups.items():
            group = FootprintGroup(self, group_id, item['feature_ids'], item['feature_geometries'])
            groups[group.id] = group.to_dict()

        logging.warning("%s - create_groups - created groups dictionary" % self.id)
        return groups

    ####################################################################################################################
    # EXPORT - We define a bunch of functions related to exporting exiting projects                                    #
    ####################################################################################################################

    def aggregate_results(self, postgres: object) -> dict:
        """
        The Function to aggregate results per task.

        Parameters
        ----------
        postgres : database connection class
            The database connection to postgres database

        Returns
        -------
        results_dict : dict
            result of the aggregation as dictionary. Key for every object is task id. Properties are decision,
            yes_count, maybe_count, bad_imagery_count

        """
        p_con = postgres()
        # sql command
        sql_query = '''
                    select
                      task_id as id
                      ,project_id as project
                      ,avg(cast(info ->> 'result' as integer))as decision
                      ,SUM(CASE
                        WHEN cast(info ->> 'result' as integer) = 1 THEN 1
                        ELSE 0
                       END) AS yes_count
                       ,SUM(CASE
                        WHEN cast(info ->> 'result' as integer) = 2 THEN 1
                        ELSE 0
                       END) AS maybe_count
                       ,SUM(CASE
                        WHEN cast(info ->> 'result' as integer) = 3 THEN 1
                        ELSE 0
                       END) AS bad_imagery_count
                    from
                      results
                    where
                      project_id = %s and cast(info ->> 'result' as integer) > 0
                    group by
                      task_id
                      ,project_id'''

        header = ['id', 'project_id', 'decision', 'yes_count', 'maybe_count', 'bad_imagery_count']
        data = [self.id]

        project_results = p_con.retr_query(sql_query, data)
        # delete/close db connection
        del p_con

        results_dict = {}
        for row in project_results:
            row_id = ''
            row_dict = {}
            for i in range(0, len(header)):
                # check for task id
                if header[i] == 'id':
                    row_id = str(row[i])
                elif header[i] == 'decision':  # check for float value
                    row_dict[header[i]] = float(str(row[i]))
                # check for integer value
                elif header[i] in ['yes_count', 'maybe_count', 'bad_imagery_count']:
                    row_dict[header[i]] = int(str(row[i]))
                # all other values will be handled as strings
                else:
                    row_dict[header[i]] = row[i]
            results_dict[row_id] = row_dict

        logging.warning('got results information from postgres for project: %s. rows = %s' % (self.id,
                                                                                              len(project_results)))
        return results_dict



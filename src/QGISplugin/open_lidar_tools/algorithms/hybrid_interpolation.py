# -*- coding: utf-8 -*-

"""
/***************************************************************************
 OpenLidarTools
                                 A QGIS QGISplugin
 Open LiDAR Toolbox
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-03-10
        copyright            : (C) 2021 by Benjamin Štular, Edisa Lozić, Stefan Eichert
        email                : stefaneichert@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 3 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Benjamin Štular, Edisa Lozić, Stefan Eichert'
__date__ = '2021-03-10'
__copyright__ = '(C) 2021 by Benjamin Štular, Edisa Lozić, Stefan Eichert'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

"""
Model exported as python.
Name : Hybrid Interpolation
Group : Analysis
With QGIS : 31604
"""

from qgis.core import QgsProcessing
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingUtils
from qgis.core import QgsProcessingParameterCrs
from qgis.core import QgsProcessingParameterBoolean
from qgis.core import QgsProcessingParameterString
import processing
import os
import inspect


class HybridInterpolation(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer('ConfidenceMapRaster', 'DFM Confidence Map', defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterLayer('IDW', 'IDW Interpolation', defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterLayer('TLI', 'TLI (TIN) Interpolation', defaultValue=None))
        self.addParameter(QgsProcessingParameterCrs('CRS', 'Source Files Coordinate System', defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('CellSize', 'Cell Size', type=QgsProcessingParameterNumber.Double, minValue=0.1, defaultValue=0.5))
        self.addParameter(QgsProcessingParameterNumber('REDgrowradiusinrastercells', 'Grow Radius (Cells)', type=QgsProcessingParameterNumber.Integer, minValue=0, maxValue=9999, defaultValue=3))
        self.addParameter(QgsProcessingParameterString('prefix', 'Name prefix for layers', multiLine=False,
                                                       defaultValue='', optional=True))
        self.addParameter(QgsProcessingParameterBoolean('loadDFM', 'Add DFM to MAP', optional=False, defaultValue=True))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(23, model_feedback)
        results = {}
        outputs = {}

        # r.resample CFM
        alg_params = {
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': parameters['CellSize'],
            'GRASS_REGION_PARAMETER': parameters['ConfidenceMapRaster'],
            'input': parameters['ConfidenceMapRaster'],
            'output': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RresampleCfm'] = processing.run('grass7:r.resample', alg_params, context=context, feedback=feedback,
                                                 is_child_algorithm=True)

        feedback.setCurrentStep(1)
        iter = 1
        if feedback.isCanceled():
            return {}
        iter = iter + 1

        # r.resample TLI
        alg_params = {
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': parameters['CellSize'],
            'GRASS_REGION_PARAMETER': parameters['ConfidenceMapRaster'],
            'input': parameters['TLI'],
            'output': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RresampleTli'] = processing.run('grass7:r.resample', alg_params, context=context, feedback=feedback,
                                                 is_child_algorithm=True)

        feedback.setCurrentStep(iter)
        if feedback.isCanceled():
            return {}
        iter = iter + 1

        # RedTmp classify
        alg_params = {
            'DATA_TYPE': 3,
            'INPUT_RASTER': outputs['RresampleCfm']['output'],
            'NODATA_FOR_MISSING': False,
            'NO_DATA': -9999,
            'RANGE_BOUNDARIES': 0,
            'RASTER_BAND': 1,
            'TABLE': [-0.001, 3, 1, 3, 6, 0],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RedtmpClassify'] = processing.run('native:reclassifybytable', alg_params, context=context,
                                                   feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(iter)
        if feedback.isCanceled():
            return {}
        iter = iter + 1

        # r.resample IDW
        alg_params = {
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': parameters['CellSize'],
            'GRASS_REGION_PARAMETER': parameters['ConfidenceMapRaster'],
            'input': parameters['IDW'],
            'output': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RresampleIdw'] = processing.run('grass7:r.resample', alg_params, context=context, feedback=feedback,
                                                 is_child_algorithm=True)

        feedback.setCurrentStep(iter)
        if feedback.isCanceled():
            return {}
        iter = iter + 1

        # tmpRed Neighbours
        alg_params = {
            '-a': False,
            '-c': False,
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'gauss': None,
            'input': outputs['RedtmpClassify']['OUTPUT'],
            'method': 1,
            'quantile': '',
            'selection': None,
            'size': 11,
            'weight': '',
            'output': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['TmpredNeighbours'] = processing.run('grass7:r.neighbors', alg_params, context=context,
                                                     feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(iter)
        if feedback.isCanceled():
            return {}
        iter = iter + 1

        # allToOne
        alg_params = {
            'DATA_TYPE': 5,
            'INPUT_RASTER': outputs['RresampleIdw']['output'],
            'NODATA_FOR_MISSING': False,
            'NO_DATA': -9999,
            'RANGE_BOUNDARIES': 0,
            'RASTER_BAND': 1,
            'TABLE': [-9998, 9999999999, 1],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Alltoone'] = processing.run('native:reclassifybytable', alg_params, context=context, feedback=feedback,
                                             is_child_algorithm=True)

        feedback.setCurrentStep(iter)
        if feedback.isCanceled():
            return {}
        iter = iter + 1

        # Reclassify redtmpOneNodata
        alg_params = {
            'DATA_TYPE': 3,
            'INPUT_RASTER': outputs['TmpredNeighbours']['output'],
            'NODATA_FOR_MISSING': True,
            'NO_DATA': -9999,
            'RANGE_BOUNDARIES': 2,
            'RASTER_BAND': 1,
            'TABLE': [1, 1, 1],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReclassifyRedtmponenodata'] = processing.run('native:reclassifybytable', alg_params, context=context,
                                                              feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(iter)
        if feedback.isCanceled():
            return {}
        iter = iter + 1

        # Translate 1
        alg_params = {
            'COPY_SUBDATASETS': False,
            'DATA_TYPE': 5,
            'EXTRA': '',
            'INPUT': outputs['Alltoone']['OUTPUT'],
            'NODATA': 0,
            'OPTIONS': '',
            'TARGET_CRS': None,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Translate1'] = processing.run('gdal:translate', alg_params, context=context, feedback=feedback,
                                               is_child_algorithm=True)

        feedback.setCurrentStep(iter)
        if feedback.isCanceled():
            return {}
        iter = iter + 1

        # r.grow 2 cells tmpred
        alg_params = {
            '-m': False,
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'input': outputs['ReclassifyRedtmponenodata']['OUTPUT'],
            'metric': 0,
            'new': 1,
            'old': 1,
            'radius': parameters['REDgrowradiusinrastercells'],
            'output': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Rgrow2CellsTmpred'] = processing.run('grass7:r.grow', alg_params, context=context, feedback=feedback,
                                                      is_child_algorithm=True)

        feedback.setCurrentStep(iter)
        if feedback.isCanceled():
            return {}
        iter = iter + 1

        # Translate redGrow
        alg_params = {
            'COPY_SUBDATASETS': False,
            'DATA_TYPE': 0,
            'EXTRA': '',
            'INPUT': outputs['Rgrow2CellsTmpred']['output'],
            'NODATA': 0,
            'OPTIONS': '',
            'TARGET_CRS': None,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['TranslateRedgrow'] = processing.run('gdal:translate', alg_params, context=context, feedback=feedback,
                                                     is_child_algorithm=True)

        feedback.setCurrentStep(iter)
        if feedback.isCanceled():
            return {}
        iter = iter + 1

        # Reclassify nodata to zero red
        alg_params = {
            'DATA_TYPE': 3,
            'INPUT_RASTER': outputs['TranslateRedgrow']['OUTPUT'],
            'NODATA_FOR_MISSING': False,
            'NO_DATA': -9999,
            'RANGE_BOUNDARIES': 2,
            'RASTER_BAND': 1,
            'TABLE': [-999999, 0.09, 0, 1, 1.01, 1, 2, 999999, 0],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReclassifyNodataToZeroRed'] = processing.run('native:reclassifybytable', alg_params, context=context,
                                                              feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(iter)
        if feedback.isCanceled():
            return {}
        iter = iter + 1

        # OneZeroTable
        alg_params = {
            'DATA_TYPE': 3,
            'INPUT_RASTER': outputs['Translate1']['OUTPUT'],
            'NODATA_FOR_MISSING': False,
            'NO_DATA': -9999,
            'RANGE_BOUNDARIES': 2,
            'RASTER_BAND': 1,
            'TABLE': [-999999999, 0.9, 1, 1, 1, 0, 1.1, 9999999, 1],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Onezerotable'] = processing.run('native:reclassifybytable', alg_params, context=context,
                                                 feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(iter)
        if feedback.isCanceled():
            return {}
        iter = iter + 1

        # red minus idw Null
        alg_params = {
            'BAND_A': 1,
            'BAND_B': 1,
            'BAND_C': None,
            'BAND_D': None,
            'BAND_E': None,
            'BAND_F': None,
            'EXTRA': '',
            'FORMULA': 'A-B',
            'INPUT_A': outputs['ReclassifyNodataToZeroRed']['OUTPUT'],
            'INPUT_B': outputs['Onezerotable']['OUTPUT'],
            'INPUT_C': None,
            'INPUT_D': None,
            'INPUT_E': None,
            'INPUT_F': None,
            'NO_DATA': None,
            'OPTIONS': '',
            'RTYPE': 4,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RedMinusIdwNull'] = processing.run('gdal:rastercalculator', alg_params, context=context,
                                                    feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(iter)
        if feedback.isCanceled():
            return {}
        iter = iter + 1

        # MakeredNodata
        alg_params = {
            '-c': False,
            '-f': False,
            '-i': False,
            '-n': False,
            '-r': False,
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': parameters['CellSize'],
            'GRASS_REGION_PARAMETER': outputs['RresampleCfm']['output'],
            'map': outputs['RedMinusIdwNull']['OUTPUT'],
            'null': None,
            'setnull': '0',
            'output': QgsProcessingUtils.generateTempFilename('redforbuffer.tif')
        }
        redforbuffer = alg_params['output']
        outputs['Makerednodata'] = processing.run('grass7:r.null', alg_params, context=context, feedback=feedback,
                                                  is_child_algorithm=True)

        feedback.setCurrentStep(iter)
        if feedback.isCanceled():
            return {}
        iter = iter + 1

        # blueTmp reclass
        alg_params = {
            'DATA_TYPE': 3,
            'INPUT_RASTER': outputs['RedMinusIdwNull']['OUTPUT'],
            'NODATA_FOR_MISSING': False,
            'NO_DATA': -9999,
            'RANGE_BOUNDARIES': 2,
            'RASTER_BAND': 1,
            'TABLE': [1, 1, 0, 0, 0, 1],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['BluetmpReclass'] = processing.run('native:reclassifybytable', alg_params, context=context,
                                                   feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(iter)
        if feedback.isCanceled():
            return {}
        iter = iter + 1

        # r.buffer
        alg_params = {
            '-z': False,
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'distances': '1',
            'input': redforbuffer,
            'units': 0,
            'output': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Rbuffer'] = processing.run('grass7:r.buffer', alg_params, context=context, feedback=feedback,
                                            is_child_algorithm=True)

        feedback.setCurrentStep(iter)
        if feedback.isCanceled():
            return {}
        iter = iter + 1

        # Translate (convert format)
        alg_params = {
            'COPY_SUBDATASETS': False,
            'DATA_TYPE': 0,
            'EXTRA': '',
            'INPUT': outputs['Rbuffer']['output'],
            'NODATA': 0,
            'OPTIONS': '',
            'TARGET_CRS': None,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['TranslateConvertFormat'] = processing.run('gdal:translate', alg_params, context=context,
                                                           feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(iter)
        if feedback.isCanceled():
            return {}
        iter = iter + 1

        # Reclassify nodata to zero
        alg_params = {
            'DATA_TYPE': 3,
            'INPUT_RASTER': outputs['TranslateConvertFormat']['OUTPUT'],
            'NODATA_FOR_MISSING': False,
            'NO_DATA': -9999,
            'RANGE_BOUNDARIES': 0,
            'RASTER_BAND': 1,
            'TABLE': [-1, 1, 0, 1, 2, 1, 2, 256, 0],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReclassifyNodataToZero'] = processing.run('native:reclassifybytable', alg_params, context=context,
                                                           feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(iter)
        if feedback.isCanceled():
            return {}
        iter = iter + 1

        # blueCalculator
        alg_params = {
            'BAND_A': 1,
            'BAND_B': 1,
            'BAND_C': None,
            'BAND_D': None,
            'BAND_E': None,
            'BAND_F': None,
            'EXTRA': '',
            'FORMULA': 'A-B',
            'INPUT_A': outputs['BluetmpReclass']['OUTPUT'],
            'INPUT_B': outputs['ReclassifyNodataToZero']['OUTPUT'],
            'INPUT_C': None,
            'INPUT_D': None,
            'INPUT_E': None,
            'INPUT_F': None,
            'NO_DATA': None,
            'OPTIONS': '',
            'RTYPE': 4,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Bluecalculator'] = processing.run('gdal:rastercalculator', alg_params, context=context,
                                                   feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(iter)
        if feedback.isCanceled():
            return {}
        iter = iter + 1

        # Raster calculator
        alg_params = {
            'BAND_A': 1,
            'BAND_B': 1,
            'BAND_C': 1,
            'BAND_D': 1,
            'BAND_E': 1,
            'BAND_F': None,
            'EXTRA': '',
            'FORMULA': '(C*A) + (D*B) + (((A+B)/2)*E)',
            'INPUT_A': outputs['RresampleTli']['output'],
            'INPUT_B': outputs['RresampleIdw']['output'],
            'INPUT_C': outputs['Bluecalculator']['OUTPUT'],
            'INPUT_D': outputs['RedMinusIdwNull']['OUTPUT'],
            'INPUT_E': outputs['ReclassifyNodataToZero']['OUTPUT'],
            'INPUT_F': None,
            'NO_DATA': None,
            'OPTIONS': '',
            'RTYPE': 5,
            'OUTPUT': QgsProcessingUtils.generateTempFilename('DFM_hybrid.tif')
        }
        DFM_hybrid = alg_params['OUTPUT']
        outputs['RasterCalculator'] = processing.run('gdal:rastercalculator', alg_params, context=context,
                                                     feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(iter)
        if feedback.isCanceled():
            return {}
        iter = iter + 1

        # r.patch
        alg_params = {
            '-z': False,
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'input': [DFM_hybrid, outputs['RresampleTli']['output']],
            'output': QgsProcessingUtils.generateTempFilename('dfmpatched.tif')
        }
        outputs['Rpatch'] = processing.run('grass7:r.patch', alg_params, context=context, feedback=feedback,
                                           is_child_algorithm=True)
        DFMPatched = outputs['Rpatch']['output']

        feedback.setCurrentStep(iter)
        if feedback.isCanceled():
            return {}
        iter = iter + 1

        # Warp (reproject)
        alg_params = {
            'DATA_TYPE': 0,
            'EXTRA': '',
            'INPUT': DFMPatched,
            'MULTITHREADING': False,
            'NODATA': None,
            'OPTIONS': '',
            'RESAMPLING': 0,
            'SOURCE_CRS': parameters['CRS'],
            'TARGET_CRS': parameters['CRS'],
            'TARGET_EXTENT': None,
            'TARGET_EXTENT_CRS': None,
            'TARGET_RESOLUTION': None,
            'OUTPUT': QgsProcessingUtils.generateTempFilename('dfmpatched.tif')
        }

        outputs['WarpReproject'] = processing.run('gdal:warpreproject', alg_params, context=context,
                                                  feedback=feedback,
                                                  is_child_algorithm=True)
        DFMPatched = outputs['WarpReproject']['OUTPUT']

        feedback.setCurrentStep(iter)
        if feedback.isCanceled():
            return {}
        iter = iter + 1

        if parameters['loadDFM']:
            # Load layer into project
            alg_params = {
                'INPUT': DFMPatched,
                'NAME': parameters['prefix'] + 'DFM'
            }


            outputs['LoadLayerIntoProject'] = processing.run('native:loadlayer', alg_params, context=context,
                                                         feedback=feedback, is_child_algorithm=True)

        results['Dfm'] = DFMPatched

        feedback.setCurrentStep(iter)
        if feedback.isCanceled():
            return {}
        iter = iter + 1

        return results

    def name(self):
        return 'Hybrid interpolation'

    def displayName(self):
        return 'Hybrid interpolation'

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def icon(self):
        cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]
        icon = QIcon(os.path.join(os.path.join(cmd_folder, 'icons/2_3_Hybrid.png')))
        return icon

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return ''

    def shortHelpString(self):
        return """<html><body>
    <p>This algorithm calculates a hybrid interpolation of DFM/DEM. It uses IDW (Inverse Distance Weighing) interpolation in areas of low DFM confidence (levels 1-3) and TLI ( Triangulation with Linear Interpolation) interpolation in areas of high DFM confidence (levels 4-6). The user provides DFM confidence map, TLI and IDW. The module works best when TLI and IDW are calculated under very similar conditions, such as those provided by Golden Software Surfer.
    This interpolator is best suited for low or medium point density data characterized by significant local variation in point density, such as an open landscape interspersed with hedgerows or other patches of dense vegetation. For high point density data, the TLI by itself usually gives better results.</p>
    <h2>Input</h2>
    <h3>DFM Confidence Map</h3>
    <p>Must be calculated with DFM Confidence Map module from IDW/TLI interpolation for the desired cell size.</p>
    <h3>IDW Interpolation</h3>
    <p>Input DFM/DEM interpolated with IDW (Inverse Distance Weighing; use Create base data tool or, if available, Golden Software Surfer).</p>
    <h3>TLI Interpolation</h3>
    <p>Input DFM/DEM interpolated with TLI (Triangulation with Linear Interpolation; use Create base data tool).</p>
    <h2>Parameters</h2>
    <h3>Source File Coordinate System</h3>
    <p>Select the Coordinate Reference System (CRS) of the input LAS /LAZ file. Make sure the CRS is Cartesian (x and y in meters, not degrees). If you are not sure which is the correct CRS and you only need it temporarily, you can select any Cartesian CRS, for example, EPSG:8687. XYZ should be in m. <b> <br>The tool will not work correctly with data in feet, km, cm etc.</b></p>
    <h3>Cell Size</h3>
    <p>The resolution or cell size of the final DFM/DEM. For best results, all inputs should have the same cell size.</p>
    <h3>Grow Radius (Cells) </h3>
    <p>Grow radius in raster cells for "RED" areas with low DFM confidence will increase (grow) the areas where IDW is used. Tweak this setting if you notice unwanted interpolation artefacts (noise) in contact areas between TLI and IDW.</p>
    <h3>Name prefix for layers</h3>
    <p>The output layers are added to the map as temporary layers with default names. They can then be saved as files. To distinguish them from files previously created with the same tool, a prefix should be defined to prevent duplication (which may cause errors on some systems).</p>
    <h3>Outputs:</h3>
    <p><b>DFM: </b>Digital Feature Model (archaeology-specific DEM, combining ground and buildings)</p>
    <p></p>
    <h2>FAQ</h2>
    <h3>I have NoData holes in my DFM/DEM</h3>
    <p>Wherever one of the inputs has a NoData value, the algorithm will return NoData. Common sources for NoData are too low radius setting for IDW or too small setting for maximum triangle size in TLI.</p>
    <h3>The artifacts (noise) in the contact areas are too big and tweaking the Grow radius doesn't help</h3>
    <p>Some amount of artifacts is inevitable. In our testing the artifacts were significantly smaller when the input layers have been calculated with Golden Software Surfer, since exactly same parameters for neighborhood search can be set. If the artifacts are so strong, that they can misguide archaeological interpretation, then we suggest using IDW interpolation instead.</p>
    <p></p>
    <br>
    <p><b>References:</b> Štular, B.; Lozić, E.; Eichert, S. Airborne LiDAR-Derived Digital Elevation Model for Archaeology.Remote Sens.2021,13, 1855. <a href="https://doi.org/10.3390/rs13091855">https://doi.org/10.3390/rs13091855</a></p>
    <br><a href="https://github.com/stefaneichert/OpenLidarTools">Website</a>
    <br><p align="right">Algorithm author: Benjamin Štular, Edisa Lozić, Stefan Eichert </p><p align="right">Help author: Benjamin Štular, Edisa Lozić, Stefan Eichert</p></body></html>"""

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return HybridInterpolation()

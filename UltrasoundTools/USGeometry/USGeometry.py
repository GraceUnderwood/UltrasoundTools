import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy, math

#
# USGeometry
#

class USGeometry(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "USGeometry"
    self.parent.categories = ["Ultrasound"]
    self.parent.dependencies = []
    self.parent.contributors = ["Matt Lougheed (Perk Lab)"]
    self.parent.helpText = """
    This is an example of scripted loadable module bundled in an extension.
    It performs a simple thresholding on the input volume and optionally captures a screenshot.
    """
    self.parent.acknowledgementText = """
"""

#
# USGeometryWidget
#

class USGeometryWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    #
    # INPUTS Area
    #
    inputsCollapsibleButton = ctk.ctkCollapsibleButton()
    inputsCollapsibleButton.text = "Inputs"
    self.layout.addWidget(inputsCollapsibleButton)
    inputsFormLayout = qt.QVBoxLayout(inputsCollapsibleButton)

    #
    # Input volume selector
    #
    self.inputSelector = slicer.qMRMLNodeComboBox()
    self.inputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.inputSelector.selectNodeUponCreation = True
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = False
    self.inputSelector.noneEnabled = False
    self.inputSelector.showHidden = False
    self.inputSelector.showChildNodeTypes = False
    self.inputSelector.setMRMLScene( slicer.mrmlScene )
    self.inputSelector.setToolTip( "Pick the input volume for geometry viewing." )

    #
    # Algorithm segmentation volume selector
    #
    self.algorithmSegmentation = slicer.qMRMLNodeComboBox()
    self.algorithmSegmentation.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
    self.algorithmSegmentation.selectNodeUponCreation = True
    self.algorithmSegmentation.addEnabled = False
    self.algorithmSegmentation.removeEnabled = False
    self.algorithmSegmentation.noneEnabled = False
    self.algorithmSegmentation.showHidden = False
    self.algorithmSegmentation.showChildNodeTypes = False
    self.algorithmSegmentation.setMRMLScene( slicer.mrmlScene )
    self.algorithmSegmentation.setToolTip( "Pick the algorithm segmentation to evaluate." )

    #
    # Volumes group box
    #
    self.inputVolumesLayout = qt.QFormLayout()
    self.inputVolumesLayout.addRow("Input volume: ", self.inputSelector)
    self.inputVolumesLayout.addRow("Algorithm segmentation: ", self.algorithmSegmentation)
    self.volumesGroupBox = qt.QGroupBox()
    self.volumesGroupBox.setTitle("Volumes")
    self.volumesGroupBox.setLayout(self.inputVolumesLayout)
    inputsFormLayout.addWidget(self.volumesGroupBox)

    #
    # Configuration file selector
    #
    fileLayout = qt.QHBoxLayout()
    self.configFile = qt.QLineEdit()
    self.configFile.setReadOnly(True)
    self.configFileButton = qt.QPushButton()
    self.configFileButton.setText("Select File")
    fileLayout.addWidget(self.configFile)
    fileLayout.addWidget(self.configFileButton)

    #
    # Manual segmentations directory
    #
    directoryLayout = qt.QHBoxLayout()
    self.directory = qt.QLineEdit()
    self.directory.setReadOnly(True)
    self.directoryButton = qt.QPushButton()
    self.directoryButton.setText("Select Directory")
    directoryLayout.addWidget(self.directory)
    directoryLayout.addWidget(self.directoryButton)

    #
    # Paths group box
    #
    self.inputFilePathsLayout = qt.QFormLayout()
    self.inputFilePathsLayout.addRow("PLUS configuration file: ", fileLayout)
    self.inputFilePathsLayout.addRow("Manual segmentations directory: ", directoryLayout)
    self.pathsGroupBox = qt.QGroupBox()
    self.pathsGroupBox.setTitle("Paths")
    self.pathsGroupBox.setLayout(self.inputFilePathsLayout)
    inputsFormLayout.addWidget(self.pathsGroupBox)

    #
    # False negative distance value
    #
    self.falseNegativeDistance = qt.QSpinBox()
    self.falseNegativeDistance.setMinimum(0)
    self.falseNegativeDistance.setSuffix(" mm")

    #
    # Parameters group box
    #
    self.inputParametersLayout = qt.QFormLayout()
    self.inputParametersLayout.addRow("False negative distance: ", self.falseNegativeDistance)
    self.parametersGroupBox = qt.QGroupBox()
    self.parametersGroupBox.setTitle("Parameters")
    self.parametersGroupBox.setLayout(self.inputParametersLayout)
    inputsFormLayout.addWidget(self.parametersGroupBox)

    #
    # OUTPUT VOLUMES Area
    #
    outputsCollapsibleButton = ctk.ctkCollapsibleButton()
    outputsCollapsibleButton.text = "Outputs"
    self.layout.addWidget(outputsCollapsibleButton)
    outputsFormLayout = qt.QVBoxLayout(outputsCollapsibleButton)

    #
    # Merged manual segmentations
    #
    self.mergedManualSegmentations = slicer.qMRMLNodeComboBox()
    self.mergedManualSegmentations.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
    self.mergedManualSegmentations.selectNodeUponCreation = True
    self.mergedManualSegmentations.addEnabled = True
    self.mergedManualSegmentations.renameEnabled = True
    self.mergedManualSegmentations.removeEnabled = True
    self.mergedManualSegmentations.noneEnabled = False
    self.mergedManualSegmentations.showHidden = False
    self.mergedManualSegmentations.showChildNodeTypes = False
    self.mergedManualSegmentations.setMRMLScene( slicer.mrmlScene )
    self.mergedManualSegmentations.setToolTip( "Pick the label map for the merged manual segmentations." )

    #
    # Scanline label map
    #
    self.scanlines = slicer.qMRMLNodeComboBox()
    self.scanlines.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
    self.scanlines.selectNodeUponCreation = True
    self.scanlines.addEnabled = True
    self.scanlines.renameEnabled = True
    self.scanlines.removeEnabled = True
    self.scanlines.noneEnabled = False
    self.scanlines.showHidden = False
    self.scanlines.showChildNodeTypes = False
    self.scanlines.setMRMLScene( slicer.mrmlScene )
    self.scanlines.setToolTip( "Pick the label map for displaying the input volumes scanlines." )

    #
    # Output segmentation label map
    #
    self.outputSegmentation = slicer.qMRMLNodeComboBox()
    self.outputSegmentation.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
    self.outputSegmentation.selectNodeUponCreation = True
    self.outputSegmentation.addEnabled = True
    self.outputSegmentation.renameEnabled = True
    self.outputSegmentation.removeEnabled = True
    self.outputSegmentation.noneEnabled = False
    self.outputSegmentation.showHidden = False
    self.outputSegmentation.showChildNodeTypes = False
    self.outputSegmentation.setMRMLScene( slicer.mrmlScene )
    self.outputSegmentation.setToolTip( "Pick the label map for the output segmentation." )

    #
    # Volumes group box
    #
    self.outputVolumesLayout = qt.QFormLayout()
    self.outputVolumesLayout.addRow("Summed manaual segmentations: ", self.mergedManualSegmentations)
    self.outputVolumesLayout.addRow("Scanlines: ", self.scanlines)
    self.outputVolumesLayout.addRow("Output segmentation: ", self.outputSegmentation)
    self.outputVolumesGroupBox = qt.QGroupBox()
    self.outputVolumesGroupBox.setTitle("Volumes")
    self.outputVolumesGroupBox.setLayout(self.outputVolumesLayout)
    outputsFormLayout.addWidget(self.outputVolumesGroupBox)

    #
    # True positive metric
    #
    self.truePositiveMetric = qt.QLineEdit()
    self.truePositiveMetric.setReadOnly(True)

    #
    # False positive metric
    #
    self.falsePositiveMetric = qt.QLineEdit()
    self.falsePositiveMetric.setReadOnly(True)

    #
    # False negative metric
    #
    self.falseNegativeMetric = qt.QLineEdit()
    self.falseNegativeMetric.setReadOnly(True)

    #
    # Output metric group box
    #
    self.outputMetricsLayout = qt.QFormLayout()
    self.outputMetricsLayout.addRow("True positive percentage: ", self.truePositiveMetric)
    self.outputMetricsLayout.addRow("False positive percentage: ", self.falsePositiveMetric)
    self.outputMetricsLayout.addRow("False negative percentage: ", self.falseNegativeMetric)
    self.outputMetricsGroupBox = qt.QGroupBox()
    self.outputMetricsGroupBox.setTitle("Metrics")
    self.outputMetricsGroupBox.setLayout(self.outputMetricsLayout)
    outputsFormLayout.addWidget(self.outputMetricsGroupBox)

    #
    # FUNCTIONS Area
    #
    functionsCollapsibleButton = ctk.ctkCollapsibleButton()
    functionsCollapsibleButton.text = "Functions"
    self.layout.addWidget(functionsCollapsibleButton)
    functionsFormLayout = qt.QVBoxLayout(functionsCollapsibleButton)

    # Button for generating scanlines from PLUS config file
    self.createScanlinesButton = qt.QPushButton("Create Scanlines")
    self.createScanlinesButton.toolTip = "Create scanlines from PLUS configuration file"
    self.createScanlinesButton.enabled = False

    # Button for combining manual segmentations into one volume
    self.createMergedManualSegmentationButton = qt.QPushButton("Merge Manual Segmentations")
    self.createMergedManualSegmentationButton.toolTip = "Combine manual segmentations into one volume"
    self.createMergedManualSegmentationButton.enabled = False

    # Button for computing metrics of a segmentation
    self.computeMetricsButton = qt.QPushButton("Compute Metrics")
    self.computeMetricsButton.toolTip = "Compute the true positive and false negative metrics of a segmentation"
    self.computeMetricsButton.enabled = False

    # Add buttongs to functions section
    functionsFormLayout.addWidget(self.createScanlinesButton)
    functionsFormLayout.addWidget(self.createMergedManualSegmentationButton)
    functionsFormLayout.addWidget(self.computeMetricsButton)

    # Connections

    # *** Input/output volumes and parameters ***
    # Ultrasound volume
    self.inputSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onInputSelect)
    # Algorithm segmentation
    self.algorithmSegmentation.connect('currentNodeChanged(vtkMRMLNode*)', self.onAlgorithmSegmentationSelect)
    # PLUS config file
    self.configFile.connect('textChanged(QString)',self.onConfigFileSelect)
    # Manual segmentations directory
    self.directory.connect('textChanged(QString)',self.createMergedManualSegmentationsEnableCheck)
    # Summed manual segmentations
    self.mergedManualSegmentations.connect("currentNodeChanged(vtkMRMLNode*)", self.createMergedManualSegmentationsEnableCheck)
    # Scanlines
    self.scanlines.connect('currentNodeChanged(vtkMRMLNode*)', self.createScanlinesEnableCheck)
    # Output segmentation
    self.outputSegmentation.connect('currentNodeChanged(vtkMRMLNode*)', self.computeMetricsEnableCheck)

    # *** Buttons for selecting config file / manual segmentation directory ***
    # Manaul segmentation directory button
    self.directoryButton.connect('clicked(bool)', self.selectDirectory)
    # Ultrasound config file button
    self.configFileButton.connect('clicked(bool)', self.selectFile)

    # *** Function buttons ***
    # Sum manual segmentations
    self.createMergedManualSegmentationButton.connect('clicked(bool)', self.onCreateMergedManualSegmentationButton)
    # Create scanlines
    self.createScanlinesButton.connect('clicked(bool)', self.onCreateScanlinesButton)
    # Compute metrics
    self.computeMetricsButton.connect('clicked(bool)', self.onComputeMetricsButton)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onInputSelect()

  def cleanup(self):
    pass

  def ultrasoundVolumeAndConfigExist(self):
    return self.inputSelector.currentNode() and os.path.isfile(self.configFile.text)

  def createScanlinesEnableCheck(self):
    self.createScanlinesButton.enabled = self.scanlines.currentNode() and self.ultrasoundVolumeAndConfigExist()

  def createMergedManualSegmentationsEnableCheck(self):
    self.createMergedManualSegmentationButton.enabled = self.mergedManualSegmentations.currentNode() and self.ultrasoundVolumeAndConfigExist() and os.path.isdir(self.directory.text)

  def computeMetricsEnableCheck(self):
    #summedImage, outputSegmentation, algorithmSegmentatiom
    self.computeMetricsButton.enabled = self.ultrasoundVolumeAndConfigExist() and self.mergedManualSegmentations.currentNode() and self.algorithmSegmentation.currentNode()

  def onInputSelect(self):
    self.createMergedManualSegmentationsEnableCheck()
    self.createScanlinesEnableCheck()
    self.computeMetricsEnableCheck()

  def onAlgorithmSegmentationSelect(self):
    self.computeMetricsEnableCheck()

  def onConfigFileSelect(self):
    self.createMergedManualSegmentationsEnableCheck()
    self.createScanlinesEnableCheck()
    self.computeMetricsEnableCheck()

  def selectFile(self):
    fileName = qt.QFileDialog().getOpenFileName()
    self.configFile.setText(fileName)

  def selectDirectory(self):
    directoryName = qt.QFileDialog().getExistingDirectory()
    self.directory.setText(directoryName)

  def onCreateScanlinesButton(self):
    logic = USGeometryLogic(self.configFile.text, self.inputSelector.currentNode())
    logic.createScanlines(self.scanlines.currentNode())

  def onCreateMergedManualSegmentationButton(self):
    logic = USGeometryLogic(self.configFile.text, self.inputSelector.currentNode())
    logic.sumManualSegmentations(self.directory.text, self.mergedManualSegmentations.currentNode())

  def onComputeMetricsButton(self):
    logic = USGeometryLogic(self.configFile.text, self.inputSelector.currentNode())
    logic.computeMergedSegmentationMetrics(self.mergedManualSegmentations.currentNode(), self.outputSegmentation.currentNode(), self.algorithmSegmentation.currentNode(), self.falseNegativeDistance.value, self.truePositiveMetric, self.falseNegativeMetric, self.falsePositiveMetric)

#
# USGeometryLogic
#

class USGeometryLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, configFile, inputVolume):

    self.inputVolume = inputVolume
    self.rasToIjk = vtk.vtkMatrix4x4()
    self.ijkToRas = vtk.vtkMatrix4x4()
    self.inputVolume.GetRASToIJKMatrix(self.rasToIjk)
    self.inputVolume.GetIJKToRASMatrix(self.ijkToRas)
    self.scanlines = []
    from xml.dom import minidom
    # Make sure the specified configuration file exists
    if not os.path.exists(configFile):
      errorMessage = "Configuration file doesn't exist."
      slicer.util.errorDisplay(errorMessage)
      raise ValueError(errorMessage)
    parser = minidom.parse(configFile)
    scanConversionElement = parser.getElementsByTagName("ScanConversion")
    # Check that that 1 ScanConversion element exists
    if (len(scanConversionElement) < 1):
      errorMessage = "Could not find ScanConversion element in configuration file!"
      slicer.util.errorDisplay(errorMessage)
      raise ValueError(errorMessage)
    elif (len(scanConversionElement) > 1):
      errorMessage = "Found multiple ScanConversion elements in configuration file!"
      slicer.util.errorDisplay(errorMessage)
      raise ValueError(errorMessage)

    scanConversionElement = scanConversionElement[0]

    # Values common to both linear and curvilinear
    self.transducerGeometry = (scanConversionElement.attributes['TransducerGeometry'].value).upper()
    # Verify proper transducer geometry
    if (self.transducerGeometry != "CURVILINEAR" and self.transducerGeometry != "LINEAR"):
      errorMessage = "TransducerGeometry must be either CURVILINEAR or LINEAR"
      slicer.util.errorDisplay(errorMessage)
      raise ValueError(errorMessage)
    self.outputImageSizePixel = scanConversionElement.attributes['OutputImageSizePixel'].value
    self.outputImageSizePixel = map(int, self.outputImageSizePixel.split(" "))
    volumeDimensions = self.inputVolume.GetImageData().GetDimensions()
    # Check that the corresponding input volume has same image slice dimensions as
    # specified in the configuration file
    if (self.outputImageSizePixel[0] != volumeDimensions[0]
        or self.outputImageSizePixel[1] != volumeDimensions[1]):
      errorMessage = "Input volume size does not correspond to size specified in configuration file.\n " \
                     "Input volume slice: [{} {}]\n" \
                     "Configuration file slice: [{} {}]".format(volumeDimensions[0], volumeDimensions[1], self.outputImageSizePixel[0], self.outputImageSizePixel[1])
      slicer.util.errorDisplay(errorMessage)
      raise ValueError(errorMessage)
    self.transducerCenterPixel = scanConversionElement.attributes['TransducerCenterPixel'].value
    self.transducerCenterPixel = map(int, self.transducerCenterPixel.split(" "))
    self.numberOfScanlines = int(scanConversionElement.attributes['NumberOfScanLines'].value)
    if (self.numberOfScanlines < 0):
      errorMessage = "NumberOfScanLines: {} cannot be less than 0".format(self.numberOfScanlines)
      slicer.util.errorDisplay(errorMessage)
      raise ValueError(errorMessage)
    self.outputImageSpacing = scanConversionElement.attributes['OutputImageSpacingMmPerPixel'].value
    self.outputImageSpacing = map(float, self.outputImageSpacing.split(" "))
    self.numberOfSamplesPerScanline = int(scanConversionElement.attributes['NumberOfSamplesPerScanLine'].value)

    # Values just for curvilinear
    if (self.transducerGeometry == "CURVILINEAR"):
      self.thetaStartDeg = float(scanConversionElement.attributes['ThetaStartDeg'].value)
      self.thetaStopDeg = float(scanConversionElement.attributes['ThetaStopDeg'].value)
      self.radiusStartMm = float(scanConversionElement.attributes['RadiusStartMm'].value)
      self.radiusStopMm = float(scanConversionElement.attributes['RadiusStopMm'].value)
      self.totalDeg = abs(self.thetaStopDeg - self.thetaStartDeg)
      self.degreesPerScanline = self.totalDeg / self.numberOfScanlines
      self.circleCenter = [self.transducerCenterPixel[0], self.transducerCenterPixel[1] - self.radiusStartMm/self.outputImageSpacing[1]]
    # Values just for linear
    elif (self.transducerGeometry == "LINEAR"):
      self.transducerWidthMm = float(scanConversionElement.attributes['TransducerWidthMm'].value)
      self.imagingDepthMm = float(scanConversionElement.attributes['ImagingDepthMm'].value)
      self.imageWidthPixel = int(self.transducerWidthMm / self.outputImageSpacing[0])
      self.topLeftPixel = [int(self.transducerCenterPixel[0] - 0.5 * self.imageWidthPixel), self.transducerCenterPixel[1]]
      self.scanlineSpacingPixels = float(self.imageWidthPixel) / (self.numberOfScanlines - 1) # There are (numberOfScanlines - 1) spaces between first and last scanline
      self.scanlineLengthPixels = int(self.imagingDepthMm / self.outputImageSpacing[1])

    # Create the scanlines
    for i in range(self.numberOfScanlines):
      [start, end] = self.scanlineEndPoints(i)
      currentScanline = Scanline(start, end)
      self.scanlines.append(currentScanline)

  def scanlineEndPoints(self, scanline):
    import math
    # Compute curvilinear xy values
    if (self.transducerGeometry == "CURVILINEAR"):

      # Compute angle for desired scanline
      angle = self.thetaStartDeg + scanline * self.degreesPerScanline
      angleRadians = math.pi * angle / 180

      # Compute the starting point
      startScanlineX = self.circleCenter[0] + math.sin(angleRadians) * self.radiusStartMm / self.outputImageSpacing[0]
      startScanlineY = self.circleCenter[1] + math.cos(angleRadians) * self.radiusStartMm / self.outputImageSpacing[1]

      # Compute the ending point
      endScanlineX = self.circleCenter[0] + math.sin(angleRadians) * self.radiusStopMm / self.outputImageSpacing[0]
      endScanlineY = self.circleCenter[1] + math.cos(angleRadians) * self.radiusStopMm / self.outputImageSpacing[1]

    # Compute linear xy values
    elif (self.transducerGeometry == "LINEAR"):
      # Compute the starting point
      startScanlineX = self.topLeftPixel[0] + scanline * self.scanlineSpacingPixels
      startScanlineY = self.topLeftPixel[1]

      # Compute the end point
      endScanlineX = startScanlineX # Vertical line so same 'x' value
      endScanlineY = self.topLeftPixel[1] + self.scanlineLengthPixels
    else:
      # ERROR: should not reach here
      print("Error in scanlineEndPoints")

    # Verify acceptable starting point for scanline
    if (startScanlineX < 0 or startScanlineX > self.outputImageSizePixel[0]-1):
      errorMessage = "Scanline starting point X value: {} out of bounds!".format(startScanlineX)
      slicer.util.errorDisplay(errorMessage)
      raise ValueError(errorMessage)
    if (startScanlineY < 0 or startScanlineY > self.outputImageSizePixel[1]-1):
      errorMessage = "Scanline starting point Y value: {} out of bounds!".format(startScanlineY)
      slicer.util.errorDisplay(errorMessage)
      raise ValueError(errorMessage)
    # Verify acceptable ending point for scanline
    if (endScanlineX < 0 or endScanlineX > self.outputImageSizePixel[0]-1):
      errorMessage = "Scanline ending point X value: {} out of bounds!".format(endScanlineX)
      slicer.util.errorDisplay(errorMessage)
      raise ValueError(errorMessage)
    if (endScanlineY < 0 or endScanlineY > self.outputImageSizePixel[1]-1):
      errorMessage = "Scanline ending point Y value: {} out of bounds!".format(endScanlineY)
      slicer.util.errorDisplay(errorMessage)
      raise ValueError(errorMessage)

    # Combine XY values and return
    startScanline = [startScanlineX, startScanlineY]
    endScanline = [endScanlineX, endScanlineY]

    return [startScanline, endScanline]

  def euclidean_distance(self,point1,point2):
      return math.sqrt((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2 + (point2[2] - point1[2]) ** 2)

  def sumManualSegmentations(self, manualSegmentationsDirectory, mergedVolume):
    # Get the manual segmentations and create a single summed image
    import glob
    manualSegmentationFilenames = glob.glob(manualSegmentationsDirectory+"/*.mha")

    # Get the first image which each successive image will be added to
    reader = vtk.vtkMetaImageReader()
    reader.SetFileName(manualSegmentationFilenames[0])
    reader.Update()
    summedImage = vtk.vtkImageData()
    summedImage.SetExtent(reader.GetOutput().GetExtent())
    summedImage.AllocateScalars(vtk.VTK_UNSIGNED_CHAR,1)
    summedImage.ShallowCopy(reader.GetOutput())

    # Initialize filter to add images together
    mathFilter = vtk.vtkImageMathematics()

    # Iterate list and add each new image
    for currentFile in manualSegmentationFilenames[1:]:
      # Get new image
      reader.SetFileName(currentFile)
      reader.Update()

      # Add it to existing summation
      mathFilter.SetInput1Data(summedImage)
      mathFilter.SetInput2Data(reader.GetOutput())
      mathFilter.Update()

      # Get new summation
      summedImage.ShallowCopy(mathFilter.GetOutput())

    # Add summed image to slicer scene
    mergedVolume.SetRASToIJKMatrix(self.rasToIjk)
    mergedVolume.SetIJKToRASMatrix(self.ijkToRas)
    mergedVolume.SetAndObserveImageData(summedImage)

  def createScanlines(self, scanlineVolume):
    imgDim = self.inputVolume.GetImageData().GetDimensions()
    drawFilter = vtk.vtkImageCanvasSource2D()
    drawFilter.SetExtent(0,imgDim[0]-1,0,imgDim[1]-1,0,0)
    drawFilter.SetScalarTypeToUnsignedChar()
    drawFilter.SetDrawColor(0) # Color for background
    drawFilter.FillBox(0,imgDim[0]-1,0,imgDim[1]-1) # Initialize background
    drawFilter.SetDrawColor(1) # Color for scanlines
    # Draw each scanline
    for i in range(self.numberOfScanlines):
      drawFilter.FillTube(int(self.scanlines[i].startPoint[0]),int(self.scanlines[i].startPoint[1]),int(self.scanlines[i].endPoint[0]),int(self.scanlines[i].endPoint[1]),0.5)
    drawFilter.Update()

    # Copy scanline slice to match the Z-dimension of input US volume
    numOfSlices = imgDim[2]
    imageAppendFilter = vtk.vtkImageAppend()
    imageAppendFilter.SetAppendAxis(2)
    for _ in range(numOfSlices):
      imageAppendFilter.AddInputData(drawFilter.GetOutput())
    imageAppendFilter.Update()

    # Set scanline imagedata
    scanlineVolume.SetIJKToRASMatrix(self.ijkToRas)
    scanlineVolume.SetRASToIJKMatrix(self.rasToIjk)
    scanlineVolume.SetAndObserveImageData(imageAppendFilter.GetOutput())

  def computeMergedSegmentationMetrics(self, summedImage, outputSegmentation, algorithmSegmentation, falseNegativeDistance, truePositiveOutput, falseNegativeOutput, falsePositiveOutput):
    imgDim = self.inputVolume.GetImageData().GetDimensions()
    summedImageData = summedImage.GetImageData()
    algorithmSegmentationImageData = algorithmSegmentation.GetImageData()
    outputSegmentationImageData = vtk.vtkImageData()
    outputSegmentationImageData.SetExtent(summedImageData.GetExtent())
    outputSegmentationImageData.AllocateScalars(vtk.VTK_UNSIGNED_CHAR,1)
    outputSegmentation.SetAndObserveImageData(outputSegmentationImageData)
    outputSegmentation.SetRASToIJKMatrix(self.rasToIjk)
    outputSegmentation.SetIJKToRASMatrix(self.ijkToRas)
    pixels = slicer.util.array(outputSegmentation.GetName())
    pixels.fill(0) # Zero out the output segmentation label map

    # Values for metric computations
    totalAlgorithmSegmentationPoints = 0
    pointsWithinAcceptableRegion = 0
    pointsWithinRequiredRegion = 0
    falsePositivePoints = 0
    scanlinesWithSegmentation = 0

    # Iterate each scanline
    for i in range(self.numberOfScanlines):
      [startScanline, endScanline] = self.scanlineEndPoints(i)
      currentScanline = Scanline(startScanline, endScanline)
      self.scanlines.append(currentScanline)
      for z in range(imgDim[2]):
        # Create the scanline line source
        currentLine = vtk.vtkLineSource()
        currentStartPoint = [startScanline[0], startScanline[1], z]
        currentEndPoint = [endScanline[0], endScanline[1], z]
        currentLine.SetPoint1(currentStartPoint)
        currentLine.SetPoint2(currentEndPoint)
        currentLine.SetResolution(self.numberOfSamplesPerScanline)
        currentLine.Update()

        # Compute the unit vector of the current scanline
        denom = math.sqrt((currentEndPoint[0] - currentStartPoint[0])**2 + (currentEndPoint[1] - currentStartPoint[1])**2)
        unitVector = [(currentEndPoint[0] - currentStartPoint[0])/denom, (currentEndPoint[1] - currentStartPoint[1])/denom]

        # Compute the unit vector length in mm
        unitVectorMM = [unitVector[0]*self.outputImageSpacing[0], unitVector[1]*self.outputImageSpacing[1]]
        unitVectorLengthMM = math.sqrt(unitVectorMM[0]**2 + unitVectorMM[1]**2)

        # Compute the factor unit vector needs to be multiplied by to get to false negative distance
        unitVectorFactor = falseNegativeDistance / unitVectorLengthMM
        linePoints = currentLine.GetOutput()
        xVals = []
        yVals = []
        algorithmSegmentationPoints = []

        # Iterate each point on line
        for j in range(linePoints.GetNumberOfPoints()):
          currentPoint = linePoints.GetPoint(j)
          summedSegPoint = summedImageData.GetScalarComponentAsDouble(int(currentPoint[0]),int(currentPoint[1]),int(currentPoint[2]),0)
          if (summedSegPoint > 0): # At least 1 ground truth at this point
            # Add points current X/Y value N times where N is overlap count
            xVals.extend([int(currentPoint[0]) for _ in range(int(summedSegPoint))])
            yVals.extend([int(currentPoint[1]) for _ in range(int(summedSegPoint))])

          algorithmSegPoint = algorithmSegmentationImageData.GetScalarComponentAsDouble(int(currentPoint[0]),int(currentPoint[1]),int(currentPoint[2]),0)
          if (algorithmSegPoint > 0): # The algorithm identified point as bone
            algorithmSegmentationPoints.append([int(currentPoint[0]),int(currentPoint[1]),int(currentPoint[2])])
            totalAlgorithmSegmentationPoints += 1

        if (len(xVals) > 0): # Scanline contains ground truth segmentation
          scanlinesWithSegmentation += 1
          # Compute mean point
          xMean = sum(xVals)/len(xVals)
          yMean = sum(yVals)/len(yVals)
          outputSegmentationImageData.SetScalarComponentFromDouble(xMean,yMean,z,0,255)

          # Compute region edges from standard deviation
          euclideanDistances = []
          for currentX, currentY in zip(xVals, yVals):
            currentDistance = self.euclidean_distance([xMean,yMean,z],[currentX,currentY,z])
            euclideanDistances.append(currentDistance)
          std = numpy.std(euclideanDistances)
          std += 1 # This is so that when calculating true positive point from the false negative point we only extend further (ie. std of 0 means the true positive point is at same point, and > 0 moves out from false negative point)

          toleranceFactor = 5 # What should be used here?
          falseNegativeRegionPoint1 = [xMean + unitVectorFactor * unitVector[0], yMean + unitVectorFactor * unitVector[1]]
          falseNegativeRegionPoint2 = [xMean + -unitVectorFactor * unitVector[0], yMean + -unitVectorFactor * unitVector[1]]

          truePositiveRegionPoint1 = [xMean + unitVectorFactor * std * unitVector[0], yMean + unitVectorFactor * std * unitVector[1]]
          truePositiveRegionPoint2 = [xMean + -unitVectorFactor * std * unitVector[0], yMean + -unitVectorFactor * std * unitVector[1]]

          # Add false negative region points to the output
          outputSegmentationImageData.SetScalarComponentFromDouble(int(falseNegativeRegionPoint1[0]),int(falseNegativeRegionPoint1[1]),z,0,1)
          outputSegmentationImageData.SetScalarComponentFromDouble(int(falseNegativeRegionPoint2[0]),int(falseNegativeRegionPoint2[1]),z,0,1)

          # Add true positive region points to the output
          outputSegmentationImageData.SetScalarComponentFromDouble(int(truePositiveRegionPoint1[0]),int(truePositiveRegionPoint1[1]),z,0,2)
          outputSegmentationImageData.SetScalarComponentFromDouble(int(truePositiveRegionPoint2[0]),int(truePositiveRegionPoint2[1]),z,0,2)

          # Compute algorithm segmentation point distances to acceptable region edge, can use either point as they are equal just opposite
          acceptableDistance = self.euclidean_distance([xMean,yMean,z],[truePositiveRegionPoint1[0],truePositiveRegionPoint1[1],z])
          falseNegativeRegionDistance = self.euclidean_distance([xMean,yMean,z],[falseNegativeRegionPoint1[0],falseNegativeRegionPoint1[1],z])
          print("*****\nFalse negative region distance: {}".format(falseNegativeRegionDistance))
          requiredRegionIdentified = False # For false negative metric
          for currentPoint in algorithmSegmentationPoints:
            currentDistance = self.euclidean_distance([xMean,yMean,z], currentPoint)
            print("Current distance: {}".format(currentDistance))
            if (currentDistance <= acceptableDistance):
              pointsWithinAcceptableRegion += 1
            else: # If not within acceptable distance it's a false positive
              falsePositivePoints += 1
            if (currentDistance < falseNegativeRegionDistance):
              requiredRegionIdentified = True

          if (requiredRegionIdentified):
            pointsWithinRequiredRegion += 1
        else: # No ground truth on this scanline:
          if len(algorithmSegmentationPoints) > 0: # Algorithm identified bone
            falsePositivePoints += len(algorithmSegmentationPoints) # All points are false positive
    '''
    outputSegmentation.SetAndObserveImageData(outputSegmentationImageData)
    outputSegmentation.SetRASToIJKMatrix(self.rasToIjk)
    outputSegmentation.SetIJKToRASMatrix(self.ijkToRas)
    '''
    # Compute / set true positive metric
    truePositiveValue = float(pointsWithinAcceptableRegion) / float(totalAlgorithmSegmentationPoints) * 100
    truePositiveOutput.setText(truePositiveValue)

    # Compute / set false positive metric
    falsePositiveValue = float(falsePositivePoints) / float(totalAlgorithmSegmentationPoints) * 100
    falsePositiveOutput.setText(falsePositiveValue)

    # Compute / set false negative metric
    falseNegativeValue = (1 - float(pointsWithinRequiredRegion) / float(scanlinesWithSegmentation)) * 100
    falseNegativeOutput.setText(falseNegativeValue)
    print("truePositiveOutput: {}\nfalsePositiveOutput: {}\nfalseNegativeOutput: {}".format(truePositiveValue, falsePositiveValue, falseNegativeValue))

class UltrasoundTransducerGeometry:
  def __init__(self, configFile, inputVolume):

    self.inputVolume = inputVolume

    from xml.dom import minidom
    parser = minidom.parse(configFile)
    scanConversionElement = parser.getElementsByTagName("ScanConversion")
    if (len(scanConversionElement) < 1):
      slicer.util.errorDisplay("Could not find ScanConversion element in configuration file!")
      return False
    elif (len(scanConversionElement) > 1):
      slicer.util.errorDisplay("Found multiple ScanConversion elements in configuration file!")
      return False

    scanConversionElement = scanConversionElement[0]

    # Values common to both linear and curvilinear
    self.transducerGeometry = scanConversionElement.attributes['TransducerGeometry'].value
    self.transducerCenterPixel = scanConversionElement.attributes['TransducerCenterPixel'].value
    self.transducerCenterPixel = map(int, self.transducerCenterPixel.split(" "))
    self.numberOfScanlines = int(scanConversionElement.attributes['NumberOfScanLines'].value)
    self.outputImageSpacing = scanConversionElement.attributes['OutputImageSpacingMmPerPixel'].value
    self.outputImageSpacing = map(float, self.outputImageSpacing.split(" "))
    self.numberOfSamplesPerScanline = int(scanConversionElement.attributes['NumberOfSamplesPerScanLine'].value)

    # Values just for curvilinear
    if (self.transducerGeometry == "CURVILINEAR"):
      self.thetaStartDeg = float(scanConversionElement.attributes['ThetaStartDeg'].value)
      self.thetaStopDeg = float(scanConversionElement.attributes['ThetaStopDeg'].value)
      self.radiusStartMm = float(scanConversionElement.attributes['RadiusStartMm'].value)
      self.radiusStopMm = float(scanConversionElement.attributes['RadiusStopMm'].value)
      self.totalDeg = abs(self.thetaStopDeg - self.thetaStartDeg)
      self.degreesPerScanline = self.totalDeg / self.numberOfScanlines
      self.circleCenter = [self.transducerCenterPixel[0], self.transducerCenterPixel[1] - self.radiusStartMm/self.outputImageSpacing[1]]
    # Values just for linear
    elif (self.transducerGeometry == "LINEAR"):
      self.transducerWidthMm = float(scanConversionElement.attributes['TransducerWidthMm'].value)
      self.imagingDepthMm = float(scanConversionElement.attributes['ImagingDepthMm'].value)
      self.imageWidthPixel = self.transducerWidthMm / float(self.outputImageSpacing[0])
      self.topLeftPixel = [self.transducerCenterPixel[0] - 0.5 * float(self.imageWidthPixel), self.transducerCenterPixel[1]]
      self.scanlineSpacingPixels = self.imageWidthPixel / float(self.numberOfScanlines)
      self.scanlineLengthPixels = self.imagingDepthMm / self.outputImageSpacing[1]

  def scanlineEndPoints(self, scanline):
    import math
    # Compute curvilinear xy values
    if (self.transducerGeometry == "CURVILINEAR"):

      # Compute angle for desired scanline
      angle = self.thetaStartDeg + scanline * self.degreesPerScanline
      angleRadians = math.pi * angle / 180

      # Compute the starting point
      startScanlineX = self.circleCenter[0] + math.sin(angleRadians) * self.radiusStartMm / self.outputImageSpacing[0]
      startScanlineY = self.circleCenter[1] + math.cos(angleRadians) * self.radiusStartMm / self.outputImageSpacing[1]

      # Compute the ending point
      endScanlineX = self.circleCenter[0] + math.sin(angleRadians) * self.radiusStopMm / self.outputImageSpacing[0]
      endScanlineY = self.circleCenter[1] + math.cos(angleRadians) * self.radiusStopMm / self.outputImageSpacing[1]
    # Compute linear xy values
    elif (self.transducerGeometry == "LINEAR"):
      # Compute the starting point
      startScanlineX = self.topLeftPixel[0] + scanline * self.scanlineSpacingPixels
      startScanlineY = self.topLeftPixel[1]

      # Compute the end point
      endScanlineX = startScanlineX # Vertical line so same 'x' value
      endScanlineY = self.topLeftPixel[1] + self.scanlineLengthPixels
    else:
      # ERROR: should not reach here
      print("Error in scanlineEndPoints")

    # Combine XY values and return
    startScanline = [startScanlineX, startScanlineY]
    endScanline = [endScanlineX, endScanlineY]

    return [startScanline, endScanline]

class Scanline():

  def __init__(self, startPoint, endPoint):
    self.startPoint = startPoint
    self.endPoint = endPoint
    self.meanPoints = []
    self.falseNegativeRegions = []
    self.truePositiveRegions = []

class USGeometryTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_USGeometry_CreateScanlines()
    self.test_USGeometry_SumManualSegmentations()

  def compareVolumes(self, volume1, volume2):
    subtractFilter = vtk.vtkImageMathematics()
    subtractFilter.SetOperationToSubtract()
    subtractFilter.SetInput1Data(volume1.GetImageData())
    subtractFilter.SetInput2Data(volume2.GetImageData())
    subtractFilter.Update()

    histogramFilter = vtk.vtkImageAccumulate()
    histogramFilter.SetComponentSpacing([1,0,0])
    histogramFilter.SetInputData(subtractFilter.GetOutput())
    histogramFilter.Update()

    # Both should be zero if generated scanlines == groundtruth
    maxValue = histogramFilter.GetMax()
    minValue = histogramFilter.GetMin()

    if (maxValue[0] == 0 and minValue[0] == 0):
      return True
    else:
      return False

  def test_USGeometry_CreateScanlines(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting CreateScanlines test")

    # Setup testing data
    import urllib
    xmlFileName = 'SpineUltrasound-Lumbar-C5_config.xml'
    testDataPath = 'https://raw.githubusercontent.com/Mattel/USBoneSegmentation/master/USGeometry/Testing/Data/Curvilinear/'
    downloads = (
        (testDataPath+'SpineUltrasound-Lumbar-C5-Trimmed.mha', 'SpineUltrasound-Lumbar-C5-Trimmed.mha', slicer.util.loadLabelVolume),
        (testDataPath+'SpineUltrasound-Lumbar-C5_config.xml', xmlFileName, None),
        (testDataPath+'GroundTruth/SpineUltrasound-Lumbar-C5_Scanline_GroundTruth.mha', 'Curvilinear_Scanline_GroundTruth.mha', slicer.util.loadLabelVolume)
        )

    # Load testing data
    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="SpineUltrasound-Lumbar-C5-Trimmed")
    groundTruthNode = slicer.util.getNode(pattern="Curvilinear_Scanline_GroundTruth")
    logic = USGeometryLogic(slicer.app.temporaryPath+'/'+xmlFileName, volumeNode)
    scanlineNode = slicer.vtkMRMLLabelMapVolumeNode()
    scanlineNode.SetName("Scanline_Test")
    slicer.mrmlScene.AddNode(scanlineNode)
    scanlineDisplayNode = slicer.vtkMRMLLabelMapVolumeDisplayNode()
    colorNode = slicer.util.getNode('GenericAnatomyColors')
    scanlineDisplayNode.SetAndObserveColorNodeID(colorNode.GetID())
    slicer.mrmlScene.AddNode(scanlineDisplayNode)
    scanlineNode.AddAndObserveDisplayNodeID(scanlineDisplayNode.GetID())
    self.delayDisplay("Running createScanlines...")
    logic.createScanlines(scanlineNode)

    volumeEqualityCheck = self.compareVolumes(groundTruthNode, scanlineNode)
    if volumeEqualityCheck == True:
      self.delayDisplay('Scanline test passed!')
    else:
      self.delayDisplay('Scanline test failed!')

  def test_USGeometry_SumManualSegmentations(self):
    self.delayDisplay("Starting SumManualSegmentations test")

    import urllib
    xmlFileName = 'SpineUltrasound-Lumbar-C5_config.xml'
    testDataPath = 'https://raw.githubusercontent.com/Mattel/USBoneSegmentation/master/USGeometry/Testing/Data/Curvilinear/'
    downloads = (
      (testDataPath+'SpineUltrasound-Lumbar-C5-Trimmed.mha', 'SpineUltrasound-Lumbar-C5-Trimmed.mha', slicer.util.loadLabelVolume),
      (testDataPath+'SpineUltrasound-Lumbar-C5_config.xml', xmlFileName, None),
      (testDataPath+'TestManualSegmentations/SpineUltrasound-Lumbar-C5-TestSeg1.mha', 'TestManualSegmentations/SpineUltrasound-Lumbar-C5-TestSeg1.mha', slicer.util.loadLabelVolume),
      (testDataPath+'TestManualSegmentations/SpineUltrasound-Lumbar-C5-TestSeg2.mha', 'TestManualSegmentations/SpineUltrasound-Lumbar-C5-TestSeg2.mha', slicer.util.loadLabelVolume),
      (testDataPath+'TestManualSegmentations/SpineUltrasound-Lumbar-C5-TestSeg3.mha', 'TestManualSegmentations/SpineUltrasound-Lumbar-C5-TestSeg3.mha', slicer.util.loadLabelVolume),
      (testDataPath+'GroundTruth/SummedManualSegmentations_GroundTruth.mha','SummedManualSegmentations_GroundTruth.mha', slicer.util.loadLabelVolume)
      )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        directoryName = os.path.dirname(filePath)
        if not os.path.exists(directoryName):
          os.makedirs(directoryName)
        logging.info('Requesting download %s from %s...\n' % (name,url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with downloading and loading')

    volumeNode = slicer.util.getNode(pattern="SpineUltrasound-Lumbar-C5-Trimmed")
    groundTruthNode = slicer.util.getNode(pattern="SummedManualSegmentations_GroundTruth")
    logic = USGeometryLogic(slicer.app.temporaryPath+'/'+xmlFileName, volumeNode)
    summedManualSegNode = slicer.vtkMRMLLabelMapVolumeNode()
    summedManualSegNode.SetName("SummedManualSegmentations_Test")
    slicer.mrmlScene.AddNode(summedManualSegNode)
    summedManualSegDisplayNode = slicer.vtkMRMLLabelMapVolumeDisplayNode()
    colorNode = slicer.util.getNode('GenericAnatomyColors')
    summedManualSegDisplayNode.SetAndObserveColorNodeID(colorNode.GetID())
    slicer.mrmlScene.AddNode(summedManualSegDisplayNode)
    summedManualSegNode.AddAndObserveDisplayNodeID(summedManualSegDisplayNode.GetID())

    self.delayDisplay("Running sumManualSegmentations...")
    logic.sumManualSegmentations(slicer.app.temporaryPath+'/TestManualSegmentations', summedManualSegNode)

    volumeEqualityCheck = self.compareVolumes(groundTruthNode, summedManualSegNode)
    if volumeEqualityCheck == True:
      self.delayDisplay("Summed manual segmentations test passed!")
    else:
      self.delayDisplay("Summed manual segmentations test failed!")

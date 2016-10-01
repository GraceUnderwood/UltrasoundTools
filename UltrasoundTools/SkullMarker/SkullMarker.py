import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

#
# SkullMarker
#

class SkullMarker(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "SkullMarker" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Ultrasound"]
    self.parent.dependencies = []
    self.parent.contributors = ["Tamas Ungi (Perk Lab)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    This module creates fiducial points on skull surfaces as scanned using ultrasound.
    """
    self.parent.acknowledgementText = """
    Perk Lab
""" # replace with organization, grant and thanks.

#
# SkullMarkerWidget
#

class SkullMarkerWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    #
    # Inputs Area
    #
    inputsCollapsibleButton = ctk.ctkCollapsibleButton()
    inputsCollapsibleButton.text = "Inputs"
    self.layout.addWidget(inputsCollapsibleButton)

    # Layout within the dummy collapsible button
    inputsFormLayout = qt.QFormLayout(inputsCollapsibleButton)

    #
    # input volume selector
    #
    self.inputSelector = slicer.qMRMLNodeComboBox()
    self.inputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.inputSelector.selectNodeUponCreation = True
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = False
    self.inputSelector.noneEnabled = False
    self.inputSelector.showHidden = False
    self.inputSelector.showChildNodeTypes = False
    self.inputSelector.setMRMLScene(slicer.mrmlScene)
    self.inputSelector.setToolTip("Pick the input to the algorithm.")
    inputsFormLayout.addRow("Input Volume: ", self.inputSelector)

    #
    # PLUS configuration file selector
    #
    fileLayout = qt.QHBoxLayout()
    self.configFile = qt.QLineEdit()
    self.configFile.setReadOnly(True)
    self.configFileButton = qt.QPushButton()
    self.configFileButton.setText("Select File")
    fileLayout.addWidget(self.configFile)
    fileLayout.addWidget(self.configFileButton)
    inputsFormLayout.addRow("Configuration file: ", fileLayout)

    #
    # Fiducial node selector
    #
    self.fiducialSelector = slicer.qMRMLNodeComboBox()
    self.fiducialSelector.nodeTypes = (("vtkMRMLMarkupsFiducialNode"), "")
    self.fiducialSelector.addEnabled = True
    self.fiducialSelector.removeEnabled = True
    self.fiducialSelector.renameEnabled = True
    self.fiducialSelector.setMRMLScene(slicer.mrmlScene)
    self.fiducialSelector.setToolTip(
      "Select the fiducial list which will contain fiducials marking bone surfaces along scanlines")
    inputsFormLayout.addRow("Fiducials points: ", self.fiducialSelector)

    #
    # Number of scanlines selector
    #
    self.scanlineNumber = qt.QSpinBox()
    self.scanlineNumber.setMinimum(1)
    self.scanlineNumber.setSingleStep(1)
    inputsFormLayout.addRow("Number of scanlines: ", self.scanlineNumber)

    #
    # Starting depth for fiducial placement
    #
    self.startingDepthMM = qt.QSpinBox()
    self.startingDepthMM.setMinimum(2)  # Bone not before 2mm
    self.startingDepthMM.setSingleStep(1)
    self.startingDepthMM.setSuffix(" mm")
    inputsFormLayout.addRow("Starting fiducial depth: ", self.startingDepthMM)

    #
    # Ending depth for fiducial placement
    #
    self.endingDepthMM = qt.QSpinBox()
    self.endingDepthMM.setMinimum(2)
    self.endingDepthMM.setSingleStep(1)
    self.endingDepthMM.setSuffix(" mm")
    inputsFormLayout.addRow("Ending fiducial depth: ", self.endingDepthMM)

    #
    # Threshold slider
    #
    self.thresholdSlider = ctk.ctkSliderWidget()
    self.thresholdSlider.maximum = 255
    self.thresholdSlider.setDecimals(0)
    inputsFormLayout.addRow("Bone surface threshold: ", self.thresholdSlider)

    #
    # Inputs Area
    #
    functionsCollapsibleButton = ctk.ctkCollapsibleButton()
    functionsCollapsibleButton.text = "Functions"
    self.layout.addWidget(functionsCollapsibleButton)

    # Layout within the dummy collapsible button
    functionsFormLayout = qt.QFormLayout(functionsCollapsibleButton)

    #
    # Configure parameters button
    #
    self.configureParametersButton = qt.QPushButton("Begin configuring threshold")
    self.configureParametersButton.setStyleSheet('QPushButton {background-color: #e67300}')
    self.configureParametersButton.toolTip = "Enables threshold configuration by placing fiducials to see current results, but does not save them"
    self.configureParametersButton.enabled = False
    functionsFormLayout.addRow(self.configureParametersButton)

    #
    # Start fiducial placement button
    #
    self.fiducialPlacementButton = qt.QPushButton("Start fiducial placement")
    self.fiducialPlacementButton.setStyleSheet('QPushButton {background-color: #009900}')
    self.fiducialPlacementButton.toolTip = "Starts and stops fiducial placement on bone surfaces along scanlines."
    self.fiducialPlacementButton.enabled = False
    functionsFormLayout.addRow(self.fiducialPlacementButton)

    # connections
    self.fiducialPlacementButton.connect('clicked(bool)', self.onFiducialPlacementButton)
    self.configureParametersButton.connect('clicked(bool)', self.onConfigureParametersButton)
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onInputSelect)
    self.fiducialSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onInputSelect)
    self.configFileButton.connect('clicked(bool)', self.selectFile)
    self.startingDepthMM.connect('valueChanged(int)', self.validateStartingDepth)
    self.endingDepthMM.connect('valueChanged(int)', self.validateEndingDepth)
    self.thresholdSlider.connect('valueChanged(double)', self.setThreshold)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onInputSelect()

  def cleanup(self):
    pass


  def onInputSelect(self):
    self.fiducialPlacementButton.enabled = self.configureParametersButton.enabled = self.inputSelector.currentNode() and self.fiducialSelector.currentNode() and os.path.isfile(
      self.configFile.text)


  def selectFile(self):
    fileName = qt.QFileDialog().getOpenFileName()
    self.configFile.setText(fileName)
    self.fiducialPlacementButton.enabled = self.configureParametersButton.enabled = self.inputSelector.currentNode() and self.fiducialSelector.currentNode() and os.path.isfile(
      fileName)


  def onFiducialPlacementButton(self):
    logic = ScanlineBoneDetectionLogic(self.configFile.text, self.inputSelector.currentNode(),
                                       self.fiducialSelector.currentNode(), self.startingDepthMM.value,
                                       self.endingDepthMM.value)

    # Validate the number of scanlines
    if (self.scanlineNumber.value > logic.ultrasoundGeometry.numberOfScanlines):
      slicer.util.errorDisplay(
        "The number of scanlines specified exceeds the maximum of: " + str(logic.ultrasoundGeometry.numberOfScanlines))
      return False

    # If fiducials are not being placed, start tracking the volume changes and swtich button to "stop"
    if (logic.changeEvent == 0):
      logic.computeFiducialScanlines(self.scanlineNumber.value)
      logic.trackVolumeChanges(self.inputSelector.currentNode())
      self.fiducialPlacementButton.setStyleSheet('QPushButton {background-color: #cc2900}')
      self.fiducialPlacementButton.setText("Stop fiducial placement")
    # If fiducials are being placed, stop tracking volume changes and switch button to "start"
    else:
      logic.stopTrackingVolumeChanges(self.inputSelector.currentNode())
      self.fiducialPlacementButton.setStyleSheet('QPushButton {background-color: #009900}')
      self.fiducialPlacementButton.setText("Start fiducial placement")


  def onConfigureParametersButton(self):
    logic = ScanlineBoneDetectionLogic(self.configFile.text, self.inputSelector.currentNode(), self.fiducialSelector.currentNode(), self.startingDepthMM.value, self.endingDepthMM.value)

    if (ScanlineBoneDetectionLogic.configuring == 0): # Configuring off, so begin configuration
      ScanlineBoneDetectionLogic.configuring = 1
      logic.computeFiducialScanlines(self.scanlineNumber.value)
      logic.trackVolumeChanges(self.inputSelector.currentNode())
      self.configureParametersButton.setStyleSheet('QPushButton {background-color: #cc2900}')
      self.configureParametersButton.setText("Stop configuring threshold")

    else: # Configuring was on, so stop
      ScanlineBoneDetectionLogic.configuring = 0
      logic.stopTrackingVolumeChanges(self.inputSelector.currentNode())
      self.configureParametersButton.setStyleSheet('QPushButton {background-color: #e67300}')
      self.configureParametersButton.setText("Begin configuring threshold")
      self.fiducialSelector.currentNode().RemoveAllMarkups()


  def validateStartingDepth(self):
    if (self.startingDepthMM.value > self.endingDepthMM.value):
      slicer.util.warningDisplay("Starting depth must be smaller than or equal to ending depth, setting starting depth to equal ending depth.")
      self.startingDepthMM.setValue(self.endingDepthMM.value)


  def validateEndingDepth(self):
    if (self.endingDepthMM.value < self.startingDepthMM.value):
      slicer.util.warningDisplay("Ending depth must be greater than or equal to ending depth, setting ending depth to equal starting depth.")
      self.endingDepthMM.setValue(self.startingDepthMM.value)


  def setThreshold(self):
    ScanlineBoneDetectionLogic.threshold = self.thresholdSlider.value


#
# SkullMarkerLogic
#

class SkullMarkerLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """
  changeEvent = 0
  threshold = 0
  configuring = 0

  def __init__(self, configFile, inputVolume, fiducialNode, startDepth, endDepth):
    import USGeometry
    self.ultrasoundGeometry = USGeometry.USGeometryLogic(configFile, inputVolume)
    self.fiducialNode = fiducialNode
    self.fiducialNode.SetMarkupLabelFormat("")  # Only show markup spheres
    self.fiducialScanlines = []
    self.startingDepthMM = startDepth
    self.endingDepthMM = endDepth
    # Fiducials for bone surface will be placed between these two values
    self.startingDepthPixel = int(self.startingDepthMM / self.ultrasoundGeometry.outputImageSpacing[1])
    self.endingDepthPixel = int(self.endingDepthMM / self.ultrasoundGeometry.outputImageSpacing[1])

  def computeFiducialScanlines(self, scanlineNumber):
    # Find the middle scanline which will always be used
    midScanlineNumber = self.ultrasoundGeometry.numberOfScanlines / 2
    midScanline = self.ultrasoundGeometry.scanlineEndPoints(midScanlineNumber)
    self.fiducialScanlines.append(midScanline)

    # Compute the interval between scanlines for even spacing
    scanlinesPerHalf = scanlineNumber / 2  # How many scanlines there will be per half
    scanlineInterval = 1
    if (scanlinesPerHalf > 0):  # If only 1 scanline there will not be any interval since only middle scanline is used
      scanlineInterval = midScanlineNumber / scanlinesPerHalf  # Number of scanlines to move between each scanline used for fiducials

    # If there is an even number of scanlines an extra scanline will need to be added after loop to make up for offset
    evenNumberOfScanlines = False
    if (scanlineNumber % 2 == 0):
      scanlinesPerHalf -= 1  # Decrease by one otherwise loop would result in an extra scanline
      evenNumberOfScanlines = True
    for i in range(scanlinesPerHalf):
      # Compute and add scanline to right of middle
      rightScanline = self.ultrasoundGeometry.scanlineEndPoints(midScanlineNumber + ((i + 1) * scanlineInterval))
      self.fiducialScanlines.append(rightScanline)
      # Compute and add scanline to left of middle
      leftScanline = self.ultrasoundGeometry.scanlineEndPoints(midScanlineNumber - ((i + 1) * scanlineInterval))
      self.fiducialScanlines.append(leftScanline)

    # If there was an even number of scanlines, add the extra scanline
    if (evenNumberOfScanlines):
      additionalScanline = self.ultrasoundGeometry.scanlineEndPoints(
        midScanlineNumber + ((scanlinesPerHalf + 1) * scanlineInterval))  # Added to right arbitrarily
      self.fiducialScanlines.append(additionalScanline)

  # Starts tracking changes to the input volume
  def trackVolumeChanges(self, inputVolume):
    ScanlineBoneDetectionLogic.changeEvent = inputVolume.AddObserver('ModifiedEvent', self.placeFiducials)

  # Stops tracking changes to the input volume
  def stopTrackingVolumeChanges(self, inputVolume):
    inputVolume.RemoveObserver(ScanlineBoneDetectionLogic.changeEvent)
    ScanlineBoneDetectionLogic.changeEvent = 0

  # Called when input volume has a modified event, will place fiducials on bone surface of fiducial scanlines
  def placeFiducials(self, volumeNode, event):
    if (volumeNode.IsA('vtkMRMLScalarVolumeNode')):
      currentImageData = slicer.util.array(volumeNode.GetName())
      ijkToRas = vtk.vtkMatrix4x4()
      volumeNode.GetIJKToRASMatrix(ijkToRas)
      modifyFlag = self.fiducialNode.StartModify()
      # If configuring, only keep max two frames of scanline fiducials
      if (ScanlineBoneDetectionLogic.configuring == 1 and self.fiducialNode.GetNumberOfFiducials() >= len(
              self.fiducialScanlines) * 2):
        self.fiducialNode.RemoveAllMarkups()
      for i in range(len(self.fiducialScanlines)):
        [scanlineStartPoint, scanlineEndPoint] = self.fiducialScanlines[i]
        # Because we are dealing with linear we can just iterate down a column and do not need to use vtkLineSource as for curvilinear - can be added
        startPoint = (scanlineStartPoint[0], self.startingDepthPixel, 0, 1)
        endPoint = (scanlineEndPoint[0], self.endingDepthPixel, 0, 1)

        # Determine if there is a bone surface point on scanline
        currentScanline = currentImageData[0, :, startPoint[0]]
        boneSurfacePoint = self.scanlineBoneSurfacePoint(currentScanline, startPoint, endPoint,
                                                         ScanlineBoneDetectionLogic.threshold)

        # Add bone surface point fiducial
        if boneSurfacePoint is not None:
          rasBoneSurfacePoint = ijkToRas.MultiplyPoint(boneSurfacePoint)
          self.fiducialNode.AddFiducialFromArray(rasBoneSurfacePoint[:3])

      self.fiducialNode.EndModify(modifyFlag)

  def scanlineBoneSurfacePoint(self, currentScanline, startPoint, endPoint, threshold):
    boneSurfacePoint = None
    boneSurfacePointValue = None
    boneAreaDepth = self.endingDepthPixel - self.startingDepthPixel
    for offset in range(boneAreaDepth):
      currentPixelValue = currentScanline[int(startPoint[1]) + offset]
      # Only consider pixels above specified threshold
      if (currentPixelValue > threshold):
        # Check for artifact
        # ***Note: currently testing w/ magic numbers***
        pointIsNotArtifact = True
        pixelAboveOffset = offset - 3
        pixelBelowOffset = offset + 3
        pixelAboveAverage = currentScanline[int(startPoint[1]) + pixelAboveOffset]
        pixelBelowAverage = currentScanline[int(startPoint[1]) + pixelBelowOffset]
        averageRange = 3
        for i in range(averageRange):
          pixelAboveAverage += currentScanline[int(startPoint[1]) + pixelAboveOffset - i]
          pixelBelowAverage += currentScanline[int(startPoint[1]) + pixelBelowAverage + i]
        pixelAboveAverage /= averageRange
        pixelBelowAverage /= averageRange

        cutoff = currentPixelValue * 0.40
        if (pixelAboveAverage < cutoff and pixelBelowAverage < cutoff):
          pointIsNotArtifact = False

        # Check for intensity increase/decrease (ie ridge)
        pointIsRidge = False
        gradientCheckLength = 5
        aboveDifferenceSum = belowDifferenceSum = 0
        previousAbovePixelValue = previousBelowPixelValue = int(currentPixelValue)
        for i in range(1, gradientCheckLength + 1):  # +1 because we don't consider potential pixel point
          abovePixelValue = int(currentScanline[int(startPoint[1]) + offset - i])
          belowPixelValue = int(currentScanline[int(startPoint[1]) + offset + i])
          aboveDifferenceSum += (previousAbovePixelValue - abovePixelValue)
          currentBelowDifference = belowPixelValue - previousBelowPixelValue
          belowDifferenceSum += (belowPixelValue - previousBelowPixelValue)
          previousAbovePixelValue = abovePixelValue
          previousBelowPixelValue = belowPixelValue

        if (aboveDifferenceSum > 0 and belowDifferenceSum < 0):
          pointIsRidge = True

        if (pointIsNotArtifact and pointIsRidge):
          boneSurfacePoint = (int(startPoint[0]), int(startPoint[1]) + offset, 0, 1)

    return boneSurfacePoint

class SkullMarkerTest(ScriptedLoadableModuleTest):
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
    self.test_SkullMarker1()

  def test_SkullMarker1(self):
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

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = SkullMarkerLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')

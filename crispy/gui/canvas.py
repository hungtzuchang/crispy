# coding: utf-8

import collections
import json
import numpy as np
import os
import sys

from PyQt5.QtCore import QItemSelectionModel, Qt
from PyQt5.QtWidgets import (
    QAbstractItemView, QComboBox, QDockWidget, QDoubleSpinBox, QGridLayout, QLabel, QLineEdit, QListView, QMainWindow,
    QPushButton, QStatusBar, QVBoxLayout, QWidget)

from crispy.gui.treemodel import TreeModel, TreeView
from crispy.gui.listmodel import ListModel
from crispy.gui.spectrum import Spectrum
from crispy.backends.quanty.quanty import Quanty


class DoubleSpinBox(QDoubleSpinBox):
    def __init__(self, *args):
        super(DoubleSpinBox, self).__init__(*args)

    def textFromValue(self, value):
        return '{:8.3f}'.format(value)

class ToolBarComboBox(QComboBox):
    def __init__(self, fixedWidth=70, *args, **kwargs):
        super(ToolBarComboBox, self).__init__(*args, **kwargs)
        self.setFixedWidth(fixedWidth)

    def updateItems(self, items):
        currentText = self.currentText()
        self.blockSignals(True)
        self.clear()
        self.addItems(items)
        try:
            self.setCurrentText(currentText)
        except ValueError:
            self.setCurrentIndex(0)
        self.blockSignals(False)


class MainWindow(QMainWindow):

    _defaults = {'element': 'Ni',
                 'charge': '2+',
                 'experiment': 'XAS',
                 'edge': 'L2,3',
                 'symmetry': 'Oh',
                 'hamiltonianModelData': collections.OrderedDict()}

    def __init__(self):
        super(MainWindow, self).__init__()
        self.__dict__.update(self._defaults)

        self.resize(1260, 680)

        self.loadParameters()

        self.createToolBar()
        self.createHamiltonianWidget()
        self.createHamiltonianParametersWidget()
        self.createExperimentWidget()
        self.createCentralWidget()
        self.createResultsWidget()
        self.createStatusBar()

        self.updateHamiltonianModelData()

    def loadParameters(self):
        dataPath = os.path.join(os.getenv('CRISPY_ROOT'), 'data')

        with open(os.path.join(dataPath, 'parameters.json')) as f:
            self.parameters = json.loads(
                f.read(), object_pairs_hook=collections.OrderedDict)

    def createToolBar(self):
        self.toolBar = self.addToolBar('User selections')

        elements = self.parameters
        self.elementsComboBox = ToolBarComboBox()
        self.elementsComboBox.addItems(elements)
        self.elementsComboBox.setCurrentText(self.element)
        self.elementsComboBox.currentTextChanged.connect(self.updateElement)
        self.toolBar.addWidget(self.elementsComboBox)

        charges = self.parameters[self.element]
        self.chargesComboBox = ToolBarComboBox()
        self.chargesComboBox.addItems(charges)
        self.chargesComboBox.setCurrentText(self.charge)
        self.chargesComboBox.currentTextChanged.connect(self.updateCharge)
        self.toolBar.addWidget(self.chargesComboBox)

        symmetries = ['Oh']
        self.symmetriesComboBox = ToolBarComboBox()
        self.symmetriesComboBox.addItems(symmetries)
        self.symmetriesComboBox.setCurrentText(self.symmetry)
        self.symmetriesComboBox.currentTextChanged.connect(self.updateSymmetry)
        self.toolBar.addWidget(self.symmetriesComboBox)

        experiments = (self.parameters[self.element][self.charge]
                                      ['experiments'])
        self.experimentsComboBox = ToolBarComboBox()
        self.experimentsComboBox.addItems(experiments)
        self.experimentsComboBox.setCurrentText(self.experiment)
        self.experimentsComboBox.currentTextChanged.connect(
            self.updateExperiment)
        self.toolBar.addWidget(self.experimentsComboBox)

        edges = (self.parameters[self.element][self.charge]
                                ['experiments'][self.experiment])
        self.edgesComboBox = ToolBarComboBox()
        self.edgesComboBox.addItems(edges)
        self.edgesComboBox.setCurrentText(self.edge)
        self.edgesComboBox.currentTextChanged.connect(self.updateEdge)
        self.toolBar.addWidget(self.edgesComboBox)

    def createStatusBar(self):
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage('Ready')

    def createHamiltonianWidget(self):
        self.hamiltonianDockWidget = QDockWidget('Hamiltonian', self)
        self.hamiltonianDockWidget.setFeatures(QDockWidget.DockWidgetMovable)

        self.hamiltonianView = QListView()

        self.hamiltonianDockWidget.setWidget(self.hamiltonianView)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.hamiltonianDockWidget)

    def createHamiltonianParametersWidget(self):
        self.hamiltonianParametersDockWidget = QDockWidget(
            'Hamiltonian Parameters', self)
        self.hamiltonianParametersDockWidget.setFeatures(
            QDockWidget.DockWidgetMovable)

        self.hamiltonianParametersView = TreeView()

        self.hamiltonianParametersDockWidget.setWidget(
            self.hamiltonianParametersView)
        self.addDockWidget(Qt.LeftDockWidgetArea,
                           self.hamiltonianParametersDockWidget)

    def createExperimentWidget(self):
        self.experimentDockWidget = QDockWidget('Experiment', self)
        self.experimentDockWidget.setFeatures(QDockWidget.DockWidgetMovable)

        widget = QWidget()

        temperatureLabel = QLabel()
        temperatureLabel.setText('Temperature (K):')

        temperatureLineEdit = QLineEdit()
        temperatureLineEdit.setText('1')
        temperatureLineEdit.setMaximumWidth(40)
        temperatureLineEdit.setAlignment(Qt.AlignRight)

        magneticFieldLabel = QLabel()
        magneticFieldLabel.setText('Magnetic field (T):')

        magneticFieldXLineEdit = QLineEdit()
        magneticFieldXLineEdit.setMaximumWidth(50)
        magneticFieldXLineEdit.setText('0.0')
        magneticFieldXLineEdit.setAlignment(Qt.AlignRight)

        magneticFieldYLineEdit = QLineEdit()
        magneticFieldYLineEdit.setMaximumWidth(50)
        magneticFieldYLineEdit.setText('0.0')
        magneticFieldYLineEdit.setAlignment(Qt.AlignRight)

        magneticFieldZLineEdit = QLineEdit()
        magneticFieldZLineEdit.setMaximumWidth(50)
        magneticFieldZLineEdit.setText('1e-6')
        magneticFieldZLineEdit.setAlignment(Qt.AlignRight)

        broadeningGaussLabel = QLabel()
        broadeningGaussLabel.setText('Gauss broadening (eV):')

        broadeningGaussLineEdit = QLineEdit()
        broadeningGaussLineEdit.setText('0.4')
        broadeningGaussLineEdit.setMaximumWidth(50)
        broadeningGaussLineEdit.setAlignment(Qt.AlignRight)

        broadeningLorentzLabel = QLabel()
        broadeningLorentzLabel.setText('Lorentz broadening (eV):')

        broadeningLorentzLineEdit = QLineEdit()
        broadeningLorentzLineEdit.setText('0.8')
        broadeningLorentzLineEdit.setMaximumWidth(50)
        broadeningLorentzLineEdit.setAlignment(Qt.AlignRight)

        layout = QGridLayout()

        layout.addWidget(temperatureLabel, 0, 0)
        layout.addWidget(temperatureLineEdit, 0, 1)

        layout.addWidget(magneticFieldLabel, 1, 0)
        layout.addWidget(magneticFieldXLineEdit, 1, 1)
        layout.addWidget(magneticFieldYLineEdit, 1, 2)
        layout.addWidget(magneticFieldZLineEdit, 1, 3)

        layout.addWidget(broadeningGaussLabel, 2, 0)
        layout.addWidget(broadeningGaussLineEdit, 2, 1)

        layout.addWidget(broadeningLorentzLabel, 3, 0)
        layout.addWidget(broadeningLorentzLineEdit, 3, 1)

        widget.setLayout(layout)

        self.experimentDockWidget.setWidget(widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.experimentDockWidget)

        # self.tabifyDockWidget(
            # self.hamiltonianDockWidget, self.experimentDockWidget)
        # self.setTabPosition(Qt.LeftDockWidgetArea, QTabWidget.South)
        # self.hamiltonianDockWidget.raise_()

    def createCentralWidget(self):
        self.centralWidget = QWidget(self)

        # Construct the spectrum.
        self.spectrum = Spectrum()

        # Construct the run button.
        self.runButton = QPushButton('Run')
        self.runButton.setFixedWidth(80)
        self.runButton.clicked.connect(self.runCalculation)

        # Set the layout.
        layout = QVBoxLayout(self.centralWidget)
        layout.addWidget(self.spectrum.canvas)
        layout.addWidget(self.runButton)
        self.centralWidget.setLayout(layout)

        self.setCentralWidget(self.centralWidget)

    def createResultsWidget(self):
        self.resultsDockWidget = QDockWidget('Results', self)
        self.resultsDockWidget.setFeatures(QDockWidget.DockWidgetMovable)

        self.resultsModel = ListModel(list())

        self.resultsView = QListView()
        self.resultsView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.resultsView.setModel(self.resultsModel)
        self.resultsView.selectionModel().selectionChanged.connect(
            self.selectedResultsChanged)

        self.resultsDockWidget.setWidget(self.resultsView)
        self.addDockWidget(Qt.RightDockWidgetArea, self.resultsDockWidget)

    def runCalculation(self):
        # Get the most recent data from the model.
        self.hamiltonianModelData = self.hamiltonianModel.getModelData()

        self.backend = 'quanty'

        shells = (self.parameters[self.element][self.charge]
                                 ['experiments'][self.experiment]
                                 [self.edge]['shells'])

        # Load the template file specific to the requested calculation.
        templateFile = os.path.join(
            os.getenv('CRISPY_ROOT'), 'backends', self.backend, 'templates',
            self.symmetry.lower(), self.experiment.lower(),
            ''.join(shells.keys()), 'crystal_field', 'template')

        try:
            template = open(templateFile, 'r').read()
        except IOError:
            print('Template file not available for the requested'
                  'calculation type.')
            return

        for shell in shells:
            template = template.replace('$NElectrons_{0:s}'.format(
                shell), str(shells[shell]))

        hamiltonians = self.hamiltonianModelData
        for hamiltonian in hamiltonians:
            configurations = hamiltonians[hamiltonian]
            for configuration in configurations:
                if 'initial' in configuration.lower():
                    suffix = 'i'
                elif 'final' in configuration.lower():
                    suffix = 'f'
                else:
                    suffix = ''
                parameters = configurations[configuration]
                for parameter in parameters:
                    template = template.replace(
                        '${0:s}_{1:s}'.format(parameter, suffix),
                        '{0:8.4f}'.format(float(parameters[parameter])))

        # Write the input to file.
        inputFile = 'input.inp'
        with open(inputFile, 'w') as f:
            f.write(template)

        # Run Quanty.
        backend = Quanty()
        backend.run(inputFile)

        # Load the data to be plotted.
        label = '{0:s}{1:s} | {2:s} | {3:s} | {4:s} | isotropic'.format(
            self.element, self.charge, self.symmetry, self.experiment,
            self.edge)
        spectrum = np.loadtxt('spectrum.dat', skiprows=5)

        # Plot the spectrum.
        self.spectrum.clear()
        self.spectrum.plot(spectrum[:, 0], -spectrum[:, 2], label)

        # Store the simulation details.
        self.resultsModel.appendItem((label, spectrum, template))

        # Remove generated files.
        os.remove(inputFile)
        os.remove('spectrum.dat')

    def selectedHamiltonianTermChanged(self):
        currentIndex = self.hamiltonianView.selectionModel().currentIndex()
        self.hamiltonianParametersView.setRootIndex(currentIndex)

    def selectedResultsChanged(self):
        selectedIndexes = self.resultsView.selectionModel().selectedIndexes()
        self.spectrum.clear()
        for index in selectedIndexes:
            label, spectrum, _ = self.resultsModel.getIndexData(index)
            self.spectrum.plot(spectrum[:, 0], -spectrum[:, 2], label)

    def updateElement(self):
        self.element = self.elementsComboBox.currentText()
        self.updateCharge()

    def updateCharge(self):
        charges = self.parameters[self.element]
        self.chargesComboBox.updateItems(charges)
        self.charge = self.chargesComboBox.currentText()
        self.updateExperiment()

    def updateSymmetry(self):
        symmetries = ['Oh']
        self.symmetriesComboBox.updateItems(symmetries)
        self.symmetry = self.symmetriesComboBox.currentText()
        self.updateHamiltonianModelData()

    def updateExperiment(self):
        experiments = (self.parameters[self.element][self.charge]
                                      ['experiments'])
        self.experimentsComboBox.updateItems(experiments)
        self.experiment = self.experimentsComboBox.currentText()
        self.updateEdge()

    def updateEdge(self):
        edges = (self.parameters[self.element][self.charge]
                                ['experiments'][self.experiment])
        self.edgesComboBox.updateItems(edges)
        self.edge = self.edgesComboBox.currentText()
        self.updateHamiltonianModelData()

    def updateHamiltonianModelData(self):
        configurations = (self.parameters[self.element][self.charge]
                                         ['experiments'][self.experiment]
                                         [self.edge]['configurations'])

        hamiltonians = (self.parameters[self.element][self.charge]
                                       ['hamiltonians'])

        for hamiltonian in hamiltonians:
            self.hamiltonianModelData[hamiltonian] = collections.OrderedDict()

            if 'Crystal field' in hamiltonian:
                parameters = hamiltonians[hamiltonian][self.symmetry]
            else:
                parameters = hamiltonians[hamiltonian]

            for configuration in configurations:
                label = '{0} conf. ({1})'.format(
                    configuration.capitalize(), configurations[configuration])

                self.hamiltonianModelData[hamiltonian][label] = (
                    parameters[configurations[configuration]])

        # Create the Hamiltonian model.
        self.hamiltonianModel = TreeModel(
            header=['parameter', 'value', 'min', 'max'],
            data=self.hamiltonianModelData)

        # Assign the Hamiltonian model to the Hamiltonian view.
        self.hamiltonianView.setModel(self.hamiltonianModel)
        self.hamiltonianView.selectionModel().setCurrentIndex(
            self.hamiltonianModel.index(0, 0), QItemSelectionModel.Select)
        currentIndex = self.hamiltonianView.selectionModel().currentIndex()
        self.hamiltonianView.selectionModel().selectionChanged.connect(
            self.selectedHamiltonianTermChanged)

        # Assign the Hamiltonian model to the Hamiltonian parameters view, and
        # set some properties.
        self.hamiltonianParametersView.setModel(self.hamiltonianModel)
        self.hamiltonianParametersView.expandAll()
        self.hamiltonianParametersView.resizeAllColumns()
        self.hamiltonianParametersView.setRootIndex(currentIndex)

    def keyPressEvent(self, press):
        if press.key() == Qt.Key_Escape:
            sys.exit()


def main():
    pass

if __name__ == '__main__':
    main()

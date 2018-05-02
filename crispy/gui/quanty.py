# coding: utf-8
# /*##########################################################################
#
# Copyright (c) 2016-2018 European Synchrotron Radiation Facility
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# ###########################################################################*/

from __future__ import absolute_import, division, unicode_literals

__authors__ = ['Marius Retegan']
__license__ = 'MIT'
__date__ = '02/05/2018'


import copy
import datetime
import gzip
import json
import numpy as np
import os
try:
    import cPickle as pickle
except ImportError:
    import pickle
import subprocess
import sys
import uuid

from PyQt5.QtCore import QItemSelectionModel, QProcess, Qt, QPoint
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QAbstractItemView, QDockWidget, QFileDialog, QAction, QMenu, QWidget)
from PyQt5.uic import loadUi
from silx.resources import resource_filename as resourceFileName

from .models.treemodel import TreeModel
from .models.listmodel import ListModel
from ..utils.broaden import broaden
from ..utils.odict import odict


class QuantyCalculation(object):

    # Parameters not loaded from external files should have defaults.
    _defaults = {
        'element': 'Ni',
        'charge': '2+',
        'symmetry': 'Oh',
        'experiment': 'XAS',
        'edge': 'L2,3 (2p)',
        'temperature': 10.0,
        'magneticField': 0.0,
        'kin': np.array([0.0, 0.0, -1.0]),
        'ein1': np.array([0.0, 1.0, 0.0]),
        'kout': np.array([0.0, 0.0, 0.0]),
        'eout1': np.array([0.0, 0.0, 0.0]),
        'calculateIso': 1,
        'calculateCD': 0,
        'calculateLD': 0,
        'nPsisAuto': 1,
        'nConfigurations': 1,
        'fk': 0.8,
        'gk': 0.8,
        'zeta': 1.0,
        'baseName': 'untitled',
        'spectra': None,
        'uuid': None,
        'startingTime': None,
        'endingTime': None,
        'verbosity': None,
    }

    def __init__(self, **kwargs):
        self.__dict__.update(self._defaults)
        self.__dict__.update(kwargs)

        path = resourceFileName(
            'crispy:' + os.path.join('modules', 'quanty', 'parameters',
                                     'parameters.json.gz'))

        with gzip.open(path, 'rb') as p:
            tree = json.loads(
                p.read().decode('utf-8'), object_pairs_hook=odict)

        branch = tree['elements']
        self.elements = list(branch)
        if self.element not in self.elements:
            self.element = self.elements[0]

        branch = branch[self.element]['charges']
        self.charges = list(branch)
        if self.charge not in self.charges:
            self.charge = self.charges[0]

        branch = branch[self.charge]['symmetries']
        self.symmetries = list(branch)
        if self.symmetry not in self.symmetries:
            self.symmetry = self.symmetries[0]

        branch = branch[self.symmetry]['experiments']
        self.experiments = list(branch)
        if self.experiment not in self.experiments:
            self.experiment = self.experiments[0]

        branch = branch[self.experiment]['edges']
        self.edges = list(branch)
        if self.edge not in self.edges:
            self.edge = self.edges[0]

        branch = branch[self.edge]

        self.templateName = branch['template name']

        self.configurations = branch['configurations']
        self.block = self.configurations[0][1][:2]
        self.nElectrons = int(self.configurations[0][1][2:])
        self.nPsis = branch['number of states']
        self.nPsisMax = self.nPsis
        try:
            self.monoElectronicRadialME = (branch[
                'monoelectronic radial matrix elements'])
        except KeyError:
            self.monoElectronicRadialME = None

        self.e1Label = branch['energies'][0][0]
        self.e1Min = branch['energies'][0][1]
        self.e1Max = branch['energies'][0][2]
        self.e1NPoints = branch['energies'][0][3]
        self.e1Edge = branch['energies'][0][4]
        self.e1Lorentzian = branch['energies'][0][5]
        self.e1Gaussian = branch['energies'][0][6]

        if 'RIXS' in self.experiment:
            self.e2Label = branch['energies'][1][0]
            self.e2Min = branch['energies'][1][1]
            self.e2Max = branch['energies'][1][2]
            self.e2NPoints = branch['energies'][1][3]
            self.e2Edge = branch['energies'][1][4]
            self.e2Lorentzian = branch['energies'][1][5]
            self.e2Gaussian = branch['energies'][1][6]

        self.hamiltonianData = odict()
        self.hamiltonianState = odict()

        if (('L2,3 (2p)' in self.edge and 'd' in self.block) or
           ('M4,5 (3d)' in self.edge and 'f' in self.block)):
            self.hasPolarization = True
        else:
            self.hasPolarization = False

        branch = tree['elements'][self.element]['charges'][self.charge]

        for label, configuration in self.configurations:
            label = '{} Hamiltonian'.format(label)
            terms = branch['configurations'][configuration]['terms']

            for term in terms:
                # Include the magnetic and exchange terms only for
                # selected type of calculations.
                if 'Magnetic Field' in term or 'Exchange Field' in term:
                    if not self.hasPolarization:
                        continue

                # Include the p-d hybridization term only for K-edges.
                if '3d-4p Hybridization' in term and 'K (1s)' not in self.edge:
                    continue

                if ('Atomic' in term or 'Magnetic Field' in term
                        or 'Exchange Field' in term):
                    parameters = terms[term]
                else:
                    try:
                        parameters = terms[term][self.symmetry]
                    except KeyError:
                        continue

                # TODO: Use a list? to hold the default scalings.
                for parameter in parameters:
                    if 'Atomic' in term:
                        if parameter[0] in ('F', 'G'):
                            scaling = 0.8
                        else:
                            scaling = 1.0
                    else:
                        scaling = str()

                    self.hamiltonianData[term][label][parameter] = (
                        parameters[parameter], scaling)

                if 'Atomic' in term or 'Crystal Field' in term:
                    self.hamiltonianState[term] = 2
                else:
                    self.hamiltonianState[term] = 0

    def saveInput(self):
        templatePath = resourceFileName(
            'crispy:' + os.path.join('modules', 'quanty', 'templates',
                                     '{}'.format(self.templateName)))

        with open(templatePath) as p:
            self.template = p.read()

        replacements = odict()

        replacements['$Verbosity'] = self.verbosity
        replacements['$NConfigurations'] = self.nConfigurations

        subshell = self.configurations[0][1][:2]
        subshell_occupation = self.configurations[0][1][2:]
        replacements['$NElectrons_{}'.format(subshell)] = subshell_occupation

        replacements['$T'] = self.temperature

        replacements['$Emin1'] = self.e1Min
        replacements['$Emax1'] = self.e1Max
        replacements['$NE1'] = self.e1NPoints
        replacements['$Eedge1'] = self.e1Edge

        if len(self.e1Lorentzian) == 1:
            if self.hasPolarization:
                replacements['$Gamma1'] = '0.1'
                replacements['$Gmin1'] = self.e1Lorentzian[0]
                replacements['$Gmax1'] = self.e1Lorentzian[0]
                replacements['$Egamma1'] = (self.e1Min + self.e1Max) / 2
            else:
                replacements['$Gamma1'] = self.e1Lorentzian[0]
        else:
            if self.hasPolarization:
                replacements['$Gamma1'] = 0.1
                replacements['$Gmin1'] = self.e1Lorentzian[0]
                replacements['$Gmax1'] = self.e1Lorentzian[1]
                if len(self.e1Lorentzian) == 2:
                    replacements['$Egamma1'] = (self.e1Min + self.e1Max) / 2
                else:
                    replacements['$Egamma1'] = self.e1Lorentzian[2]
            else:
                pass

        s = '{{{0:.6g}, {1:.6g}, {2:.6g}}}'
        u = self.kin / np.linalg.norm(self.kin)
        replacements['$kin'] = s.format(u[0], u[1], u[2])

        v = self.ein1 / np.linalg.norm(self.ein1)
        replacements['$ein1'] = s.format(v[0], v[1], v[2])

        # Generate a second, perpendicular, polarization vector to the plane
        # defined by the wave vector and the first polarization vector.
        # TODO: Move this to the Quanty widget.
        w = np.cross(v, u)
        w = w / np.linalg.norm(w)
        replacements['$ein2'] = s.format(w[0], w[1], w[2])

        replacements['$calculateIso'] = self.calculateIso
        replacements['$calculateCD'] = self.calculateCD
        replacements['$calculateLD'] = self.calculateLD

        if 'RIXS' in self.experiment:
            # The Lorentzian broadening along the incident axis cannot be
            # changed in the interface, and must therefore be set to the
            # final value before the start of the calculation.
            # replacements['$Gamma1'] = self.e1Lorentzian
            replacements['$Emin2'] = self.e2Min
            replacements['$Emax2'] = self.e2Max
            replacements['$NE2'] = self.e2NPoints
            replacements['$Eedge2'] = self.e2Edge
            replacements['$Gamma2'] = self.e2Lorentzian[0]

        replacements['$NPsisAuto'] = self.nPsisAuto
        replacements['$NPsis'] = self.nPsis

        for term in self.hamiltonianData:
            if 'Atomic' in term:
                name = 'H_atomic'
            elif 'Crystal Field' in term:
                name = 'H_cf'
            elif '3d-Ligands Hybridization' in term:
                name = 'H_3d_Ld_hybridization'
            elif '3d-4p Hybridization' in term:
                name = 'H_3d_4p_hybridization'
            elif '4d-Ligands Hybridization' in term:
                name = 'H_4d_Ld_hybridization'
            elif '5d-Ligands Hybridization' in term:
                name = 'H_5d_Ld_hybridization'
            elif 'Magnetic Field' in term:
                name = 'H_magnetic_field'
            elif 'Exchange Field' in term:
                name = 'H_exchange_field'
            else:
                pass

            configurations = self.hamiltonianData[term]
            for configuration, parameters in configurations.items():
                if 'Initial' in configuration:
                    suffix = 'i'
                elif 'Intermediate' in configuration:
                    suffix = 'm'
                elif 'Final' in configuration:
                    suffix = 'f'
                for parameter, (value, scaling) in parameters.items():
                    # Convert to parameters name from Greek letters.
                    parameter = parameter.replace('ζ', 'zeta')
                    parameter = parameter.replace('Δ', 'Delta')
                    parameter = parameter.replace('σ', 'sigma')
                    parameter = parameter.replace('τ', 'tau')
                    key = '${}_{}_value'.format(parameter, suffix)
                    replacements[key] = '{}'.format(value)
                    key = '${}_{}_scaling'.format(parameter, suffix)
                    replacements[key] = '{}'.format(scaling)

            checkState = self.hamiltonianState[term]
            if checkState > 0:
                checkState = 1

            replacements['${}'.format(name)] = checkState

        if self.monoElectronicRadialME:
            for parameter in self.monoElectronicRadialME:
                value = self.monoElectronicRadialME[parameter]
                replacements['${}'.format(parameter)] = value

        replacements['$baseName'] = self.baseName

        for replacement in replacements:
            self.template = self.template.replace(
                replacement, str(replacements[replacement]))

        with open(self.baseName + '.lua', 'w') as f:
            f.write(self.template)

        self.uuid = uuid.uuid4().hex[:8]


class QuantyDockWidget(QDockWidget):

    def __init__(self, parent):
        super(QuantyDockWidget, self).__init__(parent)

        # Load the external .ui file for the widget.
        path = resourceFileName(
            'crispy:' + os.path.join('gui', 'uis', 'quanty', 'main.ui'))
        loadUi(path, baseinstance=self, package='crispy.gui')

        self.timeout = 4000
        self.counter = 1

        self.calculation = QuantyCalculation()
        self.setUi()
        self.populateUi()

    def setUi(self):
        # Create the results model and assign it to the view.
        self.resultsModel = ListModel()

        self.resultsView.setModel(self.resultsModel)
        self.resultsView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.resultsView.selectionModel().selectionChanged.connect(
            self.selectedCalculationsChanged)
        # Add a context menu.
        self.resultsView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.resultsView.customContextMenuRequested[QPoint].connect(
            self.showResultsContextMenu)

        # Enable actions.
        self.elementComboBox.currentTextChanged.connect(self.resetCalculation)
        self.chargeComboBox.currentTextChanged.connect(self.resetCalculation)
        self.symmetryComboBox.currentTextChanged.connect(self.resetCalculation)
        self.experimentComboBox.currentTextChanged.connect(
            self.resetCalculation)
        self.edgeComboBox.currentTextChanged.connect(self.resetCalculation)

        self.temperatureLineEdit.editingFinished.connect(
            self.updateTemperature)
        self.magneticFieldLineEdit.editingFinished.connect(
            self.updateMagneticField)

        self.e1MinLineEdit.editingFinished.connect(self.updateE1Min)
        self.e1MaxLineEdit.editingFinished.connect(self.updateE1Max)
        self.e1NPointsLineEdit.editingFinished.connect(self.updateE1NPoints)
        self.e1LorentzianLineEdit.editingFinished.connect(
            self.updateE1Lorentzian)
        self.e1GaussianLineEdit.editingFinished.connect(self.updateE1Gaussian)
        self.kinLineEdit.editingFinished.connect(self.updateIncidentWaveVector)
        self.ein1LineEdit.editingFinished.connect(
            self.updateIncidentPolarizationVector)

        self.e2MinLineEdit.editingFinished.connect(self.updateE2Min)
        self.e2MaxLineEdit.editingFinished.connect(self.updateE2Max)
        self.e2NPointsLineEdit.editingFinished.connect(self.updateE2NPoints)
        self.e2LorentzianLineEdit.editingFinished.connect(
            self.updateE2Lorentzian)
        self.e2GaussianLineEdit.editingFinished.connect(self.updateE2Gaussian)

        self.calculateIsoCheckBox.toggled.connect(
            self.updateSpectraToCalculate)
        self.calculateCDCheckBox.toggled.connect(self.updateSpectraToCalculate)
        self.calculateLDCheckBox.toggled.connect(self.updateSpectraToCalculate)

        self.fkLineEdit.editingFinished.connect(self.updateScalingFactors)
        self.gkLineEdit.editingFinished.connect(self.updateScalingFactors)
        self.zetaLineEdit.editingFinished.connect(self.updateScalingFactors)

        self.syncParametersCheckBox.toggled.connect(self.updateSyncParameters)

        self.nPsisAutoCheckBox.toggled.connect(self.updateNPsisAuto)
        self.nPsisLineEdit.editingFinished.connect(self.updateNPsis)
        self.nConfigurationsLineEdit.editingFinished.connect(
            self.updateConfigurations)

        self.plotIsoCheckBox.toggled.connect(self.plotSelectedCalculations)
        self.plotCDCheckBox.toggled.connect(self.plotSelectedCalculations)
        self.plotLDCheckBox.toggled.connect(self.plotSelectedCalculations)

        icon = QIcon(resourceFileName(
            'crispy:' + os.path.join('gui', 'icons', 'save.svg')))
        self.saveInputAsPushButton.setIcon(icon)
        self.saveInputAsPushButton.clicked.connect(self.saveInputAs)

        icon = QIcon(resourceFileName(
            'crispy:' + os.path.join('gui', 'icons', 'play.svg')))
        self.calculationPushButton.setIcon(icon)
        self.calculationPushButton.clicked.connect(self.runCalculation)

        self.resultsModel.dataChanged.connect(self.plotSelectedCalculations)

    def populateUi(self):
        self.elementComboBox.setItems(
            self.calculation.elements, self.calculation.element)
        self.chargeComboBox.setItems(
            self.calculation.charges, self.calculation.charge)
        self.symmetryComboBox.setItems(
            self.calculation.symmetries, self.calculation.symmetry)
        self.experimentComboBox.setItems(
            self.calculation.experiments, self.calculation.experiment)
        self.edgeComboBox.setItems(
            self.calculation.edges, self.calculation.edge)

        self.temperatureLineEdit.setValue(self.calculation.temperature)
        self.magneticFieldLineEdit.setValue(self.calculation.magneticField)

        if self.calculation.hasPolarization:
            self.magneticFieldLineEdit.setEnabled(True)
            self.kinLineEdit.setEnabled(True)
            self.ein1LineEdit.setEnabled(True)
            self.calculateIsoCheckBox.setEnabled(True)
            self.calculateCDCheckBox.setEnabled(True)
            self.calculateLDCheckBox.setEnabled(True)
        else:
            self.magneticFieldLineEdit.setEnabled(False)
            self.kinLineEdit.setEnabled(False)
            self.ein1LineEdit.setEnabled(False)
            self.calculateIsoCheckBox.setEnabled(True)
            self.calculateCDCheckBox.setEnabled(False)
            self.calculateLDCheckBox.setEnabled(False)

        self.kinLineEdit.setVector(self.calculation.kin)
        self.ein1LineEdit.setVector(self.calculation.ein1)

        self.calculateIsoCheckBox.setChecked(self.calculation.calculateIso)
        self.calculateCDCheckBox.setChecked(self.calculation.calculateCD)
        self.calculateLDCheckBox.setChecked(self.calculation.calculateLD)

        self.fkLineEdit.setValue(self.calculation.fk)
        self.gkLineEdit.setValue(self.calculation.gk)
        self.zetaLineEdit.setValue(self.calculation.zeta)

        self.nPsisLineEdit.setValue(self.calculation.nPsis)
        self.nPsisAutoCheckBox.setChecked(self.calculation.nPsisAuto)
        self.nConfigurationsLineEdit.setValue(self.calculation.nConfigurations)

        self.nConfigurationsLineEdit.setEnabled(False)
        termName = '{}-Ligands Hybridization'.format(self.calculation.block)
        if termName in self.calculation.hamiltonianData:
            termState = self.calculation.hamiltonianState[termName]
            if termState != 0:
                self.nConfigurationsLineEdit.setEnabled(True)

        self.energiesTabWidget.setTabText(0, str(self.calculation.e1Label))
        self.e1MinLineEdit.setValue(self.calculation.e1Min)
        self.e1MaxLineEdit.setValue(self.calculation.e1Max)
        self.e1NPointsLineEdit.setValue(self.calculation.e1NPoints)
        self.e1LorentzianLineEdit.setList(self.calculation.e1Lorentzian)
        self.e1GaussianLineEdit.setValue(self.calculation.e1Gaussian)

        if 'RIXS' in self.calculation.experiment:
            if self.energiesTabWidget.count() == 1:
                tab = self.energiesTabWidget.findChild(QWidget, 'e2Tab')
                self.energiesTabWidget.addTab(tab, tab.objectName())
                self.energiesTabWidget.setTabText(1, self.calculation.e2Label)
            self.e2MinLineEdit.setValue(self.calculation.e2Min)
            self.e2MaxLineEdit.setValue(self.calculation.e2Max)
            self.e2NPointsLineEdit.setValue(self.calculation.e2NPoints)
            self.e2LorentzianLineEdit.setList(self.calculation.e2Lorentzian)
            self.e2GaussianLineEdit.setValue(self.calculation.e2Gaussian)
        else:
            self.energiesTabWidget.removeTab(1)

        # Create a Hamiltonian model.
        self.hamiltonianModel = TreeModel(
            ('Parameter', 'Value', 'Scaling'),
            self.calculation.hamiltonianData)
        self.hamiltonianModel.setNodesCheckState(
            self.calculation.hamiltonianState)
        if self.syncParametersCheckBox.isChecked():
            self.hamiltonianModel.setSyncState(True)
        else:
            self.hamiltonianModel.setSyncState(False)
        self.hamiltonianModel.dataChanged.connect(self.updateHamiltonianData)
        self.hamiltonianModel.nodeCheckStateChanged.connect(
            self.updateHamiltonianNodeCheckState)

        # Assign the Hamiltonian model to the Hamiltonian terms view.
        self.hamiltonianTermsView.setModel(self.hamiltonianModel)
        self.hamiltonianTermsView.selectionModel().setCurrentIndex(
            self.hamiltonianModel.index(0, 0), QItemSelectionModel.Select)
        self.hamiltonianTermsView.selectionModel().selectionChanged.connect(
            self.selectedHamiltonianTermChanged)

        # Assign the Hamiltonian model to the Hamiltonian parameters view.
        self.hamiltonianParametersView.setModel(self.hamiltonianModel)
        self.hamiltonianParametersView.expandAll()
        self.hamiltonianParametersView.resizeAllColumnsToContents()
        self.hamiltonianParametersView.setColumnWidth(0, 130)
        self.hamiltonianParametersView.setRootIndex(
            self.hamiltonianTermsView.currentIndex())

        # Set the sizes of the two views.
        self.hamiltonianSplitter.setSizes((150, 300, 0))

    def enableUi(self, flag=True):
        self.elementComboBox.setEnabled(flag)
        self.chargeComboBox.setEnabled(flag)
        self.symmetryComboBox.setEnabled(flag)
        self.experimentComboBox.setEnabled(flag)
        self.edgeComboBox.setEnabled(flag)

        self.temperatureLineEdit.setEnabled(flag)
        self.magneticFieldLineEdit.setEnabled(flag)

        self.e1MinLineEdit.setEnabled(flag)
        self.e1MaxLineEdit.setEnabled(flag)
        self.e1NPointsLineEdit.setEnabled(flag)
        self.e1LorentzianLineEdit.setEnabled(flag)
        self.e1GaussianLineEdit.setEnabled(flag)

        self.e2MinLineEdit.setEnabled(flag)
        self.e2MaxLineEdit.setEnabled(flag)
        self.e2NPointsLineEdit.setEnabled(flag)
        self.e2LorentzianLineEdit.setEnabled(flag)
        self.e2GaussianLineEdit.setEnabled(flag)

        if self.calculation.hasPolarization:
            self.kinLineEdit.setEnabled(flag)
            self.ein1LineEdit.setEnabled(flag)
            self.calculateIsoCheckBox.setEnabled(flag)
            self.calculateCDCheckBox.setEnabled(flag)
            self.calculateLDCheckBox.setEnabled(flag)
        else:
            self.kinLineEdit.setEnabled(False)
            self.ein1LineEdit.setEnabled(False)
            self.calculateIsoCheckBox.setEnabled(False)
            self.calculateCDCheckBox.setEnabled(False)
            self.calculateLDCheckBox.setEnabled(False)

        self.fkLineEdit.setEnabled(flag)
        self.gkLineEdit.setEnabled(flag)
        self.zetaLineEdit.setEnabled(flag)

        self.syncParametersCheckBox.setEnabled(flag)

        self.nPsisAutoCheckBox.setEnabled(flag)
        if self.nPsisAutoCheckBox.isChecked():
            self.nPsisLineEdit.setEnabled(False)
        else:
            self.nPsisLineEdit.setEnabled(flag)

        self.nConfigurationsLineEdit.setEnabled(flag)

        self.hamiltonianTermsView.setEnabled(flag)
        self.hamiltonianParametersView.setEnabled(flag)
        self.resultsView.setEnabled(flag)

        self.saveInputAsPushButton.setEnabled(flag)

    def updateTemperature(self):
        temperature = self.temperatureLineEdit.getValue()

        if temperature < 0:
            message = 'The temperature cannot be negative.'
            self.getStatusBar().showMessage(message, self.timeout)
            self.temperatureLineEdit.setValue(self.calculation.temperature)
            return
        elif temperature == 0:
            self.nPsisAutoCheckBox.setChecked(False)
            self.updateNPsisAuto()
            self.nPsisLineEdit.setValue(1)
            self.updateNPsis()

        self.calculation.temperature = temperature

    def updateMagneticField(self):
        magneticField = self.magneticFieldLineEdit.getValue()

        if magneticField == 0:
            self.calculation.hamiltonianState['Magnetic Field'] = 0
            self.calculateCDCheckBox.setChecked(False)
        else:
            self.calculation.hamiltonianState['Magnetic Field'] = 2
            self.calculateCDCheckBox.setChecked(True)
        self.hamiltonianModel.setNodesCheckState(
            self.calculation.hamiltonianState)

        # Normalize the current incident vector.
        kin = self.calculation.kin
        kin = kin / np.linalg.norm(kin)

        configurations = self.calculation.hamiltonianData['Magnetic Field']
        for configuration in configurations:
            parameters = configurations[configuration]
            for i, parameter in enumerate(parameters):
                value = magneticField * -kin[i]
                if abs(value) == 0.0:
                    value = 0.0
                configurations[configuration][parameter] = (value, str())
        self.hamiltonianModel.updateModelData(self.calculation.hamiltonianData)

        self.calculation.magneticField = magneticField

    def updateE1Min(self):
        e1Min = self.e1MinLineEdit.getValue()

        if e1Min > self.calculation.e1Max:
            message = ('The lower energy limit cannot be larger than '
                       'the upper limit.')
            self.getStatusBar().showMessage(message, self.timeout)
            self.e1MinLineEdit.setValue(self.calculation.e1Min)
            return

        self.calculation.e1Min = e1Min

    def updateE1Max(self):
        e1Max = self.e1MaxLineEdit.getValue()

        if e1Max < self.calculation.e1Min:
            message = ('The upper energy limit cannot be smaller than '
                       'the lower limit.')
            self.getStatusBar().showMessage(message, self.timeout)
            self.e1MaxLineEdit.setValue(self.calculation.e1Max)
            return

        self.calculation.e1Max = e1Max

    def updateE1NPoints(self):
        e1NPoints = self.e1NPointsLineEdit.getValue()

        e1Min = self.calculation.e1Min
        e1Max = self.calculation.e1Max
        e1LorentzianMin = float(self.calculation.e1Lorentzian[0])

        e1NPointsMin = int(np.floor((e1Max - e1Min) / e1LorentzianMin))
        if e1NPoints < e1NPointsMin:
            message = ('The number of points must be greater than '
                       '{}.'.format(e1NPointsMin))
            self.getStatusBar().showMessage(message, self.timeout)
            self.e1NPointsLineEdit.setValue(self.calculation.e1NPoints)
            return

        self.calculation.e1NPoints = e1NPoints

    def updateE1Lorentzian(self):
        try:
            e1Lorentzian = self.e1LorentzianLineEdit.getList()
        except ValueError:
            message = 'Invalid data for the Lorentzian brodening.'
            self.getStatusBar().showMessage(message, self.timeout)
            self.e1LorentzianLineEdit.setList(self.calculation.e1Lorentzian)
            return

        # Do some validation of the input value.
        if len(e1Lorentzian) > 3:
            message = 'The broadening can have at most three elements.'
            self.getStatusBar().showMessage(message, self.timeout)
            self.e1LorentzianLineEdit.setList(self.calculation.e1Lorentzian)
            return

        try:
            e1LorentzianMin = float(e1Lorentzian[0])
        except IndexError:
            pass
        else:
            if e1LorentzianMin < 0:
                message = 'The broadening cannot be negative.'
                self.getStatusBar().showMessage(message, self.timeout)
                self.e1LorentzianLineEdit.setList(
                    self.calculation.e1Lorentzian)
                return

        try:
            e1LorentzianMax = float(e1Lorentzian[1])
        except IndexError:
            pass
        else:
            if e1LorentzianMax < 0:
                message = 'The broadening cannot be negative.'
                self.getStatusBar().showMessage(message, self.timeout)
                self.e1LorentzianLineEdit.setList(
                    self.calculation.e1Lorentzian)

        try:
            e1LorentzianPivotEnergy = float(e1Lorentzian[2])
        except IndexError:
            pass
        else:
            e1Min = self.calculation.e1Min
            e1Max = self.calculation.e1Max

            if not (e1Min < e1LorentzianPivotEnergy < e1Max):
                message = ('The transition point must lie between the upper '
                           'and lower energy limits.')
                self.getStatusBar().showMessage(message, self.timeout)
                self.e1LorentzianLineEdit.setList(
                    self.calculation.e1Lorentzian)
                return

        self.calculation.e1Lorentzian = e1Lorentzian

    def updateE1Gaussian(self):
        e1Gaussian = self.e1GaussianLineEdit.getValue()

        if e1Gaussian < 0:
            message = 'The broadening cannot be negative.'
            self.getStatusBar().showMessage(message, self.timeout)
            self.e1GaussianLineEdit.setValue(self.calculation.e1Gaussian)
            return

        self.calculation.e1Gaussian = e1Gaussian

        # TODO: Move this to the spectra dialog.
        if not self.calculation.spectra:
            return

        try:
            index = list(self.resultsView.selectedIndexes())[-1]
        except IndexError:
            return
        else:
            self.resultsModel.replaceItem(index,  self.calculation)
            self.plotSelectedCalculations()

    def updateIncidentWaveVector(self):
        try:
            kin = self.kinLineEdit.getVector()
        except ValueError:
            message = 'Invalid data for the wave vector.'
            self.getStatusBar().showMessage(message, self.timeout)
            self.kinLineEdit.setVector(self.calculation.kin)
            return

        if np.all(kin == 0):
            message = 'The wave vector cannot be null.'
            self.getStatusBar().showMessage(message, self.timeout)
            self.kinLineEdit.setVector(self.calculation.kin)
            return

        # The kin value should be fine; save it.
        self.calculation.kin = kin

        # The polarization vector must be correct.
        ein1 = self.ein1LineEdit.getVector()

        # If the wave and polarization vectors are not perpendicular, select a
        # new perpendicular vector for the polarization.
        if np.dot(kin, ein1) != 0:
            if kin[2] != 0 or (-kin[0] - kin[1]) != 0:
                ein1 = np.array([kin[2], kin[2], -kin[0] - kin[1]])
            else:
                ein1 = np.array([-kin[2] - kin[1], kin[0], kin[0]])
            self.ein1LineEdit.setVector(ein1)

        self.calculation.ein1 = ein1

    def updateIncidentPolarizationVector(self):
        try:
            ein1 = self.ein1LineEdit.getVector()
        except ValueError:
            message = 'Invalid data for the polarization vector.'
            self.getStatusBar().showMessage(message, self.timeout)
            self.ein1LineEdit.setVector(self.calculation.ein1)
            return

        if np.all(ein1 == 0):
            message = 'The polarization vector cannot be null.'
            self.getStatusBar().showMessage(message, self.timeout)
            self.ein1LineEdit.setVector(self.calculation.ein1)
            return

        kin = self.calculation.kin
        if np.dot(kin, ein1) != 0:
            message = ('The wave and polarization vectors need to be '
                       'perpendicular.')
            self.getStatusBar().showMessage(message, self.timeout)
            self.ein1LineEdit.setVector(self.calculation.ein1)
            return

        self.calculation.ein1 = ein1

    def updateE2Min(self):
        e2Min = self.e2MinLineEdit.getValue()

        if e2Min > self.calculation.e2Max:
            message = ('The lower energy limit cannot be larger than '
                       'the upper limit.')
            self.getStatusBar().showMessage(message, self.timeout)
            self.e2MinLineEdit.setValue(self.calculation.e2Min)
            return

        self.calculation.e2Min = e2Min

    def updateE2Max(self):
        e2Max = self.e2MaxLineEdit.getValue()

        if e2Max < self.calculation.e2Min:
            message = ('The upper energy limit cannot be smaller than '
                       'the lower limit.')
            self.getStatusBar().showMessage(message, self.timeout)
            self.e2MaxLineEdit.setValue(self.calculation.e2Max)
            return

        self.calculation.e2Max = e2Max

    def updateE2NPoints(self):
        e2NPoints = self.e2NPointsLineEdit.getValue()

        e2Min = self.calculation.e2Min
        e2Max = self.calculation.e2Max
        e2LorentzianMin = float(self.calculation.e2Lorentzian[0])

        e2NPointsMin = int(np.floor((e2Max - e2Min) / e2LorentzianMin))
        if e2NPoints < e2NPointsMin:
            message = ('The number of points must be greater than '
                       '{}.'.format(e2NPointsMin))
            self.getStatusBar().showMessage(message, self.timeout)
            self.e2NPointsLineEdit.setValue(self.calculation.e2NPoints)
            return

        self.calculation.e2NPoints = e2NPoints

    def updateE2Lorentzian(self):
        try:
            e2Lorentzian = self.e2LorentzianLineEdit.getList()
        except ValueError:
            message = 'Invalid data for the Lorentzian brodening.'
            self.getStatusBar().showMessage(message, self.timeout)
            self.e2LorentzianLineEdit.setList(self.calculation.e2Lorentzian)
            return

        # Do some validation of the input value.
        if len(e2Lorentzian) > 3:
            message = 'The broadening can have at most three elements.'
            self.getStatusBar().showMessage(message, self.timeout)
            self.e2LorentzianLineEdit.setList(self.calculation.e2Lorentzian)
            return

        try:
            e2LorentzianMin = float(e2Lorentzian[0])
        except IndexError:
            pass
        else:
            if e2LorentzianMin < 0:
                message = 'The broadening cannot be negative.'
                self.getStatusBar().showMessage(message, self.timeout)
                self.e2LorentzianLineEdit.setList(
                    self.calculation.e2Lorentzian)
                return

        try:
            e2LorentzianMax = float(e2Lorentzian[1])
        except IndexError:
            pass
        else:
            if e2LorentzianMax < 0:
                message = 'The broadening cannot be negative.'
                self.getStatusBar().showMessage(message, self.timeout)
                self.e2LorentzianLineEdit.setList(
                    self.calculation.e2Lorentzian)

        try:
            e2LorentzianPivotEnergy = float(e2Lorentzian[2])
        except IndexError:
            pass
        else:
            e2Min = self.calculation.e2Min
            e2Max = self.calculation.e2Max

            if not (e2Min < e2LorentzianPivotEnergy < e2Max):
                message = ('The transition point must lie between the upper '
                           'and lower energy limits.')
                self.getStatusBar().showMessage(message, self.timeout)
                self.e2LorentzianLineEdit.setList(
                    self.calculation.e2Lorentzian)
                return

        self.calculation.e2Lorentzian = list(map(float, e2Lorentzian))

    def updateE2Gaussian(self):
        e2Gaussian = self.e2GaussianLineEdit.getValue()

        if e2Gaussian < 0:
            message = 'The broadening cannot be negative.'
            self.getStatusBar().showMessage(message, self.timeout)
            self.e2GaussianLineEdit.setValue(self.calculation.e2Gaussian)
            return

        self.calculation.e2Gaussian = e2Gaussian

        # TODO: Move this to the spectra dialog.
        if not self.calculation.spectra:
            return

        try:
            index = list(self.resultsView.selectedIndexes())[-1]
        except IndexError:
            return
        else:
            self.resultsModel.replaceItem(index,  self.calculation)
            self.plotSelectedCalculations()

    def updateSpectraToCalculate(self):
        self.calculation.calculateIso = int(
            self.calculateIsoCheckBox.isChecked())
        self.calculation.calculateCD = int(
            self.calculateCDCheckBox.isChecked())
        self.calculation.calculateLD = int(
            self.calculateLDCheckBox.isChecked())

    def updateScalingFactors(self):
        fk = self.fkLineEdit.getValue()
        gk = self.gkLineEdit.getValue()
        zeta = self.zetaLineEdit.getValue()

        if fk < 0 or gk < 0 or zeta < 0:
            message = 'The scaling factors cannot be negative.'
            self.getStatusBar().showMessage(message, self.timeout)
            self.fkLineEdit.setValue(self.calculation.fk)
            self.gkLineEdit.setValue(self.calculation.gk)
            self.zetaLineEdit.setValue(self.calculation.zeta)
            return

        self.calculation.fk = fk
        self.calculation.gk = gk
        self.calculation.zeta = zeta

        # FIXME: This should be already updated to the most recent data.
        # self.calculation.hamiltonianData = self.hamiltonianModel.getModelData() # noqa
        terms = self.calculation.hamiltonianData

        for term in terms:
            if 'Atomic' not in term:
                continue
            configurations = terms[term]
            for configuration in configurations:
                parameters = configurations[configuration]
                for parameter in parameters:
                    value, scaling = parameters[parameter]
                    if parameter.startswith('F'):
                        terms[term][configuration][parameter] = (value, fk)
                    elif parameter.startswith('G'):
                        terms[term][configuration][parameter] = (value, gk)
                    elif parameter.startswith('ζ'):
                        terms[term][configuration][parameter] = (value, zeta)
                    else:
                        continue
        self.hamiltonianModel.updateModelData(self.calculation.hamiltonianData)
        # I have no idea why this is needed. Both views should update after
        # the above function call.
        self.hamiltonianTermsView.viewport().repaint()
        self.hamiltonianParametersView.viewport().repaint()

    def updateNPsisAuto(self):
        nPsisAuto = int(self.nPsisAutoCheckBox.isChecked())

        if nPsisAuto:
            self.nPsisLineEdit.setValue(self.calculation.nPsisMax)
            self.nPsisLineEdit.setEnabled(False)
        else:
            self.nPsisLineEdit.setEnabled(True)

        self.calculation.nPsisAuto = nPsisAuto

    def updateNPsis(self):
        nPsis = self.nPsisLineEdit.getValue()

        if nPsis <= 0:
            message = 'The number of states must be larger than zero.'
            self.getStatusBar().showMessage(message, self.timeout)
            self.nPsisLineEdit.setValue(self.calculation.nPsis)
        elif nPsis > self.calculation.nPsisMax:
            message = 'The selected number of states exceeds the maximum'
            self.getStatusBar().showMessage(message, self.timeout)
            self.nPsisLineEdit.setValue(self.calculation.nPsisMax)
            nPsis = self.calculation.nPsisMax

        self.calculation.nPsis = nPsis

    def updateSyncParameters(self, flag):
        self.hamiltonianModel.setSyncState(flag)

    def updateHamiltonianData(self):
        self.calculation.hamiltonianData = self.hamiltonianModel.getModelData()

    def updateHamiltonianNodeCheckState(self, index, state):
        hamiltonianState = self.hamiltonianModel.getNodesCheckState()
        self.calculation.hamiltonianState = hamiltonianState

        # If needed, enable the configurations.
        term = '{}-Ligands Hybridization'.format(self.calculation.block)
        if term in index.data():
            if state == 0:
                nConfigurations = 1
                self.nConfigurationsLineEdit.setEnabled(False)
            elif state == 2:
                nConfigurations = 2
                self.nConfigurationsLineEdit.setEnabled(True)

            self.nConfigurationsLineEdit.setValue(nConfigurations)

    def updateConfigurations(self, *args):
        nConfigurations = self.nConfigurationsLineEdit.getValue()

        if 'd' in self.calculation.block:
            nConfigurationsMax = 10 - self.calculation.nElectrons + 1
        elif 'f' in self.calculation.block:
            nConfigurationsMax = 14 - self.calculation.nElectrons + 1
        else:
            return

        if nConfigurations > nConfigurationsMax:
            message = 'The maximum number of configurations is {}.'.format(
                nConfigurationsMax)
            self.getStatusBar().showMessage(message, self.timeout)
            self.nConfigurationsLineEdit.setValue(nConfigurationsMax)
            nConfigurations = nConfigurationsMax

        self.calculation.nConfigurations = nConfigurations

    def saveInput(self):
        # Set the verbosity of the calculation.
        self.calculation.verbosity = self.getVerbosity()

        path = self.getCurrentPath()
        os.chdir(path)

        try:
            self.calculation.saveInput()
        except (IOError, OSError) as e:
            message = 'Cannot write the Quanty input file.'
            self.getStatusBar().showMessage(message)
            return

    def saveInputAs(self):
        path, _ = QFileDialog.getSaveFileName(
            self, 'Save Quanty Input',
            os.path.join(self.getCurrentPath(), '{}.lua'.format(
                self.calculation.baseName)), 'Quanty Input File (*.lua)')

        if path:
            self.saveInput()
            basename = os.path.basename(path)
            self.calculation.baseName, _ = os.path.splitext(basename)
            self.updateMainWindowTitle()
            self.setCurrentPath(path)

    def saveCalculationsAs(self):
        path, _ = QFileDialog.getSaveFileName(
            self, 'Save Calculations',
            os.path.join(self.getCurrentPath(), '{}.pkl'.format(
                self.calculation.baseName)), 'Pickle File (*.pkl)')

        if path:
            calculations = copy.deepcopy(self.resultsModel.getData())
            calculations.reverse()
            with open(path, 'wb') as p:
                pickle.dump(calculations, p, pickle.HIGHEST_PROTOCOL)
            self.setCurrentPath(path)

    def saveSelectedCalculationsAs(self):
        path, _ = QFileDialog.getSaveFileName(
            self, 'Save Calculations',
            os.path.join(self.getCurrentPath(), '{}.pkl'.format(
                self.calculation.baseName)), 'Pickle File (*.pkl)')

        if path:
            calculations = self.getSelectedCalculationsData()
            calculations.reverse()
            with open(path, 'wb') as p:
                pickle.dump(calculations, p, pickle.HIGHEST_PROTOCOL)
            self.setCurrentPath(path)

    def resetCalculation(self):
        element = self.elementComboBox.currentText()
        charge = self.chargeComboBox.currentText()
        symmetry = self.symmetryComboBox.currentText()
        experiment = self.experimentComboBox.currentText()
        edge = self.edgeComboBox.currentText()

        self.calculation = QuantyCalculation(
            element=element, charge=charge, symmetry=symmetry,
            experiment=experiment, edge=edge)

        self.populateUi()
        self.updateMainWindowTitle()
        self.getPlotWidget().reset()
        self.resultsView.selectionModel().clearSelection()

    def removeSelectedCalculations(self):
        self.resultsModel.removeItems(self.resultsView.selectedIndexes())
        self.updateResultsViewSelection()

    def removeCalculations(self):
        self.resultsModel.reset()
        self.getPlotWidget().reset()

    def loadCalculations(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 'Load Calculations',
            self.getCurrentPath(), 'Pickle File (*.pkl)')

        if path:
            with open(path, 'rb') as p:
                self.resultsModel.appendItems(pickle.load(p))
            self.updateResultsViewSelection()
            self.updateMainWindowTitle()
            self.quantyToolBox.setCurrentWidget(self.resultsPage)
            self.setCurrentPath(path)

    def runCalculation(self):
        if not self.getQuantyPath():
            message = 'The path of the Quanty executable is not set.'
            self.getStatusBar().showMessage(message)
            return

        command = self.getQuantyPath()

        # Test the executable.
        with open(os.devnull, 'w') as f:
            try:
                subprocess.call(command, stdout=f, stderr=f)
            except OSError as e:
                if e.errno == os.errno.ENOENT:
                    message = 'The Quanty executable was not found.'
                    self.getStatusBar().showMessage(message)
                    return
                else:
                    raise

        # Write the input file to disk.
        self.saveInput()

        # Disable the UI while the calculation is running.
        self.enableUi(False)

        # Initialize the dictionary holding the spectra.
        self.calculation.spectra = odict()

        self.calculation.startingTime = datetime.datetime.now()

        # Run Quanty using QProcess.
        self.process = QProcess()

        self.process.start(command, (self.calculation.baseName + '.lua', ))
        message = (
            'Running "Quanty {}" in {}.'.format(
                self.calculation.baseName + '.lua', os.getcwd()))
        self.getStatusBar().showMessage(message)

        if sys.platform in 'win32' and self.process.waitForStarted():
            self.updateCalculationPushButton()
        else:
            self.process.started.connect(self.updateCalculationPushButton)
        self.process.readyReadStandardOutput.connect(self.handleOutputLogging)
        self.process.finished.connect(self.processCalculation)

    def updateCalculationPushButton(self, type='stop'):
        types = {
            'stop': {
                'iconName': 'stop.svg',
                'buttonText': 'Stop',
                'buttonToolTip': 'Stop Quanty.'},
            'run': {
                'iconName': 'play.svg',
                'buttonText': 'Run',
                'buttonToolTip': 'Run Quanty.'},
        }

        icon = QIcon(resourceFileName(
            'crispy:' + os.path.join('gui', 'icons', types[type]['iconName'])))
        self.calculationPushButton.setIcon(icon)

        self.calculationPushButton.setText(types[type]['buttonText'])
        self.calculationPushButton.setToolTip(types[type]['buttonToolTip'])

        self.calculationPushButton.disconnect()
        if type == 'stop':
            self.calculationPushButton.clicked.connect(self.stopCalculation)
        elif type == 'run':
            self.calculationPushButton.clicked.connect(self.runCalculation)
        else:
            pass

    def stopCalculation(self):
        self.process.kill()
        self.enableUi(True)

    def processCalculation(self):
        startingTime = self.calculation.startingTime

        # When did I finish?
        endingTime = datetime.datetime.now()
        self.calculation.endingTime = endingTime

        # Reset the calculation button.
        self.updateCalculationPushButton('run')

        # Re-enable the UI if the calculation has finished.
        self.enableUi(True)

        # Evaluate the exit code and status of the process.
        exitStatus = self.process.exitStatus()
        exitCode = self.process.exitCode()

        if exitStatus == 0 and exitCode == 0:
            message = ('Quanty has finished successfully in ')
            delta = int((endingTime - startingTime).total_seconds())
            hours, reminder = divmod(delta, 60)
            minutes, seconds = divmod(reminder, 60)
            if hours > 0:
                message += '{} hours {} minutes and {} seconds.'.format(
                    hours, minutes, seconds)
            elif minutes > 0:
                message += '{} minutes and {} seconds.'.format(
                    minutes, seconds)
            else:
                message += '{} seconds.'.format(seconds)
            self.getStatusBar().showMessage(message, self.timeout)
        elif exitStatus == 0 and exitCode == 1:
            self.handleErrorLogging()
            message = (
                'Quanty has finished unsuccessfully. '
                'Check the logging window for more details.')
            self.getStatusBar().showMessage(message, self.timeout)
            return
        # exitCode is platform dependent; exitStatus is always 1.
        elif exitStatus == 1:
            message = 'Quanty was stopped.'
            self.getStatusBar().showMessage(message, self.timeout)
            return

        self.calculation.label = '#{} | {} | {} | {} | {} | {}'.format(
            self.counter, self.calculation.element, self.calculation.charge,
            self.calculation.symmetry, self.calculation.experiment,
            self.calculation.edge)

        self.counter += 1

        spectraAttributes = list()
        if self.calculateIsoCheckBox.isChecked():
            spectraAttributes.append(('Isotropic', '_iso'))
        if self.calculateCDCheckBox.isChecked():
            spectraAttributes.append(('XMCD', '_cd'))
        if self.calculateLDCheckBox.isChecked():
            spectraAttributes.append(('X(M)LD', '_ld'))

        for spectrumName, spectrumSuffix in spectraAttributes:
            self.readSpectrumData(spectrumName, spectrumSuffix)

        # Store the calculation in the model.
        self.resultsModel.appendItems([self.calculation])

        # Should this be a signal?
        self.updateResultsViewSelection()

        # If the "Hamiltonian Setup" page is currently selected, when the
        # current widget is set to the "Results Page", the former is not
        # displayed. To avoid this I switch first to the "General Setup" page.
        self.quantyToolBox.setCurrentWidget(self.generalPage)
        # Open the results page.
        self.quantyToolBox.setCurrentWidget(self.resultsPage)

    def readSpectrumData(self, spectrumName, spectrumSuffix):
        f = '{0:s}{1:s}.spec'.format(self.calculation.baseName, spectrumSuffix)
        try:
            data = np.loadtxt(f, skiprows=5)
        except IOError as e:
            return

        if 'RIXS' in self.calculation.experiment:
            self.calculation.spectra[spectrumName] = -data[:, 2::2]
        else:
            self.calculation.spectra[spectrumName] = -data[:, 2::2][:, 0]

    def plot(self, spectrumName):
        if spectrumName in self.calculation.spectra:
            data = self.calculation.spectra[spectrumName]
        else:
            return

        # Check if the data is valid.
        if np.max(np.abs(data)) < np.finfo(np.float32).eps:
            message = 'The {} spectrum has very low intensity.'.format(
                spectrumName)
            self.getStatusBar().showMessage(message, self.timeout)
            return

        if 'RIXS' in self.calculation.experiment:
            # Keep the aspect ratio for RIXS plots.
            self.getPlotWidget().setKeepDataAspectRatio(flag=True)
            self.getPlotWidget().setGraphXLabel('Incident Energy (eV)')
            self.getPlotWidget().setGraphYLabel('Energy Transfer (eV)')

            colormap = {'name': 'viridis', 'normalization': 'linear',
                                'autoscale': True, 'vmin': 0.0, 'vmax': 1.0}
            self.getPlotWidget().setDefaultColormap(colormap)

            e1Min = self.calculation.e1Min
            e1Max = self.calculation.e1Max
            e1NPoints = self.calculation.e1NPoints

            e2Min = self.calculation.e2Min
            e2Max = self.calculation.e2Max
            e2NPoints = self.calculation.e2NPoints

            xScale = (e1Max - e1Min) / e1NPoints
            yScale = (e2Max - e2Min) / e2NPoints
            scale = (xScale, yScale)

            xOrigin = e1Min
            yOrigin = e2Min
            origin = (xOrigin, yOrigin)

            z = data

            e1Gaussian = self.calculation.e1Gaussian
            e2Gaussian = self.calculation.e2Gaussian

            if e1Gaussian > 0. and e2Gaussian > 0.:
                xFwhm = e1Gaussian / xScale
                yFwhm = e2Gaussian / yScale

                fwhm = [xFwhm, yFwhm]
                z = broaden(z, fwhm, 'gaussian')

            self.getPlotWidget().addImage(
                z, origin=origin, scale=scale, reset=False)

        else:
            self.getPlotWidget().setKeepDataAspectRatio(flag=False)
            self.getPlotWidget().setGraphXLabel('Absorption Energy (eV)')
            self.getPlotWidget().setGraphYLabel(
                'Absorption Cross Section (a.u.)')

            e1Min = self.calculation.e1Min
            e1Max = self.calculation.e1Max
            e1NPoints = self.calculation.e1NPoints

            scale = (e1Max - e1Min) / e1NPoints

            e1Gaussian = self.calculation.e1Gaussian

            x = np.linspace(e1Min, e1Max, e1NPoints + 1)
            y = data

            fwhm = e1Gaussian / scale
            y = broaden(y, fwhm, 'gaussian')

            legend = '{} | {} | {}'.format(
                self.calculation.label.split()[0], spectrumName,
                self.calculation.uuid)

            try:
                self.getPlotWidget().addCurve(x, y, legend)
            except AssertionError:
                message = 'The x and y arrays have different lengths.'
                self.getStatusBar().showMessage(message)

    def selectedHamiltonianTermChanged(self):
        index = self.hamiltonianTermsView.currentIndex()
        self.hamiltonianParametersView.setRootIndex(index)

    def showResultsContextMenu(self, position):
        icon = QIcon(resourceFileName(
            'crispy:' + os.path.join('gui', 'icons', 'save.svg')))
        self.saveSelectedCalculationsAsAction = QAction(
            icon, 'Save Selected Calculations As...', self,
            triggered=self.saveSelectedCalculationsAs)
        self.saveCalculationsAsAction = QAction(
            icon, 'Save Calculations As...', self,
            triggered=self.saveCalculationsAs)

        icon = QIcon(resourceFileName(
            'crispy:' + os.path.join('gui', 'icons', 'trash.svg')))
        self.removeSelectedCalculationsAction = QAction(
            icon, 'Remove Selected Calculations', self,
            triggered=self.removeSelectedCalculations)
        self.removeCalculationsAction = QAction(
            icon, 'Remove Calculations', self,
            triggered=self.removeCalculations)

        icon = QIcon(resourceFileName(
            'crispy:' + os.path.join('gui', 'icons', 'folder-open.svg')))
        self.loadCalculationsAction = QAction(
            icon, 'Load Calculations', self,
            triggered=self.loadCalculations)

        self.resultsContextMenu = QMenu('Results Context Menu', self)
        self.resultsContextMenu.addAction(
            self.saveSelectedCalculationsAsAction)
        self.resultsContextMenu.addAction(
            self.removeSelectedCalculationsAction)
        self.resultsContextMenu.addSeparator()
        self.resultsContextMenu.addAction(self.saveCalculationsAsAction)
        self.resultsContextMenu.addAction(self.removeCalculationsAction)
        self.resultsContextMenu.addSeparator()
        self.resultsContextMenu.addAction(self.loadCalculationsAction)

        if not self.resultsView.selectedIndexes():
            self.removeSelectedCalculationsAction.setEnabled(False)
            self.saveSelectedCalculationsAsAction.setEnabled(False)

        if not self.resultsModel.getData():
            self.saveCalculationsAsAction.setEnabled(False)
            self.removeCalculationsAction.setEnabled(False)

        self.resultsContextMenu.exec_(self.resultsView.mapToGlobal(position))

    def getSelectedCalculationsData(self):
        calculations = list()
        indexes = self.resultsView.selectedIndexes()
        for index in indexes:
            calculation = copy.deepcopy(self.resultsModel.getIndexData(index))
            calculations.append(calculation)
        return calculations

    def selectedCalculationsChanged(self):
        self.plotSelectedCalculations()
        self.populateUi()
        self.updateMainWindowTitle()

    def plotSelectedCalculations(self):
        self.getPlotWidget().reset()

        spectraName = list()
        if self.plotIsoCheckBox.isChecked():
            spectraName.append('Isotropic')
        if self.plotCDCheckBox.isChecked():
            spectraName.append('XMCD')
        if self.plotLDCheckBox.isChecked():
            spectraName.append('XMLD')

        calculations = self.getSelectedCalculationsData()
        for calculation in calculations:
            self.calculation = calculation
            for spectrumName in spectraName:
                self.plot(spectrumName)

    def updateResultsViewSelection(self):
        self.resultsView.selectionModel().clearSelection()
        index = self.resultsModel.index(self.resultsModel.rowCount() - 1)
        self.resultsView.selectionModel().select(
            index, QItemSelectionModel.Select)
        # Update available actions in the main menu.
        if not self.resultsModel.getData():
            self.updateMenu(False)
        else:
            self.updateMenu(True)

    def handleOutputLogging(self):
        self.process.setReadChannel(QProcess.StandardOutput)
        data = self.process.readAllStandardOutput().data()
        data = data.decode('utf-8').rstrip()
        self.getLoggerWidget().appendPlainText(data)

    def handleErrorLogging(self):
        self.process.setReadChannel(QProcess.StandardError)
        data = self.process.readAllStandardError().data()
        self.getLoggerWidget().appendPlainText(data.decode('utf-8'))

    def updateMainWindowTitle(self):
        title = 'Crispy - {}'.format(self.calculation.baseName + '.lua')
        self.setMainWindowTitle(title)

    def updateMenu(self, flag):
        self.parent().quantyMenuUpdate(flag)

    def setMainWindowTitle(self, title):
        self.parent().setWindowTitle(title)

    def getStatusBar(self):
        return self.parent().statusBar()

    def getPlotWidget(self):
        return self.parent().plotWidget

    def getLoggerWidget(self):
        return self.parent().loggerWidget

    def setCurrentPath(self, path):
        dirname, _ = os.path.split(path)
        self.parent().updateSettings('currentPath', dirname)

    def getCurrentPath(self):
        return self.parent().settings['currentPath']

    def getQuantyPath(self):
        path = self.parent().settings['quanty.path']
        executable = self.parent().settings['quanty.executable']
        return os.path.join(path, executable)

    def getVerbosity(self):
        return self.parent().settings['quanty.verbosity']


if __name__ == '__main__':
    pass

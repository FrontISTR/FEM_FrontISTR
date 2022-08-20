# ***************************************************************************
# *   Copyright (c) 2015 Bernd Hahnebach <bernd@bimstatik.org>              *
# *   Copyright (c) 2022 FrontISTR Commons <https://www.frontistr.com/>     *
# *                                                                         *
# *   This file is part of the FreeCAD CAx development system.              *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

__title__ = "FrontISTR constraint temperature task panel for the document object"
__author__ = "FrontISTR Commons"
__url__ = "https://www.frontistr.com/"

## @package task_fistr_constraint_temperature
#  \ingroup FEM
#  \brief task panel for FrontISTR constraint temperature object

import FreeCAD
import FreeCADGui
from FreeCAD import Units

from femguiutils import selection_widgets
from femtools import femutils
from femtools import membertools


class _TaskPanel(object):

    def __init__(self, obj):
        self._obj = obj

        self._paramWidget = FreeCADGui.PySideUic.loadUi(
            FreeCAD.getUserAppDataDir() + "Mod/FEM_FrontISTR/Resources/TaskFrontISTRConstraintTemperature.ui")
        self._initParamWidget()

        # form made from param and selection widget
        self.form = [self._paramWidget]

        analysis = obj.getParentGroup()
        self._mesh = None
        self._part = None
        if analysis is not None:
            self._mesh = membertools.get_single_member(analysis, "Fem::FemMeshObject")
        if self._mesh is not None:
            self._part = femutils.get_part_to_mesh(self._mesh)
        self._partVisible = None
        self._meshVisible = None

    def open(self):
        if self._mesh is not None and self._part is not None:
            self._meshVisible = self._mesh.ViewObject.isVisible()
            self._partVisible = self._part.ViewObject.isVisible()
            self._mesh.ViewObject.hide()
            self._part.ViewObject.show()

    def reject(self):
        self._restoreVisibility()
        FreeCADGui.ActiveDocument.resetEdit()
        return True

    def accept(self):
        self._applyWidgetChanges()
        self._obj.Document.recompute()
        FreeCADGui.ActiveDocument.resetEdit()
        self._restoreVisibility()
        return True

    def _restoreVisibility(self):
        if self._mesh is not None and self._part is not None:
            if self._meshVisible:
                self._mesh.ViewObject.show()
            else:
                self._mesh.ViewObject.hide()
            if self._partVisible:
                self._part.ViewObject.show()
            else:
                self._part.ViewObject.hide()

    def _initParamWidget(self):
        unit = "K"
        self._paramWidget.if_temperature.setText(
            str(self._obj.Temperature) + unit)

    def _applyWidgetChanges(self):
        unit = "K"
        quantity = Units.Quantity(self._paramWidget.if_temperature.text())
        self._obj.Temperature = quantity.getValueAs(unit).Value

# ***************************************************************************
# *   Copyright (c) 2016 Bernd Hahnebach <bernd@bimstatik.org>              *
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

__title__ = "FrontISTR material creep document object"
__author__ = "FrontISTR Commons"
__url__ = "https://www.frontistr.com/"

from femobjects import base_fempythonobject


class MaterialCreepFISTR(base_fempythonobject.BaseFemPythonObject):
    """
    The MaterialCreepFISTR object
    """

    Type = "Fem::MaterialCreepFISTR"

    def __init__(self, obj):
        super(MaterialCreepFISTR, self).__init__(obj)
        self.add_properties(obj)

    def add_properties(self, obj):
        if not hasattr(obj, "LinearBaseMaterial"):
            obj.addProperty(
                "App::PropertyLink",
                "LinearBaseMaterial",
                "Base",
                "Set the linear material the nonlinear builds upon."
            )

        if not hasattr(obj, "CreepRateCoeff"):
            obj.addProperty(
                "App::PropertyString",
                "CreepRateCoeff",
                "Fem",
                "Set creep rate coefficient 'A' of creep material."
            )
            obj.CreepRateCoeff = "1.0e-10"

        if not hasattr(obj, "StressExponent"):
            obj.addProperty(
                "App::PropertyFloat",
                "StressExponent",
                "Fem",
                "Set stress exponent 'n' of creep material."
            )
            obj.StressExponent = 5.0

        if not hasattr(obj, "TimeExponent"):
            obj.addProperty(
                "App::PropertyFloat",
                "TimeExponent",
                "Fem",
                "Set time exponent 'm' of creep material."
            )
            obj.TimeExponent = 0.0

        if not hasattr(obj, "Temperature"):
            obj.addProperty(
                "App::PropertyFloat",
                "Temperature",
                "Fem",
                "Set temperature of creep material."
            )
            obj.Temperature = 300.0

        if not hasattr(obj, "TemperatureEnabled"):
            obj.addProperty(
                "App::PropertyBool",
                "TemperatureEnabled",
                "Fem",
                "Use temperature of creep material."
            )

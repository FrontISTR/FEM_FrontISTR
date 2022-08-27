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

__title__ = "FrontISTR material viscoelastic document object"
__author__ = "FrontISTR Commons"
__url__ = "https://www.frontistr.com/"

from femobjects import base_fempythonobject


class MaterialViscoelasticFISTR(base_fempythonobject.BaseFemPythonObject):
    """
    The MaterialViscoelasticFISTR object
    """

    Type = "Fem::MaterialViscoelasticFISTR"

    def __init__(self, obj):
        super(MaterialViscoelasticFISTR, self).__init__(obj)
        self.add_properties(obj)

    def add_properties(self, obj):
        if not hasattr(obj, "LinearBaseMaterial"):
            obj.addProperty(
                "App::PropertyLink",
                "LinearBaseMaterial",
                "Base",
                "Set the linear material the nonlinear builds upon."
            )

        if not hasattr(obj, "ShearRelaxationModulus"):
            obj.addProperty(
                "App::PropertyFloat",
                "ShearRelaxationModulus",
                "Fem",
                "Set shear relaxation modulus of viscoelastic material."
            )
            obj.ShearRelaxationModulus = 0.5

        if not hasattr(obj, "RelaxationTime"):
            obj.addProperty(
                "App::PropertyFloat",
                "RelaxationTime",
                "Fem",
                "Set relaxation time of viscoelastic material."
            )
            obj.RelaxationTime = 1.0

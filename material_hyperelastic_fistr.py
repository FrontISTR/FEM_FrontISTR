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

__title__ = "FrontISTR material hyperelastic document object"
__author__ = "FrontISTR Commons"
__url__ = "https://www.frontistr.com/"

from femobjects import base_fempythonobject


class MaterialHyperelasticFISTR(base_fempythonobject.BaseFemPythonObject):
    """
    The MaterialHyperelasticFISTR object
    """

    Type = "Fem::MaterialHyperelasticFISTR"

    def __init__(self, obj):
        super(MaterialHyperelasticFISTR, self).__init__(obj)
        self.add_properties(obj)

    def add_properties(self, obj):
        if not hasattr(obj, "LinearBaseMaterial"):
            obj.addProperty(
                "App::PropertyLink",
                "LinearBaseMaterial",
                "Base",
                "Set the linear material the nonlinear builds upon."
            )

        if not hasattr(obj, "MaterialModelHyperelastic"):
            choices_hyperelastic_material_models = [
                "NEOHOOKE",
                "MOONEY-RIVLIN",
                "ARRUDA-BOYCE",
            ]
            obj.addProperty(
                "App::PropertyEnumeration",
                "MaterialModelHyperelastic",
                "Fem",
                "Set hyperelastic model of hyperelastic material."
            )
            obj.MaterialModelHyperelastic = choices_hyperelastic_material_models
            obj.MaterialModelHyperelastic = choices_hyperelastic_material_models[0]

        if not hasattr(obj, "Constant_C10"):
            obj.addProperty(
                "App::PropertyFloat",
                "Constant_C10",
                "Fem",
                "Set constant 'C10' for NEOHOOKE and MOONEY-RIVLIN models."
            )
            obj.Constant_C10 = 0.1486

        if not hasattr(obj, "Constant_C01"):
            obj.addProperty(
                "App::PropertyFloat",
                "Constant_C01",
                "Fem",
                "Set constant 'C01' for MOONEY-RIVLIN model."
            )
            obj.Constant_C01 = 0.4849

        if not hasattr(obj, "Constant_mu"):
            obj.addProperty(
                "App::PropertyFloat",
                "Constant_mu",
                "Fem",
                "Set constant 'mu' for ARRUDA-BOYCE model."
            )
            obj.Constant_mu = 0.71

        if not hasattr(obj, "Constant_lambda"):
            obj.addProperty(
                "App::PropertyFloat",
                "Constant_lambda",
                "Fem",
                "Set constant 'lambda_m' for ARRUDA-BOYCE model."
            )
            obj.Constant_lambda = 1.7029

        if not hasattr(obj, "Constant_D"):
            obj.addProperty(
                "App::PropertyFloat",
                "Constant_D",
                "Fem",
                "Set constant 'D' for all hyperelastic models."
            )
            obj.Constant_D = 0.0789

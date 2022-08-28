# ***************************************************************************
# *   Copyright (c) 2016 Bernd Hahnebach <bernd@bimstatik.org>              *
# *   Copyright (c) 2020 FrontISTR Commons <https://www.frontistr.com/>     *
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

__title__ = "Objects FrontISTR"
__author__ = "FrontISTR Commons"
__url__ = "https://www.frontistr.com/"

import FreeCAD

def makeSolverFrontISTRTools(
    doc,
    name="SolverFISTRTools"
):
    """makeSolverFrontISTRTools(document, [name]):
    makes a FrontISTR solver object for the fistr tools module"""
    obj = doc.addObject("Fem::FemSolverObjectPython", name)
    import solver_fistrtools
    solver_fistrtools.SolverFISTRTools(obj)
    if FreeCAD.GuiUp:
        import view_solver_fistrtools
        view_solver_fistrtools.VPSolverFrontISTRTools(obj.ViewObject)
    return obj

def makeConstraintTemperatureFrontISTR(
    doc,
    name="ConstraintTemperatureFrontISTR"
):
    """makeConstraintTemperatureFrontISTR(document, [name]):
    makes a FrontISTR constraint temperature object for thermal stress analyses"""
    obj = doc.addObject("Fem::ConstraintPython", name)
    import constraint_temperature_fistr
    constraint_temperature_fistr.ConstraintTemperatureFISTR(obj)
    if FreeCAD.GuiUp:
        import view_constraint_temperature_fistr
        view_constraint_temperature_fistr.VPConstraintTemperatureFrontISTR(obj.ViewObject)
    return obj

def makeMaterialViscoelasticFrontISTR(
    doc,
    base_material,
    name="MaterialViscoelasticFrontISTR"
):
    """makeMaterialViscoelasticFrontISTR(document, base_material, [name]):
    makes a FrontISTR material viscoelastic object"""
    obj = doc.addObject("Fem::FeaturePython", name)
    import material_viscoelastic_fistr
    material_viscoelastic_fistr.MaterialViscoelasticFISTR(obj)
    obj.LinearBaseMaterial = base_material
    if FreeCAD.GuiUp:
        import view_material_viscoelastic_fistr
        view_material_viscoelastic_fistr.VPMaterialViscoelasticFrontISTR(obj.ViewObject)
    return obj

def makeMaterialCreepFrontISTR(
    doc,
    base_material,
    name="MaterialCreepFrontISTR"
):
    """makeMaterialCreepFrontISTR(document, base_material, [name]):
    makes a FrontISTR material creep object"""
    obj = doc.addObject("Fem::FeaturePython", name)
    import material_creep_fistr
    material_creep_fistr.MaterialCreepFISTR(obj)
    obj.LinearBaseMaterial = base_material
    if FreeCAD.GuiUp:
        import view_material_creep_fistr
        view_material_creep_fistr. VPMaterialCreepFrontISTR(obj.ViewObject)
    return obj

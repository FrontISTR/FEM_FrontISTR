# ***************************************************************************
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

__title__="FreeCAD FrontISTR Command Class"
__author__ = "FrontISTR Commons"
__url__ = "https://www.frontistr.com/"

import FreeCAD, FreeCADGui, Mesh, Part, MeshPart, Draft, DraftGeomUtils, os
from FreeCAD import Vector
import math
import numpy as np

if FreeCAD.GuiUp:
    import FreeCADGui
    import Fem
    import FemGui
    from PySide import QtCore, QtGui
    from DraftTools import translate
    from PySide.QtCore import QT_TRANSLATE_NOOP
    from femtools.femutils import is_of_type
else:
    # \cond
    def translate(ctxt,txt, utf8_decode=False):
        return txt
    def QT_TRANSLATE_NOOP(ctxt,txt):
        return txt
    # \endcond

class _CommandFISTRsolver:
    def GetResources(self):
        return {'Pixmap'  : FreeCAD.getUserAppDataDir()+ "Mod/FEM_FrontISTR/Resources/FrontISTR_solver.svg" ,
                'MenuText': QT_TRANSLATE_NOOP("FISTR_solver","FrontISTR Solver"),
                'Accel': "S, X",
                'ToolTip': QT_TRANSLATE_NOOP("FISTR_solver","Creates a FrontISTR solver object")}
                
    def IsActive(self):
        active = (
            FemGui.getActiveAnalysis() is not None
            and self.active_analysis_in_active_doc()
        )
        return active
        #return FreeCADGui.ActiveDocument is not None

    def active_analysis_in_active_doc(self):
        analysis = FemGui.getActiveAnalysis()
        if analysis.Document is FreeCAD.ActiveDocument:
            self.active_analysis = analysis
            return True
        else:
            return False

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create SolverFrontISTR")
        FreeCADGui.addModule("ObjectsFISTR")
        FreeCADGui.addModule("FemGui")
        FreeCADGui.doCommand(
            "FemGui.getActiveAnalysis().addObject(ObjectsFISTR."
            "makeSolverFrontISTRTools(FreeCAD.ActiveDocument))"
        )
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _CommandFISTRConstraintTemperature:
    def GetResources(self):
        return {'Pixmap'  : FreeCAD.getUserAppDataDir()+ "Mod/FEM_FrontISTR/Resources/FrontISTR_ConstraintTemperature.svg" ,
                'MenuText': QT_TRANSLATE_NOOP("FISTR_ConstraintTemperature","FrontISTR constraint temperature"),
                'ToolTip': QT_TRANSLATE_NOOP(
                    "FISTR_ConstraintTemperature",
                    "Creates a FrontISTR constraint for temperature acting on a body"
                )}

    def IsActive(self):  # same as above
        active = (
            FemGui.getActiveAnalysis() is not None
            and self.active_analysis_in_active_doc()
        )
        return active
    
    def active_analysis_in_active_doc(self):  # same as above
        analysis = FemGui.getActiveAnalysis()
        if analysis.Document is FreeCAD.ActiveDocument:
            self.active_analysis = analysis
            return True
        else:
            return False

    def Activated(self):  # do_activated == "add_obj_on_gui_set_edit"
        FreeCAD.ActiveDocument.openTransaction("Create FrontISTR constraint temperature")
        FreeCADGui.addModule("ObjectsFISTR")
        FreeCADGui.addModule("FemGui")
        FreeCADGui.doCommand(
            "FemGui.getActiveAnalysis().addObject(ObjectsFISTR."
            "makeConstraintTemperatureFrontISTR(FreeCAD.ActiveDocument))"
        )
        FreeCADGui.Selection.clearSelection()
        FreeCADGui.doCommand(
            "FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)"
        )
        FreeCAD.ActiveDocument.recompute()

class _CommandFISTRMaterialViscoelastic:
    def GetResources(self):
        return {'Pixmap'  : FreeCAD.getUserAppDataDir()+ "Mod/FEM_FrontISTR/Resources/FrontISTR_MaterialViscoelastic.svg" ,
                'MenuText': QT_TRANSLATE_NOOP("FISTR_MaterialViscoelastic","FrontISTR material viscoelastic"),
                'ToolTip': QT_TRANSLATE_NOOP(
                    "FISTR_MaterialViscoelastic",
                    "Creates a FrontISTR material viscoelastic"
                )}

    def IsActive(self):  # is_active == "with_material_solid"
        active = (
            FemGui.getActiveAnalysis() is not None
            and self.active_analysis_in_active_doc()
            and self.material_solid_selected()
        )
        return active
    
    def active_analysis_in_active_doc(self):  # same as above
        analysis = FemGui.getActiveAnalysis()
        if analysis.Document is FreeCAD.ActiveDocument:
            self.active_analysis = analysis
            return True
        else:
            return False

    def material_solid_selected(self):
        sel = FreeCADGui.Selection.getSelection()
        if (
            len(sel) == 1
            and sel[0].isDerivedFrom("App::MaterialObjectPython")
            and hasattr(sel[0], "Category")
            and sel[0].Category == "Solid"
        ):
            self.selobj = sel[0]
            return True
        else:
            return False

    def Activated(self):
        # see https://github.com/FreeCAD/FreeCAD/blob/master/src/Mod/Fem/femcommands/commands.py#L573
        # test if there is a viscoelastic material which has the selected material as base material
        for o in self.selobj.Document.Objects:
            if (
                is_of_type(o, "Fem::MaterialViscoelasticFISTR")
                and o.LinearBaseMaterial == self.selobj
            ):
                FreeCAD.Console.PrintError(
                    "Viscoelastic material {} is based on the selected material {}. "
                    "Only one viscoelastic object allowed for each material.\n"
                    .format(o.Name, self.selobj.Name)
                )
                return

        # add a viscoelastic material
        string_lin_mat_obj = "FreeCAD.ActiveDocument.getObject('" + self.selobj.Name + "')"
        command_to_run = (
            "FemGui.getActiveAnalysis().addObject(ObjectsFISTR."
            "makeMaterialViscoelasticFrontISTR(FreeCAD.ActiveDocument, {}))"
            .format(string_lin_mat_obj)
        )
        FreeCAD.ActiveDocument.openTransaction("Create FrontISTR material viscoelastic")
        FreeCADGui.addModule("ObjectsFISTR")
        FreeCADGui.addModule("FemGui")
        FreeCADGui.doCommand(command_to_run)
        # set property of the solver to nonlinear
        # (only if one solver is available and if this solver is a FrontISTR solver):
        # The original code assumes that SolverCcxTools is at the top. However, SolverFISTRTools is not placed at the top.
        solver_object = None
        for m in self.active_analysis.Group:
            if not solver_object and is_of_type(m, "Fem::SolverFISTRTools"):
                solver_object = m
                FreeCAD.Console.PrintMessage(
                    "Set Nonlinearity to yes for {}\n"
                    .format(solver_object.Label)
                )
                solver_object.Nonlinearity = "yes"
            else:
                # we do not change attributes if we have more than one solver
                # since we do not know which one to take
                solver_object = None
        FreeCADGui.Selection.clearSelection()
        ### if use taskpanel for viscoelastic
        # FreeCADGui.doCommand(
        #     "FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)"
        # )
        FreeCAD.ActiveDocument.recompute()


class _CommandFISTRMaterialCreep:
    def GetResources(self):
        return {'Pixmap'  : FreeCAD.getUserAppDataDir()+ "Mod/FEM_FrontISTR/Resources/FrontISTR_MaterialCreep.svg" ,
                'MenuText': QT_TRANSLATE_NOOP("FISTR_MaterialCreep","FrontISTR material creep"),
                'ToolTip': QT_TRANSLATE_NOOP(
                    "FISTR_MaterialCreep",
                    "Creates a FrontISTR material creep"
                )}

    def IsActive(self):  # is_active == "with_material_solid"
        active = (
            FemGui.getActiveAnalysis() is not None
            and self.active_analysis_in_active_doc()
            and self.material_solid_selected()
        )
        return active
    
    def active_analysis_in_active_doc(self):  # same as above
        analysis = FemGui.getActiveAnalysis()
        if analysis.Document is FreeCAD.ActiveDocument:
            self.active_analysis = analysis
            return True
        else:
            return False

    def material_solid_selected(self):
        sel = FreeCADGui.Selection.getSelection()
        if (
            len(sel) == 1
            and sel[0].isDerivedFrom("App::MaterialObjectPython")
            and hasattr(sel[0], "Category")
            and sel[0].Category == "Solid"
        ):
            self.selobj = sel[0]
            return True
        else:
            return False

    def Activated(self):
        # see https://github.com/FreeCAD/FreeCAD/blob/master/src/Mod/Fem/femcommands/commands.py#L573
        # test if there is a creep material which has the selected material as base material
        for o in self.selobj.Document.Objects:
            if (
                is_of_type(o, "Fem::MaterialCreepFISTR")
                and o.LinearBaseMaterial == self.selobj
            ):
                FreeCAD.Console.PrintError(
                    "CReep material {} is based on the selected material {}. "
                    "Only one creep object allowed for each material.\n"
                    .format(o.Name, self.selobj.Name)
                )
                return

        # add a creep material
        string_lin_mat_obj = "FreeCAD.ActiveDocument.getObject('" + self.selobj.Name + "')"
        command_to_run = (
            "FemGui.getActiveAnalysis().addObject(ObjectsFISTR."
            "makeMaterialCreepFrontISTR(FreeCAD.ActiveDocument, {}))"
            .format(string_lin_mat_obj)
        )
        FreeCAD.ActiveDocument.openTransaction("Create FrontISTR material creep")
        FreeCADGui.addModule("ObjectsFISTR")
        FreeCADGui.addModule("FemGui")
        FreeCADGui.doCommand(command_to_run)
        # set property of the solver to nonlinear
        # (only if one solver is available and if this solver is a FrontISTR solver):
        # The original code assumes that SolverCcxTools is at the top. However, SolverFISTRTools is not placed at the top.
        solver_object = None
        for m in self.active_analysis.Group:
            if not solver_object and is_of_type(m, "Fem::SolverFISTRTools"):
                solver_object = m
                FreeCAD.Console.PrintMessage(
                    "Set Nonlinearity to yes for {}\n"
                    .format(solver_object.Label)
                )
                solver_object.Nonlinearity = "yes"
            else:
                # we do not change attributes if we have more than one solver
                # since we do not know which one to take
                solver_object = None
        FreeCADGui.Selection.clearSelection()
        FreeCAD.ActiveDocument.recompute()


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('FISTR_solver',_CommandFISTRsolver())
    FreeCADGui.addCommand('FISTR_ConstraintTemperature', _CommandFISTRConstraintTemperature())
    FreeCADGui.addCommand('FISTR_MaterialViscoelastic', _CommandFISTRMaterialViscoelastic())
    FreeCADGui.addCommand('FISTR_MaterialCreep', _CommandFISTRMaterialCreep())

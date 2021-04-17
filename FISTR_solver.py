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


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('FISTR_solver',_CommandFISTRsolver())

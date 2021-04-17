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


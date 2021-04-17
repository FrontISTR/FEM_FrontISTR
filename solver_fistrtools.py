# ***************************************************************************
# *   Copyright (c) 2015 Bernd Hahnebach <bernd@bimstatik.org>              *
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

__title__ = "FreeCAD FEM solver FrontISTR tools document object"
__author__ = "FrontISTR Commons"
__url__ = "https://www.frontistr.com/"

import FreeCAD

from femobjects import base_fempythonobject
from femsolver_FrontISTR.solver import add_attributes


class SolverFISTRTools(base_fempythonobject.BaseFemPythonObject):
    """The Fem::FemSolver's Proxy python type, add solver specific properties
    """

    Type = "Fem::SolverFISTRTools"

    def __init__(self, obj):
        super(SolverFISTRTools, self).__init__(obj)

        fistr_prefs = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Fem/FrontISTR")

        obj.addProperty(
            "App::PropertyPath",
            "WorkingDir",
            "Fem",
            "Working directory for calculations, will only be used it is left blank in preferences"
        )
        # the working directory is not set, the solver working directory is
        # only used if the preferences working directory is left blank

        # add attributes from framework FrontISTR solver
        add_attributes(obj, fistr_prefs)

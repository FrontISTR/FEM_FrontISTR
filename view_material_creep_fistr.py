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

__title__ = "FrontISTR material creep ViewProvider for the document object"
__author__ = "FrontISTR Commons"
__url__ = "https://www.frontistr.com/"

## @package view_material_creep_fistr
#  \ingroup FEM
#  \brief view provider for FrontISTR material creep object

import FreeCAD
from femviewprovider import view_base_femconstraint


class VPMaterialCreepFrontISTR(view_base_femconstraint.VPBaseFemConstraint):
    """
    A View Provider for the FrontISTR material creep object
    """

    def getIcon(self):
        return FreeCAD.getUserAppDataDir()+ "Mod/FEM_FrontISTR/Resources/FrontISTR_MaterialCreep.svg"

    # values with exponential notation cannot be edited from task panels
    # thus we do not use the task panel for FrontISTR material creep

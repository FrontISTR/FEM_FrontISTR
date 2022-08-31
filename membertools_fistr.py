# ***************************************************************************
# *   Copyright (c) 2017 Markus Hovorka <m.hovorka@live.de>                 *
# *   Copyright (c) 2018 Bernd Hahnebach <bernd@bimstatik.org>              *
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


__title__ = "FrontISTR analysis tools"
__author__ = "FrontISTR Commons"
__url__ = "https://www.frontistr.com/"


from femtools import membertools


class AnalysisMemberfistr(membertools.AnalysisMember):

    def __init__(self, analysis):
        super().__init__(analysis)
        """
        # members of the analysis. All except solvers and the mesh

        constraints:
        constraints_temperature_fistr : list of dictionaries
            list of temperatures for the FrontISTR thermal stress analysis.
            [{"Object":temperature_obj, "xxxxxxxx":value}, {}, ...]
        """

        # get member
        # constraints
        # see `constraints_temperature_fistr.py`
        self.cons_temperature_fistr = super().get_several_member(
            "Fem::ConstraintTemperatureFISTR"
        )

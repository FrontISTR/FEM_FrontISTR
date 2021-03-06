# ***************************************************************************
# *   Copyright (c) 2017 Markus Hovorka <m.hovorka@live.de>                 *
# *   Copyright (c) 2017 Bernd Hahnebach <bernd@bimstatik.org>              *
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

__title__ = "FreeCAD FEM solver FrontISTR tasks"
__author__ = "FrontISTR Commons"
__url__ = "https://www.frontistr.com/"

## \addtogroup FEM
#  @{

import os
import os.path
import subprocess

import FreeCAD

from . import writer
from femsolver import run
from femsolver import settings
import importfistrAvsResults
from femtools import femutils
from femtools import membertools


_inputFileName = None


class Check(run.Check):

    def run(self):
        self.pushStatus("Checking analysis...\n")
        self.checkMesh()
        self.checkMaterial()


class Prepare(run.Prepare):

    def run(self):
        global _inputFileName
        self.pushStatus("Preparing input files...\n")
        w = writer.FemInputWriterfistr(
            self.analysis,
            self.solver,
            membertools.get_mesh_to_solve(self.analysis)[0],  # pre check has been done already
            membertools.AnalysisMember(self.analysis),
            self.directory
        )
        path = w.write_FrontISTR_input_file()
        # report to user if task succeeded
        if path != "":
            self.pushStatus("Write completed!")
        else:
            self.pushStatus("Writing FrontISTR input file failed!")
        _inputFileName = os.path.splitext(os.path.basename(path))[0]


class Solve(run.Solve):

    def run(self):
        if not _inputFileName:
            # TODO do not run solver
            # do not try to read results in a smarter way than an Exception
            raise Exception("Error on writing FrontISTR input file.\n")
        self.pushStatus("Executing solver...\n")
        binary = settings.get_binary("FrontISTR")
        self._process = subprocess.Popen(
            [binary, "-i", _inputFileName],
            cwd=self.directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        self.signalAbort.add(self._process.terminate)
        # output = self._observeSolver(self._process)
        self._process.communicate()
        self.signalAbort.remove(self._process.terminate)
        # if not self.aborted:
        #     self._updateOutput(output)
        # del output   # get flake8 quiet


class Results(run.Results):

    def run(self):
        if not _inputFileName:
            # TODO do not run solver
            # do not try to read results in a smarter way than an Exception
            raise Exception("Error on writing FrontISTR input file.\n")
        prefs = FreeCAD.ParamGet(
            "User parameter:BaseApp/Preferences/Mod/Fem/General")
        if not prefs.GetBool("KeepResultsOnReRun", False):
            self.purge_results()
        self.load_results_fistravs()

    def purge_results(self):
        for m in membertools.get_member(self.analysis, "Fem::FemResultObject"):
            if m.Mesh and femutils.is_of_type(m.Mesh, "Fem::MeshResult"):
                self.analysis.Document.removeObject(m.Mesh.Name)
            self.analysis.Document.removeObject(m.Name)
        self.analysis.Document.recompute()

    def load_results_fistravs(self):
        avs_result_file = os.path.join(
            self.directory, _inputFileName + ".avs")
        if os.path.isfile(avs_result_file):
            result_name_prefix = "FrontISTR_" + self.solver.AnalysisType + "_"
            importfistrAvsResults.importAvs(
                avs_result_file, self.analysis, result_name_prefix)
        else:
            raise Exception(
                "FEM: No results found at {}!".format(avs_result_file))

##  @}

# ***************************************************************************
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

__title__ = "FreeCAD FEM solver object FrontISTR"
__author__ = "FrontISTR Commons"
__url__ = "https://www.frontistr.com/"

## @package SolverFrontISTR
#  \ingroup FEM

import glob
import os

import FreeCAD

from . import tasks
from femsolver import run
from femsolver import solverbase
from femtools import femutils

if FreeCAD.GuiUp:
    import FemGui

ANALYSIS_TYPES = ["static", "check"]


def create(doc, name="SolverFrontISTR"):
    return femutils.createObject(
        doc, name, Proxy, ViewProxy)


class Proxy(solverbase.Proxy):
    """The Fem::FemSolver's Proxy python type, add solver specific properties
    """

    Type = "Fem::SolverFrontISTR"

    def __init__(self, obj):
        super(Proxy, self).__init__(obj)
        obj.Proxy = self
        fistr_prefs = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Fem/FrontISTR")
        add_attributes(obj, fistr_prefs)

    def createMachine(self, obj, directory, testmode=False):
        return run.Machine(
            solver=obj, directory=directory,
            check=tasks.Check(),
            prepare=tasks.Prepare(),
            solve=tasks.Solve(),
            results=tasks.Results(),
            testmode=testmode)

    def editSupported(self):
        return True

    def edit(self, directory):
        pattern = os.path.join(directory, "*.inp")
        FreeCAD.Console.PrintMessage("{}\n".format(pattern))
        f = glob.glob(pattern)[0]
        FemGui.open(f)

    def execute(self, obj):
        return


class ViewProxy(solverbase.ViewProxy):
    pass


# helper add properties, this is outside of the class to be able
# to use the attribute setter from framework solver and fistrtools solver.
# some real value parameters are defined not by floating-point numbers but by characters.
# This is because FreeCAD task panel does not accept exponential notation.
def add_attributes(obj, fistr_prefs):

    obj.addProperty(
        "App::PropertyIntegerConstraint",
        "n_process",
        "General",
        "Number of process for palallel execution"
    )
    n_process = fistr_prefs.GetInt("n_process", 4)
    obj.n_process = n_process

    obj.addProperty(
        "App::PropertyEnumeration",
        "AnalysisType",
        "General",
        "Type of the analysis"
    )
    obj.AnalysisType = ANALYSIS_TYPES
    analysis_type = fistr_prefs.GetInt("AnalysisType", 0)
    obj.AnalysisType = ANALYSIS_TYPES[analysis_type]

    choices_nonlinear = ["yes", "no"]
    obj.addProperty(
        "App::PropertyEnumeration",
        "Nonlinearity",
        "General",
        "Set material nonlinearity (needs geometrical nonlinearity)"
    )
    obj.Nonlinearity = choices_nonlinear
    obj.Nonlinearity = choices_nonlinear[1]

    known_fistr_solver_types = [
        "CG",
        "BiCGSTAB",
        "GMRES",
        "GPBiCG",
        "MUMPS",
        "DIRECT"
    ]
    obj.addProperty(
        "App::PropertyEnumeration",
        "MatrixSolverType",
        "General",
        "Type of solver to use"
    )
    obj.MatrixSolverType = known_fistr_solver_types
    solver_type = fistr_prefs.GetInt("Solver", 0)
    obj.MatrixSolverType = known_fistr_solver_types[solver_type]

    known_fistr_precond_types = [
        "SSOR",
        "DIAG",
        "AMG",
        "ILU0",
        "ILU1",
        "ILU2"
    ]
    obj.addProperty(
        "App::PropertyEnumeration",
        "MatrixPrecondType",
        "General",
        "Type of preconditioner to use"
    )
    obj.MatrixPrecondType = known_fistr_precond_types
    precond_type = fistr_prefs.GetInt("Precond", 2)
    obj.MatrixPrecondType = known_fistr_precond_types[precond_type]

    choices_iterlog = ["yes", "no"]
    obj.addProperty(
        "App::PropertyEnumeration",
        "MatrixSolverIterLog",
        "General",
        "Output convergence history of iterative solver"
    )
    obj.MatrixSolverIterLog = choices_iterlog
    iter_log = fistr_prefs.GetString("MatrixSolverIterLog", "no")
    if iter_log != "yes":
        iter_log = "no"
    obj.MatrixSolverIterLog = iter_log

    choices_timelog = ["yes", "no"]
    obj.addProperty(
        "App::PropertyEnumeration",
        "MatrixSolverTimeLog",
        "General",
        "Output execution summary of iterative solver"
    )
    obj.MatrixSolverTimeLog = choices_timelog
    time_log = fistr_prefs.GetString("MatrixSolverTimeLog", "yes")
    if time_log != "no":
        time_log = "yes"
    obj.MatrixSolverTimeLog = time_log

    obj.addProperty(
        "App::PropertyIntegerConstraint",
        "MatrixSolverNumIter",
        "General",
        "Maximum number of iteration (iterative solver only)"
    )
    num_iter = fistr_prefs.GetInt("MatrixSolverNumIter", 5000)
    obj.MatrixSolverNumIter = num_iter

    obj.addProperty(
        "App::PropertyString",
        "MatrixSolverResidual",
        "General",
        "Convergence threshold of iterative solver"
    )
    solver_threshold = fistr_prefs.GetString("MatrixSolverResidual", "1.0e-6")
    obj.MatrixSolverResidual = solver_threshold

    known_fistr_output_format = [
        "AVS",
        "VTK (paraview required)",
        "Binary VTK (paraview required)"
    ]
    obj.addProperty(
        "App::PropertyEnumeration",
        "OutputFileFormat",
        "General",
        "File format of output file."
    )
    obj.OutputFileFormat = known_fistr_output_format
    output_format = fistr_prefs.GetInt("OutputFileFormat", 0)
    obj.OutputFileFormat = known_fistr_output_format[output_format]

    choices_increment_type = ["auto", "fixed"]
    obj.addProperty(
        "App::PropertyEnumeration",
        "IncrementType",
        "Static",
        "Type of time increment. Cutback is available only"
    )
    obj.IncrementType = choices_increment_type
    increment_type = fistr_prefs.GetString("IncrementType", "auto")
    obj.IncrementType = increment_type

    obj.addProperty(
        "App::PropertyFloatConstraint",
        "TimeEnd",
        "Static",
        "Analysis Time End"
    )
    time_end = fistr_prefs.GetFloat("TimeEnd", 1.0)
    obj.TimeEnd = time_end

    obj.addProperty(
        "App::PropertyFloatConstraint",
        "InitialTimeIncrement",
        "Static",
        "Initial Time Increment"
    )
    init_time_increment = fistr_prefs.GetFloat("InitialTimeIncrement", 1.0)
    obj.InitialTimeIncrement = init_time_increment

    obj.addProperty(
        "App::PropertyString",
        "MinimumTimeIncrement",
        "Static",
        "Minimum Time Increment"
    )
    min_time_increment = fistr_prefs.GetString("MinimumTimeIncrement", "1.0e-4")
    obj.MinimumTimeIncrement = min_time_increment

    obj.addProperty(
        "App::PropertyFloatConstraint",
        "MaximumTimeIncrement",
        "Static",
        "Maximum Time Increment"
    )
    max_time_increment = fistr_prefs.GetFloat("MaximumTimeIncrement", 1.0)
    obj.MaximumTimeIncrement = max_time_increment

    obj.addProperty(
        "App::PropertyString",
        "NewtonConvergeResidual",
        "Static",
        "Convergence threshold of Newton iteration"
    )
    newton_res = fistr_prefs.GetString("NewtonConvergeResidual", "1.0e-6")
    obj.NewtonConvergeResidual = newton_res

    obj.addProperty(
        "App::PropertyIntegerConstraint",
        "NewtonMaximumIteration",
        "Static",
        "Maximum number of Newton iteration"
    )
    newton_iter = fistr_prefs.GetInt("NewtonMaximumIteration", 20)
    obj.NewtonMaximumIteration = newton_iter

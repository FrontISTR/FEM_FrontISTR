#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2020                                                    *
#*   FrontISTR Commons https://www.frontistr.com/                          *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

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

ANALYSIS_TYPES = ["static", "frequency", "thermomech", "check"]


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
# to use the attribute setter from framework solver and fistrtools solver
def add_attributes(obj, fistr_prefs):

    obj.addProperty(
        "App::PropertyEnumeration",
        "AnalysisType",
        "Fem",
        "Type of the analysis"
    )
    obj.AnalysisType = ANALYSIS_TYPES
    analysis_type = fistr_prefs.GetInt("AnalysisType", 0)
    obj.AnalysisType = ANALYSIS_TYPES[analysis_type]

    choices_geom_nonlinear = ["linear", "nonlinear"]
    obj.addProperty(
        "App::PropertyEnumeration",
        "GeometricalNonlinearity",
        "Fem",
        "Set geometrical nonlinearity"
    )
    obj.GeometricalNonlinearity = choices_geom_nonlinear
    nonlinear_geom = fistr_prefs.GetBool("NonlinearGeometry", False)
    if nonlinear_geom is True:
        obj.GeometricalNonlinearity = choices_geom_nonlinear[1]  # nonlinear
    else:
        obj.GeometricalNonlinearity = choices_geom_nonlinear[0]  # linear

    choices_material_nonlinear = ["linear", "nonlinear"]
    obj.addProperty(
        "App::PropertyEnumeration",
        "MaterialNonlinearity",
        "Fem",
        "Set material nonlinearity (needs geometrical nonlinearity)"
    )
    obj.MaterialNonlinearity = choices_material_nonlinear
    obj.MaterialNonlinearity = choices_material_nonlinear[0]

    obj.addProperty(
        "App::PropertyIntegerConstraint",
        "EigenmodesCount",
        "Fem",
        "Number of modes for frequency calculations"
    )
    noem = fistr_prefs.GetInt("EigenmodesCount", 30)
    obj.EigenmodesCount = (noem, 1, 100, 1)

    obj.addProperty(
        "App::PropertyFloatConstraint",
        "EigenmodeLowLimit",
        "Fem",
        "Low frequency limit for eigenmode calculations"
    )
    ell = fistr_prefs.GetFloat("EigenmodeLowLimit", 0.0)
    obj.EigenmodeLowLimit = (ell, 0.0, 1000000.0, 10000.0)

    obj.addProperty(
        "App::PropertyFloatConstraint",
        "EigenmodeHighLimit",
        "Fem",
        "High frequency limit for eigenmode calculations"
    )
    ehl = fistr_prefs.GetFloat("EigenmodeHighLimit", 1000000.0)
    obj.EigenmodeHighLimit = (ehl, 0.0, 1000000.0, 10000.0)

    obj.addProperty(
        "App::PropertyFloatConstraint",
        "TimeInitialStep",
        "Fem",
        "Initial time steps"
    )
    ini = fistr_prefs.GetFloat("AnalysisTimeInitialStep", 1.0)
    obj.TimeInitialStep = ini

    obj.addProperty(
        "App::PropertyFloatConstraint",
        "TimeEnd",
        "Fem",
        "End time analysis"
    )
    eni = fistr_prefs.GetFloat("AnalysisTime", 1.0)
    obj.TimeEnd = eni

    obj.addProperty(
        "App::PropertyBool",
        "ThermoMechSteadyState",
        "Fem",
        "Choose between steady state thermo mech or transient thermo mech analysis"
    )
    sted = fistr_prefs.GetBool("StaticAnalysis", True)
    obj.ThermoMechSteadyState = sted

    known_fistr_solver_types = [
        "CG",
        "BiCGSTAB",
        "GMRES",
        "GPBiCG",
        "MUMPS",
        "DIRECTmkl"
    ]
    obj.addProperty(
        "App::PropertyEnumeration",
        "MatrixSolverType",
        "Fem",
        "Type of solver to use"
    )
    obj.MatrixSolverType = known_fistr_solver_types
    solver_type = fistr_prefs.GetInt("Solver", 0)
    obj.MatrixSolverType = known_fistr_solver_types[solver_type]

    known_fistr_precond_types = [
        "AMG",
        "SSOR",
        "DIAGNAL_SCALING",
        "Block ILU(0)",
        "Block ILU(1)",
        "Block ILU(2)"
    ]
    obj.addProperty(
        "App::PropertyEnumeration",
        "MatrixPrecondType",
        "Fem",
        "Type of preconditioner to use"
    )
    obj.MatrixPrecondType = known_fistr_precond_types
    precond_type = fistr_prefs.GetInt("Precond", 0)
    obj.MatrixPrecondType = known_fistr_precond_types[precond_type]

    obj.addProperty(
        "App::PropertyBool",
        "BeamShellResultOutput3D",
        "Fem",
        "Output 3D results for 1D and 2D analysis "
    )
    dimout = fistr_prefs.GetBool("BeamShellOutput", False)
    obj.BeamShellResultOutput3D = dimout

    obj.addProperty(
        "App::PropertyIntegerConstraint",
        "SUBSTEPS",
        "Fem",
        "Number of increment for each step"
    )
    n_substeps = fistr_prefs.GetInt("SUBSTEPS", 1)
    obj.SUBSTEPS = n_substeps

    obj.addProperty(
        "App::PropertyIntegerConstraint",
        "n_process",
        "Fem",
        "Number of process for palallel execution"
    )
    n_process = fistr_prefs.GetInt("n_process", 4)
    obj.n_process = n_process

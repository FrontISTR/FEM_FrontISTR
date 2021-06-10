# ***************************************************************************
# *   Copyright (c) 2015 Przemo Firszt <przemo@firszt.eu>                   *
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

__title__ = "FemToolsfistr"
__author__ = "FrontISTR Commons"
__url__ = "https://www.frontistr.com/"

## \addtogroup FEM
#  @{

import os
import sys
import subprocess

import FreeCAD

from femtools import femutils
from femtools import membertools

from PySide import QtCore  # there might be a special reason this is not guarded ?!?
if FreeCAD.GuiUp:
    from PySide import QtGui
    import FemGui


class FemToolsFISTR(QtCore.QRunnable, QtCore.QObject):
    """

    Attributes
    ----------
    analysis : Fem::FemAnalysis
        FEM group analysis object
        has to be present, will be set in __init__
    solver : Fem::FemSolverObjectPython
        FEM solver object
        has to be present, will be set in __init__
    base_name : str
        name of .inp/.avs file (without extension)
        It is used to construct .inp file path that is passed to FrontISTR fistr
    fistr_binary : str
    working_dir : str
    results_present : bool
        indicating if there are calculation results ready for us
    members : class femtools/membertools/AnalysisMember
        contains references to all analysis member except solvers and mesh
        Updated with update_objects
    """

    finished = QtCore.Signal(int)

    def __init__(self, analysis=None, solver=None, test_mode=False):
        """The constructor

        Parameters
        ----------
        analysis : Fem::FemAnalysis, optional
            analysis group as a container for all  objects needed for the analysis
        solver : Fem::FemSolverObjectPython, optional
            solver object to be used for this solve
        test_mode : bool, optional
            mainly used in unit tests
        """

        QtCore.QRunnable.__init__(self)
        QtCore.QObject.__init__(self)

        self.analysis = None
        self.solver = None

        if analysis:
            self.analysis = analysis
            if solver:
                # analysis and solver given
                self.solver = solver
            else:
                # analysis given, search for the solver
                self.find_solver()
                if not self.solver:
                    raise Exception("FEM: No solver found!")
        else:
            if solver:
                # solver given, search for the analysis
                self.solver = solver
                self.find_solver_analysis()
                if not self.analysis:
                    raise Exception(
                        "FEM: The solver was given as parameter, "
                        "but no analysis for this solver was found!"
                    )
            else:
                # neither analysis nor solver given, search both
                self.find_analysis()
                if not self.analysis:
                    raise Exception(
                        "FEM: No solver was given and either no active analysis "
                        "or no analysis at all or more than one analysis found!"
                    )
                self.find_solver()
                if not self.solver:
                    raise Exception("FEM: No solver found!")

        if self.analysis.Document is not self.solver.Document:
            raise Exception(
                "FEM: The analysis and solver are not in the same document!"
            )
        if self.solver not in self.analysis.Group:
            raise Exception(
                "FEM: The solver is not part of the analysis Group!"
            )

        # print(self.solver)
        # print(self.analysis)
        if self.analysis and self.solver:
            self.working_dir = ""
            self.fistr_binary = ""
            self.base_name = ""
            self.results_present = False
            if test_mode:
                self.test_mode = True
                self.fistr_binary_present = True
            else:
                self.test_mode = False
                self.fistr_binary_present = False
            self.result_object = None
        else:
            raise Exception(
                "FEM: Something went wrong, "
                "the exception should have been raised earlier!"
            )

    def purge_results(self):
        """Remove all result objects and result meshes from an analysis group
        """
        from femresult.resulttools import purge_results as pr
        pr(self.analysis)

    def reset_mesh_purge_results_checked(self):
        """Reset mesh color, deformation and removes all result objects
        if preferences to keep them is not set.
        """
        self.fem_prefs = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Fem/General")
        keep_results_on_rerun = self.fem_prefs.GetBool("KeepResultsOnReRun", False)
        if not keep_results_on_rerun:
            self.purge_results()

    def reset_all(self):
        """Reset mesh color, deformation and removes all result objects
        """
        self.purge_results()

    def _get_several_member(self, obj_type):
        return membertools.get_several_member(self.analysis, obj_type)

    def find_analysis(self):
        if FreeCAD.GuiUp:
            self.analysis = FemGui.getActiveAnalysis()
        if self.analysis:
            return
        found_analysis = False
        # search in the active document
        for m in FreeCAD.activeDocument().Objects:
            if femutils.is_of_type(m, "Fem::FemAnalysis"):
                if not found_analysis:
                    self.analysis = m
                    found_analysis = True
                else:
                    self.analysis = None  # more than one analysis
        if self.analysis:
            if FreeCAD.GuiUp:
                FemGui.setActiveAnalysis(self.analysis)

    def find_solver_analysis(self):
        """ get the analysis group the solver belongs to
        """
        if self.solver.getParentGroup():
            obj = self.solver.getParentGroup()
            if femutils.is_of_type(obj, "Fem::FemAnalysis"):
                self.analysis = obj
                if FreeCAD.GuiUp:
                    FemGui.setActiveAnalysis(self.analysis)

    def find_solver(self):
        found_solver_for_use = False
        for m in self.analysis.Group:
            if femutils.is_of_type(m, "Fem::SolverFISTRTools"):
                # we are going to explicitly check for the fistr tools solver type only,
                # thus it is possible to have lots of framework solvers inside the analysis anyway
                # for some methods no solver is needed (purge_results) --> solver could be none
                # analysis has one solver and no solver was set --> use the one solver
                # analysis has more than one solver and no solver was set --> use solver none
                # analysis has no solver --> use solver none
                if not found_solver_for_use:
                    # no solver was found before
                    self.solver = m
                    found_solver_for_use = True
                else:
                    # another solver was found --> We have more than one solver
                    # we do not know which one to use, so we use none !
                    self.solver = None
                    FreeCAD.Console.PrintLog(
                        "FEM: More than one solver in the analysis "
                        "and no solver given to analyze. "
                        "No solver is set!\n"
                    )

    def update_objects(self):
        ## @var mesh
        #  mesh of the analysis. Used to generate .inp file and to show results
        self.mesh = None
        mesh, message = membertools.get_mesh_to_solve(self.analysis)
        if mesh is not None:
            self.mesh = mesh
        else:
            if FreeCAD.GuiUp:
                QtGui.QMessageBox.critical(None, "Missing prerequisite", message)
            raise Exception(message + "\n")

        ## @var members
        # members of the analysis. All except solvers and the mesh
        self.member = membertools.AnalysisMember(self.analysis)

    def check_prerequisites(self):
        FreeCAD.Console.PrintMessage("Check prerequisites.\n")
        message = ""
        # analysis
        if not self.analysis:
            message += "No active Analysis\n"
        # solver
        if not self.solver:
            message += "No solver object defined in the analysis\n"
        if not self.working_dir:
            message += "Working directory not set\n"
        if not (os.path.isdir(self.working_dir)):
            message += (
                "Working directory \'{}\' doesn't exist."
                .format(self.working_dir)
            )
        from femtools.checksanalysis import check_analysismember
        message += check_analysismember(
            self.analysis,
            self.solver,
            self.mesh,
            self.member
        )
        return message

    def set_base_name(self, base_name=None):
        """
        Set base_name

        Parameters
        ----------
        base_name : str, optional
            base_name base name of .inp/.avs file (without extension).
            It is used to construct .inp file path that is passed to FrontISTR fistr
        """
        if base_name is None:
            self.base_name = ""
        else:
            self.base_name = base_name
        # Update inp file name
        self.set_inp_file_name()

    def set_inp_file_name(self, inp_file_name=None):
        """
        Set inp file name. Normally inp file name is set by write_inp_file.
        That name is also used to determine location and name of avs result file.

        Parameters
        ----------
        inp_file_name : str, optional
            input file name path
        """
        if inp_file_name is not None:
            self.inp_file_name = inp_file_name
            self.cnt_file_name = inp_file_name+".cnt"
        else:
            self.inp_file_name = os.path.join(self.working_dir, (self.base_name + ".inp"))
            self.cnt_file_name = os.path.join(self.working_dir, (self.base_name + ".cnt"))

    def setup_working_dir(self, param_working_dir=None, create=False):
        """Set working dir for solver execution.

        Parameters
        ----------
        param_working_dir :  str, optional
            directory to be used for writing
        create : bool, optional
            Should the working directory be created if it does not exist
        """
        self.working_dir = ""
        # try to use given working dir or overwrite with solver working dir
        fem_general_prefs = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Fem/General")
        if param_working_dir is not None:
            self.working_dir = param_working_dir
            if femutils.check_working_dir(self.working_dir) is not True:
                if create is True:
                    FreeCAD.Console.PrintMessage(
                        "Dir given as parameter \'{}\' doesn't exist.\n".format(self.working_dir)
                    )
                else:
                    FreeCAD.Console.PrintError(
                        "Dir given as parameter \'{}\' doesn't exist "
                        "and create parameter is set to False.\n"
                        .format(self.working_dir)
                    )
                    self.working_dir = femutils.get_pref_working_dir(self.solver)
                    FreeCAD.Console.PrintMessage(
                        "Dir \'{}\' will be used instead.\n"
                        .format(self.working_dir)
                    )
        elif fem_general_prefs.GetBool("OverwriteSolverWorkingDirectory", True) is False:
            self.working_dir = self.solver.WorkingDir
            if femutils.check_working_dir(self.working_dir) is not True:
                if self.working_dir == '':
                    FreeCAD.Console.PrintError(
                        "Working Dir is set to be used from solver object "
                        "but Dir from solver object \'{}\' is empty.\n"
                        .format(self.working_dir)
                    )
                else:
                    FreeCAD.Console.PrintError(
                        "Dir from solver object \'{}\' doesn't exist.\n"
                        .format(self.working_dir)
                    )
                self.working_dir = femutils.get_pref_working_dir(self.solver)
                FreeCAD.Console.PrintMessage(
                    "Dir \'{}\' will be used instead.\n"
                    .format(self.working_dir)
                )
        else:
            self.working_dir = femutils.get_pref_working_dir(self.solver)

        # check working_dir exist, if not use a tmp dir and inform the user
        if femutils.check_working_dir(self.working_dir) is not True:
            FreeCAD.Console.PrintError(
                "Dir \'{}\' doesn't exist or cannot be created.\n"
                .format(self.working_dir)
            )
            self.working_dir = femutils.get_temp_dir(self.solver)
            FreeCAD.Console.PrintMessage(
                "Dir \'{}\' will be used instead.\n"
                .format(self.working_dir)
            )

        # Update inp file name
        self.set_inp_file_name()

    # modify floating point number expression compatible to FrontISTR
    # (should be removed if FrontISTR solver accepts the expression such as 1e-3)
    def mod_fp_expression(self,FILENAME):
        import re
        p = re.compile(r'([+\-,\s][0-9]+)([eE])')

        f = open(FILENAME,"r")
        dat = f.readlines()
        f.close()

        found_modfp=False
        dat2 = []
        for line in dat:
            if p.search(line) == None:
                dat2.append(line)
            else:
                dat2.append(p.sub(r'\1.\2',line))
                found_modfp=True

        if found_modfp:
            f = open(FILENAME,"w")
            f.writelines(dat2)
            f.close()

    def write_inp_file(self):
        import femsolver_FrontISTR.writer as iw
        self.inp_file_name = ""
        try:
            inp_writer = iw.FemInputWriterfistr(
                self.analysis,
                self.solver,
                self.mesh,
                self.member,
                self.working_dir
            )
            self.inp_file_name = inp_writer.write_FrontISTR_input_file()
            self.cnt_file_name = self.inp_file_name+".cnt.txt"
            self.mod_fp_expression(self.inp_file_name+".inp")
        except Exception as e:
            FreeCAD.Console.PrintError(
                "Unexpected error when writing FrontISTR input file: {}\n"
                .format(sys.exc_info()[0])
            )
            FreeCAD.Console.PrintError("[x] Type: {type}".format(type=type(e))+"\n")
            FreeCAD.Console.PrintError("[x] Args: {args}".format(args=e.args)+"\n")
            FreeCAD.Console.PrintError("[x] Message: {message}".format(message=e.message)+"\n")
            FreeCAD.Console.PrintError("[x] Error: {error}".format(error=e)+"\n")
            raise

    def part_inp_file(self):
        # partitioner
        if self.solver.n_process > 1:
            os.environ["OMP_NUM_THREADS"] = str(self.solver.n_process)
        import subprocess
        from platform import system
        startup_info = None
        if system() == "Windows":
            # Windows workaround to avoid blinking terminal window
            startup_info = subprocess.STARTUPINFO()
            startup_info.dwFlags = subprocess.STARTF_USESHOWWINDOW

        p = subprocess.Popen(
            [self.partitioner_binary],
            cwd=self.working_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            startupinfo=startup_info
        )
        part_stdout, part_stderr = p.communicate()

    def setup_fistr(self, fistr_binary=None, fistr_binary_sig="FrontISTR"):
        """Set FrontISTR binary path and validate its execution or download FrontISTR.

        Parameters
        ----------
        fistr_binary : str, optional
            It defaults to `None`. The path to the `fistr` binary. If it is `None`,
            the path is guessed.
        fistr_binary_sig : str, optional
            Defaults to 'FrontISTR'. Expected output from `fistr` when run empty.

        Raises
        ------
        Exception
        """
        error_title = "No FrontISTR binary fistr"
        error_message = ""
        from platform import system
        fistr_std_location = FreeCAD.ParamGet(
            "User parameter:BaseApp/Preferences/Mod/Fem/FrontISTR"
        ).GetBool("UseStandardfistrLocation", True)
        if fistr_std_location:
            if system() == "Windows":
                fistr_path = FreeCAD.getUserAppDataDir() + "Mod/FEM_FrontISTR/bin/fistr1.exe"
                partitioner_path = FreeCAD.getUserAppDataDir() + "Mod/FEM_FrontISTR/bin/hecmw_part1.exe"
                mpiexec_path = FreeCAD.getUserAppDataDir() + "Mod/FEM_FrontISTR/bin/mpiexec.exe"
                FreeCAD.ParamGet(
                    "User parameter:BaseApp/Preferences/Mod/Fem/FrontISTR"
                ).SetString("fistrBinaryPath", fistr_path)
                self.fistr_binary = fistr_path
                self.partitioner_binary = partitioner_path
                self.mpiexec_binary = mpiexec_path
            elif system() in ("Linux", "Darwin"):
                p1 = subprocess.Popen(["which", "fistr1"], stdout=subprocess.PIPE)
                if p1.wait() == 0:
                    if sys.version_info.major >= 3:
                        fistr_path = p1.stdout.read().decode("utf8").split("\n")[0]
                    else:
                        fistr_path = p1.stdout.read().split("\n")[0]
                elif p1.wait() == 1:
                    error_message = (
                        "FEM: FrontISTR binary fistr1 not found in "
                        "standard system binary path. "
                        "Please install fistr or set path to binary "
                        "in FEM preferences tab FrontISTR.\n"
                    )
                    if FreeCAD.GuiUp:
                        QtGui.QMessageBox.critical(None, error_title, error_message)
                    raise Exception(error_message)
                self.fistr_binary = fistr_path

                p2 = subprocess.Popen(["which", "hecmw_part1"], stdout=subprocess.PIPE)
                if p2.wait() == 0:
                    if sys.version_info.major >= 3:
                        partitioner_path = p2.stdout.read().decode("utf8").split("\n")[0]
                    else:
                        partitioner_path = p2.stdout.read().split("\n")[0]
                elif p2.wait() == 1:
                    error_message = (
                        "FEM: FrontISTR binary hecmw_part1 not found in "
                        "standard system binary path.\n"
                    )
                    if FreeCAD.GuiUp:
                        QtGui.QMessageBox.critical(None, error_title, error_message)
                    raise Exception(error_message)
                self.partitioner_binary = partitioner_path

                p3 = subprocess.Popen(["which", "mpirun"], stdout=subprocess.PIPE)
                if p3.wait() == 0:
                    if sys.version_info.major >= 3:
                        mpiexec_path = p3.stdout.read().decode("utf8").split("\n")[0]
                    else:
                        mpiexec_path = p3.stdout.read().split("\n")[0]
                elif p3.wait() == 1:
                    error_message = (
                        "FEM: FrontISTR binary mpirun not found in "
                        "standard system binary path.\n"
                    )
                    if FreeCAD.GuiUp:
                        QtGui.QMessageBox.critical(None, error_title, error_message)
                    raise Exception(error_message)
                self.mpiexec_binary = mpiexec_path
        else:
            if not fistr_binary:
                self.fistr_prefs = FreeCAD.ParamGet(
                    "User parameter:BaseApp/Preferences/Mod/Fem/FrontISTR"
                )
                fistr_binary = self.fistr_prefs.GetString("fistrBinaryPath", "")
                if not fistr_binary:
                    FreeCAD.ParamGet(
                        "User parameter:BaseApp/Preferences/Mod/Fem/FrontISTR"
                    ).SetBool("UseStandardfistrLocation", True)
                    error_message = (
                        "FEM: FrontISTR binary fistr path not set at all. "
                        "The use of standard path was activated in "
                        "FEM preferences tab FrontISTR. Please try again!\n"
                    )
                    if FreeCAD.GuiUp:
                        QtGui.QMessageBox.critical(None, error_title, error_message)
                    raise Exception(error_message)
            self.fistr_binary = fistr_binary

        startup_info = None
        if system() == "Windows":
            # Windows workaround to avoid blinking terminal window
            startup_info = subprocess.STARTUPINFO()
            startup_info.dwFlags = subprocess.STARTF_USESHOWWINDOW
        fistr_stdout = None
        fistr_stderr = None
        try:
            p = subprocess.Popen(
                [self.fistr_binary, "-v"],
                cwd=self.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                startupinfo=startup_info
            )
            fistr_stdout, fistr_stderr = p.communicate()
            if fistr_binary_sig in str(fistr_stdout):
                self.fistr_binary_present = True
            else:
                raise Exception("FEM: wrong fistr binary")
                # since we raise an exception the try will fail and
                # the exception later with the error popup will be raised
                # TODO: I'm still able to break it.
                # If user doesn't give a file but a path without a file or
                # a file which is not a binary no exception at all is raised.
        except OSError as e:
            FreeCAD.Console.PrintError("{}\n".format(e))
            if e.errno == 2:
                FreeCAD.Console.PrintMessage("Start installing FrontISTR...")
                message = (
                    "FrontISTR binary files are not found. "
                    "Start the installation. This may take several time."
                )
                QtGui.QMessageBox.warning(None, "Install FrontISTR", message)
                if system() == "Windows":
                    import urllib.request
                    import zipfile
                    import shutil
                    from pathlib import Path
                    filename = 'FrontISTR-latest.hybrid_impi_mkl_intelthread.zip'
                    filepath = Path(FreeCAD.getUserAppDataDir() + 'Mod/FEM_FrontISTR/' + filename)
                    req = urllib.request.Request(
                        # TODO: this redirector does not work
                        #'https://www.frontistr.com/download/link.php?' +
                        'https://frontistr-commons.gitlab.io/FrontISTR/release/x86_64-w64-mingw32/' +
                        filename)
                    with urllib.request.urlopen(req) as response, open(filepath, "wb") as out_file:
                        shutil.copyfileobj(response, out_file)
                    with zipfile.ZipFile(filepath) as zf:
                        zf.extractall(Path(FreeCAD.getUserAppDataDir() + 'Mod/FEM_FrontISTR/bin'))
                else:
                    error_message = (
                        "FEM: FrontISTR binary fistr \'{}\' not found. "
                        "Please set the FrontISTR binary fistr path in "
                        "FEM preferences tab FrontISTR.\n"
                        .format(fistr_binary)
                    )
                    if FreeCAD.GuiUp:
                        QtGui.QMessageBox.critical(None, error_title, error_message)
                    raise Exception(error_message)
                FreeCAD.Console.PrintMessage("Done\n")
            else:
                FreeCAD.Console.PrintError(
                    "Unexpected error when executing FrontISTR: {}\n"
                    .format(sys.exc_info()[0])
                )
                FreeCAD.Console.PrintError("[x] Type: {type}".format(type=type(e))+"\n")
                FreeCAD.Console.PrintError("[x] Args: {args}".format(args=e.args)+"\n")
                FreeCAD.Console.PrintError("[x] Message: {message}".format(message=e.message)+"\n")
                FreeCAD.Console.PrintError("[x] Error: {error}".format(error=e)+"\n")

        except Exception as e:
            FreeCAD.Console.PrintError("{}\n".format(e))
            error_message = (
                "FEM: FrontISTR fistr \'{}\' output \'{}\' doesn't "
                "contain expected phrase \'{}\'. "
                "There are some problems when running the fistr binary. "
                "Check if fistr runs standalone without FreeCAD.\n"
                .format(fistr_binary, fistr_stdout, fistr_binary_sig)
            )
            if FreeCAD.GuiUp:
                QtGui.QMessageBox.critical(None, error_title, error_message)
            raise Exception(error_message)

    def start_fistr(self):
        import multiprocessing
        from platform import system
        self.fistr_stdout = ""
        self.fistr_stderr = ""
        
        if "OMP_NUM_THREADS" in os.environ:
            ont_backup_available = True
            ont_backup = os.environ.get("OMP_NUM_THREADS")
        else:
            ont_backup_available = False
        
        if self.solver.n_process > 1:
            os.environ["OMP_NUM_THREADS"] = str(1)
            os.environ["MKL_NUM_THREADS"] = str(1)
        
        n_pe = '%d'%self.solver.n_process
        FreeCAD.Console.PrintMessage(" ".join([self.mpiexec_binary,"-n",n_pe,self.fistr_binary])+"\n")

        from platform import system
        startup_info = None
        if system() == "Windows":
            # Windows workaround to avoid blinking terminal window
            startup_info = subprocess.STARTUPINFO()
            startup_info.dwFlags = subprocess.STARTF_USESHOWWINDOW

        p = subprocess.Popen(
            [self.mpiexec_binary,"-n",n_pe,self.fistr_binary],
            cwd=self.working_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            startupinfo=startup_info
        )
        self.fistr_stdout, self.fistr_stderr = p.communicate()

        if sys.version_info.major >= 3:
            if system() == "Windows":
                # TODO: encoding autodetection doesn't work on Windows yet
                encoding = 'cp932'
            else:
                encoding = 'utf-8'
            self.fistr_stdout = self.fistr_stdout.decode(encoding)
            self.fistr_stderr = self.fistr_stderr.decode(encoding)

        if ont_backup_available:
            os.environ["OMP_NUM_THREADS"] = str(ont_backup)

        return p.returncode

    def get_fistr_version(self):
        self.setup_fistr()
        import re
        from platform import system
        startup_info = None
        if system() == "Windows":
            # Windows workaround to avoid blinking terminal window
            startup_info = subprocess.STARTUPINFO()
            startup_info.dwFlags = subprocess.STARTF_USESHOWWINDOW
        fistr_stdout = None
        fistr_stderr = None
        # Now extract the version number
        p = subprocess.Popen(
            [self.fistr_binary, "-v"],
            cwd=self.working_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            startupinfo=startup_info
        )
        fistr_stdout, fistr_stderr = p.communicate()
        if sys.version_info.major >= 3:
            fistr_stdout = fistr_stdout.decode()
            # fistr_stderr = fistr_stderr.decode()
        m = re.search(r"(\d+).(\d+)", fistr_stdout)
        return (int(m.group(1)), int(m.group(2)))

    def fistr_run(self):
        FreeCAD.Console.PrintMessage("Run FrontISTR ...\n")
        if self.test_mode:
            FreeCAD.Console.PrintError("FrontISTR can not be run if test_mode is True.\n")
            return
        self.setup_fistr()
        if self.fistr_binary_present is False:
            error_message = (
                "FEM: FrontISTR binary fistr \'{}\' not found. "
                "Please set the FrontISTR binary fistr path in FEM preferences tab FrontISTR.\n"
                .format(self.fistr_binary)
            )
            if FreeCAD.GuiUp:
                QtGui.QMessageBox.critical(None, "No FrontISTR binary fistr", error_message)
            raise Exception(error_message)
        progress_bar = FreeCAD.Base.ProgressIndicator()
        progress_bar.start("Everything seams fine. FrontISTR fistr will be executed ...", 0)
        ret_code = 0
        ret_code = self.start_fistr()
        self.finished.emit(ret_code)
        progress_bar.stop()
        if ret_code or self.fistr_stderr:
            if ret_code == 201 and self.solver.AnalysisType == "check":
                FreeCAD.Console.PrintMessage(
                    "It seams we run into NOANALYSIS problem, "
                    "thus workaround for wrong exit code for *NOANALYSIS check "
                    "and set ret_code to 0.\n"
                )
                # https://forum.freecadweb.org/viewtopic.php?f=18&t=31303&start=10#p260743
                ret_code = 0
            else:
                FreeCAD.Console.PrintError("FrontISTR failed with exit code {}\n".format(ret_code))
                FreeCAD.Console.PrintMessage("--------start of stderr-------\n")
                FreeCAD.Console.PrintMessage(self.fistr_stderr)
                FreeCAD.Console.PrintMessage("--------end of stderr---------\n")
                FreeCAD.Console.PrintMessage("--------start of stdout-------\n")
                FreeCAD.Console.PrintMessage(self.fistr_stdout)
                FreeCAD.Console.PrintMessage("\n--------end of stdout---------\n")
                FreeCAD.Console.PrintMessage("--------start problems---------\n")
                self.has_no_material_assigned()
                self.has_nonpositive_jacobians()
                FreeCAD.Console.PrintMessage("\n--------end problems---------\n")
        else:
            FreeCAD.Console.PrintMessage("FrontISTR finished without error.\n")
        return ret_code

    def run(self):
        self.update_objects()
        self.setup_working_dir()
        message = self.check_prerequisites()
        if message:
            error_message = (
                "FrontISTR was not started due to missing prerequisites:\n{}\n"
                .format(message)
            )
            FreeCAD.Console.PrintError(error_message)
            if FreeCAD.GuiUp:
                QtGui.QMessageBox.critical(
                    None,
                    "Missing prerequisite",
                    error_message
                )
            return False
        else:
            self.write_inp_file()
            if self.inp_file_name == "":
                error_message = "Error on writing FrontISTR input file.\n"
                FreeCAD.Console.PrintError(error_message)
                if FreeCAD.GuiUp:
                    QtGui.QMessageBox.critical(
                        None,
                        "Error",
                        error_message
                    )
                return False
            else:
                FreeCAD.Console.PrintMessage(
                    "Writing FrontISTR input file completed.\n"
                )
                ret_code = self.fistr_run()
                if ret_code != 0:
                    error_message = (
                        "FrontISTR finished with error {}.\n"
                        .format(ret_code)
                    )
                    FreeCAD.Console.PrintError(error_message)
                    if FreeCAD.GuiUp:
                        QtGui.QMessageBox.critical(
                            None,
                            "Error",
                            error_message
                        )
                    return False
                else:
                    FreeCAD.Console.PrintMessage("**** try to read result files\n")
                    self.load_results()
                    # TODO: output an error message if there where problems reading the results
        return True

    def has_no_material_assigned(self):
        if " *ERROR in calinput: no material was assigned" in self.fistr_stdout:
            without_material_elements = []
            without_material_elemnodes = []
            for line in self.fistr_stdout.splitlines():
                if "to element" in line:
                    # print(line)
                    # print(line.split())
                    non_mat_ele = int(line.split()[2])
                    # print(non_mat_ele)
                    if non_mat_ele not in without_material_elements:
                        without_material_elements.append(non_mat_ele)
            for e in without_material_elements:
                for n in self.mesh.FemMesh.getElementNodes(e):
                    without_material_elemnodes.append(n)
            without_material_elements = sorted(without_material_elements)
            without_material_elemnodes = sorted(without_material_elemnodes)
            command_for_withoutmatnodes = (
                "without_material_elemnodes = {}"
                .format(without_material_elemnodes)
            )
            command_to_highlight = (
                "Gui.ActiveDocument.{}.HighlightedNodes = without_material_elemnodes"
                .format(self.mesh.Name)
            )
            # some output for the user
            FreeCAD.Console.PrintError(
                "\n\nFrontISTR returned an error due to elements without materials.\n"
            )
            FreeCAD.Console.PrintMessage(
                "without_material_elements = {}\n"
                .format(without_material_elements)
            )
            FreeCAD.Console.PrintMessage(command_for_withoutmatnodes + "\n")
            if FreeCAD.GuiUp:
                import FreeCADGui
                # with this the list without_material_elemnodes
                # will be available for further user interaction
                FreeCADGui.doCommand(command_for_withoutmatnodes)
                FreeCAD.Console.PrintMessage("\n")
                FreeCADGui.doCommand(command_to_highlight)
            FreeCAD.Console.PrintMessage(
                "\nFollowing some commands to copy. "
                "They will highlight the elements without materials "
                "or to reset the highlighted nodes:\n"
            )
            FreeCAD.Console.PrintMessage(command_to_highlight + "\n")
            # command to reset the Highlighted Nodes
            FreeCAD.Console.PrintMessage(
                "Gui.ActiveDocument.{}.HighlightedNodes = []\n\n"
                .format(self.mesh.Name)
            )
            return True
        else:
            return False

    def has_nonpositive_jacobians(self):
        if "*ERROR in e_c3d: nonpositive jacobian" in self.fistr_stdout:
            nonpositive_jacobian_elements = []
            nonpositive_jacobian_elenodes = []
            for line in self.fistr_stdout.splitlines():
                if "determinant in element" in line:
                    # print(line)
                    # print(line.split())
                    non_posjac_ele = int(line.split()[3])
                    # print(non_posjac_ele)
                    if non_posjac_ele not in nonpositive_jacobian_elements:
                        nonpositive_jacobian_elements.append(non_posjac_ele)
            for e in nonpositive_jacobian_elements:
                for n in self.mesh.FemMesh.getElementNodes(e):
                    nonpositive_jacobian_elenodes.append(n)
            nonpositive_jacobian_elements = sorted(nonpositive_jacobian_elements)
            nonpositive_jacobian_elenodes = sorted(nonpositive_jacobian_elenodes)
            command_for_nonposjacnodes = (
                "nonpositive_jacobian_elenodes = {}"
                .format(nonpositive_jacobian_elenodes)
            )
            command_to_highlight = (
                "Gui.ActiveDocument.{}.HighlightedNodes = nonpositive_jacobian_elenodes"
                .format(self.mesh.Name)
            )
            # some output for the user
            FreeCAD.Console.PrintError(
                "\n\nFrontISTR returned an error due to nonpositive jacobian elements.\n"
            )
            FreeCAD.Console.PrintMessage(
                "nonpositive_jacobian_elements = {}\n"
                .format(nonpositive_jacobian_elements)
            )
            FreeCAD.Console.PrintMessage(command_for_nonposjacnodes + "\n")
            if FreeCAD.GuiUp:
                import FreeCADGui
                # with this the list nonpositive_jacobian_elenodes
                # will be available for further user interaction
                FreeCADGui.doCommand(command_for_nonposjacnodes)
                FreeCAD.Console.PrintMessage("\n")
                FreeCADGui.doCommand(command_to_highlight)
            FreeCAD.Console.PrintMessage(
                "\nFollowing some commands to copy. "
                "They highlight the nonpositive jacobians "
                "or to reset the highlighted nodes:\n"
            )
            FreeCAD.Console.PrintMessage(command_to_highlight + "\n")
            # command to reset the Highlighted Nodes
            FreeCAD.Console.PrintMessage(
                "Gui.ActiveDocument.{}.HighlightedNodes = []\n\n"
                .format(self.mesh.Name)
            )
            return True
        else:
            return False

    def load_results(self):
        FreeCAD.Console.PrintMessage("We will load the fistr visualized file.\n")
        self.results_present = False
        self.load_results_fistravs()

    def load_results_fistravs(self):
        """Load results of fistr calculations from .avs file.
        """
        import importfistrAvsResults

        # grep visfiles
        visfiles = []
        for file in os.listdir(self.working_dir):
            if file.find("_vis_psf.") < 0:
                continue
            visfiles.append(file)
        visfiles.sort()

        # read only visfile at the last substep
        avs_result_file = self.working_dir.replace("\\","/")+"/"+visfiles[-1]
        if os.path.isfile(avs_result_file):
            importfistrAvsResults.importAvs(avs_result_file, self.analysis, "FISTR_")
            for m in self.analysis.Group:
                if m.isDerivedFrom("Fem::FemResultObject"):
                    self.results_present = True
                    break
            else:
                if self.solver.AnalysisType == "check":
                    for m in self.analysis.Group:
                        if m.isDerivedFrom("Fem::FemMeshObjectPython"):
                            # we have no result object but a mesh object
                            # this happens in NOANALYSIS mode
                            break
                else:
                    FreeCAD.Console.PrintError("FEM: No result object in active Analysis.\n")
        else:
            raise Exception("FEM: No results found at {}!".format(avs_result_file))

class FrontISTRTools(FemToolsFISTR):

    def __init__(self, solver=None):
        FemToolsFISTR.__init__(self, None, solver)

##  @}

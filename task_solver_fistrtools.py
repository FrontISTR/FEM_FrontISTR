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

__title__ = "FEM solver FrontISTR tools task panel for the document object"
__author__ = "FrontISTR Commons"
__url__ = "https://www.frontistr.com/"

## @package task_solver_fistrtools
#  \ingroup FEM
#  \brief task panel for solver FrontISTR tools object

import os
import sys
import time
from PySide import QtCore
from PySide import QtGui
from PySide.QtCore import Qt
from PySide.QtGui import QApplication

import FreeCAD
import FreeCADGui

import FemGui

if sys.version_info.major >= 3:
    def unicode(text, *args):
        return str(text)


class _TaskPanel:
    """
    The TaskPanel for FrontISTR tools solver object
    """

    def __init__(self, solver_object):
        self.form = FreeCADGui.PySideUic.loadUi(
            FreeCAD.getUserAppDataDir()+ "Mod/FEM_FrontISTR/Resources/SolverFrontISTR.ui"
        )

        from fistrtools import FrontISTRTools as fistr
        # we do not need to pass the analysis, it will be found on fea init
        # TODO: if there is not analysis object in document init of fea
        # will fail with an exception and task panel will not open
        # handle more smart by a pop up error message and still open
        # task panel, may be deactivate write and run button.
        self.fea = fistr(solver_object)
        self.fea.setup_working_dir()
        self.fea.setup_fistr()

        self.FrontISTR = QtCore.QProcess()
        self.Timer = QtCore.QTimer()
        self.Timer.start(300)

        self.fem_console_message = ""

        # Connect Signals and Slots
        QtCore.QObject.connect(
            self.form.tb_choose_working_dir,
            QtCore.SIGNAL("clicked()"),
            self.choose_working_dir
        )
        QtCore.QObject.connect(
            self.form.pb_write_inp,
            QtCore.SIGNAL("clicked()"),
            self.write_input_file_handler
        )
        QtCore.QObject.connect(
            self.form.pb_edit_inp,
            QtCore.SIGNAL("clicked()"),
            self.editFrontISTRInputFile
        )
        QtCore.QObject.connect(
            self.form.pb_run_fistr,
            QtCore.SIGNAL("clicked()"),
            self.runFrontISTR
        )
        QtCore.QObject.connect(
            self.form.rb_static_analysis,
            QtCore.SIGNAL("clicked()"),
            self.select_static_analysis
        )
        QtCore.QObject.connect(
            self.form.rb_frequency_analysis,
            QtCore.SIGNAL("clicked()"),
            self.select_frequency_analysis
        )
        QtCore.QObject.connect(
            self.form.rb_thermomech_analysis,
            QtCore.SIGNAL("clicked()"),
            self.select_thermomech_analysis
        )
        QtCore.QObject.connect(
            self.form.rb_check_mesh,
            QtCore.SIGNAL("clicked()"),
            self.select_check_mesh
        )
        QtCore.QObject.connect(
            self.FrontISTR,
            QtCore.SIGNAL("started()"),
            self.FrontISTRStarted
        )
        QtCore.QObject.connect(
            self.FrontISTR,
            QtCore.SIGNAL("stateChanged(QProcess::ProcessState)"),
            self.FrontISTRStateChanged
        )
        QtCore.QObject.connect(
            self.FrontISTR,
            QtCore.SIGNAL("error(QProcess::ProcessError)"),
            self.FrontISTRError
        )
        QtCore.QObject.connect(
            self.FrontISTR,
            QtCore.SIGNAL("finished(int)"),
            self.FrontISTRFinished
        )
        QtCore.QObject.connect(
            self.Timer,
            QtCore.SIGNAL("timeout()"),
            self.UpdateText
        )

        self.update()

    def getStandardButtons(self):
        # only show a close button
        # def accept() in no longer needed, since there is no OK button
        return int(QtGui.QDialogButtonBox.Close)

    def reject(self):
        FreeCADGui.ActiveDocument.resetEdit()

    def update(self):
        "fills the widgets"
        self.form.le_working_dir.setText(self.fea.working_dir)
        if self.fea.solver.AnalysisType == "static":
            self.form.rb_static_analysis.setChecked(True)
        elif self.fea.solver.AnalysisType == "frequency":
            self.form.rb_frequency_analysis.setChecked(True)
        elif self.fea.solver.AnalysisType == "thermomech":
            self.form.rb_thermomech_analysis.setChecked(True)
        elif self.fea.solver.AnalysisType == "check":
            self.form.rb_check_mesh.setChecked(True)
        return

    def femConsoleMessage(self, message="", color="#000000"):
        if sys.version_info.major < 3:
            message = message.encode("utf-8", "replace")
        self.fem_console_message = self.fem_console_message + (
            '<font color="#0000FF">{0:4.1f}:</font> <font color="{1}">{2}</font><br>'
            .format(time.time() - self.Start, color, message)
        )
        self.form.textEdit_Output.setText(self.fem_console_message)
        self.form.textEdit_Output.moveCursor(QtGui.QTextCursor.End)

    def printFrontISTRstdout(self):

        out = self.FrontISTR.readAllStandardOutput()
        # print(type(out))
        # <class 'PySide2.QtCore.QByteArray'>

        if out.isEmpty():
            self.femConsoleMessage("FrontISTR stdout is empty", "#FF0000")
            return False

        if sys.version_info.major >= 3:
            # https://forum.freecadweb.org/viewtopic.php?f=18&t=39195
            # convert QByteArray to a binary string an decode it to "utf-8"
            out = out.data().decode()  # "utf-8" can be omitted
            # print(type(out))
            # print(out)
        else:
            try:
                out = unicode(out, "utf-8", "replace")
                rx = QtCore.QRegExp("\\*ERROR.*\\n\\n")
                # print(rx)
                rx.setMinimal(True)
                pos = rx.indexIn(out)
                while not pos < 0:
                    match = rx.cap(0)
                    FreeCAD.Console.PrintError(match.strip().replace("\n", " ") + "\n")
                    pos = rx.indexIn(out, pos + 1)
            except UnicodeDecodeError:
                self.femConsoleMessage("Error converting stdout from FrontISTR", "#FF0000")
        out = os.linesep.join([s for s in out.splitlines() if s])
        out = out.replace("\n", "<br>")
        # print(out)
        self.femConsoleMessage(out)

        if "*ERROR in e_c3d: nonpositive jacobian" in out:
            error_message = (
                "\n\nFrontISTR returned an error due to "
                "nonpositive jacobian determinant in at least one element\n"
                "Use the run button on selected solver to get a better error output.\n"
            )
            FreeCAD.Console.PrintError(error_message)

        if "*ERROR" in out:
            return False
        else:
            return True

    def UpdateText(self):
        if(self.FrontISTR.state() == QtCore.QProcess.ProcessState.Running):
            self.form.l_time.setText("Time: {0:4.1f}: ".format(time.time() - self.Start))

    def FrontISTRError(self, error=""):
        print("Error() {}".format(error))
        self.femConsoleMessage("FrontISTR execute error: {}".format(error), "#FF0000")

    def FrontISTRNoError(self):
        print("FrontISTR done without error!")
        self.femConsoleMessage("FrontISTR done without error!", "#00AA00")

    def FrontISTRStarted(self):
        # print("FrontISTRStarted()")
        FreeCAD.Console.PrintLog("FrontISTR state: {}\n".format(self.FrontISTR.state()))
        self.form.pb_run_fistr.setText("Break FrontISTR")

    def FrontISTRStateChanged(self, newState):
        if (newState == QtCore.QProcess.ProcessState.Starting):
                self.femConsoleMessage("Starting FrontISTR...")
        if (newState == QtCore.QProcess.ProcessState.Running):
                self.femConsoleMessage("FrontISTR is running...")
        if (newState == QtCore.QProcess.ProcessState.NotRunning):
                self.femConsoleMessage("FrontISTR stopped.")

    def FrontISTRFinished(self, exitCode):
        # print("FrontISTRFinished(), exit code: {}".format(exitCode))
        FreeCAD.Console.PrintLog("FrontISTR state: {}\n".format(self.FrontISTR.state()))

        # Restore previous cwd
        QtCore.QDir.setCurrent(self.cwd)

        self.Timer.stop()

        if self.printFrontISTRstdout():
            self.FrontISTRNoError()
        else:
            self.FrontISTRError()

        self.form.pb_run_fistr.setText("Re-run FrontISTR")
        self.femConsoleMessage("Loading result sets...")
        self.form.l_time.setText("Time: {0:4.1f}: ".format(time.time() - self.Start))
        self.fea.reset_mesh_purge_results_checked()
        self.fea.inp_file_name = self.fea.inp_file_name

        # check if fistr is greater than 2.10, if not do not read results
        # https://forum.freecadweb.org/viewtopic.php?f=18&t=23548#p183829 Point 3
        # https://forum.freecadweb.org/viewtopic.php?f=18&t=23548&start=20#p183909
        # https://forum.freecadweb.org/viewtopic.php?f=18&t=23548&start=30#p185027
        # https://github.com/FreeCAD/FreeCAD/commit/3dd1c9f
        majorVersion, minorVersion = self.fea.get_fistr_version()
        if majorVersion == 2 and minorVersion <= 10:
            message = (
                "The used FrontISTR version {}.{} creates broken output files. "
                "The result file will not be read by FreeCAD FEM. "
                "You still can try to read it stand alone with FreeCAD, but it is "
                "strongly recommended to upgrade FrontISTR to a newer version.\n"
                .format(majorVersion, minorVersion)
            )
            QtGui.QMessageBox.warning(None, "Upgrade FrontISTR", message)
            raise

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.fea.load_results()
        except Exception:
            FreeCAD.Console.PrintError("loading results failed\n")

        QApplication.restoreOverrideCursor()
        self.form.l_time.setText("Time: {0:4.1f}: ".format(time.time() - self.Start))

    def choose_working_dir(self):
        wd = QtGui.QFileDialog.getExistingDirectory(None, "Choose FrontISTR working directory",
                                                    self.fea.working_dir)
        if os.path.isdir(wd):
            self.fea.setup_working_dir(wd)
        self.form.le_working_dir.setText(self.fea.working_dir)

    def write_input_file_handler(self):
        self.Start = time.time()
        self.form.l_time.setText("Time: {0:4.1f}: ".format(time.time() - self.Start))
        QApplication.restoreOverrideCursor()
        if self.check_prerequisites_helper():
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.fea.write_inp_file()
            if self.fea.inp_file_name != "":
                self.femConsoleMessage("Write completed.")
                self.form.pb_edit_inp.setEnabled(True)
                self.form.pb_run_fistr.setEnabled(True)
            else:
                self.femConsoleMessage("Write .inp file failed!", "#FF0000")
            QApplication.restoreOverrideCursor()
        self.form.l_time.setText("Time: {0:4.1f}: ".format(time.time() - self.Start))

    def check_prerequisites_helper(self):
        self.Start = time.time()
        self.femConsoleMessage("Check dependencies...")
        self.form.l_time.setText("Time: {0:4.1f}: ".format(time.time() - self.Start))

        self.fea.update_objects()
        message = self.fea.check_prerequisites()
        if message != "":
            QtGui.QMessageBox.critical(None, "Missing prerequisite(s)", message)
            return False
        return True

    def start_ext_editor(self, ext_editor_path, filename):
        if not hasattr(self, "ext_editor_process"):
            self.ext_editor_process = QtCore.QProcess()
        if self.ext_editor_process.state() != QtCore.QProcess.Running:
            self.ext_editor_process.start(ext_editor_path, [filename])

    def editFrontISTRInputFile(self):
        print("editFrontISTRInputFile {}".format(self.fea.inp_file_name))
        fistr_prefs = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Fem/FrontISTR")
        if fistr_prefs.GetBool("UseInternalEditor", True):
            FemGui.open(self.fea.inp_file_name)
        else:
            ext_editor_path = fistr_prefs.GetString("ExternalEditorPath", "")
            if ext_editor_path:
                self.start_ext_editor(ext_editor_path, self.fea.inp_file_name)
            else:
                print(
                    "External editor is not defined in FEM preferences. "
                    "Falling back to internal editor"
                )
                FemGui.open(self.fea.inp_file_name)

    def runFrontISTR(self):
        # print("runFrontISTR")
        self.Start = time.time()

        self.femConsoleMessage("FrontISTR binary: {}".format(self.fea.fistr_binary))
        self.femConsoleMessage("FrontISTR input file: {}".format(self.fea.inp_file_name))
        self.femConsoleMessage("Run FrontISTR...")

        FreeCAD.Console.PrintMessage(
            "run FrontISTR at: {} with: {}\n"
            .format(self.fea.fistr_binary, self.fea.inp_file_name)
        )
        # change cwd because fistr may crash if directory has no write permission
        # there is also a limit of the length of file names so jump to the document directory
        self.cwd = QtCore.QDir.currentPath()
        fi = QtCore.QFileInfo(self.fea.inp_file_name)
        QtCore.QDir.setCurrent(fi.path())
        self.FrontISTR.start(self.fea.fistr_binary, ["-i", fi.baseName()])

        QApplication.restoreOverrideCursor()

    def select_analysis_type(self, analysis_type):
        if self.fea.solver.AnalysisType != analysis_type:
            self.fea.solver.AnalysisType = analysis_type
            self.form.pb_edit_inp.setEnabled(False)
            self.form.pb_run_fistr.setEnabled(False)

    def select_static_analysis(self):
        self.select_analysis_type("static")

    def select_frequency_analysis(self):
        self.select_analysis_type("frequency")

    def select_thermomech_analysis(self):
        self.select_analysis_type("thermomech")

    def select_check_mesh(self):
        self.select_analysis_type("check")

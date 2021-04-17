# ***************************************************************************
# *   Copyright (c) 2009 Juergen Riegel <juergen.riegel@web.de>             *
# *   Copyright (c) 2020 Bernd Hahnebach <bernd@bimstatik.org>              *
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


__title__="FreeCAD FrontISTR Workbench GUI"
__author__ = "FrontISTR Commons"
__url__ = "https://www.frontistr.com/"

class FrontISTR(Workbench):
    "FrontISTR workbench object"
    def __init__(self):
        self.__class__.Icon = FreeCAD.getUserAppDataDir()+ "Mod/FEM_FrontISTR/Resources/FrontISTR.svg"
        self.__class__.MenuText = "FrontISTR"
        self.__class__.ToolTip = "Parallel FEM solver workbench"

    def Initialize(self):
        # load the module
        import Fem
        import FemGui
        import femcommands.commands
        
        import FISTR_solver

        def QT_TRANSLATE_NOOP(scope, text): return text
        #FreeCADGui.addCommand("FEM_SolverFrontISTR",_SolverFrontISTR())
        self.fstrtools = ["FISTR_solver"]
        self.appendToolbar(QT_TRANSLATE_NOOP("Workbench","FrontISTR tools"),self.fstrtools)
        
        #self.appendToolbar(QT_TRANSLATE_NOOP("Workbench","E.M. FastHenry tools"),self.emfhtools)
        #self.appendMenu(QT_TRANSLATE_NOOP("EM","&EM"),self.emfhtools + self.emvhtools + self.emtools)
        #FreeCADGui.addIconPath(":/icons")
        #FreeCADGui.addLanguagePath(":/translations")
        #FreeCADGui.addPreferencePage(":/ui/preferences-EM.ui","EM")
        #FreeCADGui.addPreferencePage(":/ui/preferences-aEMdefaults.ui","EM")
        Log ('Loading FrontISTR module... done\n')

    def Activated(self):
        Log("FrontISTR workbench activated\n")
        
    def Deactivated(self):
        Log("FrontISTR workbench deactivated\n")

#    def ContextMenu(self, recipient):
#        self.appendContextMenu("Utilities",self.EMcontexttools)

    # needed if this is a pure Python workbench
    def GetClassName(self): 
        return "Gui::PythonWorkbench"

FreeCADGui.addWorkbench(FrontISTR)

# File format pref pages are independent and can be loaded at startup
#import EM_rc
#FreeCADGui.addPreferencePage(":/ui/preferences-inp.ui","Import-Export")




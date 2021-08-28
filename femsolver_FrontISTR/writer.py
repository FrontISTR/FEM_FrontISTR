# ***************************************************************************
# *   Copyright (c) 2015 Przemo Firszt <przemo@firszt.eu>                   *
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


__title__ = "FreeCAD FEM solver FrontISTR writer"
__author__ = "FrontISTR Commons"
__url__ = "https://www.frontistr.com/"

## \addtogroup FEM
#  @{

# import io
import codecs
import os
import six
import sys
import time
from os.path import join

import FreeCAD

from femsolver import writerbase
from femmesh import meshtools
from femtools import geomtools


# Interesting forum topic: https://forum.freecadweb.org/viewtopic.php?&t=48451
# TODO somehow set units at beginning and every time a value is retrieved use this identifier
# this would lead to support of unit system, force might be retrieved in base writer!

class FemInputWriterfistr(writerbase.FemInputWriter):
    def __init__(
        self,
        analysis_obj,
        solver_obj,
        mesh_obj,
        member,
        dir_name=None
    ):
        writerbase.FemInputWriter.__init__(
            self,
            analysis_obj,
            solver_obj,
            mesh_obj,
            member,
            dir_name
        )
        self.mesh_name = self.mesh_object.Name
        self.include = join(self.dir_name, self.mesh_name)

        self.msh_name = self.include + ".inp"
        self.cnt_name = self.include + ".cnt"
        self.dat_name = join(self.dir_name, "hecmw_ctrl.dat")
        self.part_dat_name = join(self.dir_name, "hecmw_part_ctrl.dat")
        self.file_name = self.include + ".inp"
        self.FluidInletoutlet_ele = []
        self.fluid_inout_nodes_file = join(
            self.dir_name,
            "{}_inout_nodes.txt".format(self.mesh_name)
        )
        from femtools import constants
        from FreeCAD import Units
        self.gravity = int(Units.Quantity(constants.gravity()).getValueAs("mm/s^2"))  # 9820 mm/s2
        # new class attributes
        self.fc_ver = FreeCAD.Version()
        self.fistr_nall = "ALL"
        self.fistr_eall = "ALL"
        self.fistr_evolumes = "Evolumes"
        self.fistr_efaces = "Efaces"
        self.fistr_eedges = "Eedges"
        self.fistr_elsets = []

        self.isactive_load = False
        self.isactive_boundary = False

    # ********************************************************************************************
    # write FrontISTR input
    def write_FrontISTR_input_file(self):
        timestart = time.process_time()
        FreeCAD.Console.PrintMessage("Start writing FrontISTR input file\n")
        FreeCAD.Console.PrintLog(
            "writerbasefistr --> self.mesh_name  -->  " + self.mesh_name + "\n"
        )
        FreeCAD.Console.PrintLog(
            "writerbasefistr --> self.dir_name  -->  " + self.dir_name + "\n"
        )
        FreeCAD.Console.PrintLog(
            "writerbasefistr --> self.include  -->  " + self.mesh_name + "\n"
        )
        FreeCAD.Console.PrintLog(
            "writerbasefistr --> self.include  -->  " + self.include + "\n"
        )

        self.write_FrontISTR_input()

        if self.femelement_count_test is True:
            return self.include
        else:
            FreeCAD.Console.PrintError(
                "Problems on writing input file, check report prints.\n\n"
            )
            return ""

    def write_FrontISTR_input(self):

        # mesh file and cntfile
        mshfile = self.write_mesh()
        cntfile = self.write_cnt()
        self.write_dat()
        
        # global settings
        self.write_global_setting(cntfile)

        # element and material sets
        self.write_element_sets_material_and_femelement_type(mshfile)

        # node sets and surface sets
        self.write_node_sets_constraints_fixed(mshfile)
        self.write_node_sets_constraints_displacement(mshfile)
        self.write_node_sets_constraints_planerotation(mshfile)
        self.write_surfaces_constraints_contact(mshfile)
        self.write_surfaces_constraints_tie(mshfile)
        self.write_surfaces_constraints_sectionprint(mshfile)
        self.write_node_sets_constraints_transform(mshfile)
        self.write_node_sets_constraints_temperature(mshfile)

        # materials and fem element types
        self.write_materials(mshfile,cntfile)
        self.write_constraints_initialtemperature(mshfile)
        self.write_femelementsets(mshfile)

        # Fluid sections:
        # not supported yet
        for femobj in self.material_objects:
            if femobj["Object"].Category == "Fluid":
                s = "FrontISTR Addon does not support fluid.\n"
                FreeCAD.Console.PrintWarning(s)
                if FreeCAD.GuiUp:
                    from PySide import QtGui
                    QtGui.QMessageBox.warning(None, "Not Supported", s)

        if self.fluidsection_objects:
            s = "FrontISTR Addon does not support fluid.\n"
            FreeCAD.Console.PrintWarning(s)
            if FreeCAD.GuiUp:
                from PySide import QtGui
                QtGui.QMessageBox.warning(None, "Not Supported", s)

        # Beam sections:
        # not supported yet
        if self.beamsection_objects:
            s = "FrontISTR Addon does not support beam.\n"
            FreeCAD.Console.PrintWarning(s)
            if FreeCAD.GuiUp:
                from PySide import QtGui
                QtGui.QMessageBox.warning(None, "Not Supported", s)

        # Shell sections:
        # not supported yet
        if self.shellthickness_objects:
            s = "FrontISTR Addon does not support shell.\n"
            FreeCAD.Console.PrintWarning(s)
            if FreeCAD.GuiUp:
                from PySide import QtGui
                QtGui.QMessageBox.warning(None, "Not Supported", s)

        # constraints independent from steps
        ## self.write_constraints_contact(cntfile)
        ## self.write_constraints_tie(cntfile)

        # constraints dependent from steps
        self.write_constraints_fixed(cntfile)
        self.write_constraints_displacement(cntfile)
        self.write_constraints_selfweight(cntfile)
        self.write_constraints_force(cntfile)
        self.write_constraints_pressure(cntfile)
        self.write_constraints_temperature(cntfile)
        self.write_constraints_heatflux(cntfile)

        # step control
        self.write_step(cntfile)

        # output
        self.write_outputs_types(cntfile)

        mshfile.close()
        cntfile.close()

    # ********************************************************************************************
    # mesh
    def write_mesh(self):
        # write mesh to file
        element_param = 1  # highest element order only
        group_param = False  # do not write mesh group data

        self.femmesh.writeABAQUS(
            self.msh_name,
            element_param,
            group_param
        )

        mshfile = codecs.open(self.msh_name, "a", encoding="utf-8")
        # delete **Define element set Eall 
        mshfile.seek(-56, os.SEEK_END)
        mshfile.truncate()

        return mshfile

    def write_cnt(self):
        cntfile = codecs.open(self.cnt_name, "w", encoding="utf-8")
        cntfile.write("#  Control File for FISTR\n")
        cntfile.write("## Analysis Control\n")
        cntfile.write("!VERSION\n")
        cntfile.write(" 3\n")

        return cntfile

    def write_dat(self):
        datfile = codecs.open(self.dat_name, "w", encoding="utf-8")
        datfile.write("!MESH, NAME=part_in,TYPE=ABAQUS\n")
        datfile.write(self.mesh_name+".inp\n")
        datfile.write("!MESH, NAME=part_out,TYPE=HECMW-DIST\n")
        datfile.write(self.mesh_name+".p\n")
        datfile.write("!MESH, NAME=fstrMSH, TYPE=HECMW-DIST\n")
        datfile.write(self.mesh_name+".p\n")
        datfile.write("!CONTROL, NAME=fstrCNT\n")
        datfile.write(self.mesh_name+".cnt\n")
        datfile.write("!RESULT, NAME=fstrRES, IO=OUT\n")
        datfile.write(self.mesh_name+".res\n")
        datfile.write("!RESULT, NAME=vis_out, IO=OUT\n")
        datfile.write(self.mesh_name+"_vis\n")
        datfile.close()
        
        partdatfile = codecs.open(self.part_dat_name, "w", encoding="utf-8")
        partdatfile.write("!PARTITION,TYPE=NODE-BASED,METHOD=PMETIS,DOMAIN={}\n"
                            .format("%d"%self.solver_obj.n_process))
        partdatfile.close()

    # ********************************************************************************************
    # constraints fixed
    def write_node_sets_constraints_fixed(self, f):
        if not self.fixed_objects:
            return
        # write for all analysis types

        # get nodes
        self.get_constraints_fixed_nodes()

        write_name = "constraints_fixed_node_sets"
        f.write("\n***********************************************************\n")
        f.write("** {}\n".format(write_name.replace("_", " ")))
        f.write("** written by {} function\n".format(sys._getframe().f_code.co_name))

        self.write_node_sets_nodes_constraints_fixed(f)

    def write_node_sets_nodes_constraints_fixed(self, f):
        # write nodes to file
        for femobj in self.fixed_objects:
            # femobj --> dict, FreeCAD document object is femobj["Object"]
            fix_obj = femobj["Object"]
            f.write("** " + fix_obj.Label + "\n")
            if self.femmesh.Volumes \
                    and (len(self.shellthickness_objects) > 0 or len(self.beamsection_objects) > 0):
                if len(femobj["NodesSolid"]) > 0:
                    f.write("*NSET,NSET=" + fix_obj.Name + "Solid\n")
                    for n in femobj["NodesSolid"]:
                        f.write(str(n) + ",\n")
                if len(femobj["NodesFaceEdge"]) > 0:
                    f.write("*NSET,NSET=" + fix_obj.Name + "FaceEdge\n")
                    for n in femobj["NodesFaceEdge"]:
                        f.write(str(n) + ",\n")
            else:
                f.write("*NSET,NSET=" + fix_obj.Name + "\n")
                for n in femobj["Nodes"]:
                    f.write(str(n) + ",\n")

    def write_constraints_fixed(self, f):
        if not self.fixed_objects:
            return
        # write for all analysis types

        self.isactive_boundary = True
        # write constraint to file
        f.write("## Fixed Constraints\n")
        f.write("## written by {} function\n".format(sys._getframe().f_code.co_name))
        for femobj in self.fixed_objects:
            # femobj --> dict, FreeCAD document object is femobj["Object"]
            f.write("## " + femobj["Object"].Label + "\n")
            fix_obj_name = " "+femobj["Object"].Name
            if self.femmesh.Volumes \
                    and (len(self.shellthickness_objects) > 0 or len(self.beamsection_objects) > 0):
                if len(femobj["NodesSolid"]) > 0:
                    f.write("!BOUNDARY, GRPID=1\n")
                    f.write(fix_obj_name + "Solid" + ",1,1\n")
                    f.write(fix_obj_name + "Solid" + ",2,2\n")
                    f.write(fix_obj_name + "Solid" + ",3,3\n")
                    f.write("\n")
                if len(femobj["NodesFaceEdge"]) > 0:
                    f.write("!BOUNDARY, GRPID=1\n")
                    f.write(fix_obj_name + "FaceEdge" + ",1,1\n")
                    f.write(fix_obj_name + "FaceEdge" + ",2,2\n")
                    f.write(fix_obj_name + "FaceEdge" + ",3,3\n")
                    f.write(fix_obj_name + "FaceEdge" + ",4,4\n")
                    f.write(fix_obj_name + "FaceEdge" + ",5,5\n")
                    f.write(fix_obj_name + "FaceEdge" + ",6,6\n")
                    f.write("\n")
            else:
                f.write("!BOUNDARY, GRPID=1\n")
                f.write(fix_obj_name + ",1,1\n")
                f.write(fix_obj_name + ",2,2\n")
                f.write(fix_obj_name + ",3,3\n")
                if self.beamsection_objects or self.shellthickness_objects:
                    f.write(fix_obj_name + ",4,4\n")
                    f.write(fix_obj_name + ",5,5\n")
                    f.write(fix_obj_name + ",6,6\n")
                f.write("\n")

    # ********************************************************************************************
    # constraints displacement
    def write_node_sets_constraints_displacement(self, f):
        if not self.displacement_objects:
            return
        # write for all analysis types

        # get nodes
        self.get_constraints_displacement_nodes()

        write_name = "constraints_displacement_node_sets"
        f.write("\n***********************************************************\n")
        f.write("** {}\n".format(write_name.replace("_", " ")))
        f.write("** written by {} function\n".format(sys._getframe().f_code.co_name))

        self.write_node_sets_nodes_constraints_displacement(f)

    def write_node_sets_nodes_constraints_displacement(self, f):
        # write nodes to file
        for femobj in self.displacement_objects:
            # femobj --> dict, FreeCAD document object is femobj["Object"]
            disp_obj = femobj["Object"]
            f.write("** " + disp_obj.Label + "\n")
            f.write("*NSET,NSET=" + disp_obj.Name + "\n")
            for n in femobj["Nodes"]:
                f.write(str(n) + ",\n")

    def write_constraints_displacement(self, f):
        if not self.displacement_objects:
            return
        # write for all analysis types

        self.isactive_boundary = True
        # write constraint to file
        f.write("## Displacement constraint applied\n")
        f.write("## written by {} function\n".format(sys._getframe().f_code.co_name))
        for femobj in self.displacement_objects:
            # femobj --> dict, FreeCAD document object is femobj["Object"]
            f.write("## " + femobj["Object"].Label + "\n")
            disp_obj = femobj["Object"]
            disp_obj_name = disp_obj.Name
            f.write("!BOUNDARY,GRPID=1\n")
            if disp_obj.xFix:
                f.write(disp_obj_name + ",1,1\n")
            elif not disp_obj.xFree:
                f.write(disp_obj_name + ",1,1," + str(disp_obj.xDisplacement) + "\n")
            if disp_obj.yFix:
                f.write(disp_obj_name + ",2,2\n")
            elif not disp_obj.yFree:
                f.write(disp_obj_name + ",2,2," + str(disp_obj.yDisplacement) + "\n")
            if disp_obj.zFix:
                f.write(disp_obj_name + ",3,3\n")
            elif not disp_obj.zFree:
                f.write(disp_obj_name + ",3,3," + str(disp_obj.zDisplacement) + "\n")

            if self.beamsection_objects or self.shellthickness_objects:
                if disp_obj.rotxFix:
                    f.write(disp_obj_name + ",4,4\n")
                elif not disp_obj.rotxFree:
                    f.write(disp_obj_name + ",4,4," + str(disp_obj.xRotation) + "\n")
                if disp_obj.rotyFix:
                    f.write(disp_obj_name + ",5,5\n")
                elif not disp_obj.rotyFree:
                    f.write(disp_obj_name + ",5,5," + str(disp_obj.yRotation) + "\n")
                if disp_obj.rotzFix:
                    f.write(disp_obj_name + ",6,6\n")
                elif not disp_obj.rotzFree:
                    f.write(disp_obj_name + ",6,6," + str(disp_obj.zRotation) + "\n")
        f.write("\n")

    # ********************************************************************************************
    # constraints planerotation
    def write_node_sets_constraints_planerotation(self, f):
        if not self.planerotation_objects:
            return
        # write for all analysis types
        s = "FrontISTR Addon does not support planerotation. \n"
        FreeCAD.Console.PrintWarning(s)
        if FreeCAD.GuiUp:
            from PySide import QtGui
            QtGui.QMessageBox.warning(None, "Not Supported", s)
        return

    # ********************************************************************************************
    # constraints contact
    def write_surfaces_constraints_contact(self, f):
        if not self.contact_objects:
            return
        # write for all analysis types
        s = "FrontISTR Addon does not support contact analysis. \n"
        FreeCAD.Console.PrintWarning(s)
        if FreeCAD.GuiUp:
            from PySide import QtGui
            QtGui.QMessageBox.warning(None, "Not Supported", s)
        return

        # get faces
        self.get_constraints_contact_faces()

        write_name = "constraints_contact_surface_sets"
        f.write("\n***********************************************************\n")
        f.write("** {}\n".format(write_name.replace("_", " ")))
        f.write("** written by {} function\n".format(sys._getframe().f_code.co_name))

        self.write_surfacefaces_constraints_contact(f)

    def write_surfacefaces_constraints_contact(self, f):
        # write faces to file
        for femobj in self.contact_objects:
            # femobj --> dict, FreeCAD document object is femobj["Object"]
            contact_obj = femobj["Object"]
            f.write("** " + contact_obj.Label + "\n")
            # slave DEP
            f.write("*SURFACE, NAME=DEP{}\n".format(contact_obj.Name))
            for i in femobj["ContactSlaveFaces"]:
                f.write("{},S{}\n".format(i[0], i[1]))
            # master IND
            f.write("*SURFACE, NAME=IND{}\n".format(contact_obj.Name))
            for i in femobj["ContactMasterFaces"]:
                f.write("{},S{}\n".format(i[0], i[1]))

    def write_constraints_contact(self, f):
        if not self.contact_objects:
            return
        # write for all analysis types

        # write constraint to file
        f.write("\n***********************************************************\n")
        f.write("** Contact Constraints\n")
        f.write("** written by {} function\n".format(sys._getframe().f_code.co_name))
        for femobj in self.contact_objects:
            # femobj --> dict, FreeCAD document object is femobj["Object"]
            contact_obj = femobj["Object"]
            f.write("** " + contact_obj.Label + "\n")
            f.write(
                "*CONTACT PAIR, INTERACTION=INT{},TYPE=SURFACE TO SURFACE\n"
                .format(contact_obj.Name)
            )
            ind_surf = "IND" + contact_obj.Name
            dep_surf = "DEP" + contact_obj.Name
            f.write(dep_surf + "," + ind_surf + "\n")
            f.write("*SURFACE INTERACTION, NAME=INT{}\n".format(contact_obj.Name))
            f.write("*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR\n")
            slope = contact_obj.Slope
            f.write(str(slope) + " \n")
            friction = contact_obj.Friction
            if friction > 0:
                f.write("*FRICTION \n")
                stick = (slope / 10.0)
                f.write(str(friction) + ", " + str(stick) + " \n")

    # ********************************************************************************************
    # constraints tie
    def write_surfaces_constraints_tie(self, f):
        if not self.tie_objects:
            return
        # write for all analysis types
        s = "FrontISTR Addon does not support tie. \n"
        FreeCAD.Console.PrintWarning(s)
        if FreeCAD.GuiUp:
            from PySide import QtGui
            QtGui.QMessageBox.warning(None, "Not Supported", s)
        return

        # get faces
        self.get_constraints_tie_faces()

        write_name = "constraints_tie_surface_sets"
        f.write("\n***********************************************************\n")
        f.write("** {}\n".format(write_name.replace("_", " ")))
        f.write("** written by {} function\n".format(sys._getframe().f_code.co_name))

        self.write_surfacefaces_constraints_tie(f)

    def write_surfacefaces_constraints_tie(self, f):
        # write faces to file
        for femobj in self.tie_objects:
            # femobj --> dict, FreeCAD document object is femobj["Object"]
            tie_obj = femobj["Object"]
            f.write("** " + tie_obj.Label + "\n")
            # slave DEP
            f.write("*SURFACE, NAME=TIE_DEP{}\n".format(tie_obj.Name))
            for i in femobj["TieSlaveFaces"]:
                f.write("{},S{}\n".format(i[0], i[1]))
            # master IND
            f.write("*SURFACE, NAME=TIE_IND{}\n".format(tie_obj.Name))
            for i in femobj["TieMasterFaces"]:
                f.write("{},S{}\n".format(i[0], i[1]))

    def write_constraints_tie(self, f):
        if not self.tie_objects:
            return
        # write for all analysis types

        # write constraint to file
        f.write("\n***********************************************************\n")
        f.write("** Tie Constraints\n")
        f.write("** written by {} function\n".format(sys._getframe().f_code.co_name))
        for femobj in self.tie_objects:
            # femobj --> dict, FreeCAD document object is femobj["Object"]
            tie_obj = femobj["Object"]
            f.write("** {}\n".format(tie_obj.Label))
            tolerance = str(tie_obj.Tolerance.getValueAs("mm")).rstrip()
            f.write(
                "*TIE, POSITION TOLERANCE={}, ADJUST=NO, NAME=TIE{}\n"
                .format(tolerance, tie_obj.Name)
            )
            ind_surf = "TIE_IND" + tie_obj.Name
            dep_surf = "TIE_DEP" + tie_obj.Name
            f.write("{},{}\n".format(dep_surf, ind_surf))

    # ********************************************************************************************
    # constraints sectionprint
    def write_surfaces_constraints_sectionprint(self, f):
        if not self.sectionprint_objects:
            return
        # write for all analysis types

        write_name = "constraints_sectionprint_surface_sets"
        f.write("\n***********************************************************\n")
        f.write("** {}\n".format(write_name.replace("_", " ")))
        f.write("** written by {} function\n".format(sys._getframe().f_code.co_name))

        self.write_surfacefaces_constraints_sectionprint(f)

    # TODO move code parts from this method to base writer module
    def write_surfacefaces_constraints_sectionprint(self, f):
        # get surface nodes and write them to file
        obj = 0
        for femobj in self.sectionprint_objects:
            # femobj --> dict, FreeCAD document object is femobj["Object"]
            sectionprint_obj = femobj["Object"]
            f.write("** " + sectionprint_obj.Label + "\n")
            obj = obj + 1
            for o, elem_tup in sectionprint_obj.References:
                for elem in elem_tup:
                    ref_shape = o.Shape.getElement(elem)
                    if ref_shape.ShapeType == "Face":
                        name = "SECTIONFACE" + str(obj)
                        f.write("*SURFACE, NAME=" + name + "\n")

                        v = self.mesh_object.FemMesh.getfistrVolumesByFace(ref_shape)
                        if len(v) > 0:
                            # volume elements found
                            FreeCAD.Console.PrintLog(
                                "{}, surface {}, {} touching volume elements found\n"
                                .format(sectionprint_obj.Label, name, len(v))
                            )
                            for i in v:
                                f.write("{},S{}\n".format(i[0], i[1]))
                        else:
                            # no volume elements found, shell elements not allowed
                            FreeCAD.Console.PrintError(
                                "{}, surface {}, Error: "
                                "No volume elements found!\n"
                                .format(sectionprint_obj.Label, name)
                            )
                            f.write("** Error: empty list\n")

    # ********************************************************************************************
    # constraints transform
    def write_node_sets_constraints_transform(self, f):
        if not self.transform_objects:
            return
        # write for all analysis type
        s = "FrontISTR Addon does not support transform. \n"
        FreeCAD.Console.PrintWarning(s)
        if FreeCAD.GuiUp:
            from PySide import QtGui
            QtGui.QMessageBox.warning(None, "Not Supported", s)
        return

    # ********************************************************************************************
    # constraints temperature
    def write_node_sets_constraints_temperature(self, f):
        if not self.temperature_objects:
            return
        if not self.analysis_type == "thermomech":
            return

        # get nodes
        self.get_constraints_temperature_nodes()

        write_name = "constraints_temperature_node_sets"
        f.write("\n***********************************************************\n")
        f.write("** {}\n".format(write_name.replace("_", " ")))
        f.write("** written by {} function\n".format(sys._getframe().f_code.co_name))

        self.write_node_sets_nodes_constraints_temperature(f)

    def write_node_sets_nodes_constraints_temperature(self, f):
        # write nodes to file
        for femobj in self.temperature_objects:
            # femobj --> dict, FreeCAD document object is femobj["Object"]
            temp_obj = femobj["Object"]
            f.write("** " + temp_obj.Label + "\n")
            f.write("*NSET,NSET=" + temp_obj.Name + "\n")
            for n in femobj["Nodes"]:
                f.write(str(n) + ",\n")

    def write_constraints_temperature(self, f):
        if not self.temperature_objects:
            return
        if not self.analysis_type == "thermomech":
            return

        self.isactive_load = True
        # write constraint to file
        f.write("## Fixed temperature constraint applied\n")
        f.write("## written by {} function\n".format(sys._getframe().f_code.co_name))
        for ftobj in self.temperature_objects:
            fixedtemp_obj = ftobj["Object"]
            f.write("## " + fixedtemp_obj.Label + "\n")
            NumberOfNodes = len(ftobj["Nodes"])
            if fixedtemp_obj.ConstraintType == "Temperature":
                f.write("!TEMPERATURE\n")
                f.write("{},{}\n".format(fixedtemp_obj.Name, fixedtemp_obj.Temperature))
                f.write("\n")
            elif fixedtemp_obj.ConstraintType == "CFlux":
                f.write("!CFLUX\n")
                f.write("{},11,{}\n".format(
                    fixedtemp_obj.Name,
                    fixedtemp_obj.CFlux * 0.001 / NumberOfNodes
                ))
                f.write("\n")

    # ********************************************************************************************
    # constraints initialtemperature
    def write_constraints_initialtemperature(self, f):
        if not self.initialtemperature_objects:
            return
        if not self.analysis_type == "thermomech":
            return

        self.isactive_load = True
        # write constraint to file
        f.write("\n***********************************************************\n")
        f.write("## Initial temperature constraint\n")
        f.write("## written by {} function\n".format(sys._getframe().f_code.co_name))
        f.write("!INITIAL CONDITIONS,TYPE=TEMPERATURE\n")
        for itobj in self.initialtemperature_objects:  # Should only be one
            inittemp_obj = itobj["Object"]
            # OvG: Initial temperature
            f.write("{0},{1}\n".format(self.fistr_nall, inittemp_obj.initialTemperature))

    # ********************************************************************************************
    # constraints selfweight
    def write_constraints_selfweight(self, f):
        if not self.selfweight_objects:
            return
        if not (self.analysis_type == "static" or self.analysis_type == "thermomech"):
            return

        self.isactive_load = True
        # write constraint to file
        f.write("## Self weight Constraint\n")
        f.write("## written by {} function\n".format(sys._getframe().f_code.co_name))
        for femobj in self.selfweight_objects:
            # femobj --> dict, FreeCAD document object is femobj["Object"]
            selwei_obj = femobj["Object"]
            f.write("## " + selwei_obj.Label + "\n")
            f.write("!DLOAD,GRPID=1\n")
            f.write(
                # elset, GRAV, magnitude, direction x, dir y ,dir z
                "{},GRAV,{},{},{},{}\n"
                .format(
                    " "+self.fistr_eall,
                    self.gravity,  # actual magnitude of gravity vector
                    selwei_obj.Gravity_x,  # coordinate x of normalized gravity vector
                    selwei_obj.Gravity_y,  # y
                    selwei_obj.Gravity_z  # z
                )
            )
            f.write("\n")
        # grav (erdbeschleunigung) is equal for all elements
        # should be only one constraint
        # different element sets for different density
        # are written in the material element sets already

    # ********************************************************************************************
    # constraints force
    def write_constraints_force(self, f):
        if not self.force_objects:
            return
        if not (self.analysis_type == "static" or self.analysis_type == "thermomech"):
            return

        self.isactive_load = True
        # check shape type of reference shape and get node loads
        self.get_constraints_force_nodeloads()

        write_name = "constraints_force_node_loads"
        f.write("## {}\n".format(write_name.replace("_", " ")))
        f.write("## written by {} function\n".format(sys._getframe().f_code.co_name))

        self.write_nodeloads_constraints_force(f)

    def write_nodeloads_constraints_force(self, f):
        # write node loads to file
        f.write("!CLOAD,GRPID=1\n")
        for femobj in self.force_objects:
            # femobj --> dict, FreeCAD document object is femobj["Object"]
            f.write("## " + femobj["Object"].Label + "\n")
            direction_vec = femobj["Object"].DirectionVector
            for ref_shape in femobj["NodeLoadTable"]:
                f.write("## " + ref_shape[0] + "\n")
                for n in sorted(ref_shape[1]):
                    node_load = ref_shape[1][n]
                    if (direction_vec.x != 0.0):
                        v1 = "{:.13E}".format(direction_vec.x * node_load)
                        f.write(str(n) + ",1," + v1 + "\n")
                    if (direction_vec.y != 0.0):
                        v2 = "{:.13E}".format(direction_vec.y * node_load)
                        f.write(str(n) + ",2," + v2 + "\n")
                    if (direction_vec.z != 0.0):
                        v3 = "{:.13E}".format(direction_vec.z * node_load)
                        f.write(str(n) + ",3," + v3 + "\n")
                f.write("\n")
            f.write("\n")

    # ********************************************************************************************
    # constraints pressure
    def write_constraints_pressure(self, f):
        if not self.pressure_objects:
            return
        if not (self.analysis_type == "static" or self.analysis_type == "thermomech"):
            return

        self.isactive_load = True
        # get the faces and face numbers
        self.get_constraints_pressure_faces()

        write_name = "constraints_pressure_element_face_loads"
        f.write("## {}\n".format(write_name.replace("_", " ")))
        f.write("## written by {} function\n".format(sys._getframe().f_code.co_name))

        self.write_faceloads_constraints_pressure(f)

    def write_faceloads_constraints_pressure(self, f):
        # write face loads to file
        for femobj in self.pressure_objects:
            # femobj --> dict, FreeCAD document object is femobj["Object"]
            prs_obj = femobj["Object"]
            f.write("## " + prs_obj.Label + "\n")
            rev = -1 if prs_obj.Reversed else 1
            f.write("!DLOAD,GRPID=1\n")
            for ref_shape in femobj["PressureFaces"]:
                # the loop is needed for compatibility reason
                # in deprecated method get_pressure_obj_faces_depreciated
                # the face ids where per ref_shape
                for face, fno in ref_shape[1]:
                    if fno > 0:  # solid mesh face
                        f.write("{},P{},{}\n".format(face, fno, rev * prs_obj.Pressure))
                    # on shell mesh face: fno == 0
                    # normal of element face == face normal
                    elif fno == 0:
                        f.write("{},S,{}\n".format(face, rev * prs_obj.Pressure))
                    # on shell mesh face: fno == -1
                    # normal of element face opposite direction face normal
                    elif fno == -1:
                        f.write("{},S,{}\n".format(face, -1 * rev * prs_obj.Pressure))

    # ********************************************************************************************
    # constraints heatflux
    def write_constraints_heatflux(self, f):
        if not self.heatflux_objects:
            return
        if not self.analysis_type == "thermomech":
            return

        write_name = "constraints_heatflux_element_face_heatflux"
        f.write("\n***********************************************************\n")
        f.write("** {}\n".format(write_name.replace("_", " ")))
        f.write("** written by {} function\n".format(sys._getframe().f_code.co_name))

        self.write_faceheatflux_constraints_heatflux(f)

    def write_faceheatflux_constraints_heatflux(self, f):
        # write heat flux faces to file
        for hfobj in self.heatflux_objects:
            heatflux_obj = hfobj["Object"]
            f.write("** " + heatflux_obj.Label + "\n")
            if heatflux_obj.ConstraintType == "Convection":
                f.write("*FILM\n")
                for o, elem_tup in heatflux_obj.References:
                    for elem in elem_tup:
                        ho = o.Shape.getElement(elem)
                        if ho.ShapeType == "Face":
                            v = self.mesh_object.FemMesh.getfistrVolumesByFace(ho)
                            f.write("** Heat flux on face {}\n".format(elem))
                            for i in v:
                                # SvdW: add factor to force heatflux to units system of t/mm/s/K
                                # OvG: Only write out the VolumeIDs linked to a particular face
                                f.write("{},F{},{},{}\n".format(
                                    i[0],
                                    i[1],
                                    heatflux_obj.AmbientTemp,
                                    heatflux_obj.FilmCoef * 0.001
                                ))
            elif heatflux_obj.ConstraintType == "DFlux":
                f.write("*DFLUX\n")
                for o, elem_tup in heatflux_obj.References:
                    for elem in elem_tup:
                        ho = o.Shape.getElement(elem)
                        if ho.ShapeType == "Face":
                            v = self.mesh_object.FemMesh.getfistrVolumesByFace(ho)
                            f.write("** Heat flux on face {}\n".format(elem))
                            for i in v:
                                f.write("{},S{},{}\n".format(
                                    i[0],
                                    i[1],
                                    heatflux_obj.DFlux * 0.001
                                ))

    # ********************************************************************************************
    # global settings
    def write_global_setting(self, f):
        # ANALYSIS type line
        #!SOLUTION, TYPE=STATIC
        # analysis line --> analysis type
        if self.analysis_type == "static":
            analysis_type = "STATIC"
        elif self.analysis_type == "heat":
            analysis_type = "HEAT"
        elif self.analysis_type == "eigen":
            analysis_type = "EIGEN"
        elif self.analysis_type == "dynamic":
            analysis_type = "DYNAMIC"
        elif self.analysis_type == "check":
            analysis_type = "ELEMCHECK"
        solution = "!SOLUTION, TYPE="+analysis_type
        # nonlinear
        if self.solver_obj.Nonlinearity == "yes":
            solution += ", NONLINEAR"
        f.write(solution+"\n")

        # CONTROLS line
        linearsolver = "!SOLVER"
        # setup linear equation solver
        solver_type = ""
        if self.solver_obj.MatrixSolverType == "CG":
            linearsolver += ",METHOD=CG"
            solver_type = "iterative"
        elif self.solver_obj.MatrixSolverType == "BiCGSTAB":
            linearsolver += ",METHOD=BiCGSTAB"
            solver_type = "iterative"
        elif self.solver_obj.MatrixSolverType == "GMRES":
            linearsolver += ",METHOD=GMRES"
            solver_type = "iterative"
        elif self.solver_obj.MatrixSolverType == "GPBiCG":
            linearsolver += ",METHOD=GPBiCG"
            solver_type = "iterative"
        elif self.solver_obj.MatrixSolverType == "MUMPS":
            linearsolver += ",METHOD=MUMPS"
            solver_type = "direct"
        elif self.solver_obj.MatrixSolverType == "DIRECT":
            linearsolver += ",METHOD=DIRECTmkl"
            solver_type = "direct"

        if solver_type == "iterative":
            # setup preconditioiner
            if self.solver_obj.MatrixPrecondType == "SSOR":
                linearsolver += ",PRECOND=1"
            elif self.solver_obj.MatrixPrecondType == "DIAG":
                linearsolver += ",PRECOND=3"
            elif self.solver_obj.MatrixPrecondType == "AMG":
                linearsolver += ",PRECOND=5"
            elif self.solver_obj.MatrixPrecondType == "ILU0":
                linearsolver += ",PRECOND=10"
            elif self.solver_obj.MatrixPrecondType == "ILU1":
                linearsolver += ",PRECOND=11"
            elif self.solver_obj.MatrixPrecondType == "ILU2":
                linearsolver += ",PRECOND=12"

        if self.solver_obj.MatrixSolverIterLog == "yes":
            linearsolver += ",ITERLOG=YES"
        else:
            linearsolver += ",ITERLOG=NO"
        if self.solver_obj.MatrixSolverTimeLog == "yes":
            linearsolver += ",TIMELOG=YES"
        else:
            linearsolver += ",TIMELOG=NO"
        f.write(linearsolver+"\n")

        # iteration number setting
        solveriter  = " {:d}".format(self.solver_obj.MatrixSolverNumIter)
        solveriter += ", 1\n"
        f.write(solveriter)

        # residual setting
        try:
            matrix_solver_residual_float = float(self.solver_obj.MatrixSolverResidual)
        except ValueError:
            matrix_solver_residual_float = 1.0e-6
            converting_string = "Converting Matrix Solver Residual value {} to float failed. Using default value 1.0E-6.".format(self.solver_obj.MatrixSolverResidual)
            FreeCAD.Console.PrintWarning(converting_string + "\n")
            if FreeCAD.GuiUp:
                from PySide import QtGui
                QtGui.QMessageBox.warning(None, "Converting value failed", converting_string)
        solverres  = " {:E}".format(matrix_solver_residual_float)
        solverres += ", 1.0, 0.0\n"
        solverres += "3, 1, 1, 2\n" #set AMG paramters
        f.write(solverres)

    # ********************************************************************************************
    # output types
    def write_outputs_types(self, f):
        f.write("### OUTPUT Control ###\n")
        #f.write("!WRITE,RESULT"+"\n")
        f.write("!WRITE,VISUAL,FREQUENCY=9999"+"\n")
        f.write("!OUTPUT_VIS"+"\n")
        f.write("PRINC_NSTRESS,ON"+"\n")
        f.write("!VISUAL,method=PSR"+"\n")
        f.write("!surface_num=1"+"\n")
        f.write("!surface 1"+"\n")
        fmtype = self.solver_obj.OutputFileFormat
        if fmtype == "AVS":
            f.write("!output_type=COMPLETE_AVS\n\n")
        elif fmtype == "VTK (paraview required)":
            f.write("!output_type=VTK\n\n")
        elif fmtype == "Binary VTK (paraview required)":
            f.write("!output_type=BIN_VTK\n\n")

    # ********************************************************************************************
    # step settings
    def write_step(self, f):
        f.write("### STEP Control ###\n")
        f.write("!AUTOINC_PARAM, NAME=AP1\n")
        f.write("0.25, 10, 50, 10, 1\n")
        f.write("1.25,  3,  3,  2, 2\n")
        f.write("0.25,  5\n")

        stepline = "!STEP,"
        if self.solver_obj.IncrementType == "auto":
            stepline += " INC_TYPE=AUTO"
        else:
            stepline += " INC_TYPE=FIXED"

        try:
            newton_converge_residual_float = float(self.solver_obj.NewtonConvergeResidual)
        except ValueError:
            newton_converge_residual_float = 1.0e-6
            converting_string = "Converting Newton Converge Residual value {} to float failed. Using default value 1.0E-6.".format(self.solver_obj.NewtonConvergeResidual)
            FreeCAD.Console.PrintWarning(converting_string + "\n")
            if FreeCAD.GuiUp:
                from PySide import QtGui
                QtGui.QMessageBox.warning(None, "Converting value failed", converting_string)
        stepline += ", CONVERG={:E}".format(newton_converge_residual_float)
        stepline += ", MAXITER={:d}".format(self.solver_obj.NewtonMaximumIteration)
        stepline += ", SUBSTEPS=10000"
        stepline += ", AUTOINCPARAM=AP1"
        f.write(stepline+"\n")

        timeline = " "
        if self.solver_obj.IncrementType == "auto":
            try:
                min_time_increment = float(self.solver_obj.MinimumTimeIncrement)
            except ValueError:
                min_time_increment = 1.0e-5
                converting_string = "Converting Newton Converge Residual value {} to float failed. Using default value 1.0E-5.".format(self.solver_obj.MinimumTimeIncrement)
                FreeCAD.Console.PrintWarning(converting_string + "\n")
                if FreeCAD.GuiUp:
                    from PySide import QtGui
                    QtGui.QMessageBox.warning(None, "Converting value failed", converting_string)

            timeline += "{:E}, {:E}, {:E}, {:E}".format(self.solver_obj.InitialTimeIncrement,
                                                        self.solver_obj.TimeEnd,
                                                        min_time_increment,
                                                        self.solver_obj.MaximumTimeIncrement)
        else:
            timeline += "{:E}, {:E}".format(self.solver_obj.InitialTimeIncrement,
                                            self.solver_obj.TimeEnd)
        f.write(timeline + "\n")
        if self.isactive_load:
            f.write("LOAD,1\n")
        if self.isactive_boundary:
            f.write("BOUNDARY,1\n")

    # ********************************************************************************************
    # material and fem element type
    def write_element_sets_material_and_femelement_type(self, f):
        f.write("\n***********************************************************\n")
        f.write("** Element sets for materials and FEM element type (solid, shell, beam)\n")
        f.write("** written by {} function\n".format(sys._getframe().f_code.co_name))

        # in any case if we have beams, we're going to need the element ids for the rotation elsets
        if self.beamsection_objects:
            # we will need to split the beam even for one beamobj
            # because no beam in z-direction can be used in fistr without a special adjustment
            # thus they need an own fistr_elset
            self.get_element_rotation1D_elements()

        # get the element ids for face and edge elements and write them into the objects
        if len(self.shellthickness_objects) > 1:
            self.get_element_geometry2D_elements()
        if len(self.beamsection_objects) > 1:
            self.get_element_geometry1D_elements()

        # get the element ids for material objects and write them into the material object
        if len(self.material_objects) > 1:
            self.get_material_elements()

        # create the fistr_elsets
        if len(self.material_objects) == 1:
            if self.femmesh.Volumes:
                # we only could do this for volumes, if a mesh contains volumes
                # we're going to use them in the analysis
                # but a mesh could contain the element faces of the volumes as faces
                # and the edges of the faces as edges
                # there we have to check for some geometric objects
                self.get_fistr_elsets_single_mat_solid()
            if len(self.shellthickness_objects) == 1:
                self.get_fistr_elsets_single_mat_single_shell()
            elif len(self.shellthickness_objects) > 1:
                self.get_fistr_elsets_single_mat_multiple_shell()
            if len(self.beamsection_objects) == 1:
                self.get_fistr_elsets_single_mat_single_beam()
            elif len(self.beamsection_objects) > 1:
                self.get_fistr_elsets_single_mat_multiple_beam()
        elif len(self.material_objects) > 1:
            if self.femmesh.Volumes:
                # we only could do this for volumes, if a mseh contains volumes
                # we're going to use them in the analysis
                # but a mesh could contain the element faces of the volumes as faces
                # and the edges of the faces as edges
                # there we have to check for some geometric objects
                # volume is a bit special
                # because retrieving ids from group mesh data is implemented
                self.get_fistr_elsets_multiple_mat_solid()
            if len(self.shellthickness_objects) == 1:
                self.get_fistr_elsets_multiple_mat_single_shell()
            elif len(self.shellthickness_objects) > 1:
                self.get_fistr_elsets_multiple_mat_multiple_shell()
            if len(self.beamsection_objects) == 1:
                self.get_fistr_elsets_multiple_mat_single_beam()
            elif len(self.beamsection_objects) > 1:
                self.get_fistr_elsets_multiple_mat_multiple_beam()

        # write fistr_elsets to file
        for fistr_elset in self.fistr_elsets:
            # use six to be sure to be Python 2.7 and 3.x compatible
            if isinstance(fistr_elset["fistr_elset"], six.string_types):
                elsetname = fistr_elset["fistr_elset"]
                if elsetname in fistr_elset.keys():
                    f.write("*ELSET,ELSET=" + fistr_elset["fistr_elset_name"] + "\n")
                    for elid in fistr_elset[elsetname]:
                        f.write(str(elid) + ",\n")
            else:
                f.write("*ELSET,ELSET=" + fistr_elset["fistr_elset_name"] + "\n")
                for elid in fistr_elset["fistr_elset"]:
                    f.write(str(elid) + ",\n")

    # self.fistr_elsets = [ {
    #                        "fistr_elset" : [e1, e2, e3, ... , en] or elements set name strings
    #                        "fistr_elset_name" : "fistr_identifier_elset"
    #                        "mat_obj_name" : "mat_obj.Name"
    #                        "fistr_mat_name" : "mat_obj.Material["Name"]"   !!! not unique !!!
    #                        "beamsection_obj" : "beamsection_obj"         if exists
    #                        "fluidsection_obj" : "fluidsection_obj"       if exists
    #                        "shellthickness_obj" : shellthickness_obj"    if exists
    #                        "beam_normal" : normal vector                 for beams only
    #                     },
    #                     {}, ... , {} ]

    # beam
    # TODO support multiple beamrotations
    # we do not need any more any data from the rotation document object,
    # thus we do not need to save the rotation document object name in the else
    def get_fistr_elsets_single_mat_single_beam(self):
        mat_obj = self.material_objects[0]["Object"]
        beamsec_obj = self.beamsection_objects[0]["Object"]
        beamrot_data = self.beamrotation_objects[0]
        for i, beamdirection in enumerate(beamrot_data["FEMRotations1D"]):
            # ID's for this direction
            elset_data = beamdirection["ids"]
            names = [
                {"short": "M0"},
                {"short": "B0"},
                {"short": beamrot_data["ShortName"]},
                {"short": "D" + str(i)}
            ]
            fistr_elset = {}
            fistr_elset["fistr_elset"] = elset_data
            fistr_elset["fistr_elset_name"] = get_fistr_elset_name_short(names)
            fistr_elset["mat_obj_name"] = mat_obj.Name
            fistr_elset["fistr_mat_name"] = mat_obj.Material["Name"]
            fistr_elset["beamsection_obj"] = beamsec_obj
            # normal for this direction
            fistr_elset["beam_normal"] = beamdirection["normal"]
            self.fistr_elsets.append(fistr_elset)

    def get_fistr_elsets_single_mat_multiple_beam(self):
        mat_obj = self.material_objects[0]["Object"]
        beamrot_data = self.beamrotation_objects[0]
        for beamsec_data in self.beamsection_objects:
            beamsec_obj = beamsec_data["Object"]
            beamsec_ids = set(beamsec_data["FEMElements"])
            for i, beamdirection in enumerate(beamrot_data["FEMRotations1D"]):
                beamdir_ids = set(beamdirection["ids"])
                # empty intersection sets possible
                elset_data = list(sorted(beamsec_ids.intersection(beamdir_ids)))
                if elset_data:
                    names = [
                        {"short": "M0"},
                        {"short": beamsec_data["ShortName"]},
                        {"short": beamrot_data["ShortName"]},
                        {"short": "D" + str(i)}
                    ]
                    fistr_elset = {}
                    fistr_elset["fistr_elset"] = elset_data
                    fistr_elset["fistr_elset_name"] = get_fistr_elset_name_short(names)
                    fistr_elset["mat_obj_name"] = mat_obj.Name
                    fistr_elset["fistr_mat_name"] = mat_obj.Material["Name"]
                    fistr_elset["beamsection_obj"] = beamsec_obj
                    # normal for this direction
                    fistr_elset["beam_normal"] = beamdirection["normal"]
                    self.fistr_elsets.append(fistr_elset)

    def get_fistr_elsets_multiple_mat_single_beam(self):
        beamsec_obj = self.beamsection_objects[0]["Object"]
        beamrot_data = self.beamrotation_objects[0]
        for mat_data in self.material_objects:
            mat_obj = mat_data["Object"]
            mat_ids = set(mat_data["FEMElements"])
            for i, beamdirection in enumerate(beamrot_data["FEMRotations1D"]):
                beamdir_ids = set(beamdirection["ids"])
                elset_data = list(sorted(mat_ids.intersection(beamdir_ids)))
                if elset_data:
                    names = [
                        {"short": mat_data["ShortName"]},
                        {"short": "B0"},
                        {"short": beamrot_data["ShortName"]},
                        {"short": "D" + str(i)}
                    ]
                    fistr_elset = {}
                    fistr_elset["fistr_elset"] = elset_data
                    fistr_elset["fistr_elset_name"] = get_fistr_elset_name_short(names)
                    fistr_elset["mat_obj_name"] = mat_obj.Name
                    fistr_elset["fistr_mat_name"] = mat_obj.Material["Name"]
                    fistr_elset["beamsection_obj"] = beamsec_obj
                    # normal for this direction
                    fistr_elset["beam_normal"] = beamdirection["normal"]
                    self.fistr_elsets.append(fistr_elset)

    def get_fistr_elsets_multiple_mat_multiple_beam(self):
        beamrot_data = self.beamrotation_objects[0]
        for beamsec_data in self.beamsection_objects:
            beamsec_obj = beamsec_data["Object"]
            beamsec_ids = set(beamsec_data["FEMElements"])
            for mat_data in self.material_objects:
                mat_obj = mat_data["Object"]
                mat_ids = set(mat_data["FEMElements"])
                for i, beamdirection in enumerate(beamrot_data["FEMRotations1D"]):
                    beamdir_ids = set(beamdirection["ids"])
                    # empty intersection sets possible
                    elset_data = list(sorted(
                        beamsec_ids.intersection(mat_ids).intersection(beamdir_ids)
                    ))
                    if elset_data:
                        names = [
                            {"short": mat_data["ShortName"]},
                            {"short": beamsec_data["ShortName"]},
                            {"short": beamrot_data["ShortName"]},
                            {"short": "D" + str(i)}
                        ]
                        fistr_elset = {}
                        fistr_elset["fistr_elset"] = elset_data
                        fistr_elset["fistr_elset_name"] = get_fistr_elset_name_short(names)
                        fistr_elset["mat_obj_name"] = mat_obj.Name
                        fistr_elset["fistr_mat_name"] = mat_obj.Material["Name"]
                        fistr_elset["beamsection_obj"] = beamsec_obj
                        # normal for this direction
                        fistr_elset["beam_normal"] = beamdirection["normal"]
                        self.fistr_elsets.append(fistr_elset)

    # fluid
    def get_fistr_elsets_single_mat_single_fluid(self):
        mat_obj = self.material_objects[0]["Object"]
        fluidsec_obj = self.fluidsection_objects[0]["Object"]
        elset_data = self.fistr_eedges
        names = [{"short": "M0"}, {"short": "F0"}]
        fistr_elset = {}
        fistr_elset["fistr_elset"] = elset_data
        fistr_elset["fistr_elset_name"] = get_fistr_elset_name_short(names)
        fistr_elset["mat_obj_name"] = mat_obj.Name
        fistr_elset["fistr_mat_name"] = mat_obj.Material["Name"]
        fistr_elset["fluidsection_obj"] = fluidsec_obj
        self.fistr_elsets.append(fistr_elset)

    def get_fistr_elsets_single_mat_multiple_fluid(self):
        mat_obj = self.material_objects[0]["Object"]
        for fluidsec_data in self.fluidsection_objects:
            fluidsec_obj = fluidsec_data["Object"]
            elset_data = fluidsec_data["FEMElements"]
            names = [{"short": "M0"}, {"short": fluidsec_data["ShortName"]}]
            fistr_elset = {}
            fistr_elset["fistr_elset"] = elset_data
            fistr_elset["fistr_elset_name"] = get_fistr_elset_name_short(names)
            fistr_elset["mat_obj_name"] = mat_obj.Name
            fistr_elset["fistr_mat_name"] = mat_obj.Material["Name"]
            fistr_elset["fluidsection_obj"] = fluidsec_obj
            self.fistr_elsets.append(fistr_elset)

    def get_fistr_elsets_multiple_mat_single_fluid(self):
        fluidsec_obj = self.fluidsection_objects[0]["Object"]
        for mat_data in self.material_objects:
            mat_obj = mat_data["Object"]
            elset_data = mat_data["FEMElements"]
            names = [{"short": mat_data["ShortName"]}, {"short": "F0"}]
            fistr_elset = {}
            fistr_elset["fistr_elset"] = elset_data
            fistr_elset["fistr_elset_name"] = get_fistr_elset_name_short(names)
            fistr_elset["mat_obj_name"] = mat_obj.Name
            fistr_elset["fistr_mat_name"] = mat_obj.Material["Name"]
            fistr_elset["fluidsection_obj"] = fluidsec_obj
            self.fistr_elsets.append(fistr_elset)

    def get_fistr_elsets_multiple_mat_multiple_fluid(self):
        for fluidsec_data in self.fluidsection_objects:
            fluidsec_obj = fluidsec_data["Object"]
            for mat_data in self.material_objects:
                mat_obj = mat_data["Object"]
                fluidsec_ids = set(fluidsec_data["FEMElements"])
                mat_ids = set(mat_data["FEMElements"])
                # empty intersection sets possible
                elset_data = list(sorted(fluidsec_ids.intersection(mat_ids)))
                if elset_data:
                    names = [
                        {"short": mat_data["ShortName"]},
                        {"short": fluidsec_data["ShortName"]}
                    ]
                    fistr_elset = {}
                    fistr_elset["fistr_elset"] = elset_data
                    fistr_elset["fistr_elset_name"] = get_fistr_elset_name_short(names)
                    fistr_elset["mat_obj_name"] = mat_obj.Name
                    fistr_elset["fistr_mat_name"] = mat_obj.Material["Name"]
                    fistr_elset["fluidsection_obj"] = fluidsec_obj
                    self.fistr_elsets.append(fistr_elset)

    # shell
    def get_fistr_elsets_single_mat_single_shell(self):
        mat_obj = self.material_objects[0]["Object"]
        shellth_obj = self.shellthickness_objects[0]["Object"]
        elset_data = self.fistr_efaces
        names = [
            {"long": mat_obj.Name, "short": "M0"},
            {"long": shellth_obj.Name, "short": "S0"}
        ]
        fistr_elset = {}
        fistr_elset["fistr_elset"] = elset_data
        fistr_elset["fistr_elset_name"] = get_fistr_elset_name_standard(names)
        fistr_elset["mat_obj_name"] = mat_obj.Name
        fistr_elset["fistr_mat_name"] = mat_obj.Material["Name"]
        fistr_elset["shellthickness_obj"] = shellth_obj
        self.fistr_elsets.append(fistr_elset)

    def get_fistr_elsets_single_mat_multiple_shell(self):
        mat_obj = self.material_objects[0]["Object"]
        for shellth_data in self.shellthickness_objects:
            shellth_obj = shellth_data["Object"]
            elset_data = shellth_data["FEMElements"]
            names = [
                {"long": mat_obj.Name, "short": "M0"},
                {"long": shellth_obj.Name, "short": shellth_data["ShortName"]}
            ]
            fistr_elset = {}
            fistr_elset["fistr_elset"] = elset_data
            fistr_elset["fistr_elset_name"] = get_fistr_elset_name_standard(names)
            fistr_elset["mat_obj_name"] = mat_obj.Name
            fistr_elset["fistr_mat_name"] = mat_obj.Material["Name"]
            fistr_elset["shellthickness_obj"] = shellth_obj
            self.fistr_elsets.append(fistr_elset)

    def get_fistr_elsets_multiple_mat_single_shell(self):
        shellth_obj = self.shellthickness_objects[0]["Object"]
        for mat_data in self.material_objects:
            mat_obj = mat_data["Object"]
            elset_data = mat_data["FEMElements"]
            names = [
                {"long": mat_obj.Name, "short": mat_data["ShortName"]},
                {"long": shellth_obj.Name, "short": "S0"}
            ]
            fistr_elset = {}
            fistr_elset["fistr_elset"] = elset_data
            fistr_elset["fistr_elset_name"] = get_fistr_elset_name_standard(names)
            fistr_elset["mat_obj_name"] = mat_obj.Name
            fistr_elset["fistr_mat_name"] = mat_obj.Material["Name"]
            fistr_elset["shellthickness_obj"] = shellth_obj
            self.fistr_elsets.append(fistr_elset)

    def get_fistr_elsets_multiple_mat_multiple_shell(self):
        for shellth_data in self.shellthickness_objects:
            shellth_obj = shellth_data["Object"]
            for mat_data in self.material_objects:
                mat_obj = mat_data["Object"]
                shellth_ids = set(shellth_data["FEMElements"])
                mat_ids = set(mat_data["FEMElements"])
                # empty intersection sets possible
                elset_data = list(sorted(shellth_ids.intersection(mat_ids)))
                if elset_data:
                    names = [
                        {"long": mat_obj.Name, "short": mat_data["ShortName"]},
                        {"long": shellth_obj.Name, "short": shellth_data["ShortName"]}
                    ]
                    fistr_elset = {}
                    fistr_elset["fistr_elset"] = elset_data
                    fistr_elset["fistr_elset_name"] = get_fistr_elset_name_standard(names)
                    fistr_elset["mat_obj_name"] = mat_obj.Name
                    fistr_elset["fistr_mat_name"] = mat_obj.Material["Name"]
                    fistr_elset["shellthickness_obj"] = shellth_obj
                    self.fistr_elsets.append(fistr_elset)

    # solid
    def get_fistr_elsets_single_mat_solid(self):
        mat_obj = self.material_objects[0]["Object"]
        elset_data = self.fistr_evolumes
        names = [
            {"long": mat_obj.Name, "short": "M0"},
            {"long": "Solid", "short": "Solid"}
        ]
        fistr_elset = {}
        fistr_elset["fistr_elset"] = elset_data
        fistr_elset["fistr_elset_name"] = get_fistr_elset_name_standard(names)
        fistr_elset["mat_obj_name"] = mat_obj.Name
        fistr_elset["fistr_mat_name"] = mat_obj.Material["Name"]
        self.fistr_elsets.append(fistr_elset)

    def get_fistr_elsets_multiple_mat_solid(self):
        for mat_data in self.material_objects:
            mat_obj = mat_data["Object"]
            elset_data = mat_data["FEMElements"]
            names = [
                {"long": mat_obj.Name, "short": mat_data["ShortName"]},
                {"long": "Solid", "short": "Solid"}
            ]
            fistr_elset = {}
            fistr_elset["fistr_elset"] = elset_data
            fistr_elset["fistr_elset_name"] = get_fistr_elset_name_standard(names)
            fistr_elset["mat_obj_name"] = mat_obj.Name
            fistr_elset["fistr_mat_name"] = mat_obj.Material["Name"]
            self.fistr_elsets.append(fistr_elset)

    def write_materials(self, f, fcnt):
        f.write("\n***********************************************************\n")
        f.write("** Materials\n")
        f.write("** written by {} function\n".format(sys._getframe().f_code.co_name))
        f.write("** Young\'s modulus unit is MPa = N/mm2\n")
        fcnt.write("## Materials\n")
        fcnt.write("## written by {} function\n".format(sys._getframe().f_code.co_name))
        fcnt.write("## Young\'s modulus unit is MPa = N/mm2\n")
        if self.analysis_type == "frequency" \
                or self.selfweight_objects \
                or (
                    self.analysis_type == "thermomech"
                    and not self.solver_obj.ThermoMechSteadyState
                ):
            f.write("** Density\'s unit is t/mm^3\n")
            fcnt.write("## Density\'s unit is t/mm^3\n")
        if self.analysis_type == "thermomech":
            f.write("** Thermal conductivity unit is kW/mm/K = t*mm/K*s^3\n")
            f.write("** Specific Heat unit is kJ/t/K = mm^2/s^2/K\n")
            fcnt.write("## Thermal conductivity unit is kW/mm/K = t*mm/K*s^3\n")
            fcnt.write("## Specific Heat unit is kJ/t/K = mm^2/s^2/K\n")
        for femobj in self.material_objects:
            # femobj --> dict, FreeCAD document object is femobj["Object"]
            mat_obj = femobj["Object"]
            mat_info_name = mat_obj.Material["Name"]
            mat_name = mat_obj.Name
            mat_label = mat_obj.Label
            # get material properties of solid material, Currently in SI units: M/kg/s/Kelvin
            if mat_obj.Category == "Solid":
                YM = FreeCAD.Units.Quantity(mat_obj.Material["YoungsModulus"])
                YM_in_MPa = float(YM.getValueAs("MPa"))
                PR = float(mat_obj.Material["PoissonRatio"])
            if self.analysis_type == "frequency" \
                    or self.selfweight_objects \
                    or (
                        self.analysis_type == "thermomech"
                        and not self.solver_obj.ThermoMechSteadyState
                    ):
                density = FreeCAD.Units.Quantity(mat_obj.Material["Density"])
                density_in_tonne_per_mm3 = float(density.getValueAs("t/mm^3"))
            if self.analysis_type == "thermomech":
                TC = FreeCAD.Units.Quantity(mat_obj.Material["ThermalConductivity"])
                # SvdW: Add factor to force units to results base units
                # of t/mm/s/K - W/m/K results in no factor needed
                TC_in_WmK = float(TC.getValueAs("W/m/K"))
                SH = FreeCAD.Units.Quantity(mat_obj.Material["SpecificHeat"])
                # SvdW: Add factor to force units to results base units of t/mm/s/K
                SH_in_JkgK = float(SH.getValueAs("J/kg/K")) * 1e+06
                if mat_obj.Category == "Solid":
                    TEC = FreeCAD.Units.Quantity(mat_obj.Material["ThermalExpansionCoefficient"])
                    TEC_in_mmK = float(TEC.getValueAs("mm/mm/K"))
                elif mat_obj.Category == "Fluid":
                    DV = FreeCAD.Units.Quantity(mat_obj.Material["DynamicViscosity"])
                    DV_in_tmms = float(DV.getValueAs("t/mm/s"))
            # write material properties
            f.write("** FreeCAD material name: " + mat_info_name + "\n")
            f.write("** " + mat_label + "\n")
            f.write("*MATERIAL, NAME=" + mat_name + "\n")
            fcnt.write("## FreeCAD material name: " + mat_info_name + "\n")
            fcnt.write("## " + mat_label + "\n")
            fcnt.write("!MATERIAL, NAME=" + mat_name + "\n")
            if mat_obj.Category == "Solid":
                f.write("*ELASTIC\n")
                f.write("{0:.0f}, {1:.3f}\n".format(YM_in_MPa, PR))
                fcnt.write("!ELASTIC\n")
                fcnt.write("{0:.0f}, {1:.3f}\n".format(YM_in_MPa, PR))

            if self.analysis_type == "frequency" \
                    or self.selfweight_objects \
                    or (
                        self.analysis_type == "thermomech"
                        and not self.solver_obj.ThermoMechSteadyState
                    ):
                f.write("*DENSITY\n")
                f.write("{0:.3e}\n".format(density_in_tonne_per_mm3))
                fcnt.write("!DENSITY\n")
                fcnt.write("{0:.3e}\n".format(density_in_tonne_per_mm3))
            if self.analysis_type == "thermomech":
                if mat_obj.Category == "Solid":
                    f.write("*CONDUCTIVITY\n")
                    f.write("{0:.3f}\n".format(TC_in_WmK))
                    f.write("*EXPANSION\n")
                    f.write("{0:.3e}\n".format(TEC_in_mmK))
                    f.write("*SPECIFIC HEAT\n")
                    f.write("{0:.3e}\n".format(SH_in_JkgK))

            # nonlinear material properties
            if self.solver_obj.Nonlinearity == "nonlinear":
                for nlfemobj in self.material_nonlinear_objects:
                    # femobj --> dict, FreeCAD document object is nlfemobj["Object"]
                    nl_mat_obj = nlfemobj["Object"]
                    if nl_mat_obj.LinearBaseMaterial == mat_obj:
                        if nl_mat_obj.MaterialModelNonlinearity == "simple hardening":
                            fcnt.write("!PLASTIC,YIELD=MISES,HARDEN=MULTILINEAR\n")
                            if nl_mat_obj.YieldPoint1:
                                f.write(nl_mat_obj.YieldPoint1 + ", 0.0\n")
                    f.write("\n")

    def write_femelementsets(self, f):
        f.write("\n***********************************************************\n")
        f.write("** Sections\n")
        f.write("** written by {} function\n".format(sys._getframe().f_code.co_name))
        for fistr_elset in self.fistr_elsets:
            if fistr_elset["fistr_elset"]:
                if "beamsection_obj"in fistr_elset:  # beam mesh
                    beamsec_obj = fistr_elset["beamsection_obj"]
                    elsetdef = "ELSET=ALL, "
                    #elsetdef = "ELSET=" + fistr_elset["fistr_elset_name"] + ", "
                    material = "MATERIAL=" + fistr_elset["mat_obj_name"]
                    normal = fistr_elset["beam_normal"]
                    if beamsec_obj.SectionType == "Rectangular":
                        height = beamsec_obj.RectHeight.getValueAs("mm")
                        width = beamsec_obj.RectWidth.getValueAs("mm")
                        section_type = ", SECTION=RECT"
                        section_geo = str(height) + ", " + str(width) + "\n"
                        section_def = "*BEAM SECTION, {}{}{}\n".format(
                            elsetdef,
                            material,
                            section_type
                        )
                    elif beamsec_obj.SectionType == "Circular":
                        radius = 0.5 * beamsec_obj.CircDiameter.getValueAs("mm")
                        section_type = ", SECTION=CIRC"
                        section_geo = str(radius) + "\n"
                        section_def = "*BEAM SECTION, {}{}{}\n".format(
                            elsetdef,
                            material,
                            section_type
                        )
                    elif beamsec_obj.SectionType == "Pipe":
                        radius = 0.5 * beamsec_obj.PipeDiameter.getValueAs("mm")
                        thickness = beamsec_obj.PipeThickness.getValueAs("mm")
                        section_type = ", SECTION=PIPE"
                        section_geo = str(radius) + ", " + str(thickness) + "\n"
                        section_def = "*BEAM GENERAL SECTION, {}{}{}\n".format(
                            elsetdef,
                            material,
                            section_type
                        )
                    # see forum topic for output formatting of rotation
                    # https://forum.freecadweb.org/viewtopic.php?f=18&t=46133&p=405142#p405142
                    section_nor = "{:f}, {:f}, {:f}\n".format(
                        normal[0],
                        normal[1],
                        normal[2]
                    )
                    f.write(section_def)
                    f.write(section_geo)
                    f.write(section_nor)
                elif "shellthickness_obj"in fistr_elset:  # shell mesh
                    shellth_obj = fistr_elset["shellthickness_obj"]
                    elsetdef = "ELSET=ALL, "
                    #elsetdef = "ELSET=" + fistr_elset["fistr_elset_name"] + ", "
                    material = "MATERIAL=" + fistr_elset["mat_obj_name"]
                    section_def = "*SHELL SECTION, " + elsetdef + material + "\n"
                    section_geo = str(shellth_obj.Thickness.getValueAs("mm")) + "\n"
                    f.write(section_def)
                    f.write(section_geo)
                else:  # solid mesh
                    elsetdef = "ELSET=ALL, "
                    #elsetdef = "ELSET=" + fistr_elset["fistr_elset_name"] + ", "
                    material = "MATERIAL=" + fistr_elset["mat_obj_name"]
                    section_def = "*SOLID SECTION, " + elsetdef + material + "\n"
                    f.write(section_def)


# ************************************************************************************************
# Helpers
# fistr elset names:
# M .. Material
# B .. Beam
# R .. BeamRotation
# D ..Direction
# F .. Fluid
# S .. Shell,
# TODO write comment into input file to elset ids and elset attributes
def get_fistr_elset_name_standard(names):
    # standard max length = 80
    fistr_elset_name = ""
    for name in names:
        fistr_elset_name += name["long"]
    if len(fistr_elset_name) < 81:
        return fistr_elset_name
    else:
        fistr_elset_name = ""
        for name in names:
            fistr_elset_name += name["short"]
        if len(fistr_elset_name) < 81:
            return fistr_elset_name
        else:
            error = (
                "FEM: Trouble in fistr input file, because an "
                "elset name is longer than 80 character! {}\n"
                .format(fistr_elset_name)
            )
            raise Exception(error)


def get_fistr_elset_name_short(names):
    # restricted max length = 20 (beam elsets)
    fistr_elset_name = ""
    for name in names:
        fistr_elset_name += name["short"]
    if len(fistr_elset_name) < 21:
        return fistr_elset_name
    else:
        error = (
            "FEM: Trouble in fistr input file, because an"
            "beam elset name is longer than 20 character! {}\n"
            .format(fistr_elset_name)
        )
        raise Exception(error)


def is_fluid_section_inlet_outlet(fistr_elsets):
    """ Fluid section: Inlet and Outlet requires special element definition
    """
    for fistr_elset in fistr_elsets:
        if fistr_elset["fistr_elset"]:
            if "fluidsection_obj" in fistr_elset:  # fluid mesh
                fluidsec_obj = fistr_elset["fluidsection_obj"]
                if fluidsec_obj.SectionType == "Liquid":
                    if (fluidsec_obj.LiquidSectionType == "PIPE INLET") \
                            or (fluidsec_obj.LiquidSectionType == "PIPE OUTLET"):
                        return True
    return False


def liquid_section_def(obj, section_type):
    if section_type == "PIPE MANNING":
        manning_area = str(obj.ManningArea.getValueAs("mm^2").Value)
        manning_radius = str(obj.ManningRadius.getValueAs("mm"))
        manning_coefficient = str(obj.ManningCoefficient)
        section_geo = manning_area + "," + manning_radius + "," + manning_coefficient + "\n"
        return section_geo
    elif section_type == "PIPE ENLARGEMENT":
        enlarge_area1 = str(obj.EnlargeArea1.getValueAs("mm^2").Value)
        enlarge_area2 = str(obj.EnlargeArea2.getValueAs("mm^2").Value)
        section_geo = enlarge_area1 + "," + enlarge_area2 + "\n"
        return section_geo
    elif section_type == "PIPE CONTRACTION":
        contract_area1 = str(obj.ContractArea1.getValueAs("mm^2").Value)
        contract_area2 = str(obj.ContractArea2.getValueAs("mm^2").Value)
        section_geo = contract_area1 + "," + contract_area2 + "\n"
        return section_geo
    elif section_type == "PIPE ENTRANCE":
        entrance_pipe_area = str(obj.EntrancePipeArea.getValueAs("mm^2").Value)
        entrance_area = str(obj.EntranceArea.getValueAs("mm^2").Value)
        section_geo = entrance_pipe_area + "," + entrance_area + "\n"
        return section_geo
    elif section_type == "PIPE DIAPHRAGM":
        diaphragm_pipe_area = str(obj.DiaphragmPipeArea.getValueAs("mm^2").Value)
        diaphragm_area = str(obj.DiaphragmArea.getValueAs("mm^2").Value)
        section_geo = diaphragm_pipe_area + "," + diaphragm_area + "\n"
        return section_geo
    elif section_type == "PIPE BEND":
        bend_pipe_area = str(obj.BendPipeArea.getValueAs("mm^2").Value)
        bend_radius_diameter = str(obj.BendRadiusDiameter)
        bend_angle = str(obj.BendAngle)
        bend_loss_coefficient = str(obj.BendLossCoefficient)
        section_geo = ("{},{},{},{}\n".format(
            bend_pipe_area,
            bend_radius_diameter,
            bend_angle,
            bend_loss_coefficient
        ))
        return section_geo
    elif section_type == "PIPE GATE VALVE":
        gatevalve_pipe_area = str(obj.GateValvePipeArea.getValueAs("mm^2").Value)
        gatevalve_closing_coeff = str(obj.GateValveClosingCoeff)
        section_geo = gatevalve_pipe_area + "," + gatevalve_closing_coeff + "\n"
        return section_geo
    elif section_type == "PIPE WHITE-COLEBROOK":
        colebrooke_area = str(obj.ColebrookeArea.getValueAs("mm^2").Value)
        colebrooke_diameter = str(2 * obj.ColebrookeRadius.getValueAs("mm"))
        colebrooke_grain_diameter = str(obj.ColebrookeGrainDiameter.getValueAs("mm"))
        colebrooke_form_factor = str(obj.ColebrookeFormFactor)
        section_geo = ("{},{},{},{},{}\n".format(
            colebrooke_area,
            colebrooke_diameter,
            "-1",
            colebrooke_grain_diameter,
            colebrooke_form_factor
        ))
        return section_geo
    elif section_type == "LIQUID PUMP":
        section_geo = ""
        for i in range(len(obj.PumpFlowRate)):
            flow_rate = str(obj.PumpFlowRate[i])
            head = str(obj.PumpHeadLoss[i])
            section_geo = section_geo + flow_rate + "," + head + ","
        section_geo = section_geo + "\n"
        return section_geo
    else:
        return ""
##  @}

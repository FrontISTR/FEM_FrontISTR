# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Frantisek Loeffelmann <LoffF@email.cz>           *
# *   Copyright (c) 2023 FrontISTR Commons <https://www.frontistr.com/>     *
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

__title__ = "FreeCAD .msh file reader"
__author__ = "FrontISTR Commons"
__url__ = "https://www.frontistr.com/"

## @package importInpMesh
#  \ingroup FEM
#  \brief FreeCAD INP file reader for FEM workbench

import FreeCAD
import os


# ********* generic FreeCAD import and export methods *********
if open.__module__ == '__builtin__':
    # because we'll redefine open below (Python2)
    pyopen = open
elif open.__module__ == 'io':
    # because we'll redefine open below (Python3)
    pyopen = open


def open(filename):
    "called when freecad opens a file"
    docname = os.path.splitext(os.path.basename(filename))[0]
    insert(filename, docname)


def insert(filename, docname):
    "called when freecad wants to import a file"
    try:
        doc = FreeCAD.getDocument(docname)
    except NameError:
        doc = FreeCAD.newDocument(docname)
    FreeCAD.ActiveDocument = doc
    import_msh_fistr(filename)


# ********* module specific methods *********
def read(filename):
    '''read a FemMesh from a msh mesh file and return the FemMesh
    '''
    # no document object is created, just the FemMesh is returned
    mesh_data = read_msh_fistr(filename)
    from feminout import importToolsFem
    return importToolsFem.make_femmesh(mesh_data)


def import_msh_fistr(filename):
    '''read a FEM mesh from a msh mesh file and insert a FreeCAD FEM Mesh object in the ActiveDocument
    '''
    femmesh = read(filename)
    mesh_name = os.path.splitext(os.path.basename(filename))[0]
    if femmesh:
        mesh_object = FreeCAD.ActiveDocument.addObject('Fem::FemMeshObject', mesh_name)
        mesh_object.FemMesh = femmesh
        FreeCAD.ActiveDocument.recompute()


def read_msh_fistr(filename):
    '''read .msh file '''
    # ATM only mesh reading is supported (no boundary conditions, node/element gropus, material definitions)

    class elements():

        tria3 = {}
        tria6 = {}
        quad4 = {}
        quad8 = {}
        tetra4 = {}
        tetra10 = {}
        hexa8 = {}
        hexa20 = {}
        penta6 = {}
        penta15 = {}
        seg2 = {}
        seg3 = {}
    error_seg3 = False  # to print "not supported"
    nodes = {}
    model_definition = True

    f = pyopen(filename, "r")
    line = "\n"
    include = ""
    f_include = None
    while line != "":
        if include:
            line = f_include.readline()
            if line == "":
                f_include.close()
                include = ""
                line = f.readline()
        else:
            line = f.readline()
        if line.strip() == '':
            continue
        elif line[0] == "#":  # comments
            continue
        elif line[0] == "!":
            if line[:2] == "!!":  # comments
                continue
            # elif line[:7].upper() == "!HEADER":
            #     continue
            read_node = False
            elm_category = []
            elm_2nd_line = False


        # reading nodes
        if (line[:5].upper() == "!NODE") and (model_definition is True):
            read_node = True
        elif read_node is True:
            line_list = line.split(',')
            number = int(line_list[0])
            x = float(line_list[1])
            y = float(line_list[2])
            z = float(line_list[3])
            nodes[number] = [x, y, z]

        # reading elements
        elif line[:8].upper() == "!ELEMENT":
            line_list = line[8:].upper().split(',')
            for line_part in line_list:
                if line_part.lstrip()[:4] == "TYPE":
                    elm_type = line_part.split('=')[1].strip()

            if elm_type in ["231", "731"]:
                elm_category = elements.tria3
                number_of_nodes = 3
            elif elm_type in ["232", "732"]:
                elm_category = elements.tria6
                number_of_nodes = 6
            elif elm_type in ["241", "741"]:
                elm_category = elements.quad4
                number_of_nodes = 4
            elif elm_type == ["242", "742"]:
                elm_category = elements.quad8
                number_of_nodes = 8
            elif elm_type == "341":
                elm_category = elements.tetra4
                number_of_nodes = 4
            elif elm_type == "342":
                elm_category = elements.tetra10
                number_of_nodes = 10
            elif elm_type == "361":
                elm_category = elements.hexa8
                number_of_nodes = 8
            elif elm_type == "362":
                elm_category = elements.hexa20
                number_of_nodes = 20
            elif elm_type == "351":
                elm_category = elements.penta6
                number_of_nodes = 6
            elif elm_type == "352":
                elm_category = elements.penta15
                number_of_nodes = 15
            elif elm_type in ["111", "611"]:
                elm_category = elements.seg2
                number_of_nodes = 2
            elif elm_type == ["112", "612"]:
                elm_category = elements.seg3
                number_of_nodes = 3
                error_seg3 = True  # to print "not supported"

        elif elm_category != []:
            line_list = line.split(',')
            if elm_2nd_line is False:
                number = int(line_list[0])
                elm_category[number] = []
                pos = 1
            else:
                pos = 0
                elm_2nd_line = False
            for en in range(pos, pos + number_of_nodes - len(elm_category[number])):
                try:
                    enode = int(line_list[en])
                    elm_category[number].append(enode)
                except:
                    elm_2nd_line = True
                    break

        elif line[:8].upper() == "!SECTION":
            model_definition = False
    if error_seg3 is True:  # to print "not supported"
        FreeCAD.Console.PrintError("Error: seg3 (3-node beam element type) not supported, yet.\n")
    f.close()

    # switch from the FrontISTR node numbering to the FreeCAD node numbering
    # numbering do not change: seg2
    for en in elements.tria3:
        n = elements.tria3[en]
        elements.tria3[en] = [n[0], n[2], n[1]]
    for en in elements.tria6:
        n = elements.tria6[en]
        elements.tria6[en] = [n[0], n[2], n[1], n[4], n[3], n[5]]
    for en in elements.quad4:
        n = elements.quad4[en]
        elements.quad4[en] = [n[0], n[3], n[2], n[1]]
    for en in elements.quad8:
        n = elements.quad8[en]
        elements.quad8[en] = [n[0], n[3], n[2], n[2], n[7], n[6], n[5], n[4]]
    for en in elements.tetra4:
        n = elements.tetra4[en]
        elements.tetra4[en] = [n[1], n[0], n[2], n[3]]
    for en in elements.tetra10:
        n = elements.tetra10[en]
        elements.tetra10[en] = [n[1], n[0], n[2], n[3], n[6], n[5], n[4],
                                n[8], n[7], n[9]]
    for en in elements.hexa8:
        n = elements.hexa8[en]
        elements.hexa8[en] = [n[5], n[6], n[7], n[4], n[1], n[2], n[3], n[0]]
    for en in elements.hexa20:
        n = elements.hexa20[en]
        elements.hexa20[en] = [n[5], n[6], n[7], n[4], n[1], n[2], n[3], n[0],
                               n[13], n[14], n[15], n[12], n[9], n[10], n[11],
                               n[8], n[17], n[18], n[19], n[16]]
    for en in elements.penta6:
        n = elements.penta6[en]
        elements.penta6[en] = [n[4], n[5], n[3], n[1], n[2], n[0]]
    for en in elements.penta15:
        n = elements.penta15[en]
        elements.penta15[en] = [n[4], n[5], n[3], n[1], n[2], n[0],
                                n[9], n[10], n[11], n[6], n[7], n[8], n[13],
                                n[14], n[12]]
    for en in elements.seg3:
        n = elements.seg3[en]
        elements.seg3[en] = [n[0], n[2], n[1]]

    return {
        'Nodes': nodes,
        'Seg2Elem': elements.seg2,
        'Seg3Elem': elements.seg3,
        'Tria3Elem': elements.tria3,
        'Tria6Elem': elements.tria6,
        'Quad4Elem': elements.quad4,
        'Quad8Elem': elements.quad8,
        'Tetra4Elem': elements.tetra4,
        'Tetra10Elem': elements.tetra10,
        'Hexa8Elem': elements.hexa8,
        'Hexa20Elem': elements.hexa20,
        'Penta6Elem': elements.penta6,
        'Penta15Elem': elements.penta15
    }

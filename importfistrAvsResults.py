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

__title__ = "Result import for FrontISTR Avs file format"
__author__ = "FrontISTR Commons"
__url__ = "https://www.frontistr.com/"

## @package importfistrAvsResults
#  \ingroup FEM
#  \brief FreeCAD FrontISTR AVS Reader for FEM workbench

import os

import FreeCAD
from FreeCAD import Console


# ********* generic FreeCAD import and export methods *********
if open.__module__ == "__builtin__":
    # because we'll redefine open below (Python2)
    pyopen = open
elif open.__module__ == "io":
    # because we'll redefine open below (Python3)
    pyopen = open


def open(filename):
    "called when freecad opens a file"
    docname = os.path.splitext(os.path.basename(filename))[0]
    insert(filename, docname)


def insert(
    filename,
    docname
):
    "called when freecad wants to import a file"
    try:
        doc = FreeCAD.getDocument(docname)
    except NameError:
        doc = FreeCAD.newDocument(docname)
    FreeCAD.ActiveDocument = doc
    importAvs(filename)


# ********* module specific methods *********
def importAvs(
    filename,
    analysis=None,
    result_name_prefix=""
):
    import ObjectsFem
    from feminout import importToolsFem

    if analysis:
        doc = analysis.Document
    else:
        doc = FreeCAD.ActiveDocument

    m = read_avs_result(filename)
    result_mesh_object = None
    res_obj = None

    if len(m["Nodes"]) > 0:
        mesh = importToolsFem.make_femmesh(m)
        result_mesh_object = ObjectsFem.makeMeshResult(
            doc,
            "ResultMesh"
        )
        result_mesh_object.FemMesh = mesh
        res_mesh_is_compacted = False
        nodenumbers_for_compacted_mesh = []

        number_of_increments = len(m["Results"])
        Console.PrintLog(
            "Increments: " + str(number_of_increments) + "\n"
        )
        if len(m["Results"]) > 0:
            for result_set in m["Results"]:
                if "number" in result_set:
                    eigenmode_number = result_set["number"]
                else:
                    eigenmode_number = 0
                step_time = result_set["time"]
                step_time = round(step_time, 2)
                if eigenmode_number > 0:
                    results_name = (
                        "{}Mode{}_Results"
                        .format(result_name_prefix, eigenmode_number)
                    )
                elif number_of_increments > 1:
                    results_name = (
                        "{}Time{}_Results"
                        .format(result_name_prefix, step_time)
                    )
                else:
                    results_name = (
                        "{}Results"
                        .format(result_name_prefix)
                    )

                res_obj = ObjectsFem.makeResultMechanical(doc, results_name)
                res_obj.Mesh = result_mesh_object
                res_obj = importToolsFem.fill_femresult_mechanical(res_obj, result_set)
                if analysis:
                    # need to be here, becasause later on, the analysis objs are needed
                    # see fill of principal stresses
                    analysis.addObject(res_obj)

                # more result object calculations
                from femresult import resulttools
                from femtools import femutils
                if not res_obj.MassFlowRate:
                    if res_mesh_is_compacted is False:
                        # first result set, compact FemMesh and NodeNumbers
                        res_obj = resulttools.compact_result(res_obj)
                        res_mesh_is_compacted = True
                        nodenumbers_for_compacted_mesh = res_obj.NodeNumbers
                    else:
                        # all other result sets, do not compact FemMesh, only set NodeNumbers
                        res_obj.NodeNumbers = nodenumbers_for_compacted_mesh

                # fill DisplacementLengths
                res_obj = resulttools.add_disp_apps(res_obj)
                # fill vonMises
                res_obj = resulttools.add_von_mises(res_obj)
                # fill principal stress
                # if material reinforced object use add additional values to the res_obj
                if res_obj.getParentGroup():
                    has_reinforced_mat = False
                    for obj in res_obj.getParentGroup().Group:
                        if femutils.is_of_type(obj, "Fem::MaterialReinforced"):
                            has_reinforced_mat = True
                            Console.PrintLog(
                                "Reinfoced material object detected, "
                                "reinforced principal stresses and standard principal "
                                " stresses will be added.\n"
                            )
                            resulttools.add_principal_stress_reinforced(res_obj)
                            break
                    if has_reinforced_mat is False:
                        Console.PrintLog(
                            "No einfoced material object detected, "
                            "standard principal stresses will be added.\n"
                        )
                        # fill PrincipalMax, PrincipalMed, PrincipalMin, MaxShear
                        res_obj = resulttools.add_principal_stress_std(res_obj)
                else:
                    Console.PrintLog(
                        "No Analysis detected, standard principal stresses will be added.\n"
                    )
                    # if a pure avs file was opened no analysis and thus no parent group
                    # fill PrincipalMax, PrincipalMed, PrincipalMin, MaxShear
                    res_obj = resulttools.add_principal_stress_std(res_obj)
                # fill Stats
                res_obj = resulttools.fill_femresult_stats(res_obj)

        else:
            error_message = (
                "Nodes, but no results found in avs file. "
                "It means there only is a mesh but no results in avs file. "
                "Usually this happens for: \n"
                "- analysis type 'NOANALYSIS'\n"
                "- if FrontISTR returned no results "
                "(happens on nonpositive jacobian determinant in at least one element)\n"
                "- just no avs results where requestet in input file "
                "(neither 'node file' nor 'el file' in output section')\n"
            )
            Console.PrintWarning(error_message)

        # create a result obj, even if we have no results but a result mesh in avs file
        # see error message above for more information
        if not res_obj:
            if result_name_prefix:
                results_name = ("{}_Results".format(result_name_prefix))
            else:
                results_name = ("Results".format(result_name_prefix))
            res_obj = ObjectsFem.makeResultMechanical(doc, results_name)
            res_obj.Mesh = result_mesh_object
            # TODO, node numbers in result obj could be set
            if analysis:
                analysis.addObject(res_obj)

        if FreeCAD.GuiUp:
            if analysis:
                import FemGui
                FemGui.setActiveAnalysis(analysis)
            doc.recompute()

    else:
        Console.PrintError(
            "Problem on avs file import. No nodes found in avs file.\n"
        )
        # None will be returned
        # or would it be better to raise an exception if there are not even nodes in avs file?

    return res_obj


# read a FrontISTR result file and extract the nodes
# displacement vectors and stress values.
def read_avs_result(
    avs_input
):
    Console.PrintMessage(
        "Read fistr results from complete avs file: {}\n"
        .format(avs_input)
    )

    if os.path.exists(avs_input):
        avs_file = pyopen(avs_input, "r")
    else:
        Console.PrintMessage(avs_input+" not found.")

    nodes = {}
    elements_hexa8 = {}
    elements_penta6 = {}
    elements_tetra4 = {}
    elements_tetra10 = {}
    elements_penta15 = {}
    elements_hexa20 = {}
    elements_tria3 = {}
    elements_tria6 = {}
    elements_quad4 = {}
    elements_quad8 = {}
    elements_seg2 = {}
    elements_seg3 = {}
    results = []
    mode_results = {}
    mode_results["number"] = float("NaN")
    mode_results["time"] = float("NaN")
    mode_disp = {}
    mode_stress = {}
    mode_strain = {}
    mode_peeq = {}
    mode_temp = {}
    mode_massflow = {}
    mode_networkpressure = {}

    dat = avs_file.readlines()
    avs_file.close()
    
    dat.reverse()
    
    for i in range(3):
        dat.pop()
    n_nodes, n_elems = map(int, dat.pop().split(" "))

    #read nodes
    for i in range(n_nodes):
        line = list(filter(None, dat.pop().split(" ")))
        nid = int(line[0])
        nodes_x = float(line[1])
        nodes_y = float(line[2])
        nodes_z = float(line[3])
        nodes[nid] = FreeCAD.Vector(nodes_x, nodes_y, nodes_z)

    #read elements
    for i in range(n_elems):
        line = list(filter(None, dat.pop().split(" ")))
        eid = int(line[0])
        etype = line[2]
        if etype == 'tet2':
            nd1 = int(line[3])
            nd2 = int(line[4])
            nd3 = int(line[5])
            nd4 = int(line[6])
            nd5 = int(line[7])
            nd6 = int(line[8])
            nd7 = int(line[9])
            nd8 = int(line[10])
            nd9 = int(line[11])
            nd10 = int(line[12])
            elements_tetra10[eid] = (nd2, nd1, nd4, nd3, nd5, nd7, nd10, nd8, nd6, nd9)
        elif etype == 'tet':
            nd1 = int(line[3])
            nd2 = int(line[4])
            nd3 = int(line[5])
            nd4 = int(line[6])
            elements_tetra4[eid] = (nd2, nd1, nd4, nd3)

    n_noderes, n_elemres = map(int, list(filter(None, dat.pop().split(" "))))
    if n_noderes > 0 :
        dofs = list(map(int, list(filter(None, dat.pop().split(" ")))))
        n_dofs = dofs[0]
        dofs[0] = 0
        for i in range(n_dofs):
            dofs[i+1] = dofs[i+1]+dofs[i]

        labels = []
        nresults = {}
        for i in range(n_dofs):
            tmp = dat.pop().split(",")[0].replace(" ","")
            labels.append(tmp)
            nresults[tmp] = {}

        for i in range(n_nodes):
            line = list(filter(None, dat.pop().split(" ")))
            nid = int(line[0])
            linedat = list(map(float,line[1:n_noderes+1]))
            for j in range(n_dofs):
                nresults[labels[j]][nid] = linedat[dofs[j]:dofs[j+1]]

        # displacement
        for nid in nresults['DISPLACEMENT'].keys():
            disp = nresults['DISPLACEMENT'][nid]
            mode_disp[nid] = FreeCAD.Vector(disp[0],disp[1],disp[2])
    
        # displacement
        for nid in nresults['NodalSTRESS'].keys():
            stress = nresults['NodalSTRESS'][nid]
            mode_stress[nid] = (stress[0],stress[1],stress[2],stress[3],stress[5],stress[4])

    
    mode_results["disp"] = mode_disp
    mode_results["stress"] = mode_stress
    results.append(mode_results)

    return {
        "Nodes": nodes,
        "Seg2Elem": elements_seg2,
        "Seg3Elem": elements_seg3,
        "Tria3Elem": elements_tria3,
        "Tria6Elem": elements_tria6,
        "Quad4Elem": elements_quad4,
        "Quad8Elem": elements_quad8,
        "Tetra4Elem": elements_tetra4,
        "Tetra10Elem": elements_tetra10,
        "Hexa8Elem": elements_hexa8,
        "Hexa20Elem": elements_hexa20,
        "Penta6Elem": elements_penta6,
        "Penta15Elem": elements_penta15,
        "Results": results
    }

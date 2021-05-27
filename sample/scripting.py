# new document
doc = App.newDocument("Scripted_FrontISTR_Cantilever3D")

# part
import Part
box_obj = doc.addObject('Part::Box', 'Box')
box_obj.Height = box_obj.Width = 1000
box_obj.Length = 8000

# see how our part looks like
import FreeCADGui
FreeCADGui.ActiveDocument.activeView().viewAxonometric()
FreeCADGui.SendMsgToActiveView("ViewFit")

# import to create objects
import ObjectsFem

# analysis
analysis_object = ObjectsFem.makeAnalysis(doc, "Analysis")

# solver 
Gui.activateWorkbench("FrontISTR")
import ObjectsFISTR
solver_object = ObjectsFISTR.makeSolverFrontISTRTools(doc, "FrontISTR")

# See add_attributes from femsolver_FrontISTR/solver and writer
# for the detail of attributions.
solver_object.n_process = 4
solver_object.AnalysisType = "static"
solver_object.Nonlinearity = "no"
solver_object.MatrixSolverType = "CG"
solver_object.MatrixPrecondType = "AMG"
solver_object.MatrixSolverIterLog = "no"
solver_object.MatrixSolverTimeLog = "yes"
solver_object.MatrixSolverNumIter = 5000
solver_object.MatrixSolverResidual = "1.0e-6"
solver_object.OutputFileFormat = "AVS"
solver_object.IncrementType = "auto"
solver_object.TimeEnd = 1.0
solver_object.InitialTimeIncrement = 1.0
solver_object.MinimumTimeIncrement = "1.0e-4"
solver_object.MaximumTimeIncrement = 1.0
solver_object.NewtonConvergeResidual = "1.0e-6"
solver_object.NewtonMaximumIteration = 20

analysis_object.addObject(solver_object)

# material
material_object = ObjectsFem.makeMaterialSolid(doc, "SolidMaterial")
mat = material_object.Material
mat['Name'] = "Steel-Generic"
mat['YoungsModulus'] = "210000 MPa"
mat['PoissonRatio'] = "0.30"
mat['Density'] = "7900 kg/m^3"
material_object.Material = mat
analysis_object.addObject(material_object)

# fixed_constraint
fixed_constraint = ObjectsFem.makeConstraintFixed(doc, "FemConstraintFixed")
fixed_constraint.References = [(doc.Box, "Face1")]
analysis_object.addObject(fixed_constraint)

# force_constraint
force_constraint = ObjectsFem.makeConstraintForce(doc, "FemConstraintForce")
force_constraint.References = [(doc.Box, "Face2")]
force_constraint.Force = 9000000.0
force_constraint.Direction = (doc.Box, ["Edge5"])
force_constraint.Reversed = True
analysis_object.addObject(force_constraint)

# gmsh
femmesh_obj = ObjectsFem.makeMeshGmsh(doc, box_obj.Name + "_Mesh")
femmesh_obj.Part = doc.Box

doc.recompute()

from femmesh.gmshtools import GmshTools as gt
gmsh_mesh = gt(femmesh_obj)
error = gmsh_mesh.create_mesh()
print(error)

analysis_object.addObject(femmesh_obj)

# recompute
doc.recompute()

# run step by step
import fistrtools
fea = fistrtools.FemToolsFISTR(solver=solver_object)
fea.update_objects()
fea.setup_working_dir()
print(fea.working_dir)
fea.setup_fistr()
message = fea.check_prerequisites()
if not message:
	fea.purge_results()
	fea.write_inp_file()
	fea.part_inp_file()
	fea.fistr_run()
	fea.load_results()
else:
    FreeCAD.Console.PrintError("Houston, we have a problem! {}\n".format(message))  # in report view
    print("Houston, we have a problem! {}\n".format(message))  # in python console

# get results
result = doc.getObject('FISTR_Results')
stats = result.Stats
print("### results ###")
for idof in [1,2,3]:
    print("U{}: Max {:12.4e}, Min {:12.4e}".format(idof, stats[2*idof-1], stats[2*idof-2]))

print("Max von mises  : {:12.4e}".format(stats[9]))
print("Max prn. stress: {:12.4e}".format(stats[11]))
print("Min prn. stress: {:12.4e}".format(stats[14]))

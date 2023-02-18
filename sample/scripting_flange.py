# new document
doc = App.newDocument("Scripted_FrontISTR_Flange")

# create the body
import Part
import PartDesign
import Sketcher

# create the shape
body_obj = doc.addObject('PartDesign::Body', 'Body')
sketch_obj0 = body_obj.newObject('Sketcher::SketchObject', 'Sketch0')
sketch_obj0.Support = (doc.getObject('XY_Plane'), [''])
sketch_obj0.MapMode = 'FlatFace'
sketch_obj0.addGeometry(Part.Circle(App.Vector(0.000000,0.000000,0), App.Vector(0,0,1), 165.000000), False)
sketch_obj0.addConstraint(Sketcher.Constraint('Coincident', 0, 3, -1, 1))
sketch_obj0.addConstraint(Sketcher.Constraint('Diameter', 0, 330.000000))
sketch_obj0.addGeometry(Part.Circle(App.Vector(0.000000,0.000000,0), App.Vector(0,0,1), 109.000000), False)
sketch_obj0.addConstraint(Sketcher.Constraint('Coincident', 1, 3, 0, 3))
sketch_obj0.addConstraint(Sketcher.Constraint('Diameter', 1, 218.000000))
pad_obj = body_obj.newObject('PartDesign::Pad', 'Pad')
pad_obj.Profile = sketch_obj0
pad_obj.Length = 22.000000
pad_obj.Direction = (0, 0, 1)
pad_obj.ReferenceAxis = (sketch_obj0, ['N_Axis'])
doc.recompute()
pad_obj.Visibility = True
sketch_obj0.Visibility = False

# see how our part looks like
Gui.ActiveDocument.activeView().viewAxonometric()
Gui.SendMsgToActiveView("ViewFit")

# create a hole
sketch_obj1 = body_obj.newObject('Sketcher::SketchObject', 'Sketch1')
sketch_obj1.Support = (pad_obj, ['Face4',])
sketch_obj1.MapMode = 'FlatFace'  # draw on Face4 of Pad (upper surface)
sketch_obj1.addGeometry(Part.Circle(App.Vector(0.000000,145.000000,0), App.Vector(0,0,1), 11.500000), False)
sketch_obj1.addConstraint(Sketcher.Constraint('PointOnObject', 0, 3, -2))
sketch_obj1.addConstraint(Sketcher.Constraint('Diameter', 0, 23.000000))
sketch_obj1.addConstraint(Sketcher.Constraint('DistanceY', -1, 1, 0, 3, 145.000000))
pocket_obj = body_obj.newObject('PartDesign::Pocket', 'Pocket')
pocket_obj.Profile = sketch_obj1
pocket_obj.Length = 22.000000
pocket_obj.Direction = (0, 0, -1)
pocket_obj.ReferenceAxis = (sketch_obj1, ['N_Axis'])
doc.recompute()
pocket_obj.Visibility = True
pad_obj.Visibility = False
sketch_obj1.Visibility = False

# create the polar pattern
polar_obj = body_obj.newObject('PartDesign::PolarPattern','PolarPattern')
polar_obj.Originals = [pocket_obj,]
polar_obj.Axis = (sketch_obj1, ['N_Axis'])
polar_obj.Occurrences = 12
body_obj.Tip = polar_obj
doc.recompute()
polar_obj.Visibility = True
pocket_obj.Visibility = False

# import to create objects
import ObjectsFem

# analysis
analysis_object = ObjectsFem.makeAnalysis(doc, 'Analysis')

# solver
Gui.activateWorkbench("FrontISTR")
import ObjectsFISTR
solver_object = ObjectsFISTR.makeSolverFrontISTRTools(doc, "FrontISTR")
solver_object.n_process = 4
solver_object.AnalysisType = "thermomech"
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
mat['YoungsModulus'] = "200 GPa"
mat['PoissonRatio'] = "0.30"
mat['Density'] = "7900 kg/m^3"
mat['ThermalConductivity'] = "500 W/m/K"
mat['ThermalExpansionCoefficient'] = "12.00 um/m/K"
mat['SpecificHeat'] = "500 J/kg/K"
material_object.Material = mat
analysis_object.addObject(material_object)

# fixed constraint
fixed_constraint = ObjectsFem.makeConstraintFixed(doc, "ConstraintFixed")
fixed_constraint.References = [(polar_obj, "Face13")]
analysis_object.addObject(fixed_constraint)

# initial temperature constraint
intial_temperature = ObjectsFem.makeConstraintInitialTemperature(doc, "ConstraintInitialTemperature")
intial_temperature.initialTemperature = 300.000000
analysis_object.addObject(intial_temperature)

# target temperature constraint
target_temperature = ObjectsFISTR.makeConstraintTemperatureFrontISTR(doc, "ConstraintTargetTemperature")
target_temperature.Temperature = 400.000000
analysis_object.addObject(target_temperature)

# gmsh
femmesh_obj = ObjectsFem.makeMeshGmsh(doc, body_obj.Name + "_Mesh")
femmesh_obj.Part = body_obj
femmesh_obj.CharacteristicLengthMax = "4.00 mm"
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
    App.Console.PrintError("Houston, we have a problem! {}\n".format(message))  # in report view
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
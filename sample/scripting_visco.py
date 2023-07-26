# new document
doc = App.newDocument("Scripted_FrontISTR_Visco")

import Sketcher
import Part

# create lower face
sketch_obj0 = doc.addObject("Sketcher::SketchObject", "Sketch")
sketch_obj0.Placement = App.Placement(App.Vector(0.000000, 0.000000, 0.000000), App.Rotation(0.000000, 0.000000, 0.000000, 1.000000))
sketch_obj0.MapMode = "Deactivated"
sketch_obj0.addGeometry(Part.ArcOfCircle(Part.Circle(App.Vector(0.000000, 0.000000, 0), App.Vector(0, 0, 1), 6.413000), 0.000000, 1.570796), False)
sketch_obj0.addConstraint(Sketcher.Constraint("Coincident", 0, 3, -1, 1)) 
sketch_obj0.addConstraint(Sketcher.Constraint("PointOnObject", 0, 1, -1)) 
sketch_obj0.addConstraint(Sketcher.Constraint("PointOnObject", 0, 2, -2)) 
sketch_obj0.addConstraint(Sketcher.Constraint("Radius", 0, 6.413000)) 
sketch_obj0.setDatum(3, App.Units.Quantity("6.413000 mm"))
sketch_obj0.addGeometry(Part.LineSegment(App.Vector(6.413000, 0.000000, 0), App.Vector(0.000000, 0.000000, 0)), False)
sketch_obj0.addConstraint(Sketcher.Constraint("Coincident", 1, 1, 0, 1)) 
sketch_obj0.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 0, 3)) 
sketch_obj0.addGeometry(Part.LineSegment(App.Vector(0.000000, 0.000000, 0), App.Vector(0.000000, 6.413000, 0)), False)
sketch_obj0.addConstraint(Sketcher.Constraint("Coincident", 2, 1, 0, 3)) 
sketch_obj0.addConstraint(Sketcher.Constraint("Coincident", 2, 2, 0, 2)) 
doc.recompute()

# create upper face
skecth_obj1 = doc.addObject("Sketcher::SketchObject", "Sketch001")
skecth_obj1.Placement = App.Placement(App.Vector(0.000000, 0.000000, 26.666667), App.Rotation(0.000000, 0.000000, 0.000000, 1.000000))
skecth_obj1.MapMode = "Deactivated"
skecth_obj1.addGeometry(Part.ArcOfCircle(Part.Circle(App.Vector(0.000000, 0.000000, 0), App.Vector(0, 0, 1), 6.297000), 0.000000, 1.570796), False)
skecth_obj1.addConstraint(Sketcher.Constraint("Coincident", 0, 3, -1, 1)) 
skecth_obj1.addConstraint(Sketcher.Constraint("PointOnObject", 0, 1, -1)) 
skecth_obj1.addConstraint(Sketcher.Constraint("PointOnObject", 0, 2, -2)) 
skecth_obj1.addConstraint(Sketcher.Constraint("Radius", 0, 6.297000)) 
skecth_obj1.setDatum(3, App.Units.Quantity("6.297000 mm"))
skecth_obj1.addGeometry(Part.LineSegment(App.Vector(6.297000, 0.000000, 0), App.Vector(0.000000, 0.000000, 0)), False)
skecth_obj1.addConstraint(Sketcher.Constraint("Coincident", 1, 1, 0, 1)) 
skecth_obj1.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 0, 3)) 
skecth_obj1.addGeometry(Part.LineSegment(App.Vector(0.000000, 0.000000, 0), App.Vector(0.000000, 6.297000, 0)), False)
skecth_obj1.addConstraint(Sketcher.Constraint("Coincident", 2, 1, 0, 3)) 
skecth_obj1.addConstraint(Sketcher.Constraint("Coincident", 2, 2, 0, 2)) 
doc.recompute()

# create body
body_obj = doc.addObject("Part::Loft", "Loft")
body_obj.Sections=[doc.Sketch, doc.Sketch001, ]
body_obj.Solid=True
body_obj.Ruled=False
body_obj.Closed=False
doc.recompute()
sketch_obj0.Visibility = False
skecth_obj1.Visibility = False

# adjust view
Gui.ActiveDocument.activeView().viewAxonometric()
Gui.SendMsgToActiveView("ViewFit")

# analysis
import ObjectsFem
analysis_obj = ObjectsFem.makeAnalysis(doc, "Analysis")

# material
material_obj = ObjectsFem.makeMaterialSolid(doc, "SolidMaterial")
mat = material_obj.Material
mat["Name"] = "NoName"
mat["YoungsModulus"] = "206.900 GPa"
mat["PoissonRatio"] = "0.29"
material_obj.Material = mat
analysis_obj.addObject(material_obj)

# recompute
doc.recompute()

# constraint FIX
cons_fix = ObjectsFem.makeConstraintDisplacement(doc, "ConsFIX")
cons_fix.zFree = False
cons_fix.zFix = True
cons_fix.References = [(doc.Loft, "Face5")]
analysis_obj.addObject(cons_fix)

# constraint LOADS
cons_loads = ObjectsFem.makeConstraintDisplacement(doc, "ConsLOADS")
cons_loads.zDisplacement = -7.000000
cons_loads.zFree = False
cons_loads.References = [(doc.Loft, "Face4")]
analysis_obj.addObject(cons_loads)

# constraint XSYMM
cons_xsymm = ObjectsFem.makeConstraintDisplacement(doc, "ConsXSYMM")
cons_xsymm.xFree = False
cons_xsymm.xFix = True
cons_xsymm.References = [(doc.Loft, "Face2")]
analysis_obj.addObject(cons_xsymm)

# constraint YSYMM
cons_ysymm = ObjectsFem.makeConstraintDisplacement(doc, "ConsYSYMM")
cons_ysymm.yFree = False
cons_ysymm.yFix = True
cons_ysymm.References = [(doc.Loft, "Face3")]
analysis_obj.addObject(cons_ysymm)

# recompute
doc.recompute()

# gmsh
femmesh_obj = ObjectsFem.makeMeshGmsh(doc, body_obj.Name + "_Mesh")
femmesh_obj.Part = body_obj
femmesh_obj.CharacteristicLengthMax = "2.00 mm"

from femmesh.gmshtools import GmshTools as gt
gmsh_mesh = gt(femmesh_obj)
error = gmsh_mesh.create_mesh()
print(error)
analysis_obj.addObject(femmesh_obj)
doc.recompute()

# solver
Gui.activateWorkbench("FrontISTR")
import ObjectsFISTR
solver_obj = ObjectsFISTR.makeSolverFrontISTRTools(doc, "FrontISTR")
solver_obj.Nonlinearity = "yes"
solver_obj.MatrixPrecondType = "SSOR"
solver_obj.MatrixSolverIterLog = "yes"
solver_obj.MatrixSolverNumIter = 10000
solver_obj.MatrixSolverResidual = "1.0e-8"
solver_obj.IncrementType = "fixed"
solver_obj.InitialTimeIncrement = 0.20
solver_obj.NewtonConvergeResidual = "1.0e-5"
solver_obj.TimeEnd = 2.00
analysis_obj.addObject(solver_obj)

# viscoelastic material
visco_obj = ObjectsFISTR.makeMaterialViscoelasticFrontISTR(doc, material_obj, "SolidMaterialVisco")
visco_obj.ShearRelaxationModulus = 0.5  # default
visco_obj.RelaxationTime = 1.0  # default
analysis_obj.addObject(visco_obj)

# recompute
doc.recompute()

# run step by step
import fistrtools
fea = fistrtools.FemToolsFISTR(solver=solver_obj)
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

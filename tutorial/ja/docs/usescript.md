# Automated analysis with Python scripts

Since FreeCAD has a Python API, it is possible to run the program automatically using Python. Although it is possible to run the program fully automatically without using the GUI at all, in this example we will run some operations from the GUI using Python. The [sample script](https://gitlab.com/FrontISTR-Commons/FEM_FrontISTR/-/blob/master/sample/scripting.py) is included in the repository.

This [sample script](https://gitlab.com/FrontISTR-Commons/FEM_FrontISTR/-/blob/master/sample/scripting.py) can be downloaded from FreeCAD's [FEM Tutorial Python]( This [sample script](https://wiki.freecadweb.org/FEM_Tutorial_Python) is a slightly modified version of FreeCAD's [FEM Tutorial Python](https://wiki.freecadweb.org/FEM_Tutorial_Python) to work with FrontISTR. 

1. When you start FreeCAD and the Python console is not displayed, check View -> Panels -> Python console. The Python console will appear in the lower right corner, and you can execute FreeCAD functions from Python by typing in the console.
![python console](./images/11_python_console.png) 
2. For example, by pasting [sample script](https://gitlab.com/FrontISTR-Commons/FEM_FrontISTR/-/blob/master/sample/scripting.py) into the Python console, you can create a CAD For example, by pasting [sample script]() into the Python console, you can create a CAD file, perform automatic meshing, assign boundary conditions, and perform FrontISTR calculations all at once.
! [python result](./images/12_python_results.png)

Translated with www.DeepL.com/Translator (free version)

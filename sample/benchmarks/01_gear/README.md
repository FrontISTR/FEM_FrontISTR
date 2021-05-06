# Benchmark 01: Involute Gear

![result_mises_small](./result_mises_small.png)

## Settings

- Objective: To compare the performance of CalculiX and FrontISTR on various mesh sizes and matrix solvers
- Model: Involute gear generated with the part design workbench
  - Analysis type: Static linear
  - Note: This model is massive and favorable for iterative solvers.
- Parameters:
  - Mesh settings: Netgen, Fineness=Moderate, First order
    1. Small: Max. Size=1.00, 48,161 nodes, 35,554 elements
    2. Middle: Max. Size=0.60, 163,686 nodes, 69,200 elements
    3. Large: Max. Size=0.40, 433,870 nodes, 140,422 elements
  - Matrix solver settings
    - CalculiX: iterativecholesky(iterative), spooles(direct)
    - FrontISTR: CG w/ AMG preconditioner(iterative), MUMPS(direct)
- Mesurement Environment
  - OS: Windows 10 Pro 10.0.19041 N/A Build 19041
  - CPU: Intel Core i7-6700 @3.40GHz 4cores x 1CPU
  - Memory: 16GB
  - FreeCAD 0.19.1 a88db11
  - FrontISTR v5.2 380f1690
  - FEM\_FrontISTR 8f57d2f3
  - Paralell settings
    - Calculix: `OMP_NUM_THREADS=4`
      - Note that Iterativecholesky solver runs sequentially. The other processes are executed in parallel.
    - FrontISTR: `n_process=4`
- Measurement method
  - Write Input Time(Tw): read from "Time: xx.x" at the bottom of the task panel when "Write input file" is complete
  - Solver time(Ts): read from "xx.x:  [FrontISTR/CalculiX] done without error!" message in FEM Console
  - Total time(Tt): read from "Time: xx.x" at the bottom of the task panel when "Run [FrontISTR/CalculiX]" is complete
  - Loading result time(Tr): Total time - Solve time
  - Max von Mises Stress: read from [FISTR|CCX]_Results



## Results

The performance(Solver time) of CalculiX and FrontISTR for the involute gear model is as follows:

![result_performance](./result_performance.png)



The detailed result table including write Input time, result loading time, Mises stress, and iterative solver information is as follows:

| model     | Solver    | Matrix Solver     | Tw (sec) | Ts (sec) | Tt (sec) | Tr (sec) | Max Mises(MPa) | iter | residual | threshold |
| --------- | --------- | ----------------- | -------- | -------- | -------- | -------- | -------------- | ---- | -------- | --------- |
| 1. small  | CalculiX  | iterativecholesky | 4.8      | 8.6      | 18.7     | 10.1     | 334.16         | 151  | 2.02E-04 | 2.24E-04  |
|           | CalculiX  | spooles           | 4.3      | 13.4     | 23.1     | 9.7      | 334.16         | N/A  | N/A      | N/A       |
|           | FrontISTR | CG w/ AMG         | 6.1      | **4.1**  | 12.4     | 8.3      | 334.16         | 30   | 6.92E-07 | 1.00E-06  |
|           | FrontISTR | MUMPS             | 6.1      | 7.0      | 15.3     | 8.3      | 334.16         | N/A  | 2.25E-12 | N/A       |
| 2. middle | CalculiX  | iterativecholesky | 18.4     | 37.9     | 75.8     | 37.9     | 397.31         | 237  | 1.13E-04 | 1.24E-04  |
|           | CalculiX  | spooles           | 19.1     | 120.1    | 151.2    | 31.1     | 397.37         | N/A  | N/A      | N/A       |
|           | FrontISTR | CG w/ AMG         | 25.8     | **13.8** | 32.8     | 19.0     | 397.37         | 24   | 9.79E-07 | 1.00E-06  |
|           | FrontISTR | MUMPS             | 25.2     | 55.3     | 77.2     | 21.9     | 397.37         | N/A  | 4.53E-12 | N/A       |
| 3. large  | CalculiX  | iterativecholesky | 55.5     | 160.3    | 265.7    | 105.4    | 442.03         | 544  | 6.19E-05 | 6.50E-05  |
|           | CalculiX  | spooles           | 50.8     | 880.8    | N/A*     | N/A*     | N/A*           | N/A  | N/A      | N/A       |
|           | FrontISTR | CG w/ AMG         | 72.4     | **41.8** | 93.2     | 51.4     | 442.02         | 29   | 7.76E-07 | 1.00E-06  |
|           | FrontISTR | MUMPS             | 74.4     | 590.5    | 651.5    | 61.0     | 442.02         | N/A  | 9.37E-12 | N/A       |

\*Problem on frd file import. No nodes found in frd file.
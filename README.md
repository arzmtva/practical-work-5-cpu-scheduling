# Practical Work 5 — CPU Scheduling Simulator

## Overview
A Python program for simulating and comparing CPU scheduling algorithms.

## Algorithms
- FCFS — First Come, First Served
- SJF — Shortest Job First
- SRTF — Shortest Remaining Time First
- Priority Scheduling
- Round Robin (RR)
- Priority Scheduling with Aging

## Features
- Calculates waiting, turnaround, and response times.
- Measures CPU utilization and context switches.
- Displays Gantt charts.
- Compares Round Robin time quantum values from 1 to 10.
- Demonstrates process starvation and aging.
- Exports results to CSV and SVG files.

## Technologies
- Python 3
- Python standard library

## Project Files
- `main.py` — main program.
- `set1.txt`, `set2.txt`, `set3.txt` — process datasets.
- `results.txt` — program output.
- `set1_results.csv` — scheduling results.
- `rr_graph.svg` — Round Robin comparison graph.

## How to Run
Run the program:

    python3 main.py

Save the output:

    python3 main.py > results.txt

Check syntax:

    python3 -m py_compile main.py

## Round Robin Experiment
The program compares time quantum values from 1 to 10 using average waiting time and context switches.

## Priority Scheduling and Aging
Aging improves the priority of waiting processes to help prevent starvation.

## Author
Practical Work 5 — 2026

# eCodeOrama

eCodeOrama is an interactive educational tool for visualizing and analyzing the flow of Scratch programs. It extracts program data from MIT Scratch (.sb3) files, then displays the relationships between sprites, events, and scripts in a variety of ways—including grid, graph, and tree layouts. The output is compatible with the traditional CodeOrama layout and also supports exports (PDF, text, CSV, Excel, JSON, and images) for further analysis or presentation.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [Usage](#usage)
- [Visualization Modes](#visualization-modes)
- [Export Options](#export-options)
- [Configuration & Customization](#configuration--customization)

---

## Overview

eCodeOrama parses Scratch projects to extract:
- **Sprites:** Visual objects in Scratch.
- **Events:** Triggers (e.g., flag clicked, key pressed, broadcast received).
- **Scripts:** Blocks of code (scripts) that run in response to events.
- **Connections:** Communication links formed by broadcast messages between scripts.

This data is then visualized interactively. Users can view the program flow in different layouts and export the results for offline use or further editing.

---

## Features

- **Parsing Scratch Files:**  
  Uses `parser.py` to read .sb3 files (which are essentially ZIP archives of JSON) and extract sprites, events, scripts, and message connections.

- **Multiple Visualization Modes:**  
  - **Grid View:** Displays a table-like layout with sprites as columns, events as rows, and scripts as cells.  
  - **Graph View:** Uses a force-directed layout (powered by `networkx`) to show sprites and scripts as nodes with message connections as directed edges.  
  - **Tree View:** Presents a hierarchical tree layout starting from a chosen root event (e.g. flag clicked).

- **Interactive GUI:**  
  Built with PyQt5 in `interface.py`:
  - File loading (Scratch .sb3 files)
  - Visualization options (edge styles, view styles, layout algorithms for graphs, tree root selection)
  - Report generation (textual reports of broadcasts, receives, and script layout)
  - Save/load of configuration (custom ordering of sprites and events)

- **Export Capabilities:**  
  Implemented in `export.py`, exports include:  
  - **PDF:** A formatted layout similar to CodeOrama examples  
  - **Text Report:** Detailed linear report showing scripts and message connections  
  - **CSV (Edge List):** A simple list of all directed message edges  
  - **Excel/LibreCalc:** Multi-sheet workbooks with grid, connections, and script details  
  - **JSON:** Structured export for integration with other tools  
  - **Image:** Current visualization exported as PNG, SVG, or PDF

- **Configuration & Customization:**  
  Through dialogs in `config_dialogs.py` users can:
  - Reorder sprites (columns) and events (rows)
  - Apply automatic ordering (topological order for events or connectivity order for sprites)
  - Toggle script folding/unfolding for minimal versus detailed views

---

## Project Structure

```
eCodeOrama/
├── config_dialogs.py      # Dialogs for layout and style configuration
├── export.py              # Export functionality to PDF, text, CSV, Excel, JSON, image
├── graph_visualizer.py    # Visualizer for force-directed graph layout using networkx
├── Ideas.html             # Additional implementation ideas and discussion documentation
├── interface.py           # Main PyQt5 GUI application code
├── parser.py              # Parses Scratch .sb3 files to extract program data
├── README.md              # This file
├── requirements.txt       # Python package dependencies
├── text_reports.py        # Generates detailed text-based reports
├── tree_visualizer.py     # Visualizer for tree/hierarchical layout
└── sb3/                   # Folder containing sample Scratch (.sb3) projects
    └── (sample files)
```

## Installation & Setup

### Requirements

The project depends on the following Python packages (see [requirements.txt](requirements.txt) for versions):

- PyQt5
- matplotlib
- numpy
- pandas
- reportlab
- xlsxwriter
- networkx

### Installation Steps

1. **Clone the repository:**

   ```bash
   git clone https://github.com/sarantos40/eCodeOrama.git
   cd eCodeOrama
   ```

2. **(Optional) Create and activate a virtual environment:**

   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**

   ```bash
   python interface.py
   ```

---

## Usage

1. **Load a Scratch File:**  
   In the application, click the "Load Scratch File" button or use the File menu → "Open Scratch File" to select a `.sb3` file.

2. **Visualization Options:**  
   Use the control panel at the top to choose:
   - Edge Style (straight, curved, or improved)
   - View Style (Grid, Graph, or Tree)
   - For Graph view, select a layout algorithm (spring, kamada_kawai, spectral)
   - For Tree view, pick a root event (e.g., flag_clicked)

3. **Generate Text Reports:**  
   Use the "Text Reports" tab to generate broadcast, receive, or script layout reports.

4. **Export Visualization/Data:**  
   Use File → "Export Visualization" to open the export dialog and choose from multiple export formats (PDF, Text, CSV, Excel, JSON, or Image).

5. **Configuration:**  
   Use View → "Configure Layout" to reorder sprites and events or adjust other layout settings.

6. **Interact with the Visualization:**  
   The interactive display supports zooming, panning (via the matplotlib navigation toolbar), and can be updated dynamically as you change settings.

---

## Visualization Modes

### Grid View

- **Layout:** Sprites are arranged as columns and events as rows.
- **Content:** Each cell contains scripts (which can be folded or unfolded).
- **Connections:** Arrows connect broadcast blocks to corresponding receive blocks.

### Graph View

- **Layout:** A force-directed (spring) or alternative layout (kamada_kawai, spectral) graph is generated using networkx.
- **Nodes:** Sprites are larger nodes, whereas individual scripts are smaller nodes.
- **Connections:** Directed edges indicate message connections between scripts.

### Tree View

- **Layout:** Displays a hierarchical tree starting from a specified root event.
- **Flow:** A breadth-first layout shows scripts triggered from the root and their subsequent broadcasts.
- **Usage:** Particularly useful to trace execution flow starting from a key event.

---

## Export Options

The export module (`export.py`) supports:

- **PDF Export:** Creates a formatted PDF with a table-like representation and connection details.
- **Text Report:** Generates a plain text layout with detailed script information.
- **CSV Export:** Outputs an edge list (source, event, message, target).
- **Excel/LibreCalc Export:** Produces a workbook with multiple sheets (grid, connections, scripts).
- **JSON Export:** Outputs structured JSON for integration with other tools.
- **Image Export:** Saves the current visualization as PNG, SVG, or PDF.

---

## Configuration & Customization

The application allows you to customize the visualization:
- **Order Customization:** Use the configuration dialogs (in `config_dialogs.py`) to manually adjust the order of sprites (columns) and events (rows). Automatic ordering (topological for events or connectivity-based for sprites) is also available.
- **Script Folding:** You can fold scripts to see a compact view or unfold them for full detail.
- **Color & Edge Customization:** Currently, some defaults are set; planned improvements include interactive editing of node and edge names and colors.

Settings are saved using QSettings and can be exported/imported via JSON files.



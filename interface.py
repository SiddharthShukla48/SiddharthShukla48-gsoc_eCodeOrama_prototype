import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QFileDialog, QLabel,
                            QComboBox, QCheckBox, QTabWidget, QTextEdit,
                            QSplitter, QAction, QToolBar, QColorDialog, QDialog,
                            QDialogButtonBox, QFormLayout, QLineEdit, QGroupBox,
                            QMessageBox)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QIcon
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from parser import ScratchParser
from visualizer import CodeOramaVisualizer
from text_reports import TextReportGenerator
from config_dialogs import OrderConfigDialog, StyleConfigDialog
import json
from export import CodeOramaExporter
from graph_visualizer import GraphVisualizer
from tree_visualizer import TreeVisualizer

class MatplotlibCanvas(FigureCanvas):
    def __init__(self, fig):
        self.fig = fig
        super(MatplotlibCanvas, self).__init__(self.fig)

class ECodeOramaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("eCodeOrama Prototype")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize components
        self.parser = ScratchParser()
        self.visualizer = CodeOramaVisualizer()
        self.codeorama_data = None
        self.settings = QSettings("eCodeOrama", "Prototype")
        
        # Setup UI
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """Create the user interface"""
        # Menu bar
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        open_action = QAction('Open Scratch File', self)
        open_action.triggered.connect(self.load_scratch_file)
        file_menu.addAction(open_action)
        
        save_config_action = QAction('Save Configuration', self)
        save_config_action.triggered.connect(self.save_configuration)
        file_menu.addAction(save_config_action)
        
        load_config_action = QAction('Load Configuration', self)
        load_config_action.triggered.connect(self.load_configuration)
        file_menu.addAction(load_config_action)
        
        export_action = QAction('Export Visualization', self)
        export_action.triggered.connect(self.export_visualization)
        file_menu.addAction(export_action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        fold_all_action = QAction('Fold All Scripts', self)
        fold_all_action.triggered.connect(self.fold_all_scripts)
        view_menu.addAction(fold_all_action)
        
        unfold_all_action = QAction('Unfold All Scripts', self)
        unfold_all_action.triggered.connect(self.unfold_all_scripts)
        view_menu.addAction(unfold_all_action)
        
        configure_layout_action = QAction('Configure Layout', self)
        configure_layout_action.triggered.connect(self.configure_layout)
        view_menu.addAction(configure_layout_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        edit_names_action = QAction('Edit Node/Edge Names', self)
        edit_names_action.triggered.connect(self.edit_names)
        tools_menu.addAction(edit_names_action)
        
        edit_colors_action = QAction('Edit Colors', self)
        edit_colors_action.triggered.connect(self.edit_colors)
        tools_menu.addAction(edit_colors_action)
        
        # Create toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        # Add toolbar buttons
        toolbar.addAction(open_action)
        toolbar.addSeparator()
        toolbar.addAction(fold_all_action)
        toolbar.addAction(unfold_all_action)
        toolbar.addSeparator()
        toolbar.addAction(export_action)
        toolbar.addAction(configure_layout_action)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        # File controls
        self.load_button = QPushButton("Load Scratch File")
        self.load_button.clicked.connect(self.load_scratch_file)
        control_layout.addWidget(self.load_button)
        
        self.status_label = QLabel("No file loaded")
        control_layout.addWidget(self.status_label)
        
        # Visualization options
        self.edge_style_combo = QComboBox()
        self.edge_style_combo.addItems(['straight', 'curved', 'improved'])
        self.edge_style_combo.setCurrentText('improved')
        self.edge_style_combo.currentTextChanged.connect(self.update_visualization)
        control_layout.addWidget(QLabel("Edge Style:"))
        control_layout.addWidget(self.edge_style_combo)
        
        self.show_messages_check = QCheckBox("Show Message Names")
        self.show_messages_check.setChecked(True)
        self.show_messages_check.stateChanged.connect(self.update_visualization)
        control_layout.addWidget(self.show_messages_check)
        
        # Add view style selection
        self.view_style_combo = QComboBox()
        self.view_style_combo.addItems(['Grid', 'Graph', 'Tree'])
        self.view_style_combo.setCurrentText('Graph')
        self.view_style_combo.currentTextChanged.connect(self.update_visualization)
        control_layout.addWidget(QLabel("View Style:"))
        control_layout.addWidget(self.view_style_combo)

        # If you're using Graph view, add layout algorithm selector
        self.graph_layout_combo = QComboBox()
        self.graph_layout_combo.addItems(['spring', 'kamada_kawai', 'spectral'])
        self.graph_layout_combo.setCurrentText('spring')
        self.graph_layout_combo.currentTextChanged.connect(self.update_visualization)
        control_layout.addWidget(QLabel("Graph Layout:"))
        control_layout.addWidget(self.graph_layout_combo)

        # Tree root event selector
        self.tree_root_combo = QComboBox()
        self.tree_root_combo.addItems(['flag_clicked', 'key_pressed', 'receive_'])
        self.tree_root_combo.setCurrentText('flag_clicked')
        self.tree_root_combo.currentTextChanged.connect(self.update_visualization)
        control_layout.addWidget(QLabel("Tree Root:"))
        control_layout.addWidget(self.tree_root_combo)

        control_layout.addStretch(1)
        
        main_layout.addLayout(control_layout)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Visualization tab
        self.viz_widget = QWidget()
        viz_layout = QVBoxLayout(self.viz_widget)
        
        # Add canvas container for the visualization
        self.canvas_container = QVBoxLayout()
        self.canvas_placeholder = QLabel("CodeOrama visualization will appear here")
        self.canvas_placeholder.setAlignment(Qt.AlignCenter)
        self.canvas_container.addWidget(self.canvas_placeholder)
        viz_layout.addLayout(self.canvas_container)
        
        self.tab_widget.addTab(self.viz_widget, "Visualization")
        
        # Text Reports tab
        self.reports_widget = QWidget()
        reports_layout = QVBoxLayout(self.reports_widget)
        
        # Add report selection controls
        report_control_layout = QHBoxLayout()
        
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems(['Broadcast Report', 'Receive Report', 'Script Layout'])
        report_control_layout.addWidget(QLabel("Report Type:"))
        report_control_layout.addWidget(self.report_type_combo)
        
        self.generate_report_button = QPushButton("Generate Report")
        self.generate_report_button.clicked.connect(self.generate_report)
        report_control_layout.addWidget(self.generate_report_button)
        
        report_control_layout.addStretch(1)
        
        reports_layout.addLayout(report_control_layout)
        
        # Add text area for reports
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setFont(QApplication.font("Monospace"))
        reports_layout.addWidget(self.report_text)
        
        self.tab_widget.addTab(self.reports_widget, "Text Reports")
    
    def load_scratch_file(self):
        """Load a Scratch sb3 file and visualize it"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Scratch File", "", "Scratch Files (*.sb3)"
        )
        
        if file_path:
            self.status_label.setText(f"Loading: {os.path.basename(file_path)}")
            
            # Parse the file
            if self.parser.parse_sb3(file_path):
                # Get CodeOrama data
                self.codeorama_data = self.parser.get_codeorama_data()
                
                # Update visualization
                self.update_visualization()
                
                # Update status
                self.status_label.setText(
                    f"Loaded: {os.path.basename(file_path)} - "
                    f"{len(self.codeorama_data['sprites'])} sprites, "
                    f"{len(self.codeorama_data['events'])} events"
                )
            else:
                self.status_label.setText(f"Error loading {os.path.basename(file_path)}")
    
    def update_visualization(self):
        """Update the visualization with current settings"""
        if not self.codeorama_data:
            return
            
        # Clear previous visualization
        for i in reversed(range(self.canvas_container.count())): 
            self.canvas_container.itemAt(i).widget().setParent(None)
        
        # Get current settings
        edge_style = self.edge_style_combo.currentText()
        show_messages = self.show_messages_check.isChecked()
        view_style = self.view_style_combo.currentText()
        
        # Get layout configuration
        layout_config = self.settings.value("layout_config", {}, type=dict)
        
        # Get script folding state
        script_folding = self.settings.value("script_folding", {}, type=dict)
        
        # Create appropriate visualization based on view style
        if view_style == 'Grid':
            # Use the original grid visualizer
            fig = self.visualizer.visualize(
                self.codeorama_data, 
                edge_style=edge_style,
                show_message_names=show_messages,
                config=layout_config,
                script_folding=script_folding
            )
        elif view_style == 'Graph':
            # Use the graph visualizer
            graph_layout = self.graph_layout_combo.currentText()
            graph_viz = GraphVisualizer()
            fig = graph_viz.visualize(
                self.codeorama_data,
                layout_type=graph_layout,
                show_message_names=show_messages
            )
        elif view_style == 'Tree':
            # Use the tree visualizer
            tree_root = self.tree_root_combo.currentText()
            tree_viz = TreeVisualizer()
            fig = tree_viz.visualize(
                self.codeorama_data,
                root_event=tree_root,
                show_message_names=show_messages
            )
        else:
            # Fallback to grid visualizer
            fig = self.visualizer.visualize(
                self.codeorama_data, 
                edge_style=edge_style,
                show_message_names=show_messages
            )
        
        # Display the visualization
        canvas = MatplotlibCanvas(fig)
        
        # Add navigation toolbar
        toolbar = NavigationToolbar(canvas, self)
        self.canvas_container.addWidget(toolbar)
        self.canvas_container.addWidget(canvas)
    
    def generate_report(self):
        """Generate the selected text report"""
        if not self.codeorama_data:
            self.report_text.setText("No Scratch file loaded.")
            return
            
        # Create report generator
        report_generator = TextReportGenerator(self.codeorama_data)
        
        # Get selected report type
        report_type = self.report_type_combo.currentText()
        
        # Generate the appropriate report
        if report_type == 'Broadcast Report':
            report = report_generator.generate_broadcast_report()
        elif report_type == 'Receive Report':
            report = report_generator.generate_receive_report()
        elif report_type == 'Script Layout':
            report = report_generator.generate_script_layout()
        else:
            report = "Unknown report type selected."
        
        # Display the report
        self.report_text.setText(report)
    
    def fold_all_scripts(self):
        """Fold all script blocks to minimal view"""
        if not self.codeorama_data:
            return
        
        # Create a folding state dict with all scripts folded
        folding_state = {}
        for sprite, event in self.codeorama_data['scripts'].keys():
            scripts = self.codeorama_data['scripts'][(sprite, event)]
            for i in range(len(scripts)):
                folding_state[(sprite, event, i)] = True
        
        # Save folding state
        self.settings.setValue("script_folding", folding_state)
        
        # Update visualization
        self.update_visualization()

    def unfold_all_scripts(self):
        """Unfold all script blocks to full view"""
        if not self.codeorama_data:
            return
        
        # Create an empty folding state dict (all unfolded)
        self.settings.setValue("script_folding", {})
        
        # Update visualization
        self.update_visualization()
    
    def save_configuration(self):
        """Save the current visualization configuration to a file"""
        if not self.codeorama_data:
            QMessageBox.warning(self, "No Data", "No Scratch file loaded to save configuration for.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Configuration", "", "Configuration Files (*.json)"
        )
        
        if file_path:
            # Gather all configuration settings
            config = {
                "edge_style": self.edge_style_combo.currentText(),
                "show_messages": self.show_messages_check.isChecked(),
                "layout_config": self.settings.value("layout_config", {}, type=dict),
                "script_folding": self.settings.value("script_folding", {}, type=dict),
                # Add more settings as needed
            }
            
            # Save to file
            try:
                with open(file_path, 'w') as f:
                    json.dump(config, f)
                
                QMessageBox.information(self, "Configuration Saved", 
                                     "Visualization settings saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save configuration: {str(e)}")

    def load_configuration(self):
        """Load a saved visualization configuration from a file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Configuration", "", "Configuration Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    config = json.load(f)
                
                # Apply the loaded configuration
                if "edge_style" in config:
                    self.edge_style_combo.setCurrentText(config["edge_style"])
                
                if "show_messages" in config:
                    self.show_messages_check.setChecked(config["show_messages"])
                
                if "layout_config" in config:
                    self.settings.setValue("layout_config", config["layout_config"])
                
                if "script_folding" in config:
                    self.settings.setValue("script_folding", config["script_folding"])
                
                # Update visualization if we have data
                if self.codeorama_data:
                    self.update_visualization()
                
                QMessageBox.information(self, "Configuration Loaded", 
                                     "Visualization settings loaded successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load configuration: {str(e)}")

    def export_visualization(self):
        """Export the current visualization or data"""
        if not self.codeorama_data:
            QMessageBox.warning(self, "No Data", "No visualization to export.")
            return
        
        # Create export dialog
        export_dialog = QDialog(self)
        export_dialog.setWindowTitle("Export Options")
        export_dialog.setMinimumWidth(400)
        
        # Dialog layout
        layout = QVBoxLayout(export_dialog)
        
        # Export format selection
        format_group = QGroupBox("Export Format")
        format_layout = QVBoxLayout(format_group)
        
        format_combo = QComboBox()
        format_combo.addItems([
            "PDF (CodeOrama Layout)", 
            "Text (Detailed Report)", 
            "CSV (Edge List)",
            "Excel/LibreCalc (Multiple Sheets)",
            "JSON (For Other Tools)",
            "Image (Current Visualization)"
        ])
        format_layout.addWidget(format_combo)
        
        layout.addWidget(format_group)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(export_dialog.accept)
        button_box.rejected.connect(export_dialog.reject)
        layout.addWidget(button_box)
        
        # Show dialog
        if export_dialog.exec_():
            # Get selected format
            selected_format = format_combo.currentText()
            
            # Get export path based on selected format
            file_filter = ""
            default_extension = ""
            
            if selected_format == "PDF (CodeOrama Layout)":
                file_filter = "PDF Files (*.pdf)"
                default_extension = ".pdf"
            elif selected_format == "Text (Detailed Report)":
                file_filter = "Text Files (*.txt)"
                default_extension = ".txt"
            elif selected_format == "CSV (Edge List)":
                file_filter = "CSV Files (*.csv)"
                default_extension = ".csv"
            elif selected_format == "Excel/LibreCalc (Multiple Sheets)":
                file_filter = "Excel Files (*.xlsx);;ODS Files (*.ods)"
                default_extension = ".xlsx"
            elif selected_format == "JSON (For Other Tools)":
                file_filter = "JSON Files (*.json)"
                default_extension = ".json"
            elif selected_format == "Image (Current Visualization)":
                file_filter = "PNG Files (*.png);;SVG Files (*.svg);;PDF Files (*.pdf)"
                default_extension = ".png"
            
            # Get file path
            file_path, selected_filter = QFileDialog.getSaveFileName(
                self, "Export Visualization", "", file_filter
            )
            
            if file_path:
                # Add file extension if not provided
                if not os.path.splitext(file_path)[1]:
                    file_path += default_extension
                
                # Get current configuration
                layout_config = self.settings.value("layout_config", {}, type=dict)
                
                # Export based on selected format
                try:
                    if selected_format == "Image (Current Visualization)":
                        # Export current visualization
                        if hasattr(self.visualizer, 'fig'):
                            self.visualizer.fig.savefig(file_path, bbox_inches='tight')
                            success = True
                        else:
                            raise Exception("No visualization figure available")
                    else:
                        # Create exporter and export
                        exporter = CodeOramaExporter(self.codeorama_data, layout_config)
                        
                        if selected_format == "PDF (CodeOrama Layout)":
                            success = exporter.export_to_pdf(file_path)
                        elif selected_format == "Text (Detailed Report)":
                            success = exporter.export_to_text(file_path)
                        elif selected_format == "CSV (Edge List)":
                            success = exporter.export_edge_list(file_path)
                        elif selected_format == "Excel/LibreCalc (Multiple Sheets)":
                            success = exporter.export_to_excel(file_path)
                        elif selected_format == "JSON (For Other Tools)":
                            success = exporter.export_to_json(file_path)
                        else:
                            raise Exception(f"Unsupported export format: {selected_format}")
                    
                    if success:
                        QMessageBox.information(self, "Export Complete", 
                                             f"Data exported to {file_path}")
                    else:
                        QMessageBox.warning(self, "Export Failed", 
                                          "Failed to export data. See console for details.")
                        
                except Exception as e:
                    QMessageBox.critical(self, "Export Error", 
                                       f"An error occurred during export:\n{str(e)}")
    
    def edit_names(self):
        """Open dialog to edit node and edge names"""
        if not self.codeorama_data:
            QMessageBox.warning(self, "No Data", "No data loaded to edit names.")
            return
            
        # This would open a dialog to edit sprite, event, and message names
        QMessageBox.information(self, "Not Implemented", 
                              "Name editing is not implemented in this prototype.")
    
    def edit_colors(self):
        """Open dialog to edit color scheme"""
        # This would open a dialog to customize colors for different elements
        dialog = QColorDialog(self)
        dialog.setCurrentColor(self.visualizer.block_colors['default'])
        if dialog.exec_():
            color = dialog.currentColor().name()
            # This would update colors but just show a message for now
            QMessageBox.information(self, "Color Selected", 
                                  f"Selected color: {color}\nColor customization to be implemented.")
    
    def configure_layout(self):
        """Open dialog to configure layout (sprite/event order)"""
        if not self.codeorama_data:
            QMessageBox.warning(self, "No Data", "No Scratch file loaded to configure.")
            return
        
        # Load any existing configuration
        config = self.settings.value("layout_config", {}, type=dict)
        
        # Open the configuration dialog
        dialog = OrderConfigDialog(
            self,
            sprites=self.codeorama_data['sprites'],
            events=self.codeorama_data['events'],
            current_config=config
        )
        
        if dialog.exec_():
            # Get the new configuration
            new_config = dialog.get_configuration()
            
            # Save to settings
            self.settings.setValue("layout_config", new_config)
            
            # Update visualization with new config
            self.update_visualization()
    
    def _load_settings(self):
        """Load application settings"""
        edge_style = self.settings.value("edge_style", "improved")
        show_messages = self.settings.value("show_messages", True, type=bool)
        
        self.edge_style_combo.setCurrentText(edge_style)
        self.show_messages_check.setChecked(show_messages)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = ECodeOramaApp()
    main_window.show()
    sys.exit(app.exec_())
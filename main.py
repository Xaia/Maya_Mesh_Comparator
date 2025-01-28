import maya.cmds as cmds
import json
from PySide2 import QtWidgets, QtCore, QtGui

class MeshComparatorUI(QtWidgets.QDialog):
    def __init__(self):
        super(MeshComparatorUI, self).__init__()
        self.setWindowTitle("Mesh Comparator")
        self.setMinimumSize(800, 600)
        self.selected_objects = []
        self.transform_diffs = []
        self.shape_diffs = []
        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_widgets(self):
        self.title_label = QtWidgets.QLabel("Select two meshes and click Compare")
        self.compare_btn = QtWidgets.QPushButton("Compare")
        self.save_btn = QtWidgets.QPushButton("Save Report")
        self.objects_label = QtWidgets.QLabel("Selected Objects:")
        self.object1_label = QtWidgets.QLabel("None")
        self.object2_label = QtWidgets.QLabel("None")
        
        self.tab_widget = QtWidgets.QTabWidget()
        self.transform_tab = QtWidgets.QWidget()
        self.shape_tab = QtWidgets.QWidget()
        
        self.tab_widget.addTab(self.transform_tab, "Transform Attributes")
        self.tab_widget.addTab(self.shape_tab, "Shape Attributes")
        
        self.create_transform_tab()
        self.create_shape_tab()

    def create_layout(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.title_label)
        
        object_layout = QtWidgets.QHBoxLayout()
        object_layout.addWidget(self.objects_label)
        object_layout.addWidget(self.object1_label)
        object_layout.addWidget(self.object2_label)
        main_layout.addLayout(object_layout)
        
        main_layout.addWidget(self.tab_widget)
        
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.compare_btn)
        button_layout.addWidget(self.save_btn)
        main_layout.addLayout(button_layout)

    def create_transform_tab(self):
        layout = QtWidgets.QVBoxLayout(self.transform_tab)
        self.transform_table = QtWidgets.QTableWidget()
        self.transform_table.setColumnCount(3)
        self.transform_table.setHorizontalHeaderLabels(["Attribute", "Object 1", "Object 2"])
        self.transform_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        layout.addWidget(self.transform_table)

    def create_shape_tab(self):
        layout = QtWidgets.QVBoxLayout(self.shape_tab)
        self.shape_table = QtWidgets.QTableWidget()
        self.shape_table.setColumnCount(3)
        self.shape_table.setHorizontalHeaderLabels(["Attribute", "Object 1", "Object 2"])
        self.shape_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        layout.addWidget(self.shape_table)

    def create_connections(self):
        self.compare_btn.clicked.connect(self.compare_meshes)
        self.save_btn.clicked.connect(self.save_report)

    def get_attributes(self, node):
        attributes = {}
        if not cmds.objExists(node):
            return attributes
            
        for attr in cmds.listAttr(node, scalar=True, visible=True):
            try:
                if cmds.getAttr(f"{node}.{attr}", settable=True):
                    value = cmds.getAttr(f"{node}.{attr}")
                    attributes[attr] = value
            except:
                continue
        return attributes

    def compare_attributes(self, node1, node2):
        node1_attrs = self.get_attributes(node1)
        node2_attrs = self.get_attributes(node2)
        
        all_attrs = sorted(list(set(node1_attrs.keys()) | set(node2_attrs.keys())))
        differences = []
        
        for attr in all_attrs:
            val1 = node1_attrs.get(attr, "N/A")
            val2 = node2_attrs.get(attr, "N/A")
            differences.append((attr, val1, val2))
            
        return differences

    def populate_table(self, table, differences):
        table.setRowCount(0)
        for row, (attr, val1, val2) in enumerate(differences):
            table.insertRow(row)
            
            item_attr = QtWidgets.QTableWidgetItem(attr)
            item_val1 = QtWidgets.QTableWidgetItem(str(val1))
            item_val2 = QtWidgets.QTableWidgetItem(str(val2))
            
            table.setItem(row, 0, item_attr)
            table.setItem(row, 1, item_val1)
            table.setItem(row, 2, item_val2)
            
            if str(val1) != str(val2):
                item_attr.setBackground(QtGui.QColor(255, 150, 150))
                item_val1.setBackground(QtGui.QColor(255, 150, 150))
                item_val2.setBackground(QtGui.QColor(255, 150, 150))

    def get_report_data(self):
        return {
            "objects": {
                "object1": self.object1_label.text(),
                "object2": self.object2_label.text()
            },
            "transform_attributes": self.transform_diffs,
            "shape_attributes": self.shape_diffs
        }

    def save_report(self):
        if not self.transform_diffs and not self.shape_diffs:
            cmds.warning("No comparison data to save. Perform a comparison first.")
            return

        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Report", "", "JSON Files (*.json);;Text Files (*.txt)"
        )

        if not file_path:
            return

        report_data = self.get_report_data()
        
        try:
            if file_path.endswith('.json'):
                with open(file_path, 'w') as f:
                    json.dump(report_data, f, indent=4)
            else:
                with open(file_path, 'w') as f:
                    f.write(f"Comparison Report between {report_data['objects']['object1']} and {report_data['objects']['object2']}\n\n")
                    
                    f.write("=== Transform Attributes ===\n")
                    for attr in report_data['transform_attributes']:
                        f.write(f"{attr[0]}:\n  {report_data['objects']['object1']}: {attr[1]}\n  {report_data['objects']['object2']}: {attr[2]}\n\n")
                    
                    f.write("\n=== Shape Attributes ===\n")
                    for attr in report_data['shape_attributes']:
                        f.write(f"{attr[0]}:\n  {report_data['objects']['object1']}: {attr[1]}\n  {report_data['objects']['object2']}: {attr[2]}\n\n")
            
            cmds.confirmDialog(title="Save Successful", message=f"Report saved to:\n{file_path}")
        except Exception as e:
            cmds.warning(f"Error saving file: {str(e)}")
            cmds.confirmDialog(title="Save Error", message=f"Failed to save file:\n{str(e)}", button=["OK"])

    def compare_meshes(self):
        self.selected_objects = cmds.ls(selection=True, type="transform")
        
        if len(self.selected_objects) != 2:
            cmds.warning("Please select exactly two mesh transforms")
            return
            
        self.object1_label.setText(self.selected_objects[0])
        self.object2_label.setText(self.selected_objects[1])
        
        # Get shape nodes
        shape1 = cmds.listRelatives(self.selected_objects[0], shapes=True)[0]
        shape2 = cmds.listRelatives(self.selected_objects[1], shapes=True)[0]
        
        # Compare transform attributes
        self.transform_diffs = self.compare_attributes(self.selected_objects[0], self.selected_objects[1])
        self.populate_table(self.transform_table, self.transform_diffs)
        
        # Compare shape attributes
        self.shape_diffs = self.compare_attributes(shape1, shape2)
        self.populate_table(self.shape_table, self.shape_diffs)

def show_ui():
    global ui
    try:
        ui.close()
    except:
        pass
    ui = MeshComparatorUI()
    ui.show()

show_ui()

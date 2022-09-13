import re
from PyQt5.QtGui import QTextBlock
from numpy.core.numeric import True_

from qtpy import QT_VERSION
from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets

QT5 = QT_VERSION[0] == '5'  # NOQA

from labelme.logger import logger
import labelme.utils
import os

# TODO(unknown):
# - Calculate optimal position so as not to go out of screen area.


class LabelQLineEdit(QtWidgets.QLineEdit):

    def setListWidget(self, list_widget):
        self.list_widget = list_widget

    def keyPressEvent(self, e):
        if e.key() in [QtCore.Qt.Key_Up, QtCore.Qt.Key_Down]:
            self.list_widget.keyPressEvent(e)
        else:
            super(LabelQLineEdit, self).keyPressEvent(e)

class LabelDialog(QtWidgets.QDialog):

    def __init__(self, text="Select object label", parent=None, labels=None,
                 sort_labels=True, show_text_field=True,
                 completion='startswith', fit_to_content=None, flags=None):
        if fit_to_content is None:
            fit_to_content = {'row': False, 'column': True}
        self._fit_to_content = fit_to_content

        super(LabelDialog, self).__init__(parent)
        self.edit = LabelQLineEdit()
        self.edit.setPlaceholderText(text) #placeholder for the top text field
        self.edit.setValidator(labelme.utils.labelValidator())
        self.edit.editingFinished.connect(self.postProcess)
        self.edit.setReadOnly(True)
        if flags:
            self.edit.textChanged.connect(self.updateFlags)
        layout = QtWidgets.QGridLayout()
        if show_text_field:
            layout.addWidget(self.edit,0,0,1,3)
        
        
        # buttons for ok and cancel
        self.buttonBox = bb = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal,
            self,
        )
        bb.button(bb.Ok).setIcon(labelme.utils.newIcon('done'))
        bb.button(bb.Cancel).setIcon(labelme.utils.newIcon('undo'))
        bb.accepted.connect(self.validate)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb,1,1)


        # list of labels (hard coded at app.py, search for self.labeldialog.setlabellist(....))
        # not using this right now
        self.labelList = QtWidgets.QListWidget()
        if self._fit_to_content['row']:
            self.labelList.setHorizontalScrollBarPolicy(
                QtCore.Qt.ScrollBarAlwaysOff
            )
        if self._fit_to_content['column']:
            self.labelList.setVerticalScrollBarPolicy(
                QtCore.Qt.ScrollBarAlwaysOff
            )
        self._sort_labels = sort_labels
        if labels:
            print(labels)
            self.labelList.addItems(labels)
        if self._sort_labels:
            self.labelList.sortItems()
        else:
            self.labelList.setDragDropMode(
                QtWidgets.QAbstractItemView.InternalMove)
        self.labelList.currentItemChanged.connect(self.labelSelected)
        self.edit.setListWidget(self.labelList)
        #layout.addWidget(self.labelList, 4,0) #just commented this one out so I dont have to change other stuff in the code


        #unsure checkbox
        self.unsure_check = QtWidgets.QCheckBox('Unsure')
        self.unsure_check.stateChanged.connect(self.check_unsure_changed)
        layout.addWidget(self.unsure_check, 1,0)

        #scanner issue checkbox
        self.scanner_issue_check = QtWidgets.QCheckBox('Scanner Issue')
        self.scanner_issue_check.stateChanged.connect(self.check_scanner_issue_changed)
        layout.addWidget(self.scanner_issue_check, 2,0)

        #low resolution checkbox
        self.low_resolution_check = QtWidgets.QCheckBox('Low Resolution Image')
        self.low_resolution_check.stateChanged.connect(self.low_resolution_check_changed)
        layout.addWidget(self.low_resolution_check, 3,0)


        self.remarks_add = LabelQLineEdit()
        self.remarks_add.setPlaceholderText("Any Remarks?")


        # button = QtWidgets.QPushButton('Add Remark') #button for adding remarks
        # button.clicked.connect(self.on_click_add_remark)

        remarksGroupBox = QtWidgets.QGroupBox("Remarks")
        vbox = QtWidgets.QVBoxLayout()
        # vbox.addWidget(self.remarks_edit)
        vbox.addWidget(self.remarks_add)
        # vbox.addWidget(button)

        remarksGroupBox.setLayout(vbox)
        layout.addWidget(remarksGroupBox, 5, 0, 1, 2)


        #Field list box
        fieldGroupBox = QtWidgets.QGroupBox("Field")
        fieldVBox = QtWidgets.QVBoxLayout()

        self.field_check = QtWidgets.QCheckBox('Captured on Field?')
        self.field_check.stateChanged.connect(self.field_check_changed)

        self.fieldList = QtWidgets.QListWidget()
        if self._fit_to_content['row']:
            self.fieldList.setHorizontalScrollBarPolicy(
                QtCore.Qt.ScrollBarAlwaysOff
            )
        if self._fit_to_content['column']:
            self.fieldList.setVerticalScrollBarPolicy(
                QtCore.Qt.ScrollBarAlwaysOff
            )

        field_list_labels = ["field1", "field2", "field3", "field4"]

        self.fieldList.addItems(field_list_labels)
        self.fieldList.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.fieldList.sortItems()

        fieldVBox.addWidget(self.field_check)
        fieldVBox.addWidget(self.fieldList)
        fieldGroupBox.setLayout(fieldVBox)
        #layout.addWidget(fieldGroupBox, 4, 2)


        #species area        
        self.aspiotus_rigidus_btn = QtWidgets.QRadioButton('Aspiotus Rigidus')
        self.aspiotus_destructor_btn = QtWidgets.QRadioButton('Aspiotus Destructor')
        self.aspiotus_excisus_btn = QtWidgets.QRadioButton('Aspiotus Excisus')
        self.aspiotus_nerii_btn = QtWidgets.QRadioButton('Aspiotus Nerii')
        self.species_unsure_btn = QtWidgets.QRadioButton('Unsure')

        self.species_btn_group = QtWidgets.QButtonGroup()
        self.species_btn_group.addButton(self.aspiotus_rigidus_btn)
        self.species_btn_group.addButton(self.aspiotus_destructor_btn)
        self.species_btn_group.addButton(self.aspiotus_excisus_btn)
        self.species_btn_group.addButton(self.aspiotus_nerii_btn)
        self.species_btn_group.addButton(self.species_unsure_btn)

        self.aspiotus_rigidus_btn.toggled.connect(self.onClickedSpecies)
        self.aspiotus_destructor_btn.toggled.connect(self.onClickedSpecies)
        self.aspiotus_excisus_btn.toggled.connect(self.onClickedSpecies)
        self.aspiotus_nerii_btn.toggled.connect(self.onClickedSpecies)
        self.species_unsure_btn.toggled.connect(self.onClickedSpecies)

        reset_button_species = QtWidgets.QPushButton('Reset')
        reset_button_species.clicked.connect(self.clearSpecies)
        groupBoxSpecies = QtWidgets.QGroupBox("Species")
        vboxSpecies = QtWidgets.QVBoxLayout()
        vboxSpecies.addWidget(self.aspiotus_rigidus_btn)
        vboxSpecies.addWidget(self.aspiotus_destructor_btn)
        vboxSpecies.addWidget(self.aspiotus_excisus_btn)   
        vboxSpecies.addWidget(self.aspiotus_nerii_btn)
        vboxSpecies.addWidget(self.species_unsure_btn)
        vboxSpecies.addWidget(reset_button_species)

        groupBoxSpecies.setLayout(vboxSpecies)
        layout.addWidget(groupBoxSpecies, 4, 1)

        
        #state labels area
        # self.unpara_no_egg_btn = QtWidgets.QRadioButton('Unparasitised without Eggs')
        # self.unpara_egg_btn = QtWidgets.QRadioButton('Unparasitised with Eggs')
        # self.para_no_hole_btn = QtWidgets.QRadioButton('Parasitised without Exit Hole')
        # self.para_hole_btn = QtWidgets.QRadioButton('Parasitised with Exit Hole')
        # self.dead_btn = QtWidgets.QRadioButton('Dead but Never Parasitised')
        # self.ignore_btn = QtWidgets.QRadioButton('Ignore Area')

        self.unpara_btn = QtWidgets.QRadioButton('Unparasitized')
        self.para_larva_btn = QtWidgets.QRadioButton('Parasitized with larva')
        self.para_pupa_btn = QtWidgets.QRadioButton('Parasitized with pupa')
        self.para_hole_btn = QtWidgets.QRadioButton('Parasitised with Exit Hole')
        self.ignore_btn = QtWidgets.QRadioButton('Ignore Area')

        self.state_btn_group = QtWidgets.QButtonGroup()
        # self.state_btn_group.addButton(self.unpara_no_egg_btn)
        # self.state_btn_group.addButton(self.unpara_egg_btn)
        # self.state_btn_group.addButton(self.para_no_hole_btn)
        # self.state_btn_group.addButton(self.para_hole_btn)
        # self.state_btn_group.addButton(self.dead_btn)
        # self.state_btn_group.addButton(self.ignore_btn)

        self.state_btn_group.addButton(self.unpara_btn)
        self.state_btn_group.addButton(self.para_larva_btn)
        self.state_btn_group.addButton(self.para_pupa_btn)
        self.state_btn_group.addButton(self.para_hole_btn)
        self.state_btn_group.addButton(self.ignore_btn)

        # self.unpara_no_egg_btn.toggled.connect(self.onClickedLabel)
        # self.unpara_egg_btn.toggled.connect(self.onClickedLabel)
        # self.para_no_hole_btn.toggled.connect(self.onClickedLabel)
        # self.para_hole_btn.toggled.connect(self.onClickedLabel)
        # self.dead_btn.toggled.connect(self.onClickedLabel)
        # self.ignore_btn.toggled.connect(self.onClickedLabel)

        self.unpara_btn.toggled.connect(self.onClickedLabel)
        self.para_larva_btn.toggled.connect(self.onClickedLabel)
        self.para_pupa_btn.toggled.connect(self.onClickedLabel)
        self.para_hole_btn.toggled.connect(self.onClickedLabel)
        self.ignore_btn.toggled.connect(self.onClickedLabel)

        reset_button = QtWidgets.QPushButton('Reset')
        reset_button.clicked.connect(self.clearStateRes)
        groupBox = QtWidgets.QGroupBox("State Label")
        vbox = QtWidgets.QVBoxLayout()
        # vbox.addWidget(self.unpara_no_egg_btn)
        # vbox.addWidget(self.unpara_egg_btn)
        # vbox.addWidget(self.para_no_hole_btn)   
        # vbox.addWidget(self.para_hole_btn)
        # vbox.addWidget(self.dead_btn)
        # vbox.addWidget(self.ignore_btn)
        # vbox.addWidget(reset_button)

        vbox.addWidget(self.unpara_btn)
        vbox.addWidget(self.para_larva_btn)
        vbox.addWidget(self.para_pupa_btn)   
        vbox.addWidget(self.para_hole_btn)
        vbox.addWidget(self.ignore_btn)
        vbox.addWidget(reset_button)

        groupBox.setLayout(vbox)
        layout.addWidget(groupBox, 4,0)

        
        # label_flags (try getting rid of this later on and see what happens, dont think its needed right now)
        if flags is None:
            flags = {}
        self._flags = flags
        self.flagsLayout = QtWidgets.QVBoxLayout()
        self.resetFlags()
        layout.addItem(self.flagsLayout)
        self.edit.textChanged.connect(self.updateFlags)
        self.setLayout(layout)
        # completion
        completer = QtWidgets.QCompleter()
        if not QT5 and completion != 'startswith':
            logger.warn(
                "completion other than 'startswith' is only "
                "supported with Qt5. Using 'startswith'"
            )
            completion = 'startswith'
        if completion == 'startswith':
            completer.setCompletionMode(QtWidgets.QCompleter.InlineCompletion)
            # Default settings.
            # completer.setFilterMode(QtCore.Qt.MatchStartsWith)
        elif completion == 'contains':
            completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
            completer.setFilterMode(QtCore.Qt.MatchContains)
        else:
            raise ValueError('Unsupported completion: {}'.format(completion))
        completer.setModel(self.labelList.model())
        self.edit.setCompleter(completer)


        #####
        self.prev_labels = {}

    #for when a label is clicked
    def onClickedLabel(self):
        radioBtn = self.sender()
        if radioBtn.isChecked():
            self.edit.setText(radioBtn.text())
            print(radioBtn.text())

    #for when a species is clicked
    def onClickedSpecies(self):
        radioBtn = self.sender()
        if radioBtn.isChecked():
            print(radioBtn.text())

    #for critical checkbox (unsure_check)
    def check_unsure_changed(self):
        checkBtn = self.sender()
        if checkBtn.isChecked():
            print("UNSURE CHECKED")
        else:
            print("UNSURE NOT CHECKED")

    #for scanner issue checkbox (scanner_issue)
    def check_scanner_issue_changed(self):
        checkBtn = self.sender()
        if checkBtn.isChecked():
            print("SCANNER ISSUE CHECKED")
        else:
            print("SCANNER ISSUE NOT CHECKED")

    #for low resolution image checkbox (low_resolution)
    def low_resolution_check_changed(self):
        checkBtn = self.sender()
        if checkBtn.isChecked():
            print("LOW RESOLUTION IMAGE CHECKED")
        else:
            print("LOW RESOLUTION IMAGE NOT CHECKED")

    # field checkbox (field_check)
    def field_check_changed(self):
        checkBtn = self.sender()
        if checkBtn.isChecked():
            print("FIELD CHECKED")
            self.fieldList.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        else:
            print("FIELD NOT CHECKED")
            items = self.fieldList.selectedItems()
            if len(items) > 0:
                for item in items:
                    item.setSelected(False)
            self.fieldList.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)

    #for adding remarks (button)
    # def on_click_add_remarks(self):
    #     if self.remarks_add.text() is not None and str(self.remarks_add.text()).strip() != "":
    #         self.addRemarks(str(self.remarks_add.text()).strip())
    #         self.remarks_add.setText(None)
    #     else:
    #         self.remarks_add.setText(None)

    # def addRemarks(self, text):
    #     text = text.strip() #strip removes spaces before and after
    #     if text != "":
    #         if self.reasonList.findItems(text, QtCore.Qt.MatchExactly):
    #             return


    #         if os.path.exists("label_list.txt"):
    #             with open("label_list.txt", "r", encoding="utf-8") as f:
    #                 contents = f.read()

    #             with open("label_list.txt", "a", encoding="utf-8") as f:
    #                 if contents[-1] != "\n":
    #                     f.write("\n")
    #                 f.write("{}\n".format(text))

    #         self.reasonList.addItem(text)
    #         self.reasonList.sortItems()

    def setLabelList(self, labels):
        self.removeAllLabels()
        self.labelList.addItems(labels)
        self.labelList.sortItems()
        
    def removeAllLabels(self):
        for i in range(self.labelList.count()):
            self.labelList.takeItem(0)
    def addLabelHistory(self, label):
        if self.labelList.findItems(label, QtCore.Qt.MatchExactly):
            return
        self.labelList.addItem(label)
        if self._sort_labels:
            self.labelList.sortItems()

    def labelSelected(self, item):
        if item is not None:
            self.edit.setText(item.text())

    def validate(self):
        text = self.edit.text()
        if hasattr(text, 'strip'):
            text = text.strip()
        else:
            text = text.trimmed()
        if text:
            self.accept()

    def postProcess(self):
        text = self.edit.text()
        if hasattr(text, 'strip'):
            text = text.strip()
        else:
            text = text.trimmed()
        self.edit.setText(text)

    def updateFlags(self, label_new):
        # keep state of shared flags
        flags_old = self.getFlags()

        flags_new = {}
        for pattern, keys in self._flags.items():
            if re.match(pattern, label_new):
                for key in keys:
                    flags_new[key] = flags_old.get(key, False)
        self.setFlags(flags_new)

    def deleteFlags(self):
        for i in reversed(range(self.flagsLayout.count())):
            item = self.flagsLayout.itemAt(i).widget()
            self.flagsLayout.removeWidget(item)
            item.setParent(None)

    def resetFlags(self, label=''):
        flags = {}
        for pattern, keys in self._flags.items():
            if re.match(pattern, label):
                for key in keys:
                    flags[key] = False
        self.setFlags(flags)

    def setFlags(self, flags):
        self.deleteFlags()
        for key in flags:
            item = QtWidgets.QCheckBox(key, self)
            item.setChecked(flags[key])
            self.flagsLayout.addWidget(item)
            item.show()

    def getFlags(self):
        flags = {}
        for i in range(self.flagsLayout.count()):
            item = self.flagsLayout.itemAt(i).widget()
            flags[item.text()] = item.isChecked()
        return flags
    # def clearReasons(self):
    #     items = self.reasonList.selectedItems()
    #     if len(items) > 0:
    #         for item in items:
    #             item.setSelected(False)

    def clearRemarks(self):
        self.remarks_add.setText('')
    
    def clearStateRes(self):
        self.state_btn_group.setExclusive(False)
        # self.unpara_no_egg_btn.setChecked(False)
        # self.unpara_egg_btn.setChecked(False)
        # self.para_no_hole_btn.setChecked(False)
        # self.para_hole_btn.setChecked(False)
        # self.dead_btn.setChecked(False)

        self.unpara_btn.setChecked(False)
        self.para_larva_btn.setChecked(False)
        self.para_pupa_btn.setChecked(False)
        self.para_hole_btn.setChecked(False)

        self.ignore_btn.setChecked(False)
        self.edit.clear()
        self.state_btn_group.setExclusive(True)

    def clearSpecies(self):
        self.species_btn_group.setExclusive(False)
        self.aspiotus_rigidus_btn.setChecked(False)
        self.aspiotus_destructor_btn.setChecked(False)
        self.aspiotus_excisus_btn.setChecked(False)
        self.aspiotus_nerii_btn.setChecked(False)
        self.species_unsure_btn.setChecked(False)
        self.species_btn_group.setExclusive(True)

    def clearField(self):
        items = self.fieldList.selectedItems()
        if len(items) > 0:
            for item in items:
                item.setSelected(False)

        self.field_check.setChecked(False)

    def popUp(self, text=None, move=True, flags=None, remarks=None, state_lbl=None, isUnsure=False, isScannerIssue=False, isLowResolution=False, species=None):
        if self._fit_to_content['row']:
            self.labelList.setMinimumHeight(
                self.labelList.sizeHintForRow(0) * self.labelList.count() + 2
            )
        if self._fit_to_content['column']:
            self.labelList.setMinimumWidth(
                self.labelList.sizeHintForColumn(0) + 2
            )
        # if text is None, the previous label in self.edit is kept
        if text is None:
            text = ""

        if flags:
            self.setFlags(flags)
        else:
            self.resetFlags(text)

        self.edit.setText(text)
        self.edit.setSelection(0, len(text))
        items = self.labelList.findItems(text, QtCore.Qt.MatchFixedString)
        if items:
            print()
            if len(items) != 1:
                logger.warning("Label list has duplicate '{}'".format(text))
            self.labelList.setCurrentItem(items[0])
            row = self.labelList.row(items[0])
            self.edit.completer().setCurrentRow(row)
        self.edit.setFocus(QtCore.Qt.PopupFocusReason)

        self.clearStateRes()

        # self.unpara_egg_btn.setChecked(True) #change this, this is only for the extreme point annotations

        if state_lbl is not None:
            print(state_lbl)
            # if state_lbl == "unpara_no_egg":
            #     self.unpara_no_egg_btn.setChecked(True)
            # elif state_lbl == "unpara_egg":
            #     self.unpara_egg_btn.setChecked(True)
            # elif state_lbl == "para_no_hole":
            #     self.para_no_hole_btn.setChecked(True)
            # elif state_lbl == "para_hole":
            #     self.para_hole_btn.setChecked(True)
            # elif state_lbl == "dead":
            #     self.dead_btn.setChecked(True)
            # elif state_lbl == "ignore":
            #     self.ignore_btn.setChecked(True)

            if state_lbl == "unpara":
                self.unpara_btn.setChecked(True)
            elif state_lbl == "para_larva":
                self.para_larva_btn.setChecked(True)
            elif state_lbl == "para_pupa":
                self.para_pupa_btn.setChecked(True)
            elif state_lbl == "para_hole":
                self.para_hole_btn.setChecked(True)
            elif state_lbl == "ignore":
                self.ignore_btn.setChecked(True)

        self.unsure_check.setChecked(isUnsure)
        self.scanner_issue_check.setChecked(isScannerIssue)
        self.low_resolution_check.setChecked(isLowResolution)

        self.clearSpecies()
        if species is not None:
            print(species)
            if species == "aspidiotus_rigidus":
                self.aspiotus_rigidus_btn.setChecked(True)
            elif species == "aspidiotus_destructor":
                self.aspiotus_destructor_btn.setChecked(True)
            elif species == "aspidiotus_excisus":
                self.aspiotus_excisus_btn.setChecked(True)
            elif species == "aspidiotus_nerii":
                self.aspiotus_nerii_btn.setChecked(True)
            elif species == "species_unsure_btn":
                self.species_unsure_btn.setChecked(True)

        # self.clearField()
        # if field is not None:
        #     self.field_check.setChecked(True)
        #     print(field)
        #     for x in range(self.fieldList.count()):
        #         if self.fieldList.item(x).text() == field:
        #             self.fieldList.item(x).setSelected(True)

        self.clearRemarks()
        if remarks is not None:
            self.remarks_add.setText(remarks)

        if move:
            self.move(QtGui.QCursor.pos())

        if self.exec_():

            state_lbl = None
            # if self.unpara_no_egg_btn.isChecked():
            #     state_lbl = "unpara_no_egg"
            # elif self.unpara_egg_btn.isChecked():
            #     state_lbl = "unpara_egg"
            # elif self.para_no_hole_btn.isChecked():
            #     state_lbl = "para_no_hole"
            # elif self.para_hole_btn.isChecked():
            #     state_lbl = "para_hole"
            # elif self.dead_btn.isChecked():
            #     state_lbl = "dead"
            # elif self.ignore_btn.isChecked():
            #     state_lbl = "ignore"

            if self.unpara_btn.isChecked():
                state_lbl = "unpara"
            elif self.para_larva_btn.isChecked():
                state_lbl = "para_larva"
            elif self.para_pupa_btn.isChecked():
                state_lbl = "para_pupa"
            elif self.para_hole_btn.isChecked():
                state_lbl = "para_hole"
            elif self.ignore_btn.isChecked():
                state_lbl = "ignore"

            isUnsure = False
            if self.unsure_check.isChecked():
                isUnsure = True

            isScannerIssue = False
            if self.scanner_issue_check.isChecked():
                isScannerIssue = True

            isLowResolution = False
            if self.low_resolution_check.isChecked():
                isLowResolution = True

            species = None
            if self.aspiotus_rigidus_btn.isChecked():
                print("in here")
                species = "aspidiotus_rigidus"
            elif self.aspiotus_destructor_btn.isChecked():
                species = "aspidiotus_destructor"
            elif self.aspiotus_excisus_btn.isChecked():
                species = "aspidiotus_excisus"
            elif self.aspiotus_nerii_btn.isChecked():
                species = "aspidiotus_nerii"
            elif self.species_unsure_btn.isChecked():
                species = "species_unsure_btn"

            # field = None
            # if self.field_check.isChecked():
            #     items = self.fieldList.selectedItems()
            #     if items != None:
            #         field = items[0].text()
            #         print("here ", field)

            remark = None
            if self.remarks_add.text() is not None and str(self.remarks_add.text()).strip() != "":
            #     reason = str(self.reason_edit.text()).strip().split(";")
                remark = str(self.remarks_add.text().strip())

            return self.edit.text(), self.getFlags(), state_lbl, remark, isUnsure, isScannerIssue, isLowResolution, species
        else:
            return None, None, None, None, False, False, False, None

""" class LabelQLineEdit(QtWidgets.QLineEdit):

    def setListWidget(self, list_widget):
        self.list_widget = list_widget

    def keyPressEvent(self, e):
        if e.key() in [QtCore.Qt.Key_Up, QtCore.Qt.Key_Down]:
            self.list_widget.keyPressEvent(e)
        else:
            super(LabelQLineEdit, self).keyPressEvent(e)

class LabelDialog(QtWidgets.QDialog):

    def __init__(self, text="Select object label", parent=None, labels=None, #ask ad about this
                 sort_labels=True, show_text_field=True,
                 completion='startswith', fit_to_content=None, flags=None):
        if fit_to_content is None:
            fit_to_content = {'row': False, 'column': True}
        self._fit_to_content = fit_to_content

        super(LabelDialog, self).__init__(parent)
        self.edit = LabelQLineEdit()
        self.edit.setPlaceholderText(text) #placeholder for the top text field
        self.edit.setValidator(labelme.utils.labelValidator())
        self.edit.editingFinished.connect(self.postProcess)
        self.edit.setReadOnly(True)
        if flags:
            self.edit.textChanged.connect(self.updateFlags)
        layout = QtWidgets.QGridLayout()
        if show_text_field:
            layout.addWidget(self.edit,0,0,1,3)
        
        
        # buttons for ok and cancel
        self.buttonBox = bb = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal,
            self,
        )
        bb.button(bb.Ok).setIcon(labelme.utils.newIcon('done'))
        bb.button(bb.Cancel).setIcon(labelme.utils.newIcon('undo'))
        bb.accepted.connect(self.validate)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb,1,1)


        # list of labels (hard coded at app.py, search for self.labeldialog.setlabellist(....))
        self.labelList = QtWidgets.QListWidget()
        if self._fit_to_content['row']:
            self.labelList.setHorizontalScrollBarPolicy(
                QtCore.Qt.ScrollBarAlwaysOff
            )
        if self._fit_to_content['column']:
            self.labelList.setVerticalScrollBarPolicy(
                QtCore.Qt.ScrollBarAlwaysOff
            )
        self._sort_labels = sort_labels
        if labels:
            print(labels)
            self.labelList.addItems(labels)
        if self._sort_labels:
            self.labelList.sortItems()
        else:
            self.labelList.setDragDropMode(
                QtWidgets.QAbstractItemView.InternalMove)
        self.labelList.currentItemChanged.connect(self.labelSelected)
        self.edit.setListWidget(self.labelList)
        layout.addWidget(self.labelList, 3,0)


        self.critical_check = QtWidgets.QCheckBox('Critical Defect')
        self.critical_check.stateChanged.connect(self.check_critical_changed)
        layout.addWidget(self.critical_check, 1,0)


        #Add reasons area
        self.reason_edit = LabelQLineEdit() #the grey box thing that gets a value when you select a reason from the box below
        self.reason_edit.setReadOnly(True)
        self.reason_edit.setStyleSheet("QLineEdit { border:none; background-color : #f0f0f0; }")
  
        # self.reason_edit.setPlaceholderText("Reason")
        # self.reason_edit.setValidator(labelme.utils.labelValidator())
        # self.reason_edit.editingFinished.connect(self.postProcess)

        self.reason_add = LabelQLineEdit()
        self.reason_add.setPlaceholderText("Add Reason")


        button = QtWidgets.QPushButton('Add Reason') #button for adding reason
        button.clicked.connect(self.on_click_add_reason)

        reasongroupBox = QtWidgets.QGroupBox("Reasons")
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.reason_edit)
        vbox.addWidget(self.reason_add)
        vbox.addWidget(button)

        reasongroupBox.setLayout(vbox)
        layout.addWidget(reasongroupBox, 2,1)


        #Reasons list box
        self.reasonList = QtWidgets.QListWidget()
        if self._fit_to_content['row']:
            self.reasonList.setHorizontalScrollBarPolicy(
                QtCore.Qt.ScrollBarAlwaysOff
            )
        if self._fit_to_content['column']:
            self.reasonList.setVerticalScrollBarPolicy(
                QtCore.Qt.ScrollBarAlwaysOff
            )

        if os.path.exists("label_list.txt"):
            with open("label_list.txt", "r", encoding="utf-8") as f:
                reason_list_labels = f.read().strip().split("\n")
        else:
            reason_list_labels = ["101", "102", "103", "104"]

        self.reasonList.addItems(reason_list_labels)
        self.reasonList.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.reasonList.sortItems()
        self.reasonList.itemSelectionChanged.connect(self.reasonSelected)
        # self.edit.setListWidget(self.labelList)
        layout.addWidget(self.reasonList, 3,1)

        
        #prediction labels area
        self.tp_btn = QtWidgets.QRadioButton('True Positive (TP)')
        self.fp_btn = QtWidgets.QRadioButton('False Positive (FP)')
        self.fn_btn = QtWidgets.QRadioButton('False Negative (FN)')

        self.tp_fp_btn_group = QtWidgets.QButtonGroup()
        self.tp_fp_btn_group.addButton(self.tp_btn)
        self.tp_fp_btn_group.addButton(self.fp_btn)
        self.tp_fp_btn_group.addButton(self.fn_btn)

        self.tp_btn.toggled.connect(self.onClicked)
        self.fp_btn.toggled.connect(self.onClicked)
        self.fn_btn.toggled.connect(self.onClicked)


        reset_button = QtWidgets.QPushButton('Reset')
        reset_button.clicked.connect(self.clearPredRes)
        groupBox = QtWidgets.QGroupBox("Prediction Label")
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.tp_btn)
        vbox.addWidget(self.fp_btn)
        vbox.addWidget(self.fn_btn)
        vbox.addWidget(reset_button)

        groupBox.setLayout(vbox)
        layout.addWidget(groupBox, 2,0)

        
        # label_flags (try getting rid of this later on and see what happens, dont think its needed right now)
        if flags is None:
            flags = {}
        self._flags = flags
        self.flagsLayout = QtWidgets.QVBoxLayout()
        self.resetFlags()
        layout.addItem(self.flagsLayout)
        self.edit.textChanged.connect(self.updateFlags)
        self.setLayout(layout)
        # completion
        completer = QtWidgets.QCompleter()
        if not QT5 and completion != 'startswith':
            logger.warn(
                "completion other than 'startswith' is only "
                "supported with Qt5. Using 'startswith'"
            )
            completion = 'startswith'
        if completion == 'startswith':
            completer.setCompletionMode(QtWidgets.QCompleter.InlineCompletion)
            # Default settings.
            # completer.setFilterMode(QtCore.Qt.MatchStartsWith)
        elif completion == 'contains':
            completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
            completer.setFilterMode(QtCore.Qt.MatchContains)
        else:
            raise ValueError('Unsupported completion: {}'.format(completion))
        completer.setModel(self.labelList.model())
        self.edit.setCompleter(completer)


        #####
        self.prev_labels = {}

    #for tp_button, fp_button, fn_button
    def onClicked(self):
        radioBtn = self.sender()
        if radioBtn.isChecked():
            print(radioBtn.text())

    #for critical checkbox (critical_check)
    def check_critical_changed(self):
        checkBtn = self.sender()
        if checkBtn.isChecked():
            print("CHECKED")
        else:
            print("NOT CHECKED")

    #for adding reasons (button)
    def on_click_add_reason(self):
        if self.reason_add.text() is not None and str(self.reason_add.text()).strip() != "":
            self.addReason(str(self.reason_add.text()).strip())
            self.reason_add.setText(None)
        else:
            self.reason_add.setText(None)

    def addReason(self, text):
        text = text.strip() #strip removes spaces before and after
        if text != "":
            if self.reasonList.findItems(text, QtCore.Qt.MatchExactly):
                return


            if os.path.exists("label_list.txt"):
                with open("label_list.txt", "r", encoding="utf-8") as f:
                    contents = f.read()

                with open("label_list.txt", "a", encoding="utf-8") as f:
                    if contents[-1] != "\n":
                        f.write("\n")
                    f.write("{}\n".format(text))

            self.reasonList.addItem(text)
            self.reasonList.sortItems()

    def setLabelList(self, labels):
        self.removeAllLabels()
        self.labelList.addItems(labels)
        self.labelList.sortItems()
        
    def removeAllLabels(self):
        for i in range(self.labelList.count()):
            self.labelList.takeItem(0)
    def addLabelHistory(self, label):
        if self.labelList.findItems(label, QtCore.Qt.MatchExactly):
            return
        self.labelList.addItem(label)
        if self._sort_labels:
            self.labelList.sortItems()

    def labelSelected(self, item):
        if item is not None:
            self.edit.setText(item.text())

    def reasonSelected(self):
        items = self.reasonList.selectedItems()
        if len(items) > 0:
            item_list = sorted([str(item.text()).strip() for item in items])

            self.reason_edit.setText(";".join(item_list))
        else:
            self.reason_edit.setText(None)


    def validate(self):
        text = self.edit.text()
        if hasattr(text, 'strip'):
            text = text.strip()
        else:
            text = text.trimmed()
        if text:
            self.accept()

    def postProcess(self):
        text = self.edit.text()
        if hasattr(text, 'strip'):
            text = text.strip()
        else:
            text = text.trimmed()
        self.edit.setText(text)

    def updateFlags(self, label_new):
        # keep state of shared flags
        flags_old = self.getFlags()

        flags_new = {}
        for pattern, keys in self._flags.items():
            if re.match(pattern, label_new):
                for key in keys:
                    flags_new[key] = flags_old.get(key, False)
        self.setFlags(flags_new)

    def deleteFlags(self):
        for i in reversed(range(self.flagsLayout.count())):
            item = self.flagsLayout.itemAt(i).widget()
            self.flagsLayout.removeWidget(item)
            item.setParent(None)

    def resetFlags(self, label=''):
        flags = {}
        for pattern, keys in self._flags.items():
            if re.match(pattern, label):
                for key in keys:
                    flags[key] = False
        self.setFlags(flags)

    def setFlags(self, flags):
        self.deleteFlags()
        for key in flags:
            item = QtWidgets.QCheckBox(key, self)
            item.setChecked(flags[key])
            self.flagsLayout.addWidget(item)
            item.show()

    def getFlags(self):
        flags = {}
        for i in range(self.flagsLayout.count()):
            item = self.flagsLayout.itemAt(i).widget()
            flags[item.text()] = item.isChecked()
        return flags
    def clearReasons(self):
        items = self.reasonList.selectedItems()
        if len(items) > 0:
            for item in items:
                item.setSelected(False)
    def clearPredRes(self):
        self.tp_fp_btn_group.setExclusive(False)
        self.tp_btn.setChecked(False)
        self.fp_btn.setChecked(False)
        self.fn_btn.setChecked(False)
        self.tp_fp_btn_group.setExclusive(True)

    def popUp(self, text=None, move=True, flags=None, reasons=None, pred_res=None, isCritical=False):
        if self._fit_to_content['row']:
            self.labelList.setMinimumHeight(
                self.labelList.sizeHintForRow(0) * self.labelList.count() + 2
            )
        if self._fit_to_content['column']:
            self.labelList.setMinimumWidth(
                self.labelList.sizeHintForColumn(0) + 2
            )
        # if text is None, the previous label in self.edit is kept
        if text is None:
            text = self.edit.text()


        if flags:
            self.setFlags(flags)
        else:
            self.resetFlags(text)

        self.edit.setText(text)
        self.edit.setSelection(0, len(text))
        items = self.labelList.findItems(text, QtCore.Qt.MatchFixedString)
        if items:
            print()
            if len(items) != 1:
                logger.warning("Label list has duplicate '{}'".format(text))
            self.labelList.setCurrentItem(items[0])
            row = self.labelList.row(items[0])
            self.edit.completer().setCurrentRow(row)
        self.edit.setFocus(QtCore.Qt.PopupFocusReason)

        self.clearPredRes()
        if pred_res is not None:
            print(pred_res)
            if pred_res == "tp":
                self.tp_btn.setChecked(True)
            elif pred_res == "fp":
                self.fp_btn.setChecked(True)
            elif pred_res == "fn":
                self.fn_btn.setChecked(True)

        self.critical_check.setChecked(isCritical)
        
        self.clearReasons()
        if reasons is not None and len(reasons) > 0:
            for reason in reasons:
                items = self.reasonList.findItems(reason, QtCore.Qt.MatchFixedString)
                items[0].setSelected(True)

        if move:
            self.move(QtGui.QCursor.pos())

        if self.exec_():

            pred_res = None
            if self.tp_btn.isChecked():
                pred_res = "tp"

            if self.fp_btn.isChecked():
                pred_res = "fp"

            if self.fn_btn.isChecked():
                pred_res = "fn"

            isCritical = False
            if self.critical_check.isChecked():
                isCritical = True

            reason = None
            if self.reason_edit.text() is not None and str(self.reason_edit.text()).strip() != "":
                reason = str(self.reason_edit.text()).strip().split(";")

            return self.edit.text(), self.getFlags(), pred_res, reason, isCritical
        else:
            return None, None, None, None, False """
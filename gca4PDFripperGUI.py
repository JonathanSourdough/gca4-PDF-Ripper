from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from pathlib import Path
import sys
import collections
import json
import copy
import PyPDF2
import gca4PDFripper


class profileBoxLayout(QVBoxLayout):
    def __init__(self, parent=None):
        QVBoxLayout.__init__(self)
        self.parent = parent
        self.hBoxes = []
        self.comboBox = QComboBox(insertPolicy=QComboBox.NoInsert)
        self.Load = QPushButton("Load")
        self.Save = QPushButton("Save")
        self.Delete = QPushButton("Delete")

        self.hBoxes.append(QHBoxLayout())
        self.hBoxes[0].addStretch(0)
        self.hBoxes[0].addWidget(QLabel("Saved Profiles"))
        self.hBoxes[0].addStretch(0)
        self.addLayout(self.hBoxes[0])

        self.hBoxes.append(QHBoxLayout())
        self.comboBox.setView(QListView())
        self.comboBox.setLineEdit(QLineEdit(placeholderText="New Profile"))
        self.hBoxes[1].addWidget(self.comboBox)
        for k in list(loadedJson.keys()):
            self.comboBox.addItem(k)
        self.comboBox.setCurrentIndex(self.comboBox.findText(parent.currentProfilename))
        self.addLayout(self.hBoxes[1])

        self.hBoxes.append(QHBoxLayout())
        self.hBoxes[2].addWidget(self.Load)
        self.Load.clicked.connect(self.loadLayout)
        self.hBoxes[2].addWidget(self.Save)
        self.Save.clicked.connect(self.saveProfile)
        self.hBoxes[2].addWidget(self.Delete)
        self.Delete.clicked.connect(self.deleteLayout)
        self.addLayout(self.hBoxes[2])

    def loadLayout(self, *args):
        QTimer.singleShot(0, lambda: self.parent.messageBox.hideBottommessage())
        global loadedJson
        currentText = self.comboBox.currentText()
        if currentText not in loadedJson.keys():
            return

        self.currentProfile = loadedJson[currentText]

        self.parent.setInfo(self.currentProfile)

        for _, v in loadedJson.items():
            v["lastUsed"] = False
        loadedJson[currentText]["lastUsed"] = True

        saveJson(loadedJson)
        loadJson()
        QTimer.singleShot(0, lambda: self.parent.messageBox.bottomMessage(currentText + " Loaded"))

    def saveProfile(self, *args):
        QTimer.singleShot(0, lambda: self.parent.messageBox.hideBottommessage())
        global loadedJson
        currentText = self.comboBox.currentText()
        if currentText == "" or currentText == "Defaults":
            return

        tempDict = copy.deepcopy(loadedJson)
        tempDict[currentText] = self.parent.getInfo()
        for _, v in tempDict.items():
            v["lastUsed"] = False
        tempDict[currentText]["lastUsed"] = True

        savedLayoutsnames = []
        for i in range(self.comboBox.count()):
            savedLayoutsnames.append(self.comboBox.itemText(i))
        if not currentText in savedLayoutsnames:
            self.comboBox.insertItem(2, currentText.lower())
        self.parent.currentProfilename = currentText
        self.comboBox.setCurrentIndex(self.comboBox.findText(self.parent.currentProfilename))

        saveJson(tempDict)
        loadJson()
        QTimer.singleShot(0, lambda: self.parent.messageBox.bottomMessage(currentText + " Saved"))

    def deleteLayout(self, *args):
        QTimer.singleShot(0, lambda: self.parent.messageBox.hideBottommessage())
        currentText = self.comboBox.currentText()
        if self.comboBox.currentIndex() == -1 or currentText == "Defaults":
            return
        loadedJson.pop(currentText)
        self.comboBox.setCurrentIndex(self.comboBox.findText("Defaults"))
        self.comboBox.removeItem(self.comboBox.findText(currentText))
        self.loadLayout()
        QTimer.singleShot(0, lambda: self.parent.messageBox.bottomMessage(currentText + " Deleted"))


class hideSectionslayout(QVBoxLayout):
    def __init__(self, parent=None):
        QVBoxLayout.__init__(self)
        self.parent = parent
        self.hiddenState = [0, 2, 2, 2, 2, 2]
        self.checkBoxes = [
            QCheckBox(text="Show/Hide Sections"),
            QCheckBox(text="Character Path"),
            QCheckBox(text="GURPS PDF In Path"),
            QCheckBox(text="Character PDF Out Path"),
            QCheckBox(text="Books"),
            QCheckBox(text="Page/Book Table"),
        ]

        self.addWidget(self.checkBoxes[0])

        self.hidablesLayout = QVBoxLayout()
        self.hidablesLayout.addWidget(
            QLabel(
                "Note: This will show/hide different elements of this UI, but will not deactivate any element's functionality."
            )
        )

        for i, v in enumerate(self.checkBoxes):
            if i != 0:
                self.hidablesLayout.addWidget(v)
            v.pressed.connect(lambda i=i: self.updateHiddenstate(i))
        self.addLayout(self.hidablesLayout)
        self.addWidget(QFrame(frameShape=QFrame.HLine))

    def updateHiddenstate(self, index):
        if self.checkBoxes[index].isChecked() == True:
            state = 0
        else:
            state = 2
        self.hiddenState[index] = state
        self.parent.showHideall(self.hiddenState)

    def showHide(self, state):
        for v in range(self.hidablesLayout.count()):
            self.hidablesLayout.itemAt(v).widget().setVisible(state)

    def returnLayoutinfo(self):
        hiddenState = []
        for v in self.checkBoxes:
            if v.isChecked() == True:
                state = 2
            else:
                state = 0
            hiddenState.append(state)
        return hiddenState

    def setlayoutinfo(self, setInfo):
        for i, v in enumerate(setInfo):
            if v == 2:
                state = Qt.Checked
            else:
                state = Qt.Unchecked
            self.checkBoxes[i].setCheckState(state)
        self.hiddenState = setInfo


class filePathbox(QVBoxLayout):
    def __init__(self, parent=None, headerText="", labelTextlist=[]):
        QVBoxLayout.__init__(self)
        self.parent = parent
        self.pathList = []
        self.hBox = QHBoxLayout()

        self.addWidget(QLabel(headerText))

        self.pathBox = QLineEdit()
        self.pathBox.setEnabled(False)
        self.hBox.addWidget(self.pathBox)

        self.browseButton = QPushButton(text="Browse")
        self.browseButton.pressed.connect(lambda: self.openDialog())
        self.hBox.addWidget(self.browseButton)

        self.dialog = QFileDialog()

        self.addLayout(self.hBox)
        for v in labelTextlist:
            self.addWidget(QLabel(v))
        self.addWidget(QFrame(frameShape=QFrame.HLine))

    def openDialog(self):
        firstPath = Path(self.pathList[0])
        openDir = str(firstPath.parent)
        if firstPath.is_dir():
            openDir = str(firstPath)
        self.pathList = self.dialog.getOpenFileNames(
            caption="Select one or more files",
            dir=openDir,
            filter="Gurps Character Assistant files (*.gca4)",
        )[0]
        self.setlayoutinfo(self.pathList)

    def returnLayoutinfo(self):
        return self.pathList

    def setlayoutinfo(self, setInfo):
        self.pathList = setInfo
        if self.pathList == []:
            self.pathList = [
                str(Path.home() / "Documents" / "GURPS Character Assistant 4" / "characters")
            ]
        if Path.is_file(Path(self.pathList[0])):
            pathText = str(self.pathList[0])
            if len(self.pathList) > 1:
                pathText = pathText + " + " + str(len(self.pathList) - 1) + " more"
            self.pathBox.setText(pathText)
        else:
            self.pathBox.setText("Choose a file")

    def showHide(self, state):
        for v in range(self.count()):
            if self.itemAt(v).__class__ == QWidgetItem:
                self.itemAt(v).widget().setVisible(state)
            elif self.itemAt(v).__class__ == QHBoxLayout:
                for v2 in range(self.itemAt(v).count()):
                    if self.itemAt(v).itemAt(v2).__class__ == QWidgetItem:
                        self.itemAt(v).itemAt(v2).widget().setVisible(state)


class folderPathbox(QVBoxLayout):
    def __init__(self, parent=None, headerText="", labelTextlist=[]):
        QVBoxLayout.__init__(self)
        self.parent = parent
        self.path = ""
        self.hBox = QHBoxLayout()

        self.addWidget(QLabel(headerText))

        self.pathBox = QLineEdit()
        self.pathBox.setEnabled(False)
        self.hBox.addWidget(self.pathBox)

        self.browseButton = QPushButton(text="Browse")
        self.browseButton.pressed.connect(lambda: self.openDialog())
        self.hBox.addWidget(self.browseButton)

        self.dialog = QFileDialog()

        self.addLayout(self.hBox)
        for v in labelTextlist:
            self.addWidget(QLabel(v))
        self.addWidget(QFrame(frameShape=QFrame.HLine))

    def openDialog(self):
        self.path = self.dialog.getExistingDirectory(
            caption="Select one or more files", dir=self.path
        )
        self.pathBox.setText(self.path)

    def returnLayoutinfo(self):
        return self.path

    def setlayoutinfo(self, setInfo):
        self.path = setInfo
        self.pathBox.setText(self.path)

    def showHide(self, state):
        for v in range(self.count()):
            if self.itemAt(v).__class__ == QWidgetItem:
                self.itemAt(v).widget().setVisible(state)
            elif self.itemAt(v).__class__ == QHBoxLayout:
                for v2 in range(self.itemAt(v).count()):
                    if self.itemAt(v).itemAt(v2).__class__ == QWidgetItem:
                        self.itemAt(v).itemAt(v2).widget().setVisible(state)


class doItBoxLayout(QHBoxLayout):
    def __init__(self, parent=None):
        QHBoxLayout.__init__(self)
        self.parent = parent
        self.doitButton = QPushButton("DO IT!")
        self.addWidget(self.doitButton)
        self.doitButton.clicked.connect(lambda: self.doItEventHandler())

    def doItEventHandler(self):
        self.parent.messageBox.bottomMessage("Starting!")
        status = gca4PDFripper.doIt(self.parent.getInfo())
        self.parent.messageBox.bottomMessage(status)


class messageBoxLayout(QVBoxLayout):
    def __init__(self, parent=None, lineTop=True, lineBottom=False):
        QVBoxLayout.__init__(self)
        self.hBox = QHBoxLayout()
        self.message = QLabel(
            "Error... Cause you shouldnt be seeing this? O.o",
            font=QFont("Tahoma", 16, 75),
            visible=False,
        )
        self.line = QFrame(frameShape=QFrame.HLine, visible=False)

        if lineTop == True:
            self.addWidget(self.line)

        self.hBox.addStretch(0)
        self.hBox.addWidget(self.message)
        self.hBox.addStretch(0)
        self.addLayout(self.hBox)
        if lineBottom == True:
            self.addWidget(self.line)

    def hideBottommessage(self):
        self.line.setVisible(False)
        self.message.setVisible(False)

    def bottomMessage(self, message):
        self.line.setVisible(True)
        self.message.setText(message)
        self.message.setVisible(True)
        self.message.update()


class bookBoxLayout(QVBoxLayout):
    def __init__(self, parent=None):
        QVBoxLayout.__init__(self)
        self.parent = parent
        self.leftScrollarea = QScrollArea(
            verticalScrollBarPolicy=Qt.ScrollBarAlwaysOn,
            horizontalScrollBarPolicy=Qt.ScrollBarAlwaysOff,
            widgetResizable=True,
        )
        self.addBookbutton = QPushButton("Add Book")
        self.hBox = QHBoxLayout()
        self.bookVbox = QVBoxLayout()
        self.books = []

        self.addWidget(
            QLabel("Add additional PDFs with the shorthand connect them with page numbers")
        )
        self.spacing1 = QSpacerItem(39, 0)
        self.hBox.addSpacerItem(self.spacing1)
        self.hBox.addWidget(QLabel("Shorthand:"))
        self.spacing2 = QSpacerItem(11, 0)
        self.hBox.addSpacerItem(self.spacing2)
        self.hBox.addWidget(QLabel("PDF name:"))
        self.hBox.addStretch()
        self.addLayout(self.hBox)
        self.bookVbox.addStretch(0)

        self.intermediateWidget = QWidget()
        self.intermediateWidget.setLayout(self.bookVbox)
        self.leftScrollarea.setWidget(self.intermediateWidget)
        self.leftScrollarea.setMinimumWidth(self.bookVbox.minimumSize().width() + 15)
        self.addWidget(self.leftScrollarea)

        self.addWidget(
            QLabel(
                "Note: Place in the 'PDF in' directory, if not set this defaults to current directory \\gurpsPDFs"
            )
        )
        self.addWidget(self.addBookbutton)
        self.addBookbutton.pressed.connect(lambda: self.addBook())

    def removeBookEventHandler(self, buttonNumber):
        previousShorthand = ""
        previousPDFname = ""
        stopAt = len(self.books) - buttonNumber
        for i, v in enumerate(self.books[::-1]):
            if i < stopAt:
                nextShorthand = v["shorthand"].text()
                v["shorthand"].setText(previousShorthand)
                previousShorthand = nextShorthand
                nextPDFname = v["PDFname"].text()
                v["PDFname"].setText(previousPDFname)
                previousPDFname = nextPDFname
        for _, v in self.books[-1].items():
            v.deleteLater()
        self.books.pop(-1)
        self.bookHboxList[-1].deleteLater()
        self.bookHboxList.pop(-1)

    def addBook(self, shorthandText="", PDFnameText=""):
        self.books.append(
            {
                "close": QPushButton(text="X"),
                "shorthand": QLineEdit(text=shorthandText),
                "PDFname": QLineEdit(text=PDFnameText),
            }
        )
        close = self.books[-1]["close"]
        shorthand = self.books[-1]["shorthand"]
        PDFname = self.books[-1]["PDFname"]
        self.bookHboxList.append(QHBoxLayout())
        self.bookHboxList[-1].addWidget(close)
        close.setFixedSize(22, 22)
        close.pressed.connect(lambda x=len(self.books) - 1: self.removeBookEventHandler(x))
        self.bookHboxList[-1].addWidget(shorthand)
        shorthand.setFixedWidth(55)
        self.bookHboxList[-1].addSpacing(10)
        self.bookHboxList[-1].addWidget(PDFname)
        self.bookVbox.insertLayout(self.bookVbox.count() - 1, self.bookHboxList[-1])

    def returnLayoutinfo(self):
        books = {}
        for v in self.books:
            books[v["shorthand"].text()] = v["PDFname"].text()
        return books

    def setlayoutinfo(self, setInfo):
        for i, v in enumerate(self.books.copy()):
            for _, v2 in v.items():
                v2.deleteLater()
            self.bookHboxList[i].deleteLater()
        self.books = []
        self.bookHboxList = []
        for k, v in setInfo.items():
            self.addBook(k, v)

    def showHide(self, state):
        for v in range(self.count()):
            if self.itemAt(v).__class__ == QWidgetItem:
                self.itemAt(v).widget().setVisible(state)
            elif self.itemAt(v).__class__ == QHBoxLayout:
                for v2 in range(self.itemAt(v).count()):
                    if self.itemAt(v).itemAt(v2).__class__ == QWidgetItem:
                        self.itemAt(v).itemAt(v2).widget().setVisible(state)
                    if self.itemAt(v).itemAt(v2).__class__ == QSpacerItem:
                        if state == 0:
                            self.itemAt(v).itemAt(v2).changeSize(
                                0, 0, hData=QSizePolicy.Fixed, vData=QSizePolicy.Fixed
                            )
                        elif state == 1:
                            self.itemAt(v).itemAt(v2).changeSize(
                                0, 0, hData=QSizePolicy.Expanding, vData=QSizePolicy.Expanding
                            )
        if state == 0:
            self.spacing1.changeSize(0, 0, hData=QSizePolicy.Fixed, vData=QSizePolicy.Fixed)
            self.spacing2.changeSize(0, 0, hData=QSizePolicy.Fixed, vData=QSizePolicy.Fixed)
        elif state == 1:
            self.spacing1.changeSize(39, 0, hData=QSizePolicy.Fixed, vData=QSizePolicy.Fixed)
            self.spacing2.changeSize(11, 0, hData=QSizePolicy.Fixed, vData=QSizePolicy.Fixed)


class pageTableBoxLayout(QVBoxLayout):
    def __init__(self, parent=None):
        QVBoxLayout.__init__(self)
        self.parent = parent
        self.pageTable = QTableWidget(1, 1)
        self.addWidget(QLabel("Aditional Pages:"))
        self.addWidget(self.pageTable)
        self.pageTable.currentCellChanged.connect(self.tableCellChanged)
        self.addWidget(
            QLabel(
                "Note: Add extra pages to begining of sections, you can also use this as a way to arrange sections."
            )
        )

    def tableCellChanged(self, currentRow, currentCol, previousRow, previousCol):
        colCount = self.pageTable.columnCount()
        rowCount = self.pageTable.rowCount()
        if currentCol == colCount - 1:
            self.pageTable.setColumnCount(colCount + 1)
        if currentRow == rowCount - 1:
            self.pageTable.setRowCount(rowCount + 1)
        if currentRow < previousRow or currentCol < previousCol:
            for col in range(colCount - 1):
                for row in range(rowCount - 1):
                    item = self.pageTable.item(row, col)
                    if item is not None and item.text() != "":
                        if currentCol < col:
                            currentCol = col
                        if currentRow < row:
                            currentRow = row
            self.pageTable.setColumnCount(currentCol + 2)
            self.pageTable.setRowCount(currentRow + 2)
        for i in range(self.pageTable.columnCount()):
            self.pageTable.setHorizontalHeaderItem(i, QTableWidgetItem())
            self.pageTable.horizontalHeaderItem(i).setText("Book/Page " + str(i))

    def returnLayoutinfo(self):
        pageTabledict = {"sections": [], "pages": []}
        pageTable = self.pageTable
        for i in range(pageTable.rowCount() - 1):
            cell = pageTable.item(i, 0)
            if cell:
                cellText = cell.text()
                if cellText:
                    pageTabledict["sections"].append(cellText)
                else:
                    pageTabledict["sections"].append("")
            else:
                pageTabledict["sections"].append("")
        for i in range(pageTable.rowCount() - 1):
            pageTabledict["pages"].append([])
            for i2 in range(1, pageTable.columnCount() - 1):
                cell = pageTable.item(i, i2)
                if cell:
                    cellText = cell.text()
                    if cellText:
                        pageTabledict["pages"][i].append(cellText)
                    else:
                        pageTabledict["pages"][i].append("")
                else:
                    pageTabledict["pages"][i].append("")
        return pageTabledict

    def setlayoutinfo(self, setInfo):
        pageTable = self.pageTable
        pageTable.setRowCount(len(setInfo["sections"]))
        pageTable.setHorizontalHeaderItem(0, QTableWidgetItem())
        pageTable.horizontalHeaderItem(0).setText("Section")
        for i, v in enumerate(setInfo["sections"]):
            pageTable.setItem(i, 0, QTableWidgetItem())
            pageTable.item(i, 0).setText(v)
        for i, v in enumerate(setInfo["pages"]):
            for i2, v2 in enumerate(v, 1):
                if i2 >= pageTable.columnCount():
                    pageTable.setColumnCount(i2 + 1)
                    pageTable.setHorizontalHeaderItem(i2, QTableWidgetItem())
                    pageTable.horizontalHeaderItem(i2).setText("Book/Page " + str(i2))
                pageTable.setItem(i, i2, QTableWidgetItem())
                pageTable.item(i, i2).setText(v2)
        pageTable.setColumnCount(pageTable.columnCount() + 1)
        tableColumncount = pageTable.columnCount()
        tableRowcount = pageTable.rowCount()
        pageTable.setHorizontalHeaderItem(tableColumncount - 1, QTableWidgetItem())
        pageTable.horizontalHeaderItem(tableColumncount - 1).setText(
            "Book/Page " + str(tableColumncount - 1)
        )
        pageTable.setRowCount(tableRowcount + 1)

    def showHide(self, state):
        for v in range(self.count()):
            if self.itemAt(v).__class__ == QWidgetItem:
                self.itemAt(v).widget().setVisible(state)


class mainWindow(QWidget):
    def __init__(self, parent=None, **kwargs):
        QWidget.__init__(self)
        self.move(200, 200)
        global loadedJson
        global scriptDir
        for k, v in loadedJson.items():
            if v["lastUsed"] == True:
                self.currentProfile = v
                self.currentProfilename = k
                break
        self.windowBox = QHBoxLayout()

        self.vBox = QVBoxLayout()

        self.profilebox = profileBoxLayout(self)
        self.vBox.addLayout(self.profilebox)

        self.hideSectionsbox = hideSectionslayout(self)
        self.vBox.addLayout(self.hideSectionsbox)

        characterHeader = "Character files:"
        characterLabeltextList = [
            "Note:",
            'Can be one or more ".gca4" files',
        ]
        self.characterBox = filePathbox(self, characterHeader, characterLabeltextList)
        self.vBox.addLayout(self.characterBox)

        inHeader = "GURPS PDFs input directory:"
        inLabeltextList = [
            'Note:"',
            "If you add PDFs, make sure to match the PDF page number and the book page number",
        ]
        self.inBox = folderPathbox(self, inHeader, inLabeltextList)
        self.vBox.addLayout(self.inBox)

        outHeader = "Assembled PDF output file/folder"
        outLabeltextList = []
        self.outBox = folderPathbox(self, outHeader, outLabeltextList)
        self.vBox.addLayout(self.outBox)

        self.doitBox = doItBoxLayout(self)
        self.vBox.addLayout(self.doitBox)

        self.messageBox = messageBoxLayout(self)
        self.vBox.addLayout(self.messageBox)

        self.vBox.addStretch(0)
        self.windowBox.addLayout(self.vBox)

        self.bookBox = bookBoxLayout(self)
        self.windowBox.addLayout(self.bookBox)

        self.pageTableBox = pageTableBoxLayout(self)
        self.windowBox.addLayout(self.pageTableBox)

        self.setLayout(self.windowBox)
        self.setInfo(self.currentProfile)

        self.show()

    def getInfo(self):
        infodict = {}
        infodict["hiddenState"] = self.hideSectionsbox.returnLayoutinfo()
        infodict["charPath"] = self.characterBox.returnLayoutinfo()
        infodict["inPath"] = self.inBox.returnLayoutinfo()
        infodict["outPath"] = self.outBox.returnLayoutinfo()
        infodict["books"] = self.bookBox.returnLayoutinfo()
        infodict["extraPages"] = self.pageTableBox.returnLayoutinfo()
        return infodict

    def setInfo(self, setDict):
        if not "hiddenState" in setDict:
            setDict["hiddenState"] = [0, 2, 2, 2, 2, 2]
        self.hideSectionsbox.setlayoutinfo(setDict["hiddenState"])
        self.characterBox.setlayoutinfo(setDict["charPath"])
        self.inBox.setlayoutinfo(setDict["inPath"])
        self.outBox.setlayoutinfo(setDict["outPath"])
        self.bookBox.setlayoutinfo(setDict["books"])
        self.pageTableBox.setlayoutinfo(setDict["extraPages"])
        self.showHideall(setDict["hiddenState"])

    def showHideall(self, stateList):
        self.hideSectionsbox.showHide(stateList[0])
        self.characterBox.showHide(stateList[1])
        self.inBox.showHide(stateList[2])
        self.outBox.showHide(stateList[3])
        self.bookBox.showHide(stateList[4])
        self.pageTableBox.showHide(stateList[5])
        QTimer.singleShot(0, lambda: self.resize(self.minimumSize()))


def saveJson(jsonTosave):
    with open(saveProfilepath, "w+") as f:
        json.dump(jsonTosave, f)


def loadJson():
    global scriptDir
    global loadedJson
    loadedJson = "{}"
    if Path(saveProfilepath).is_file():
        try:
            with open(saveProfilepath, "r") as f:
                loadedJson = json.loads(f.read())
        except json.decoder.JSONDecodeError:
            loadedJson = "{}"
    if loadedJson == "" or loadedJson == "{}":
        loadedJson = {
            "Defaults": {
                "lastUsed": True,
                "charPath": [
                    str(Path.home() / "Documents" / "GURPS Character Assistant 4" / "characters")
                ],
                "outPath": str(scriptDir / "assembledPDFs"),
                "inPath": str(scriptDir / "gurpsPDFs"),
                "books": {
                    "B": "Basic Set Part 1 _ 2 - GURPS - 4th Edition.pdf",
                    "GF": "Gun Fu - GURPS - 4th Edition.pdf",
                    "HT": "High-Tech - GURPS - 4th Edition.pdf",
                    "P": "Powers - GURPS - 4th Edition.pdf",
                    "PU1:": "Imbuements - Power-Ups 1 - GURPS - 4th Edition.pdf",
                    "PU2:": "Perks - Power-Ups 2 - GURPS - 4th Edition.pdf",
                    "PU3:": "Talents - Power-Ups 3 - GURPS - 4th Edition.pdf",
                    "LT": "Low-Tech - GURPS - 4th Edition.pdf",
                    "M": "Magic - GURPS - 4th Edition.pdf",
                    "MA": "Martial Arts - GURPS - 4th Edition.pdf",
                    "MY": "Mysteries - GURPS - 4th Edition.pdf",
                    "PP": "Psionic Powers - GURPS - 4th Edition.pdf",
                    "Th": "Thaumatology - GURPS - 4th Edition.pdf",
                },
                "extraPages": {
                    "sections": ["Game Mechanics"],
                    "pages": [["B398", "B399", "B355", "B358", "B379", "B383"]],
                },
                "hiddenState": [0, 2, 2, 2, 2, 2],
            }
        }


def windowCreate():
    global instance
    instance = mainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    scriptDir = Path(__file__).resolve().parent
    saveProfilepath = scriptDir / "savedProfiles.json"
    loadJson()
    app = QApplication(sys.argv)
    windowCreate()

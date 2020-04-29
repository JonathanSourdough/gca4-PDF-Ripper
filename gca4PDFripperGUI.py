from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
import sys
import os
import collections
import json
import copy
import PyPDF2
import gca4PDFripper


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
            QLabel(
                "Add additional PDFs with the shorthand connect them with page numbers")
        )
        self.hBox.addSpacing(39)
        self.hBox.addWidget(QLabel("Shorthand:"))
        self.hBox.addSpacing(11)
        self.hBox.addWidget(QLabel("PDF name:"))
        self.hBox.addStretch()
        self.addLayout(self.hBox)
        self.bookVbox.addStretch(0)

        self.intermediateWidget = QWidget()
        self.intermediateWidget.setLayout(self.bookVbox)
        self.leftScrollarea.setWidget(self.intermediateWidget)
        self.leftScrollarea.setMinimumWidth(
            self.bookVbox.minimumSize().width() + 15)
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
        for tk, v in self.books[-1].items():
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
        close.pressed.connect(lambda x=len(self.books) -
                              1: self.removeBookEventHandler(x))
        self.bookHboxList[-1].addWidget(shorthand)
        shorthand.setFixedWidth(55)
        self.bookHboxList[-1].addSpacing(10)
        self.bookHboxList[-1].addWidget(PDFname)
        self.bookVbox.insertLayout(
            self.bookVbox.count() - 1, self.bookHboxList[-1])

    def returnLayoutinfo(self):
        books = {}
        for v in self.books:
            books[v["shorthand"].text()] = v["PDFname"].text()
        return {"books": books}

    def setlayoutinfo(self, setDict):
        for i, v in enumerate(self.books.copy()):
            for tk, v2 in v.items():
                v2.deleteLater()
            self.bookHboxList[i].deleteLater()
        self.books = []
        self.bookHboxList = []
        for k, v in setDict["books"].items():
            self.addBook(k, v)


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
        self.comboBox.setCurrentIndex(
            self.comboBox.findText(parent.currentProfilename))
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
        QTimer.singleShot(
            0, lambda: self.parent.messageBox.hideBottommessage())
        global loadedJson
        currentText = self.comboBox.currentText()
        if currentText not in loadedJson.keys():
            return

        self.currentProfile = loadedJson[currentText]

        self.parent.setInfo(self.currentProfile)

        for tk, v in loadedJson.items():
            v["lastUsed"] = False
        loadedJson[currentText]["lastUsed"] = True

        saveJson(loadedJson)
        loadJson()
        QTimer.singleShot(0, lambda: self.parent.messageBox.bottomMessage(
            currentText + " Loaded"))

    def saveProfile(self, *args):
        QTimer.singleShot(
            0, lambda: self.parent.messageBox.hideBottommessage())
        global loadedJson
        currentText = self.comboBox.currentText()
        if currentText == "" or currentText == "Defaults":
            return

        tempDict = copy.deepcopy(loadedJson)
        tempDict[currentText] = self.parent.getInfo()
        for tk, v in tempDict.items():
            v["lastUsed"] = False
        tempDict[currentText]["lastUsed"] = True

        savedLayoutsnames = []
        for i in range(self.comboBox.count()):
            savedLayoutsnames.append(self.comboBox.itemText(i))
        if not currentText in savedLayoutsnames:
            self.comboBox.insertItem(2, currentText.lower())
        self.parent.currentProfilename = currentText
        self.comboBox.setCurrentIndex(
            self.comboBox.findText(self.parent.currentProfilename))

        saveJson(tempDict)
        loadJson()
        QTimer.singleShot(
            0, lambda: self.parent.messageBox.bottomMessage(currentText + " Saved"))

    def deleteLayout(self, *args):
        QTimer.singleShot(
            0, lambda: self.parent.messageBox.hideBottommessage())
        currentText = self.comboBox.currentText()
        if self.comboBox.currentIndex() == -1 or currentText == "Defaults":
            return
        loadedJson.pop(currentText)
        self.comboBox.setCurrentIndex(self.comboBox.findText("Defaults"))
        self.comboBox.removeItem(self.comboBox.findText(currentText))
        self.loadLayout()
        QTimer.singleShot(0, lambda: self.parent.messageBox.bottomMessage(
            currentText + " Deleted"))


class characterBoxLayout(QVBoxLayout):
    def __init__(self, parent=None):
        QVBoxLayout.__init__(self)
        self.pathBox = QLineEdit()

        self.addWidget(QLabel("Character file/folder:"))
        self.addWidget(self.pathBox)
        self.addWidget(
            QLabel(
                "Note: Can be a file or a folder, if its a folder it will do for all .gca4 in that folder"
            )
        )
        self.addWidget(
            QLabel(
                'Note: If left blank, assumed directory is "current directory \\characters"')
        )
        self.addWidget(QFrame(frameShape=QFrame.HLine))

    def returnLayoutinfo(self):
        pathText = self.pathBox.text()
        if pathText != "":
            return {"charPath": pathText}
        else:
            self.pathBox.setText(cwd + "\\characters")
            return {"charPath": cwd + "\\characters"}

    def setlayoutinfo(self, setDict):
        self.pathBox.setText(setDict["charPath"])


class outBoxLayout(QVBoxLayout):
    def __init__(self, parent=None):
        QVBoxLayout.__init__(self)
        self.pathBox = QLineEdit()

        self.addWidget(QLabel("Assembled PDF output file/folder:"))
        self.addWidget(self.pathBox)
        self.addWidget(
            QLabel(
                'Note: If left blank assumed directory is "current directory \\assembledPDFs"')
        )
        self.addWidget(QFrame(frameShape=QFrame.HLine))

    def returnLayoutinfo(self):
        pathText = self.pathBox.text()
        if pathText != "":
            return {"outPath": pathText}
        else:
            self.pathBox.setText(cwd + "\\assembledPDFs")
            return {"outPath": cwd + "\\assembledPDFs"}

    def setlayoutinfo(self, setDict):
        self.pathBox.setText(setDict["outPath"])


class inBoxLayout(QVBoxLayout):
    def __init__(self, parent=None):
        QVBoxLayout.__init__(self)
        self.pathBox = QLineEdit()

        self.addWidget(QLabel("Game PDFs Input Dir:"))
        self.addWidget(self.pathBox)
        self.addWidget(
            QLabel(
                'Note: If left blank assumed directory is "current directory \\gurpsPDFs"')
        )
        self.addWidget(
            QLabel(
                "Note: If you add PDFs, make sure to trim the extra pages that offset the PDF page number from the book page number"
            )
        )
        self.addWidget(QFrame(frameShape=QFrame.HLine))

    def returnLayoutinfo(self):
        pathText = self.pathBox.text()
        if pathText != "":
            return {"inPath": pathText}
        else:
            self.pathBox.setText(cwd + "\\gurpsPDFs")
            return {"inPath": cwd + "\\gurpsPDFs"}

    def setlayoutinfo(self, setDict):
        self.pathBox.setText(setDict["inPath"])


class doItBoxLayout(QHBoxLayout):
    def __init__(self, parent=None):
        QHBoxLayout.__init__(self)
        self.parent = parent
        self.doitButton = QPushButton("DO IT!")
        self.addWidget(self.doitButton)
        self.doitButton.clicked.connect(lambda: self.doItEventHandler())

    def doItEventHandler(self):
        status = gca4PDFripper.doIt(self.parent.getInfo())
        QTimer.singleShot(
            0, lambda: self.parent.messageBox.bottomMessage(status))


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
        self.message.setVisible(True)
        self.message.setText(message)


class pageTableBoxLayout(QVBoxLayout):
    def __init__(self, parent=None):
        QVBoxLayout.__init__(self)
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

    def returnLayoutinfo(self):
        tempDict = {"sections": [], "pages": []}
        pageTable = self.pageTable
        for i in range(pageTable.rowCount() - 1):
            cell = pageTable.item(i, 0)
            if cell:
                cellText = cell.text()
                if cellText:
                    tempDict["sections"].append(cellText)
                else:
                    tempDict["sections"].append("")
            else:
                tempDict["sections"].append("")
        for i in range(pageTable.rowCount() - 1):
            tempDict["pages"].append([])
            for i2 in range(1, pageTable.columnCount() - 1):
                cell = pageTable.item(i, i2)
                if cell:
                    cellText = cell.text()
                    if cellText:
                        tempDict["pages"][i].append(cellText)
                    else:
                        tempDict["pages"][i].append("")
                else:
                    tempDict["pages"][i].append("")
        return {"extraPages": tempDict}

    def setlayoutinfo(self, setDict):
        pageTable = self.pageTable
        pageTable.setRowCount(len(setDict["extraPages"]["sections"]))
        pageTable.setHorizontalHeaderItem(0, QTableWidgetItem())
        pageTable.horizontalHeaderItem(0).setText("Section")
        for i, v in enumerate(setDict["extraPages"]["sections"]):
            pageTable.setItem(i, 0, QTableWidgetItem())
            pageTable.item(i, 0).setText(v)
        for i, v in enumerate(setDict["extraPages"]["pages"]):
            for i2, v2 in enumerate(v, 1):
                if i2 >= pageTable.columnCount():
                    pageTable.setColumnCount(i2 + 1)
                    pageTable.setHorizontalHeaderItem(i2, QTableWidgetItem())
                    pageTable.horizontalHeaderItem(
                        i2).setText("Book/Page " + str(i2))
                pageTable.setItem(i, i2, QTableWidgetItem())
                pageTable.item(i, i2).setText(v2)
        pageTable.setColumnCount(pageTable.columnCount() + 1)
        tableColumncount = pageTable.columnCount()
        tableRowcount = pageTable.rowCount()
        pageTable.setHorizontalHeaderItem(
            tableColumncount - 1, QTableWidgetItem())
        pageTable.horizontalHeaderItem(tableColumncount - 1).setText(
            "Book/Page " + str(tableColumncount - 1)
        )
        pageTable.setRowCount(tableRowcount + 1)


class mainWindow(QWidget):
    def __init__(self, parent=None, **kwargs):
        QWidget.__init__(self)
        self.move(200, 200)
        global loadedJson
        global cwd
        for k, v in loadedJson.items():
            if v["lastUsed"] == True:
                self.currentProfile = v
                self.currentProfilename = k
                break
        self.windowBox = QHBoxLayout()

        # Left Panel
        self.bookBox = bookBoxLayout(self)
        self.windowBox.addLayout(self.bookBox)

        self.middlePanelbox = QVBoxLayout()

        # Middle Panel
        self.profilebox = profileBoxLayout(self)
        self.middlePanelbox.addLayout(self.profilebox)

        self.characterBox = characterBoxLayout(self)
        self.middlePanelbox.addLayout(self.characterBox)

        self.outBox = outBoxLayout(self)
        self.middlePanelbox.addLayout(self.outBox)

        self.inBox = inBoxLayout(self)
        self.middlePanelbox.addLayout(self.inBox)

        self.doitBox = doItBoxLayout(self)
        self.middlePanelbox.addLayout(self.doitBox)

        self.messageBox = messageBoxLayout(self)
        self.middlePanelbox.addLayout(self.messageBox)

        # Right Panel
        self.middlePanelbox.addStretch(0)
        self.windowBox.addLayout(self.middlePanelbox)

        self.pageTableBox = pageTableBoxLayout(self)
        self.windowBox.addLayout(self.pageTableBox)

        self.setLayout(self.windowBox)
        self.setInfo(self.currentProfile)
        self.show()

    def getInfo(self):
        infodict = {}
        layouts = [self.bookBox, self.characterBox,
                   self.outBox, self.inBox, self.pageTableBox]
        for v in layouts:
            infodict.update(v.returnLayoutinfo())
        return infodict

    def setInfo(self, setDict):
        layouts = [self.bookBox, self.characterBox,
                   self.outBox, self.inBox, self.pageTableBox]
        for v in layouts:
            v.setlayoutinfo(setDict)


def saveJson(jsonTosave):
    global loadedJson
    with open(saveProfilepath + ".json", "w+") as f:
        json.dump(jsonTosave, f)


def loadJson():
    global cwd
    global loadedJson
    loadedJson = "{}"
    if os.path.isfile(saveProfilepath + ".json"):
        try:
            with open(saveProfilepath + ".json", "r") as f:
                loadedJson = json.loads(f.read())
        except json.decoder.JSONDecodeError:
            loadedJson = "{}"
    if loadedJson == "" or loadedJson == "{}":
        loadedJson = {
            "Defaults": {
                "lastUsed": True,
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
                "charPath": "C:\\Users\\"
                + os.getlogin()
                + "\\Documents\\GURPS Character Assistant 4\\characters",
                "outPath": cwd + "\\assembledPDFs",
                "inPath": cwd + "\\gurpsPDFs",
                "extraPages": {
                    "sections": ["Game Mechanics"],
                    "pages": [["B398", "B399", "B355", "B358", "B379", "B383"]],
                },
            }
        }


def windowCreate():
    global instance
    instance = mainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    cwd = os.path.dirname(os.path.realpath(__file__))
    print(cwd)
    saveProfilepath = cwd + "\\savedProfiles"
    loadJson()
    app = QApplication(sys.argv)
    windowCreate()

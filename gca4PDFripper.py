import os
import argparse
import copy
import PyPDF2
from fpdf import FPDF as fpdf
import io
import json


def find_between(s, first, last):
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""


def rfind_between(s, first, last):
    try:
        start = s.rindex(first) + len(first)
        end = s.rindex(last, start)
        return s[start:end]
    except ValueError:
        return ""


def getToPDF(characterList, books, pagesToPDF={}, sections=[]):
    lastSection = "Header"
    for v in characterList:
        if v == "":
            continue
        elif v[0] == "[":
            lastSection = v[1:-1]
            if lastSection not in sections:
                sections.append(lastSection)
            if lastSection not in pagesToPDF:
                pagesToPDF[lastSection] = copy.deepcopy(books)
        if "page" in v:
            pageIndex = v.index("page")
            booksAndpages = find_between(v[pageIndex:-1], "(", ")").split(",")
            for v in booksAndpages:
                possibleBooks = [i for i in books if i in v]
                try:
                    theBook = max(possibleBooks, key=len)
                except ValueError:
                    return "Error", "Book for " + v + " not found."
                thePage = v.split(theBook)[-1]
                if thePage not in pagesToPDF[lastSection][theBook]:
                    pagesToPDF[lastSection][theBook].append(thePage)
    pagesToPDF = removeEmptytoPDF(pagesToPDF, sections)
    return pagesToPDF, sections


def removeEmptytoPDF(toPDFdict, sections):
    for v in toPDFdict.copy():
        for k, sv in toPDFdict[v].copy().items():
            if sv == []:
                toPDFdict[v].pop(k)
        if toPDFdict[v] == {}:
            toPDFdict.pop(v)
            sections.pop(sections.index(v))
    return toPDFdict


def loadPDFs(pagesToPDF, PDFLocations, gurpsPDFs={}):
    for v in pagesToPDF:
        for sv in pagesToPDF[v]:
            if sv not in gurpsPDFs:
                gurpsPDFs[sv] = PyPDF2.PdfFileReader(PDFLocations[sv])
    return gurpsPDFs


def assemblePDFs(sections, pagesToPDF, gurpsPDFs, characterName, assembledPDFdir):
    assembledPDFs = {}
    assembledCharacterPDFdir = assembledPDFdir + "/" + characterName + "/"
    tempPDFpath = os.getcwd() + "/ShouldDissappear.pdf"
    for v in sections:
        assembledPDFs[v] = PyPDF2.PdfFileWriter()
        genTitlepage(v)
        temp = PyPDF2.PdfFileReader(tempPDFpath)
        assembledPDFs[v].addPage(temp.getPage(0))
        if os.path.exists(tempPDFpath):
            os.remove(tempPDFpath)
        for k, sv in pagesToPDF[v].items():
            for tv in sv:
                assembledPDFs[v].addPage(gurpsPDFs[k].getPage(int(tv) - 1))
        if not os.path.exists(assembledCharacterPDFdir):
            os.makedirs(assembledCharacterPDFdir)
        with open(assembledCharacterPDFdir + v + ".pdf", "wb") as fileOut:
            assembledPDFs[v].write(fileOut)
    assembledCharacterPDF = PyPDF2.PdfFileWriter()
    for v in assembledPDFs:
        assembledCharacterPDF.appendPagesFromReader(assembledPDFs[v])
    with open(assembledPDFdir + characterName + ".pdf", "wb") as fileOut:
        assembledCharacterPDF.write(fileOut)


def genTitlepage(string):
    tempPDFpath = os.getcwd() + "/ShouldDissappear.pdf"
    newPage = fpdf(format="letter", unit="pt")
    newPage.add_page(orientation="P")
    newPage.set_font("Arial", size=20)
    newPage.cell(0, 700, txt=string, ln=1, align="C")
    newPage.output(tempPDFpath, "F")


def loadJson(file):
    if os.path.isfile(file):
        with open(file, "r") as f:
            try:
                return json.loads(f.read())
            except json.decoder.JSONDecodeError:
                print("incorrect json format in extra-pages")
                quit()


def doIt(infoDict):
    global cwd
    characterDir = infoDict["charPath"]
    characters = []
    if os.path.isdir(characterDir):
        for v in os.listdir(characterDir):
            if os.path.isfile(characterDir + "\\" + v):
                if v.lower().endswith(".gca4"):
                    characters.append(characterDir + "\\" + v)
            if characters == []:
                return "No .gca4 files found in the listed directory"
    elif os.path.isfile(characterDir):
        if characterDir.lower().endswith(".gca4"):
            characters.append(characterDir)
        if characters == []:
            return "File listed is not a .gca4"
    else:
        return "Listed Character file/directory does not exist"

    outDir = infoDict["outPath"]
    if not outDir.endswith(("\\", "/")):
        outDir = outDir + "\\"
    if not os.path.isdir(outDir):
        os.mkdir(outDir)

    inDir = infoDict["inPath"]
    if inDir == "":
        inDir = cwd + "\\gurpsPDFs"
    if not os.path.isdir(inDir):
        return "Listed GURPS PDF directory does not exist"

    PDFsin = []
    booksDict = infoDict["books"]
    for v in os.listdir(inDir):
        if (inDir + "\\" + v).lower().endswith(".pdf"):
            PDFsin.append(v)
    for _, v in booksDict.items():
        if v not in PDFsin:
            return "Expected GURPS PDF missing from directory: " + v

    books = {}
    for k in booksDict:
        books[k] = []
    PDFlocations = {}
    for k, v in booksDict.items():
        PDFlocations[k] = inDir + "\\" + v

    pagesToPDF = {}
    pages = infoDict["extraPages"]["pages"]
    sections = infoDict["extraPages"]["sections"]
    for i, v in enumerate(sections):
        lastSection = v
        pagesToPDF[lastSection] = copy.deepcopy(books)
        for i2, v in enumerate(pages[i]):
            thisText = v
            if thisText != "":
                possibleBooks = [i for i in books if i in thisText]
                if possibleBooks != []:
                    theBook = max(possibleBooks, key=len)
                    thePage = thisText.split(theBook)[-1]
                    if thePage not in pagesToPDF[lastSection][theBook]:
                        pagesToPDF[lastSection][theBook].append(thePage)
                else:
                    return "Mismatch between shorthand and additional pages entry: " + str(thisText)

    gurpsPDFs = {}
    try:
        for v in characters:
            with open(v, encoding="utf8", errors="ignore") as file:
                characterList = file.read().split("\n")
            characterName = rfind_between(v, "/", ".")
            if characterName == "":
                characterName = rfind_between(v, "\\", ".")
            pagesToPDF, sections = getToPDF(characterList, books, pagesToPDF, sections)
            if pagesToPDF == "Error":
                return sections
            gurpsPDFs = loadPDFs(pagesToPDF, PDFlocations, gurpsPDFs)
            assemblePDFs(sections, pagesToPDF, gurpsPDFs, characterName, outDir)
    except IndexError as x:
        return "Page number exceeds book length,\ncheck the extra pages table and the shorthands for PDFs"
    return "Finished!"


if __name__ == "__main__":
    cwd = os.getcwd()
    description = """This program is designed to let you generate a PDF based off of a .gca4 file
    A default profile is supplied, and each piece can be overwritten seperately using arguments listed below
    """

    epilogue = (
        """json formatting example:
{
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
    "Th": "Thaumatology - GURPS - 4th Edition.pdf"
  },
  "charPath": "C:\\Users\\"""
        + os.getlogin()
        + """\\Documents\\GURPS Character Assistant 4\\characters",
  "outPath": \""""
        + cwd
        + """\\assembledPDFs",
  "inPath": \""""
        + cwd
        + """\\gurpsPDFs",
  "extraPages": {
    "sections": [
      "Game Mechanics"
    ],
    "pages": [
      [
        "B398",
        "B399",
        "B355",
        "B358",
        "B379",
        "B383"
      ]
    ]
  }
}"""
    )

    epilogue = epilogue.replace("\\", "/")

    parser = argparse.ArgumentParser(
        description=description,
        epilog=epilogue,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-p",
        "--profile",
        help="Full path to JSON file with all the available input information, this is in json format. Below is the defaults as an example",
        required=False,
    )
    parser.add_argument(
        "-c", "--character", help="Full file path to character sheet", required=False
    )
    parser.add_argument(
        "-g", "--gurps-pdfs", help="Full file path to GURPS PDFs directory", required=False
    )
    parser.add_argument("-o", "--output", help="Full file path to output folder", required=False)
    parser.add_argument(
        "-b",
        "--books",
        help='Full path to JSON file with Shorthand:PDFname for instructing which pdf to use when it sees an item in the "extra-pages" argument, or from the .gca4 file. See the "books" section within the json below for correct formatting',
        required=False,
    )
    parser.add_argument(
        "-e",
        "--extra-pages",
        help='Full path to JSON file with Additional pages and sections to add into the assembled PDF. See the "extraPages" section within the json below for correct formatting',
        required=False,
    )

    profile = {
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
        "charPath": "c:\\Users\\"
        + os.getlogin()
        + "\\Documents\\GURPS Character Assistant 4\\characters",
        "outPath": cwd + "\\assembledPDFs",
        "inPath": cwd + "\\gurpsPDFs",
        "extraPages": {
            "sections": ["Game Mechanics"],
            "pages": [["B398", "B399", "B355", "B358", "B379", "B383"]],
        },
    }

    args = vars(parser.parse_args())

    if args["profile"] != None:
        profile.update(loadJson(args["profile"]))

    if args["character"] != None:
        profile["charPath"] = args["character"]

    if args["gurps_pdfs"] != None:
        profile["inPath"] = args["gurps_pdfs"]

    if args["output"] != None:
        profile["outPath"] = args["output"]

    if args["books"] != None:
        profile["books"] = loadJson(args["books"])

    if args["extra_pages"] != None:
        profile["extraPages"] = loadJson(args["extra_pages"])

    print("Started")
    status = doIt(profile)
    print(status)

    # books = [ "B", "S", "MA", "M", "P", "L", "BT", "Bio", "CR", "SPI", "DR", "F", "HT", "PU:", "DF:", "GF", "Old West", "High-Tech", "UT", "PG1:", "PG2:", "LT:IA", "LT", "LT2:", "LT3:", "GLAD", "MY", "SU", "TS:CT", "PU1:", "PU2:", "PU3:", "H", "MA:", "A1:", "A2:", "A3:", "BS", "MH:", "Psi", "P3/21:", "MA:FC", "SV", "T:IW", "SC:AS", "DFM1:", "Th:UM", "LFM", "PP", "SS2:" "SS4:", "GT", "Th",

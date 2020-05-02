# gca4 PDF Ripper

This is a utility written in python for the GURPS Character Assistant program with the purpose of creating a PDF relevant to your character.

## Prerequisites

You will need to install python (designed and tested in Python 3.7.0)<br />
https://www.python.org/downloads/

Once python is installed you will need to install the required packages, Included in the repo is a requirements.txt to make your life easy.<br />
```
pip install -r requirements.txt
```

## How to run

Once you have done the above steps all you should need to do is run the script with command prompt.<br />

There is 2 ways to run the program:

Or with the GUI:
```
python gca4PDFripperGUI.py
```

With the CLI:
```
python gca4PDFripper.py
```

## How to use

The GUI will let you easily customize all the variables associated with creating a PDF from a gca4 file. Features explained inside the program.

The CLI will use the default character save location for GCA4, and will use my programmed in options as default. This will allow you to easily just run the program and it should assemble the PDF for you... However all parameters are changable (like in the GUI) via command line arguments if you are having issues, or and for advanced users. 

```
python gca4PDFripper.py -h
```

for more information


# Thanks

Thanks to everyone at Steven Jackson Games for creating GURPS and the character assistant.<br />
http://www.sjgames.com/gurps/<br />
http://www.sjgames.com/gurps/characterassistant/

Thanks to you the reader/user who was part of the why behind doing this.

Code by Jonathan Sourdough

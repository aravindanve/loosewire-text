# Loosewire Text

A single file python script to compile text wireframes for web projects, into 
self contained interactive html files. The loosewire text format supports 
screen urls, descriptions, data fields, form fields, action buttons, custom
action results, comments, notes and interactive screen linking.

## Single file distribution
Found in the `dist/` directory
### Requirements
* Python 3+

### Compile a .lwtx file
Copy `dist/lwtx.py` to your `bin` directory and don't forget to do `chmod +x lwtx.py`

    ./lwtx.py [filename]

## Building from source
### Requirements
* Python 3+
* rjsmin python module
* Node.js
* Lessc (npm less package)

### Build
From the project directory `./`, run:

    python3 build.py



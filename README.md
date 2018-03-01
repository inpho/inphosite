## Installation

The InPhO ("inphosite") server can be installed on a variety of computers and has been successfully installed under Linux and Mac OS. 
You should probably not tackle this installation process unless you are already familiar with installing code from a variety of sources. 
The instructions below are not complete and you may run into some unanticipated problems.  These instructions also presuppose that you
have a working connection to a sql server that will house the data being served.

### User

We recommend that you create a user specifically to host the server, and that you are installing the software while logged in as that user.

### Miniconda

Obtain the appropriate Miniconda installation package from 
* `https://repo.continuum.io/miniconda/Miniconda2-4.3.30-Linux-x86_64.sh` or 
* `https://repo.continuum.io/miniconda/Miniconda2-4.3.30-MacOSX-x86_64.sh`

Once downloaded run the script with bash.

### Python packages

*	`conda install -c alefnula mysql-python`
*	`pip install nltk`
*	`pip install sphinx`
*	`pip install docutils`

### Setup 

Download and run the setup.py script from https://github.com/inpho/inphosite/blob/master/setup.py with
```python setup.py develop```

### Configuration
You will need to install configuration (`.ini`) files, wherever you decide to locate these (e.g. `/var` in the instructions below):
* inpho.ini in `/var/inpho` based on https://github.com/inpho/inpho/blob/master/template.ini
* development.ini in `/var/inpho/inphosite` based on `https://github.com/inpho/inphosite/blob/master/template.ini`

## Running the Server
From the inphosite director run
```paster serve --reload development.ini```


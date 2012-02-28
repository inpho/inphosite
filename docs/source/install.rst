Developing inphosite
========================
The inphosite module contains all materials pertaining to the Indiana Philsophy
Ontology (InPhO) Project's online presence, including the API.

For work pretaining to dynamic ontology, we have started work on the `CodEx
(Coding Expertise) project <http://github.com/inpho/codex>`_. The scripts
directory of the inphosite project contains temporary code relating to dynamic
ontology construction, evaluation and maintainence tasks for the InPhO. We hope
to separate this code and the data model out from the web framework in the
upcoming months.

GitHub
--------
The inphosite code is hosted on GitHub at `http://github.com/inpho/inphosite`.
GitHub offers many collaborative tools, and makes independent work incredibly
easy to merge. For a summary of Git's advantages as a version control system,
see `Why Git is Better than X <http://whygitisbetterthanx.com/>`_.

Install inphosite
-------------------
To begin working with the inphosite code:

.. note::
    If you have not yet done so, please `Copy the Database`_ before begining!

1.  `Create a GitHub account <https://github.com/signup/free>`_

#.  Set up Git: 
    `Linux <http://help.github.com/linux-set-up-git/>`_, 
    `Mac OS X <http://help.github.com/mac-set-up-git/>`_,
    `Windows <http://help.github.com/win-set-up-git/>`_

#.  Fork the inphosite project, `using these instructions
    <http://help.github.com/fork-a-repo/>`_.

#.  Enter the git repository directory::

        cd inphosite

#.  A convenience script has been created which automates the install of the
    virtual environment, nltk, inphosite and creates a development.ini::

        ./setup.sh
    
    If this does not work see `Manual Installation`_ and return to these
    instructions.

#.  In development.ini:

    *   Modify the ``sqlalchemy.url`` directive to contain the proper username,
        password, and database name for your copy of the InPhO.
    *   Modify the ``host`` directive if you wish to enable external access. Be well
        aware that external access with the debugger enabled is a gargantuan
        security flaw if the paste server is started with root privileges.
    *   Modify the ``port`` directive to an open port on your machine. Otherwise
        you will receive an error on starting paster::

            socket.error: [Errno 48] Address already in use

#.  Activate the sandbox environment::

        source sandbox/bin/activate

#.  Use the ``websetup.py`` to finish initializing the database::

        paster setup-app development.ini

#.  You are now ready to go! You can start a paster server from the command::
    
        paster serve --reload development.ini

    Or interact with the environment directly using the paster shell::

        paster shell development.ini


Manual Installation
'''''''''''''''''''''

#.  Create a `Python virtual environment
    <http://pypi.python.org/pypi/virtualenv>`_::

        easy_install virtualenv
        virtualenv --no-site-packages sandbox

#.  Enter the sandbox environment::

        source sandbox/bin/activate

#.  Configure the project for development, which will also download the
    appropriate dependencies::

        python setup.py develop

#.  Setup the development.ini file by first copying over template.ini::
    
        cp template.ini development.ini


Copy the Database
'''''''''''''''''''
.. note::
    Currently the database is only open to internal InPhO development. In coming
    months we hope to eliminate this step, instead building the data set
    automatically. If you wish to have a copy of our database, let us know and
    we will send a link to a sanitized version of the db.

.. note::
    You will need to install `MySQL Community Server 5.1
    <http://dev.mysql.com/downloads/mysql/5.1.html>`_ before proceeding.

1.  ``ssh`` into ``inpho.cogs.indiana.edu`` and export the database::
    
        mysqldump seponto -u inpho -p > FILENAME

#.  ``scp`` the backup file to your personal machine::
        
        scp FILENAME user@host:~/sql/

#.  back on your personal machine, create the database inpho::
    
        mysql -u root -p    #You will be prompted for password
        mysql> CREATE DATABASE inpho;
        Query OK, 1 row affected (0.00 sec)
        mysql> USE inpho;
        Database changed
        mysql> exit
        Bye

#.  Restore the database::
    
        mysql --database inpho -u root -p < FILENAME

#.  Create new users for inpho database::

        mysql -u root -p    #You will be prompted for password
        mysql> CREATE USER 'inpho'@'localhost' IDENTIFIED BY 'password';
        mysql> GRANT ALL PRIVILEGES ON inpho.* TO 'inpho'@'localhost' 
            ->     WITH GRANT OPTION;
        mysql> CREATE USER 'inpho'@'%' IDENTIFIED BY 'password';
        mysql> GRANT ALL PRIVILEGES ON inpho.* TO 'inpho'@'%' 

    .. note::
        The second account is only necessary if you wish to allow database
        connections from other machines. Very important if you set your
        development.ini's ``host`` directive to ``0.0.0.0``!

Devlopment practices
----------------------
Bugs reports are stored on the `InPhOdev Trac
<http://inphodev.cogs.indiana.edu:8000>`_. Please coordinate through this
system. To request a non-anonymous account, please contact us at
`inpho@indiana.edu <mailto:inpho@indiana.edu>`_.

GitHub makes it incredibly easily to collaborate through the fork and pull
request model of devlopment. Each fork gives you a free sandbox to create your
own InPhO, and the pull requests foster quick and easy code review. 

After creating changes that you wish to submit to the inphosite project,
`submit a pull request <http://help.github.com/pull-requests/>`_.

Style Guidelines
''''''''''''''''''
Here are some general code guidelines for the InPhO. If you notice existing code
which does not follow these guidelines, feel free to patch.

*   `PEP 8: Style Guide for Python Code
    <http://www.python.org/dev/peps/pep-0008/>`_ -- When in doubt, default to
    this.
*   **Indentation**: 4 spaces. **No tabs.** Only way to maintain a consistent look,
    and is the Python standard practice.
*   **Docstrings**: Put them everywhere. Triple quote. Inline comments may start
    with ``#`` Default to `PEP 257: Docstring
    Conventions <http://www.python.org/dev/peps/pep-0257/>`_
*   **Line width**: Prefer to keep limited to 80 characters. Sometimes this
    doesn't make sense, but make use of automatic linewrapping in your text
    editor of choice. Use parens to group expressions and break after operators.
    See `PEP 8 <http://www.python.org/dev/peps/pep-0008/>`_ for details.
*   **Newline character**: Use Unix-style line returns, not Windows CRLF. We
    deploy to a Unix environment, and the core team deals in a Unix environment.
    Git has settings to `autocorrect line endings
    <http://help.github.com/dealing-with-lineendings/>`_.
*   **Capitalization**: Function names are NEVER to be capitalized. Use
    underscore_notation. Class names should be capitalized in PascalCase. Again,
    see `PEP 8 <http://www.python.org/dev/peps/pep-0008/>`_ for details.

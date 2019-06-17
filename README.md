# roboserver
Competition server used for RobotX, RoboBoat and more.

Setup instructions
------------------
This codebase is still using Python 2.7. An update to Python 3 is coming but it isn't yet ready.
To install all dependencies of this server and be ready to run it, all you have to do is
``` sh
python setup.py install
```
In case the line above fails because you don't have python installed, see: <https://docs.python-guide.org/starting/installation/>


Running Server
------------------
The server can easily be started by using either one of the commands below:
``` sh
python server.py
```

Running tests
------------------
A basic set of integration tests can be run by typing:
``` sh
python setup.py test
```  


Accessing logs
------------------
The web logs are now available through an integrated web server. To see the web log, visit [localhost:5000](http://localhost:5000)


How the code is structured
------------------
```
roboserver
│   setup.py: The python setuptools script that describes the projects, define dependencies, etc.
│   server.py: The main script for roboserver.
│
└───serv
│   │   buoy.py: The class connecting to a RobotX buoy for status.
│   │   pinger.py: The class connecting to the shared RoboBoat/RoboSub/RobotX pinger for status.
|   |   sevenseg.py: The class connecting to a RobotX buoy for status.
|   |   timeutil.py: A set of time-related utility functions.
```
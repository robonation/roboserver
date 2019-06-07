# roboserver
Competition server used for RobotX, RoboBoat and more.

Setup instructions
------------------
To install all dependencies of this server and be ready to run it, all you have to do is
    python setup.py install

In case the line above fails because you don't have python installed: <https://docs.python-guide.org/starting/installation/>

Running Server
------------------
The server can easily be started by using either one of the commands below:
    python server.py
    ./server.py

Running tests
------------------
A basic set of integration tests can be run by typing:
    python setup.py test
tests require the server to be running

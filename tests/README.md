To run the test suite, first, create and activate a virtual environment. Then
install some requirements and run the tests::

cd tests
sudo apt-get install virtualenv python3 libyajl-dev
virtualenv -p $(which python3) ~/ve/tinman-tests
source ~/ve/tinman-tests/bin/activate
pip install pipenv
pipenv install
pip install ..
./runtests.py


# create venv
python3 -m venv venv

# activate venv
source venv/bin/activate

# install dependencies
pip3 install -r requirements.txt

# install anthropic
git clone https://github.com/anthropics/anthropic-sdk-python.git
cd anthropic-sdk-python
pip3 install .
cd ..
rm -rf anthropic-sdk-python

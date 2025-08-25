conda create -n ptmchat python=3.12.3 -y
conda activate ptmchat

conda install pip
# Flask API + requests (to call Ollama)
pip install flask requests

# Database utils
pip install psycopg2-binary sqlalchemy
conda install pandas

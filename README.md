# sqlalchemy_db2_bug
Help duplicate sqlalchemy with db2 ibm_db_sa bug

First install docker server and python docker client

Docker engine from here https://www.docker.com
Next install python docker client, https://github.com/docker/docker-py
pip install docker

Install ibm_db python driver https://github.com/ibmdb/python-ibmdb#downloads
pip install ibm_db

May be you have to do also
pip install ibm_db_sa

The next step 
python docker_prepare_db2.py
This will download the db2 docker image, run db2 and create sample database

Next run the code to see the sqlalchemy or db2 bug, this will connect to db2 using 
locahost port 50001, db2user db2inst1 and db2password db2inst1

python db2_test_sa.py

I tested this under python 2.7



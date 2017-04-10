import sqlalchemy
import string
from sqlalchemy import *
import ibm_db_sa
import ibm_db
import ibm_db_dbi
from ibm_db_dbi import OperationalError
import os
from sqlalchemy.schema import CreateTable
import logging
import logging.handlers

format_hdlr = "%(asctime)s %(levelname)s:%(lineno)-3s - %(funcName)-20s %(message)-40s "
hdlr = logging.handlers.RotatingFileHandler('db2_test_sa.log',maxBytes=1000000, backupCount = 2)
hdlr1 =  logging.StreamHandler()
log_formatter = logging.Formatter(format_hdlr)
hdlr.setFormatter(log_formatter)
hdlr1.setFormatter(log_formatter)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(hdlr)
log.addHandler(hdlr1)


def ibm_db_sa_DDL_test():
  try:
    user     = os.environ['DB2_USER']
    password = os.environ['DB2_PASSWORD_']
  except Exception:
    user     = "db2inst1"
    password = "db2inst1"
  
  conn_str = string.Template('db2+ibm_db://$user:$password@localhost:50001/Sample?PROTOCOL=TCPIP').substitute(
                            user = user,
                            password = password)
  db2 = sqlalchemy.create_engine(conn_str,convert_unicode=True,encoding='utf-8', echo=False) #echo=True
  metadata = MetaData()
  log.info ("sqlalchemy.create_engine %s" % db2)
 
  try:
    metadata.reflect(bind=db2)
  except sqlalchemy.exc.SQLAlchemyError as e:
    log.error("SQLAlchemyError %s" % e)
    
    return

  for t in metadata.sorted_tables:
     log.info ("CreateTable %s %s" % (t.name, CreateTable(t).compile(db2)))


def mymain():
   ibm_db_sa_DDL_test()

if __name__ == "__main__":
   mymain()


# log.py
__version__ = "v20200208"
import os
import logging
from datetime import datetime
license = "20200401"


def logInit(fileName,  logFolder="logs/"):
    global logger
    logger = log(fileName, logFolder)


def log(fileName, logFolder):
    try:
        # Creates the Directory for Output
        if not os.path.exists(logFolder):
            os.makedirs(logFolder)
    except OSError:
        print("Creation of the log directory failed")
    now = datetime.now()
    current_time = now.strftime("%Y%m%d%H%M%S")
    # Create and configure logger
    logging.basicConfig(filename=logFolder+fileName + "_"+current_time+".log",
                        format='%(asctime)s %(message)s',
                        filemode='w')
    # Creating an object
    logger = logging.getLogger()
    # Setting the threshold of logger to DEBUG
    logger.setLevel(logging.DEBUG)
    return logger


def Print(obj0, obj1="", obj2=""):
    print(obj0, obj1, obj2)
    logger.debug("".join([str(obj0), str(obj1), str(obj2)]))


def Input(obj):
    logger.debug(str(obj))
    IN = input(obj)
    logger.debug(str(IN))
    return IN

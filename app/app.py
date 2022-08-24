import logging
import os
from dotenv import load_dotenv
from database_scheduler import DatabaseScheduler
from log_formatter import log_setup
import time
import test

pemeg = """

\x1b[94;20m██████╗ ███████╗███╗   ███╗███████╗ ██████╗ 
\x1b[94;20m██╔══██╗██╔════╝████╗ ████║██╔════╝██╔════╝ 
\x1b[94;20m██████╔╝█████╗  ██╔████╔██║█████╗  ██║  ███╗
\x1b[94;20m██╔═══╝ ██╔══╝  ██║╚██╔╝██║██╔══╝  ██║   ██║
\x1b[94;20m██║     ███████╗██║ ╚═╝ ██║███████╗╚██████╔╝
\x1b[94;20m╚═╝     ╚══════╝╚═╝     ╚═╝╚══════╝ ╚═════╝ 
                                            
"""


if __name__ == "__main__":
    print(pemeg)
    load_dotenv("../.env")
    log_setup()
    log = logging.getLogger()
    if os.getenv("RUN_TESTS_ON_STARTUP", 1) == '1':
        log.info("Running tests...")
        test_status = os.system("python -m unittest -v")
        if test_status != 0:
            log.critical("Tests failed. Stopping application...")
            # app termination if test fails
            quit(1)
    log.info("Tests completed. Status: OK. Running application...")
    database_scheduler = DatabaseScheduler()
    database_scheduler.start()
    while True:
        time.sleep(.5)

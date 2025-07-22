import logging

configured_flag = False

def setup_logging(file_name: str):
    ''' Configure the logging facility, only once '''
    global configured_flag
    if not configured_flag:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            filename=file_name
        )
        configured_flag = True
import time
from config import *
from parser import RelyhomeParser


def main():
    start = time.time()
    rely_parser = RelyhomeParser()
    try:
        rely_parser.parse()
        end = time.time()
        log.info(f'Time spent: {round(end - start)} s, ')
    except Exception as ex:
        log.error(ex)


if __name__ == "__main__":
    main()

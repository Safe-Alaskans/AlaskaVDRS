import os

import logging
from logging.handlers import RotatingFileHandler

if os.getcwd().endswith('local_extraction'):
    from extraction_tools import convert_folder, txt_validator, prep_data
else:
    from local_extraction.extraction_tools import (convert_folder,
                                                   txt_validator, prep_data)


logger = logging.getLogger(__name__)


def main():
    os.makedirs('output', exist_ok=True)

    logging.basicConfig(
        handlers=[RotatingFileHandler('output/logs.log', maxBytes=2097152,
                                      backupCount=20, encoding='utf-8')],
        level=logging.INFO, format='[%(asctime)s] %(levelname)s %(message)s')

    logger.info('Script started (master_script)')

    while True:
        proceed_with_step = input('Convert, validate or prepare? '
                                  '("1", "2" or "3", "q" to quit): ').strip()
        if proceed_with_step == '1':
            print('Pick a folder to convert:')
            convert_folder.main()
        elif proceed_with_step == '2':
            print('Pick a folder to validate:')
            txt_validator.main()
        elif proceed_with_step == '3':
            print('Pick a folder to prepare:')
            prep_data.main()
        elif proceed_with_step == 'q':
            break
        else:
            print('Invalid input, must be one of the options '
                  '("1", "2", "3" or "q"), try again or quit using Ctrl+C')

    logger.info('Script finished (master_script)')


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception('Exception')

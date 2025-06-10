"""Validate TXT results by checking percentage of common words.
"""

import os

import logging
from logging.handlers import RotatingFileHandler

if os.getcwd().endswith('extraction_tools'):
    from convert_folder import print_prog_bar
elif os.getcwd().endswith('local_extraction'):
    from extraction_tools.convert_folder import print_prog_bar
else:
    from local_extraction.extraction_tools.convert_folder import print_prog_bar


logger = logging.getLogger(__name__)


def main():
    os.makedirs('output', exist_ok=True)

    logging.basicConfig(
        handlers=[RotatingFileHandler('output/logs.log', maxBytes=2097152,
                                      backupCount=20, encoding='utf-8')],
        level=logging.INFO, format='[%(asctime)s] %(levelname)s %(message)s')

    logger.info('Script started (txt_validator)')

    process_path = input('Path (example: "source_files/tutorials"): ')

    common_path_prefix = ''
    if os.getcwd().endswith('extraction_tools'):
        common_path_prefix = '../'
    elif os.getcwd().endswith('data2llmBeta2'):
        common_path_prefix = 'local_extraction/'
    with open(f'{common_path_prefix}common.txt', 'r') as c:
        common_words = [cw_item.lower().strip() for cw_item in c.readlines()]

    files_dict = dict()
    for files_tuple in os.walk(process_path):
        for process_file in files_tuple[2]:
            files_progress = [files_tuple[2].index(process_file),
                              len(files_tuple[2]), f'files ({files_tuple[0]})']
            if process_file.endswith('.txt'):
                logger.info(f'Processing {process_file}..')

                file_path = f'{files_tuple[0]}/{process_file}'

                with open(file_path, 'r') as check_file:
                    result_words = [''.join(
                        [i_char for i_char in f_word.lower().strip()
                         if i_char.isalpha()]) for f_word
                        in ' '.join(check_file.read().split('\n')).split(' ')
                        if f_word.strip()]

                common_found = 0
                for r_word in result_words:
                    if r_word in common_words:
                        common_found += 1

                if len(result_words) > 0:
                    common_percentage = round(
                        common_found / len(result_words) * 100)
                else:
                    common_percentage = 0

                if common_percentage <= 25:
                    files_dict[file_path] = common_percentage

                logger.info(f'Processed {process_file}')

            print_prog_bar(files_progress)

    common_sorted = sorted(
        files_dict.items(), reverse=True, key=lambda f: f[1])

    if not common_sorted:
        print('All files appear OK (no files with too little common words)')
    else:
        print('Files with too little common words:')
        for doc_check in common_sorted:
            print(f'{doc_check[1]}% - "{doc_check[0]}"')

    logger.info('Script finished (txt_validator)')


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception('Exception')

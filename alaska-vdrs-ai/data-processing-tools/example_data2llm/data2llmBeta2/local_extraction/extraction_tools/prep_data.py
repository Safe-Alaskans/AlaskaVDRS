"""Convert source files with the "convert_folder" script.
Use this script to extract the data and generate JSON and TXT files.

Download the English stopwords from nltk:
import nltk
nltk.download('stopwords')
"""

import os
import json
from datetime import datetime, timezone

import pdfplumber
from nltk.corpus import stopwords

import logging
from logging.handlers import RotatingFileHandler

if os.getcwd().endswith('extraction_tools'):
    from convert_folder import validate_input, print_prog_bar
elif os.getcwd().endswith('local_extraction'):
    from extraction_tools.convert_folder import validate_input, print_prog_bar
else:
    from local_extraction.extraction_tools.convert_folder import (
        validate_input, print_prog_bar)


logger = logging.getLogger(__name__)


def stopwords_gen():
    """Return a list of stopwords to filter out"""
    stopwords_list = [''.join([sw_letter for sw_letter in s_word
                               if sw_letter.isalpha()])
                      for s_word in stopwords.words('english')]

    common_path_prefix = ''
    if os.getcwd().endswith('extraction_tools'):
        common_path_prefix = '../'
    elif os.getcwd().endswith('data2llmBeta2'):
        common_path_prefix = 'local_extraction/'
    with open(f'{common_path_prefix}common.txt', 'r') as cw:
        common_words = cw.read()

    stopwords_list.extend([''.join([cw_letter for cw_letter in cw_word
                                    if cw_letter.isalpha()]).lower()
                           for cw_word in common_words.split('\n')])
    stopwords_list.extend(['', 'blank'])

    return stopwords_list


def to_process_gen(process_path):
    """Return a dictionary of files to process, organized by path"""
    to_process = dict()
    for files_tuple in os.walk(process_path):
        for process_file in files_tuple[2]:
            if process_file.endswith('.txt'):
                if files_tuple[0] not in to_process.keys():
                    to_process[files_tuple[0]] = [process_file]
                else:
                    files_list = to_process[files_tuple[0]]
                    files_list.append(process_file)
                    to_process[files_tuple[0]] = files_list

    return to_process


def keywords_gen(src_rows_list, stopwords_list):
    """Return top ten most frequent words, excluding stopwords"""
    doc_words = []
    for doc_word in ' '.join(src_rows_list).split(' '):
        doc_words.append(''.join([word_letter for word_letter in doc_word
                                  if word_letter.isalnum()]))

    # generate word occurrences dictionary
    count_dict = dict()
    for word_count in doc_words:
        wc_lower = word_count.lower()

        if wc_lower not in count_dict.keys():
            count_dict[wc_lower] = dict()

        if not count_dict[wc_lower].get('occurrences'):
            count_dict[wc_lower]['occurrences'] = [
                word_check.lower() for word_check in doc_words].count(wc_lower)

        if 'variants' not in count_dict[wc_lower].keys():
            count_dict[wc_lower]['variants'] = [word_count]
        else:
            variants_list = count_dict[wc_lower]['variants']

            if word_count not in variants_list:
                variants_list.append(word_count)

            count_dict[wc_lower]['variants'] = variants_list

    # return ten keywords
    return [v['variants'][0]
            for k, v in sorted(count_dict.items(), reverse=True,
                               key=lambda c: c[1]['occurrences'])
            if k not in stopwords_list and not k.isnumeric()
            and len(k) > 1][:10]


def process_src_file(src_dict, stopwords_list, use_chunking):
    """Create JSON and TXT of file contents"""
    result_folder = f'{"-".join(src_dict["path"].split("/"))}'
    file_process = src_dict['file_name']

    logger.info(f'Processing "{file_process}"..')

    doc_dict = {file_process: dict()}

    # get metadata
    try:
        with pdfplumber.open(
                f'{src_dict["path"]}/{file_process}.pdf') as pdf_src:
            metadata_dict = pdf_src.metadata
            metadata_dict['pdf_pages_count'] = len(pdf_src.pages)
    except FileNotFoundError:
        logger.warning(f'No PDF for "{file_process}", no metadata')

        metadata_dict = dict()

    metadata_json = {
        'title': metadata_dict.get('Title'),
        'author': metadata_dict.get('Author'),
        'created_at': metadata_dict.get('CreationDate'),
        'modified_at': metadata_dict.get('ModDate'),
        'pages_count': metadata_dict.get('pdf_pages_count'),
        'processed_utc': datetime.now(timezone.utc).isoformat()
    }

    with open(f'{src_dict["path"]}/{file_process}.txt', 'r') as doc_txt:
        doc_read = '\n\n'.join([dt_row for dt_row
                                in doc_txt.read().split('\n\n') if dt_row])
        doc_text_rows = doc_read.split('\n')

    # split text into chunks of at least [base_chunk] tokens
    logger.info('Splitting into chunks..')

    d_chunk = []
    chunk_size = 0
    base_chunk = 4450
    doc_chunks = []
    for doc_row in doc_text_rows:
        row_tokens_float = len(doc_row.split(' ')) * 1.4

        row_tokens = int(row_tokens_float)
        if row_tokens_float % 1:
            row_tokens += 1

        d_chunk.append(doc_row)
        chunk_size += row_tokens

        if (chunk_size >= base_chunk and doc_row.strip().endswith('.')) \
                or chunk_size >= round(base_chunk * 1.1):
            doc_chunks.append(d_chunk)
            d_chunk = []
            chunk_size = 0

    # append the rest
    doc_chunks.append(d_chunk)

    # if chunking is not used, doc_chunks will consist of one large chunk
    if not use_chunking:
        logger.info('Merging chunks and generating keywords..')

        keywords_dict = dict()
        merged_chunks = []
        for chunk_add in doc_chunks:
            kw_chunk = keywords_gen(chunk_add, stopwords_list)
            keywords_list = [[kwc, len(kw_chunk) - kw_chunk.index(kwc)]
                             for kwc in kw_chunk]

            for kw_list_item in keywords_list:
                if kw_list_item[0] not in keywords_dict.keys():
                    keywords_dict[kw_list_item[0]] = kw_list_item[1]
                else:
                    kw_count = keywords_dict[kw_list_item[0]]
                    kw_count += kw_list_item[1]
                    keywords_dict[kw_list_item[0]] = kw_count

            merged_chunks.extend(chunk_add)

        keywords_lines = []
        for k, v in keywords_dict.items():
            keywords_lines.extend([k for k_item in range(v)])

        merged_keywords = keywords_gen(keywords_lines, stopwords_list)
        doc_chunks = [merged_chunks]

    for chunk_w in doc_chunks:
        logger.info(f'Processing chunk {doc_chunks.index(chunk_w) + 1}/'
                    f'{len(doc_chunks)}..')

        if use_chunking:
            metadata_json['keywords'] = keywords_gen(chunk_w, stopwords_list)
        else:
            metadata_json['keywords'] = merged_keywords

        doc_dict[file_process]['metadata'] = metadata_json

        file_postfix = ''
        if len(doc_chunks) > 1:
            file_postfix = f'_chunk_{doc_chunks.index(chunk_w) + 1}'

        doc_dict[file_process]['text'] = '\n'.join(chunk_w).strip()

        # write dict to JSON and raw text to TXT
        with open(f'output/{result_folder}/results_json/'
                  f'{file_process}{file_postfix}.json', 'w') as rj:
            rj.write(json.dumps(doc_dict, indent=4))

        with open(f'output/{result_folder}/results_txt/'
                  f'{file_process}{file_postfix}.txt', 'w') as rt:
            rt.write(doc_dict[file_process]['text'])


def main():
    os.makedirs('output', exist_ok=True)

    logging.basicConfig(
        handlers=[RotatingFileHandler('output/logs.log', maxBytes=2097152,
                                      backupCount=20, encoding='utf-8')],
        level=logging.INFO, format='[%(asctime)s] %(levelname)s %(message)s')

    logger.info('Script started (prep_data)')

    process_path = input('Path (example: "source_files/tutorials"): ')

    use_chunking = validate_input('Use chunking? (y/n): ', ['y', 'n'])
    if use_chunking == 'y':
        use_chunking = True
    else:
        use_chunking = False

    stopwords_list = stopwords_gen()

    logger.info('Processing TXTs..')

    to_process = to_process_gen(process_path)

    for tp_path in to_process.keys():
        tp_folder = f'{"-".join(tp_path.split("/"))}'

        os.makedirs(f'output/{tp_folder}/results_json', exist_ok=True)
        os.makedirs(f'output/{tp_folder}/results_txt', exist_ok=True)

    tp_keys_list = list(to_process.keys())
    for files_path, path_files in to_process.items():
        folders_progress = [tp_keys_list.index(files_path), len(tp_keys_list),
                            'folders']
        for src_file in path_files:
            files_progress = [path_files.index(src_file), len(path_files),
                              'files']
            process_src_file({'path': files_path,
                              'file_name': src_file.removesuffix('.txt')},
                             stopwords_list, use_chunking)

            print_prog_bar(files_progress, folders_progress)

    logger.info('Script finished (prep_data)')


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception('Exception')

"""Convert a folder of source files for further processing.
Options:
1) Selenium (Firefox, tested on version 116.0.3);
Supported extensions: [PDF] (reqs: Firefox and geckodriver)
2) pdfplumber (similar to pdftotext but has trouble with scanned books);
Supported extensions: [PDF]
3) pdftotext + ebook-convert.
Supported extensions: [PDF, EPUB, MOBI] (reqs: poppler-utils and calibre)
(i) ebook-convert can be used with PDFs, but loses formatting, ebooks only
(i) ignore non-critical errors thrown by the converter libraries
"""

import os
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pdfplumber

import logging
from logging.handlers import RotatingFileHandler


logger = logging.getLogger(__name__)


def processed_gen(process_path):
    """Return a list of processed files for skipping"""
    processed = [find_file.removesuffix('.txt') for find_file
                 in sum([found_files[2] for found_files
                         in os.walk(process_path)], [])
                 if find_file.endswith('.txt')]

    return processed


def print_prog_bar(*args):
    bars_data = []
    for bar_input in args:
        bar_fill = round((bar_input[0] + 1) / bar_input[1] * 10)
        bar_empty = 10 - bar_fill
        bar_progress = f'{bar_input[0] + 1}/{bar_input[1]}'

        bars_data.append({'bar_fill': bar_fill, 'bar_empty': bar_empty,
                          'bar_progress': bar_progress, 'label': bar_input[2]})

    print_end = ''
    if len(bars_data) > 1:
        print_end = f'\033[{len(bars_data) - 1}A'

    print('\n'.join(
        [f'  |{"".join(["█" for prog_fill in range(bd_item["bar_fill"])])}'
         f'{"".join([" " for prog_empty in range(bd_item["bar_empty"])])}| '
         f'{bd_item["bar_progress"]} {bd_item["label"]}'
         for bd_item in bars_data]), end=f'{print_end}\r')

    if sum([abs(done_arg[0] - done_arg[1]) for done_arg in args]) == len(args):
        print(''.join(['\n' for newline in range(len(args))]))


def pdfplumber_extract(file_path):
    with pdfplumber.open(file_path) as pdf_file:
        raw_text = '\n'.join([p_page.extract_text(
            layout=True, x_density=4.5).strip() for p_page in pdf_file.pages])

    # trim left margin
    left_spaces = [len(line_ls) - len(line_ls.lstrip())
                   for line_ls in raw_text.split('\n')]
    strip_spaces = sorted(
        {set_item: left_spaces.count(set_item)
         for set_item in set(left_spaces)}.items(),
        reverse=True, key=lambda s: s[1])[0][0]

    processed_lines = []
    add_line_break = True
    for text_line in raw_text.split('\n'):
        trimmed_spaces = 0
        line_processed = False
        for line_char in text_line:
            if line_char == ' ' and trimmed_spaces <= strip_spaces \
                    and not line_processed:
                text_line = text_line[1:]
                trimmed_spaces += 1
            else:
                line_processed = True

        if text_line.strip():
            processed_lines.append(text_line)
            add_line_break = True
        elif add_line_break:
            processed_lines.append(text_line)
            add_line_break = False

    return processed_lines


def get_style_val(style_string, split_before, split_after):
    return float(style_string.split(split_before)[1].split(split_after)[0])


def update_raw_dict(proc_elem, elem_index, raw_dict, page_num):
    try:
        offset_top = get_style_val(
            proc_elem['style'], 'top: calc(var(--scale-factor)*', 'px')
        offset_left = get_style_val(
            proc_elem['style'], 'left: calc(var(--scale-factor)*', 'px')
        offset_unit = 'pixel'
    except IndexError:
        offset_top = get_style_val(proc_elem['style'], '; top: ', '%;')
        offset_left = get_style_val(proc_elem['style'], 'left: ', '%;')
        offset_unit = 'percent'

    # separate in case offset is in percent but scale is present
    try:
        scale = int(get_style_val(
            proc_elem['style'], 'transform: scaleX(', ')') * 100)
    except IndexError:
        scale = 0

    if page_num not in raw_dict.keys():
        raw_dict[page_num] = [{'coords': [offset_top, offset_left],
                               'coords_unit': offset_unit,
                               'text': proc_elem.text, 'scale': scale,
                               'position': elem_index}]
    else:
        text_get = raw_dict[page_num]
        text_get.append({'coords': [offset_top, offset_left],
                         'coords_unit': offset_unit,
                         'text': proc_elem.text, 'scale': scale,
                         'position': elem_index})
        raw_dict[page_num] = text_get


def set_page_scale(driver):
    driver.find_element(By.CSS_SELECTOR, 'select#scaleSelect').click()
    driver.find_element(By.CSS_SELECTOR, 'option#pageFitOption').click()


def selenium_extract(driver, file_path, result_format, files_progress):
    driver.get(f'file://{os.path.abspath(file_path)}')
    sleep(5)

    set_page_scale(driver)

    page_height = 0
    raw_dict = dict()
    pages_range = range(int(driver.find_element(
        By.CSS_SELECTOR, 'input#pageNumber').get_attribute('max')))
    for page_click in pages_range:
        page_num = page_click + 1

        logger.info(f'Processing page {page_num}')

        page_selector = f'div.page[data-page-number="{page_num}"]'

        prev_page_height = page_height
        page_height = get_style_val(
            driver.find_element(
                By.CSS_SELECTOR, page_selector).get_attribute('style'),
            'height: calc(var(--scale-factor) * ', 'px);')
        if prev_page_height == 0:
            prev_page_height = page_height

        page_height_changed = abs(page_height - prev_page_height) > 4

        if page_height_changed:
            set_page_scale(driver)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.textLayer')))
        sleep(1)

        pg_data = BeautifulSoup(driver.page_source, 'html.parser').select(
            page_selector)[0]

        # filter repeating and incomplete text boxes
        mc_elems = pg_data.select('span.markedContent')
        if mc_elems:
            for filter_item in mc_elems:
                if filter_item.has_attr('id') and filter_item.text:
                    mc_all = pg_data.find_all('span', id=filter_item['id'])
                    if len(mc_all) == 2:
                        mc_all[0].decompose()

        select_content = pg_data.select('span')
        for proc_elem in select_content:
            elem_index = select_content.index(proc_elem)
            if proc_elem.has_attr('style'):
                update_raw_dict(proc_elem, elem_index, raw_dict, page_num)

        print_prog_bar([page_click, len(pages_range), 'pages'], files_progress)

        next_button = driver.find_element(By.CSS_SELECTOR, 'button#next')
        if not next_button.get_attribute('disabled'):
            next_button.click()

    lines_all = []
    if result_format == '1':
        # attempt to preserve page formatting
        for rd_page in raw_dict.values():
            for rd_line in rd_page:
                line_index = rd_page.index(rd_line)
                if line_index > 0:
                    if rd_line['coords'][0] != \
                            rd_page[line_index - 1]['coords'][0]:
                        rd_line['text'] = '\n' + rd_line['text']

                lines_all.append(rd_line['text'])
    elif result_format == '2':
        # page text in one line (may be parsed better by the model)
        for rd_page in raw_dict.values():
            words_line = []
            for words in rd_page:
                words_line.append(words['text'])

            la_append = ' '.join(
                w_line for w_line in words_line if w_line.strip())
            if lines_all:
                la_append = '\n' + la_append

            lines_all.append(la_append)

    return lines_all


def validate_input(input_msg, options_list):
    while True:
        choice_input = input(input_msg).strip()
        if choice_input in options_list:
            break
        else:
            print(f'Invalid input, must be one of the options '
                  f'{options_list}, try again or quit using Ctrl+C')

    return choice_input


def main():
    os.makedirs('output', exist_ok=True)

    logging.basicConfig(
        handlers=[RotatingFileHandler('output/logs.log', maxBytes=2097152,
                                      backupCount=20, encoding='utf-8')],
        level=logging.INFO, format='[%(asctime)s] %(levelname)s %(message)s')

    logger.info('Script started (convert_folder)')

    process_path = input('Path (example: "source_files/tutorials"): ')

    convert_options = {'1': 'Selenium', '2': 'pdfplumber',
                       '3': 'pdftotext + ebook-convert'}
    convert_with = validate_input(
        'Selenium, pdfplumber or utilities ("1", "2", "3"): ', ['1', '2', '3'])

    logger.info(
        f'Converting into TXT (using {convert_options.get(convert_with)})..')

    if convert_with == '1':
        result_format = validate_input(
            'Attempt to preserve page formatting '
            '("1") or each page in one line '
            '("2", may be parsed better by the model)?: ', ['1', '2'])

        # commented out for now, some files may end up empty or incomplete
        # possibly a memory or cache issue, restarting as a temporary solution
        # maybe clear Firefox memory between files
        # make sure only the selenium instance is affected
        """# init browser if using Selenium
        logger.info('Initializing browser..')

        # headless mode, comment out regular driver if using it
        '''driver_options = webdriver.FirefoxOptions()
        driver_options.add_argument('-headless')
        driver = webdriver.Firefox(options=driver_options)'''
        driver = webdriver.Firefox()"""

    processed = processed_gen(process_path)

    print('Processing files, check output/logs.log for more progress info..')

    for files_tuple in os.walk(process_path):
        for process_file in files_tuple[2]:
            logger.info(f'Processing "{process_file}"..')

            files_progress = [files_tuple[2].index(process_file),
                              len(files_tuple[2]), f'files ({files_tuple[0]})']

            file_path = f'{files_tuple[0]}/{process_file}'
            name_ext = os.path.splitext(process_file)

            if name_ext[0] not in processed:
                if convert_with == '1' and name_ext[1] == '.pdf':
                    # separate instance for each file
                    driver_options = webdriver.FirefoxOptions()
                    driver_options.add_argument('-headless')
                    driver = webdriver.Firefox(options=driver_options)

                    try:
                        selenium_extracted = selenium_extract(
                            driver, file_path, result_format, files_progress)
                    except Exception:
                        driver.quit()

                        raise Exception('Error with selenium_extract')

                    with open(f'{files_tuple[0]}/{name_ext[0]}.txt',
                              'w') as selenium_write:
                        selenium_write.write(''.join(selenium_extracted))

                    # quit if initialized for each file
                    driver.quit()

                elif convert_with == '2' and name_ext[1] == '.pdf':
                    pdfplumber_extracted = pdfplumber_extract(file_path)
                    with open(f'{files_tuple[0]}/{name_ext[0]}.txt',
                              'w') as plumber_write:
                        plumber_write.write('\n'.join(pdfplumber_extracted))

                    print_prog_bar(files_progress)

                elif convert_with == '3' \
                        and name_ext[1] in ['.pdf', '.epub', '.mobi']:
                    if process_file.endswith('.pdf'):
                        os.system(f'cd "{files_tuple[0]}" && '
                                  f'pdftotext -layout "{process_file}"')
                    elif name_ext[1] in ['.epub', '.mobi']:
                        os.system(f'cd "{files_tuple[0]}" && '
                                  f'ebook-convert "{process_file}" '
                                  f'"{name_ext[0]}.txt"')

                        with open(f'{files_tuple[0]}/{name_ext[0]}.txt',
                                  'r+') as t:
                            txt_contents = '\n'.join(
                                [t_row for t_row in t.read().split('\n')
                                 if t_row])
                            t.seek(0)
                            t.write(txt_contents)
                            t.truncate()

                    print_prog_bar(files_progress)
                else:
                    logger.info(
                        f'Skipped "{file_path}" (extension not supported)')
            else:
                logger.info(f'Skipped "{file_path}" (processed already)')

            logger.info(f'Processed "{process_file}"')

    # quit if initialized before processing the files
    '''if convert_with == '1':
        driver.quit()'''

    logger.info('Script finished (convert_folder)')


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception('Exception')

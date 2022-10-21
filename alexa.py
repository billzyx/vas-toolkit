from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from seleniumwire import webdriver
from argparse import ArgumentParser
from time import sleep
import os
import logging
from datetime import datetime
from datetime import timedelta
import gzip
from file_saver import FileSaver
import yaml

# pip3 install selenium-wire==3.0.2

logger = None


def init_logging(save_dir_path):
    logger_init = logging.getLogger("alexa")
    formatter = logging.Formatter("%(asctime)s;%(levelname)s    %(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    file_handler = logging.FileHandler(filename=os.path.join(save_dir_path, 'alexa.log'))
    file_handler.setFormatter(formatter)
    logger_init.addHandler(file_handler)
    logger_init.addHandler(stream_handler)
    logger_init.setLevel(logging.DEBUG)
    return logger_init


def init_driver(profile):
    logger.info("Starting chromedriver")
    chrome_options = Options()
    # use local data directory
    # headless mode can't be enabled since then amazon shows captcha
    work_dir_path = os.getcwd()
    chrome_options.add_argument("user-data-dir={}".format(os.path.join(work_dir_path, "profiles", profile)))
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--remote-debugging-port=4444')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_argument("--disable-web-security")

    options = {
        'suppress_connection_errors': True,  # Show full tracebacks for any connection errors
        # 'backend': 'mitmproxy'  # Use the mitmproxy backend (see limitations above)
        'connection_timeout': 100
    }
    driver = webdriver.Chrome(
        executable_path=ChromeDriverManager().install(),
        options=chrome_options, service_log_path='NUL', seleniumwire_options=options)

    driver.implicitly_wait(10)
    return driver


def amazon_login(driver, account, password, date_from=None, date_to=None, device=None):
    driver.implicitly_wait(120)
    logger.info("GET https://alexa.amazon.com/spa/index.html")
    # get main page
    driver.get('https://alexa.amazon.com/spa/index.html')
    sleep(4)
    url = driver.current_url
    # if amazon asks for signin, it will redirect to a page with signin in url
    if 'signin' in url:
        logger.info("Got login page: logging in...")
        # find email field
        # WebDriverWait waits until elements appear on the page
        # so it prevents script from failing in case page is still being loaded
        # Also if script fails to find the elements (which should not happen
        # but happens if your internet connection fails)
        # it is possible to catch TimeOutError and loop the script, so it will
        # repeat.
        check_field = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, 'ap_email')))
        email_field = driver.find_element_by_id('ap_email')
        email_field.clear()
        # type email
        email_field.send_keys(account)
        check_field = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, 'ap_password')))
        # find password field
        password_field = driver.find_element_by_id('ap_password')
        password_field.clear()
        # type password
        password_field.send_keys(password)
        # find submit button, submit
        check_field = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, 'signInSubmit')))
        submit = driver.find_element_by_id('signInSubmit')
        submit.click()
    # get history page
    driver.get('https://www.amazon.com/alexa-privacy/apd/rvh')
    sleep(4)
    # amazon can give second auth page, so repeat the same as above
    if 'signin' in driver.current_url:
        logger.info("Got confirmation login page: logging in...")
        try:
            driver.implicitly_wait(2)
            check_field = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, 'ap_email')))
            email_field = driver.find_element_by_id('ap_email')
            email_field.clear()
            email_field.send_keys(account)
            check_field = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, 'continue')))
            submit = driver.find_element_by_id('continue')
            submit.click()
            sleep(1)
        except:
            pass
        check_field = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, 'ap_password')))
        password_field = driver.find_element_by_id('ap_password')
        password_field.clear()
        password_field.send_keys(password)
        check_field = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, 'signInSubmit')))
        submit = driver.find_element_by_id('signInSubmit')
        submit.click()
        sleep(3)
    driver.implicitly_wait(120)
    logger.info("GET https://www.amazon.com/alexa-privacy/apd/rvh")
    # get history page again
    driver.get('https://www.amazon.com/alexa-privacy/apd/rvh')
    # find selector which allows to select Date Range
    check = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(
            (By.CLASS_NAME, "selected-filter")))
    logger.info("Selecting Date ...")
    history = driver.find_elements_by_class_name('selected-filter')
    history[0].click()
    check = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(
            (By.CLASS_NAME, "selected-filter")))
    history = driver.find_elements_by_class_name('selected-filter')
    history[1].click()
    # click 'All History'
    all_hist = driver.find_elements_by_class_name('filter-by-date-option')

    if date_from and date_to:
        def select_date(date_to_select):
            year_link = driver.find_elements_by_class_name('react-datepicker__year-select')
            for option in year_link[0].find_elements_by_tag_name('option'):
                if option.text == date_to_select.split('/')[2]:
                    option.click()
                    break
            month_link = driver.find_elements_by_class_name('react-datepicker__month-select')
            for option in month_link[0].find_elements_by_tag_name('option'):
                if option.get_attribute('value') == str(int(date_to_select.split('/')[0]) - 1):
                    option.click()
                    break
            number = int(date_to_select.split('/')[1])
            number = '{:03d}'.format(number)
            number_link = driver.find_elements_by_class_name('react-datepicker__day--' + number)
            if len(number_link) > 1 and int(date_to_select.split('/')[1]) > 15:
                number_link[1].click()
            else:
                number_link[0].click()

        custom_link = driver.find_element_by_id('custom-date-range-filter')
        custom_link.click()
        from_d = driver.find_element_by_id('date-start')
        from_d.click()
        select_date(date_from)

        sleep(2)
        to_d = driver.find_element_by_id('date-end')
        to_d.click()
        select_date(date_to)
        # subm = driver.find_element_by_id('submit')
        # subm.click()
    else:
        for link in all_hist:
            if 'All' in link.text:
                link.click()
    sleep(2)
    if device:
        logger.info("Selecting Device ...")
        # Expand device option menu
        device_menu = driver.find_elements_by_class_name('filter-by-device-menu')
        assert len(device_menu) == 1
        device_menu_selected_filter = device_menu[0].find_elements_by_class_name('selected-filter')
        assert len(device_menu_selected_filter) == 1
        device_menu_selected_filter[0].click()

        # Re-find device option menu after expansion
        device_menu = driver.find_elements_by_class_name('filter-by-device-menu')
        assert len(device_menu) == 1
        all_device_option_list = device_menu[0].find_elements_by_class_name('filter-options-list')
        assert len(all_device_option_list) == 1
        all_device = all_device_option_list[0].find_elements_by_class_name('filter-row')
        device_name_list = [str(link.text).strip() for link in all_device]
        logger.info("Find available devices: " + str(device_name_list))
        if device not in device_name_list:
            logger.critical("Could not find the device, make sure the device name is correct. ")
            exit()
        for link in all_device:
            if device in link.text:
                logger.info("Selecting device: " + str(link.text).strip())
                link.click()
                break


def parse_page(driver, reverse=False, file_saver=None, start_date=None, end_date=None, start_time=None, end_time=None):
    driver.implicitly_wait(2)

    # For no record found in current time range
    end = driver.find_elements_by_class_name('full-width-message')
    if 'No records found' in end[0].text:
        logger.info('No record found in current time range.')
        if file_saver:
            file_saver.end_of_add()
        return
    is_start = True
    # Date checked by Amazon in the last step, check the time only in this step
    if start_time:
        start_time = datetime.strptime('{} {}'.format(start_date, start_time), "%m/%d/%Y %H:%M")
        is_start = False
    if end_time:
        end_time = datetime.strptime('{} {}'.format(end_date, end_time), "%m/%d/%Y %H:%M")
    check = WebDriverWait(driver, 30).until(EC.presence_of_element_located(
        (By.CLASS_NAME, "apd-content-box")))
    boxes = driver.find_elements_by_class_name('apd-content-box')
    # mainBox corresponds to each element with audio recording
    if reverse:
        boxes = reversed(boxes)
    for box in boxes:
        # Get box record datetime
        time_item_boxes = box.find_elements_by_class_name("record-info")
        assert len(time_item_boxes) == 1
        time_boxes = time_item_boxes[0].find_elements_by_class_name("item")
        assert len(time_boxes) <= 2
        box_date = str(time_boxes[0].text)
        box_time = str(time_boxes[1].text)
        if box_date.lower() == 'yesterday':
            box_date = datetime.today() - timedelta(days=1)
            box_date = box_date.strftime('%B %d, %Y')
        elif box_date.lower() == 'today':
            box_date = datetime.today()
            box_date = box_date.strftime('%B %d, %Y')

        box_date_time = '{} {}'.format(box_date, box_time)
        box_date_time = datetime.strptime(box_date_time, "%B %d, %Y %I:%M %p")
        logger.info('Web box time: ' + str(box_date_time))
        if file_saver:
            file_saver.set_box_time(box_date_time)

        # Get box record device
        device_boxes = time_item_boxes[0].find_elements_by_class_name("device-name")
        assert len(device_boxes) == 1
        device_name = str(device_boxes[0].text)
        logger.info('Web device name: ' + device_name)
        if file_saver:
            file_saver.set_device_name(device_name)

        # Start time and end time
        if not is_start:
            if box_date_time < start_time:
                continue
            else:
                logger.info('Web box time: ' + str(box_date_time))
                logger.info('Start time: ' + str(start_time))
                logger.info('Crawling started.')
                is_start = True
        if end_time:
            if box_date_time > end_time:
                logger.info('Web box time: ' + str(box_date_time))
                logger.info('End time: ' + str(end_time))
                logger.info('Crawling ended.')
                break

        expand_button = box.find_elements_by_class_name('apd-expand-toggle-button')
        expand_button[0].click()
        check = WebDriverWait(box, 30).until(EC.presence_of_element_located(
            (By.CLASS_NAME, 'record-item-text')))
        text_boxes = box.find_elements_by_class_name('record-item-text')
        if not text_boxes:
            logger.info("Non-text file. Skipped.")
            continue
        for record_item_box in box.find_elements_by_class_name('record-item'):
            text_boxes = record_item_box.find_elements_by_class_name('record-item-text')
            assert len(text_boxes) <= 1
            voice_boxes = record_item_box.find_elements_by_class_name('play-audio-button')
            assert len(voice_boxes) <= 1
            for text_box in text_boxes:
                if 'customer-transcript' in text_box.get_attribute('class'):
                    logger.info('Text *PAR:\t' + str(text_box.text))
                    if file_saver:
                        save_text = str(text_box.text)[1:]
                        save_text = save_text[:-1]
                        if len(text_boxes) == len(voice_boxes) == 1:
                            file_saver.add_text_with_audio_link('*PAR:\t' + save_text)
                        else:
                            file_saver.add_text('*PAR:\t' + save_text)
                elif 'alexa-response' in text_box.get_attribute('class'):
                    logger.info('Text *%xvas:\t' + str(text_box.text))
                    assert len(voice_boxes) == 0
                    if file_saver:
                        save_text = str(text_box.text)[1:]
                        save_text = save_text[:-1]
                        file_saver.add_text('%xvas:\t' + save_text)
                else:
                    # replacement-text, often happens when ASR failed
                    logger.info('Text *%rep:\t' + str(text_box.text))
                    if file_saver:
                        if len(text_boxes) == len(voice_boxes) == 1:
                            file_saver.add_text_with_audio_link('%rep:\t' + str(text_box.text))
                        else:
                            file_saver.add_text('%rep:\t' + str(text_box.text))
            for voice_box_idx in range(len(voice_boxes)):
                assert len(text_boxes) == len(voice_boxes) == 1
                voice_boxes = record_item_box.find_elements_by_class_name('play-audio-button')
                voice_boxes[voice_box_idx].click()
                request = driver.wait_for_request('https://www.amazon.com/alexa-privacy/apd/rvh/audio\?.+',
                                                  timeout=100)
                logger.info('GET Audio: ' + str(request.url))
                logger.info('Status_code: ' + str(request.response.status_code))
                if file_saver:
                    logger.info('Saving to file: ' + '{:03d}.wav'.format(file_saver.audio_file_count))
                    file_saver.add_audio(gzip.decompress(request.response.body))
                del driver.requests
                sleep(3)
    if file_saver:
        file_saver.end_of_add()


def scroll_page(driver):
    scroll_pause_time = 0.5

    # Get scroll height
    last_height = 100

    while True:
        # Scroll down to bottom
        driver.execute_script('window.scrollTo(0, ' + str(last_height) + ');')
        last_height += 100

        # Wait to load page
        sleep(scroll_pause_time)

        if EC.presence_of_element_located((By.CLASS_NAME, 'full-width-message')):
            end = driver.find_elements_by_class_name('full-width-message')
            if 'End of list' in end[0].text or 'No records found' in end[0].text:
                break


def setdefault_recursively(tgt, default):
    for k in default:
        if isinstance(default[k], dict):  # if the current item is a dict,
            # expand it recursively
            setdefault_recursively(tgt.setdefault(k, {}), default[k])
        else:
            # ... otherwise simply set a default value if it's not set before
            tgt.setdefault(k, default[k])


def main():
    global logger
    ap = ArgumentParser()
    ap.add_argument(
        "--config_file_path", required=False, default='config/example.yaml',
        help="Path of the config file."
    )
    args = vars(ap.parse_args())
    config_file_path = args['config_file_path']
    with open(config_file_path, 'r', encoding='utf-8') as file:
        args = yaml.safe_load(file)
    default_dict = {
        "save_dir": "vas_save",
        "session_name": None,
        "reverse": True,
        "device": None,
        "date_from": None,
        "date_to": None,
        "time_from": None,
        "time_to": None,
        'profile': os.path.basename(config_file_path).split('.')[0],
        'save_date_time': False,
        'save_device_name': False,
    }
    setdefault_recursively(args, default_dict)
    if args['session_name']:
        args['save_dir'] = os.path.join(os.path.abspath(args['save_dir']), args['session_name'])
    else:
        args['save_dir'] = os.path.join(
            os.path.abspath(args['save_dir']),
            str(datetime.now()).replace(':', '-').replace(' ', '-').replace('.', '-'))
    os.makedirs(args['save_dir'])
    logger = init_logging(args['save_dir'])

    if args["date_from"] and not args["date_to"]:
        args["date_to"] = str(datetime.now().month) + '/' + str(datetime.now(
        ).day) + '/' + str(datetime.now().year)
    if args["date_to"] and not args["date_from"]:
        logger.critical("You haven't specified beginning date. Use --date_from option.")
        exit(1)
    if not args["date_from"] and (args["time_from"] or args["time_to"]):
        logger.critical("You specified the time_from/time_to but don't specified date_from/date_to.")
        exit(1)

    file_saver = FileSaver(root_dir=args['save_dir'], save_date_time=args['save_date_time'],
                           save_device_name=args['save_device_name'])

    logger.info('args:')
    for arg in args:
        logger.info(str(arg) + ': ' + str(args[arg]))

    # start chromedriver
    driver = init_driver(args['profile'])
    logger.info('Driver started.')

    try:
        # login
        amazon_login(driver, args['account'], args['password'], args["date_from"], args["date_to"], args['device'])
    except TimeoutException:
        # catch broken connection
        logger.critical("Timeout exception. No internet connection? ")
        # sleep(10)
        exit()

    if args['reverse']:
        scroll_page(driver)
    parse_page(driver, reverse=args['reverse'], file_saver=file_saver,
               start_date=args['date_from'], end_date=args['date_to'],
               start_time=args['time_from'], end_time=args['time_to'])

    logger.info("All done. Exit.")


if __name__ == '__main__':
    main()

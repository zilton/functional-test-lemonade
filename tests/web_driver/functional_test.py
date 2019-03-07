# -*- coding: utf-8 -*-
import argparse
import json
import re
import sys
import time
import unittest

import selenium.webdriver.support.expected_conditions as ec
import selenium.webdriver.support.ui as ui
from pyvirtualdisplay import Display
from selenium.common.exceptions import NoAlertPresentException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from tbselenium.tbdriver import TorBrowserDriver

from tests.mail import email_sender

workflow_ids = []
workflow_message_error_warning = []
workflow_message_completed = ""

lemonade_login = ""
lemonade_password = ""

# Constants
ERROR_MSG = 'ERROR'
RUNNING_MSG = 'RUNNING'
COMPLETED_MSG = 'COMPLETED'
WAITING_MSG = 'WAITING'
WARNING_MSG = 'WARNING'

MAX_LOAD_PROBLEM = 3
LOAD_TIME = 10


class UntitledTestCase(unittest.TestCase):
    def setUp(self):
        print 'Loading...'

        self.display = Display(visible=0, size=(800, 600))
        self.display.start()

        self.driver = TorBrowserDriver('/scratch/zilton/troll/tor-browser_pt-BR/', tbb_logfile_path='test.log')

        # self.driver = webdriver.Chrome('chromium-browser')
        self.base_url = "https://lemonade.ctweb.inweb.org.br/#/workflows/1/"
        self.verificationErrors = []
        self.accept_next_alert = True

    def is_visible(self, locator, timeout=20):
        try:
            ui.WebDriverWait(self.driver, timeout).until(ec.visibility_of_element_located((By.ID, locator)))
            return True
        except TimeoutException:
            return False

    def is_not_visible(self, locator, timeout=2):
        try:
            ui.WebDriverWait(self.driver, timeout).until_not(ec.visibility_of_element_located((By.ID, locator)))
            return True
        except TimeoutException:
            return False

    def test_untitled_test_case(self):
        global workflow_message_error_warning, workflow_message_completed

        driver = self.driver
        '''Login'''
        driver.get("https://lemonade.ctweb.inweb.org.br/#/login")
        driver.find_element_by_xpath("//input[@type='email']").clear()
        driver.find_element_by_xpath("//input[@type='email']").send_keys(lemonade_login)
        driver.find_element_by_xpath("//input[@type='password']").clear()
        driver.find_element_by_xpath("//input[@type='password']").send_keys(lemonade_password)
        driver.find_element_by_xpath("//button[@type='submit']").click()
        time.sleep(LOAD_TIME)

        count_progress = 1.0
        length = len(workflow_ids)
        index = 0
        count_problem = 1
        while index < length:
            workflow_id = workflow_ids[index]

            '''Access the page of the workflow'''
            url = self.base_url + str(workflow_id)
            driver.get(url)

            '''Execute the workflow'''
            while True:
                try:
                    time.sleep(LOAD_TIME * 0.2)
                    driver.find_element_by_id("tlb-execute-wf").click()
                    break
                except Exception:
                    pass

            while True:
                try:
                    time.sleep(LOAD_TIME * 0.2)
                    driver.find_element_by_id("mdl-execute-wf").click()
                    break
                except Exception:
                    pass

            '''Monitoring the status of the execution'''
            time.sleep(LOAD_TIME)
            status = WAITING_MSG
            current_url = driver.current_url

            # Workflow with problem
            if current_url == "https://lemonade.ctweb.inweb.org.br/#/" and count_problem < MAX_LOAD_PROBLEM:
                count_problem += 1
                continue
            elif count_problem == MAX_LOAD_PROBLEM:
                status = WARNING_MSG

            while (status is WAITING_MSG) or (status == RUNNING_MSG):
                while True:
                    try:
                        status = str(driver.find_element_by_id("dtl-job-status").get_attribute(name='title').upper())
                        if status:
                            break
                        time.sleep(LOAD_TIME * 0.2)
                    except Exception:
                        pass

                if (status == WAITING_MSG) or (status == RUNNING_MSG):
                    driver.refresh()
                    time.sleep(LOAD_TIME)

            '''Main message after the execution ends'''
            message = ''
            if status != WARNING_MSG:
                while message == '':
                    try:
                        message = driver.find_element_by_id("dtl-job-status-text").text
                        break
                    except Exception:
                        pass
                    driver.refresh()
                    time.sleep(LOAD_TIME)

            workflow_name = ''
            while True and count_problem < MAX_LOAD_PROBLEM:
                try:
                    time.sleep(LOAD_TIME * 0.2)
                    workflow_name = driver.find_element_by_xpath("//a[contains(@href, '#/workflows/1/%s')]"
                                                                 % workflow_id).text
                    break
                except Exception:
                    pass

            if status == WARNING_MSG:
                message += ' - The execution presented an atypical problem. ' \
                           'Please check the workflow and the correct ' \
                           'update of the messages on the Lemonade page.'

            msg_dict = {'workflow_name': workflow_name,
                        'workflow_id': workflow_id,
                        'message': message,
                        'status': status,
                        'url': url
                        }

            if status != COMPLETED_MSG:
                workflow_message_error_warning.append(msg_dict)
            else:
                workflow_message_completed += " " + workflow_id

            UntitledTestCase.update_progress(job_title='Testing Lemonade workflow: ', progress=count_progress)
            count_progress += 1

            index += 1
            count_problem = 1

        self.driver.close()

    @staticmethod
    def update_progress(job_title, progress):
        global workflow_ids
        length = len(workflow_ids)
        progress = progress / length
        block = int(round(length * progress))
        message = "\r{0}: [{1}] {2}%".format(job_title,
                                             ', '.join(workflow_ids[:int(progress * length)]) + "-" * (length - block),
                                             round(progress * 100, 2))
        if progress >= 1:
            message += " DONE\r\n"
        sys.stdout.write(message)
        sys.stdout.flush()

    def is_element_present(self, how, what):
        try:
            self.driver.find_element(by=how, value=what)
        except NoSuchElementException:
            return False
        return True

    def is_alert_present(self):
        try:
            self.driver.switch_to_alert()
        except NoAlertPresentException:
            return False
        return True

    def close_alert_and_get_its_text(self):
        try:
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            if self.accept_next_alert:
                alert.accept()
            else:
                alert.dismiss()
            return alert_text
        finally:
            self.accept_next_alert = True

    def tearDown(self):
        UntitledTestCase.sendEmail()
        self.driver.quit()
        self.display.stop()
        self.assertEqual([], self.verificationErrors)

    @staticmethod
    def sendEmail():
        global workflow_message_error_warning, workflow_message_completed

        if len(workflow_message_error_warning) > 0:
            workflow_message_completed = re.sub("^\s+|\s+$", "", workflow_message_completed)

            message = 'WORKFLOWS THAT PERFORMED CORRECTLY: %s' % (workflow_message_completed.replace(' ', ', '))
            message += '\n\nWORKFLOWS THAT DID NOT RUN SUCCESSFULLY:\n'
            for m in workflow_message_error_warning:
                if m['status'] == WARNING_MSG:
                    message += '\n- WORKFLOW: %s' % m['workflow_id']
                else:
                    message += '\n- WORKFLOW: %s' % m['workflow_name']
                message += '\n\tSTATUS: %s' % m['status']
                message += '\n\tMESSAGE: %s' % m['message']
                message += '\n\tURL: %s' % m['url']
                message += '\n___________________________\n'

            subject = "[LEMONADE] - Automatic Test for Workflows"

            email_sender.main(message_status_report=message.encode('utf-8'), subject=subject)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-c')
    parser.add_argument('unittest_args', nargs='*')

    args = parser.parse_args()
    sys.argv[1:] = args.unittest_args

    if args.c:
        correct = False

        with open(args.c) as f:
            config = json.load(f)
            f.close()

        if config['email']['sender']['login'] and config['email']['sender']['password']:
            email_sender.address = config['email']['sender']['login']
            email_sender.password = config['email']['sender']['password']
            email_sender.contacts = config['email']['to']['file']
            email_sender.message = config['email']['message']['file']

            if config['lemonade']['login'] and config['lemonade']['password']:
                lemonade_login = config['lemonade']['login']
                lemonade_password = config['lemonade']['password']

                if len(config['workflow']['list']) > 0:
                    for _id in config['workflows']:
                        workflow_ids.append(str(_id))
                    unittest.main()

                    correct = True
                elif config['workflow']['file']:
                    with open(config['workflow']['file'], 'r') as f:
                        lines = f.readlines()
                        line = lines[0]
                        for i in range(1, len(lines)):
                            line += ';' + lines[i]
                        f.close()

                    line = line.replace('\n', '')
                    workflow_ids = re.split(',|;|\.|\s+|-', line, flags=re.DOTALL)
                    unittest.main()

                    correct = True

        if not correct:
            print 'Please, fill in the configuration file (JSON) correctly.'
    else:
        parser.print_usage()

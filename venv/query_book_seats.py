# Selenium Imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
# HTML imports
import requests
from bs4 import BeautifulSoup
# Email imports
import smtplib
import getpass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
# OS and Time import
import os, time

class QueryDal:

    def __init__(self, course_number, netid="", netpassword="",
                    headless=True, add_flag=0, drop_flag=0, crns=[], drop_courses_indices=[], term="202010"):
        # Setting course parameters
        self.course_number = course_number
        self.URL = f"https://dalonline.dal.ca/PROD/fysktime.P_DisplaySchedule?s_term={term}&s_subj=CSCI&s_numb={course_number}&s_district=100"
        # Set NetID and password
        self.netid = netid
        self.netpassword = netpassword
        # Headless flag
        self.headless = headless
        # Dalonline URL
        self.dalonline_url = "https://dalonline.dal.ca"
        # Setting add and drop flags
        self.add_flag = add_flag
        self.drop_flag = drop_flag
        # CRNs to be added
        self.crns = crns
        # Row indices to be dropped
        self.drop_courses_indices = drop_courses_indices
        # Term
        self.term = term


    def get_response(self):
        # Getting HTML source code
        response = requests.get(self.URL).content.decode('ascii', 'ignore').encode('utf-8')
        # Converting to BS4 object
        self.bs_response = BeautifulSoup(response, 'html.parser')

    def get_seats(self):
        # Checking availability
        self.seats = int(self.bs_response.find_all("td", {"class":"dettl"})[15].find("p").text)
        return self.seats

    @staticmethod
    def send_mail(send_from, send_to, subject, body_of_msg, files=[],
            server="localhost", port=587, username='', password='',
            use_tls=True):
        # Send email to given list of addresses
        message = MIMEMultipart()
        message['From'] = send_from
        message['To'] = ", ".join(send_to)
        message['Date'] = formatdate(localtime=True)
        message['Subject'] = subject
        message.attach(MIMEText(body_of_msg))
        smtp = smtplib.SMTP(server, port)
        if use_tls:
            smtp.starttls()
        smtp.login(username, password)
        smtp.sendmail(send_from, send_to, message.as_string())
        smtp.quit()

    def book_dal_online(self):
        self.setup_selenium()
        self.login_dal_online()
        #WebDriverWait(self.driver, 2)
        self.select_term()
        if self.drop_flag:
            #WebDriverWait(self.driver, 2)
            self.drop_courses()
        if self.add_flag:
            #WebDriverWait(self.driver, 2)
            self.add_courses()
        WebDriverWait(self.driver, 2)
        self.driver.close()

    def login_dal_online(self):
        # Open browser and open dalonline
        self.driver.get(self.dalonline_url)
        # Enter username
        username_input = self.driver.find_element_by_id("username")
        username_input.send_keys(self.netid)
        # Enter password
        password_input = self.driver.find_element_by_id("password")
        password_input.send_keys(self.netpassword)
        # Click Login
        self.driver.find_element_by_name("submit").click()

    def select_term(self):
        self.driver.get("https://dalonline.dal.ca/PROD/bwskfreg.P_AltPin")
        # Selecting FALL 2020 and submitting
        select = Select(self.driver.find_element_by_id('term_id'))
        select.select_by_value(self.term)
        self.driver.find_element_by_xpath("//form[1]/input[@value='Submit']").click()

    def add_courses(self):
        # Adding courses via CRNs and clicking on submit changes
        for index, crn in enumerate(self.crns, 1):
            element = self.driver.find_element_by_id(f"crn_id{index}")
            element.send_keys(crn)
        self.driver.find_element_by_xpath("//input[@value='Submit Changes']").click()

    def drop_courses(self):
        # Selecting "drop-web" for all courses and clicking on submit changes
        for index in self.drop_courses_indices:
            select = Select(self.driver.find_element_by_xpath(f"//form[1]/table[1]/tbody[1]/tr[{index}]/td[2]/select[1]"))
            select.select_by_value("DW")
        self.driver.find_element_by_xpath("//input[@value='Submit Changes']").click()

    def setup_selenium(self):
        # Setting chromedriver path
        CHROMEDRIVERPATH = os.path.join(os.getcwd(), "chromedriver")
        # Setting Chrome Options
        self.options = Options()
        # Setting headless flag
        if self.headless:
            self.options.add_argument("--headless")
        # Selenium driver
        self.driver = webdriver.Chrome(options=self.options, executable_path=CHROMEDRIVERPATH)

if __name__ == "__main__":
    # Get from address
    username = input("Enter email:\n")
    # Get to addresses
    to_addresses = input("Enter the addresses you want to send an email to(separated by comma):\n").split(",")
    # Get password for sender email
    password = getpass.getpass()
    # Enter term
    term = input("Enter term: 202010 for fall 2019 and 202020 for winter 2020\n")
    # Get course number
    course_number = input("Enter course number:\n")
    # Want email service or booking seat service
    service = int(input("Enter 0 for email notification on availability, 1 for booking seat automatically:\n"))
    if service:
        # NET ID
        netid = input("Enter NetID:\n")
        # NET PASSWORD
        netpassword = getpass.getpass()
        drop_flag = int(input("Do you want to drop courses? Say 1 for Yes, 0 for No\n"))
        drop_courses_indices=[]
        if drop_flag:
            # Row indices to be dropped
            drop_courses_indices = input("Enter indices to be dropped (separate by comma if more than 1):\n").split(",")
        add_flag = int(input("Do you want to add courses? Say 1 for Yes, 0 for No\n"))
        crns=[]
        if add_flag:
            # CRNs to be added
            crns = input("Enter CRNs to be added (separate by comma if more than 1):\n").split(",")
        # Creating dalquery object
        dalquery = QueryDal(course_number, netid=netid, netpassword=netpassword, headless=True,
                    add_flag=add_flag, drop_flag=drop_flag, crns=crns, drop_courses_indices=drop_courses_indices, term=term)
    else:
        # Creating dalquery object
        dalquery = QueryDal(course_number, netid, netpassword, True, term=term)

    print("SEATS:")
    while True:
        # Query every 1 min
        time.sleep(60)
        # Get html source
        dalquery.get_response()
        # Check number of seats
        seats = dalquery.get_seats()
        print(seats)
        # If seats are available
        if seats:
            print(seats)
            break

    #QueryDal
    # Send email with given inputs
    QueryDal.send_mail(username, to_addresses, f"SEATS ARE AVAILABLE FOR CSCI{course_number}",
                f"Seats Available: {seats}", server="smtp.gmail.com", username=username, password=password)
    if service:
        # Book if boolean value is 1
        dalquery.book_dal_online()

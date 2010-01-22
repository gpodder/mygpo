#
# This file is part of my.gpodder.org.
#
# my.gpodder.org is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# my.gpodder.org is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public
# License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with my.gpodder.org. If not, see <http://www.gnu.org/licenses/>.
#

from selenium import selenium

import unittest, time, re

class Login(unittest.TestCase):
    def setUp(self):
        self.verificationErrors = []
        self.selenium = selenium("localhost", 4444, "*firefox", "http://127.0.0.1:8000/")
        self.selenium.start()
    
    def test_login_logout(self):
        sel = self.selenium
        sel.open("/")
        sel.type("user", "ale")
        sel.type("pwd", "ale")
        sel.click("//input[@value='Login']")
        sel.wait_for_page_to_load("30000")
        self.failUnless(sel.is_text_present("ale"))
        sel.click("link=Logout")
        sel.wait_for_page_to_load("30000")
        self.failUnless(sel.is_text_present("my.gpodder.org"))
    
    def test_false_login(self):
        sel = self.selenium
        sel.open("/")
        sel.type("user", "ale")
        sel.type("pwd", "false")
        sel.click("//input[@value='Login']")
        sel.wait_for_page_to_load("30000")
        self.failUnless(sel.is_text_present("Unknown user or wrong password"))
        
    def tearDown(self):
        self.selenium.stop()

class Podcasts(unittest.TestCase):
    def setUp(self):
        self.verificationErrors = []
        self.selenium = selenium("localhost", 4444, "*firefox", "http://127.0.0.1:8000/")
        self.selenium.start()
        self.selenium.open("/")
        self.selenium.type("user", "ale")
        self.selenium.type("pwd", "ale")
        self.selenium.click("//input[@value='Login']")
        self.selenium.wait_for_page_to_load("30000")
        
    def test_add_two_podcasts(self):
        sel = self.selenium
        sel.open("podcast/1")
        sel.click("link=Subscribe to Testpodcast 1")
        sel.wait_for_page_to_load("30000")
        sel.click("//input[@value='OK']")
        sel.click("link=Subscriptions")
        self.failUnless(sel.is_text_present("Testpodcast 1"))
        self.failUnless(sel.is_text_present("test_dev1"))
        sel.open("podcast/2")
        sel.click("link=Subscribe to Testpodcast 2")
        sel.wait_for_page_to_load("30000")
        sel.click("//input[@value='OK']")
        sel.click("link=Subscriptions")
        self.failUnless(sel.is_text_present("Testpodcast 2"))
        self.failUnless(sel.is_text_present("test_dev1"))
        
    def test_start_syncronisation(self):
        sel = self.selenium
        sel = self.selenium
        sel.open("/device/1")
        self.failUnless(sel.is_text_present("Synchronize with the following devices:"))
        sel.click("//input[@value='OK']")
        self.failUnless(sel.is_text_present("test_dev2"))
        
    def test_stop_syncronisation(self):
        sel = self.selenium
        sel.open("/device/1")
        sel.click("link=Stop synchronisation for test_dev1")
        self.failUnless(sel.is_text_present("not synchronized"))
        
    def test_add_and_remove_podcast(self):
        sel = self.selenium
        sel.open("/podcast/3")
        sel.click("link=Subscribe to Testpodcast 3")
        sel.click("//input[@value='OK']")
        sel.click("link=Subscriptions")
        self.failUnless(sel.is_text_present("Testpodcast 3"))
        sel.click("link=Testpodcast 3")
        sel.click("//div[@id='body']/ul/li/div[2]/a/img")
        self.failUnless(sel.is_text_present("Subscribe to Testpodcast 3"))
        
    def tearDown(self):
        self.selenium.stop()

if __name__ == "__main__":
    unittest.main()



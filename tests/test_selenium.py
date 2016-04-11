import re
import time
import threading
import unittest
from selenium import webdriver
from app import create_app, db
from app.models import Role, User, Post

class SeleniuTestCase(unittest.TestCase):
	client = None

	@classmethod
	def setUpClass(cls):
		#launch Firefox
		try:
			cls.client = webdriver.Chrome()
		except:
			pass

		if cls.client:
			cls.app = create_app('testing')
			cls.app_context = cls.app.app_context()
			cls.app_context.push()

			import logging
			logger = logging.getLogger('werkzeug')
			logger.setLevel('ERROR')

			# create database, and fill it up with some faked data
			db.create_all()
			Role.insert_roles()
			User.generate_fake(10)
			Post.generate_fake(10)

			# add administrater
			admin_role = Role.query.filter_by(permissions=0xff).first()
			admin = User(email='john@example.com',
						 username='john', password='cat',
						 role=admin_role, confirmed=True)
			db.session.add(admin)
			db.session.commit()

			# launch Flask server in a thread
			threading.Thread(target=cls.app.run).start()

			# give the server a second to ensure it is up
			time.sleep(1)

	@classmethod
	def tearDownClass(cls):
		if cls.client:
			# close Flask server and browser
			cls.client.get('http://localhost:5000/shutdown')
			cls.client.close()

			# destroy database
			db.drop_all()
			db.session.remove()

			#delete program context
			cls.app_context.pop()

	def setup(self):
		if not self.client:
			self.skipTest('web browser not available')

	def tearDwon(self):
		pass

	def test_admin_home_page(self):
		# enter homepage
		self.client.get('http://localhost:5000/')
		self.assertTrue(re.search('Hello,\s+Stranger!', self.client.page_source))

		# enter login page
		self.client.find_element_by_link_text('Log In').click()
		self.assertTrue('<h1>Login</h1>' in self.client.page_source)

		# login
		self.client.find_element_by_name('email').send_keys('john@example.com')
		self.client.find_element_by_name('password').send_keys('cat')
		self.client.find_element_by_name('submit').click()
		self.assertTrue(re.search('Hello,\s+john!', self.client.page_source))

		# enter userdata page
		self.client.find_element_by_link_text('Profile').click()
		self.assertTrue('<h1>john</h1>' in self.client.page_source)

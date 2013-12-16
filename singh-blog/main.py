#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
I have implemented jinja2 with python. Jinja2 is a full featured template
engine for Python.

Jinja is a template engine for the Python programming language. 
It is similar to the Django template engine but provides Python-like 
expressions while ensuring that the templates are evaluated in a sandbox. 
It's a text-based template language and thus can be used to generate any 
markup as well as sourcecode. It's licensed under a BSD License.

Since the Requirement of the project requires us to use google app engine 
most of the classes used are google app engine classes like webapp,ext,api etc

"""
from jinja2 import BaseLoader, TemplateNotFound
from os.path import join, exists, getmtime
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import images
from google.appengine.ext.db import Key
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import urlfetch

import datetime
import webapp2
import jinja2
import os
import urllib
import logging
import cgi
import re,textwrap

jinja_env = jinja2.Environment (
	loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
	extensions=['jinja2.ext.autoescape'],
	autoescape=True)
template_dir = os.path.join(os.path.dirname(__file__), 'templates')


def render_str(template, **params):
	t = jinja_env.get_template(template)
	return t.render(params)

class BaseHandler(webapp2.RequestHandler):
	def render(self,template,**kw):
		self.response.out.write(render_str(template, **kw))
	
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

""" This basic class my contact details like Phone, email id"""

class About(BaseHandler):

	def get(self):
		url=""
		url_linktext=""

		if users.get_current_user():
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		else:
			url = users.create_login_url(self.request.uri)
			url_linktext = 'Login'
		upper_post = db.GqlQuery("SELECT * FROM UpperModel ")
		upper_posts_dic = {"upper_post" : upper_post, 'url': url,
            'url_linktext': url_linktext}	
		self.render('about.html',**upper_posts_dic)

'''

This is default home page class which displays blog
details like blogger name, id and date of blog creation. It displays 
10 blog details as per the project requirement. To see more more blogs(if any)
use the Next button at the bottom(Note: Next button will only be activated if 
number of blogs are more than 10).

'''
class Home(BaseHandler):

	def get(self):
		url=""
		url_linktext=""
		user = users.get_current_user()
		if users.get_current_user():
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		else:
			url = users.create_login_url(self.request.uri)
			url_linktext = 'Login'
		

		page = self.request.get('page')
		
		if page == "":
			page=1
		
		number_of_sheet = db.GqlQuery(" SELECT * FROM UpperModel")
		number = int (number_of_sheet.count())		
		sheet=int (page)
		value = int (sheet)*10-10
		number_of_tags = db.GqlQuery(" SELECT DISTINCT tag FROM LowerModel")

		
		if (number % 10 == 0 ):
			total_page = number/10
		else:	
			total_page = int (number) /10 + 1
		
		
		if (total_page > sheet): 
			flag = True
		else: 
			flag = False

		
		posts_query = db.GqlQuery(" SELECT * FROM UpperModel order by user_id")
		posts = posts_query.fetch(10, offset=value)
		upper_posts_dic = {"posts" : posts, 'url': url,'page' : page,'flag' : flag,
		    'url_linktext': url_linktext, 'user_id' : user, 'number_of_tags' : number_of_tags }
		
		self.render('/home.html', **upper_posts_dic)    

		
"""

This class contains the information of all the post written by various
users so far. Please note : One user can have multiple blogs and each blog 
may contain more than one posts (So with same blog id, there can be more than one post).

"""
class All_Posts(BaseHandler):

	def get(self):


		url=""
		url_linktext=""
		if users.get_current_user():
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		else:
			url = users.create_login_url(self.request.uri)
			url_linktext = 'Login'
		
		page = self.request.get('page')
		logging.info("page :::::::::: %s" %page)

		if page ==  "":
			page=1
		sheet=int (page)
		value = int (sheet)*10-10
		number_of_page = db.GqlQuery(" SELECT * FROM LowerModel ORDER BY adddate DESC")
		number = int (number_of_page.count())
		logging.info("Number :::::::::: %s" %number)
		if (number % 10 ==0 ):
			total_page = number/10
		else:	
			total_page = int (number) /10 + 1

		if (total_page > sheet): 
			flag = True
		else: 
			flag = False
		
		logging.info("total_page :::::::::: %s" %total_page)	
		logging.info("sheet :::::::::: %s" %sheet)

		posts_query = db.GqlQuery(" SELECT * FROM LowerModel ORDER BY adddate DESC")
		posts = posts_query.fetch(10, offset=value)
		posts_dic = {"posts" : posts, 'url': url, 'page' : page, 'flag' :flag,
       'url_linktext': url_linktext}
		self.render('all_posts.html', **posts_dic)

'''

This class is upper layer of the Model structure created specifically
for this project. As per the structure, This class contains details only
basic details of project like user id,blog id, blog name.

'''
class Write_UpperModel(BaseHandler):

	def get(self):
		user = users.get_current_user() 
		url=""
		url_linktext=""

		if users.get_current_user():
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		else:
			self.redirect(users.create_login_url(self.request.uri))
			url = users.create_login_url(self.request.uri)
			url_linktext = 'Login'

		user_id = users.get_current_user()	
		upper_post = db.GqlQuery("SELECT * FROM UpperModel where user_id = :1 " , user_id)
		upper_posts_dic = {"upper_post" : upper_post, 'url': url,
		    'url_linktext': url_linktext}
		self.render('write_upper_model.html', **upper_posts_dic)

	def post(self):
		url=""
		url_linktext=""
		if users.get_current_user():
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		else:
			url = users.create_login_url(self.request.uri)
			url_linktext = 'Login'

		User_blog_id = self.request.get('blog_id')
		User_user_id = users.get_current_user()
		User_blog_name = self.request.get('blog_name')
		blog_details = UpperModel(blog_id=User_blog_id,blog_name=User_blog_name,user_id=User_user_id)
		blog_details.put()
		self.redirect('/write_lower_model?blog_id=%s' % User_blog_id)

class rss(BaseHandler):

	def get(self):


		url=""
		url_linktext=""
		if users.get_current_user():
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		else:
			url = users.create_login_url(self.request.uri)
			url_linktext = 'Login'
		
		posts_query = db.GqlQuery(" SELECT * FROM LowerModel ORDER BY adddate DESC")
		posts = posts_query.fetch(10)
		posts_dic = {"posts" : posts, 'url': url,'url_linktext': url_linktext}
		self.render('rss.xml', **posts_dic)


		
'''

This class is upper layer of the Model structure created specifically
for this project. As per the structure, This class contains details only
basic details of project like user id,blog id, blog name.

'''

class Write_LowerModel(BaseHandler):

 	def get(self):
 		blog_id = self.request.get('blog_id')
		
		url=""
		url_linktext=""

		if users.get_current_user():
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		else:
			url = users.create_login_url(self.request.uri)
			url_linktext = 'Login'

		upper_post = UpperModel.gql("where blog_id = :1 ORDER BY adddate DESC ", blog_id)
		upper_posts_dic = {"upper_post" : upper_post, "blog_id": blog_id, 'url': url,
            'url_linktext': url_linktext}
		self.render('write_lower_model.html', **upper_posts_dic)
		
	def post(self):
		url=""
		tag = []
		content_limit = []
		url = users.create_logout_url(self.request.uri)
		url_linktext = 'Logout'
		blog_id = self.request.get('blog_id')
		subject = self.request.get('subject')
		content = self.request.get('content')
		content_limit = re.sub(r'<.+?>','',content)
		content_less = content_limit[:500]
		#content_limit = textwrap.wrap(content,500)
		#content_less = content_limit[0]
		photo1 = self.request.get('img')
		temp_tag = self.request.get('tag')
		logging.info("tag :  :   :  %s" %temp_tag)
		temp_tag2 = temp_tag.replace(" ","")
		tag = temp_tag2.split(",")
		logging.info("temp_tag2 :  :   :  %s" %temp_tag2)
		logging.info("tag :  :   :  %s" %tag)
		if photo1:
			photo = db.Blob(photo1)
			#photo = images.resize(self.request.get('photo1'),32,32)
			#photo = db.Blob(photo1)
		else:
			photo = db.Blob()
		user = users.get_current_user()
		blog_post = LowerModel(title=subject, content=content_less,user_id=user,blog_id=blog_id,photo=photo,tag=tag)
		blog_post.put()
		self.redirect('/%s' %blog_id)
	
'''

This class as Name suggest is Page handler class which render( or browse) any 
specific page when clicked. This clas uses the regular expression (/([^.]+)') for 
this purpose. It displays all lower level details about any particular blog.

'''

class PageHandler(BaseHandler):

	def get(self, blog_id):
		url=""
		url_linktext=""
		if users.get_current_user():
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		else:
			self.redirect(users.create_login_url(self.request.uri))
			url = users.create_login_url(self.request.uri)
			url_linktext = 'Login'
		posts = db.GqlQuery("SELECT * FROM LowerModel where blog_id = :1 ORDER BY adddate DESC ", blog_id)
		posts_dic = {"posts" : posts, 'url': url,
		    'url_linktext': url_linktext}
		self.render('specific_posts.html', **posts_dic)

'''

This class as browse the lower model detail of any particular post. 

'''

class SpecificPost(BaseHandler):

	def get(self):
		url=""
		url_linktext=""
		if users.get_current_user():
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		else:
			url = users.create_login_url(self.request.uri)
			url_linktext = 'Login'

		post_key = self.request.get('post_key')
		key_obj = Key(post_key)
		posts = LowerModel.gql("where __key__ = :1", key_obj)
		logging.info("specific post ::  %s " % posts.count())
		posts_dic = {"posts" : posts}
		self.render('specific_posts.html', **posts_dic)

'''

This class perform the operaton of modifying any blog. This class help in 
modifying any post of any particular specific blog id.
Please Note : Blog/Post can only be modified by the owner of that 
particular blog/post.

'''

class AddModifyBlog(BaseHandler):


	def get(self):
		url=""
		url = users.create_logout_url(self.request.uri)
		url_linktext = 'Logout'
		blog_id = self.request.get('blog_id')

		upper_post = LowerModel.gql("where blog_id = :1", blog_id)

		logging.info('count ::::: %s' % upper_post.count() )

		upper_posts_dic = {"upper_post" : upper_post, "blog_id": blog_id, 'url': url,
            'url_linktext': url_linktext}

		self.render('addmodifyblog.html', **upper_posts_dic)

	def post(self):
		url=""
		url = users.create_logout_url(self.request.uri)
		url_linktext = 'Logout'
		blog_id = self.request.get('blog_id')
		subject = self.request.get('subject')
		content = self.request.get('content')
		user = users.get_current_user()
		blog_post = LowerModel(title=subject, content=content,user_id=user,blog_id=blog_id)
		blog_post.put()
		self.redirect('/%s' % blog_id)


'''
This class is perform the function of modifying any particular post.
Please Note : Blog/Post can only be modified by the owner of that 
particular blog/post.

'''
class EditPost(BaseHandler):


	def get(self):
		url=""
		#blog_name = self.request.get('blog_name')
		blog_id = self.request.get('blog_id')
		url = users.create_logout_url(self.request.uri)
		url_linktext = 'Logout'
		post_key = self.request.get('post_key')
		
		key_obj = Key(post_key)
		posts = LowerModel.gql("where __key__ = :1", key_obj)
		logging.info("specific key ::  %s " % post_key)
		logging.info("specific post ::  %s " % posts.count())
		#posts_dic = {"post" : post}
		#self.render('editpost.html', **posts_dic)
		#post_key = self.request.get('post_key')
		#logging.info("post_key   :::::::::: %s" %post_key)
		#key_obj = Key(post_key)
		#posts = LowerModel.gql("where __key__ = :1", blog_id)
		#post = LowerModel.gql("where blog_name = :1 and blog_id = :2 ", blog_name, blog_id)
		#logging.info("post.count :::::::: %s" %post.count )
		#posts_dic = {"post" : post, "blog_id": blog_id, 'url': url,
         #   'url_linktext': url_linktext}
		
		#photo = self.request.get('photo')
		#logging.info("specific post ::  %s " %posts.count())
		posts_dic = {"posts" : posts}
		self.render('editpost.html', **posts_dic)

	def post(self):

		post_key = self.request.get('post_key')
		
		key_obj = Key(post_key)
		posts = LowerModel.gql("where __key__ = :1", key_obj)

		posts.title = self.request.get('subject')

		posts.content = self.request.get('content')

		posts.put()

		self.redirect('/%s' % blog_id)

'''
This class store/display all the tags created while writing posts by 
the all the users. This class help in searching for all the posts 
which belog to same tag.

'''
class SearchByTag(BaseHandler):


	def get(self):
		tag=self.request.get('tag')
		url=""
		url_linktext=""
		if users.get_current_user():
			url = users.create_logout_url(self.request.uri)
			url_linktext = 'Logout'
		else:
			url = users.create_login_url(self.request.uri)
			url_linktext = 'Login'

		page = self.request.get('page')
		
		if page == "":
			page=1
		sheet=int (page)
		value = int (sheet)*10-10
		number_of_page = db.GqlQuery(" SELECT * FROM LowerModel ORDER BY adddate DESC")
		number = int (number_of_page.count())
		
				
		if (number % 10 == 0 ):
			total_page = number/10
		else:	
			total_page = int (number) /10 + 1

		if (total_page > sheet): 
			flag = True
		else: 
			flag = False

		posts_query = db.GqlQuery(" SELECT * FROM LowerModel where tag = :1 ORDER BY adddate DESC", tag)
		
		posts = posts_query.fetch(10, offset=value)

		posts_dic = { "posts" : posts, 'url': url, 'page' : page, 'flag' :flag, 'tag' : tag, 'url_linktext': url_linktext}
		self.render('all_posts.html', **posts_dic)
'''
This class defines the UpperModel structure, which act like a 
upper layer in the design of this project. This class only 
define 3 things
1.blog_id
2.user_id
3.blog_name
'''
		
class UpperModel(db.Model):


	blog_id = db.StringProperty(required=True)
	user_id = db.UserProperty(required=True)
	blog_name = db.StringProperty(required=True)


'''
This class defines the LowerModel structure, contains key things 
required by the user like This class only define 3 things
1.blog_id
2.user_id
3.content
4.adddate
5.photo
6.tags

'''
class LowerModel(db.Model):

	blog_id = db.StringProperty()
	title = db.StringProperty(required=True)
	user_id = db.UserProperty()
	content = db.StringProperty(required=True,multiline=True)
	adddate = db.DateTimeProperty(auto_now_add=True)
	photo = db.BlobProperty()	
	tag = db.StringListProperty(indexed=True)

	

'''
This class is mainly designed to handle(store) and display images.

'''
class Image(webapp2.RequestHandler):


    def get(self):

		LowerModel = db.get(self.request.get('img_id'))
		if LowerModel.photo:
			self.response.headers['Content-Type'] = 'image/png'
			logging.info("in lower")
			self.response.out.write(LowerModel.photo)
		else:
			#self.error(404)
			logging.info("in else")
			self.response.out.write("No Photo")
            	
app = webapp2.WSGIApplication([
	('/',Home),
	('/write_upper_model',Write_UpperModel),
	('/img',Image),
    ('/all_posts', All_Posts),
    ('/about', About),
    ('/addmodifyblog',AddModifyBlog),
    ('/editpost', EditPost),
	('/showpost', SpecificPost),
    ('/write_lower_model',Write_LowerModel),
    ('/searchbytag',SearchByTag),
	('/rss',rss),
    ('/([^.]+)', PageHandler),
    ('/([^&]+)', PageHandler)
], debug=True)


#!/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import os
import tornado.ioloop
import tornado.web
import tornado.escape
import tornado.options
from tornado.options import define, options
import logging
import sqlite3
from datetime import date,datetime
from PIL import Image


conn = sqlite3.connect("proconDB.db")
c = conn.cursor()
if list(c.execute("select count(*) from sqlite_master where type='table' and name='blog';"))[0][0] == 0:
  b_d = u"""
  create table blog(
    id integer primary key,
    writer varchar(10),
    date datetime,
    title varchar(30),
    category varchar(12),
    body varchar(300)
        );
  """
  c.execute(b_d)
  conn.commit()

define("port", default=5000, type=int)
define("username", default="user")
define("password", default="pass")

class BaseHandler(tornado.web.RequestHandler):
  cookie_username = "username"

  def get_current_user(self):
    username = self.get_secure_cookie(self.cookie_username)
    logging.debug('BaseHandler - username: %s' % username)
    if not username: return None
    return tornado.escape.utf8(username)

  def set_current_user(self, username):
    self.set_secure_cookie(self.cookie_username, tornado.escape.utf8(username))

  def clear_current_user(self):
    self.clear_cookie(self.cookie_username)

class MainHandler(BaseHandler):
  @tornado.web.authenticated
  def get(self):
    self.write("Hello, <b>" + self.get_current_user() + "</b> <br> <a href=/auth/logout>Logout</a>")


class AuthLoginHandler(BaseHandler):
  def get(self):
    self.render("login.html")

  def post(self):
    logging.debug("xsrf_cookie:" + self.get_argument("_xsrf", None))
    
    self.check_xsrf_cookie()

    username = self.get_argument("username")
    password = self.get_argument("password")

    logging.debug('AuthLoginHandler:post %s %s' % (username, password))

    user_data=list(c.execute('''SELECT * FROM admin where name="%s";''' % username))[0]
    print(user_data)
    if user_data != None and user_data[2] == password:
      self.set_current_user(username)
      self.redirect("/home")
    else:
			self.write_error(403)

class AuthLogoutHandler(BaseHandler):
	def get(self):	
		self.clear_current_user()
		self.redirect('/home')

class HomeHandler(BaseHandler):
  def get(self):
  	self.render("home.html",
                login_user = self.get_current_user()
                )
class ActHandler(tornado.web.RequestHandler):
  def get(self):
  	self.render("activity.html")

class BlogHandler(BaseHandler):
  def get(self):
    blog_data=c.execute("SELECT * FROM blog ORDER BY id DESC;")

    self.render("blog.html",
                blog_data = blog_data,
                login_user = self.get_current_user()
                )
   
  def post(self):
    blog_id = list(c.execute("select count(*) from blog;"))[0][0] + 1
    writer = self.get_current_user()
    date = datetime.now()
    title = self.get_argument('blog_title')
    category = self.get_argument('blog_category')
    body = self.get_argument('blog_body')
    print(body)
    
    c.execute('''insert into blog(id,writer,date,title,category,body) values(:id, :writer, :date, :title, :category, :body)''', {'id':blog_id, 'writer':writer, 'date': date.today(), 'title':title, 'category':category, 'body':body})
    conn.commit()
    
    self.redirect("/blog")
               
               
class ImageSaveHandler(BaseHandler):
  def post(self):
		file1 = self.request.files['aaa'][0]
		original_fname = file1['filename']
		extension = os.path.splitext(original_fname)[1]
		fname=str(datetime.now())[:19]+"_"+self.get_current_user()
		final_filename= fname+extension
		output_file = open("img/" + final_filename, 'w')
		output_file.write(file1['body'])
		self.redirect("/blog")


class LinkHandler(tornado.web.RequestHandler):
  def get(self):
    self.render("link.html")
class WikiHandler(tornado.web.RequestHandler):
  def get(self):
    self.render("wiki.html")

class Application(tornado.web.Application):
  def __init__(self):
    handlers = [
      (r"/home", HomeHandler),
      (r"/activity", ActHandler),
      (r"/blog", BlogHandler),
      (r"/blog/image_save", ImageSaveHandler),
      (r"/link", LinkHandler),
      (r"/wiki", WikiHandler),
		  (r'/', MainHandler),
      (r'/auth/login', AuthLoginHandler),
      (r'/auth/logout', AuthLogoutHandler)
    ]
    settings = dict(
    	cookie_secret='gaofjawpoer940r34823842398429afadfi4iias',
    	static_path=os.path.join(os.path.dirname(__file__), "static"),
    	template_path=os.path.join(os.path.dirname(__file__), "templates"),
  		login_url="/auth/login",
   		xsrf_cookies=True,
    	autoescape="xhtml_escape",
    	debug=True,
    )
    tornado.web.Application.__init__(self, handlers, **settings)


def main():
  tornado.options.parse_config_file(os.path.join(os.path.dirname(__file__), 'server.conf'))
  tornado.options.parse_command_line()
  app = Application()
  app.listen(options.port)
  logging.debug('run on port %d in %s mode' % (options.port, options.logging))
  tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
  main()


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
    nickname varchar(20),
    date datetime,
    title varchar(30),
    category varchar(12),
    body varchar(300)
        );
  """
  c.execute(b_d)
  conn.commit()

define("port", default=5000, type=int)

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
    if user_data != None and user_data[2] == password:
      self.set_current_user(username)
      self.redirect("/home")
    else:
			self.write_error(403)

class AuthLogoutHandler(BaseHandler):
	def get(self):	
		self.clear_current_user()
		self.redirect('/home')

class AddUserHandler(BaseHandler):
  def get(self):
    current_user = self.get_current_user()
    c_user_data=list(c.execute('''SELECT * FROM admin where name="%s";''' % current_user))[0]
    if c_user_data != None and c_user_data[3] == "A":
      self.render("add_user.html",
                login_user = current_user
                )
    else:
      self.write_error(403)

   
  def post(self):
    user_id = list(c.execute("select count(*) from admin;"))[0][0] + 1
    name = self.get_argument('name')
    password = self.get_argument('password')
    accessibility = self.get_argument('accessibility')
    nickname = self.get_argument('nickname')
    classroom = self.get_argument('classroom')
    
    c.execute('''insert into admin(id,name,password,accessibility,nickname,class) values(:id, :name, :password, :accessibility, :nickname, :classroom)''', {'id':user_id, 'name':name, 'password': password, 'accessibility':accessibility, 'nickname':nickname, 'classroom':classroom})
    conn.commit()
    
    self.redirect("/home")







class HomeHandler(BaseHandler):
  def get(self):
    current_user = self.get_current_user()
    a_right=False
    if current_user != None:
      c_user_data=list(c.execute('''SELECT * FROM admin where name="%s";''' % str(current_user)))[0]
      if c_user_data[3] == "A":
        a_right=True
    else:
      c_user_data = None
    self.render("home.html",
                login_user = c_user_data,
                access_right = a_right
                )

class ActHandler(BaseHandler): 
  def get(self):
    current_user = self.get_current_user()
    if current_user != None:
      c_user_data=list(c.execute('''SELECT * FROM admin where name="%s";''' % str(current_user)))[0]
      conn.commit()
    else:
      c_user_data = None
    
    self.render("activity.html",
                login_user = c_user_data
                )

class BlogHandler(BaseHandler):
  def get(self,page_number):
    current_user = self.get_current_user()
    if current_user != None:
      c_user_data=list(c.execute('''SELECT * FROM admin where name="%s";''' % str(current_user)))[0]
    else:
      c_user_data = None
    
    x = int(page_number)
    lim = 5
    y = (x-1)*lim
    blog_count = list(c.execute("select count(*) from blog;"))[0][0]
    b_data=c.execute("SELECT * FROM blog ORDER BY id DESC LIMIT %d OFFSET %d;" % (lim,y))
    page = int(blog_count/lim + (1-1/lim))
    self.render("blog.html",
                b_data = b_data,
                login_user = c_user_data,
                blog_count = blog_count,
                lim = lim,
                page = page,
                current_page = page_number
                )

class BlogSaveHandler(BaseHandler):
  def post(self):
    c_user_data=list(c.execute('''SELECT * FROM admin where name="%s";''' % str(self.get_current_user())))[0]

    blog_id = list(c.execute("select count(*) from blog;"))[0][0] + 1
    writer = self.get_current_user()
    nickname = list(c_user_data)[4]
    date = datetime.now()
    title = self.get_argument('blog_title')
    category = self.get_argument('blog_category')
    body = self.get_argument('blog_body')
    
    c.execute('''insert into blog(id,writer,nickname,date,title,category,body) values(:id, :writer, :nickname, :date, :title, :category, :body)''', {'id':blog_id, 'writer':writer, 'nickname':nickname, 'date': date.today(), 'title':title, 'category':category, 'body':body})
    conn.commit()
    
    self.redirect("/blog/1")
               
               
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


class LinkHandler(BaseHandler):
  def get(self):
    current_user = self.get_current_user()
    if current_user != None:
      c_user_data=list(c.execute('''SELECT * FROM admin where name="%s";''' % str(current_user)))[0]
    else:
      c_user_data = None
    
    self.render("link.html",
                login_user = c_user_data
                )
class WikiHandler(BaseHandler):
  def get(self):
    current_user = self.get_current_user()
    if current_user != None:
      c_user_data=list(c.execute('''SELECT * FROM admin where name="%s";''' % str(current_user)))[0]
    else:
      c_user_data = None

    self.render("wiki.html",
                login_user = c_user_data
                )

class WikiDetailHandler(BaseHandler):
  
  def get(self):
    current_user = self.get_current_user()
    if current_user != None:
      c_user_data=list(c.execute('''SELECT * FROM admin where name="%s";''' % str(current_user)))[0]
    else:
      c_user_data = None

    self.render("useful_items.html",
                login_user = c_user_data
                )


class Application(tornado.web.Application):
  def __init__(self):
    handlers = [
      (r"/home", HomeHandler),
      (r"/activity", ActHandler),
      (r"/blog/([1-9]+)", BlogHandler),
      (r"/blog/image_save", ImageSaveHandler),
      (r"/blog/text_save", BlogSaveHandler),
      (r"/link", LinkHandler),
      (r"/wiki", WikiHandler),
      (r"/wiki/useful_items", WikiDetailHandler),
		  (r'/', MainHandler),
      (r'/auth/login', AuthLoginHandler),
      (r'/auth/logout', AuthLogoutHandler),
      (r'/auth/add_user', AddUserHandler)
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


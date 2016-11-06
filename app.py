from flask import Flask, render_template, request, session , g , redirect , url_for ,abort, render_template , flash, jsonify
import sqlite3
import gc
import json
#from textstat.textstat import textstat
#import re
import urllib
from passlib.hash import sha256_crypt
from functools import wraps
from flask_oauth import OAuth

DATABASE = 'BucketSuper.db'
DEBUG = True
SECRET_KEY = 'development_key'

app = Flask(__name__)
app.config.from_object(__name__)

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Please Login to view this page...")
            return redirect(url_for('login_page'))
    return wrap

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g,'db',None)
    if db is not None:
        db.close()
        gc.collect()
        
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/')
def index():
    return redirect(url_for('login_page'))



@app.route('/login/', methods=["GET","POST"])
def login_page():
    try:
        if 'logged_in' in session:
            return redirect(url_for('buckets_page'))
        if request.method == "POST":
            
            username = request.form['username']
            password = request.form['password']
            
            cur = g.db.execute('select username,password from userdb where username=?',[username])
            row = cur.fetchone()  
            if row is None:                
                flash("Invalid Login, Please try again..")
                return render_template('login.html')            
            
            if sha256_crypt.verify(password, row[1]):
                session['logged_in'] = True
                session['username'] = username
                return redirect(url_for('buckets_page'))
            else:
                flash("Invalid Login, Please try again...")
                return render_template('login.html')
        else:
            return render_template('login.html')
    except Exception as e:
        flash(e)
        flash("Invalid login, Please try again")
        return render_template('login.html')
    
@app.route('/logintwitter/')
def twitterLogin():
    return twitter.authorize(callback=url_for('oauth_authorized',
        next = request.args.get('next') or request.referrer or None))

@app.route('/logout/')
@login_required
def logout():
    session.clear()
    flash("you have been succesfully logged out")
    return redirect(url_for('index'))

                        

@app.route('/register/',methods=['GET','POST'])
def register_page():
    try:
        if request.method == "POST":
            
            username = request.form['username']
            password = request.form['password']
            passconfirm = request.form['passconfirm']
            
            if password != passconfirm:
                flash("Passwords do not match")
                return render_template('register.html')
            
            
            cur = g.db.execute('select username from userdb where username=?',[username])
            
            rows = cur.fetchall()
            
            if len(rows) != 0 :
                flash('username already exists')
                return render_template('register.html')
            
            else:
                password = sha256_crypt.encrypt(request.form['password'])
                tableName = username
                g.db.execute('insert into userdb (username,password) values(?,?)',[username,password])                
                g.db.commit()
                flash("Thank you for registering, please login")
                return redirect(url_for('login_page'))
        else:
            return render_template('register.html')
    except Exception as e:
        flash(e)
        return render_template('register.html')
    
    
@app.route('/buckets/',methods=['GET','POST'])
@login_required
def buckets_page():
    try:
        username = session['username']
        if request.method == "POST":
            bucket = request.form['bucket']
            query = 'select listID from BucketListDB where username LIKE ' +'"'+ username +'"' + ' AND listID LIKE '+'"'+ bucket +'"'
            cur = g.db.execute(query)
            rows = cur.fetchall()
            if len(rows)==0:
                g.db.execute('insert into BucketListDB (username,ListID) values(?,?)',[username,bucket])
                g.db.commit()                
            else:
                flash("bucket list already exits")
                
        
        query = 'select listID from BucketListDB where username LIKE '+'"'+ username +'"'
        cur = g.db.execute(query)
        rows = cur.fetchall()
        bucket_ids=[]
        for bucket in rows:
            item = (bucket[0],bucket[0].replace(" ","_"),urllib.quote(bucket[0]))
            bucket_ids.append(item)
        return render_template('buckets.html', buckets = bucket_ids , username = username )
    except Exception as e:
        flash(e)
        return render_template('error.html')

@app.route('/deletebucket/',methods=['GET'])
@login_required
def deleteBucket():
    try:
        if request.method == "GET":
            username = str(request.args.get('username'))
            bucket = str(request.args.get('listID'))
            if session['username'] != username:
                flash("Invalid Request")
                return render_template('error.html')
            query = 'delete from BucketListDB where username like '+'"'+ username +'"'+ ' AND listID LIKE '+'"'+ bucket +'"'
            g.db.execute(query)
            query = 'delete from BucketListItemDB where username like '+'"'+ username +'"' + ' AND listID LIKE '+'"'+ bucket +'"'
            g.db.execute(query)
            g.db.commit()

            return redirect(url_for('buckets_page'))
        else:
            return redirect(url_for('index'))
    except Exception as e:
        flash(e)
        return render_template('error.html')

@app.route('/viewBucketList/',methods=['GET'])
def viewBuckets_page():
    try:
        if request.method == "GET":
            username = str(request.args.get('username'))
            bucket = str(request.args.get('listID'))        
            
            query = 'select listItem from BucketListItemDB where username like '+'"'+ username +'"' + ' AND listID LIKE '+'"'+ bucket +'"'
            cur = g.db.execute(query)
            rows = cur.fetchall()
            if 'logged_in' in session:
                return render_template('viewBucketList.html',bucket = bucket,bucketListItems = rows,loggedin = 1)
            else:
                return render_template('viewBucketList.html',bucket = bucket,bucketListItems = rows,loggedin = 0)
        else:
            return redirect(url_for('index'))
    except Exception as e:
        flash(e)
        return render_template('error.html')


@app.route('/editBucketListItem/',methods=['GET','POST'])
@login_required
def editBucketList_page():
    try:
        if request.method == "POST":
            ListItem = request.form['item']
            bucket = request.form['bucket']
            username = session['username']
            query = 'select ListItem from BucketListItemDB where listID like '+'"'+ bucket +'"'+ ' AND ListItem LIKE '+'"'+ ListItem +'"'
            cur = g.db.execute(query)
            rows = cur.fetchall()
            if len(rows)!=0:
                flash("list item already exists")
                return redirect(url_for('editBucketList_page',username=username, listID=bucket))
            else:
                g.db.execute('insert into BucketListItemDB (username,ListID,ListItem) values(?,?,?)',[username,bucket,ListItem])
                g.db.commit()
                return redirect(url_for('editBucketList_page',username=username, listID=bucket))
                
        else:
            username = str(request.args.get('username'))
            bucket = str(request.args.get('listID'))
            query = 'select listItem from BucketListItemDB where username like '+'"'+ username +'"' + ' AND listID LIKE '+'"'+ bucket +'"' 
            cur = g.db.execute(query)
            rows = cur.fetchall()
            bucket_url = urllib.quote(bucket)
            bucket_id = bucket.replace(" ","_")
            return render_template('editBucketList.html',bucket = bucket , ListItems = rows , username = username , bucket_id = bucket_id, bucket_url = bucket_url)
    except Exception as e:
        flash(e)
        return render_template('error.html')
    
@app.route('/deletebucketlistitem/',methods=['GET'])
@login_required
def deleteBucketListItem():
    try:
        username = session['username']
        bucket = str(request.args.get('ListID'))
        listItem = str(request.args.get('ListItem'))
        query = 'delete from BucketListItemDB where username like '+'"'+ username +'"' + ' AND ListID LIKE '+'"'+ bucket +'"'+ ' AND ListItem LIKE '+'"'+ listItem +'"'
        g.db.execute(query)
        g.db.commit()
        return redirect(url_for('editBucketList_page',username = username, listID = bucket))
    except Exception as e:
        flash(e)
        return render_template('error.html')
    
@app.route('/search/',methods=['GET','POST'])
@login_required
def searchBuckets():
    try:
        username = session['username']
        if request.method == "POST":
            searchQuery = request.form['query']
            sqlQuery = 'select ListID,ListItem from BucketListItemDB where ListID like '+'"%'+ searchQuery +'%"' + ' or ListItem LIKE '+'"%'+ searchQuery +'%"' 
            print sqlQuery
            cur = g.db.execute(sqlQuery)
            rows = cur.fetchall()
            print rows
            return render_template('searchList.html',rows = rows)
        return render_template('searchList.html')
    except Exception as e:
        flash(e)
        return render_template('error.html')
            
            
    
    
if __name__ == '__main__':
    app.run(debug = True)
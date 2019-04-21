from flask import Flask, render_template, session, request, redirect, flash
# import the function connectToMySQL from the file mysqlconnection.py
from mysqlconnection import connectToMySQL
import datetime
import re
from flask_bcrypt import Bcrypt
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
app = Flask(__name__)
app.secret_key = 'SecretsSecretsAreNoFun,SecretsSecretsHurtSomeone'
bcrypt = Bcrypt(app)
# invoke the connectToMySQL function and pass it the name of the database we're using
# connectToMySQL returns an instance of MySQLConnection, which we will store in the variable 'mysql'



def check_login():
    if 'id' not in session or session['id'] == None:
        return False
    return True

@app.route('/')
def index():
    if 'id' not in session:
        session['id'] = None
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    session.clear()
    messages = False
                ######## first name registration validation #######
    if len(request.form['first_name']) < 1:
        flash(f"<span style='color: red'>*Missing Field Required</span>", 'first_name')
        messages = True
    if len(request.form['first_name']) < 2:
        messages = True
        flash(f"<span style='color: red'>*First name must be 2+ characters</span>", 'first_name')

            ######## last name registration validation #######
    if len(request.form['last_name']) < 1:
        messages = True
        flash(f"<span style='color: red'>*Missing Field Required</span>", 'last_name')
    if len(request.form['last_name']) < 2:
        messages = True
        flash(f"<span style='color: red'>*Last name must be 2+ characters</span>", 'last_name')

            ######## email registration validation #######
    if len(request.form['email']) < 1:
        messages = True
        flash(f"<span style='color: red'>*Missing Field Required</span>", 'email')
    if not EMAIL_REGEX.match(request.form['email']):
        messages = True
        flash(f"<span style='color: red'>*Format Invalid for Email Address</span>", 'email')

            ######## password registration validation #######
    if len(request.form['password']) < 8:
        messages = True
        flash(f"<span style='color: red'>*Password must be atleast 8 characters</span>", 'password')
    if (request.form['confirmpassword'] != request.form['password']):
        messages = True
        flash(f"<span style='color: red'>*Passwords do not match</span>", 'confirmpassword')

              ######## email registration validation (if exists) #######
    emailQuery = "SELECT * FROM users WHERE email = %(email)s;"
    data = {"email" : request.form['email']}
    mysql = connectToMySQL("quotes")
    results = mysql.query_db(emailQuery, data)
    if results:
        flash(f"<span style='color: red'>*{request.form['email']} already exists. Try Again</span>", 'email')
    elif messages == True:
        return redirect('/')
    else:
        pw_hash = bcrypt.generate_password_hash(request.form['password'])  
        mysql = connectToMySQL("quotes")
        query = "INSERT INTO users (`first_name`,`last_name`,`email`, `password`, `created_at`, `updated_at`) VALUES (%(first_name)s, %(last_name)s, %(email)s, %(password_hash)s, %(created_at)s, %(updated_at)s );"
        data = {
            "first_name": request.form["first_name"],
            "last_name": request.form["last_name"],
            "email": request.form["email"],
            "password_hash": pw_hash,
            "created_at": datetime.datetime.now(),
            "updated_at" : datetime.datetime.now()
        }
        newUser = mysql.query_db(query, data)
        session['id'] = newUser
        print(session['id'], "register - SESSION")
        return redirect('/quotes')
    return redirect('/')

@app.route('/login', methods=['POST'])
def login():
    session.clear()
    if len(request.form['email']) < 1:
        flash(f"<span style='color: red'>*Missing Field Required</span>",'log_email')
    elif not EMAIL_REGEX.match(request.form['email']):
        flash(f"<span style='color: red'><br/>*Format Invalid for Email Address</span>", 'log_email')
    if len(request.form['password']) < 1:
        flash(f"<span style='color: red'>*Missing Field Required</span>",'log_password')
    mysql = connectToMySQL("quotes")
    query = "SELECT * FROM users WHERE email = %(email)s;"
    data = {"email" : request.form['email']}
    result = mysql.query_db(query, data)
    if result:
        if bcrypt.check_password_hash(result[0]['password'], request.form['password']):
            session['id'] = result[0]['id']
            return redirect('/quotes')
        else:
            flash(f"<span style='color: red'><br/>*Password Incorrect</span>", 'log_password')
            return render_template('index.html')
    else:
        flash(f"<span style='color: red'>*Email Doesn't Exist</span>", 'log_email')

    return redirect('/')

def countLikes(id):
    
    return redirect('/quotes')


@app.route('/like/<id>')
def like(id):

    print(id)
    mysql=connectToMySQL('quotes')
    query = "INSERT INTO likes (`user_id`, `quote_id`) VALUES (%(user_id)s, %(quote_id)s);"
    data = {
        "user_id" : session['id'],
        "quote_id" : id
    }
    mysql.query_db(query,data)
    countLikes(id)
    return redirect('/quotes')


@app.route('/quotes')
def quotes():
    if check_login():
        #query to get the header first name to display
        mysql = connectToMySQL('quotes')
        query = "SELECT users.first_name FROM users WHERE id = %(id)s;"
        data = {"id" : session['id']}
        name = mysql.query_db(query, data)
        firstName = name[0]['first_name']
      
        #query to get user for each quote
        mysql=connectToMySQL('quotes')
        query = "SELECT quotes.id AS idQ, users.id, users.first_name, quotes.created_at, quotes.quote, quotes.author, COUNT(likes.id) AS likes FROM users JOIN quotes ON users.id = quotes.user_id LEFT JOIN likes ON likes.quote_id = quotes.id GROUP BY quotes.id ORDER BY created_at DESC;"
        quote = mysql.query_db(query)
        
        return render_template('quotes.html', firstName=firstName, quote=quote)

    else:
        return redirect('/')


#query for delete button, only if session['id] == posted by user

@app.route("/delete/<id>")
def delete(id):
    print(id)

    #deletes likes from quote first, then.....
    mysql=connectToMySQL('quotes')
    query = "DELETE FROM likes WHERE quote_id = %(id)s;"
    data = {"id" : id}
    mysql.query_db(query, data)
    #deletes quote
    mysql=connectToMySQL('quotes')
    query = "DELETE FROM quotes WHERE id = %(id)s ;"
    data = {"id" : id}
    mysql.query_db(query,data)
    
    return redirect('/quotes')


@app.route('/quotes', methods=['POST'])
def newQuote():
    if check_login():
        if len(request.form['author']) < 3:
            flash(f"<span style='color: red'><br/>*Author name must contain at least 3 characters</span>", 'author')
            return redirect('/quotes')
        if len(request.form['quote']) < 3:
            flash(f"<span style='color: red'><br/>*All quotes must contain at least 3 characters</span>", 'quote')
            return redirect('/quotes')

        # add new quote  
        mysql = connectToMySQL('quotes')
        query = query = "INSERT INTO quotes (quotes.author, quotes.quote, user_id, created_at, updated_at) VALUES (%(author)s, %(quote)s, %(user_id)s, NOW(), NOW());"
        data = {
            "author" : request.form['author'],
            "quote" : request.form['quote'],
            "user_id" : session['id']
        }
        mysql.query_db(query,data)
        flash(f"<span style='color: green'><br/>*Quote Added successfully</span>", 'newquote')
        return redirect('/quotes')
    return redirect('/')

@app.route('/myaccount/<id>')
def myaccount(id):
    if check_login():
        #query to get the header first name to display
        mysql = connectToMySQL('quotes')
        query = "SELECT users.id, users.first_name, users.last_name, users.email FROM users WHERE id = %(id)s;"
        data = {"id" : session['id']}
        accountInfo = mysql.query_db(query, data)
        firstName = accountInfo[0]['first_name']
        lastName = accountInfo[0]['last_name']
        eMail = accountInfo[0]['email']
        return render_template('myaccount.html', firstName=firstName, lastName=lastName, eMail=eMail)
    else:
        return redirect('/')

@app.route('/update', methods=['POST'])
def update():
    if len(request.form['first_name']) < 1:
        flash(f"<span style='color: red'>*Required Field(s) Missing</span>", 'noupdate')
        return redirect('/myaccount/<id>')
    if len(request.form['last_name']) < 1:
        flash(f"<span style='color: red'>*Required Field(s) Missing</span>", 'noupdate')
        return redirect('/myaccount/<id>')
    if len(request.form['email']) < 1:
        flash(f"<span style='color: red'>*Required Field(s) Missing</span>", 'noupdate')
        return redirect('/myaccount/<id>')
    if not EMAIL_REGEX.match(request.form['email']):
        flash(f"<span style='color: red'>Not a Valid Email</span>", 'notemail')
        return redirect('/myaccount/<id>')
    else:
        mysql = connectToMySQL("quotes")
        query = "UPDATE users SET `first_name` = %(first_name)s, `last_name` = %(last_name)s, `email` = %(email)s WHERE (`id` = %(id)s);"
        data = {
            "first_name": request.form["first_name"],
            "last_name": request.form["last_name"],
            "email": request.form["email"],
            "id" : session['id']
        }
        mysql.query_db(query, data)
        flash(f"<span style='color: green'>*User Updated Successfully</span>", 'update')
        return redirect ('/myaccount/<id>')


@app.route('/user/<id>')
def viewUser(id):
    if check_login():
         #query to get the header first name to display
        mysql = connectToMySQL('quotes')
        query = "SELECT users.first_name, users.last_name, users.email FROM users WHERE id = %(id)s;"
        data = {"id" : session['id']}
        accountInfo = mysql.query_db(query, data)
        firstName = accountInfo[0]['first_name']

        #query to get all quotes posted by clicked on user
        mysql = connectToMySQL("quotes")
        query = "SELECT quotes.quote, quotes.author, users.first_name, quotes.created_at FROM users JOIN quotes ON users.id = quotes.user_id WHERE users.id = %(id)s;"
        data = {'id' : id}
        userQuotes = mysql.query_db(query, data)
        print(userQuotes)
       
        return render_template('user.html', firstName=firstName, userQuotes=userQuotes)
    else:
        return redirect('/')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True)


from flask import Flask, render_template, url_for, redirect, request
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pandas as pd

app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisissecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'
Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


database_path = "inventory.db"
engine = create_engine("sqlite:///" + database_path)

def format_query_view():
    # Path to sqlite
    # convert db query to list of list for simplicity
    result = engine.execute("SELECT * FROM Inventory")
    newresult = []
    for x in result:
        x = list(x)
        newresult.append(x)
    result = newresult

    new_results = []
    for row in result:
        locations = row[3].split("||")
        newrow = []
        for loc in locations:
            newrow = []
            for field in range(0, 8):
                if field == 3:
                    newrow.append(loc)
                    continue
                newrow.append(row[field])
            new_results.append(newrow)
    result = new_results
    mydata = pd.DataFrame(data=result, columns=["mrn", "upc", "sdy", "loc", "min", "max", "mfg", "desc"])

    locs = mydata["loc"].tolist()
    qtylist = []
    loclist = []
    for loc in locs:
        location = loc.split("|")[0]
        qty = loc.split("|")[1]
        qtylist.append(qty)
        loclist.append(location)
    mydata["loc"] = loclist
    mydata["qty"] = qtylist
    newdf = mydata[['mrn', 'upc', 'sdy', 'loc', 'qty', 'min', 'max', 'mfg', 'desc']]
    newdf.replace("nan", "", inplace=True)
    newdf = newdf.loc[newdf["desc"] != ""]
    listoflist = []
    for x in range(0, len(newdf)):
        listoflist.append(list(newdf.iloc[x].values))
    # newdf.iloc[0].values
    result = listoflist
    return (result)




def format_query_change():
    # Path to sqlite
    # convert db query to list of list for simplicity
    result = engine.execute("SELECT * FROM Inventory")
    print(result)
    newresult = []
    for x in result:
        x = list(x)
        newresult.append(x)
    result = newresult
    return (result)


#returns a list of results matching mystring
def search_string_view(mystring):
    result = format_query_view()

    #convert all to uppercase for consistancy
    resultupper = []
    for line in result:
        resultupper.append([str(field).upper() for field in line])
    result = resultupper

    #convert search string to upper
    mystring = mystring.upper()

    #check which parts include search term
    parts = []
    for line in result:
        if any(mystring in field for field in line):
            parts.append(line)
        
    parts_breaks = []
    #add breaks to list fields
    for x in parts:
        newline = [str(s).replace("||", "<br>") for s in x]
        parts_breaks.append(newline)
    parts = parts_breaks
    return (parts)

#returns a list of results matching mystring
def search_string_change(mystring):
    result = format_query_change()

    #convert all to uppercase for consistancy
    resultupper = []
    for line in result:
        resultupper.append([str(field).upper() for field in line])
    result = resultupper

    #convert search string to upper
    mystring = mystring.upper()

    #check which parts include search term
    parts = []
    for line in result:
        if any(mystring in field for field in line):
            parts.append(line)
        
    parts_breaks = []
    #add breaks to list fields
    for x in parts:
        newline = [str(s).replace("||", "<br>") for s in x]
        parts_breaks.append(newline)
    parts = parts_breaks
    return (parts)



class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')


class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=3, max=50)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=3, max=50)])

@app.route('/', methods=["POST", "GET"])
def index():
    result = format_query_view()
    results_found = ""
    current_term = ""
    #if searching, use filter function
    if request.method == "POST":
        search_term = request.form["searchterm"]
        parts = search_string_view(search_term)
        results_found = len(parts)
        current_term = search_term
    else:
        #convert results to uppercase for consistancy
        #this is the initial query showing all parts
        parts = []
        for x in result:
            parts.append([str(field).upper() for field in x])
        parts_breaks = []
        #add breaks to list fields
        for x in parts:
            newline = [str(s).replace("||", "<br>") for s in x]
            parts_breaks.append(newline)
        parts = parts_breaks    
    return render_template("index.html", parts=parts, current_term=current_term, results_found=results_found) 

@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('dashboard'))
        return 'Invalid Username or Password'
    return render_template('login.html', form=form)

@app.route('/signup', methods=["GET", "POST"])
def signup():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        # return '<h1>' + form.username.data + " " + form.password.data + form.email.data + "</h1>"
        auser = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(auser)
        db.session.commit()
        return 'new user has been created'
    return render_template('signup.html', form=form)

@app.route('/dashboard', methods=["POST", "GET"])
@login_required
def dashboard():
    console_msg = ""
    result = format_query_change()
    results_found = ""
    current_term = ""
    parts = []

    #display search results OR display all results
    if request.method == "POST":
        if "searchterm" in request.form:
            search_term = request.form["searchterm"]
            parts = search_string_change(search_term)
            results_found = len(parts)
            current_term = search_term
    if request.method == "GET":
        #
        # shows values on homepage when first loading
        #
        #convert results to uppercase for consistancy
        #this is the initial query showing all parts
        parts = []
        for x in result:
            parts.append([str(field).upper() for field in x])
        
        parts_breaks = []
        #add breaks to list fields

        for x in parts:
            newline = [str(s).replace("||", "<br>") for s in x]
            parts_breaks.append(newline)
        parts = parts_breaks

        #
        # handle changes to values
        #
        #
        #  Handle removing or adding to UPC or Alternate PN list
        #
        upc_checked = False
        sdy_checked = False
        theresults = request.args.to_dict()
        if len(request.args.to_dict().keys()) > 1:
            if any("upc_check" in x for x in theresults.keys()):
                for x in theresults.keys():
                    if "check" in x:
                        if theresults[x] == "on":
                            upc_checked = True 
            elif any("sdy_check" in x for x in theresults.keys()):
                for x in theresults.keys():
                    if "check" in x:
                        if theresults[x] == "on":
                            sdy_checked = True 

            if upc_checked:
                for x in theresults:
                    if "edit" in x:
                        removeval = theresults[x].upper()
                        pn = x.split("-")[1]
                        current_upc_list = engine.execute(f"SELECT upclist FROM inventory WHERE mrn = '{pn}';").first()[0]
                        if current_upc_list == "":
                            console_msg = "Nothing to remove"
                            return render_template("dashboard.html", parts=parts, current_term=current_term, results_found=results_found, console_msg=console_msg)

                        if "||" in current_upc_list:
                            current_upc_list = current_upc_list.split("||")
                            current_upc_list = [x.upper() for x in current_upc_list]
                        else:
                            current_upc_list = [current_upc_list.upper()]
                        try:
                            current_upc_list.remove(removeval)
                            new_upc_list = current_upc_list
                            new_upc_string = ""
                            
                            if len(new_upc_list) > 0:
                                for counter, x in enumerate(new_upc_list):
                                    if counter == len(new_upc_list)-1:
                                        new_upc_string = new_upc_string + x
                                        break
                                    new_upc_string = new_upc_string + x + "||"
                            else:
                                new_upc_string = ""
                            engine.execute(f"UPDATE inventory SET upclist = '{new_upc_string}' WHERE mrn = '{pn}';")
                            return redirect("/dashboard")
                        except Exception as error:
                            print(error)
                            console_msg = "Value not found in UPC list!"
                            return render_template("dashboard.html", parts=parts, current_term=current_term, results_found=results_found, console_msg=console_msg)
                            
            if sdy_checked:
                for x in theresults:
                    if "edit" in x:
                        removeval = theresults[x].upper()
                        pn = x.split("-")[1]
                        current_sdy_list = engine.execute(f"SELECT sdylist FROM inventory WHERE mrn = '{pn}';").first()[0]
                        if "||" in current_sdy_list:
                            current_sdy_list = current_sdy_list.split("||")
                            current_sdy_list = [x.upper() for x in current_sdy_list]
                        else:
                            current_sdy_list = [current_sdy_list.upper()]
                        try:
                            current_sdy_list.remove(removeval)
                            new_sdy_list = current_sdy_list
                            new_sdy_string = ""
                            print(len(new_sdy_list))
                            print("newsdylist")
                            if len(new_sdy_list) > 1:
                                for counter, x in enumerate(new_sdy_list):
                                    if counter == len(new_sdy_list)-1:
                                        new_sdy_string = new_sdy_string + x
                                        break
                                    new_sdy_string = new_sdy_string + x + "||"
                            else:
                                new_sdy_string = ""
                            engine.execute(f"UPDATE inventory SET sdylist = '{new_sdy_string}' WHERE mrn = '{pn}';")
                            return redirect("/dashboard")
                        except Exception as error:
                            print(error)
                            print(current_sdy_list)
                            console_msg = "Value not found in PN list!"
                            return render_template("dashboard.html", parts=parts, current_term=current_term, results_found=results_found, console_msg=console_msg)
        #
        #
        #   Handle adding / editing values 
        #
        #
        elif len(request.args.to_dict().keys()) == 1:
            for x in theresults:
                pn = x.split("-")[1]
                field = x.split("-")[0]
                newval = theresults[x]
            row_list = engine.execute(f"SELECT * FROM inventory WHERE mrn = '{pn}';").first()
            if field == "upc_edit":
                if newval in row_list[1]:
                    console_msg = newval + " is already tied to the pn " + pn
                    return render_template("dashboard.html", parts=parts, current_term=current_term, results_found=results_found, console_msg=console_msg)
                else:
                    current_upclist = row_list[1]
                    if current_upclist == "":
                        new_upclist = newval
                        engine.execute(f"UPDATE inventory SET upclist = '{new_upclist}' WHERE mrn = '{pn}'")
                    else:
                        new_upclist = current_upclist + "||" + newval
                        engine.execute(f"UPDATE inventory SET upclist = '{new_upclist}' WHERE mrn = '{pn}'")
                    return redirect("/dashboard")



            if field == "sdy_edit":
                if newval in row_list[2]:
                    console_msg = newval + " is already tied to the pn " + pn
                    return render_template("dashboard.html", parts=parts, current_term=current_term, results_found=results_found, console_msg=console_msg)
                else:
                    current_sdylist = row_list[2]
                    if current_sdylist == "":
                        new_sdylist = newval
                        engine.execute(f"UPDATE inventory SET sdylist = '{new_sdylist}' WHERE mrn = '{pn}';")
                    else:
                        new_sdylist = current_sdylist + "||" + newval
                        engine.execute(f"UPDATE inventory SET sdylist = '{new_sdylist}' WHERE mrn = '{pn}';")
                    return redirect("/dashboard")


            if field == "loc":
                if "|" not in newval:
                    console_msg = "You must enter new values in partnumber|vendor format."
                    return render_template("dashboard.html", parts=parts, current_term=current_term, results_found=results_found, console_msg=console_msg) 
                if newval in row_list[3]:
                    console_msg = newval + " is already tied to the pn " + pn
                    return render_template("dashboard.html", parts=parts, current_term=current_term, results_found=results_found, console_msg=console_msg)
                else:
                    current_loclist = row_list[3]
                    if current_loclist == "":
                        engine.execute(f"UPDATE inventory SET loclist = '{newval}' WHERE mrn = '{pn}';")
                        return redirect("/dashboard")
                    
                    #remove locations with 0 qty
                    newnewloclist = []
                    for x in current_loclist:
                        locs = x.split("||")
                        if locs[1] == 0:
                            continue
                        newnewloclist.append(locs[0] + "||" + locs[1])
                    new_loclist = newnewloclist
                    new_loclist = current_loclist + "||" + newval
                    engine.execute(f"UPDATE inventory SET loclist = '{new_loclist}' WHERE mrn = '{pn}';")
                    return redirect("/dashboard")


            
            if field == "max":
                currentmax = row_list[5]
                if (int(currentmax) < int(row_list[4])):
                    console_msg = "Max cannot be less than min for pn " + pn + "!"
                    return render_template("dashboard.html", parts=parts, current_term=current_term, results_found=results_found, console_msg=console_msg)
                try:
                    newval = int(newval)
                    engine.execute(f"UPDATE inventory SET max = {newval} WHERE mrn = '{pn}';")
                    return(redirect("/dashboard"))
                except:
                    console_msg = "Value for max must be an integer!"
                    return render_template("dashboard.html", parts=parts, current_term=current_term, results_found=results_found, console_msg=console_msg)

            if field == "min":
                try:
                    newval = int(newval)
                except:
                    console_msg = "Value for min must be an integer!"
                    return render_template("dashboard.html", parts=parts, current_term=current_term, results_found=results_found, console_msg=console_msg)    
                if newval < 0:
                    console_msg = "Value for min must be greater than 0!"
                    return render_template("dashboard.html", parts=parts, current_term=current_term, results_found=results_found, console_msg=console_msg)   
                elif newval > int(row_list[5]):
                    console_msg = "Value for min must be less than Max!"
                    return render_template("dashboard.html", parts=parts, current_term=current_term, results_found=results_found, console_msg=console_msg)                                                       
                else:
                    engine.execute(f"UPDATE inventory SET min = {newval} WHERE mrn = '{pn}';")
                    return(redirect("/dashboard"))
            
            if field == "mfg":
                engine.execute(f"UPDATE inventory SET mfg = '{newval}' WHERE mrn = '{pn}';")
                return(redirect("/dashboard"))  

            if field == "desc":
                engine.execute(f"UPDATE inventory SET desc = '{newval}' WHERE mrn = '{pn}';")
                return(redirect("/dashboard"))  
        else:
            pass
    return render_template('dashboard.html', parts=parts, current_term=current_term, results_found=results_found, console_msg=console_msg) 

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, render_template, redirect, request, session
from flask_session import Session
from tempfile import mkdtemp
import sqlite3
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash

# Configure app
app = Flask(__name__)

conn = sqlite3.connect("database.db")
cur = conn.cursor()
cur.execute(
    "CREATE TABLE IF NOT EXISTS users (user_id INTEGER, username TEXT, hash TEXT, PRIMARY KEY(user_id))"
)
cur.execute(
    "CREATE TABLE IF NOT EXISTS blog (blog_id INTEGER, title TEXT, para TEXT, anchor TEXT, hyperlink TEXT, PRIMARY KEY(blog_id))"
)
cur.execute(
    "CREATE TABLE IF NOT EXISTS blogsite (blogsite_id INTEGER, blogname TEXT, about TEXT, media TEXT, medialink TEXT, PRIMARY KEY(blogsite_id))"
)
conn.commit()

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


def login_required(f):
    # Decorate routes to require login. https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


# Create route for the homepage
@app.route("/", methods=["GET", "POST"])
def index():
    # Connet to sql database
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM blogsite")
    blogsite_data = cur.fetchall()

    # Check whether the blogsite is newly hosted
    if len(blogsite_data) == 0:
        cur.execute(
            "INSERT INTO blogsite (blogname, about, media, medialink) VALUES('Blog Site', 'Sample about text', 'Update blog and about', '/settings')"
        )
    conn.commit()

    # If newly hosted, fill blogsite with dummy data
    blog_data = []
    blog_id = 1
    blog_title = "Sample Title"
    paragraphs = ["Sample paragraph 1", "Sample Paragraph 2"]
    blog_anchor = "Add article by Log in"
    blog_hyperlink = "/login"
    cur.execute("SELECT blogname FROM blogsite WHERE blogsite_id = 1")
    blogname_data = cur.fetchall()
    blogname = blogname_data[0][0]

    # Create logic to navigate through the blogs
    if request.method == "POST":
        if (
            not request.form.get("blog_id_decrement")
            and not request.form.get("blog_id_increment")
            and not request.form.get("blog_id")
        ):
            return render_template(
                "index.html",
                blogname=blogname,
                blog_id=blog_id,
                blog_title=blog_title,
                paragraphs=paragraphs,
                blog_anchor=blog_anchor,
                blog_hyperlink=blog_hyperlink,
            )

        # Navigate to the previous blog
        if request.form.get("blog_id_decrement"):
            blog_id = int(request.form.get("blog_id_decrement")) - 1
            cur.execute("SELECT * FROM blog WHERE blog_id = ?", (blog_id,))
            blog_data = cur.fetchall()
            if len(blog_data) == 0:
                blog_id = blog_id + 1
            cur.execute("SELECT * FROM blog WHERE blog_id = ?", (blog_id,))
            blog_data = cur.fetchall()
            if len(blog_data) == 0:
                return render_template(
                    "index.html",
                    blogname=blogname,
                    blog_id=blog_id,
                    blog_title=blog_title,
                    paragraphs=paragraphs,
                    blog_anchor=blog_anchor,
                    blog_hyperlink=blog_hyperlink,
                )

        # Navigate to the next blog
        if request.form.get("blog_id_increment"):
            blog_id = int(request.form.get("blog_id_increment")) + 1
            cur.execute("SELECT * FROM blog WHERE blog_id = ?", (blog_id,))
            blog_data = cur.fetchall()
            if len(blog_data) == 0:
                blog_id = blog_id - 1
            cur.execute("SELECT * FROM blog WHERE blog_id = ?", (blog_id,))
            blog_data = cur.fetchall()
            if len(blog_data) == 0:
                return render_template(
                    "index.html",
                    blogname=blogname,
                    blog_id=blog_id,
                    blog_title=blog_title,
                    paragraphs=paragraphs,
                    blog_anchor=blog_anchor,
                    blog_hyperlink=blog_hyperlink,
                )

        # Fill the page with requested blogs paragraph
        if request.form.get("blog_id"):
            blog_id = int(request.form.get("blog_id"))
            cur.execute("SELECT * FROM blog WHERE blog_id = ?", (blog_id,))
            blog_data = cur.fetchall()

        blog_id = blog_data[0][0]
        blog_title = blog_data[0][1]
        blog_paragraph = blog_data[0][2]
        paragraphs = blog_paragraph.split("**++**")
        blog_anchor = blog_data[0][3]
        blog_hyperlink = blog_data[0][4]

        cur.execute("SELECT blogname FROM blogsite WHERE blogsite_id = 1")
        blogname_data = cur.fetchall()
        blogname = blogname_data[0][0]
        return render_template(
            "index.html",
            blogname=blogname,
            blog_id=blog_id,
            blog_title=blog_title,
            paragraphs=paragraphs,
            blog_anchor=blog_anchor,
            blog_hyperlink=blog_hyperlink,
        )

    # If the website has data already (Not newly hosted), fetch the first blog
    else:
        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute("SELECT * FROM blog WHERE blog_id = 1")
        blog_data = cur.fetchall()
        if len(blog_data) == 0:
            return render_template(
                "index.html",
                blogname=blogname,
                blog_id=blog_id,
                blog_title=blog_title,
                paragraphs=paragraphs,
                blog_anchor=blog_anchor,
                blog_hyperlink=blog_hyperlink,
            )

        blog_id = blog_data[0][0]
        blog_title = blog_data[0][1]
        blog_paragraph = blog_data[0][2]
        paragraphs = blog_paragraph.split("**++**")
        blog_anchor = blog_data[0][3]
        blog_hyperlink = blog_data[0][4]

        cur.execute("SELECT blogname FROM blogsite WHERE blogsite_id = 1")
        blogname_data = cur.fetchall()
        blogname = blogname_data[0][0]
        return render_template(
            "index.html",
            blogname=blogname,
            blog_id=blog_id,
            blog_title=blog_title,
            paragraphs=paragraphs,
            blog_anchor=blog_anchor,
            blog_hyperlink=blog_hyperlink,
        )


# About page route that fetches about info from the database
@app.route("/about", methods=["GET", "POST"])
def about():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM blogsite WHERE blogsite_id = 1")
    blogname_data = cur.fetchall()
    blogname = blogname_data[0][1]
    about = blogname_data[0][2]
    media = blogname_data[0][3]
    medialink = blogname_data[0][4]
    return render_template(
        "about.html", blogname=blogname, about=about, media=media, medialink=medialink
    )


# Settings page showing different links to the settings
@app.route("/settings", methods=["GET", "POST"])
@login_required
def update():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM blogsite WHERE blogsite_id = 1")
    blogname_data = cur.fetchall()
    blogname = blogname_data[0][1]
    return render_template("settings.html", blogname=blogname)


# Add a new blog to the databse through the add setting
@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    para_num_list = range(1, 11)
    para_name_list = []
    cur.execute("SELECT * FROM blogsite WHERE blogsite_id = 1")
    blogname_data = cur.fetchall()
    blogname = blogname_data[0][1]

    # Obtain number of paragraphs, title and other info from the author
    if request.method == "POST":
        if not request.form.get("paraNumber") and not request.form.get("num_of_para"):
            return render_template(
                "add.html",
                blogname=blogname,
                error_message="Fill all entries, now start again!",
                para_num_list=para_num_list,
                para_num_got="no",
            )
        if not request.form.get("paraNumber") or not request.form.get("num_of_para"):
            if request.form.get("paraNumber"):
                for i in range(1, int(request.form.get("paraNumber")) + 1):
                    para_name_list.append("paragraph_" + str(i))
                num_of_para = request.form.get("paraNumber")
                return render_template(
                    "add.html",
                    blogname=blogname,
                    error_message="",
                    paras=para_name_list,
                    num_of_para=num_of_para,
                    para_num_got="yes",
                )
            else:
                num_of_para = len(para_num_list)
                num_of_para = request.form.get("num_of_para")
                for i in range(1, int(request.form.get("num_of_para")) + 1):
                    para_name_list.append("paragraph_" + str(i))

                if (
                    not request.form.get("title")
                    or not request.form.get("read_more_title")
                    or not request.form.get("read_more_link")
                ):
                    return render_template(
                        "add.html",
                        blogname=blogname,
                        error_message="Fill all entries!",
                        paras=para_name_list,
                        num_of_para=num_of_para,
                        para_num_got="yes",
                    )
                for para_name in para_name_list:
                    if not request.form.get(para_name):
                        return render_template(
                            "add.html",
                            blogname=blogname,
                            error_message="Fill all entries!",
                            paras=para_name_list,
                            num_of_para=num_of_para,
                            para_num_got="yes",
                        )

                para_text = ""
                for para_name in para_name_list:
                    para_text = para_text + request.form.get(para_name) + "**++**"
                para_list_temp = para_text.split("**++**")
                para_list_temp.pop()
                para_text = "**++**".join(para_list_temp)

                cur.execute(
                    "INSERT INTO blog (title, para, anchor, hyperlink) VALUES(?, ?, ?, ?)",
                    (
                        request.form.get("title"),
                        para_text,
                        request.form.get("read_more_title"),
                        request.form.get("read_more_link"),
                    ),
                )
                conn.commit()
                return render_template(
                    "add.html",
                    blogname=blogname,
                    error_message="You have succefully added last article. Add more or go to settings!",
                    para_num_list=para_num_list,
                    para_num_got="no",
                )

    # Show the add page previous to obtaining blog data
    else:
        return render_template(
            "add.html",
            blogname=blogname,
            para_num_list=para_num_list,
            para_num_got="no",
        )


# Login the admin (user) so that he can access the settings
@app.route("/login", methods=["GET", "POST"])
def login():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM users")
    user_data = cur.fetchall()
    if not len(user_data) > 0:
        return redirect("/register")
    cur.execute("SELECT * FROM blogsite WHERE blogsite_id = 1")
    blogname_data = cur.fetchall()
    blogname = blogname_data[0][1]

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template(
                "login.html",
                blogname=blogname,
                error_message="Invalid username, try again!",
            )

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template(
                "login.html",
                blogname=blogname,
                error_message="Invalid password, try again!",
            )

        # Query database for username
        cur.execute(
            "SELECT * FROM users WHERE username = ?", (request.form.get("username"),)
        )
        data = cur.fetchall()

        # Ensure username exists and password is correct
        if len(data) != 1 or not check_password_hash(
            data[0][2], request.form.get("password")
        ):
            return render_template(
                "login.html",
                blogname=blogname,
                error_message="Username and passwordn doesn't match, try again!",
            )

        # Remember which user has logged in
        session["user_id"] = data[0][1]

        # Redirect user to home page
        return redirect("/settings")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        if session.get("user_id"):
            return redirect("/settings")
        session.clear()
        return render_template("login.html", blogname=blogname)


@app.route("/logout")
def logout():
    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


# Register a new user (the admin) for the newly hosted blog site
@app.route("/register", methods=["GET", "POST"])
def register():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM blogsite WHERE blogsite_id = 1")
    blogname_data = cur.fetchall()
    blogname = blogname_data[0][1]
    if request.method == "POST":
        if (
            not request.form.get("username")
            or not request.form.get("password")
            or not request.form.get("passwordRepeat")
        ):
            return render_template(
                "register.html",
                blogname=blogname,
                error_message="Fill all entries and submit!",
            )

        elif request.form.get("password") != request.form.get("passwordRepeat"):
            print("4")
            return render_template(
                "register.html",
                blogname=blogname,
                error_message="The repeated password don't match, try again!",
            )

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute(
            "SELECT username FROM users WHERE username=?",
            (request.form.get("username"),),
        )
        data = cur.fetchall()
        if len(data) > 0:
            print("5")
            return render_template(
                "register.html",
                blogname=blogname,
                error_message="Username already taken, try again!",
            )

        cur.execute(
            "INSERT INTO users (username, hash) VALUES(?, ?)",
            (
                request.form.get("username"),
                generate_password_hash(request.form.get("password")),
            ),
        )
        conn.commit()

        return redirect("/login")

    else:
        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM users")
        data = cur.fetchall()
        if len(data) > 0:
            return redirect("/login")
        else:
            return render_template("register.html", blogname=blogname)


# Update the website name
@app.route("/blogname", methods=["GET", "POST"])
@login_required
def blogname():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM blogsite WHERE blogsite_id = 1")
    blogname_data = cur.fetchall()
    blogname = blogname_data[0][1]

    # Logic to update the name
    if request.method == "POST":
        if not request.form.get("blogname"):
            return render_template(
                "blogname.html",
                blogname=blogname,
                error_message="Type the name correctly",
            )

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute(
            "UPDATE blogsite SET blogname = ? WHERE blogsite_id = 1",
            (request.form.get("blogname"),),
        )
        conn.commit()

        return redirect("/settings")

    # Entry fields to update the website name
    else:
        return render_template("blogname.html", blogname=blogname)


# Update the about data
@app.route("/updateabout", methods=["GET", "POST"])
@login_required
def updateabout():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM blogsite WHERE blogsite_id = 1")
    blogname_data = cur.fetchall()
    blogname = blogname_data[0][1]

    # Obtain the updated data
    if request.method == "POST":
        if (
            not request.form.get("updateabout")
            or not request.form.get("updatemedia")
            or not request.form.get("updatemedialink")
        ):
            return render_template(
                "updateabout.html", blogname=blogname, error_message="Fill all entries!"
            )

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute(
            "UPDATE blogsite SET about =?, media = ?, medialink = ? WHERE blogsite_id = 1",
            (
                request.form.get("updateabout"),
                request.form.get("updatemedia"),
                request.form.get("updatemedialink"),
            ),
        )
        conn.commit()

        return redirect("/about")
    # Show the updating field entries
    else:
        return render_template(
            "updateabout.html",
            blogname=blogname,
        )


# Delete setting to delete blogs
@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    if request.method == "POST":
        if request.form.get("blog_id"):
            cur.execute(
                "DELETE from blog WHERE blog_id = ?", (request.form.get("blog_id"),)
            )
            conn.commit()

        return redirect("/delete")

    # show all the article and arrange in order
    else:
        cur.execute("SELECT blog_id, title FROM blog")
        blog_data = cur.fetchall()
        cur.execute("SELECT * FROM blogsite WHERE blogsite_id = 1")
        blogname_data = cur.fetchall()
        blogname = blogname_data[0][1]
        return render_template("delete.html", blogname=blogname, blog_data=blog_data)


if __name__ == "__main__":
    app.run(debug=True)

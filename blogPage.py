from functools import wraps
from flask import Flask, render_template, request, url_for, flash, abort
from flask_ckeditor import CKEditor
from flask_ckeditor.utils import cleanify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import redirect
import datetime
from flask_bootstrap import Bootstrap
from forms import NewPostForm, RegisterForm, LoginForm, CommentForm
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_gravatar import Gravatar


TODAY = datetime.date.today() #Date object


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base) #Create object with declarative base


login_manager = LoginManager()

blog = Flask(__name__, static_folder='static', template_folder='templates')

blog.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///posts.db"
blog.config['SECRET_KEY'] ="MySuperDuperSecretKey"
blog.config['CKEDITOR_PKG_TYPE'] = 'basic' #CKEditor package type
db.init_app(blog)  #Initialize the SQLAchemy
ckeditor = CKEditor(blog) #Initialize CKEditor
bootstrap = Bootstrap(blog) #Initialize/install bootstrap
login_manager.init_app(blog)
gravatar = Gravatar(blog,
                    size=30,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)


class User(UserMixin, db.Model): #User table
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
#One-to-many relationships, one user can have multiple POST and COMMENTS
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comments", back_populates="comment_author")


class BlogPost(db.Model): #Blogpost table
    id = db.Column(db.Integer, primary_key = True, nullable=False, unique=True)
    title = db.Column(db.String(250), nullable=False, unique=True)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text(), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    #Many-to-one relationship from USER who can have multiple posts
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = relationship("User", back_populates="posts")
    #One-to-many relationship one blog-post can have multiple COMMENTS
    comments = relationship("Comments", back_populates="parent_post")


    # def serialize(self): #In unlikely case of Api this sh**
    #     return {column.name : getattr(self, column.name) for column in self.__table__.columns}
    #        #Column name     :            Column Value    for every column in the self(Your own) table column


class Comments(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    text = db.Column(db.Text, nullable=False)

#Many-to-one relationship one USER can have multiple comments
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    comment_author = relationship("User", back_populates="comments")
#Many-to-one relationship one BLOG-POST can have multiple comments
    post_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'))
    parent_post = relationship("BlogPost", back_populates="comments")


# with blog.app_context(): #Run when need to create table
#     db.create_all()   #Table created

def admin_only(func):
    @wraps(func)
    def wrap_it(*args, **kwargs):
        if current_user.id == 1:
            return func(*args, **kwargs)
        else:
            abort(403)
    return wrap_it


@blog.route("/")
def home_page():
    data = db.session.query(BlogPost).all()
    return render_template("./index.html", data = data, logged_in=current_user.is_authenticated) #Blogs showing from DB


@blog.route("/about")
def about_page():
    return render_template("./about.html", logged_in=current_user.is_authenticated)


@blog.route("/contact")
def contact_page():
    return render_template("./contact.html", logged_in=current_user.is_authenticated)


@blog.route("/post/<int:blog_id>", methods=["GET", "POST"]) #Click on post, get post
def post(blog_id):
    clicked_post = db.session.query(BlogPost).get(blog_id) #DONE
    form = CommentForm()
    if request.method == "POST":
        if current_user.is_authenticated:
            comment = cleanify(request.form.get("comment"))#CKeditor field
            new_comment = Comments(
                text = comment,
                author_id = current_user.id,
                post_id = blog_id,
            )
            db.session.add(new_comment)
            db.session.commit()
            return redirect(url_for("post", blog_id=blog_id))
        else:
            flash("Please login first.")
            return redirect(url_for("login"))

    return  render_template("post.html", post_data=clicked_post, logged_in=current_user.is_authenticated,
                            form=form)


@blog.route("/message_sent", methods = ["GET", "POST"])
def receive_data(): #Contact form data receiver
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        message = request.form["message"]
        user_data = {"name" : name, "email" : email, "phone" : phone, "message" : message}
        #Call send_email method here.
        return render_template("message_success.html", user_data = user_data)
    return render_template("contact.html", logged_in=current_user.is_authenticated)


@blog.route("/create_post", methods = ["GET", "POST"])
@login_required
@admin_only
def create_post():
    global TODAY
    form = NewPostForm()
    if request.method == "POST":
        title = request.form.get("title")
        date = TODAY
        body = cleanify(request.form.get("body"))
        img_url = request.form.get("img_url")
        subtitle = request.form.get("subtitle")
        new_post = BlogPost(
            title = title,
            date = date,
            body = body,
            img_url = img_url,
            subtitle = subtitle,
            author_id = current_user.name,
                            )

        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('home_page'))
    return render_template("create_post.html", form=form, logged_in=current_user.is_authenticated)




@blog.route("/edit_post/<int:blog_id>", methods = ["GET", "POST"])
@login_required
@admin_only
def edit_post(blog_id):

    required_post = db.session.query(BlogPost).get(blog_id)
    edit_form = NewPostForm(
        title = required_post.title,
        body = required_post.body,

        img_url = required_post.img_url,
        subtitle = required_post.subtitle,
    )

    if request.method == "GET":
        return render_template("edit_post.html", form = edit_form, logged_in=current_user.is_authenticated)
    elif request.method == "POST":
        title: str = request.form.get("title")
        body: str = cleanify(request.form.get("body"))

        img_url: str = request.form.get("img_url")
        subtitle: str = request.form.get("subtitle")

        required_post.title = title #New values from form and commit to db
        required_post.body=body

        required_post.img_url=img_url
        required_post.subtitle=subtitle
        db.session.commit()
    return redirect(url_for('post', blog_id=blog_id))


@blog.route("/delete/<int:blog_id>")
@admin_only
def delete_post(blog_id):
    post_to_delete = db.session.query(BlogPost).get(blog_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('home_page'))

@blog.route("/login", methods = ["GET", "POST"])
def login():
    form = LoginForm()

    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()  # Find user by email entered by user

        if user is not None:  # It means email matched
            # Check stored password hash against entered password hashed.
            if check_password_hash(user.password, password):
                login_user(user)
                if current_user.id == 1:
                    flash("Administrator have successfully logged in.")
                    return redirect(url_for('home_page'))
                flash("You have successfully logged in.")
                return redirect(url_for('home_page'))
            else:
                flash("Incorrect Password")
                return redirect(url_for("login"))
        else:  # No email matched
            flash("Incorrect email")
    return render_template("login.html",form=form, logged_in=current_user.is_authenticated)

@blog.route("/register", methods = ["GET", "POST"])
def register():
    form = RegisterForm()
    if request.method == "POST":
        email = request.form.get("email")
        if User.query.filter_by(email=email).first():
            flash("User already exists.")
            return redirect(url_for("login"))
        else:
            new_user = User(
                name=request.form.get("name"), #Pycharm giving unexpected arguments here, Why??
                email=email,
                password=generate_password_hash(password=request.form.get("password"), method="pbkdf2:sha256")
            )
            db.session.add(new_user)  # Add user
            db.session.commit()  # Add in to db
            login_user(new_user)
            flash("You have successfully logged in. Happy commenting")
            return redirect(url_for("home_page"))
    return render_template("register.html", form=form, logged_in=current_user.is_authenticated)

@blog.route("/log_out")
def log_out():
    logout_user()
    flash("You have successfully logged out.")
    return redirect(url_for("home_page"))




#def send_email() #TODO: Contact form SMTP lib send email







if __name__ == "__main__":
    blog.run(debug=True)
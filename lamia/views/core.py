from lamia import login_manager
from lamia import app, bcrypt
from lamia.parsers import ForumPostParser
from collections import OrderedDict
from lamia.forms.core import LoginForm, RegistrationForm, ForgotPasswordForm, ResetPasswordForm
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash, session, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from lamia.utilities import get_top_frequences, scrub_json, humanize_time, ForumHTMLCleaner, parse_search_string_return_q, parse_search_string
from lamia.email_utilities import send_mail_w_template
from mongoengine.queryset import Q
from wand.image import Image
from werkzeug import secure_filename, urls
import arrow, mimetypes, json, os, hashlib, time, StringIO
from lamia.views.dashboard import broadcast
from ipwhois import IPWhois
import urllib, urllib2
import HTMLParser
from werkzeug.exceptions import default_exceptions, HTTPException
from  werkzeug.debug import get_current_traceback
from lamia import sqla
from flask_login import AnonymousUserMixin
import lamia.sqlmodels as sqlm
import pytz
import math, random, time
from os import path
import os

class Anonymouse(AnonymousUserMixin):
    login_name = None
    is_admin = False
    no_images = False
    id = None
    is_mod = False

login_manager.login_view = "sign_in"
login_manager.anonymous_user = Anonymouse

@app.before_request
def make_session_permanent():
    session.permanent = True

@app.before_request
def add_canonical_url():
    request.canonical = app.config['BASE'] + request.path

@app.before_request
def check_ip_ban():
    if request.path != "/banned" and not request.path.startswith("/static/"):
        try: # TODO : wat
            ip_address = sqla.session.query(sqlm.IPAddress).filter_by(ip_address=request.remote_addr, banned=True)[0]
            return redirect("/banned", 307)
        except:
            sqla.session.rollback()
            pass

@app.errorhandler(500)
def server_error(e):
    traceback = get_current_traceback()
    l = sqlm.SiteLog()
    l.method = request.method
    l.path = request.path
    l.ip_address = request.remote_addr
    l.agent_platform = request.user_agent.platform
    l.agent_browser = request.user_agent.browser
    l.agent_browser_version = request.user_agent.version
    l.agent = request.user_agent.string
    l.time = arrow.utcnow().datetime

    try:
        if current_user.is_authenticated():
            l.user = current_user
    except:
        pass

    if isinstance(e, HTTPException):
        description = unicode(e.get_description(request.environ))
        code = unicode(e.code)
        name = unicode(e.name)
    else:
        description = "Shit... Something's broken!"
        code = unicode(500)
        name = "Server Error."

    l.error = True
    l.error_name = name
    l.error_code = code
    l.error_description = description + "\n\n" + traceback.plaintext

    try:
        sqla.session.add(l)
        sqla.session.commit()
    except:
        sqla.session.rollback()

    return render_template('500.jade', page_title="SERVER ERROR! - %%GENERIC SITENAME%%"), 500

@app.errorhandler(403)
def unauthorized_access(e):
    traceback = get_current_traceback()
    l = sqlm.SiteLog()
    l.method = request.method
    l.path = request.path
    l.ip_address = request.remote_addr
    l.agent_platform = request.user_agent.platform
    l.agent_browser = request.user_agent.browser
    l.agent_browser_version = request.user_agent.version
    l.agent = request.user_agent.string
    l.time = arrow.utcnow().datetime

    try:
        if current_user.is_authenticated():
            l.user = current_user
    except:
        pass

    if isinstance(e, HTTPException):
        description = unicode(e.get_description(request.environ))
        code = unicode(e.code)
        name = unicode(e.name)
    else:
        description = "Page not found."
        code = unicode(403)
        name = "Page Not Found."

    l.error = True
    l.error_name = name
    l.error_code = code
    l.error_description = description

    try:
        sqla.session.add(l)
        sqla.session.commit()
    except:
        sqla.session.rollback()

    return render_template('403.jade', page_title="Page Not Found - %%GENERIC SITENAME%%"), 403

@app.errorhandler(404)
def page_not_found(e):
    traceback = get_current_traceback()
    l = sqlm.SiteLog()
    l.method = request.method
    l.path = request.path
    l.ip_address = request.remote_addr
    l.agent_platform = request.user_agent.platform
    l.agent_browser = request.user_agent.browser
    l.agent_browser_version = request.user_agent.version
    l.agent = request.user_agent.string
    l.time = arrow.utcnow().datetime

    try:
        if current_user.is_authenticated():
            l.user = current_user
    except:
        pass

    if isinstance(e, HTTPException):
        description = unicode(e.get_description(request.environ))
        code = unicode(e.code)
        name = unicode(e.name)
    else:
        description = "Page not found."
        code = unicode(404)
        name = "Page Not Found."

    l.error = True
    l.error_name = name
    l.error_code = code
    l.error_description = description

    try:
        sqla.session.add(l)
        sqla.session.commit()
    except:
        sqla.session.rollback()

    return render_template('404.jade', page_title="Page Not Found - %%GENERIC SITENAME%%"), 404

@app.route('/under-construction')
def under_construction():
    return render_template("under_construction.jade", page_title="We're working on the site!")

# TODO link this to the db
if app.settings_file.get("lockout_on", False):
    @app.before_request
    def lockdown_site():
        if not (request.path == "/under-construction" or request.path == "/sign-in" or "/static" in request.path):
            if current_user.is_authenticated() and (current_user.is_admin or current_user.is_allowed_during_construction):
                pass
            else:
                return redirect("/under-construction")

@app.before_request
def intercept_banned():
    if current_user.is_authenticated():
        if current_user.banned and not (request.path == "/banned" or request.path == "/sign-out" or "/static" in request.path):
            return redirect("/banned")

@app.context_processor
def inject_notification_count():
    c = current_user
    try:
        if c.is_authenticated():
            return dict(notification_count=c._get_current_object().get_notification_count())
        else:
            return dict(notification_count=0)
    except:
        return dict(notification_count=0)

_client_template_cache = {} # TODO : obviously this is not thread safe
@app.context_processor
def inject_theme_coffee_templates():
    c = current_user
    my_coffee_template_overrides={}
    if c.is_authenticated():
        if c.theme and c.theme.directory_name:
            coffee_tmpl_override_path = path.join(app.config["DEFAULT_TEMPLATE_DIR"], "themes", current_user.theme.directory_name, "_coffee")
            if path.exists(coffee_tmpl_override_path):
                for tmpl in os.listdir(coffee_tmpl_override_path):
                    my_coffee_template_overrides[tmpl.replace(".html", "")] = open(path.join(coffee_tmpl_override_path, tmpl)).read()
    
    return dict(theme_coffee_templates=my_coffee_template_overrides)

@app.before_request
def log_request():
    if not request.path.startswith("/admin/") and not request.path.startswith("/static/"):
        l = sqlm.SiteLog()
        l.method = request.method
        l.path = request.path
        l.ip_address = request.remote_addr
        l.agent_platform = request.user_agent.platform
        l.agent_browser = request.user_agent.browser
        l.agent_browser_version = request.user_agent.version
        l.agent = request.user_agent.string
        l.time = arrow.utcnow().datetime.replace(tzinfo=None)

        try:
            if current_user.is_authenticated():
                l.user = current_user
            sqla.session.add(l)
            sqla.session.commit()
        except:
            sqla.session.rollback()

@app.route('/get-user-info-api', methods=['POST',])
def get_user_info_api():
    request_json = request.get_json(force=True)
    user_name = urls.url_decode(request_json.get("user"))
    user_name = user_name.keys()[0]
    user_name = urllib2.unquote(user_name)

    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=user_name)[0]
    except:
        return app.jsonify(data=False)

    try:
        last_at = user.last_seen_at
        last_url = user.last_at_url
    except:
        last_at = False
        last_url = ""

    if arrow.get(user.last_seen).datetime < arrow.utcnow().replace(hours=-1).datetime:
        last_at = False

    try:
        recent_status = sqla.session.query(sqlm.StatusUpdate) \
            .filter_by(author=user) \
            .filter(sqlm.StatusUpdate.attached_to_user == None) \
            .order_by(sqla.desc(sqlm.StatusUpdate.created))[0]
        recent_status_update = recent_status.message
        recent_status_update_id = recent_status.id
    except IndexError:
        recent_status_update = False
        recent_status_update_id = False

    return app.jsonify(
        avatar_image=user.get_avatar_url("60"),
        avatar_x=user.avatar_60_x,
        avatar_y=user.avatar_60_y,
        name=user.display_name,
        login_name=user.my_url,
        last_seen=humanize_time(user.last_seen),
        last_seen_at=last_at,
        last_seen_url=last_url,
        recent_status_message_id=recent_status_update_id,
        recent_status_message=recent_status_update,
        joined=humanize_time(user.joined, "MMM D YYYY"),
        roles=user.get_roles()
    )

@app.route('/change-theme/<id>', methods=['POST'])
@login_required
def change_theme(id):
    user = current_user

    try:
        theme = sqlm.SiteTheme.query.filter_by(id=id)[0]
    except IndexError:
        return abort(404)

    user.theme = theme
    user.theme_last_updated = time.time()
    return app.jsonify(url="/")

@app.route('/make-report', methods=['POST'])
@login_required
def make_report():
    request_json = request.get_json(force=True)

    _type = request_json.get("content_type", "post")
    text = request_json.get("reason", "Blank reason.")

    if _type == "post":
        try:
            content = sqla.session.query(sqlm.Post).filter_by(id=request_json.get("pk"))[0]
        except:
            return abort(500)
        content_id = content.id
        content_html = content.html
        content_author = content.author
        report_area = content.topic.category.slug
        url = "/t/%s/page/1/post/%s" % (content.topic.slug, content.id)
    elif _type == "status":
        try:
            content = sqla.session.query(sqlm.StatusUpdate).filter_by(id=request_json.get("pk"))[0]
        except:
            return abort(500)
        content_id = content.id
        content_html = content.message
        content_author = content.author
        report_area = "status"
        url = "/status/%s" % (content.id,)
    elif _type == "blogentry":
        try:
            content = sqla.session.query(sqlm.BlogEntry).filter_by(id=request_json.get("pk"))[0]
        except:
            return abort(500)
        content_id = content.id
        content_html = content.html
        content_author = content.author
        report_area = "blog-entry"
        url = "/blog/%s/e/%s" % (content.blog.slug,content.slug)
    elif _type == "blogcomment":
        try:
            content = sqla.session.query(sqlm.BlogComment).filter_by(id=request_json.get("pk"))[0]
        except:
            return abort(500)
        content_id = content.id
        content_html = content.html
        content_author = content.author
        report_area = "blog-comment"
        url = "/blog/%s/e/%s" % (content.blog.slug,content.blog_entry.slug)
    elif _type == "pm":
        try:
            content = sqla.session.query(sqlm.PrivateMessageReply).filter_by(id=request_json.get("pk"))[0]
        except:
            return abort(500)
        content_id = content.id
        content_html = content.message
        content_author = content.author
        report_area = "direct-message"
        url = "/messages/%s/page/1/post/%s" % (content.pm.id, content.id)
    elif _type == "profile":
        try:
            content = sqla.session.query(sqlm.User).filter_by(id=request_json.get("pk"))[0]
        except:
            return abort(500)
        content_id = content.id
        content_html = content.about_me
        content_author = content
        report_area = "user-profile"
        url = "/member/%s" % (content.my_url)

    try:
        report = sqla.session.query(sqlm.Report).filter_by(
            content_type=_type,
            content_id=content_id,
            content_author=current_user) \
            .filter_by(status="open")[0]
        return app.jsonify(status="reported")
    except:
        sqla.session.rollback()
        pass
    
    report = sqlm.Report(
        content_type = _type,
        content_url = url,
        created = arrow.utcnow().datetime.replace(tzinfo=None),
        report_last_updated = arrow.utcnow().datetime.replace(tzinfo=None),
        content_id = content_id,
        content_author = content_author,
        report_author = current_user,
        status = "open",
        reported_content_html = content_html,
        report_message = text,
        report_area = report_area,
        report_comment_count = 0
    )
    
    sqla.session.add(report)
    sqla.session.commit()

    broadcast(
        to=list(sqla.session.query(sqlm.User).filter_by(is_admin=True).all()),
        category="mod",
        url=url,
        title="reported a %s" % (_type),
        description=text,
        content=report,
        author=current_user
        )
    return app.jsonify(status="reported")

@app.route('/pm-topic-list-api', methods=['GET'])
@login_required
def pm_topic_list_api():
    query = request.args.get("q", "")[0:300]
    if len(query) < 2:
        return app.jsonify(results=[])

    q_ = sqla.session.query(sqlm.PrivateMessage) \
        .join(sqlm.PrivateMessageUser) \
        .filter(
            sqlm.PrivateMessageUser.author == current_user,
            sqlm.PrivateMessageUser.blocked == False,
            sqlm.PrivateMessageUser.exited == False
            ) \
        .join(sqlm.PrivateMessage.last_reply) \
        .order_by(sqlm.PrivateMessageReply.created.desc())

    q_ = parse_search_string(query,
        sqlm.PrivateMessage,
        q_,
        ["title",])

    topics = q_.all()

    results = [{"text": unicode(t.title), "id": str(t.id)} for t in topics]
    return app.jsonify(results=results)

# class Draft(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     author_id = db.Column(db.Integer, db.ForeignKey('user.id',
#         name="fk_draft_author", ondelete="CASCADE"), index=True)
#     author = db.relationship("User", foreign_keys="Draft.author_id")
#    
#     path = db.Column(db.String)
#     contents = db.Column(db.String)
#     created = db.Column(db.DateTime, index=True)
#     primary_editor = db.Column(db.Boolean, default=True, index=True)

@app.route('/drafts/clear', methods=['POST',])
@login_required
def clear_drafts():
    request_json = request.get_json(force=True)
    
    quill_id = request_json.get("quill_id", 1)
    
    primary = False
    if quill_id == 1:
        primary = True
        
    path = request_json["path"].split("/")
    path = "/".join(path[:3])
    
    sqla.session.query(sqlm.Draft).filter_by(author=current_user) \
        .filter_by(primary_editor = primary, path = path).delete()
            
    return app.jsonify(count=0)

@app.route('/drafts/count', methods=['POST',])
@login_required
def count_drafts():
    request_json = request.get_json(force=True)
    
    quill_id = request_json.get("quill_id", 1)
    
    primary = False
    if quill_id == 1:
        primary = True
        
    path = request_json["path"].split("/")
    path = "/".join(path[:3])
    
    count = sqla.session.query(sqlm.Draft).filter_by(author=current_user) \
        .filter_by(primary_editor = primary, path = path).count()
            
    return app.jsonify(count=count)
    
@app.route('/drafts/save', methods=['POST',])
@login_required
def save_draft():
    request_json = request.get_json(force=True)
    
    quill_id = request_json.get("quill_id", 1)
    
    primary = False
    if quill_id == 1:
        primary = True
        
    path = request_json["path"].split("/")
    path = "/".join(path[:3])
    
    draft = sqlm.Draft()
    draft.path = path
    draft.primary_editor = primary
    draft.created = arrow.utcnow().datetime
    draft.author = current_user
    draft.author_name = current_user.login_name
    draft.contents = request_json.get("contents")
    sqla.session.add(draft)
    sqla.session.commit()
    
    return "Ok."
    
@app.route('/drafts/get', methods=['POST',])
@login_required
def get_drafts():
    request_json = request.get_json(force=True)

    quill_id = request_json.get("quill_id", 1)

    primary = False
    if quill_id == 1:
        primary = True
    
    path = request_json["path"].split("/")
    path = "/".join(path[:3])
    
    _id = request_json["id"]

    try:
        draft = sqla.session.query(sqlm.Draft).filter_by(author=current_user) \
            .filter_by(primary_editor = primary, path = path, id = _id).order_by(sqla.desc(sqlm.Draft.created))[0]
    except IndexError:
        return abort(404)

    return app.jsonify(contents=draft.contents)
    
@app.route('/drafts/list', methods=['POST',])
@login_required
def list_drafts():
    request_json = request.get_json(force=True)
    
    quill_id = request_json.get("quill_id", 1)
    
    primary = False
    if quill_id == 1:
        primary = True
        
    path = request_json["path"].split("/")
    path = "/".join(path[:3])
    
    drafts = sqla.session.query(sqlm.Draft).filter_by(author=current_user) \
        .filter_by(primary_editor = primary, path = path).order_by(sqla.desc(sqlm.Draft.created))[:10]
    parsed_drafts = []
    
    for draft in drafts:
        parsed_drafts.append({
            "time": humanize_time(draft.created, "MMM D YYYY HH:mm:ss"),
            "contents": draft.contents,
            "id": draft.id
        })    
    
    return app.jsonify(drafts=parsed_drafts)

@app.route('/attach', methods=['POST',])
@login_required
def create_attachment():
    file = request.files['file']
    if file:
        filename = secure_filename(file.filename)
        image = Image(file=file)
        
        exif = {}
        exif.update((k[5:], v) for k, v in image.metadata.items()
                                   if k.startswith('exif:'))
                                   
        orientation = exif.get("Orientation", '1')
        
        if orientation == '3':
            image.rotate(180)
            image.orientation = 'undefined'
        elif orientation == '6':
            image.rotate(90)
            image.orientation = 'undefined'
        elif orientation == '8':
            image.rotate(270)
            image.orientation = 'undefined'

        img_bin = image.make_blob()
        # img_hash = hashlib.sha512(img_bin).hexdigest()

        # try:
        #     attach = sqla.session.query(sqlm.Attachment).filter_by(file_hash=img_hash)[0]
        #     return app.jsonify(attachment=str(attach.id), xsize=attach.x_size, ysize=attach.y_size)
        # except:
        #     pass

        time_snapshot = time.time()
        attach = sqlm.Attachment()
        attach.extension = filename.split(".")[-1]
        attach.x_size = image.width
        attach.y_size = image.height
        attach.mimetype = mimetypes.guess_type(filename)[0]
        attach.size_in_bytes = len(img_bin)
        attach.owner = current_user
        attach.alt = filename
        attach.created_date = arrow.utcnow().datetime
        attach.file_hash = "disabled"
        attach.linked = False
        upload_path = os.path.join(os.getcwd(), "lamia/static/uploads", str(time_snapshot)+"_"+str(current_user.id)+filename)
        attach.path = str(time_snapshot)+"_"+str(current_user.id)+filename

        sqla.session.add(attach)
        sqla.session.commit()
        image.save(filename=upload_path)
        return app.jsonify(attachment=str(attach.id), xsize=attach.x_size, ysize=attach.y_size)
    else:
        return abort(404)

@app.route('/robots.txt')
def robots_static_from_root():
    return send_from_directory(app.static_folder, app.settings_file.get("robots-alt", request.path[1:]))

@app.route('/sitemap-characters.xml')
def character_sitemap_generate():
    pages = []

    for character in sqla.session.query(sqlm.Character).filter_by(hidden=False)[:50000]:

        url = "%s/characters/%s" % (app.config['BASE'], character.slug,)
        modified = arrow.utcnow().datetime
        pages.append([url, modified])

    sitemap_xml = render_template('sitemap.xml', pages=pages)
    response= make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"
    return response

@app.route('/sitemap-members.xml')
def member_sitemap_generate():
    pages = []

    for member in sqla.session.query(sqlm.User) \
        .filter_by(banned=False, validated=True) \
        .order_by(sqla.desc(sqlm.User.joined))[:50000]:

        url = "%s/member/%s" % (app.config['BASE'], member.get_url_safe_login_name(),)
        modified = arrow.utcnow().datetime
        pages.append([url, modified])

    sitemap_xml = render_template('sitemap.xml', pages=pages)
    response= make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"
    return response

@app.route('/sitemap-status-updates.xml')
def status_update_sitemap_generate():
    pages = []

    for status_update in sqlm.StatusUpdate.query.filter_by(hidden=False) \
        .order_by(sqla.desc(sqlm.StatusUpdate.created))[:50000]:
        url = "%s/status/%s" % (app.config['BASE'], status_update.id,)
        modified = status_update.created
        pages.append([url, modified])

    sitemap_xml = render_template('sitemap.xml', pages=pages)
    response= make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"
    return response

@app.route('/sitemap-blog-entries.xml')
def blog_sitemap_generate():
    pages = []

    for entry in sqla.session.query(sqlm.BlogEntry) \
            .join(sqlm.Blog, sqlm.BlogEntry.blog_id == sqlm.Blog.id) \
            .filter(sqlm.Blog.disabled.isnot(True)) \
            .filter(sqlm.BlogEntry.draft.isnot(True)) \
            .filter(sqlm.BlogEntry.published.isnot(None)) \
            .filter(sqla.or_(
                sqlm.Blog.privacy_setting == "all",
            )) \
            .order_by(sqla.desc(sqlm.BlogEntry.published)):

        comments = sqla.session.query(sqlm.BlogComment) \
            .filter_by(blog_entry=entry, hidden=False) \
            .order_by(sqlm.BlogComment.created)
        comments_count = comments.count()

        url = "%s/blog/%s/e/%s" % (app.config['BASE'], entry.blog.slug, entry.slug)
        if comments_count > 0:
            modified = comments[-1].created.isoformat()
        else:
            modified = entry.published
        pages.append([url, modified])

        if comments_count > 10:
            comment_pages = int(math.ceil(float(comments_count)/10.0))-1
            for comment_page in range(2,comment_pages+1):
                url = "%s/blog/%s/e/%s/page/%s" % (app.config['BASE'], entry.blog.slug, entry.slug, comment_page)
                modified = comments[-1].created
                pages.append([url, modified])

    sitemap_xml = render_template('sitemap.xml', pages=pages[:50000])
    response= make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"
    return response

@app.route('/sitemap-topics.xml')
def topic_sitemap_generate():
    pages = []

    for topic in sqla.session.query(sqlm.Topic) \
        .filter(sqla.or_(sqlm.Topic.hidden == False, sqlm.Topic.hidden == None)) \
        .filter(sqlm.Topic.category.has(sqlm.Category.restricted==False)) \
        .join(sqlm.Topic.recent_post).order_by(sqlm.Post.created.desc()):

        topic_post_count = sqla.session.query(sqlm.Post).filter_by(topic=topic) \
            .filter(sqla.or_(sqlm.Post.hidden == False, sqlm.Post.hidden == None)).count()

        if topic_post_count <= 20:
            url = "%s/t/%s" % (app.config['BASE'], topic.slug)
            modified = topic.recent_post.created
            pages.append([url, modified])
            continue
        else:
            topic_pages = int(math.ceil(float(topic.post_count)/20.0))

            for topic_page in xrange(1,topic_pages+1):
                url = "%s/t/%s/page/%s" % (app.config['BASE'], topic.slug, topic_page)
                modified = topic.recent_post.created
                pages.append([url, modified])
                continue

    sitemap_xml = render_template('sitemap.xml', pages=pages[:50000])
    response= make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"
    return response

@app.route('/sitemap.xml')
def sitemap_index_generate():
    pages = []

    # for status_update in sqlm.StatusUpdate.query.filter_by(hidden=False):
    #     url = "%s/status/%s" % (app.config['BASE'], status_update.id,)
    #     modified = status_update.created.isoformat()
    #     pages.append([url, modified])
    #
    recent_post_time = sqla.session.query(sqlm.Topic) \
        .filter(sqla.or_(sqlm.Topic.hidden == False, sqlm.Topic.hidden == None)) \
        .filter(sqlm.Topic.category.has(sqlm.Category.restricted==False)) \
        .join(sqlm.Topic.recent_post).order_by(sqlm.Post.created.desc())[0].recent_post.created

    recent_status_time = sqla.session.query(sqlm.StatusUpdate) \
        .filter_by(hidden=False) \
        .order_by(sqla.desc(sqlm.StatusUpdate.created))[0].created

    recent_blog_time = sqla.session.query(sqlm.Blog) \
        .join(sqlm.Blog.recent_entry) \
        .filter(sqlm.Blog.disabled.isnot(True)) \
        .filter(sqlm.BlogEntry.draft.isnot(True)) \
        .filter(sqlm.BlogEntry.published.isnot(None)) \
        .filter(sqla.or_(
            sqlm.Blog.privacy_setting == "all"
        )) \
        .order_by(sqla.desc(sqlm.BlogEntry.published))[0].recent_entry.created

    pages.append([app.config['BASE']+"/sitemap-topics.xml", recent_post_time])
    pages.append([app.config['BASE']+"/sitemap-status-updates.xml", recent_status_time])
    pages.append([app.config['BASE']+"/sitemap-blog-entries.xml", recent_blog_time])
    pages.append([app.config['BASE']+"/sitemap-characters.xml", recent_post_time])
    pages.append([app.config['BASE']+"/sitemap-members.xml", recent_post_time])

    sitemap_xml = render_template('sitemap_index.xml', pages=pages)
    response= make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"
    return response

@login_manager.user_loader
def load_user(login_name):
    try:
        user = sqla.session.query(sqlm.User).filter_by(login_name=login_name)[0]
    except IndexError:
        return None

    if user.hidden_last_seen is not None:
        is_recently_active = user.hidden_last_seen > arrow.utcnow().replace(minutes=-5).datetime.replace(tzinfo=None)

        if is_recently_active:
            user.time_online += int((arrow.utcnow() - arrow.get(user.hidden_last_seen)).total_seconds())

    user.hidden_last_seen = arrow.utcnow().datetime.replace(tzinfo=None)
    if not user.anonymous_login:
        user.last_seen = arrow.utcnow().datetime.replace(tzinfo=None)
    if request.path.startswith("/message"):
        user.last_seen_at = "Private messages"
        user.last_at_url = "/messages"
    elif request.path == "/":
        user.last_seen_at = "Forum index"
        user.last_at_url = "/"
    elif request.path.startswith("/admin"):
        user.last_seen_at = "Forum index"
        user.last_at_url = "/"
    elif request.path.startswith("/t/"):
        try:
            topic = sqla.session.query(sqlm.Topic) \
                .filter_by(hidden=False) \
                .filter(sqlm.Topic.category.has(sqlm.Category.restricted==False)) \
                .filter_by(slug=request.path.split("/")[2])[0]
            user.last_seen_at = unicode(topic.title)
            user.last_at_url = "/t/"+unicode(topic.slug)
        except IndexError:
            pass
    elif request.path.startswith("/status-updates"):
        user.last_seen_at = "Viewing status updates"
        user.last_at_url = "/status-updates"
    elif request.path.startswith("/status/"):
        try:
            status = sqla.session.query(sqlm.StatusUpdate).filter_by(hidden=False).filter_by(id=request.path.split("/")[2])[0]
            user.last_seen_at = unicode(status.author.display_name)+"\'s status update"
            user.last_at_url = "/status/"+unicode(status.id)
        except IndexError:
            pass
    elif request.path.startswith("/category/"):
        try:
            category = sqla.session.query(sqlm.Category).filter_by(restricted=False).filter_by(slug=request.path.split("/")[2])[0]
            user.last_seen_at = category.name
            user.last_at_url = "/category/"+unicode(category.slug)
        except IndexError:
            pass
    elif request.path.startswith("/search"):
        user.last_seen_at = "Searching..."
        user.last_at_url = "/search"
    elif request.path.startswith("/characters/"):
        try:
            character = sqla.session.query(sqlm.Character).filter_by(slug=request.path.split("/")[2])[0]
            user.last_seen_at = "Viewing character %s" % unicode(character.name)
            user.last_at_url = "/characters/"+unicode(character.slug)
        except:
            pass
    elif request.path.startswith("/member/"):
        try:
            profile = sqla.session.query(sqlm.User).filter_by(login_name=request.path.split("/")[2])[0]
            user.last_seen_at = "Viewing user %s" % unicode(profile.display_name)
            user.last_at_url = "/member/"+unicode(profile.my_url)
        except:
            pass
    elif request.path == ("/characters"):
        user.last_seen_at = "Browsing character database"
        user.last_at_url = "/characters"
    elif request.path == ("/blogs"):
        user.last_seen_at = "Browsing blogs"
        user.last_at_url = "/blogs"
    elif request.path.startswith("/blog/"):
        full_path = request.path.split("/")
        try:
            if len(full_path) > 4:
                try:
                    blog = sqla.session.query(sqlm.Blog).filter_by(slug=full_path[2])[0]
                except IndexError:
                    user.last_seen_at = "Forum index"
                    user.last_at_url = "/"

                if blog.privacy_setting == "you":
                    user.last_seen_at = "Forum index"
                    user.last_at_url = "/"
                elif blog.privacy_setting == "editors":
                    user.last_seen_at = "Forum index"
                    user.last_at_url = "/"

                try:
                    entry = sqla.session.query(sqlm.BlogEntry).filter_by(blog=blog, slug=full_path[4])[0]
                    user.last_seen_at = entry.title
                    user.last_at_url = "/blog/%s/e/%s" % (blog.slug, entry.slug)
                except IndexError:
                    user.last_seen_at = "Forum index"
                    user.last_at_url = "/"

            elif len(full_path) < 4:
                try:
                    blog = sqla.session.query(sqlm.Blog).filter_by(slug=full_path[2])[0]
                except IndexError:
                    user.last_seen_at = "Forum index"
                    user.last_at_url = "/"

                if blog.privacy_setting == "you":
                    user.last_seen_at = "Forum index"
                    user.last_at_url = "/"
                elif blog.privacy_setting == "editors":
                    user.last_seen_at = "Forum index"
                    user.last_at_url = "/"

                user.last_seen_at = blog.name
                user.last_at_url = "/blog/%s" % (blog.slug)
            else:
                user.last_seen_at = "Browsing blogs"
                user.last_at_url = "/blogs"
        except IndexError:
            user.last_seen_at = "Browsing blogs"
            user.last_at_url = "/blogs"
    try:
        ip_address = sqla.session.query(sqlm.IPAddress).filter_by(ip_address=request.remote_addr, user=user).one()
    except:
        ip_address = sqlm.IPAddress()
        ip_address.ip_address = request.remote_addr
        ip_address.user = user

    ip_address.last_seen = arrow.utcnow().datetime.replace(tzinfo=None)
    user.last_seen_ip_address = request.remote_addr

    sqla.session.add(user)
    sqla.session.add(ip_address)
    sqla.session.commit()

    if user.validated:
        return user
    else:
        return None

@app.route('/password-reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if current_user.is_authenticated():
        return abort(404)

    try:
        user = sqla.session.query(sqlm.User).filter_by(password_forgot_token=token)[0]
    except:
        return abort(404)

    form = ResetPasswordForm(csrf_enabled=False)
    form.user = user
    if form.validate_on_submit():
        user.password_forgot_token = None
        user.password_forgot_token_date = None
        user.set_password(form.password.data.strip())
        sqla.session.add(user)
        sqla.session.commit()
        login_user(user)
        return redirect("/")

    return render_template("new_password.jade", page_title="Forgot Password - %%GENERIC SITENAME%%", form=form, token=token)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated():
        return abort(404)

    form = ForgotPasswordForm(csrf_enabled=False)
    if form.validate_on_submit():
        time = str(arrow.utcnow().timestamp)+"THIS IS A POINTLESS BIT OF TEXT LOL"
        token = bcrypt.generate_password_hash(time,10).encode('utf-8').replace("/","_")
        form.user.password_forgot_token = token
        form.user.password_forgot_token_date = arrow.utcnow().datetime.replace(tzinfo=None)
        send_mail_w_template(
            send_to=[form.user,],
            template="password_reset.txt",
            subject="Password Reset Email - %%GENERIC SITENAME%%",
            variables={
                "display_name": unicode(form.user.display_name),
                "address": app.config['BASE'] + "/password-reset/" + str(token)
            }
        )
        sqla.session.add(form.user)
        sqla.session.commit()
        return render_template("forgot_password_confirm.jade", page_title="Forgot Password - %%GENERIC SITENAME%%", profile=form.user)

    return render_template("forgot_password.jade", page_title="Forgot Password - %%GENERIC SITENAME%%", form=form)

@app.route('/hello/<pk>')
def confirm_register(pk):
    try:
        user = sqla.session.query(sqlm.User).filter_by(id=pk)[0]
    except:
        return abort(404)
        
    if user.new_user_token == "":
        return abort(404)
    
    return render_template("confirm_new_user.jade", page_title="Welcome! - %%GENERIC SITENAME%%", profile=user)
    
@app.route('/confirm-user/<token>')
def real_confirm_register(token):
    try:
        user = sqla.session.query(sqlm.User).filter_by(new_user_token=token)[0]
    except:
        return abort(404)
        
    if user.new_user_token == "":
        return abort(404)
    
    user.validated = True
    user.new_user_token = ""
    user.new_user_token_date = None
    
    broadcast(
        to=sqla.session.query(sqlm.User).filter_by(
            banned=False,
            ).filter(sqlm.User.login_name != user.login_name) \
            .filter(sqlm.User.hidden_last_seen > arrow.utcnow().replace(hours=-24).datetime.replace(tzinfo=None)) \
            .all(),
        category="new_member",
        url="/member/"+unicode(user.my_url),
        title="has joined the forum! Greet them!",
        description="",
        content=user,
        author=user
        )

    broadcast(
        to=[user,],
        category="new_member",
        url="/category/welcome",
        title="Welcome! Click here to introduce yourself!",
        description="",
        content=user,
        author=user
        )
    
    sqla.session.add(user)
    sqla.session.commit()
    
    return render_template("welcome_new_user.jade", page_title="Welcome! - %%GENERIC SITENAME%%", profile=user)

def credits():
    return render_template("acknowledgement.jade", page_title="Thank You - %%GENERIC SITENAME%%")
    
@app.route('/stats')
def stats():
    topten = sqla.session.query(sqlm.TopTen).all()
    if len(topten) == 0:
        abort(404)
    
    all_stats = {}
    
    for stat in topten:            
        db_users = []
        
        for user in stat.users:
            _u = sqla.session.query(sqlm.User).filter_by(login_name = user)[0]
            db_users.append(_u)
        
        stat.db_users = db_users
        all_stats[stat.name] = stat
    
    return render_template("global_stats.jade", page_title="Stats - %%GENERIC SITENAME%%", all_stats=all_stats)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated():
        return abort(404)

    form = RegistrationForm(csrf_enabled=False)
    form.ip = request.remote_addr
    if form.validate_on_submit():
        new_user = sqlm.User(
            login_name = form.username.data.strip().lower(),
            my_url = form.username.data.strip().lower(),
            display_name = form.username.data.strip(),
            email_address = form.email.data.strip().lower()
        )
        new_user.set_password(form.password.data.strip())
        new_user.joined = arrow.utcnow().datetime
        new_user.over_thirteeen = True
        new_user.validated = False
        new_user.how_did_you_find_us = form.how_did_you_find_us.data
        new_user.last_seen_ip_address = request.remote_addr

        sqla.session.add(new_user)
        sqla.session.commit()
        
        try:
            category = sqla.session.query(sqlm.Category).filter_by(slug="news")[0]

            if not new_user in category.watchers:
                category.watchers.append(new_user)
            
            try:
                sqla.session.add(category)
                sqla.session.commit()
            except:
                sqla.session.rollback()
            
        except IndexError:
            sqla.session.rollback()
            return abort(404)

        # send_mail_w_template(
        #     send_to=[new_user,],
        #     template="pending_validation.txt",
        #     subject="Your Account is Being Reviewed - %%GENERIC SITENAME%%",
        #     variables={
        #         "_user": new_user,
        #     }
        # )
        
        try:
            manual_validation = sqlm.SiteSetting.query.filter_by(name="manual_validation")[0].value == "on"
        except:
            sqla.session.rollback()
            manual_validation = False
            
        time = str(arrow.utcnow().timestamp)+"THIS IS ANOTHER POINTLESS BIT OF TEXT LOL"
        token = bcrypt.generate_password_hash(time,10).encode('utf-8').replace("/","_")
        new_user.new_user_token = token
        new_user.new_user_token_date = arrow.utcnow().datetime.replace(tzinfo=None)
        sqla.session.add(new_user)
        sqla.session.commit()
            
        if not manual_validation:
            send_mail_w_template(
                send_to=[new_user,],
                template="welcome_to_moe.txt",
                subject="Welcome to %%GENERIC SITENAME%%!",
                variables={
                    "_user": new_user,
                    "address": app.config['BASE'] + "/confirm-user/" + str(token)
                }
            )

            broadcast(
                to=sqla.session.query(sqlm.User).filter_by(is_admin=True).all(),
                category="mod",
                url="/member/"+unicode(new_user.my_url),
                title="has joined the forum. Please review!",
                description="",
                content=new_user,
                author=new_user
                )
        else:
            broadcast(
                to=sqla.session.query(sqlm.User).filter_by(is_admin=True).all(),
                category="mod",
                url="/member/"+unicode(new_user.my_url),
                title="has joined the forum. MANUAL VALIDATION IS ON! So, review and validate.",
                description="",
                content=new_user,
                author=new_user
                )

        return redirect('/hello/'+str(new_user.id))

    return render_template("register.jade", page_title="Become One of Us - %%GENERIC SITENAME%%", form=form)

@app.route('/sign-in', methods=['GET', 'POST'])
def sign_in():
    if current_user.is_authenticated():
        return abort(404)

    form = LoginForm(csrf_enabled=False)
    if form.validate_on_submit():
        if form.user.banned:
            return redirect("/banned")

        login_user(form.user)

        if form.anonymouse.data:
            form.user.anonymous_login=True
        else:
            form.user.anonymous_login=False

        try:
            sqla.session.add(form.user)
            sqla.session.commit()
        except:
            sqla.session.rollback()
            pass

        # try:
        #     fingerprint__info_from_browser = json.loads(request.form.get("log_in_token"))
        # except:
        #     fingerprint__info_from_browser = {"pl": []}
        #
        # fingerprint_data = {}
        # fingerprint_data["current_user"] = form.user.login_name
        # fingerprint_data["screen_width"] = fingerprint__info_from_browser.get("sw", 0)
        # fingerprint_data["screen_height"] = fingerprint__info_from_browser.get("sh", 0)
        # fingerprint_data["screen_colors"] = fingerprint__info_from_browser.get("cd", 0)
        # fingerprint_data["timezone"] = fingerprint__info_from_browser.get("tz", 0)
        #
        # for browser_plugin in fingerprint__info_from_browser.get("pl", []):
        #     try:
        #         fingerprint_data[browser_plugin["name"].replace(".", "dt").replace("$", "dl")] = browser_plugin["description"]
        #     except:
        #         pass
        #
        # for browser_plugin in fingerprint__info_from_browser.get("pl", []):
        #     try:
        #         for browser_plugin_object in browser_plugin.keys():
        #             fingerprint_data[browser_plugin_object] = browser_plugin[browser_plugin_object]
        #     except:
        #         pass
        #
        # fingerprint_data["agent_platform"] = request.user_agent.platform
        # fingerprint_data["agent_browser"] = request.user_agent.browser
        # fingerprint_data["agent_browser_version"] = request.user_agent.version
        # fingerprint_data["agent"] = request.user_agent.string
        #
        # try:
        #     for element in request.user_agent.platform.split(" "):
        #         fingerprint_data[element] = element
        # except:
        #     pass
        #
        # try:
        #     for element in request.user_agent.browser.split(" "):
        #         fingerprint_data[element] = element
        # except:
        #     pass
        #
        # try:
        #     for element in request.user_agent.version.split(" "):
        #         fingerprint_data[element] = element
        # except:
        #     pass
        #
        # try:
        #     for element in request.user_agent.string.split(" "):
        #         fingerprint_data[element] = element
        # except:
        #     pass
        #
        # try:
        #     obj = IPWhois(request.remote_addr)
        #     results=obj.lookup(get_referral=True)
        #     fingerprint_data["ip_owner"] = results["nets"][0]["name"]
        # except:
        #     pass
        #
        # clean_fingerprint_data = {}
        # fingerprint_hash = ""
        # for key, value in sorted(fingerprint_data.items()):
        #     fingerprint_hash += unicode(key) + " "
        #     fingerprint_hash += unicode(value) + " "
        #     clean_fingerprint_data[key.replace(".", "dt").replace("$", "dl")]=value
        #
        # _fingerprint_hash = hashlib.sha256(fingerprint_hash.encode('utf-8')).hexdigest()
        #
        # try:
        #     f = sqla.session.query(sqlm.Fingerprint).filter_by(fingerprint_hash=_fingerprint_hash)[0]
        #     f.last_seen = arrow.utcnow().datetime.replace(tzinfo=None)
        # except:
        #     f = sqlm.Fingerprint()
        #     f.user = form.user
        #     f.last_seen = arrow.utcnow().datetime.replace(tzinfo=None)
        #     f.json = clean_fingerprint_data
        #     f.fingerprint_hash = _fingerprint_hash
        #     f.factors = len(clean_fingerprint_data)
        #
        # try:
        #     sqla.session.add(f)
        #     sqla.session.commit()
        # except:
        #     sqla.session.rollback()

        try:
            return redirect(form.redirect_to.data)
        except:
            return redirect("/")
    else:
        form.redirect_to.data = request.args.get('next', "/")
        
    flavor_text = [
        [
            "Welcome back! Don't worry, everything is more or less exactly the way you left it. I hope you didn't leave the stove on!",
        ],
        [
            "Welcome back! I've heard this amazing rumor, lately. I'll tell you after you sign in. Maybe."
        ],
        [
            "Welcome back! Did you know that today's my birthday? Actually, it isn't, but you should still sign in and go party, just in case."
        ],
        [
            "Welcome back! Insert witty greeting text. No, this isn't a placeholder. It's a statement of philosophy."
        ]
    ]
    
    flavor_text = random.choice(flavor_text)

    return render_template("sign_in.jade", page_title="Sign In - %%GENERIC SITENAME%%", form=form, flavor_text=flavor_text)

@app.route('/banned')
def banned_user():
    image_dir = os.path.join(os.getcwd(),"lamia/static/banned_images/")
    images = ["/static/banned_images/"+unicode(i) for i in os.listdir(image_dir)]
    return render_template("banned.jade", page_title="You Are Banned.", images=images)

@app.route('/sign-out', methods=['POST'])
def sign_out():
    logout_user()
    return redirect(app.config['BASE'])

@app.route('/user-list-api', methods=['GET'])
@login_required
def user_list_api():
    query = request.args.get("q", "")[0:100]

    if len(query) < 2:
        return app.jsonify(results=[])

    users = parse_search_string(query, sqlm.User, sqla.session.query(sqlm.User), ["display_name", "login_name"]) \
        .filter(sqlm.User.banned.isnot(True)).filter(sqlm.User.validated.isnot(False)).all()
    results = [{"text": unicode(u.display_name), "id": unicode(u.id)} for u in users]

    results_starting_ = []
    results_other_ = []

    for result in results:
        if result["text"].lower().startswith(query.lower()[0]):
            results_starting_.append(result)
        else:
            results_other_.append(result)

    results_starting_.extend(results_other_)
    return app.jsonify(results=results_starting_)

@app.route('/user-list-api-variant', methods=['GET'])
@login_required
def user_list_api_variant():
    query = request.args.get("q", "")[0:100]
    if len(query) < 2:
        return app.jsonify(results=[])

    users = parse_search_string(query, sqlm.User, sqla.session.query(sqlm.User), ["display_name", "login_name"]).filter_by(banned=False, validated=True).all()
    results = [{"text": unicode(u.display_name), "id": unicode(u.login_name)} for u in users]

    results_starting_ = []
    results_other_ = []

    for result in results:
        if result["text"].lower().startswith(query.lower()[0]):
            results_starting_.append(result)
        else:
            results_other_.append(result)

    results_starting_.extend(results_other_)
    return app.jsonify(results=results_starting_)

@app.route('/members', methods=["GET",])
@login_required
def show_memeber_listing():
    return render_template("members.jade", page_title="Members - %%GENERIC SITENAME%%")

@app.route('/preview', methods=["POST",])
@login_required
def preview():
    request_json = request.get_json(force=True)
    clean_html_parser = ForumPostParser()

    return app.jsonify(preview=clean_html_parser.parse(request_json.get("text", ""), _object=current_user))

@app.route('/toggle-manual-validation', methods=["POST",])
@login_required
def toggle_manual_validation():
    if not current_user.is_authenticated():
        if not current_user.is_admin:
            return abort(404)
    
    try:
        setting = sqlm.SiteSetting.query.filter_by(name="manual_validation")[0]
        
        if setting.value == "on":
            setting.value = "off"
        else:
            setting.value = "on"
    except:
        sqla.session.rollback()
        setting = sqlm.SiteSetting(name="manual_validation", value="on")
        
    sqla.session.add(setting)
    sqla.session.commit()
    
    return app.jsonify(response="Ok.")

@app.route('/member-list-api', methods=["GET",])
@login_required
def member_list_api():
    try:
        current = int(request.args.get("start"))
    except:
        current = 0

    try:
        draw = int(request.args.get("draw"))
    except:
        draw = 0

    try:
        length = int(request.args.get("length"))
    except:
        length = 10

    try:
        order = int(request.args.get("order[0][column]"))
    except:
        order = 4

    if order == 4:
        order = "joined"
    elif order == 5:
        order = "hidden_last_seen"
    elif order == 3:
        order = "is_admin"
    elif order == 0:
        order = "display_name"
    else:
        order = "joined"

    try:
        direction = request.args.get("order[0][dir]")
    except:
        direction = "desc"

    query = request.args.get("search[value]", "")[0:100]

    member_count = parse_search_string(query,
        sqlm.User,
        sqla.session.query(sqlm.User),
        ["display_name", "login_name"]
    ).filter_by(banned=False, validated=True).count()

    if direction == "desc":
        users = parse_search_string(query,
            sqlm.User,
            sqla.session.query(sqlm.User),
            ["display_name", "login_name"]
        ).filter_by(banned=False, validated=True) \
        .order_by(sqla.desc(getattr(sqlm.User, order)))[current:current+length]
    else:
        users = parse_search_string(query,
            sqlm.User,
            sqla.session.query(sqlm.User),
            ["display_name", "login_name"]
        ).filter_by(banned=False, validated=True) \
        .order_by(getattr(sqlm.User, order))[current:current+length]

    table_data = []
    for i, user in enumerate(users):
        my_roles = [" <b>"+role+"</b>" for role in user.get_roles()]
        roles_template = """"""
        if len(my_roles) > 0:
            roles_template += """<a class="btn btn-default toggle-show-roles-button btn-xs" style="margin-top: 5px;">Community Roles</a>
            <div class="roles-div" style="display: none;">
            """
            for r in my_roles:
                roles_template += r + "<br>"
            roles_template += """</div>"""

        extra = ""

        if i > 7:
            extra = """data-hplacement=\"top\""""
        last_seen = arrow.get(user.hidden_last_seen).timestamp
        if arrow.get(user.hidden_last_seen).datetime.replace(tzinfo=None) == arrow.get(0).datetime.replace(tzinfo=None):
            human_last_seen = ""
        else:
            human_last_seen = humanize_time(user.hidden_last_seen)

        table_data.append(
            [
                """<a href="/member/%s"><img src="%s" width="%spx" height="%spx" class="avatar-mini" style="margin-right: 15px;"/></a>
                <a class="hover_user" %s href="/member/%s">%s</a>""" % (unicode(user.my_url),
                                                                        user.get_avatar_url("60"),
                                                                        user.avatar_60_x,
                                                                        user.avatar_60_y,
                                                                        extra,
                                                                        unicode(user.my_url),
                                                                        unicode(user.display_name)),
                humanize_time(user.joined),
                human_last_seen,
                roles_template,
                arrow.get(user.joined).timestamp,
                last_seen
            ]
        )
    data = {
        "draw": draw,
        "recordsTotal": member_count,
        "recordsFiltered": member_count,
        "data": table_data
    }
    return app.jsonify(data)
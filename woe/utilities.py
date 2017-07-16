from lxml.html.clean import Cleaner
import hashlib
import arrow
from woe import app
import cgi, pytz, os
import regex as re
from woe import sqla
from flask.ext.login import current_user
from mongoengine.queryset import Q
from BeautifulSoup import BeautifulSoup

url_rgx = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
spec_characters = re.compile('&[a-z0-9]{2,5};')
twitter_hashtag_re = re.compile(r'(?<=^|(?<=[^a-zA-Z0-9-\.]))#([A-Za-z]+[A-Za-z0-9-]+)')
twitter_user_re = re.compile(r'(?<=^|(?<=[^a-zA-Z0-9-\.]))@([A-Za-z]+[A-Za-z0-9-]+)')
link_re = re.compile(ur'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))')
bbcode_re = re.compile("(\[(attachment|custompostcaracter|postcharacter|spoiler|center|img|quote|font|color|size|url|b|i|s|prefix|@|reply|character|postcharacter|list).*?\])")

from HTMLParser import HTMLParser

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

words_re = re.compile("[a-zA-Z0-9']+")

def strip_tags(html):
    spc = spec_characters.findall(html)
    for sp in spc:
        html = html.replace(sp, "")
    links = link_re.findall(html)
    for link in links:
        html = html.replace(link[0], "")
    bbcode = bbcode_re.findall(html)
    for code in bbcode:
        html = html.replace(code[0], "")
    soup = BeautifulSoup(html)
    text = soup.getText()
    words = words_re.findall(text)
    return words

def get_preview_for_email(html):
    spc = spec_characters.findall(html)
    for sp in spc:
        html = html.replace(sp, "")
    links = link_re.findall(html)
    for link in links:
        html = html.replace(link[0], "")
    bbcode = bbcode_re.findall(html)
    for code in bbcode:
        html = html.replace(code[0], "")
    soup = BeautifulSoup(html)
    text = soup.getText()
    if len(text) > 100:
        text = text[:100] + "..."
    return text

def get_preview(html, characters):
    spc = spec_characters.findall(html)
    for sp in spc:
        html = html.replace(sp, "")
    links = link_re.findall(html)
    for link in links:
        html = html.replace(link[0], "")
    bbcode = bbcode_re.findall(html)
    for code in bbcode:
        html = html.replace(code[0], "")
    soup = BeautifulSoup(html)
    text = soup.getText()
    if len(text) > characters:
        text = text[:characters] + "..."
    return text

def parse_search_string(search_text, model, query_object, fields_to_search):
    if search_text.strip() == "":
        return query_object

    and_terms = []
    not_terms = []

    search_tokens = search_text.split(" ")

    token_buffer = ""
    quote_active = False
    negative = False
    for i, token in enumerate(search_tokens):
        if token.strip() == "":
            continue
        if token == "-":
            continue
        if token == "\"":
            continue

        if token[0] == "-":
            negative = True
            token = token[1:]
        else:
            if not quote_active:
                negative = False

        if token[0] == "\"":
            for look_forward_token in search_tokens[i:]:
                if look_forward_token[len(look_forward_token)-1] == "\"":
                    quote_active = True
            token = token[1:]

        if token[len(token)-1] == "\"":
            token_buffer = token_buffer.strip() + " " + token[:len(token)-1]
            quote_active = False

        if quote_active:
            token_buffer = token_buffer.strip() + " " + token + " "
        else:
            if token_buffer == "":
                token_buffer = token

            if negative:
                not_terms.append(token_buffer)
            else:
                and_terms.append(token_buffer)
            token_buffer = ""

    or_groups = []

    for term in and_terms:
        and_query = []
        for field in fields_to_search:
            if type(field) is str:
                and_query.append(getattr(model, field).ilike("%%%s%%" % term.strip()))
            else:
                and_query.append(field.ilike("%%%s%%" % term.strip()))
        or_groups.append(and_query)

    for term in not_terms:
        and_query = []
        for field in fields_to_search:
            if type(field) is str:
                and_query.append(~getattr(model, field).ilike("%%%s%%" % term.strip()))
            else:
                and_query.append(~field.ilike("%%%s%%" % term.strip()))
        or_groups.append(and_query)

    for or_group in or_groups:
        query_object = query_object.filter(sqla.or_(*or_group))

    return query_object

def parse_search_string_return_q(search_text, fields_to_search):
    if search_text.strip() == "":
        return Q()

    and_terms = []
    not_terms = []

    search_tokens = search_text.split(" ")

    token_buffer = ""
    quote_active = False
    negative = False
    for i, token in enumerate(search_tokens):
        if token.strip() == "":
            continue

        if token[0] == "-":
            negative = True
            token = token[1:]
        else:
            if not quote_active:
                negative = False

        if token[0] == "\"":
            for look_forward_token in search_tokens[i:]:
                if look_forward_token[len(look_forward_token)-1] == "\"":
                    quote_active = True
            token = token[1:]

        if token[len(token)-1] == "\"":
            token_buffer = token_buffer.strip() + " " + token[:len(token)-1]
            quote_active = False

        if quote_active:
            token_buffer = token_buffer.strip() + " " + token + " "
        else:
            if token_buffer == "":
                token_buffer = token

            if negative:
                not_terms.append(token_buffer)
            else:
                and_terms.append(token_buffer)
            token_buffer = ""

    q_params = []

    for term in and_terms:
        for field in fields_to_search:
            field_name_mongoengine = field + "__icontains"
            q_param = {field_name_mongoengine: term}
            q_params.append(q_param)

    for term in not_terms:
        for field in fields_to_search:
            field_name_mongoengine = field + "__not__icontains"
            q_param = {field_name_mongoengine: term}
            q_params.append(q_param)

    if len(q_params) == 0:
        return Q()

    q_to_return = Q(**q_params[0])

    for q_parameter in q_params[1:]:
        q_to_return = q_to_return & Q(**q_parameter)

    return q_to_return

def scrub_json(list_of_json, fields_to_scrub=[]):
    for o in list_of_json:
        for f in fields_to_scrub:
            try:
                del o[f]
            except KeyError:
                continue

def get_top_frequences(frequencies, trim, floor=1):
    inside_out = {}

    for key, value in frequencies.items():
        if value > floor:
            inside_out[value] = key

    values = inside_out.keys()
    values.sort()
    values.reverse()
    keys = [inside_out[v] for v in values]

    return ([keys[:trim], values[:trim]])

def md5(txt):
    return hashlib.md5(txt).hexdigest()

def ipb_password_check(salt, old_hash, password):
    password = password.replace("&", "&amp;") \
            .replace("\\", "&#092;") \
            .replace("!", "&#33;") \
            .replace("$", "&#036;") \
            .replace("\"", "&quot;") \
            .replace("<", "&lt;") \
            .replace(">", "&gt;") \
            .replace("\'", "&#39;")
    new_hash = md5( md5(salt) + md5(password) )

    return new_hash == old_hash

emoticon_codes = {
    ":anger:" : "angry.png",
    ":)" : "smile.png",
    ":(" : "sad.png",
    ":heart:" : "heart.png",
    ":surprise:" : "oh.png",
    ":wink:" : "wink.png",
    ":cry:" : "cry.png",
    ":silly:" : "tongue.png",
    ":blushing:" : "embarassed.png",
    ":lol:" : "biggrin.png",
    ":D" : "biggrin.png",
}

class ForumHTMLCleaner(object):
    def __init__(self):
        self.cleaner = Cleaner(
            style=False,
            links=True,
            add_nofollow=True,
            page_structure=False,
            safe_attrs_only=False
        )

    def basic_escape(self, dirty_text):
        text = cgi.escape(dirty_text)
        return text
        
    def tweet_clear(self, dirty_text):
        text = cgi.escape(dirty_text)

        urls = url_rgx.findall(text)
        for url in urls:
            text = text.replace(url, """<a href="%s" target="_blank">%s</a>""" % (unicode(url), unicode(url),), 1)

        hashtags = twitter_hashtag_re.findall(text)
        for hashtag in hashtags:
            text = text.replace("#"+hashtag, """<a href="%s" target="_blank">%s</a>""" % (unicode("https://twitter.com/hashtag/")+unicode(hashtag), unicode("#")+unicode(hashtag),), 1)

        users = twitter_user_re.findall(text)
        for user in users:
            text = text.replace("@"+user, """<a href="%s" target="_blank">%s</a>""" % (unicode("https://twitter.com/")+unicode(user), unicode("@")+unicode(user),), 1)

        return text

    def escape(self, dirty_text):
        text = cgi.escape(dirty_text)

        urls = url_rgx.findall(text)
        for url in urls:
            text = text.replace(url, """<a href="%s" target="_blank">%s</a>""" % (unicode(url), unicode(url),), 1)

        for smiley in emoticon_codes.keys():
            img_html = """<img src="%s" />""" % (os.path.join("/static/emotes",emoticon_codes[smiley]),)
            text = text.replace(smiley, img_html)

        return text

    def clean(self, dirty_html):
        try:
            html = self.cleaner.clean_html(dirty_html)
        except:
            html = dirty_html # WARNING - POTENTIALLY STUPID

        if html[0:5] == "<div>":
            html = html[5:]
        if html[-6:] == "</div>":
            html = html[:-6]

        return html

@app.template_filter('twittercleaner')
def twitter_cleaner(twitter):
    cleaner = ForumHTMLCleaner()
    try:
        _html = cleaner.tweet_clear(twitter)
    except:
        return ""
        
    return _html

@app.template_filter('datetimeformat')
def date_time_format(time, format_str="YYYY"):
    if time == None:
        return ""

    try:
        timezone = current_user._get_current_object().time_zone
    except:
        timezone = "US/Pacific"

    try:
        a = arrow.get(time).to(timezone)
        return a.format(format_str)
    except:
        a = arrow.utcnow().to(timezone)
        return a.format(format_str)
        
@app.template_filter()
def number_format(value, tsep=',', dsep='.'):
    s = unicode(value)
    cnt = 0
    numchars = dsep + '0123456789'
    ls = len(s)
    while cnt < ls and s[cnt] not in numchars:
        cnt += 1

    lhs = s[:cnt]
    s = s[cnt:]
    if not dsep:
        cnt = -1
    else:
        cnt = s.rfind(dsep)
    if cnt > 0:
        rhs = dsep + s[cnt+1:]
        s = s[:cnt]
    else:
        rhs = ''

    splt = ''
    while s != '':
        splt = s[-3:] + tsep + splt
        s = s[:-3]

    return lhs + splt[:-1] + rhs

@app.template_filter('humanize_time')
def humanize(time, format_str="MMM D YYYY, hh:mm a"):
    if time == None:
        return ""

    try:
        timezone = current_user._get_current_object().time_zone
    except:
        timezone = "US/Pacific"

    try:
        a = arrow.get(time).to(timezone)
        now = arrow.utcnow().to(timezone)
        b = arrow.utcnow().replace(hours=-48).to(timezone)
        c = arrow.utcnow().replace(hours=-24).to(timezone)
        d = arrow.utcnow().replace(hours=-4).to(timezone)
        if a > d:
            return a.humanize()
        elif a > c and now.day == a.day:
            return "Today " + a.format("hh:mm a")
        elif a > b and (now.day-1) == a.day:
            return "Yesterday " + a.format("hh:mm a")
        else:
            return a.format(format_str)
    except:
        return ""

def humanize_time(time, format_str="MMM D YYYY, hh:mm a"):
    if time == None:
        return ""

    try:
        timezone = current_user._get_current_object().time_zone
    except:
        timezone = "US/Pacific"

    try:
        a = arrow.get(time).to(timezone)
        now = arrow.utcnow().to(timezone)
        b = arrow.utcnow().replace(hours=-48).to(timezone)
        c = arrow.utcnow().replace(hours=-24).to(timezone)
        d = arrow.utcnow().replace(hours=-4).to(timezone)
        if a > d:
            return a.humanize()
        elif a > c and now.day == a.day:
            return "Today " + a.format("hh:mm a")
        elif a > b and (now.day-1) == a.day:
            return "Yesterday " + a.format("hh:mm a")
        else:
            return a.format(format_str)
    except:
        return ""

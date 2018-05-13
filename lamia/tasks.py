from lamia import app
from lamia import sqla
import lamia.sqlmodels as sqlm
from lamia import settings_file
from lamia.sqlmodels import *

from wand.image import Image
from celery import Celery
from celery.schedules import crontab

import arrow
import feedparser
import os

celery = app.celery

###############################################################################
# Logging function
###############################################################################

def log_task(name=False, recurring=False, meta=False):
    task = sqlm.TaskLog(
        name=name,
        recurring=recurring,
        meta=meta,
        created=arrow.utcnow().datetime.replace(tzinfo=None)
    )
    

###############################################################################
# RSS Feed updater
###############################################################################

@celery.task
def rss_feed_updater():
    print("rss_feed_updater running.")

    rss_feeds = RSSScraper.query.all()

    for feed in rss_feeds:
        if feed.user_account_for_posting == None:
            continue
        
        if feed.feed_type not in RSSScraper.TYPE_CHOICES:
            continue
        
        parsed_feed = feedparser.parse(feed.rss_feed_url)
    
        if feed.feed_type == "wordpress":
            for entry in parsed_feed["entries"]:
                try:
                    entry_id = int(entry["post-id"])
                    entry_content = entry["content"][0]["value"]
                    entry_published = arrow.get(entry["published_parsed"])
                except:
                    continue
                
                existing_content_count = RSSContent.query.filter_by(remote_id=entry_id).count()
                if existing_content_count > 0:
                    continue
            
                topic = Topic(
                        category=feed.category_for_topics,
                        author=feed.user_account_for_posting,
                        slug=sqlm.find_topic_slug(entry["title"]),
                        title=entry["title"],
                        created=entry_published.datetime.replace(tzinfo=None),
                        post_count=1
                    )
                sqla.session.add(topic)
                sqla.session.commit()
            
                more_link = """<div>[button="Click Here to View Post"]%s[/button]</div>""" % entry["id"]
            
                post = Post(
                        author=feed.user_account_for_posting,
                        html=entry["content"][0]["value"].replace("<p>", "<div>").replace("</p>", "</div>") + "\n\n" + more_link,
                        topic=topic,
                        t_title=topic.title,
                        created=entry_published.datetime.replace(tzinfo=None)
                    )
                sqla.session.add(post)
                sqla.session.commit()
            
                topic.first_post = post
                topic.recent_post = post
                topic.recent_post_time = post.created
                sqla.session.add(topic)

                rss_content = RSSContent(
                        remote_id = entry_id,
                        remote_url = entry["id"],
                        last_modified = arrow.utcnow().datetime.replace(tzinfo=None),
                        topic = topic,
                        scraper = feed
                    )

                sqla.session.add(rss_content)
                sqla.session.commit()

###############################################################################
# Other misc. tasks
###############################################################################

@celery.task()
def verify_attachment(filepath, size):
    filepath = os.path.join(os.getcwd(), "lamia/static/uploads", filepath)
    sizepath = os.path.join(os.getcwd(), "lamia/static/uploads", 
        ".".join(filepath.split(".")[:-1])+".custom_size."+size+"."+filepath.split(".")[-1])
    
    if not os.path.exists(sizepath):
        image = Image(filename=filepath)
        xsize = image.width
        ysize = image.height
        resize_measure = min(float(size)/float(xsize),float(size)/float(ysize))
        image.resize(int(round(xsize*resize_measure)),int(round(ysize*resize_measure)))
        image.save(filename=sizepath)
        
    return True

@celery.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    # Run RSS feed update every X seconds - use "rss_feed_update_delay" in config.json to set an integer value
    sender.add_periodic_task(settings_file["rss_feed_update_delay"], rss_feed_updater.s(), name='rss_feed_updater')
    

from rq import get_current_job
from app import create_app, db
from app.models import Task, User, Post
import sys
import time
import json
from flask import render_template
from app.email import send_email

app = create_app()
app.app_context().push()


def _set_task_progress(progress):
    """
    Task Helpers
    The export task can call _set_task_progress() to record the progress percentage.
    """
    job = get_current_job()
    if job:
        # writes the percentage to the job.meta dictionary and saves it to Redis
        job.meta['progress'] = progress
        job.save_meta()
        task = Task.query.get(job.get_id())
        task.user.add_notification('task_progress', {'task_id': job.get_id(),
                                                     'progress': progress})
        if progress >= 100:
            task.complete = True
        # The database commit call ensures that the task and
        # the notification object added by add_notification()
        # are both saved immediately to the database.
        db.session.commit()


def export_posts(user_id):
    try:
        user = User.query.get(user_id)
        _set_task_progress(0)
        data = []
        i = 0
        total_posts = user.posts.count()
        for post in user.posts.order_by(Post.timestamp.asc()):
            data.append({'body': post.body,
                         'timestamp': post.timestamp.isoformat() + 'Z'})
            time.sleep(5)
            i += 1
            _set_task_progress(100 * i // total_posts)

        send_email('[Microblog] Your blog posts',
                   sender=app.config['ADMINS'][0], recipients=[user.email],
                   text_body=render_template('email/export_posts.txt', user=user),
                   html_body=render_template('email/export_posts.html', user=user),
                   attachments=[('posts.json', 'application/json',
                                 json.dumps({'post': data}, indent=4))],
                   sync=True)
    except:
        _set_task_progress(100)
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())

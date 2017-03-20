from invoke import task

@task
def devworker(ctx):
    # solo-pool is to prevent forking-segfault that happens with sqlite db client
    ctx.run('celery worker --app=resource_manager --pool=solo --loglevel info --beat')

@task
def run(ctx):
    ctx.run('python manage.py runserver 8002')

# @task
# def resetmigrations(ctx):
#     ctx.run('rm -rf rime/migrations')
#     ctx.run('rm -f db.sqlite3')
#     ctx.run('python manage.py makemigrations')
#     ctx.run('python manage.py migrate')

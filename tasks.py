from invoke import task

@task
def devworker(ctx):
    # solo-pool is to prevent forking-segfault that happens with sqlite db client
    ctx.run('celery worker --app=resource_manager --pool=solo --loglevel info --beat')

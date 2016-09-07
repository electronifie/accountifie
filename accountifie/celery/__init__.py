from __future__ import absolute_import
from .celery import app as celery_app
from django.http import JsonResponse


def background_task(*args, **kwargs):
    return run_task.delay(*args, **kwargs)

def background_status(request, task_id):
    task = celery_app.AsyncResult(id=task_id)
    return JsonResponse(task.result)


@celery_app.task(bind=True)
def run_task(self, *args, **kwargs):
    task_name = kwargs['task']
    self.update_state(state='PROGRESS', meta={'status': 'IN_PROGRESS', 'task_name': task_name})
    rslts = kwargs['calc']()
    return {'status': 'COMPLETED', 'task_name': task_name, 'result': rslts}

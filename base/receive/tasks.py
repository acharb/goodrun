from base.celery import app


@app.task
def load_next_questions_for(userprofile, first_node):
    # TODO Error handling
    try:
        userprofile._load_question_flow_list_into_queue(first_node)
    except Exception:
        return

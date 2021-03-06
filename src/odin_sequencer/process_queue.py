try:
    from celery import Celery

    process_queue = Celery('odin_sequencer',
                        broker='redis://te7aegserver.aeg.lan',
                        backend='redis://te7aegserver.aeg.lan',
                        include=['odin_sequencer.process_queue_context'])


    def process_monitor(log_message, start_process_task, finish_process_task, start_process_group_task, finish_process_group_task):
        state = process_queue.events.State()

        def announce_task_started(event):
            state.event(event)
            # task name is sent only with -received event, and state
            # will keep track of this for us.
            start_process_task(event['task_uuid'])

            log_message('<b>TASK STARTED</b>: %s' % (
                event['task_name'],))

        def announce_group_task_started(event):
            state.event(event)
            # task name is sent only with -received event, and state
            # will keep track of this for us.
            is_first = start_process_group_task(event['task_uuid'], event['group_uuid'])
            
            if is_first:
                log_message('<b>GROUP TASK STARTED</b>: %s task %s' % (
                    event['group_uuid'], event['task_name'],))

        def announce_task_succeeded(event):
            state.event(event)
            # task name is sent only with -received event, and state
            # will keep track of this for us.
            finish_process_task(event['task_uuid'])

            log_message('<b style="color:green">TASK FINISHED</b>: %s' % (
                event['task_name'],))

        def announce_group_task_succeeded(event):
            state.event(event)
            # task name is sent only with -received event, and state
            # will keep track of this for us.
            is_last = finish_process_group_task(event['task_uuid'], event['group_uuid'])

            if is_last:
                log_message('<b style="color:green">GROUP TASK FINISHED</b>: %s' % (
                    event['task_name'],))

        def announce_task_failed(event):
            state.event(event)
            # task name is sent only with -received event, and state
            # will keep track of this for us.
            finish_process_task(event['task_uuid'])

            log_message('<b style="color:red">TASK FAILED</b>: %s' % (
                event['task_name'],))

        def announce_group_task_failed(event):
            state.event(event)
            # task name is sent only with -received event, and state
            # will keep track of this for us.
            is_last = finish_process_group_task(event['task_uuid'], event['group_uuid'])

            log_message('<b style="color:red">TASK FAILED</b>: %s' % (
                event['task_name'],))

        with process_queue.connection() as connection:
            recv = process_queue.events.Receiver(connection, handlers={
                    'started-task': announce_task_started,
                    'started-group-task': announce_group_task_started,
                    'successful-task': announce_task_succeeded,
                    'successful-group-task': announce_group_task_succeeded,
                    'failed-task': announce_task_failed,
                    'failed-group-task': announce_group_task_failed,
            })
            recv.capture(limit=None, timeout=None, wakeup=True)

except ModuleNotFoundError as error:
    process_queue = None
    process_monitor = None

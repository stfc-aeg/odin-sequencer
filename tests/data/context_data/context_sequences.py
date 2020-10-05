# Basic command sequences for testing context use in CommandSequenceManager

provides = ['context_access', 'missing_context_obj']

def context_access(value=0):
    """Calls context increment method with the value passed as an argument, returing value."""

    ctx_obj = get_context('context_object')
    return ctx_obj.increment(value)

def missing_context_obj():

    ctx_obj = get_context('missing_context_object')

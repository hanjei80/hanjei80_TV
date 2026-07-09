def register(si):
    si.add_builtin("square", lambda x: x * x)
    si.add_builtin("cube", lambda x: x * x * x)

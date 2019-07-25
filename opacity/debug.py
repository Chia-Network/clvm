
PRELUDE = '''<html>
<head>
  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css"
      integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T"
      crossorigin="anonymous">
  <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js"
      integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo"
      crossorigin="anonymous"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js"
      integrity="sha384-UO2eT0CpHqdSJQ6hJty5KVphtPhzWj9WO1clHTMGa3JDZwrnQq4sF86dIHNDz0W1"
      crossorigin="anonymous"></script>
  <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js"
      integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM"
      crossorigin="anonymous"></script>
</head>
<body>
<div class="container">
'''


TRAILER = "</div></body></html>"


def dump_sexp(s, disassemble):
    return '<span id="%s">%s</span>' % (id(s), disassemble(s))


def dump_invocation(form, rewrit_form, env, result, disassemble):
    print('<hr><div class="invocation" id="%s">' % id(form))
    print('<span class="form"><a name="id_%s">%s</a></span>' % (
        id(form), dump_sexp(form, disassemble)))
    print('<ul>')
    if form != rewrit_form:
        print('<li>Rewritten as:<span class="form"><a name="id_%s">%s</a></span></li>' % (
            id(rewrit_form), dump_sexp(rewrit_form, disassemble)))
    for _, e in enumerate(env):
        print('<li>x%d: <a href="#id_%s">%s</a></li>' % (_, id(e), dump_sexp(e, disassemble)))
    print('</ul>')
    print('<span class="form">%s</span>' % dump_sexp(result, disassemble))
    if form.listp() and len(form) > 1:
        print('<ul>')
        for _, arg in enumerate(form[1:]):
            print('<li>arg %d: <a href="#id_%s">%s</a></li>' % (
                _, id(arg), dump_sexp(arg, disassemble)))
        print('</ul>')
    print("</div>")


def trace_to_html(invocations, disassemble):
    invocations = reversed(invocations)

    print(PRELUDE)

    id_set = set()
    id_list = []

    for form, rewrit_form, env, rv in invocations:
        dump_invocation(form, rewrit_form, env, rv, disassemble)
        the_id = id(form)
        if the_id not in id_set:
            id_set.add(the_id)
            id_list.append(form)

    print('<hr>')
    for _ in id_list:
        print('<div><a href="#id_%s">%s</a></div>' % (id(_), disassemble(_)))
    print('<hr>')

    print(TRAILER)


def trace_to_text(trace, disassemble):
    for (form, env), rv in trace:
        env_str = ", ".join(disassemble(_) for _ in env.as_iter())
        rewrit_form = form
        if form != rewrit_form:
            print("%s -> %s [%s] => %s" % (
                disassemble(form),
                disassemble(rewrit_form),
                env_str, disassemble(rv)))
        else:
            print("%s [%s] => %s" % (
                disassemble(form), env_str, disassemble(rv)))
        print("")


def make_tracing_f(inner_f):
    log_entries = []

    def tracing_f(self, *args):
        try:
            rv = inner_f(self, *args)
        except Exception as ex:
            rv = args[-1].to(("FAIL: %s" % str(ex)).encode("utf8"))
            raise
        finally:
            log_entry = (args, rv)
            log_entries.append(log_entry)
        return rv

    return tracing_f, log_entries

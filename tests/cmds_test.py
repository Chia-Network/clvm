import io
import os
import pkg_resources
import shlex
import sys
import unittest


# If the REPAIR environment variable is set, any tests failing due to
# wrong output will be corrected. Be sure to do a "git diff" to validate that
# you're getting changes you expect.

REPAIR = os.getenv("REPAIR", 0)


def get_test_cases(path):
    PREFIX = os.path.dirname(__file__)
    TESTS_PATH = os.path.join(PREFIX, path)
    paths = []
    for dirpath, dirnames, filenames in os.walk(TESTS_PATH):
        for fn in filenames:
            if fn.endswith(".txt") and fn[0] != '.':
                paths.append(os.path.join(dirpath, fn))
    paths.sort()
    test_cases = []
    for p in paths:
        with open(p) as f:
            # allow "#" comments at the beginning of the file
            comments = []
            while 1:
                cmd = f.readline()
                if len(cmd) < 1 or cmd[0] != '#':
                    break
                comments.append(cmd)
            expected_output = f.read()
            test_name = os.path.relpath(
                p, PREFIX).replace(".", "_").replace("/", "_")
            test_cases.append((test_name, cmd, expected_output, comments, p))
    return test_cases


class TestCmds(unittest.TestCase):
    def invoke_tool(self, cmd_line):

        # capture io
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        old_stdout = sys.stdout
        old_stderr = sys.stderr

        sys.stdout = stdout_buffer
        sys.stderr = stderr_buffer

        args = shlex.split(cmd_line)
        v = pkg_resources.load_entry_point('opacity', 'console_scripts',
                                           args[0])(args)

        sys.stdout = old_stdout
        sys.stderr = old_stderr

        return v, stdout_buffer.getvalue(), stderr_buffer.getvalue()


def make_f(cmd, expected_output, comments, path):

    def f(self):
        for c in cmd.split(";"):
            r, actual_output, actual_stderr = self.invoke_tool(c)
        if actual_output != expected_output:
            print(cmd)
            print(actual_output)
            print(expected_output)
            if REPAIR:
                f = open(path, "w")
                f.write(''.join(comments))
                f.write(cmd)
                f.write(actual_output)
                f.close()
        self.assertEqual(expected_output, actual_output)
    return f


def inject(*paths):
    for path in paths:
        for idx, (name, i, o, comments, path) in enumerate(get_test_cases(path)):
            name_of_f = "test_%s" % name
            setattr(TestCmds, name_of_f, make_f(i, o, comments, path))


inject("opc", "v0_0_2")

inject("runtime_001")

inject("compiler_001")

inject("puzzles")

inject("compiler")

inject("brun")


def main():
    unittest.main()


if __name__ == "__main__":
    main()


"""
Copyright 2018 Chia Network Inc

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

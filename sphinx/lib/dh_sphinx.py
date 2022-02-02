import os
import pkgutil
import shutil
import sys
import threading
from pathlib import Path

import jpy
from deephaven.start_jvm import start_jvm

_exit_timer = None

def setup_sphinx_environment():
    # add the deephaven-ib path
    new_python_path = Path(os.path.realpath(__file__)).parents[2].joinpath("src")
    sys.path.append(str(new_python_path))

    # start the jvm so that deephaven can be loaded
    if not jpy.has_jvm():
        os.environ['JAVA_VERSION'] = '11'
        start_jvm(devroot="/tmp", workspace="/tmp", propfile='dh-defaults.prop',
                  java_home=os.environ.get('JDK_HOME', None),
                  jvm_classpath="/opt/deephaven/server/lib/*", skip_default_classpath=True)

    # Sphinx hangs for some reason.  Maybe the JVM doesn't clean up completely.  Forcing exit.

    def exit_handler():
        print("Exit handler")
        # jpy.destroy_jvm()

        import sys, traceback, threading
        thread_names = {t.ident: t.name for t in threading.enumerate()}
        for thread_id, frame in sys._current_frames().items():
            print("Thread %s:" % thread_names.get(thread_id, thread_id))
            traceback.print_stack(frame)
            print()

        print("Calling sys.exit()")
        sys.exit()

    global _exit_timer
    _exit_timer = threading.Timer(30, exit_handler)
    _exit_timer.start()


def glob_package_names(packages):
    rst = []

    for package in packages:
        rst.append(package.__name__)

        if hasattr(package, "__path__"):
            for importer, modname, ispkg in pkgutil.walk_packages(path=package.__path__, prefix=package.__name__ + '.',
                                                                  onerror=lambda x: None):
                rst.append(modname)

    return rst


def _add_package(tree, package):
    n = package[0]

    if n not in tree:
        tree[n] = {}

    if len(package) > 1:
        _add_package(tree[n], package[1:])


def package_tree(package_names):
    rst = {}
    for pn in package_names:
        spn = pn.split('.')
        _add_package(rst, spn)
    return rst


def make_rst_tree(package, tree):
    package_name = ".".join(package)

    if len(tree) == 0:
        toctree = ""
    else:
        toctree = ".. toctree::\n"
        for k in tree:
            p = package.copy()
            p.append(k)
            pn = ".".join(p)
            toctree += "%s%s <%s>\n" % (" " * 4, k, pn)

    rst = "%s\n%s\n\n%s\n.. automodule:: %s\n    :members:\n    :no-undoc-members:\n    :show-inheritance:\n    :inherited-members:\n\n" % (
        package_name, "=" * len(package_name), toctree, package_name)

    if len(package) > 0:
        filename = f"code/{package_name}.rst"

        with open(filename, "w") as file:
            file.write(rst)

    for k, v in tree.items():
        p = package.copy()
        p.append(k)
        make_rst_tree(p, v)


def make_rst_modules(docs_title, package_roots):
    rst = f'''
Python Modules
##############

{docs_title}

.. toctree::
    :glob:

'''

    for pr in package_roots:
        rst += "\n%s./code/%s" % (" " * 4, pr.__name__)

    filename = "modules.rst"

    with open(filename, "w") as file:
        file.write(rst)


def gen_sphinx_modules(docs_title, package_roots, package_excludes):
    pn = glob_package_names(package_roots)
    pn = [p for p in pn if not any(exclude in p for exclude in package_excludes)]
    pt = package_tree(pn)

    if os.path.exists("code"):
        shutil.rmtree("code")
    os.mkdir("code")

    make_rst_modules(docs_title, package_roots)
    make_rst_tree([], pt)

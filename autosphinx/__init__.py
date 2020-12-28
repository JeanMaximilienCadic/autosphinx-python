from docutils import nodes
from sphinx import addnodes
import os
from autosphinx.functional import *
from gnutools.utils import listfiles, parent, name
import numpy as np

class PyscriptParser(dict):
    def __init__(self, file):
        super(PyscriptParser, self).__init__()
        self._file = file
        self._lines = [l.split("\n")[0] for l in open(self._file, "r").readlines()]
        self.update({"classes": {}, "functions": {}})
        self.run()

    def get_generic_name(self, pattern, ind):
        return self._lines[ind].split(pattern)[1]

    def get_class_name(self, ind):
        name = self.get_generic_name(CLASS_DEF, ind)
        sep = "(" if "(" in name else ":"
        name = name.split(sep)[0]
        return name

    def get_method_name(self, ind):
        return self.get_generic_name(METHOD_DEF, ind).split("(")[0]

    def get_function_name(self, ind):
        return self.get_generic_name(FUNCTION_DEF, ind).split("(")[0]

    def get_comment(self, start, stop):
        try:
            inds_comment = [k+start for k, l in enumerate(self._lines[start:stop]) if '"""' in l]
            assert len(inds_comment)==2 or len(inds_comment)==0
            if len(inds_comment)==2:
                comment = "\n".join(self._lines[inds_comment[0]:inds_comment[1]+1])
                return comment
        except AssertionError:
            pass
    def run(self):
        inds_class  = sorted([k for k, l in enumerate(self._lines) if starts_with(l, CLASS_DEF)      ])
        inds_method = sorted([k for k, l in enumerate(self._lines) if starts_with(l, METHOD_DEF)     ])
        inds_function  = [k for k, l in enumerate(self._lines) if starts_with(l, FUNCTION_DEF)   ]
        inds_method += [len(self._lines)]
        # Update classes and methods
        if len(inds_class)>0:
            classes = {}
            for ind_class in inds_class:
                dmethods = {}
                [dmethods.update({
                    self.get_method_name(ind): {
                        "block": (ind, inds_method[k + 1]),
                        "comment": self.get_comment(ind, inds_method[k + 1])
                    }
                }) for k, ind in enumerate(inds_method[:-1])]
                classes.update({self.get_class_name(ind_class): dmethods})
            self.update({"classes": classes})

        # Update the functions list (BUGGY)
        if len(inds_function)>0:
            inds_function += [min(max(inds_function) + 10, len(self._lines))]
            functions = dict([(self.get_function_name(ind), {
                "block": (ind, inds_function[k + 1]),
                "comment": self.get_comment(ind, inds_function[k + 1])
            })  for k, ind in enumerate(inds_function[:-1])])
            self.update({"functions": functions})

class AutoSphinx:
    def __init__(self, lib_root, version, logo_img=""):
        os.environ["ASPHINX_LIBROOT"]   = lib_root
        os.environ["ASPHINX_NAMELIB"]   = name(lib_root)
        os.environ["ASPHINX_VERSION"]   = version
        os.environ["ASPHINX_LOGO"]      = logo_img
        os.environ["PATH"]              = f"{parent(os.sys.executable)}:{os.environ['PATH']}"
        self._name_lib = name(lib_root)
        self._lib_root = lib_root
        self._parent_lib_root =  f"{parent(self._lib_root)}/"
        self._version = version
        self._current_dir = parent(os.path.abspath(__file__))
        self._module=None
        self._name_class = None
        self._name_function = None

    def run(self, export_dir):
        command = \
            f"cd {self._current_dir};"\
            f"export ASPHINX_LIBROOT={os.environ['ASPHINX_LIBROOT']};" \
            f"export ASPHINX_NAMELIB={os.environ['ASPHINX_NAMELIB']};" \
            f"export ASPHINX_VERSION={os.environ['ASPHINX_VERSION']};" \
            f"export ASPHINX_LOGO={os.environ['ASPHINX_LOGO']};" \
            f"export PATH={os.environ['PATH']};" \
            f"python conf.py;" \
            "make html;" \
            f"rsync -avz --remove-source-files html/ {export_dir}/;" \
            f"rm -r doctrees html *.rst"
        os.system(f"/bin/sh -c '{command}'")

    def get_packages(self, root, namelib):
        """
        Get the list of packages availables in a root

        :param root: package root
        :return list:
        """
        root = os.path.realpath(root)
        files = listfiles(root, patterns=[".py"], excludes=[".pyc", "__pycache__"])
        files = [f for f in files if os.stat(f).st_size>0]
        py_files = [file.rsplit(self._parent_lib_root)[1] for file in files]
        modules = [parent(file).replace("/", ".").split(f"{namelib}.") for file in py_files]
        modules = [m for m in modules if len(m)==2]
        return list(np.unique([m[1] for m in modules]))

    @staticmethod
    def patched_make_field(self, types, domain, items, **kw):
        # `kw` catches `env=None` needed for newer sphinx while maintaining
        #  backwards compatibility when passed along further down!

        # type: # (List, unicode, Tuple) -> nodes.field
        def handle_item(fieldarg, content):
            par = nodes.paragraph()
            par += addnodes.literal_strong('', fieldarg)  # Patch: this line added
            # par.extend(self.make_xrefs(self.rolename, domain, fieldarg,
            #                           addnodes.literal_strong))
            if fieldarg in types:
                par += nodes.Text(' (')
                # NOTE: using .pop() here to prevent a single type node to be
                # inserted twice into the doctree, which leads to
                # inconsistencies later when references are resolved
                fieldtype = types.pop(fieldarg)
                if len(fieldtype) == 1 and isinstance(fieldtype[0], nodes.Text):
                    typename = u''.join(n.astext() for n in fieldtype)
                    typename = typename.replace('int', 'python:int')
                    typename = typename.replace('long', 'python:long')
                    typename = typename.replace('float', 'python:float')
                    typename = typename.replace('type', 'python:type')
                    par.extend(self.make_xrefs(self.typerolename, domain, typename,
                                               addnodes.literal_emphasis, **kw))
                else:
                    par += fieldtype
                par += nodes.Text(')')
            par += nodes.Text(' -- ')
            par += content
            return par

        fieldname = nodes.field_name('', self.label)
        if len(items) == 1 and self.can_collapse:
            fieldarg, content = items[0]
            bodynode = handle_item(fieldarg, content)
        else:
            bodynode = self.list_type()
            for fieldarg, content in items:
                bodynode += nodes.list_item('', handle_item(fieldarg, content))
        fieldbody = nodes.field_body('', bodynode)
        return nodes.field('', fieldname, fieldbody)



    def read_member_class(self, pyscript):
        currentmodule = pyscript["currentmodule"]
        for name_class, methods in pyscript["classes"].items():
            members = ", ".join(list(methods.keys()))
            self.__output += f".. currentmodule:: {currentmodule}\n\n"
            self.__output += \
                f"{name_class}\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n" \
                f".. autoclass:: {name_class}\n" \
                f"    :members: {members}\n" \
                "    :special-members:\n\n"
            # with open("all.txt", "a") as f:
            #     f.write(self.__output + "\n")

    def read_functions(self, pyscript):
        currentfile = pyscript["currentfile"]
        currentmodule = pyscript["currentmodule"]
        if len(pyscript["functions"]) > 0:
            self.__output += f".. currentmodule:: {currentmodule}\n\n"
            self.__output += f"{currentfile}\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n"
            block = "".join([f".. autofunction:: {function}\n" for function in pyscript["functions"].keys()])
            self.__output += block

        self.__output += "\n"

    def get_current_module(self, f):
        return parent(f).split(self._parent_lib_root)[1].replace("/", ".").split(".py")[0]

    def generate_rst(self, pkg):
        """
        Scan a package and generate automatically a rst string to save as a rst file for documentation.

        :param root: package root
        :param package: package or module to generate the rst file
        :return string:
        """

        #Set the variables
        package = f"{self._lib_root}/{pkg.replace('.', '/')}"
        files = os.listdir(package)
        pyfiles = [f"{package}/{f}" for f in files if f[-3:]==".py"]
        pyscripts = [PyscriptParser(file) for file in pyfiles]
        [s.update({"currentmodule": self.get_current_module(s._file), "currentfile":name(s._file)}) for s in pyscripts]


        self.__output = f"{pyscripts[0]['currentmodule']}\n==============================================================\n\n"

        # Process each module sequentially
        [self.read_member_class(pyscript) for pyscript in pyscripts]
        [self.read_functions(pyscript) for pyscript in pyscripts]

        # Write the result
        print(f"{self.__output}\n============================================================================\n")
        with open(f"{self._current_dir}/{self._name_lib}.{pkg}.rst", "w") as f:
            f.write(self.__output)


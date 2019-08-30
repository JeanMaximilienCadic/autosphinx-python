from docutils import nodes
from sphinx import addnodes
import os
from gnutools.utils import listfiles, parent, name, ext
import numpy as np

class AutoSphinx:
    def __init__(self, lib_root, version, export_dir=None, logo_img=""):
        os.environ["ASPHINX_LIBROOT"] = lib_root
        os.environ["ASPHINX_NAMELIB"] = name(lib_root)
        os.environ["ASPHINX_VERSION"] = version
        os.environ["ASPHINX_LOGO"] = logo_img
        os.environ["PATH"]= parent(os.sys.executable) + ":" + os.environ["PATH"]
        self._name_lib = name(lib_root)
        self._lib_root = lib_root
        self._version = version
        self._dir = parent(os.path.abspath(__file__))
        self._export_dir = export_dir

    def run(self):
        os.system("python {current_dir}/conf.py".format(current_dir=self._dir))
        os.system("cd {current_dir} && make html".format(current_dir=self._dir))
        os.system("rm {current_dir}/*.rst".format(current_dir=self._dir))
        dirs = ["doctrees", "html", "img"]
        [os.system("mv {current_dir}/{dir} {export_dir}".format(current_dir=self._dir,
                                                                export_dir=self._export_dir,
                                                                dir=dir))
                   for dir in dirs if not os.path.exists("{export_dir}/{dir}".format(export_dir=self._export_dir,
                                                                                     dir=dir))]
        [os.system("rm -r {current_dir}/{dir}".format(current_dir=self._dir, dir=dir))
         for dir in dirs if os.path.exists("{current_dir}/{dir}".format(dir=dir, current_dir=self._dir))]

    # def clean(self):
    #     from gnutools.utils import listfiles
    #     import os
        # Remove some files
        # Remove some directories
        # [os.system("rm -r {}".format(dir)) for dir in ["doctrees", "html/_sources", "static", "templates"]]
        # # Copy for azure
        # os.makedirs("templates")
        # os.system("cp -r html templates/docs")
        # # Create the folders
        # [os.system("mkdir {}".format(dir)) for dir in ["static", "static/docs"]]
        # os.system("mv templates/docs/_static static/docs")
        # os.system("mv templates/docs/objects.inv static/docs")
        # os.system("mv templates/docs/searchindex.js static/docs")

        # # Replace the path in all files
        # def replace_in_file(file, pattern_in, pattern_out):
        #     def replace_in_line(line, pattern_in, pattern_out):
        #         return line.replace(pattern_in, pattern_out)
        #
        #     lines = [replace_in_line(line, pattern_in, pattern_out) for line in open(file, "r").readlines()]
        #     open(file, "w").writelines(lines)

        # [replace_in_file(file, "_static", "../static/docs/") for file in
        #  listfiles(root="templates/docs", patterns=[".html"])]


    @staticmethod
    def get_packages(root, namelib):
        """
        Get the list of packages availables in a root

        :param root: package root
        :return list:
        """
        root = os.path.realpath(root)
        proot = parent(root) + "/"
        py_files = [file.rsplit(proot)[1] for file in listfiles(root, patterns=[".py"], excludes=[".pyc", "__pycache__"]) if os.stat(file).st_size>0]
        modules = [parent(file).replace("/", ".").split("{namelib}.".format(namelib=namelib)) for file in py_files]
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

    def generate_rst(self, root, package, pkg):
        """
        Scan a package and generate automatically a rst string to save as a rst file for documentation.

        :param root: package root
        :param package: package or module to generate the rst file
        :return string:
        """
        root = os.path.realpath(root)
        package = os.path.realpath(package)
        proot = parent(root) + "/"

        pyfiles = listfiles(package, patterns=[".py"], excludes=[".pyc", "__pycache__"])
        modules = np.unique([file.replace(proot, "").replace("/", ".").replace(".py", "") for file in pyfiles])
        module_name = package.replace(proot, "").replace("/", ".").replace(".py", "")
        output = "{}\n==============================================================\n\n".format(module_name)
        for module in modules:
            splits = module.split("__init__")
            if len(splits)==2:
                path = "{}{}__init__.py".format(proot, splits[0].replace(".", "/"))
            else:
                path = "{}{}.py".format(proot, module.replace(".", "/"))
            with open(path, "r") as f:
                modules_dict = {}
                modules_dict[name(path)] = []
                members_class = {}
                functions = []
                lines = f.readlines()
                last = ""
                for line in lines:
                    if ((line[:8] == "    def ") | (line[:6] == "class ")):
                        if line.__contains__("class "):
                            name_class = line.split("class ")[1].replace(":\n", "").split("(")[0].split("\n")[0]
                            modules_dict[name_class] = module
                            members_class[name_class] = []
                            last = "class"
                        else:
                            name_member_class = line.split("    def ")[1].split("(")[0]
                            if not name_member_class.__contains__("__"):
                                if last == "class":
                                    members_class[name_class].append(name_member_class)
                                    last = "class"
                    elif line[:4] == "def ":
                        name_function = line.split("def ")[1].split("(")[0]
                        modules_dict[name_function] = module
                        functions.append(name_function)
                        last = "function"

                for name_class, class_value in members_class.items():
                    if not name_class[0]=="_":
                        members = ", ".join([value for value in class_value if not value[0]=="_"])
                        output += ".. currentmodule:: {}\n\n".format(module_name)
                        output += \
                            "{name_class}\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n" \
                            ".. autoclass:: {name_class}\n" \
                            "    :members: {members}\n" \
                            "    :special-members:\n\n".format(name_class=name_class, members=members)

                if len(functions) > 0:
                    if not ext(module)=="__init__":
                        output += ".. currentmodule:: {}\n\n".format(module_name)
                        output += "{}\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n".format(
                            ext(module))
                    else:
                        output += ".. currentmodule:: {}\n\n".format(module_name)
                    for function in functions:
                        if not function[0]=="_":
                            output += \
                                ".. autofunction:: {}\n".format(function)
                output += "\n"
        print("{}\n============================================================================\n".format(output))
        with open("{dir}/{namelib}.{pkg}.rst".format(dir=self._dir,
                                                     namelib=self._name_lib,
                                                     pkg=pkg), "w") as f:
            f.write(output)
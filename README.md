<p align="center">
  <img src="https://raw.githubusercontent.com/JeanMaximilienCadic/autosphinx-python/master/img/autosphinx.png"/>
</p>

# Python package to create documentation easily with Sphinx

## Requirements
```bash
pip install -r requirements.txt
pip install autosphinx
```
## Getting Started


```bash
from autosphinx import AutoSphinx

sphinx = AutoSphinx(lib_root="/media/jcadic/PythonProjects/project",
                    version="1.0a29",
                    logo_img="/home/jcadic/PythonImages/logo_project.png")

sphinx.run(export_dir="/home/jcadic/PythonDocs/project")
```


## Contributions

Email me at j.cadic@9dw-lab.com for any questions.

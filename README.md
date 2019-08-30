<p align="center">
  <img src="https://raw.githubusercontent.com/JeanMaximilienCadic/autosphinx-python/master/img/autosphinx.png"/>
</p>

# Cython packaging for python wheels

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
                    export_dir="/home/jcadic/PythonDocs/project",
                    logo_img="/home/jcadic/PythonImages/logo_project.png")

sphinx.run()

```


## Contributions

Email me at j.cadic@9dw-lab.com for any questions.

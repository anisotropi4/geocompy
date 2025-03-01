
# geocompy

[![Render](https://github.com/geocompx/geocompy/actions/workflows/main.yaml/badge.svg)](https://github.com/geocompx/geocompy/actions/workflows/main.yaml)
<!-- [![Binder](http://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/geocompr/py/main?urlpath=lab/tree/ipynb) -->
[![Open in GitHub
Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=447558863)

<https://py.geocompx.org>

Running the code in this book requires the following:

1.  Python dependencies, which can be installed with
    [`pip`](https://pypi.org/project/pip/), a package manager or a
    [Docker](https://docs.docker.com/get-docker/) container (see below)
2.  An integrated development environment (IDE) such as [VS
    Code](https://code.visualstudio.com/) (running locally or on
    [Codespaces](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=447558863)/other
    host) or [Jupyter
    Notebook](https://github.com/geocompx/geocompy/tree/main/ipynb) for
    running and exploring the Python code interactively
3.  [Quarto](https://quarto.org/docs/get-started/), which is used to
    generate the book

<!-- ## Reproduce the book in Binder
&#10;To reproduce this book you can simply click on the link below to see the code running in your web browser (see details of how this works at [mybinder.org](https://mybinder.org/)):
&#10;[![Binder](http://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/geocompx/geocompy/readme-clean?urlpath=lab/tree/ipynb)
 -->

## Reproduce the book with GitHub Codespaces

GitHub [Codespaces](https://github.com/features/codespaces) minimise
set-up costs by providing access to a modern IDE (VS Code) plus
dependencies in your browser. This can save time on package
installation. Codespaces allow you to make and commit changes, providing
a way to test changes and contribute fixes in an instant.

To run the book in Codespaces, click on the link below.

<div>

[![](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=447558863)

Open in GitHub Codespaces

</div>

You should [see](https://github.com/geocompx/geocompy/issues/114)
something like this, the result of running all the code in the book by
opening the terminal (e.g. with the command Ctrl+J) and entering the
following command:

    quarto preview

![](https://user-images.githubusercontent.com/1825120/202933280-e313c076-f188-4efd-9de1-5625eb169045.png)

## Reproduce the book with Docker (devcontainer)

If you can install [Docker](https://docs.docker.com/desktop/install/)
this is likely to be the quickest way to reproduce the contents of this
book. To do this from within VS Code:

1.  Install Microsoft’s official [Dev
    Container](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
    extension
2.  Open the folder containing the repo in VS Code and click on the
    ‘Reopen in container’ button that should appear, as shown below (you
    need to have Docker installed on your computer for this to work)

![](https://user-images.githubusercontent.com/1825120/202933928-eb6de086-f9a5-43cd-9932-e6ec84746d45.png)

Edit the code in the containerised instance of VS Code that will appear
🎉

See details below for other ways to get the dependencies and reproduce
the book.

## Install dependencies with pip

<details>

Use `pip` to install the dependencies as follows, after cloning the repo
and opening a terminal in the root folder of the repo.

First we’ll set-up a virtual environment to install the dependencies in:

``` sh
# Create a virtual environment called geocompy
python -m venv geocompy
# Activate the virtual environment
source geocompy/bin/activate
```

Then install the dependencies (with the optional
[`python -m`](https://fosstodon.org/deck/@hugovk@mastodon.social/111311327842154267)
prefix specifying the Python version):

``` sh
# Install dependencies from the requirements.txt file
python -m pip install -r requirements.txt
```

You can also install packages individually, e.g.:

``` sh
pip install jupyter-book
```

Deactivate the virtual environment when you’re done:

``` sh
deactivate
```

</details>

## Install dependencies with a package manager

<details>

The [`environment.yml`](environment.yml) file contains a list of
dependencies that can be installed with a package manager such as
`conda`, `mamba` or `micromamba`. The instructions below are for
[micromamba](https://mamba.readthedocs.io/en/latest/installation.html#micromamba)
but should work for any package manager.

``` bash
# For Linux, the default shell is bash:
curl micro.mamba.pm/install.sh | bash
# For macOS, the default shell is zsh:
curl micro.mamba.pm/install.sh | zsh
```

After answering the questions, install dependencies with the following
command:

``` bash
micromamba env create -f environment.yml
```

Activate the environment as follows:

``` bash
micromamba activate geocompy
```

Install kernel, this will allow you to select the environment in vscode
or IPython as follows:

``` bash
python -m ipykernel install --user
```

You can now reproduce the book (requires quarto to be installed):

``` bash
micromamba run -n geocompy quarto preview
```

</details>

### Reproduce chapters with jupyter

<details>

VS Code’s `quarto.quarto` plugin can Python code in the chunks in the
.qmd files in this book interactively.

However, you can also run any of the chapters in a Jupyter Notebook,
e.g. as follows:

``` sh
cd ipynb
# jupyter notebook . # open a notebook showing all chapters
jupyter notebook 02-spatial-data.ipynb
```

You should see something like this:

![](https://user-images.githubusercontent.com/1825120/176920562-d2e7f9af-84b4-4352-8a50-9d9946084c66.png)

See documentation on running and developing Python code in a Jupyter
notebook at [docs.jupyter.org](https://docs.jupyter.org/en/latest/).

</details>

# Additional information

If you’re interested in how to auto-generate and run the .py and .ipynb
files from the .qmd files, see below.

<details>

## Updating the .py and .ipynb files

The Python scripts and IPython notebook files stored in the [code](code)
and [ipynb](ipynb) folders are generated from the .qmd files. To
regenerate them, you can use the following commands, to generate .ipynb
and .py files for local versions of Chapter 2, for example:

``` bash
quarto convert 02-spatial-data.qmd # generate .ipynb file
jupytext --to py *.ipynb # generate .py files .ipynb files
```

Do this for all chapters with the following bash script in the repo:

``` bash
./convert.sh
```

## Updating .py and .ipynb files with GitHub Actions

We have set-up a GitHub Action to do this automatically: every commit
message that contains the text string ‘convert’ will create and push
updated .ipynb and .py files.

## Executing the .py and .ipynb files

Running the code chunks in the .qmd files in an IDE such as VSCode or
directly with quarto is the main way code in this book is designed to be
run interactively, but you can also execute the .py and .ipynb files
directly. To run the code for chapter 2, for example, you can run one of
the following commands from your system shell:

``` bash
python code/chapters/02-spatial-data.py # currently requires manual intervention to complete, see #71
ipython ipynb/02-spatial-data.ipynb # currently requires manual intervention to complete, see #71
bash ./run-code.sh # run all .python files
```

## Updating packages

We pin package versions in the [environment.yml](environment.yml) and
[requirements.txt](requirements.txt) files to ensure reproducibility.

To update the `requirements.txt` run the following:

``` bash
python -m pip install pur
pur -r requirements.txt
python -m pip install -r requirements.txt
```

To update the `environment.yml` file in the same way based on your newly
installed packages, run the following:

``` bash
micromamba list export > environment.yml
```

</details>

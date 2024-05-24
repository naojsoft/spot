# Site Planning and Observation Tool (SPOT)

## Installation

We recommend a (mini)conda environment for newer users.
Use [this file](spot_conda_environment.yml) to create a conda environment
named "spot" like so:

```bash
$ conda env create -f spot_conda_environment.yml
```

Activate this environment:

```bash
    $ conda activate spot
```

If you have cloned the SPOT source:

```bash
    $ pip install .
```

Finally, if you want to use NAOJ features, use
[this file](spot_pip_requirements.txt) to install the
remaining requirements via *pip*:

```bash
    $ pip install -r spot_pip_requirements.txt
```

Assuming everything installed without error, you are now ready to run
spot:

```bash
    $ spot --loglevel=20 --stderr
```


## Requirements
varVAMP runs on UNIX Systems, MacOSX and Windows with Python3 >=3.9 installed.

## Installation

From PyPI:

```shell
pip install varvamp
```

That was already it. To check if it worked:

```shell
varvamp -v
```
You should see the current varVAMP version.

## Installation for advanced customization or development

All varVAMP options (such as temperature, size, penalties) can be customized in the config.py. However, to do this you will have to install varvamp not from the PyPI repository, but directly from this github repository.

### - via pip (recommended)

```shell
git clone https://github.com/jonas-fuchs/varVAMP
cd varVAMP
pip install .
```

### - via requirements.txt

```shell
git clone https://github.com/jonas-fuchs/varVAMP
cd varVAMP
pip install -r requirements.txt
python3 varvamp -v
```


#### [Next: Preparing your data](./preparing_the_data.md)

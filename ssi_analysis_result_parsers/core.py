# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_core.ipynb.

# %% auto 0
__all__ = ['PACKAGE_NAME', 'DEV_MODE', 'PACKAGE_DIR', 'PROJECT_DIR', 'config', 'set_env_variables', 'get_config',
           'show_project_env_vars', 'get_samplesheet', 'PipelineResults', 'update_results_dict',
           'print_results_dict_to_tsv']

# %% ../nbs/00_core.ipynb 4
# Need the ssi_analysis_result_parsers for a few functions, this can be considered a static var

import importlib
import importlib.util
import os

PACKAGE_NAME: str = (
    "ssi_analysis_result_parsers"  # Make sure to adjust this to your package name
)
DEV_MODE: bool = (
    False  # set below to override, as this is in an export block it'll be exported while the dev mode section is not
)

PACKAGE_DIR = None
try:
    spec = importlib.util.find_spec(PACKAGE_NAME)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    PACKAGE_DIR = os.path.dirname(module.__file__)
except ImportError:
    DEV_MODE = True
except AttributeError:
    DEV_MODE = True
PROJECT_DIR = os.getcwd()  # override value in dev mode
if PROJECT_DIR.endswith("nbs"):
    DEV_MODE = True
    PROJECT_DIR = os.path.split(PROJECT_DIR)[0]

# %% ../nbs/00_core.ipynb 10
# standard libs
import os
import re

# Common to template
# add into settings.ini, requirements, package name is python-dotenv, for conda build ensure `conda config --add channels conda-forge`
import dotenv  # for loading config from .env files, https://pypi.org/project/python-dotenv/
import envyaml  # Allows to loads env vars into a yaml file, https://github.com/thesimj/envyaml
import fastcore  # To add functionality related to nbdev development, https://github.com/fastai/fastcore/
import pandas  # For sample sheet manipulation
from fastcore import (
    test,
)
from fastcore.script import (
    call_parse,
)  # for @call_parse, https://fastcore.fast.ai/script

# Project specific libraries

from pathlib import Path
from hashlib import sha256

# %% ../nbs/00_core.ipynb 13
import importlib
import importlib.util


def set_env_variables(config_path: str, overide_env_vars: bool = True) -> bool:
    # Load dot env sets environmental values from a file, if the value already exists it will not be overwritten unless override is set to True.
    # If we have multiple .env files then we need to apply the one which we want to take precedence last with overide.

    # Order of precedence: .env file > environment variables > default values
    # When developing, making a change to the config will not be reflected until the environment is restarted

    # Set the env vars first, this is needed for the card.yaml to replace ENV variables
    # NOTE: You need to adjust PROJECT_NAME to your package name for this to work, the exception is only for dev purposes
    # This here checks if your package is installed, such as through pypi or through pip install -e  [.dev] for development. If it is then it'll go there and use the config files there as your default values.
    try:
        dotenv.load_dotenv(f"{PACKAGE_DIR}/config/config.default.env", override=False)
    except Exception as e:
        print(f"Error: {PACKAGE_DIR}/config/config.default.env does not exist")
        return False

    # 2. set values from file:
    if os.path.isfile(config_path):
        dotenv.load_dotenv(config_path, override=overide_env_vars)

    return True

# %% ../nbs/00_core.ipynb 15
import importlib
import importlib.util


def get_config(config_path: str = None, overide_env_vars: bool = True) -> dict:
    if config_path is None:
        config_path = ""
    # First sets environment with variables from config_path, then uses those variables to fill in appropriate values in the config.yaml file, the yaml file is then returned as a dict
    # If you want user env variables to take precedence over the config.yaml file then set overide_env_vars to False
    set_env_variables(config_path, overide_env_vars)

    config: dict = envyaml.EnvYAML(
        os.environ.get(
            "CORE_YAML_CONFIG_FILE", f"{PACKAGE_DIR}/config/config.default.yaml"
        ),
        strict=False,
    ).export()

    return config

# %% ../nbs/00_core.ipynb 17
# create a os.PathLike object
config = get_config(os.environ.get("CORE_CONFIG_FILE", ""))

# %% ../nbs/00_core.ipynb 19
def show_project_env_vars(config: dict) -> None:
    # Prints out all the project environment variables
    # This is useful for debugging and seeing what is being set
    for k, v in config.items():
        # If ENV var starts with PROJECTNAME_ then print
        if k.startswith(config["CORE_PROJECT_VARIABLE_PREFIX"]):
            print(f"{k}={v}")

# %% ../nbs/00_core.ipynb 23
import pandas as pd


def get_samplesheet(sample_sheet_config: dict) -> pd.DataFrame:
    # Load the sample sheet into a pandas dataframe
    # If columns is not None then it will only load those columns
    # If the sample sheet is a csv then it will load it as a csv, otherwise it will assume it's a tsv

    # Expected sample_sheet_config:
    # sample_sheet:
    #   path: path/to/sample_sheet.tsv
    #   delimiter: '\t' # Optional, will assume , for csv and \t otherwises
    #   header: 0 # Optional, 0 indicates first row is header, None indicates no header
    #   columns: ['column1', 'column2', 'column3'] # Optional, if not provided all columns will be used

    # Example sample sheet:
    # #sample_id	file_path	metadata1	metadata2
    # Sample1	/path/to/sample1.fasta	value1	option1
    # Sample2	/path/to/sample2.fasta	value2	option2
    # Sample3	/path/to/sample3.fasta	value3	option1
    # Sample4	/path/to/sample4.fasta	value1	option2
    # Sample5	/path/to/sample5.fasta	value2	option1

    # This function should also handle ensuring the sample sheet is in the correct format, such as ensuring the columns are correct and that the sample names are unique.
    if not os.path.isfile(sample_sheet_config["path"]):
        raise FileNotFoundError(f"File {sample_sheet_config['path']} does not exist")
    if "delimiter" in sample_sheet_config:
        delimiter = sample_sheet_config["delimiter"]
    else:
        # do a best guess based on file extension
        delimiter = "," if sample_sheet_config["path"].endswith(".csv") else "\t"
    header = 0
    # if "header" in sample_sheet_config:
    #     header = sample_sheet_config["header"]
    # else:
    #     # check if the first line starts with a #, if so lets assume it's a header otherwise assume there isn't one
    #     with open(sample_sheet_config["path"], "r") as f:
    #         first_line = f.readline()
    #         header = 0 if first_line.startswith("#") else None
    if "columns" in sample_sheet_config:
        columns = sample_sheet_config[
            "columns"
        ]  # note the # for the first item needs to be stripped to compare to the columns
    else:
        columns = None  # implies all columns
    try:
        # note when we have a header the first column may begin with a #, so we need to remove it
        df = pd.read_csv(
            sample_sheet_config["path"],
            delimiter=delimiter,
            header=header,
            comment=None,
        )
    except Exception as e:
        print(
            "Error: Could not load sample sheet into dataframe, you have a problem with your sample sheet or the configuration."
        )
        raise e

    # Check the first header has a # in it, if so remove it for only that item
    if df.columns[0].startswith("#"):
        df.columns = [col.lstrip("#") for col in df.columns]
    # Ensure the sample sheet has the correct columns
    if columns is not None and not all([col in df.columns for col in columns]):
        raise ValueError("Error: Sample sheet does not have the correct columns")
    # also drop columns which are not needed
    if columns is not None:
        df = df[columns]

    # Clean the df of any extra rows that can be caused by empty lines in the sample sheet
    df = df.dropna(how="all")
    return df

# %% ../nbs/00_core.ipynb 24
class PipelineResults:

    def __init__(self, results_dict):
        print(results_dict)
        self.results_dict = results_dict
        self.results_df = pandas.DataFrame.from_dict(results_dict, orient="index")

    def write_tsv(self, output_file: Path) -> None:
        print_df = self.results_df.reset_index(names="sample_name")
        print_df.to_csv(output_file, sep="\t", index=False)
        return None

    @classmethod
    def from_results_dataframe(cls, results_df: pandas.DataFrame):
        # results_df = results_df.set_index("sample_name")
        results_dict = results_df.to_dict(orient="index")
        return cls(results_dict)

    @classmethod
    def from_results_tsv(cls, results_tsv: Path):
        results_df = pandas.read_csv(results_tsv, sep="\t")
        results_df.set_index("sample_name", inplace=True, drop=True)
        results_dict = results_df.to_dict(orient="index")
        return cls(results_dict)

    def __repr__(self):
        return f"< Generic analysis results object. {len(self.results_df)} samples with {len(self.results_df.columns)} result variables > "

    def __len__(self):
        return len(self.results_dict)

    def __iter__(self):
        for sample_name in self.results_dict:
            yield sample_name

    def items(self):
        for sample_name, results_d in self.results_dict:
            yield sample_name, results_d

    def results(self):
        for results_d in self.results_dict.values():
            yield results_d


def update_results_dict(
    old_results: dict,
    new_results: dict,
    old_duplicate_key_prefix: str = None,
    new_duplicate_key_prefix: str = None,
):
    if old_results is None:
        return new_results
    elif new_results is None:
        return old_results
    else:
        duplicate_keys = list(set(old_results.keys()) & set(new_results.keys()))
        if len(duplicate_keys) == 0:
            old_results.update(new_results)
            return old_results
        else:
            if old_duplicate_key_prefix is None and new_duplicate_key_prefix is None:
                raise ValueError(
                    "Provided dictionaries contain duplicate keys. Old_duplicate_key_prefix and/or new_duplicate_key_prefix must be provided"
                )
            elif old_duplicate_key_prefix == new_duplicate_key_prefix:
                raise ValueError(
                    "old_duplicate_key_prefix and new_duplicate_key_prefix cannot be identical"
                )
            else:
                combined_dict = {}
                if old_duplicate_key_prefix is None:
                    combined_dict.update(old_results)
                else:
                    for key, value in old_results.items():
                        if key in duplicate_keys:
                            combined_dict.update(
                                {f"{old_duplicate_key_prefix}{key}": value}
                            )
                        else:
                            combined_dict.update({key: value})
                if new_duplicate_key_prefix is None:
                    combined_dict.update(new_results)
                else:
                    for key, value in new_results.items():
                        if key in duplicate_keys:
                            combined_dict.update(
                                {f"{new_duplicate_key_prefix}{key}": value}
                            )
                        else:
                            combined_dict.update({key: value})
            return combined_dict


def print_results_dict_to_tsv(
    results_dict: dict, output_file: Path, sample_name: str = None
) -> None:
    if sample_name is None:
        header = "\t".join(str(x) for x in results_dict.keys())
        values = "\t".join(str(x) for x in results_dict.values())
    else:
        header = "sample_name\t" + "\t".join([str(x) for x in results_dict.keys()])
        values = sample_name + "\t" + "\t".join([str(x) for x in results_dict.values()])
    o = open(output_file, "w")
    o.write(header + "\n")
    o.write(values + "\n")
    o.close()
    return None

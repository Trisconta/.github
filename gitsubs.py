""" gitsubs.py -- Resolves git submodules of interest.
"""

import sys
import os
import subprocess
sys.path.append(os.path.join(os.path.dirname(__file__), "other/sources/pyyaml/lib"))
import yaml
import configparser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GITMODULES = ROOT / ".gitmodules"
YAML_FILE = ROOT / "submodules.yaml"
KEY_NAME = "interest1"

CMDS = {
    "a": "Save YAML",
    "b": "generate YAML from loaded submodules",
    "c": "generate YAML from loaded submodules, recursively",
    "d": "Detect submodules, recursively",
    "e": "dEtailed submodules, recursively",
}


def usage(myname=None):
    myname = os.path.basename(__file__) if myname is None else myname
    print("""Usage: python {} [{}]

Reference yaml: {}""".
        format(
            myname,
            "|".join(sorted(CMDS)),
            YAML_FILE,
        ),
    )
    print("\nCommands:")
    for key, desc in CMDS.items():
        print(f"  {key}: {desc}")
    sys.exit(0)


def main():
    """ submodules.yaml example:

interest1:
  - libs/a
  - libs/c
  - tools/x
    """
    do_script(sys.argv[1:])


def do_script(args):
    """ Main script """
    cwd = os.getcwd()
    param = args if args else ["a"]
    cmd = param[0]
    del param[0]
    if cmd not in CMDS or param:
        usage()
    if cmd == "a":
        tup = command_a()
    elif cmd == "b":
        tup = command_b()
    elif cmd == "c":
        tup = command_c()
    elif cmd == "d":
        set_config(cwd)
        tup = command_d()
    elif cmd == "e":
        set_config(cwd)
        tup = command_e()
    else:
        return tuple()
    msg, lsts = tup
    if msg:
        print("ERROR:", msg)
    return tup


def set_config(path: str):
    """ Horrible setting constant function!
	ROOT = Path(__file__).resolve().parent
	GITMODULES = ROOT / ".gitmodules"
	YAML_FILE = ROOT / "submodules.yaml"
    """
    global ROOT, GITMODULES, YAML_FILE
    new_root = Path(path)
    ROOT = new_root
    GITMODULES = ROOT / ".gitmodules"
    YAML_FILE = ROOT / "submodules.yaml"
    return os.path.realpath(new_root)


def run(cmd):
    subprocess.run(cmd, shell=True, check=True)


def load_gitmodules():
    config = configparser.ConfigParser()
    config.read(GITMODULES)
    modules = {}
    for section in config.sections():
        if section.startswith("submodule"):
            name = section.split('"')[1]
            path = config[section]["path"]
            modules[path] = section
    return modules, config


def load_interest1(key=KEY_NAME):
    with open(YAML_FILE, "r") as f:
        data = yaml.safe_load(f)
    return set(data.get(key, []))


def remove_from_git_config(path):
    hint = f"git config --remove-section submodule.{path} || true"
    return hint


def find_loaded_submodules_recursively(start_paths: list):
    """
    Given a list of submodule paths, recursively detect nested submodules.
    Returns a set of all loaded submodule paths.
    """
    lst = loaded_submodules(start_paths)
    return lst[0]


def loaded_submodules(start_paths: list):
    loaded = set()
    stack = list(start_paths)
    dct = {
        "root": [],
        "ref": {},
    }
    while stack:
        path = stack.pop()
        p = ROOT / path
        # Only consider if directory exists and is non-empty
        if not (p.exists() and any(p.iterdir())):
            continue
        loaded.add(path)
        # Look for nested .gitmodules
        nested_gitmodules = p / ".gitmodules"
        if nested_gitmodules.exists():
            dct["root"].append((path, None))
            config = configparser.ConfigParser()
            config.read(nested_gitmodules)
            for section in sorted(config.sections()):
                if not section.startswith("submodule"):
                    continue
                nested_path = config[section]["path"]
                full_nested_path = f"{path}/{nested_path}"
                stack.append(full_nested_path)
                dct["root"].append((path, nested_path))
        else:
            assert path not in dct["ref"], f"Duplicate? {path}"
            dct["root"].append((path, ""))
            a_len = len(dct["ref"])
            dct["ref"][path] = a_len + 1
    return (loaded, dct)


def is_initialized(path: str) -> bool:
    """ A submodule is initialized if .git/modules/<path> exists.
    """
    mod_path = ROOT / ".git" / "modules" / path
    return mod_path.exists()

# ------------------------------------------------------------

def command_a(debug=0):
    """
    Command A:
    Enforce submodules.yaml as the single source of truth.
    Only submodules listed under interest1 are initialized.
    """
    interest1 = load_interest1()
    modules, config = load_gitmodules()
    #s_recurse = " --recursive"
    s_recurse = ""
    seq, mal = [], []
    for path, section in modules.items():
        if path in interest1:
            if is_initialized(path):
                if debug > 0:
                    print(f"Already initialized: {path}")
            else:
                print(f"Initializing submodule: {path}")
                run(f"git submodule update --init{s_recurse} {path}")
                seq.append(path)
        else:
            if debug > 0:
                print(f"Ignoring submodule: {path}")
            #run(f"git submodule deinit -f {path}")
            remove_from_git_config(path)
            #config.remove_section(section)
            subdir = ROOT / path
            if not subdir.exists():
                mal.append(subdir)
    msg = f"At least one module not found ({mal[0]})" if mal else ""
    return msg, (seq, mal)


def command_b():
    """
    Command B:
    Detect which submodules are currently loaded in the working tree.
    A submodule is considered loaded if its directory exists and is non-empty.
    Write submodules.yaml with these paths under the key interest1.
    """
    modules, _ = load_gitmodules()
    loaded = []
    for path in modules:
        p = ROOT / path
        if p.exists() and any(p.iterdir()):
            loaded.append(path)
    data = {KEY_NAME: sorted(loaded)}
    with open(YAML_FILE, "w") as fdout:
        yaml.safe_dump(data, fdout, sort_keys=False)
    print("Generated submodules.yaml with interest1:")
    for m in loaded:
        print("  -", m)
    return "", loaded


def command_c():
    """
    Detect loaded submodules recursively and write yaml.
    """
    modules, _ = load_gitmodules()
    # First-level submodules
    first_level = list(modules.keys())
    # Recursively detect nested ones
    loaded = find_loaded_submodules_recursively(first_level)
    data = {KEY_NAME: sorted(loaded)}
    with open(YAML_FILE, "w") as fdout:
        yaml.safe_dump(data, fdout, sort_keys=False)
    print("Generated submodules.yaml with interest1:")
    for m in sorted(loaded):
        print("  -", m)
    return "", sorted(loaded)


def command_d():
    """
    Detect loaded submodules recursively.
    """
    modules, _ = load_gitmodules()
    # First-level submodules
    first_level = list(modules.keys())
    # Recursively detect nested ones
    loaded = find_loaded_submodules_recursively(first_level)
    for m in sorted(loaded):
        print(m)
    return "", sorted(loaded)


def command_e():
    """
    Detect detailed loaded submodules recursively.
    """
    modules, _ = load_gitmodules()
    # First-level submodules
    first_level = sorted(modules)
    # Recursively detect nested ones
    tup = loaded_submodules(first_level)
    _, dct = tup
    act = dct["root"]
    for left, right in act:
        if right is None:
            print(left, "-->")
        else:
            if right:
                print(left, right)
    #for key, right in dct["ref"].items(): print("REF:", key, right)
    return "", tup


if __name__ == "__main__":
    main()

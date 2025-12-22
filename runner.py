#!/usr/bin/env python3

import fnmatch
import json
import os
import shutil
import subprocess
import sys

def load_config(config_path: str = "config.json"):
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"error during loading config: {e}")
        sys.exit(1)

def print_with_interval(title: str = "default", content: str = "default"):
    print(f"--- {title} ---")
    print(f"{content}")
    print(f"=== {title} ===")

def run_command(command: str,
                res_path: str,
                output: bool,
                cwd: str):
    print_with_interval("run_command",
                        f"command: {command}\n"
                        f"res_path: {res_path}\n"
                        f"output: {output}\n"
                        f"cwd: {cwd}")

    with open(res_path, 'w') as f:
        sys.stdout.write(f"--- start to run {command} ---\n")
        sys.stdout.flush()

        p = subprocess.Popen(command,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             text=True,
                             cwd=cwd,
                             shell=True)

        while True:
            line = p.stdout.readline()

            if not line and p.poll() is not None:
                break

            f.write(line)
            f.flush()
            if output:
                sys.stdout.write(line)
                sys.stdout.flush()

        sys.stdout.write(f"=== finish to {command} ===\n")
        sys.stdout.flush()

        return p.returncode


def run_tests(conf: dict):
    # Print parameters, error if any parameters are missed
    print_with_interval("runner variables",
                        f"RES_CLEANUP: {conf['RES_CLEANUP']}")
    print_with_interval("environment variables",
                        f"TEST_BROWSERS: {conf['TEST_BROWSERS']}\n"
                        f"TEST_SHOW_BROWSER: {conf['TEST_SHOW_BROWSER']}\n"
                        f"TEST_OS: {conf['TEST_OS']}\n"
                        f"TEST_COMPOSE: {conf['TEST_COMPOSE']}"
                        )
    print_with_interval("testsuite path",
                        f"TESTSUITE_PATH: {conf['TESTSUITE_PATH']}")
    print_with_interval("machine",
                        f"MACHINE: {conf['MACHINE']}")

    # create test results directories
    if os.path.isdir(conf['TESTSUITE_PATH']):
        if conf["RES_CLEANUP"] and os.path.exists(conf['TEST_COMPOSE']):
            shutil.rmtree(conf['TEST_COMPOSE'])
        for b in conf['TEST_BROWSERS']:
            os.makedirs(f"{conf['TEST_COMPOSE']}/{b}")

    # check whether run all test suites
    if os.path.isdir(conf['TESTSUITE_PATH']):
        # search all test suites
        ts_list = [ f for f in os.listdir(conf['TESTSUITE_PATH'] + "/test")
                    if fnmatch.fnmatch(f, "check-machines-*")
                    and not fnmatch.fnmatch(f, "check-machines-migrate") ]
        if len(ts_list) > 0:
            print(f"test suite list: {ts_list}")
        else:
            raise Exception(f"search test suites failed - ts_list: {ts_list}")

    command_pre = (f"TEST_SHOW_BROWSER={conf['TEST_SHOW_BROWSER']} "
                   f"TEST_OS={conf['TEST_OS']} "
                   "test/")
    for b in conf['TEST_BROWSERS']:
        if os.path.isdir(conf['TESTSUITE_PATH']):
            for ts in ts_list:
                command = ((f"source {conf.get('PYTHONVENV')} && " if conf.get('PYTHONVENV') else "") +
                           f"TEST_BROWSER={b} " +
                           command_pre +
                           ts +
                           f" --machine {conf['MACHINE']}")

                res = run_command(command,
                                  res_path=f"{conf['TEST_COMPOSE']}/{b}/{ts}",
                                  output=True,
                                  cwd=conf['TESTSUITE_PATH'])
                print(f"=== {ts} finished - return code: {res} ===")

        else:
            # run single test case/suite
            test_home = os.path.abspath(os.path.join(conf['TESTSUITE_PATH'],
                                                     os.pardir,
                                                     os.pardir))

            if conf.get("TEST_CASE"):
                # if no () for the first line, "" will combine with "+" firstly
                # Then the following string will be skipped in the else block
                command = ((f"source {conf.get('PYTHONVENV')} && " if conf.get('PYTHONVENV') else "") +
                           f"TEST_BROWSER={b} " +
                           command_pre +
                           os.path.basename(conf['TESTSUITE_PATH']) +
                           " -st" +
                           f" --machine {conf['MACHINE']} " +
                           conf['TEST_CASE'])

                res = run_command(command,
                                  res_path=conf["TEST_CASE"],
                                  output=True,
                                  cwd=test_home)
                print(f"=== single test case finished - return code: {res} ===")
                if res:
                    raise Exception(f"unexcepted existing: return {res}")
            else:
                command = ((f"source {conf.get('PYTHONVENV')} && " if conf.get('PYTHONVENV') else "") +
                           f"TEST_BROWSER={b} " +
                           command_pre +
                           os.path.basename(conf['TESTSUITE_PATH']) +
                           f" --machine {conf['MACHINE']} ")

                res = run_command(command,
                                  res_path=os.path.basename(conf['TESTSUITE_PATH']),
                                  output=True,
                                  cwd=test_home)
                print(f"=== single test suite finished - return code: {res} ===")
                if res:
                    raise Exception(f"unexcepted existing: return {res}")


if __name__ == "__main__":
    conf = load_config()

    run_tests(conf)

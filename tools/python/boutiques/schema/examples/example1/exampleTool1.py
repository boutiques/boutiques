#!/usr/bin/env python

import argparse
import os
import sys


def file_exists(parser, file_name):
    if not os.path.exists(file_name):
        parser.error("File not found: %s" % file_name)
    return file_name


def is_valid_enum_value(parser, value):
    if value not in ['val1', 'val2', 'val3']:
        parser.error("Invalid enum value: %s" % value)
    return value


def test_mutex_group(results):
    if results.number and results.enum_input:
        sys.stderr.write(
            "error: number and enum_input are mutually exclusive.\n")
        sys.exit(1)


def test_one_is_required_group(results):
    if (not results.number) and (not results.enum_input):
        sys.stderr.write("error: one of number or enum_input is required.\n")
        sys.exit(1)


def test_envVar(results):
    var = os.getenv("ENVAR")
    if var != "theValue":
        sys.stderr.write(
            "error: ENVAR environment variable must be set to 'theValue'.\n")
        sys.exit(1)


def test_cwd_envVar(results):
    if not results.no_opts:
        homeDir = os.getenv("HOME")
        if homeDir != os.getenv("PWD"):
            sys.stderr.write("error: HOME environment variable must be set to the current"
                             " working directory.\n")
            sys.exit(1)


def test_config_file(results):
    if results.config_file:
        with(open(results.config_file, 'r')) as co:
            config_string = co.read()
            if config_string != "# This is a demo configuration file\nnumInput=4\nstrInput='coin;plop'":
                sys.stderr.write(
                    "error: invalid configuration file:\n %s\n" % config_string)
                sys.exit(1)


def test_conditional_output_paths(results):
    if results.cond_out:
        path = "{0}_default.txt".format(results.output_file)
        if results.string and results.number > 10:
            path = "{0}_{1}_{2}.txt".format(
                results.output_file, results.string, results.number)
        elif results.string:
            path = "{0}_{1}.txt".format(results.output_file, results.string)

        with open(results.output_file + "_out1.txt", 'w') as f:
            f.write("File content")
        stripped_extensions = [".one", ".two", ".three", ".four", ".five"]
        for extension in stripped_extensions:
            path = path.replace(extension, "")
        with open(path, 'w') as f:
            f.write("File content")
    else:
        with open(results.output_file, 'w') as f:
            f.write("File content")


def main(args=None):
    parser = argparse.ArgumentParser(
        description="A tool to test Boutiques",
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-c', '--config_file',
                        type=lambda x: file_exists(parser, x),
                        help='A config file with a number.')
    parser.add_argument('-i', '--string_input', nargs='+',
                        help='One or more strings.')
    parser.add_argument('-l', '--int_input', nargs='+',
                        help='One or more ints.', type=int)
    parser.add_argument('-t', '--file_list', nargs='+', help='One or more files.',
                        type=lambda x: file_exists(parser, x))
    parser.add_argument('file', metavar='file_input',
                        type=lambda x: file_exists(parser, x),
                        nargs=1, help='Any existing file.')
    parser.add_argument('-f', '--flag', action='store_true', help='A flag.')
    parser.add_argument('-n', '--number', type=int,
                        help='A number. Cannot be used when enum_input is used')
    parser.add_argument('-s', '--string', help='A string')
    parser.add_argument('-e', '--enum_input',
                        type=lambda x: is_valid_enum_value(parser, x),
                        nargs=1, help='A string in {"val1", "val2", "val3"}.')
    parser.add_argument('output_file',
                        help='The output file.')
    parser.add_argument('--no-opts', action='store_true',
                        help='Ignore container options.')
    parser.add_argument('--cond_out', action='store_true',
                        help='Create conditional output Files')

    results = parser.parse_args() if args is None else parser.parse_args(args)

    test_mutex_group(results)
    test_one_is_required_group(results)
    test_envVar(results)
    test_cwd_envVar(results)
    test_config_file(results)
    sys.stdout.write("This is stdout")
    sys.stderr.write("This is stderr")
    test_conditional_output_paths(results)


if __name__ == "__main__":
    main()

#!/usr/bin/env python

import argparse, os, sys

def file_exists(parser, file_name):
    if not os.path.exists(file_name):
        parser.error("File not found: %s" % file_name)
    return file_name
        
def is_valid_enum_value(parser, value):
    if not value in ['val1', 'val2', 'val3']:
        parser.error("Invalid enum value: %s" % value)
    return value
        
def main(args=None):
    parser=argparse.ArgumentParser(description="A tool to test Boutiques", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-c', '--config_file', type=lambda x:file_exists(parser,x),
                         help='A config file with a number.')
    parser.add_argument('-i', '--string_input', nargs='+', help='One or more strings.')
    parser.add_argument('-l', '--int_input', nargs='+', help='One or more ints.', type=int)
    parser.add_argument('file', metavar='file_input',
                        type=lambda x: file_exists(parser, x),
                        nargs=1, help='Any existing file.')
    parser.add_argument('-f', '--flag', action='store_true', help='A flag.')
    parser.add_argument('-n', '--number', type=int, help='A number. Cannot be used when enum_input is used')
    parser.add_argument('-s', '--string', help='A string')
    parser.add_argument('-e', '--enum_input',
                        type=lambda x: is_valid_enum_value(parser, x),
                        nargs=1, help='A string in {"val1", "val2", "val3"}.')
    parser.add_argument('output_file',
                         help='The output file.')
   

    results=parser.parse_args() if args is None else parser.parse_args(args)

    if results.number and results.enum_input:
        sys.stderr.write("error: number and enum_input are mutually exclusive.\n")
        sys.exit(1)

    if (not results.number) and (not results.enum_input):
        sys.stderr.write("error: one of number or enum_input is required.\n")
        sys.exit(1)
   
    var = os.getenv("ENVAR")
    if var != "theValue":
        sys.stderr.write("error: ENVAR environment variable must be set to 'theValue'.\n")
        sys.exit(1)

    homeDir = os.getenv("HOME")
    if homeDir != os.getenv("PWD"):
        sys.stderr.write("error: HOME environment variable must be set to the current"
                         " working directory.\n")
        sys.exit(1)

    with(open(results.config_file,'r')) as co:
        config_string = co.read()
        if config_string != "# This is a demo configuration file\nnumInput=4\nstrInput='coin;plop'":
            sys.stderr.write("error: invalid configuration file:\n %s\n" % config_string)
            sys.exit(1)
        
    sys.stdout.write("This is stdout")
    sys.stderr.write("This is stderr")
    with open(results.output_file, 'w') as f:
        f.write("File content")

if  __name__ == "__main__":
    main()

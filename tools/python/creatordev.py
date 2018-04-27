from argparse import ArgumentParser
import boutiques.creator as bc

parser = ArgumentParser(description="my tool description")
parser.add_argument('myarg1', action="store", help="my help 1")
parser.add_argument('myarg2', action="store", help="my help 2")
parser.add_argument("--myarg3", "-m", action="store", help="my help 3")

subparser = parser.add_subparsers(help="the choices you will make")
                                  # dest="choicer")

sb1 = subparser.add_parser("option1", help="the first value")
sb1.add_argument("suboption1", help="the first sub option option")
sb1.add_argument("suboption2", help="the first sub option option")

sb1 = subparser.add_parser("option2", help="the second value")
sb1.add_argument("suboption2", help="the second sub option option")
sb1.add_argument("--suboptionflag1", "-s", help="the second sub option flag")
sb1.add_argument("--suboptionflag2", "-d", action="store_true",
                 help="the second sub option flag")

creatorObj = bc.CreateDescriptor(parser, execname='/path/to/myscript.py')

'''
Sample Docopt script for bosh import testing

Usage:
  test_import X a <list>...
  test_import X a b g
  test_import X b (--bar1=Number|--bar2=File) [--foo1=String|--foo2=<Number>|--foo3=File]
  test_import X b g (--bar1=Number|--bar2=File)
  test_import X c --d1=String --d2=Number --d3=File --d4=Flag --d5=<dummy>
  test_import Y <m1> <m2> <m31> <m41> [--desc1]
  test_import Y <m1> <m2> <m32> <m42> --desc2
  test_import -h | --help

Options:
  -h --help       Help descriptions
  --bar1=Number   requires b
  --bar2=File     requires b
  --foo1=String   requires bar1_bar2
  --foo2=<Number>   requires bar1_bar2
  --foo3=File     requires bar1_bar2
  --d1=String     string type
  --d2=Number     number type [default: 50]
  --d3=File       file type
  --d4=Flag       flag type
  --d5=<dummy>    non-supported type
  --desc1         desc1 d3$c&p+0s ~!@#$%^&*()_+=-
  --desc2         desc2 descriptions
'''


# Dummy code
def foo(bar):
    pass

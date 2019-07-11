'''
Sample Docopt script for bosh import testing

Usage:
  test_import X a <list>...
  test_import X b (--bar1|--bar2) [--foo1|--foo2|--foo3]
  test_import X c --d1=String --d2=Number --d3=File --d4=Path --d5=<dummy>
  test_import Y <m1> <m2> <m31> <m41> --desc1
  test_import Y <m1> <m2> <m32> <m42> --desc2
  test_import -h | --help

Options:
  -h --help     Help descriptions
  --d1=String   string type
  --d2=Number   number type
  --d3=File     file type
  --d4=Path     path type
  --d5=<dummy>  non-supported type
  --desc1       desc1 d3$c&p+0/\/s \b\f\n\r\t\\
  --desc2       desc2 descriptions
'''

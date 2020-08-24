#!/usr/bin/env python


def raise_error(error_class, message, r=None):
    if r is not None:
        raise error_class("[ ERROR ({1}) ] {0}"
                          .format(message, r.status_code))
    else:
        raise error_class("[ ERROR ] {0}"
                          .format(message))


def print_info(message, r=None):
    if r is not None:
        print("[ INFO ({1}) ] {0}".format(message, r.status_code))
    else:
        print("[ INFO ] {0}".format(message))


def print_warning(message):
    print("[ WARNING ] {0}".format(message))


def print_error(message):
    print("[ ERROR ] {0}".format(message))

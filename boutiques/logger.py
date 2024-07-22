#!/usr/bin/env python


def raise_error(error_class, message, r=None):
    if r is not None:
        raise error_class(f"[ ERROR ({r.status_code}) ] {message}")
    else:
        raise error_class(f"[ ERROR ] {message}")


def print_info(message, r=None):
    if r is not None:
        print(f"[ INFO ({r.status_code}) ] {message}")
    else:
        print(f"[ INFO ] {message}")


def print_warning(message):
    print(f"[ WARNING ] {message}")


def print_error(message):
    print(f"[ ERROR ] {message}")

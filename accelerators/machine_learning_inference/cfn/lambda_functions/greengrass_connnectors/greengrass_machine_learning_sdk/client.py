#
# Copyright 2010-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#


def client(client_type, **kwargs):
    if client_type == 'inference':
        from .inference import Client
    elif client_type == 'feedback':
        from .feedback import Client
    else:
        raise Exception('Client type {} is not recognized.'.format(repr(client_type)))

    return Client(**kwargs)

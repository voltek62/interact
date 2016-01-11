import os
from urllib.error import HTTPError
from urllib.request import urlopen
from flask import Flask, redirect

from . import util

def download_file_and_redirect(**kwargs):
    """
    Must be called with username, file_url, config keyword args.

    Downloads the file from file_url and saves it into the COPY_PATH in config.
    """
    username = kwargs['username']
    file_url = kwargs['file_url']
    config = kwargs['config']

    assert username and file_url and config

    try:
        file_contents = _get_remote_file(config, file_url)
        destination = os.path.basename(file_url)
        path = util.construct_path(config['COPY_PATH'], locals())

        # destination might change if the file results in a copy
        destination = _write_to_destination(
            file_contents, path, destination, config)
        #print(' * Wrote {}'.format(path + '/' + destination))
        util.chown(username, path, destination)

        redirect_url = util.construct_path(
            config['REDIRECT_PATH'], locals())
        return redirect(redirect_url)

    except HTTPError:
        return 'Source file "{}" does not exist or is not accessible.'.\
            format(file_url)

def _get_remote_file(config, source):
    """Fetches file, throws an HTTPError if the file is not accessible."""
    assert source.startswith(config['ALLOWED_DOMAIN'])
    return urlopen(source).read().decode('utf-8')

def _write_to_destination(file_contents, path, destination, config):
    """Write file to destination on server."""

    # check that this filetype is allowed (ideally, not an executable)
    assert '.' in destination and \
        destination.split('.')[-1] in config['ALLOWED_FILETYPES']

    if os.path.exists(os.path.join(path, destination)):
        root = destination.rsplit('.', 1)[0]
        suffix = destination.split('.')[-1]
        destination = '{}-copy.{}'.format(root, suffix)
        return _write_to_destination(file_contents, path, destination, config)

    # make user directory if it doesn't exist
    os.makedirs('/'.join(path.split('/')[:-1]), exist_ok=True)

    # write the file
    open(os.path.join(path, destination), 'wb').write(file_contents.encode('utf-8'))

    return destination

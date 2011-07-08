#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2011, Pontus Lundkvist <plundra@lavabit.com>
# 
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
# 
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import os
import mimetypes
import bottle
import logging

from urllib2 import URLError

import config
import putils

_log = logging.getLogger("es3main")

def list(directory):
    """List content of directory"""
    output = "<ul>"

    for entry in [".."] + os.listdir(directory):
        # Check if dir, add slash
        if os.path.isdir(os.path.join(directory, entry)):
            entry += "/"
        output += """<li><a href="%s">%s</a></li>""" % (entry, entry)

    output += "</ul>"
    return output

def replicate(data, path):
    """Replicate file to slave"""
    _log.info("Sending copy of %s to %s" % (path, config.REPLICATION_URL))
    try:
        putils.httpput(os.path.join(config.REPLICATION_URL, path), data,
                       {"X-ES3-COPY": True})
    except URLError, e:
        _log.error("Failed to replicate %s: %s" % (path, e))
    
@bottle.get("/:path#[a-zA-Z0-9./]*#")
def get(path):
    """Method to deliver requested files"""
    
    # Set filepath based on request-URI
    filepath = os.path.realpath(os.path.join(config.STORAGE_DIR, path))
        
    # Double-check that the requested file is within STORAGE_DIR
    if not filepath.startswith(config.STORAGE_DIR):
        bottle.abort(403, "Forbidden")
    
    # Check if requested path is a directory
    if os.path.isdir(filepath):
        if not bottle.request.path.endswith("/"):
            bottle.redirect(bottle.request.path + "/")
        else:
            return list(filepath)
                
        
    # Check if file exists
    if not os.path.isfile(filepath):
        bottle.abort(404, "Not found")
    
    # Try guess content-type based on file extension
    guess_type = mimetypes.guess_type(filepath)[0]
    
    # Set type if found, else fall back to plain/text
    bottle.response.headers["Content-Type"] = guess_type or "plain/text"

    # Open file and return data
    return open(filepath).read()

@bottle.put("/:path#[a-zA-Z0-9./]*#")
def put(path):
    """Method to store file on disk"""
    
    # Set filepath based on request-URI
    filepath = os.path.realpath(os.path.join(config.STORAGE_DIR, path))
    
    # Double-check that the requested file is within STORAGE_DIR
    if not filepath.startswith(config.STORAGE_DIR):
        bottle.abort(403, "Verboten")

    # Don't overwrite files
    if os.path.exists(filepath):
        bottle.abort(409, "File exists")
    
    filedata = bottle.request.body.read()
    
    with open(filepath, "wb") as f:
        f.write(filedata)

    # Was this a copy or should make a copy somewhere?
    # Check for querystring or header noting this.
    if not (bottle.request.query.get("copy") or bottle.request.headers.get("X-ES3-COPY")):
        _log.info("Making replica of %s" % path)
        replicate(filedata, path)
    else:
        _log.info("No need for a copy")
        
    bottle.response.status = 201
    return "Created"

if __name__ == "__main__":
    logging.basicConfig(level=logging.NOTSET)
    assert os.path.isdir(config.STORAGE_DIR), "STORAGE_DIR exists and isdir()"
    bottle.run(host=config.HTTP_HOST, port=config.HTTP_PORT)

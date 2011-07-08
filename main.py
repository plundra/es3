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
import time
import mimetypes
import bottle

STORAGE_DIR = "/tmp/es3storage"

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

@bottle.get("/:path#[a-zA-Z0-9./]*#")
def get(path):
    """Method to deliver requested files"""
    
    # Set filepath based on request-URI
    filepath = os.path.realpath(os.path.join(STORAGE_DIR, path))
        
    # Double-check that the requested file is within STORAGE_DIR
    if not filepath.startswith(STORAGE_DIR):
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
    filepath = os.path.realpath(os.path.join(STORAGE_DIR, path))
    
    # Double-check that the requested file is within STORAGE_DIR
    if not filepath.startswith(STORAGE_DIR):
        bottle.abort(403, "Verboten")

    # Don't overwrite files
    if os.path.exists(filepath):
        bottle.abort(409, "File exists")
    
    with open(filepath, "wb") as f:
        f.write(bottle.request.body.read())

    bottle.response.status = 201
    return "Created"

if __name__ == "__main__":
    assert os.path.isdir(STORAGE_DIR), "STORAGE_DIR exists and isdir()"
    bottle.run(host="0.0.0.0", port=7070)

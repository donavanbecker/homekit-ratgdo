#!/usr/bin/env python3
#
# This script converts standard web content files (html, css, etc) into a C++ language
# header file that is included in the program body.  The files are compressed and use
# PROGMEM keyword to store in Flash to save RAM.
#
# With thanks to https://github.com/mitchjs for removal of dependencies on external gzip/sed/xxd 
# 
# Copyright (c) 2023 David Kerr, https://github.com/dkerr64
#
import os
import shutil
import base64
import zlib
import gzip

sourcepath = "src/www"
targetpath = sourcepath + "/build"

filenames = next(os.walk(sourcepath), (None, None, []))[2]
print("Compressing and converting files from " + sourcepath + " into " + targetpath)

# Start by deleting the target directory, then creating empty one.
try:
    shutil.rmtree(targetpath)
except FileNotFoundError:
    pass
os.mkdir(targetpath)

# calculate a CRC32 for each file and base64 encode it, this will change if the
# file contents are changed.  We use this to control browser caching.
file_crc = {}
for file in filenames:
    # skip hidden files
    if file[0] == ".":
        continue

    # skip status.json
    if file == "status.json":
        continue

    with open(sourcepath + "/" + file, "rb") as f:
        # read contents of the file
        data = f.read()
        crc32 = (
            base64.urlsafe_b64encode(zlib.crc32(data).to_bytes(4, byteorder="big"))
            .decode()
            .replace("=", "")
        )
        f.close()
        file_crc[file] = crc32
        print("CRC: " + crc32 + " (" + file + ")")

# Open webcontent file and write warning header...
wf = open(targetpath + "/webcontent.h", "w")
wf.write("/**************************************\n")
wf.write(" * Autogenerated DO NOT EDIT\n")
wf.write(" **************************************/\n")
wf.write("#include <unordered_map>\n")
wf.write("#include <string>\n")
wf.flush()

varnames = []
# now loop through each file...
for file in filenames:
    # skip hidden files
    if file[0] == ".":
        continue

    # skip status.json
    if file == "status.json":
        continue

    # create gzip file name
    gzfile = targetpath + "/" + file + ".gz"
    # create variable names
    varnames.append(("/" + file, gzfile.replace(".", "_").replace("/", "_").replace("-", "_"), file_crc[file]))
    # get file type
    t = file.rpartition(".")[-1]
    # if file matches, add true crc to ?v=CRC-32 marker and create the gzip
    if (t == "html") or (t == "htm") or (t == "js"):
        with open(sourcepath + "/" + file, 'rb') as f_in, gzip.open(gzfile, 'wb') as f_out:
            # read contents of the file
            data = f_in.read()
            # loop through each file that could be referenced
            for f_name, crc32 in file_crc.items():
                # Replace the target string with real crc
                data = data.replace(bytes(f_name + "?v=CRC-32", 'utf-8'), bytes(f_name + "?v=" + crc32, 'utf-8'))
            f_out.write(data)
            f_out.close()
    else :
        with open(sourcepath + "/" + file, 'rb') as f_in, gzip.open(gzfile, 'wb') as f_out:
            f_out.writelines(f_in)
            f_out.close()
   
    # create the 'c' code
    # const unsigned char src_www_build_apple_touch_icon_png_gz[] PROGMEM = {
    # const unsigned int src_www_build_apple_touch_icon_png_gz_len = 2721;
    wf.write("const unsigned char %s[] PROGMEM = {\n" % gzfile.replace(".", "_").replace("/", "_").replace("-", "_") )
    count = 0
    with open(gzfile, 'rb') as f:
        bytes_read = f.read(12)
        while bytes_read:
            count = count + len(bytes_read)
            wf.write('  ')
            for b in bytes_read:
                wf.write('0x%02X,' % b)
            wf.write('\n')
            bytes_read = f.read(12)
    
    wf.write('};\n')
    wf.write("const unsigned int %s_len = %d;\n\n" % (gzfile.replace(".", "_").replace("/", "_").replace("-", "_"), count) )

wf.flush()

# Add possible MIME types to the file...
wf.write(
    """
const char type_svg[]  = "image/svg+xml";
const char type_bmp[]  = "image/bmp";
const char type_gif[]  = "image/gif";
const char type_jpeg[] = "image/jpeg";
const char type_jpg[]  = "image/jpeg";
const char type_png[]  = "image/png";
const char type_tiff[] = "image/tiff";
const char type_tif[]  = "image/tiff";
const char type_txt[]  = "text/plain";
const char type_[]     = "text/plain";
const char type_htm[]  = "text/html";
const char type_html[] = "text/html";
const char type_css[]  = "text/css";
const char type_js[]   = "text/javascript";
const char type_mjs[]  = "text/javascript";
const char type_json[] = "application/json";

"""
)

# Use an unordered_map so we can lookup the data, length and type based on filename...
wf.write(
    "const std::unordered_map<std::string, std::tuple<const unsigned char *, const unsigned int, const char *, std::string>> webcontent = {"
)
n = 0
for file, var, crc32 in varnames:
    t = ""
    if file.find(".") > 0:
        t = file.rpartition(".")[-1]
    # Need comma at end of every line except last one...
    if n > 0:
        wf.write(",")
    wf.write('\n  { "' + file + '", {' + var + ", " + var + "_len, type_" + t + ', "' + crc32 + '"' + "} }")
    n = n + 1

# All done, close the file...
wf.write("\n};\n")
wf.close()

print("processed " + str(len(varnames)) + " files")

#! /usr/bin/python
# canonurls.py - canonicalize and clean a list of URLs.  -*- encoding: utf-8 -*-
# Copyright © 2010, 2013 Zack Weinberg
# Portions © 2009 Serge Broslavsky
#
# Copying and distribution of this program, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved.  This program is offered as-is,
# without any warranty.

import fileinput
import multiprocessing
import optparse
import os
import sys

import http.cookiejar
import http.client
import urllib.parse

# We have to do the HTTP queries by hand because of urllib bugs and
# sites that misbehave if they see its default user-agent.  This means
# we have to create a shim between httplib and cookielib, because
# cookielib assumes you're using urllib.  Thanks to Serge Broslavsky
# for this shim class:
# http://stackoverflow.com/questions/1016765/how-to-use-cookielib-with-httplib-in-python

class HTTPRequest(object):
    """
    Data container for HTTP request (used for cookie processing).
    """

    def __init__(self, url, headers={}, method='GET'):
        self._url = urllib.parse.urlsplit(urllib.parse.urldefrag(url)[0])
        self._headers = {
          "User-Agent":
            "Mozilla/5.0 (Macintosh; rv:24.0) Gecko/20100101 Firefox/24.0"
        }
        self._method = method

        for key, value in list(headers.items()):
            self.add_header(key, value)

    def has_header(self, name):
        return name in self._headers

    def add_header(self, key, val):
        self._headers[key.capitalize()] = val

    def add_unredirected_header(self, key, val):
        self._headers[key.capitalize()] = val

    def is_unverifiable(self):
        return True

    def get_type(self):
        return self._url.scheme

    def get_full_url(self):
        return self._url.geturl()

    def get_header(self, header_name, default=None):
        return self._headers.get(header_name.capitalize(), default)

    def get_host(self):
        return self._url.netloc

    get_origin_req_host = get_host

    def get_headers(self):
        return self._headers

    def fire(self):
        if self._url.scheme == 'http':
            conn = http.client.HTTPConnection(self._url.netloc, timeout=30)
        elif self._url.scheme == 'https':
            conn = http.client.HTTPSConnection(self._url.netloc, timeout=30)
        else:
            raise IOError("unsupported URL '%s'" % self.get_full_url())
        path = self._url.path
        if self._url.query != "":
            path = path + '?' + self._url.query

        conn.request(self._method, path, headers=self._headers)
        resp = conn.getresponse()
        # patch httplib response to look like urllib2 response,
        # for the sake of cookie processing
        resp.info = lambda: resp.msg
        return resp

#
# Logging.  Note that sys.stderr is shared among all worker processes
# so we must take care to always print complete lines in a single
# write() call.  The obsessive flushing may or may not be necessary
# depending on exactly which Python version you have.
#

options = None
mypid   = None

def fmt_status(resp):
    return str(resp.status) + " " + str(resp.reason)

def fmt_cookies(jar):
    if not options.verbose: return ""
    if not jar: return ""
    return " [" + " ".join(cookie.name + "=" + cookie.value
                           for cookie in jar) + "]"

def log_start(orig_url):
    if not options.verbose: return
    sys.stderr.write("{:05}: {} ...\n".format(mypid, orig_url))
    sys.stderr.flush()

def log_success(orig_url, canon, resp):
    if not options.verbose: return
    if resp.status != 200:
        sys.stderr.write("{:05}: {} => {} ({})\n"
                         .format(mypid, orig_url, canon, fmt_status(resp)))
    else:
        sys.stderr.write("{:05}: {} => {}\n".format(mypid, orig_url, canon))
    sys.stderr.flush()

def log_fail(orig_url, resp):
    if not options.verbose: return
    sys.stderr.write("{:05}: {} => {}\n"
                     .format(mypid, orig_url, fmt_status(resp)))
    sys.stderr.flush()


def log_good_redirect(orig_url, redir, resp, cookies):
    if not options.verbose: return
    sys.stderr.write("{:05}: {} => {} to {}{}\n"
                     .format(mypid, orig_url, fmt_status(resp), redir,
                             fmt_cookies(cookies)))
    sys.stderr.flush()

def log_bad_redirect(orig_url, resp):
    if not options.verbose: return
    sys.stderr.write("{:05}: {} => {} to nowhere\n"
                     .format(mypid, orig_url, fmt_status(resp)))
    sys.stderr.flush()

def log_redirect_loop(orig_url, redir, resp):
    if not options.verbose: return
    sys.stderr.write("{:05}: {} => {} to {}, loop detected\n"
                     .format(mypid, orig_url, fmt_status(resp), redir))
    sys.stderr.flush()

def log_declined_redirect(orig_url, canon, redir, resp):
    if not options.verbose: return
    sys.stderr.write("{:05}: {} => {} ({} to {})\n"
                     .format(mypid, orig_url, canon, fmt_status(resp), redir))
    sys.stderr.flush()

def log_env_error(orig_url, exc):
    if exc.filename:
        sys.stderr.write("{:05}: {} => {}: {}\n"
                         .format(mypid, orig_url, exc.filename, exc.strerror))
    else:
        sys.stderr.write("{:05}: {} => {}\n"
                         .format(mypid, orig_url, exc.strerror))
    sys.stderr.flush()

def log_http_error(orig_url, exc):
    sys.stderr.write("{:05}: {} => HTTP error ({}): {}\n"
                     .format(mypid, orig_url, exc.__class__.__name__, str(exc)))
    sys.stderr.flush()

def log_gen_error(orig_url, exc):
    sys.stderr.write("{:05}: {} => {}\n"
                     .format(mypid, orig_url, str(exc)))
    sys.stderr.flush()


# Custom canonization function which treats "foo.com/blah" as equivalent to
# "http://foo.com/blah" rather than as a partial URL with no host or scheme
# (as urlparse.urlsplit does).
def precanonize(url):
    (scheme, sep, rest) = url.partition('://')
    if sep == '':
        rest = scheme
        scheme = 'http'
    else:
        scheme = scheme.lower()
    (host, sep, path) = rest.partition('/')
    if path == '':
        path = '/'
    else:
        path = '/' + path
    host = host.lower()
    return scheme + "://" + host + path

# Custom canonization function which forces "http://foo.com" to
# "http://foo.com/" and removes empty params/query/fragment.
def postcanonize(url):
    (scheme, netloc, path, params, query, fragment) = \
        urllib.parse.urlparse(url)
    if (scheme == 'http' or scheme == 'https') and path == '':
        path = '/'
    return urllib.parse.urlunparse((scheme, netloc, path, params, query, fragment))

def is_siteroot(url):
    parsed = urllib.parse.urlparse(url)
    return ((parsed.path == '' or parsed.path == '/')
            and parsed.params == ''
            and parsed.query == ''
            and parsed.fragment == '')

def chase_redirects(orig_url):
    global mypid
    if mypid is None: mypid = os.getpid()

    seen = set()
    cookies = http.cookiejar.CookieJar()
    orig_url = orig_url.strip()
    url = precanonize(orig_url)
    log_start(orig_url)
    try:
        while True:
            req = HTTPRequest(url)
            url = req.get_full_url()

            seen.add(url)
            cookies.add_cookie_header(req)
            resp = req.fire()
            resp.read()

            if 200 <= resp.status < 300:
                # done, yay
                log_success(orig_url, url, resp)
                return (orig_url, url)

            if resp.status not in (301, 302, 303, 307):
                # treat any 1xx and 3xx codes that we don't understand as
                # hard errors, as well as 4xx/5xx
                log_fail(orig_url, resp)
                return (orig_url, None)

            # Redirected, so where to?
            location = resp.getheader("Location")
            if location is None:
                location = resp.getheader("Uri")
            if location is None:
                log_bad_redirect(orig_url, resp)
                return (orig_url, None)

            # pick up any cookies attached to the redirection
            cookies.extract_cookies(resp, req)

            # update the url
            newurl = urllib.parse.urljoin(url, location)
            if newurl in seen:
                log_redirect_loop(orig_url, newurl, resp)
                return (orig_url, None)

            if options.sites_only and is_siteroot(url):
                # If this redirect added nontrivial path, query, or
                # fragment components to the URL, stop and return the
                # URL _before_ the redirect.  For instance, this
                # causes us to canonicalize blogger.com to
                # http://www.blogger.com/ instead of
                # https://accounts.google.com/ServiceLogin?service=blogger&...
                components = urllib.parse.urlsplit(newurl)
                if ((components.path and components.path != '/')
                    or components.query or components.fragment):
                    log_declined_redirect(orig_url, url, newurl, resp)
                    return (orig_url, url)

            log_good_redirect(orig_url, newurl, resp, cookies)
            url = newurl
            # and loop

    # Do not allow any exceptions to escape, or the entire job will crash.
    except http.client.HTTPException as e:
        log_http_error(orig_url, e)
        return (orig_url, None)

    except EnvironmentError as e:
        log_env_error(orig_url, e)
        return (orig_url, None)

    except Exception as e:
        log_gen_error(orig_url, e)
        return (orig_url, None)

def sanitize_urls(urls):
    results = {}
    workers = multiprocessing.Pool(options.parallel)
    pid = os.getpid()

    for (original, redir) in workers.imap_unordered(chase_redirects, urls,
                                                    chunksize=10):
        if redir is None:
            continue

        canon = postcanonize(redir)

        if canon in results:
            if options.verbose:
                sys.stderr.write("{:05}: {} => duplicates {}\n"
                                 .format(pid, original, results[canon]))
        else:
            results[canon] = original

    workers.close()
    workers.join()

    for url in sorted(results.keys()):
        sys.stdout.write(url + "\n")

if __name__ == '__main__':

    op = optparse.OptionParser(
        usage="usage: %prog [options] lists ... > output",
        version="%prog 1.0")
    op.add_option("-q", "--quiet",
                  action="store_false", dest="verbose", default=True,
                  help="don't print progress messages to stderr")
    op.add_option("-p", "--parallel",
                  action="store", dest="parallel", type="int", default=10,
                  help="number of simultaneous HTTP requests to issue")
    op.add_option("-S", "--sites-only",
                  action="store_true", dest="sites_only", default=False,
                  help="Don't follow redirects away from a site root")

    (options, args) = op.parse_args()
    sanitize_urls(fileinput.input(args))

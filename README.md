# emrCounter


## About

Philosopedia is a simple Python app that attempts to link various entries on Wikipedia to the Wikipedia entry for 'Philosophy', in an attempt to validate the above assertion.

This has been done before (see: [here](http://ryanelmquist.com/cgi-bin/xkcdwiki) and [here](http://xefer.com/wikipedia), but I wanted to not only open-source the code, but also keep a running inventory of words that both were and weren't able to link to Philosophy.

## Dependencies/Requirements

 * Developed/tested on Python 2.6.1
 * All required Python deps can be installed using PyPy or similar
 * [boto](http://code.google.com/p/boto/) for AWS API interaction
 * [bottle](http://bottlepy.org/docs/dev/) for Sinatra-like web routing
 * [pytz](http://pytz.sourceforge.net/) for timezone junk

## Installing/Running

 * replace <aws_access_key> and <aws_secret_key> with the appropriate values in counter.py
 * $ python counter.py
 * browse to localhost:8080/page







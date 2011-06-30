# emrCounter

## About

emrCounter is a dead-simple python app that aims to illustrate the amount of work being done by a set of Amazon Elastic MapReduce (EMR) jobs running under a given AWS account. 
The jobs themselves log metrics to Amazon SimpleDB, and the emrCounter app serves up a page that shows an animated view of those metrics.

Credit for the cool Apple-style flip counter animation goes to [Chris Nanney](http://cnanney.com/journal/code/apple-style-counter-revisited/)

## Dependencies/Requirements

 * Developed/tested on Python 2.6.1
 * The easiest way to get all the required Python deps is by using [pip](http://pypi.python.org/pypi/pip) and [virtualenv](http://pypi.python.org/pypi/virtualenv)
 * emrCounter uses the following Python dependencies:
    * [boto](http://code.google.com/p/boto/) for AWS API interaction
    * [bottle](http://bottlepy.org/docs/dev/) for Sinatra-like web routing
    * [pytz](http://pytz.sourceforge.net/) for timezone junk

## Installing/Running

 * $ pip install -E path/to/virtualenv -r pip_requirements.txt
 * replace the appropriate values in config.ini
 * $ python counter.py
 * browse to localhost:8080/page







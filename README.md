# sparqlbin.com

A generic SPARQL processor and sharing tool. Like [pastebin.com](http://pastebin.com) or [SQL fiddle](http://sqlfiddle.com/) for SPARQL queries.

There is an example deployment of the service at [sparqlbin.com](http://sparqlbin.com/) that currently uses a CouchDB provided by [Cloudant](http://cloudant.com/) till I get the chance to set it up locally, so be gentle with the sharing please. 

## Dependencies

* [SPARQLWrapper](http://sparql-wrapper.sourceforge.net/ "SPARQL Endpoint interface to Python") for delegating the queries to endpoints
* [Apache CouchDB](http://couchdb.apache.org/) as a backend for managing the sharing of the queries

## To dos

* set up CouchDB locally
* integrate Alvaro's RDF vis and SPARQL query builder

## License and Acknowledgements

The software provided here is in the public domain. The initial idea has been developed together with [Richard Cyganiak](https://github.com/cygri).
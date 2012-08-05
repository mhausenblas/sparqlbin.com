# sparqlbin.com

A generic SPARQL processor and sharing tool. Like [pastebin.com](http://pastebin.com) or [SQL fiddle](http://sqlfiddle.com/) for SPARQL queries.

An example deployment of the service at [sparqlbin.com](http://sparqlbin.com/) that currently uses a CouchDB provided by [Cloudant](http://cloudant.com/) till I get the chance to set it up locally, so be gentle with the sharing please. 

There is also a [documentation](https://github.com/mhausenblas/sparqlbin.com/wiki) of the deployment and the API available.

## Dependencies

* [SPARQLWrapper](http://sparql-wrapper.sourceforge.net/ "SPARQL Endpoint interface to Python") for delegating the queries to endpoints
* [Apache CouchDB](http://couchdb.apache.org/) as a backend for managing the sharing of the queries

## Release Planning

See [milestones](https://github.com/mhausenblas/sparqlbin.com/issues/milestones) on GitHub.

## License and Acknowledgements

The software provided here is in the public domain. The initial idea has been developed together with [Richard Cyganiak](https://github.com/cygri).
# CIDE-APP
## API ENDPOINTS
- [/](http://apps.klimeto.com/cide-app)
- [/establishment](http://apps.klimeto.com/cide-app/establishment)
- [/inspection](http://apps.klimeto.com/cide-app/inspection)

## API verzus APP authentication
For a REST service you do not need Flask-Login. Typically in web services you do not store client state (what Flask-Login does), instead you authenticate each and every request. Flask-HTTPAuth does this for you.

You would use both only if you have an application that has a web component and a REST API component. In that case Flask-Login will handle the web app routes, and Flask-HTTPAuth will handle the API routes.

## API endpoint:
### GET Filter establishments /api/establishment
By defaul returns all records, but can be filtered by name /api/establishment?name=*value* aor oib /api/establishment?oib=*value*
### GET Inspections for a single establishment /api/inspection/establishmentcode
Lists basic metadata as inspection date and inspector full name.
In addition specific inspections metadata are provided if any created as described below.
### GET List of specific inspections type and inspectors assigned to these types /api/inspection/type
It used to get information for specific inspection creation
### POST Create coordinated inspection /api/inspection
curl -X POST -H "Content-Type: application/json" -d @data/insertinspection.json -u username:password
### POST Update coordinated inspection by adding specific inspection
curl -X POST -H "Content-Type: application/json" -d @data/updateinspection.json -u username:password

 

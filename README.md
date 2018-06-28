# CIDE-APP
## API ENDPOINTS
- [/](http://apps.klimeto.com/cide-app)
- [/establishment](http://apps.klimeto.com/cide-app/establishment)
- [/inspection](http://apps.klimeto.com/cide-app/inspection)

## API verzus APP authentication
For a REST service you do not need Flask-Login. Typically in web services you do not store client state (what Flask-Login does), instead you authenticate each and every request. Flask-HTTPAuth does this for you.

You would use both only if you have an application that has a web component and a REST API component. In that case Flask-Login will handle the web app routes, and Flask-HTTPAuth will handle the API routes.

## API requests examples:
###POST Create coordinated inspection @/api/inspection
curl -X POST -H "Content-Type: application/json" -d @data/createInspection.json 

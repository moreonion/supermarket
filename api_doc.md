# Supermarket API

- [URL](#root-url)
- [Resources](#resources)
- [Collections](#collections)
- [Documentation](#documentation)

## Root URL

https://api.supplychainge.org/api/v1/

## Resources
> root url + resource + identifier

#### Examples:
- https://supermarket.more-onion.at/api/v1/labels/1
- https://supermarket.more-onion.at/api/v1/products/1

### Methods
- GET: Retrieve a resource item
- PUT: Replace a resource item (providing the entire item)
- PATCH: Update a resource item (providing only changed attributes)
- DELETE: Delete a resource item

### Response body
#### GET, PUT, PATCH, DELETE
```json
{
  "item": {"…"},
  "errors": ["…"]
}
```
#### Error (4xx)
```json
{
  "message": "…",
  "errors": ["…"]
}
```

### Optional URL parameters for GET

#### Including/Excluding
- `only`: comma seperated list of attributes to fetch
- `include`: attribute(s) of related fields that should be included formatted as `<related name>.<field name>`, seperated by comma. 'all' includes all fields of the related item.
- `lang`: ISO language code to filter translations by language (instead of a translation object, only the value for the given language will be returned)

###### Examples
- https://supermarket.more-onion.at/api/v1/labels/1?include=products.name,meets_criterion.criterion.all
  → include product names and all criterion fields for a label item
- https://supermarket.more-onion.at/api/v1/products/1?only=id,name
  → show only id and name of a product
- https://supermarket.more-onion.at/api/v1/labels/1?lang=de
  → return only the German translation of label name, description, etc.

## Collections
> root url + resource

#### Examples:
- https://supermarket.more-onion.at/api/v1/labels
- https://supermarket.more-onion.at/api/v1/products

### Methods
- GET: Retrieve a specific listing of resources
- POST: Create a new resource item

### Response body
#### GET
```json
{
  "items": ["…"],
  "errors": ["…"],
  "pages": {
    "total": "…",
    "current": "…",
    "prev": "…",
    "prev_url": "…",
    "next": "…",
    "next_url": "…"
   }
}
```
#### POST
```json
{
  "item": {"…"},
  "errors": ["…"]
}
```
#### Error (4xx)
```json
{
  "message": "…",
  "errors": ["…"]
}
```

### Optional URL parameters for GET

#### Pagination
- `limit`: maximum number of items per page (default 20)
- `page`: which page to display (default 1)

###### Examples
- https://supermarket.more-onion.at/api/v1/labels?limit=10&page=2
  → limit labels per page to 10 and show page 2
- https://supermarket.more-onion.at/api/v1/products?limit=50
  → limit products per page to 50

#### Sorting
- `sort`: field name(s) to sort by, seperated by comma and preceeded by `-` to sort descending.

###### Examples
- https://supermarket.more-onion.at/api/v1/labels?sort=name
  → sort labels alphabetically by their name
- https://supermarket.more-onion.at/api/v1/products?sort=-id
  → sort products descending by their id

#### Including/Excluding
- `only`: comma seperated list of attributes to fetch
- `include`: attribute(s) of related fields that should be included formatted as `<related name>.<field name>`, seperated by comma. 'all' includes all fields of the related item.
- `lang`: ISO language code to filter translations by language (instead of a translation object, only the value for the given language will be returned)

###### Examples
- https://supermarket.more-onion.at/api/v1/labels?include=products.name,meets_criterion.criterion.all
  → include product names and all criterion fields for label items
- https://supermarket.more-onion.at/api/v1/products?only=id,name
  → show only id and name of each product
- https://supermarket.more-onion.at/api/v1/labels?lang=de
  → return only the German translation of label names, descriptions, etc.

#### Filtering
- `<field name>:<op>`: filter by a value using the given operator (no operator defaults to "equal")

##### Filter operators
- 'lt': lower (should only be used for numbers)
- 'le': lower or equal (should only be used for numbers)
- 'eq': equal
- 'ne': not equal
- 'ge': greater or equal (should only be used for numbers)
- 'gt': greater (should only be used for numbers)
- 'in': equal to one of serveral options, seperated by comma
- 'like': contains the value, case insensitive (can only be used for strings).

##### Filtering translations
When using filters with a translation object, the language to use for filtering needs to be appended to the fieldname, seperated by a dot.

###### Examples
- https://supermarket.more-onion.at/api/v1/labels?countries=AT
  → show only labels that are used in Austria
- https://supermarket.more-onion.at/api/v1/products?name.en:like=chocolate
  → show only products that have "chocolate" in their English name

## Documentation
> root url + 'doc' + resource

#### Examples:
- https://supermarket.more-onion.at/api/v1/doc/labels
- https://supermarket.more-onion.at/api/v1/doc/products

### Methods
- GET: Retrieve documentaion for a resource

### Response body
#### GET
```json
{
  "fields": {"…"},
  "link": "(link to collection)"
}
```

### Field description
```json
{
  "type": "…",
  "list": "(boolean)",
  "required": "(boolean)",
  "read-only": "(boolean)",
  "doc": "(only for related fields)",
  "fields": "(only for nested fields)"
}
```

- `type`: what type of value to expect, e.g. "string", "integer",…
  - "related": Relationship to another resource, represented by the related resources’ identifier. The link to this resource’s documentation page (if there is one) is included in `doc`.
  - "nested": A related item that is included (nested) in the result. The nested fields are described in `fields`. By default, only fields that do not have their own endpoint are nested.
  - "translation": Object containing language specific field values
- `list`: whether to expect a single item or a list of items of `type`
- `required`: whether the field is required (then it has to be included in POST and PUT requests)
- `read-only`: whether the field is read-only (read-only fields will be ignored in POST, PUT and PATCH requests)

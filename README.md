# backend-object-mapper
An object mapper for elasticsearch

## Contents
* [Requirements](#requirements)
* [Installation](#installation)
* [Setup](#setup)
* [Docs](#docs)
    * [Definition](#definition)
    * [Property Types](#property_types)
    * [Property Types Example](#property_types_example)
    * [Find Entity](#find_entity)
        * [Search by attribute](#search_by_attribute)
        * [Geo Query](#geoquery)
    * [Delete Entity](#delete_entity)
    * [Versioning](#versioning)
        * [Get all versions](#get_all_versions)
        * [Load a version](#load_a_version)
    * [Using Entity as Property](#using_entity_as_property)


## <a name="requirements">Requirements</a>
* Python 3.0+
* elasticsearch==5.3.0

## <a name="installation">Installation</a>
* ```pip install -r requirements.txt```
* ```python setup.py install```
* Elasticsearch instance running. Configuration to be updated in `env.sh`

## <a name="setup">Setup</a>
* Update the environment variables for elasticsearch in `env.sh` and run ```source ./env.sh```

## <a name="docs">Docs</a>

### <a name="definition">Definition</a>
Below is the definition of a custom entity
```python
from esorm.entity import StructuredEntity
from esorm.properties import *
from datetime import datetime

class CustomEntity(StructuredEntity):
    name = StringProperty(allowed_values=["custom"])
    uid = UniqueIdProperty()
    date = DateTimeProperty()
    
custom_entity = CustomEntity(name="custom",
                             uid="customuid",
                             date=datetime.utcnow())
                             
# OR

custom_entity = CustomEntity()
custom_entity.set_value('name', 'custom')
custom_entity.set_value('uid', 'customuid')
custom_entity.set_value('date', datetime.utcnow())

# Saving the object
custom_entity.save()
```

If any of the attributes is not given any value, default values will be assigned to them.
For `uid`, it will generate an internal uid.

### <a name="property_types">Property Types</a>
Following property types are currently supported:
* StringProperty (default: ")
* UniqueIdProperty (default: str()uuid.uuid4())
* IntegerProperty (default: -1)
* FloatProperty (default: float('inf'))
* ArrayProperty (default: [])
* JsonObjectProperty (default: {})
* DateTimeProperty (default: datetime.utcnow())
* GeocoordinateProperty (default: {})

Each property has following options:
* allowed_values
* allowed_values_from_url
* default

### <a name="property_types_example">Property Type Example</a>
```python
class CustomEntity(StructuredEntity):
    name = StringProperty(allowed_values=["custom"])
    
    # This argument makes a GET request to the specified URL and looks for "allowed_values" key for list of allowed_calues
    address = StringProperty(allowed_values_from_url="http://localhost:5000/")
    
    # The tuple below matches the range of the integers, lowed bound and uppr bound inclusive
    # (20, 30) means all numbers from 20 (inclusive) till 30 (inclusive)
    age = IntegerProperty(allowed_values=[43, (20, 30), 35])
    
    height = FloatProperty(allowed_values=[180.0, (120, 200)])
    
    dob = DateTimeProperty(datetime.utcnow())
    
    # Note: This field always must be named as "coordinates" to be able to query via geo queries
    coordinates = GeocoordinateProperty()
    
    # Note: This field must be named as "uid"
    # This field is mandatory
    uid = UniqueIdProperty()
    
    # Array Property
    phone = ArrayProperty(base_property=StringProperty())
```
Note: `uid` is mandatory to define, else `ValueError` is raised.

### <a name="find_entity">Find Entity</a>

#### Search by attribute
#### <a name="search_by_attribute">Search by attribute</a>
```python
# Returns a list of matching entities
CustomEntity.entities().get(name="custom")
```

#### <a name="geoquery">Geo Queries</a>
```python
# Returns list of matching entities
CustomEntity.entities().get(geo_near=({"lat": 17.45, "lon": 78.56}, 300))
```

`geo_near` is a `tuple`, which takes `dict` as the first argument, `distance` in `kilometers` as the second argument.

### <a name="delete_entity">Delete an Entity</a>
```python
custom_entity.delete()
```
Delete doesn't really delete the document, but will disable it for search.

## <a name="versioning">Versioning</a>
Versions of documents are maintained in a separate index located at the config provided in `esorm/config`

### <a name="get_all_versions">Get all versions</a>
```python
custom_entity.get_all_versions()
# Output
[2,1]
```
It returns all the version numbers available, greatest number depicting the latest version.

### <a name="load_a_version">Load a version</a>
```python
# Load a version
custom_entity.load_version(1)

# Save it (a new version is created)
custom_entity.save()
```

### <a name="delete_a_version">Delete a version</a>

## <a name="using_entity_as_property">Using Entity as Property</a>
Entities can also be used as properties.

```python
class NewEntity(StructuredEntity):
    uid = UniqueIdProperty()
    entity = CustomEntity()
    entity_list = ArrayProperty(base_property=CustomEntity())
    
new_entity = NewEntity(uid="new", entity=custom_entity, entity_list=[custom_entity])
print(new_entity)

# To get value as JSON (resolves nested JSON)
print(new_entity.get_value_as_json())
```

## Author
Mayank Chutani <br>

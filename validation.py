import jsonschema

from read_schema import read_with_id


def get_rec_dependencies(file_dependencies, store):
    for d in file_dependencies:
        if d not in store:
            store[d] = read_with_id(d)
            get_rec_dependencies(store[d].get("file_dependencies", []), store)


def get_resolver(schema):
    schema_store = {}
    get_rec_dependencies(schema.get("file_dependencies", []), schema_store)
    return jsonschema.RefResolver.from_schema(schema, store=schema_store)


def make_validator(schema, default_document, resolver=None, draft=jsonschema.Draft7Validator):
    if resolver is None:
        resolver = jsonschema.RefResolver.from_schema(schema)
    resolver.store[""] = default_document

    def data_callable(validator_instance, property_value, instance, schema):
        _schema = {}
        for pv in property_value:
            _schema[pv] = validator_instance.resolver.resolve_from_url(property_value[pv])

        for error in validator_instance.descend(instance, _schema):
            yield error

    def is_property_of_callable(validator_instance, property_value, instance, schema):
        keys = [k for k in property_value]
        if instance not in keys:
            msg = f"{instance} is not in {keys}."
            if len(msg) > 200: msg = "<instance> is not in <keys>."
            yield jsonschema.exceptions.ValidationError(msg)

    _mapping = {
        "isPropertyOf": is_property_of_callable,
        "data": data_callable
    }

    return jsonschema.validators.extend(draft, _mapping)(schema, resolver=resolver)


def validate(instance, schema):
    resolver = get_resolver(schema)
    validator = make_validator(schema, instance, resolver=resolver)
    return validator.validate(instance)


if __name__ == "__main__":
    import json

    with open('../states/state0.json', 'r', encoding="utf-8") as finst:
        test_instance = json.load(finst)
    with open('../resources/state_schema.json', 'r', encoding="utf-8") as fsche:
        test_schema = json.load(fsche)

    validate(test_instance, test_schema)

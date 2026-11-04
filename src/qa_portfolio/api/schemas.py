"""JSON Schemas for Restful-Booker responses (draft 2020-12).

`additionalProperties: false` makes the contract strict: a new or renamed field
in the response fails the test instead of slipping through unnoticed.
"""

BOOKING = {
    "type": "object",
    "required": ["firstname", "lastname", "totalprice", "depositpaid", "bookingdates"],
    "additionalProperties": False,
    "properties": {
        "firstname": {"type": "string"},
        "lastname": {"type": "string"},
        "totalprice": {"type": "integer", "minimum": 0},
        "depositpaid": {"type": "boolean"},
        "bookingdates": {
            "type": "object",
            "required": ["checkin", "checkout"],
            "additionalProperties": False,
            "properties": {
                "checkin": {"type": "string", "format": "date"},
                "checkout": {"type": "string", "format": "date"},
            },
        },
        "additionalneeds": {"type": "string"},
    },
}

CREATED_BOOKING = {
    "type": "object",
    "required": ["bookingid", "booking"],
    "additionalProperties": False,
    "properties": {
        "bookingid": {"type": "integer", "minimum": 1},
        "booking": BOOKING,
    },
}

BOOKING_ID_LIST = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["bookingid"],
        "properties": {"bookingid": {"type": "integer"}},
    },
}

TOKEN = {
    "type": "object",
    "required": ["token"],
    "additionalProperties": False,
    "properties": {"token": {"type": "string", "minLength": 10}},
}

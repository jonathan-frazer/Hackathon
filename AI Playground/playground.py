import re

def extract_json_string(input_string):
    # Use regex to find the first opening and last closing curly braces
    match = re.search(r'({.*})', input_string, re.DOTALL)
    if match:
        return match.group(1)  # Return the matched JSON string
    return None  # Return None if no match is found

# Example usage
input_string = '''extrastuff{
    "database": "LibraryDB",
    "tables": [
        {
            "name": "books",
            "columns": [
                {
                    "name": "id",
                    "type": "INTEGER",
                    "constraints": [
                        "PRIMARY KEY",
                        "AUTOINCREMENT"
                    ]
                },
                {
                    "name": "title",
                    "type": "VARCHAR(100)",
                    "constraints": [
                        "NOT NULL"
                    ]
                }
            ]
        }
    ]
}extasrsae'''

result = extract_json_string(input_string)
print(result)

import yaml

# Open and read the YAML file
with open('data.yaml', 'r') as file:
    data = yaml.safe_load(file)

# Print the data
print(data)
print(data['name'])  # Accessing a specific field

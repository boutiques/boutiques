require 'json-schema'

def usage
  puts "validate: [schema_file] [json_file]"
  exit 
end

if ARGV.length != 2
  usage
end

schema_file = ARGV[0]
json_file = ARGV[1]

errors = JSON::Validator.fully_validate(schema_file, File.read(json_file, :validate_schema => true))

errors << "OK" if errors == []
puts "#{errors}"

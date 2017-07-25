import boutiques

print("Good test:")
boutiques.validate_json('./boutiques/schema/example_good.json')

print("\nBad test:")
boutiques.validate_json('./boutiques/schema/example_bad.json')

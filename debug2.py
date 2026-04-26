# Debug: check what's in saved_options['base_price']
from controllers.offer_controller import OfferController

ctrl = OfferController()
offer_data = ctrl.get_offer_with_items(4)
item = offer_data['items'][0]
saved_options = item.get('options', {})

print("=== Debug saved_options ===")
print(f"saved_item['base_price']: {item['base_price']}")
print(f"saved_options['base_price']: {saved_options.get('base_price')}")
print(f"saved_options['final']: {saved_options.get('final')}")
print()
print("This is the problem: saved_options['base_price'] = 15000 (price without options)")
print("But we're using saved_item['base_price'] = 25900 (price WITH options)")
print()
print("Need to use saved_options['base_price'] as base, and show extras_breakdown")
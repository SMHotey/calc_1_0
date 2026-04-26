# Full simulation of what _show_item_details now does
from controllers.offer_controller import OfferController

ctrl = OfferController()
offer_data = ctrl.get_offer_with_items(4)

row = 0
saved_item = offer_data['items'][row]
saved_options = saved_item.get('options', {})

# Init values from DB (the old way)
base_price = saved_item.get('base_price', 0)
final_price = saved_item.get('final_price', 0)
extras_breakdown = saved_options.get('extras_breakdown', []) if isinstance(saved_options, dict) else []

print("=== Initial values from DB ===")
print(f"base_price (from saved_item): {base_price}")
print(f"final_price (from saved_item): {final_price}")
print(f"extras_breakdown: {len(extras_breakdown)} items")

# Apply the fix logic
if extras_breakdown and base_price > 0:
    print("\n>>> Applying fix...")
    
    if isinstance(saved_options, dict) and 'base_price' in saved_options:
        base_price_from_options = saved_options.get('base_price', 0)
        if base_price_from_options > 0:
            print(f"  Setting base_price = saved_options['base_price'] = {base_price_from_options}")
            base_price = base_price_from_options
    
    if isinstance(saved_options, dict) and 'final' in saved_options:
        final_from_options = saved_options.get('final', 0)
        if final_from_options > 0:
            print(f"  Setting final_price = saved_options['final'] = {final_from_options}")
            final_price = final_from_options

print("\n=== FINAL VALUES PASSED TO DIALOG ===")
print(f"base_price: {base_price}")
print(f"final_price: {final_price}")
print(f"extras_breakdown: {extras_breakdown}")

print("\n=== EXPECTED DIALOG DISPLAY ===")
print(f"Базовая стоимость изделия (БЕЗ опций): {base_price}")
print(f"Таблица опций:")
for ex in extras_breakdown:
    print(f"  - {ex['name']}: {ex['price']} (базовый: {ex['base']})")
print(f"Итого: {final_price}")
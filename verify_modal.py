# Full integration test - what actually gets shown in the modal
import sys
sys.path.insert(0, '.')

from controllers.offer_controller import OfferController
from controllers.calculator_controller import CalculatorController
from views.item_details_dialog import ItemDetailsDialog

# Get existing offer with items
offer_ctrl = OfferController()
offers = offer_ctrl.get_all_offers()

if not offers:
    print("No offers found!")
    exit(1)

print("="*60)
print("Available offers:")
for o in offers:
    print(f"  Offer {o['id']}: {o['number']} - {o['total']} rub")

# Get first offer with items
for offer in offers:
    offer_data = offer_ctrl.get_offer_with_items(offer['id'])
    if offer_data and offer_data.get('items'):
        print(f"\n=== Testing with Offer {offer['id']} ({offer_data['number']}) ===")
        print(f"Items count: {len(offer_data['items'])}")
        
        # Test first item
        row = 0
        item = offer_data['items'][row]
        
        print(f"\nItem data from DB:")
        print(f"  product_type: {item['product_type']}")
        print(f"  subtype: {item['subtype']}")
        print(f"  width: {item['width']}, height: {item['height']}")
        print(f"  quantity: {item['quantity']}")
        print(f"  base_price: {item['base_price']}")
        print(f"  final_price: {item['final_price']}")
        print(f"  markup_percent: {item.get('markup_percent')}")
        print(f"  markup_abs: {item.get('markup_abs')}")
        
        saved_options = item.get('options', {})
        print(f"\nSaved options keys: {list(saved_options.keys())}")
        
        # Get extras_breakdown
        extras_breakdown = saved_options.get('extras_breakdown', []) if isinstance(saved_options, dict) else []
        print(f"Extras breakdown count: {len(extras_breakdown)}")
        print(f"Extras breakdown: {extras_breakdown}")
        
        # Simulate what happens in _show_item_details
        markup_pct = item.get('markup_percent', 0) or 0
        markup_abs = item.get('markup_abs', 0) or 0
        
        # Check if we should recalculate
        base_price = item.get('base_price', 0)
        
        if extras_breakdown and base_price > 0:
            print("\n>>> Using saved extras_breakdown directly (NOT recalculating)")
            final_extras = extras_breakdown
            final_base_price = base_price
            final_final_price = item['final_price']
        else:
            print("\n>>> Recalculating...")
            calc = CalculatorController()
            
            result = calc.validate_and_calculate(
                product_type=item['product_type'],
                subtype=item['subtype'],
                height=item['height'],
                width=item['width'],
                price_list_id=1,
                options=saved_options,
                markup_percent=markup_pct,
                markup_abs=markup_abs,
                quantity=item['quantity']
            )
            
            if result.get('success'):
                final_base_price = result.get('price_per_unit', 0)
                final_final_price = result.get('total_price', 0)
                final_extras = result.get('details', {}).get('extras_breakdown', [])
                print(f"Calculated: base={final_base_price}, final={final_final_price}")
                print(f"Calc extras: {final_extras}")
            else:
                print(f"Calc error: {result.get('error')}")
                final_base_price = base_price
                final_final_price = item['final_price']
                final_extras = []
        
        # What gets passed to dialog
        print("\n=== DATA PASSED TO DIALOG ===")
        print(f"base_price: {final_base_price}")
        print(f"final_price: {final_final_price}")
        print(f"extras_breakdown: {final_extras}")
        
        # Now test the dialog directly
        print("\n=== TESTING DIALOG ===")
        dialog_data = {
            "product_type": f"{item['product_type']} {item['subtype']}",
            "width": int(item['width']),
            "height": int(item['height']),
            "quantity": item['quantity'],
            "base_price": final_base_price,
            "final_price": final_final_price,
            "markup": item.get('markup', ''),
            "options": saved_options,
            "extras_breakdown": final_extras
        }
        
        # Create dialog (but don't show - just check what it would display)
        print(f"\nDialog would receive:")
        print(f"  base_price: {dialog_data['base_price']}")
        print(f"  final_price: {dialog_data['final_price']}")
        print(f"  extras_breakdown ({len(dialog_data['extras_breakdown'])} items):")
        for i, ex in enumerate(dialog_data['extras_breakdown']):
            print(f"    {i+1}. {ex.get('name')}: {ex.get('price')} (base: {ex.get('base')})")
        
        if not dialog_data['extras_breakdown']:
            print("\n*** PROBLEM: No extras_breakdown! ***")
            print("The dialog will show fallback 'Дополнительные опции' instead of detailed breakdown")
        
        break
else:
    print("No items found in any offer")
# Check what happens with the offers the user might be looking at
from controllers.offer_controller import OfferController

ctrl = OfferController()

# Get all offers
offers = ctrl.get_all_offers()

for offer in offers[:5]:
    offer_data = ctrl.get_offer_with_items(offer['id'])
    if offer_data and offer_data.get('items'):
        for i, item in enumerate(offer_data['items'][:2]):
            opts = item.get('options', {})
            base_price = item.get('base_price', 0)
            final_price = item.get('final_price', 0)
            
            has_extras = isinstance(opts, dict) and 'extras_breakdown' in opts and opts['extras_breakdown']
            opts_base = opts.get('base_price', 'N/A') if isinstance(opts, dict) else 'N/A'
            opts_final = opts.get('final', 'N/A') if isinstance(opts, dict) else 'N/A'
            
            print(f"Offer {offer['id']}, Item {i}:")
            print(f"  item.base_price: {base_price}")
            print(f"  item.final_price: {final_price}")
            print(f"  saved_options.base_price: {opts_base}")
            print(f"  saved_options.final: {opts_final}")
            print(f"  has extras_breakdown: {bool(has_extras)}")
            if has_extras:
                for ex in opts['extras_breakdown']:
                    print(f"    - {ex}")
            print()
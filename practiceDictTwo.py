def display_inventory(inventory):
    print("Inventory:")
    item_total = 0
    for item, quantity in inventory.items():
        print(quantity, item)
        item_total += quantity

    if item_total == 0:
        print("There is no more items in the inventory!")
    else:
        print("Total number of items: " + str(item_total))

def add_to_inventory(inventory, added_items):
    print("Updated Inventory:")
    for i in added_items:
        if i not in inventory:
            inventory.setdefault(i, 1)
        else:
            inventory[i] += 1

    return inventory


dragon_loot = ['gold coin', 'dagger', 'gold coin', 'gold coin', 'ruby']
inventory = {'rope' : 1, 'torch' : 6, 'gold coin' : 42, 'dagger' : 1, 'arrow' : 12}
empty_inventory = {'rope' : 0}   

display_inventory(inventory)
display_inventory(empty_inventory)
display_inventory({})

updated_inv = add_to_inventory(inventory, dragon_loot)

display_inventory(updated_inv)
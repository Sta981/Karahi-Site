"""Local food photography, with administrator image choices preserved."""

FOOD_IMAGES = {
    "Samosa Chaat": "samosa-chaat.png",
    "Chicken Pakora": "chicken-pakora.jpg",
    "Papri Chaat": "papri-chaat.jpg",
    "Chicken Karahi": "chicken-karahi.jpg",
    "Lamb Karahi": "lamb-karahi.jpg",
    "Paneer Karahi": "paneer-karahi.jpg",
    "Peshawari Charsi Karahi": "charsi-karahi.jpg",
    "Butter Chicken": "butter-chicken.jpg",
    "Nihari": "nihari.jpg",
    "Daal Makhani": "daal-makhani.jpg",
    "Chana Masala": "chana-masala.jpg",
    "Chicken Tikka": "chicken-tikka.jpg",
    "Seekh Kebab": "seekh-kebab.jpg",
    "Lamb Chops": "lamb-chops.png",
    "Chicken Biryani": "chicken-biryani.jpg",
    "Vegetable Pulao": "vegetable-pulao.jpg",
    "Steamed Basmati": "basmati-rice.jpg",
    "Garlic Naan": "garlic-naan.jpg",
    "Plain Naan": "plain-naan.jpg",
    "Tandoori Roti": "tandoori-roti.jpg",
    "Mango Lassi": "mango-lassi.jpg",
    "Masala Chai": "masala-chai.jpg",
    "Gulab Jamun": "gulab-jamun.jpg",
    "Kheer": "kheer.jpg",
}

SEEDED_ILLUSTRATIONS = {
    f"/static/img/{name}.svg" for name in (
        "starters", "karahi", "curries", "tandoor-bbq", "rice", "breads", "drinks-desserts"
    )
}


def menu_image(item):
    image = item.images[0] if item.images else None
    # Replace the seeded SVG illustrations at display time; keep custom photos.
    if image and image.url and image.url not in SEEDED_ILLUSTRATIONS:
        return image.url
    return "/static/img/food/" + FOOD_IMAGES.get(item.name, "banner.png")

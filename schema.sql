-- Maison Elara database schema (SQLite)

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS newsletter_signups;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    price REAL NOT NULL,
    category TEXT NOT NULL,            -- Clothing | Jewellery | Accessories
    image_url TEXT NOT NULL,
    gallery TEXT DEFAULT '',           -- comma-separated extra image urls
    stock INTEGER NOT NULL DEFAULT 0,
    sizes TEXT DEFAULT '',             -- comma-separated, e.g. "XS,S,M,L,XL"
    colors TEXT DEFAULT '',            -- comma-separated, e.g. "Black,Gold,Ivory"
    is_featured INTEGER NOT NULL DEFAULT 0,
    is_new_arrival INTEGER NOT NULL DEFAULT 0,
    is_best_seller INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    customer_name TEXT NOT NULL,
    email TEXT NOT NULL,
    address TEXT NOT NULL,
    city TEXT NOT NULL,
    postal_code TEXT NOT NULL,
    country TEXT NOT NULL,
    total_price REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',   -- pending | paid | shipped | cancelled
    stripe_session_id TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    quantity INTEGER NOT NULL,
    size TEXT DEFAULT '',
    color TEXT DEFAULT '',
    FOREIGN KEY (order_id) REFERENCES orders (id),
    FOREIGN KEY (product_id) REFERENCES products (id)
);

CREATE TABLE reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT NOT NULL,
    rating INTEGER NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE newsletter_signups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Note: the admin account is created by database.py (init_db), not here,
-- so its password is hashed properly with Werkzeug at setup time.

-- Seed products
INSERT INTO products (name, description, price, category, image_url, stock, sizes, colors, is_featured, is_new_arrival, is_best_seller) VALUES
('The Elara Trench Coat', 'A tailored double-breasted trench in fine Italian wool blend, cut for a sculpted silhouette. Finished with horn buttons and a matching belt.', 2.00, 'Clothing', 'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=900&q=80', 12, 'XS,S,M,L,XL', 'Black,Beige,Ivory', 1, 1, 0),
('Noir Silk Slip Dress', 'A bias-cut silk slip dress with a fluid drape, designed for evenings that call for quiet confidence.', 20.00, 'Clothing', 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=900&q=80', 8, 'XS,S,M,L', 'Black,Gold', 1, 0, 1),
('Cashmere Column Coat', 'Floor-grazing cashmere coat with a minimalist collar and concealed placket. An heirloom piece.', 50.00, 'Clothing', 'https://images.unsplash.com/photo-1544022613-e87ca75a784a?w=900&q=80', 6, 'S,M,L', 'Beige,Black', 0, 1, 0),
('Tailored Wide-Leg Trousers', 'High-waisted wide-leg trousers in a smooth wool crepe, engineered for a longer leg line.', 10.00, 'Clothing', 'https://images.unsplash.com/photo-1509631179647-0177331693ae?w=900&q=80', 15, 'XS,S,M,L,XL', 'Black,Beige', 0, 0, 1),
('Ivory Draped Blouse', 'A silk-charmeuse blouse with a softly draped neckline and mother-of-pearl buttons.', 30.00, 'Clothing', 'https://images.unsplash.com/photo-1485462537746-965f33f7f6a7?w=900&q=80', 10, 'XS,S,M,L', 'Ivory,Black', 1, 0, 0),
('Elara Gold Cascade Necklace', 'An 18k gold-plated cascade necklace, hand-linked and finished with a lobster clasp. Water-resistant plating.', 80.00, 'Jewellery', 'https://images.unsplash.com/photo-1611591437281-460bfbe1220a?w=900&q=80', 20, '', 'Gold', 1, 1, 1),
('Signature Pearl Drop Earrings', 'Freshwater pearls suspended from brushed gold vermeil settings. A quiet statement.', 65.00, 'Jewellery', 'https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?w=900&q=80', 25, '', 'Gold,Pearl', 0, 1, 0),
('Eternity Gold Bangle Set', 'A set of three stackable bangles in polished 18k gold vermeil, designed to be worn together or alone.', 100.00, 'Jewellery', 'https://images.unsplash.com/photo-1611591437281-460bfbe1220a?w=900&q=80', 18, '', 'Gold', 1, 0, 1),
('Onyx Signet Ring', 'A modern signet ring set with a polished black onyx stone in a heavy gold-vermeil band.', 25.00, 'Jewellery', 'https://images.unsplash.com/photo-1605100804763-247f67b3557e?w=900&q=80', 14, '5,6,7,8,9', 'Gold', 0, 0, 0),
('Maison Monogram Cufflinks', 'Engraved monogram cufflinks in brushed gold, presented in a signature Maison Elara box.', 20.00, 'Accessories', 'https://images.unsplash.com/photo-1611652022419-a9419f74343d?w=900&q=80', 22, '', 'Gold,Silver', 0, 1, 0),
('The Elara Leather Tote', 'Structured full-grain leather tote with gold-tone hardware and a suede-lined interior.', 10.00, 'Accessories', 'https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=900&q=80', 9, '', 'Black,Beige,Ivory', 1, 0, 1),
('Silk Gold-Trim Scarf', 'A hand-rolled silk twill scarf finished with a fine gold edge, printed with an original house motif.', 2.00, 'Accessories', 'https://images.unsplash.com/photo-1601924994987-69e26d50dc26?w=900&q=80', 30, '', 'Black,Beige,Gold', 0, 1, 0);

-- Seed reviews
INSERT INTO reviews (customer_name, rating, message) VALUES
('Amara D.', 5, 'Every piece from Maison Elara feels like an investment. The trench coat is impeccably tailored — I get compliments every time.'),
('Sophie L.', 5, 'The gold cascade necklace is even more beautiful in person. Packaging alone felt like a luxury experience.'),
('Priya K.', 5, 'Quiet, timeless, expensive-looking without shouting about it. Exactly what I want from a wardrobe staple.'),
('Isabelle R.', 4, 'Beautiful craftsmanship on the leather tote. Shipping took a little longer than expected, but worth the wait.');

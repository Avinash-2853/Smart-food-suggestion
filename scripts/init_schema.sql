CREATE EXTENSION IF NOT EXISTS earthdistance CASCADE;
CREATE EXTENSION IF NOT EXISTS cube CASCADE;
CREATE EXTENSION IF NOT EXISTS postgis;


CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    password_hash VARCHAR(255), -- NULL if social login only
    cognito_user_id VARCHAR(255) UNIQUE NOT NULL, -- Cognito user ID
    status VARCHAR(50) DEFAULT 'active', -- active, inactive, suspended
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE -- Soft delete
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_cognito_user_id ON users(cognito_user_id);
CREATE INDEX idx_users_status ON users(status);


CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    date_of_birth DATE,
    profile_image_url TEXT,
    preferences JSONB DEFAULT '{}', -- Dietary preferences, cuisine preferences
    notification_preferences JSONB DEFAULT '{
        "email": true,
        "sms": false,
        "push": true
    }',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_user_profiles_preferences ON user_profiles USING GIN(preferences);


CREATE TABLE user_addresses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    label VARCHAR(50) NOT NULL, -- Home, Work, Other
    street_address TEXT NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(50) NOT NULL,
    zip_code VARCHAR(10) NOT NULL,
    country VARCHAR(50) DEFAULT 'USA',
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_addresses_user_id ON user_addresses(user_id);
CREATE INDEX idx_user_addresses_location ON user_addresses USING GIST(
    ll_to_earth(latitude, longitude)
); -- For geospatial queries


CREATE TABLE user_payment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    payment_type VARCHAR(50) NOT NULL, -- card, wallet
    provider VARCHAR(50) NOT NULL, -- stripe, apple_pay, google_pay
    provider_token VARCHAR(255) NOT NULL, -- Tokenized payment method ID
    last_four_digits VARCHAR(4), -- For cards
    card_brand VARCHAR(50), -- visa, mastercard, amex
    expiry_month INTEGER,
    expiry_year INTEGER,
    is_default BOOLEAN DEFAULT FALSE,
    billing_address JSONB, -- Billing address details
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE -- Soft delete
);

CREATE INDEX idx_user_payment_methods_user_id ON user_payment_methods(user_id);
CREATE INDEX idx_user_payment_methods_provider_token ON user_payment_methods(provider_token);


CREATE TABLE restaurants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL, -- URL-friendly identifier
    description TEXT,
    cuisine_types TEXT[] NOT NULL, -- ['Italian', 'Pizza', 'Mediterranean']
    status VARCHAR(50) DEFAULT 'pending', -- pending, active, inactive, suspended
    owner_email VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    website_url TEXT,
    logo_url TEXT,
    cover_image_url TEXT,
    rating_average DECIMAL(3, 2) DEFAULT 0.00, -- 0.00 to 5.00
    rating_count INTEGER DEFAULT 0,
    address JSONB NOT NULL, -- {street, city, state, zip, country, lat, lng}
    operating_hours JSONB NOT NULL, -- {monday: {open: "09:00", close: "22:00"}, ...}
    delivery_zones JSONB NOT NULL, -- [{type: "zip", values: ["10001", "10002"]}, {type: "polygon", coordinates: [...]}]
    minimum_order_amount DECIMAL(10, 2) DEFAULT 0.00,
    delivery_fee DECIMAL(10, 2) DEFAULT 0.00,
    estimated_prep_time INTEGER, -- Minutes
    fssai_license_number VARCHAR(100), -- Food license number
    tax_id VARCHAR(100), -- EIN or tax ID
    bank_account_details JSONB, -- Encrypted bank account info
    onboarding_status VARCHAR(50) DEFAULT 'not_started', -- not_started, in_progress, completed, rejected
    onboarding_completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE -- Soft delete
);

CREATE INDEX idx_restaurants_status ON restaurants(status);
CREATE INDEX idx_restaurants_cuisine_types ON restaurants USING GIN(cuisine_types);
CREATE INDEX idx_restaurants_slug ON restaurants(slug);
CREATE INDEX idx_restaurants_location ON restaurants USING GIST(
    ll_to_earth((address->>'latitude')::DECIMAL, (address->>'longitude')::DECIMAL)
);


CREATE TABLE restaurant_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL, -- owner, manager, staff
    permissions JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(restaurant_id, user_id)
);

CREATE INDEX idx_restaurant_users_restaurant_id ON restaurant_users(restaurant_id);
CREATE INDEX idx_restaurant_users_user_id ON restaurant_users(user_id);


CREATE TABLE menu_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    menu_type VARCHAR(50) DEFAULT 'regular', -- regular, catering
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_menu_categories_restaurant_id ON menu_categories(restaurant_id);
CREATE INDEX idx_menu_categories_menu_type ON menu_categories(menu_type);


CREATE TABLE menu_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    category_id UUID REFERENCES menu_categories(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    image_url TEXT,
    category VARCHAR(50), -- starter, main, dessert, drink, side
    dietary_tags TEXT[] DEFAULT '{}', -- ['vegetarian', 'vegan', 'gluten-free', 'halal']
    allergens TEXT[] DEFAULT '{}', -- ['peanuts', 'dairy', 'eggs']
    nutritional_info JSONB, -- {calories, protein, carbs, fat, ...}
    spice_level INTEGER DEFAULT 0, -- 0-5
    is_available BOOLEAN DEFAULT TRUE,
    availability_schedule JSONB, -- {monday: {start: "09:00", end: "22:00"}, ...}
    minimum_quantity INTEGER DEFAULT 1, -- For catering
    serves_people INTEGER, -- Number of people this serves (for catering)
    tags TEXT[] DEFAULT '{}', -- ['spicy', 'popular', 'new', 'corporate-friendly']
    search_keywords TEXT[], -- For search optimization
    rating_average DECIMAL(3, 2) DEFAULT 0.00,
    rating_count INTEGER DEFAULT 0,
    order_count INTEGER DEFAULT 0, -- Popularity metric
    menu_type VARCHAR(50) DEFAULT 'regular', -- regular, catering
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE -- Soft delete
);

CREATE INDEX idx_menu_items_restaurant_id ON menu_items(restaurant_id);
CREATE INDEX idx_menu_items_category_id ON menu_items(category_id);
CREATE INDEX idx_menu_items_menu_type ON menu_items(menu_type);
CREATE INDEX idx_menu_items_is_available ON menu_items(is_available);
CREATE INDEX idx_menu_items_dietary_tags ON menu_items USING GIN(dietary_tags);
CREATE INDEX idx_menu_items_tags ON menu_items USING GIN(tags);
CREATE INDEX idx_menu_items_search_keywords ON menu_items USING GIN(search_keywords);
CREATE INDEX idx_menu_items_price ON menu_items(price);


CREATE TABLE menu_item_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    menu_item_id UUID NOT NULL REFERENCES menu_items(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL, -- Small, Large, Regular, Spicy
    price_modifier DECIMAL(10, 2) DEFAULT 0.00, -- Additional price
    is_default BOOLEAN DEFAULT FALSE,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_menu_item_variants_menu_item_id ON menu_item_variants(menu_item_id);


CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(50) UNIQUE NOT NULL, -- Human-readable order number
    user_id UUID NOT NULL REFERENCES users(id),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id),
    status VARCHAR(50) NOT NULL DEFAULT 'created', -- created, accepted, preparing, ready, dispatched, delivered, cancelled, failed
    order_type VARCHAR(50) NOT NULL, -- single_restaurant, multi_restaurant
    delivery_mode VARCHAR(50) NOT NULL, -- pickup, home_delivery, corporate
    delivery_address JSONB NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL,
    tax_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    delivery_fee DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    tip_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    discount_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    total_amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    special_instructions TEXT,
    estimated_prep_time INTEGER, -- Minutes
    estimated_delivery_time TIMESTAMP WITH TIME ZONE,
    actual_delivery_time TIMESTAMP WITH TIME ZONE,
    payment_status VARCHAR(50) DEFAULT 'pending', -- pending, authorized, captured, failed, refunded
    payment_method_id UUID REFERENCES user_payment_methods(id),
    payment_gateway_reference_id VARCHAR(255), -- Stripe payment intent ID
    delivery_partner VARCHAR(50), -- doordash, uber, internal
    delivery_tracking_id VARCHAR(255),
    cancellation_reason TEXT,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_restaurant_id ON orders(restaurant_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_order_number ON orders(order_number);
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_orders_payment_status ON orders(payment_status);
-- Partition by created_at for large tables (Phase 2)


CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    menu_item_id UUID NOT NULL REFERENCES menu_items(id),
    menu_item_name VARCHAR(255) NOT NULL, -- Snapshot at time of order
    menu_item_price DECIMAL(10, 2) NOT NULL, -- Snapshot at time of order
    variant_id UUID REFERENCES menu_item_variants(id),
    variant_name VARCHAR(100),
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL,
    special_instructions TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_menu_item_id ON order_items(menu_item_id);


CREATE TABLE order_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL,
    status_message TEXT,
    updated_by VARCHAR(100), -- user_id or system
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_order_status_history_order_id ON order_status_history(order_id);
CREATE INDEX idx_order_status_history_created_at ON order_status_history(created_at);


CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id),
    payment_intent_id VARCHAR(255) UNIQUE NOT NULL, -- Stripe payment intent ID
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(50) NOT NULL, -- pending, processing, succeeded, failed, cancelled, refunded
    payment_method_type VARCHAR(50), -- card, wallet
    payment_method_id UUID REFERENCES user_payment_methods(id),
    gateway VARCHAR(50) NOT NULL, -- stripe, adyen
    gateway_transaction_id VARCHAR(255),
    failure_reason TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_payments_order_id ON payments(order_id);
CREATE INDEX idx_payments_payment_intent_id ON payments(payment_intent_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_gateway_transaction_id ON payments(gateway_transaction_id);


CREATE TABLE refunds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID NOT NULL REFERENCES payments(id),
    order_id UUID NOT NULL REFERENCES orders(id),
    refund_amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(50) NOT NULL, -- pending, processing, succeeded, failed
    gateway_refund_id VARCHAR(255),
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_refunds_payment_id ON refunds(payment_id);
CREATE INDEX idx_refunds_order_id ON refunds(order_id);


CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id),
    user_id UUID NOT NULL REFERENCES users(id),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id),
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(255),
    comment TEXT,
    item_ratings JSONB, -- {menu_item_id: rating, ...}
    is_verified_purchase BOOLEAN DEFAULT TRUE,
    is_moderated BOOLEAN DEFAULT FALSE,
    moderation_status VARCHAR(50) DEFAULT 'pending', -- pending, approved, rejected
    restaurant_response TEXT,
    restaurant_response_at TIMESTAMP WITH TIME ZONE,
    helpful_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE -- Soft delete
);

CREATE INDEX idx_reviews_order_id ON reviews(order_id);
CREATE INDEX idx_reviews_user_id ON reviews(user_id);
CREATE INDEX idx_reviews_restaurant_id ON reviews(restaurant_id);
CREATE INDEX idx_reviews_rating ON reviews(rating);
CREATE INDEX idx_reviews_moderation_status ON reviews(moderation_status);


CREATE TABLE support_tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_number VARCHAR(50) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id),
    restaurant_id UUID REFERENCES restaurants(id),
    order_id UUID REFERENCES orders(id),
    type VARCHAR(50) NOT NULL, -- order_issue, payment_issue, account_issue, general
    priority VARCHAR(50) DEFAULT 'medium', -- low, medium, high, urgent
    status VARCHAR(50) DEFAULT 'open', -- open, in_progress, resolved, closed
    subject VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    assigned_to VARCHAR(100), -- Support agent ID
    resolution TEXT,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_support_tickets_user_id ON support_tickets(user_id);
CREATE INDEX idx_support_tickets_restaurant_id ON support_tickets(restaurant_id);
CREATE INDEX idx_support_tickets_order_id ON support_tickets(order_id);
CREATE INDEX idx_support_tickets_status ON support_tickets(status);
CREATE INDEX idx_support_tickets_ticket_number ON support_tickets(ticket_number);


CREATE TABLE support_ticket_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL REFERENCES support_tickets(id) ON DELETE CASCADE,
    sender_id UUID REFERENCES users(id), -- NULL if system message
    sender_type VARCHAR(50) NOT NULL, -- user, restaurant, support_agent, system
    message TEXT NOT NULL,
    attachments JSONB DEFAULT '[]', -- [{url, filename, type}]
    is_internal BOOLEAN DEFAULT FALSE, -- Internal notes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_support_ticket_messages_ticket_id ON support_ticket_messages(ticket_id);


-- Order Status Enum
CREATE TYPE order_status AS ENUM (
    'created',
    'accepted',
    'preparing',
    'ready',
    'dispatched',
    'delivered',
    'cancelled',
    'failed'
);

-- Payment Status Enum
CREATE TYPE payment_status AS ENUM (
    'pending',
    'authorized',
    'captured',
    'failed',
    'refunded',
    'partially_refunded'
);

-- Restaurant Status Enum
CREATE TYPE restaurant_status AS ENUM (
    'pending',
    'active',
    'inactive',
    'suspended'
);


# NOVELIA BOOKS — DATA DICTIONARY

> **Classification:** Production Database Architecture Reference  
> **Target Database:** MySQL 8.x (Storage Engine: InnoDB, Collation: utf8mb4_unicode_ci)  
> **Total Tables:** 34  
> **ORM Specification:** SQLAlchemy 2.x Declarative  
> **Migration Management:** Alembic  

---

## 1. ARCHITECTURAL OVERVIEW & UNIVERSAL RULES

1. **Monetary Precision:** All currency fields (`price`, `original_price`, `subtotal_amount`, `shipping_fee`, `discount_amount`, `total_amount`, `discount_value`) strictly utilize `DECIMAL(12, 2)` with database-level `CheckConstraint >= 0`. `FLOAT` or `DOUBLE` types are strictly prohibited.
2. **Financial Immutability & Snapshots:** When an order is placed, `order_items` captures static snapshots of `book_title_snapshot`, `book_isbn_snapshot`, `book_sku_snapshot`, and `price_at_purchase`. Modifying or deleting a book in the catalog never alters historical invoices.
3. **Primary Keys:** All transactional tables utilize `BigInteger` auto-incrementing surrogate primary keys (`id`).
4. **Referential Integrity & Delete Cascades:**
   - Orders, order items, payments, and shipments are **NEVER** cascaded upon catalog or user deletion. Foreign keys utilize `ON DELETE RESTRICT` or `ON DELETE SET NULL`.
   - Child components such as `cart_items`, `wishlist_items`, and `book_images` utilize `ON DELETE CASCADE`.
5. **Timezone Uniformity:** All timestamps are recorded in UTC (`DateTime`).
6. **Character Set:** Database, tables, and string columns default to `utf8mb4` to support multi-language book content and Vietnamese Unicode diacritics.

---

## 2. TABLE SPECIFICATIONS BY DOMAIN

### A. USERS & ACCESS

#### 1. `roles`
- **Purpose:** System RBAC role definitions (`CUSTOMER`, `STAFF`, `ADMIN`).
- **Columns:**
  | Column | Data Type | Nullable | Default | Constraints / Indexes | Description |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | `id` | `BigInteger` | NO | Auto | PK | Unique surrogate identifier |
  | `name` | `String(50)` | NO | None | Unique, Index | Role name (`CUSTOMER`, `STAFF`, `ADMIN`) |
  | `description` | `String(255)`| YES | None | None | Role description and responsibilities |
  | `created_at` | `DateTime` | NO | UTC Now | None | Record creation timestamp |

#### 2. `users`
- **Purpose:** Customer and staff credentials, authentication state, and core profile.
- **Columns:**
  | Column | Data Type | Nullable | Default | Constraints / Indexes | Description |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | `id` | `BigInteger` | NO | Auto | PK | Unique user identifier |
  | `email` | `String(255)`| NO | None | Unique, Index | User login email |
  | `hashed_password`| `String(255)`| NO | None | None | Bcrypt password hash |
  | `full_name` | `String(150)`| NO | None | None | User's legal or display name |
  | `phone` | `String(20)` | YES | None | None | Primary contact telephone |
  | `is_active` | `Boolean` | NO | `True` | None | Account status flag |
  | `created_at` | `DateTime` | NO | UTC Now | None | Account creation timestamp |
  | `updated_at` | `DateTime` | NO | UTC Now | None | Last profile update timestamp |

#### 3. `user_roles`
- **Purpose:** Many-to-Many association mapping Users to Roles.
- **Columns:**
  | Column | Data Type | Nullable | Default | Constraints / Indexes | Description |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | `id` | `BigInteger` | NO | Auto | PK | Surrogate identifier |
  | `user_id` | `BigInteger` | NO | None | FK (`users.id` CASCADE) | References user |
  | `role_id` | `BigInteger` | NO | None | FK (`roles.id` CASCADE) | References assigned role |
  | `assigned_at` | `DateTime` | NO | UTC Now | None | Timestamp assignment was granted |
- **Table Constraints:** `UniqueConstraint("user_id", "role_id", name="uq_user_role")`.

#### 4. `user_addresses`
- **Purpose:** Customer shipping address notebook for expedited checkout and logistics routing.
- **Columns:**
  | Column | Data Type | Nullable | Default | Constraints / Indexes | Description |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | `id` | `BigInteger` | NO | Auto | PK | Address record ID |
  | `user_id` | `BigInteger` | NO | None | FK (`users.id` CASCADE) | Address owner |
  | `recipient_name`| `String(100)`| NO | None | None | Recipient contact name |
  | `phone` | `String(20)` | NO | None | None | Recipient contact phone |
  | `province_code`| `String(50)` | NO | None | None | Administrative province code |
  | `province_name`| `String(100)`| NO | None | None | Province / City display name |
  | `district_code`| `String(50)` | NO | None | None | District code |
  | `district_name`| `String(100)`| NO | None | None | District display name |
  | `ward_code` | `String(50)` | NO | None | None | Ward code |
  | `ward_name` | `String(100)`| NO | None | None | Ward display name |
  | `street_address`| `String(255)`| NO | None | None | Street name, house number |
  | `is_default` | `Boolean` | NO | `False` | None | Default shipping address flag |
  | `created_at` | `DateTime` | NO | UTC Now | None | Timestamp created |
  | `updated_at` | `DateTime` | NO | UTC Now | None | Timestamp updated |

#### 5. `user_preferences`
- **Purpose:** Stored customer interests, favorite genres/authors, and reading goals for BookMatch AI personalization.
- **Columns:**
  | Column | Data Type | Nullable | Default | Constraints / Indexes | Description |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | `id` | `BigInteger` | NO | Auto | PK | Preference identifier |
  | `user_id` | `BigInteger` | NO | None | FK (`users.id` CASCADE), Unique | One-to-one user association |
  | `preferred_categories` | `JSON` | NO | `[]` | None | Array of category slugs |
  | `preferred_authors` | `JSON` | YES | `[]` | None | Array of author slugs |
  | `reading_goals`| `String(255)`| YES | None | None | Target reading pace or interests |
  | `created_at` | `DateTime` | NO | UTC Now | None | Record created |
  | `updated_at` | `DateTime` | NO | UTC Now | None | Record updated |

---

### B. CATALOG

#### 6. `publishers`
- **Purpose:** Publishing houses producing books in the catalog.
- **Columns:**
  | Column | Data Type | Nullable | Default | Constraints / Indexes | Description |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | `id` | `BigInteger` | NO | Auto | PK | Unique publisher ID |
  | `name` | `String(150)`| NO | None | Unique, Index | Publisher trade name |
  | `slug` | `String(170)`| NO | None | Unique, Index | URL-friendly slug |
  | `contact_info` | `String(255)`| YES | None | None | Email or phone contact |
  | `address` | `String(255)`| YES | None | None | Physical headquarters address |
  | `website` | `String(255)`| YES | None | None | Official homepage URL |
  | `created_at` | `DateTime` | NO | UTC Now | None | Created timestamp |

#### 7. `authors`
- **Purpose:** Biographical and professional metadata of writers and translators.
- **Columns:**
  | Column | Data Type | Nullable | Default | Constraints / Indexes | Description |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | `id` | `BigInteger` | NO | Auto | PK | Unique author ID |
  | `name` | `String(150)`| NO | None | Index | Pen name or legal name |
  | `slug` | `String(170)`| NO | None | Unique, Index | URL-friendly slug |
  | `bio` | `Text` | YES | None | None | Author biography |
  | `avatar_url` | `String(500)`| YES | None | None | Portrait photography link |
  | `birth_year` | `Integer` | YES | None | None | Year of birth |
  | `nationality` | `String(100)`| YES | None | None | Country of origin |
  | `created_at` | `DateTime` | NO | UTC Now | None | Created timestamp |

#### 8. `categories`
- **Purpose:** Hierarchical taxonomy for book classification and navigation.
- **Columns:**
  | Column | Data Type | Nullable | Default | Constraints / Indexes | Description |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | `id` | `BigInteger` | NO | Auto | PK | Unique category ID |
  | `name` | `String(100)`| NO | None | Unique, Index | Genre or category name |
  | `slug` | `String(120)`| NO | None | Unique, Index | URL slug |
  | `description` | `String(255)`| YES | None | None | Brief category summary |
  | `parent_id` | `BigInteger` | YES | None | FK (`categories.id` SET NULL) | Recursive parent category |
  | `display_order`| `Integer` | NO | `0` | None | Sorting priority in menu |
  | `created_at` | `DateTime` | NO | UTC Now | None | Created timestamp |

#### 9. `books`
- **Purpose:** Central entity representing a commercial book publication.
- **Columns:**
  | Column | Data Type | Nullable | Default | Constraints / Indexes | Description |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | `id` | `BigInteger` | NO | Auto | PK | Unique book ID |
  | `isbn` | `String(20)` | NO | None | Unique, Index | International Standard Book Number |
  | `sku` | `String(50)` | NO | None | Unique, Index | Stock Keeping Unit |
  | `title` | `String(255)`| NO | None | Index | Title of publication |
  | `slug` | `String(280)`| NO | None | Unique, Index | URL slug |
  | `publisher_id` | `BigInteger` | NO | None | FK (`publishers.id` RESTRICT) | Publisher reference |
  | `price` | `DECIMAL(12,2)`| NO | None | Index | Current retail selling price |
  | `original_price`| `DECIMAL(12,2)`| NO | None | None | Original list cover price |
  | `page_count` | `Integer` | YES | None | None | Number of pages |
  | `dimension` | `String(50)` | YES | None | None | Size (e.g. `14 x 20.5 cm`) |
  | `weight_grams` | `Integer` | NO | `300` | None | Shipping weight in grams |
  | `cover_type` | `String(30)` | NO | `'PAPERBACK'`| None | `PAPERBACK`, `HARDCOVER` |
  | `description` | `Text` | YES | None | None | Book synopsis & back cover text |
  | `sample_text` | `Text` | YES | None | None | Sample chapter excerpt for preview |
  | `cover_image_url`| `String(500)`| NO | None | None | Primary display cover image URL |
  | `status` | `String(30)` | NO | `'ACTIVE'` | Index | `DRAFT`, `ACTIVE`, `OUT_OF_STOCK`, `DISCONTINUED` |
  | `published_date`| `Date` | YES | None | None | Official release date |
  | `created_at` | `DateTime` | NO | UTC Now | None | Creation timestamp |
  | `updated_at` | `DateTime` | NO | UTC Now | None | Last update timestamp |

#### 10. `book_authors`
- **Purpose:** Many-to-Many association between Books and Authors, capturing primary author status and display order.
- **Columns:** `id`, `book_id` (FK), `author_id` (FK), `is_primary` (Boolean), `order_index` (Integer).
- **Constraints:** `UniqueConstraint("book_id", "author_id", name="uq_book_author")`.

#### 11. `book_categories`
- **Purpose:** Many-to-Many association linking Books to one or more Categories.
- **Columns:** `id`, `book_id` (FK), `category_id` (FK).
- **Constraints:** `UniqueConstraint("book_id", "category_id", name="uq_book_category")`.

#### 12. `book_images`
- **Purpose:** Secondary product gallery images and lookbook photography.
- **Columns:** `id`, `book_id` (FK), `image_url` (String(500)), `alt_text` (String(255)), `display_order` (Integer), `is_cover` (Boolean), `created_at`.

---

### C. INVENTORY

#### 13. `inventory`
- **Purpose:** Real-time physical and reserved stock quantities per book item.
- **Columns:**
  | Column | Data Type | Nullable | Default | Constraints / Indexes | Description |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | `id` | `BigInteger` | NO | Auto | PK | Unique inventory record |
  | `book_id` | `BigInteger` | NO | None | FK (`books.id` CASCADE), Unique | Referenced book |
  | `physical_stock` | `Integer` | NO | `0` | Check `physical_stock >= 0` | Total stock physically in warehouse |
  | `reserved_stock` | `Integer` | NO | `0` | Check `reserved_stock >= 0` | Stock held for pending orders |
  | `low_stock_threshold`| `Integer`| NO | `10` | None | Warning threshold for reorder alerts |
  | `updated_at` | `DateTime` | NO | UTC Now | None | Last stock change timestamp |
- **Check Constraints:** `CheckConstraint("physical_stock >= reserved_stock", name="chk_inventory_non_negative")`.
- **Available Stock Calculation:** `physical_stock - reserved_stock`.

#### 14. `inventory_transactions`
- **Purpose:** Complete audit trail for every inventory movement (import, order hold, release, export, manual adjustments).
- **Columns:** `id`, `inventory_id` (FK), `transaction_type` (`IMPORT`, `EXPORT`, `ORDER_HOLD`, `ORDER_RELEASE`, `ADJUSTMENT`), `quantity_change`, `stock_after`, `reference_code`, `notes`, `created_by_user_id` (FK), `created_at`.

---

### D. COMMERCE

#### 15. `carts` & 16. `cart_items`
- **Purpose:** Persistent shopping cart storage per authenticated customer.
- **`carts` Columns:** `id`, `user_id` (FK, Unique), `created_at`, `updated_at`.
- **`cart_items` Columns:** `id`, `cart_id` (FK), `book_id` (FK), `quantity` (Integer > 0), `added_at`, `updated_at`.
- **Constraints:** `UniqueConstraint("cart_id", "book_id")`, `CheckConstraint("quantity > 0")`.

#### 17. `wishlists` & 18. `wishlist_items`
- **Purpose:** Customer saved book lists and gift registries.
- **`wishlists` Columns:** `id`, `user_id` (FK), `name`, `is_public`, `created_at`, `updated_at`.
- **`wishlist_items` Columns:** `id`, `wishlist_id` (FK), `book_id` (FK), `added_at`.
- **Constraints:** `UniqueConstraint("wishlist_id", "book_id")`.

#### 19. `orders`
- **Purpose:** Master retail order document containing immutable totals and delivery snapshots.
- **Columns:**
  | Column | Data Type | Nullable | Default | Constraints / Indexes | Description |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | `id` | `BigInteger` | NO | Auto | PK | Order record ID |
  | `order_code` | `String(50)` | NO | None | Unique, Index | Public alphanumeric tracking code (e.g. `ORD-20261020-001`) |
  | `user_id` | `BigInteger` | NO | None | FK (`users.id` RESTRICT), Index | Customer account placing order |
  | `subtotal_amount`| `DECIMAL(12,2)`| NO | None | Check `>= 0` | Gross total of all line items |
  | `shipping_fee` | `DECIMAL(12,2)`| NO | `0.00` | Check `>= 0` | Carrier delivery charges |
  | `discount_amount`| `DECIMAL(12,2)`| NO | `0.00` | Check `>= 0` | Deductions from promotional vouchers |
  | `total_amount` | `DECIMAL(12,2)`| NO | None | Check `>= 0` | Net payable balance: `subtotal + shipping - discount` |
  | `status` | `String(30)` | NO | `'PENDING'` | Index | Order lifecycle state |
  | `recipient_name`| `String(100)`| NO | None | None | Shipping recipient contact name |
  | `recipient_phone`| `String(20)` | NO | None | None | Shipping recipient contact phone |
  | `shipping_province`| `String(100)`| NO | None | None | Destination province snapshot |
  | `shipping_district`| `String(100)`| NO | None | None | Destination district snapshot |
  | `shipping_ward` | `String(100)`| NO | None | None | Destination ward snapshot |
  | `shipping_street_address`| `String(255)`| NO | None | None | Street and house address snapshot |
  | `customer_notes`| `Text` | YES | None | None | Special instructions from customer |
  | `staff_notes` | `Text` | YES | None | None | Private operational notes |
  | `cancelled_reason`| `String(255)`| YES | None | None | Reason if order was cancelled |
  | `created_at` | `DateTime` | NO | UTC Now | Index | Order submission timestamp |
  | `updated_at` | `DateTime` | NO | UTC Now | None | Last state transition timestamp |
- **Order Lifecycle States:**
  - `PENDING`: Order placed, waiting for payment confirmation or inventory allocation.
  - `CONFIRMED`: Payment verified or COD order accepted by staff.
  - `PROCESSING`: Items picked from warehouse and packaged.
  - `SHIPPING`: Handed over to shipping carrier (GHN/GHTK).
  - `COMPLETED`: Successfully delivered and payment collected.
  - `CANCELLED`: Order cancelled by customer or staff before shipment.
  - `REFUNDED`: Order returned and refund processed.

#### 20. `order_items`
- **Purpose:** Granular order items capturing immutable title, ISBN, SKU, and unit price snapshots.
- **Columns:**
  | Column | Data Type | Nullable | Default | Constraints / Indexes | Description |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | `id` | `BigInteger` | NO | Auto | PK | Line item ID |
  | `order_id` | `BigInteger` | NO | None | FK (`orders.id` CASCADE) | Parent order |
  | `book_id` | `BigInteger` | YES | None | FK (`books.id` SET NULL) | Catalog reference (preserves history if deleted) |
  | `book_title_snapshot`| `String(255)`| NO | None | None | Exact book title at time of checkout |
  | `book_isbn_snapshot` | `String(20)` | NO | None | None | Exact ISBN at time of checkout |
  | `book_sku_snapshot` | `String(50)` | NO | None | None | Exact SKU at time of checkout |
  | `price_at_purchase` | `DECIMAL(12,2)`| NO | None | Check `>= 0` | Price per unit charged to customer |
  | `quantity` | `Integer` | NO | None | Check `> 0` | Number of units purchased |
  | `subtotal` | `DECIMAL(12,2)`| NO | None | Check `>= 0` | `price_at_purchase * quantity` |
  | `created_at` | `DateTime` | NO | UTC Now | None | Created timestamp |

#### 21. `coupons` & 22. `coupon_usages`
- **Purpose:** Marketing discount vouchers and redemption auditing.
- **`coupons` Columns:** `id`, `code` (Unique), `discount_type` (`PERCENTAGE`, `FIXED_AMOUNT`), `discount_value`, `min_order_value`, `max_discount_value`, `usage_limit`, `used_count`, `start_date`, `end_date`, `is_active`, `created_at`, `updated_at`.
- **`coupon_usages` Columns:** `id`, `coupon_id` (FK), `user_id` (FK), `order_id` (FK), `discount_applied`, `used_at`.
- **Constraints:** `UniqueConstraint("coupon_id", "order_id")`.

---

### E. PAYMENT & SHIPPING

#### 23. `payments`
- **Purpose:** Electronic and COD payment transactions linked to orders.
- **Columns:** `id`, `payment_code` (Unique), `order_id` (FK, Unique), `payment_method` (`COD`, `VNPAY`, `MOMO`, `ZALOPAY`, `BANK_TRANSFER`), `payment_status` (`PENDING`, `PAID`, `FAILED`, `REFUNDED`), `amount` (DECIMAL), `transaction_id`, `gateway_response` (JSON), `paid_at`, `created_at`, `updated_at`.

#### 24. `refund_requests`
- **Purpose:** Formal customer refund claims and managerial approvals.
- **Columns:** `id`, `refund_code` (Unique), `order_id` (FK), `payment_id` (FK), `amount`, `reason`, `status` (`PENDING`, `APPROVED`, `REJECTED`, `COMPLETED`), `admin_notes`, `processed_by_user_id` (FK), `processed_at`, `created_at`, `updated_at`.

#### 25. `shipments` & 26. `shipment_events`
- **Purpose:** Carrier dispatch tracking and real-time webhook checkpoint logs.
- **`shipments` Columns:** `id`, `tracking_code` (Unique), `order_id` (FK, Unique), `carrier` (`GHN`, `GHTK`, `INTERNAL`), `shipping_service_id`, `shipping_fee`, `status` (`PENDING`, `READY_TO_PICK`, `PICKING`, `IN_TRANSIT`, `DELIVERED`, `RETURNED`, `FAILED`), `estimated_delivery_date`, `dispatched_at`, `delivered_at`, `created_at`, `updated_at`.
- **`shipment_events` Columns:** `id`, `shipment_id` (FK), `status`, `location`, `description`, `raw_payload` (JSON), `occurred_at`, `created_at`.

---

### F. CUSTOMER EXPERIENCE

#### 27. `reviews`
- **Purpose:** 1-to-5 star ratings, feedback comments, and verified purchase markers.
- **Columns:** `id`, `user_id` (FK), `book_id` (FK), `order_id` (FK nullable), `rating` (Integer 1-5), `title`, `comment`, `is_verified_purchase`, `status` (`PENDING`, `APPROVED`, `HIDDEN`), `created_at`, `updated_at`.
- **Constraints:** `UniqueConstraint("user_id", "book_id")`, `CheckConstraint("rating >= 1 AND rating <= 5")`.

#### 28. `notifications`
- **Purpose:** In-app real-time alerts for order status changes, promotional campaigns, and stock notifications.
- **Columns:** `id`, `user_id` (FK), `title`, `message`, `notification_type` (`ORDER`, `PROMOTION`, `SYSTEM`, `INVENTORY`), `reference_link`, `is_read`, `read_at`, `created_at`.

---

### G. AI ECOSYSTEM

#### 29. `ai_conversations` & 30. `ai_messages`
- **Purpose:** Full dialogue history for Novelia AI Assistant and BookMatch advisory sessions.
- **`ai_conversations` Columns:** `id`, `session_uuid` (Unique), `user_id` (FK nullable), `conversation_type` (`ASSISTANT`, `BOOKMATCH`), `title`, `created_at`, `updated_at`.
- **`ai_messages` Columns:** `id`, `conversation_id` (FK), `sender` (`USER`, `ASSISTANT`, `SYSTEM`, `TOOL`), `content`, `tool_calls` (JSON), `tool_results` (JSON), `tokens_used`, `created_at`.

#### 31. `ai_action_logs`
- **Purpose:** Strict audit log for all backend tool executions triggered by the AI agent.
- **Columns:** `id`, `conversation_id` (FK), `user_id` (FK), `user_role` (`CUSTOMER`, `STAFF`, `ADMIN`), `tool_name`, `input_arguments` (JSON), `execution_status` (`SUCCESS`, `REJECTED_RBAC`, `FAILED_VALIDATION`, `ERROR`, `CONFIRMATION_REQUIRED`), `confirmation_token`, `is_confirmed`, `output_summary`, `execution_duration_ms`, `created_at`.

#### 32. `user_book_events`
- **Purpose:** Telemetry for personalization and recommendation ranking.
- **Columns:** `id`, `user_id` (FK nullable), `session_id`, `book_id` (FK), `event_type` (`VIEW`, `SEARCH_CLICK`, `ADD_TO_CART`, `WISHLIST`, `PURCHASE`), `metadata_json`, `created_at`.

#### 33. `book_recommendations`
- **Purpose:** Precomputed user recommendation scores.
- **Columns:** `id`, `user_id` (FK), `book_id` (FK), `algorithm_type` (`COLLABORATIVE`, `CONTENT_BASED`, `BOOKMATCH_AI`, `TRENDING`), `score` (`DECIMAL(5, 4)` between 0.0000 and 1.0000), `reason`, `generated_at`.
- **Constraints:** `UniqueConstraint("user_id", "book_id", "algorithm_type")`, `CheckConstraint("score >= 0.0000 AND score <= 1.0000")`.

---

### H. SYSTEM AUDITING

#### 34. `audit_logs`
- **Purpose:** Immutable administrative action log for security forensics, role promotions, and inventory adjustments.
- **Columns:** `id`, `user_id` (FK nullable), `action`, `entity_type`, `entity_id`, `old_values` (JSON), `new_values` (JSON), `ip_address`, `user_agent`, `created_at`.

## Table `schema_migrations`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `filename` | `text` | Primary |
| `hash` | `text` |  |
| `applied_at` | `timestamptz` |  |

## Table `customers`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `email` | `text` |  Unique |
| `full_name` | `text` |  |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |
| `password_hash` | `text` |  |
| `role` | `text` |  |

## Table `tickets`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `customer_id` | `uuid` |  |
| `subject` | `text` |  |
| `status` | `text` |  |
| `priority` | `text` |  |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |

## Table `conversations`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `ticket_id` | `uuid` |  |
| `role` | `text` |  |
| `content` | `text` |  |
| `created_at` | `timestamptz` |  |

## Table `products`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `name` | `text` |  |
| `description` | `text` |  |
| `price` | `numeric` |  |
| `sku` | `text` |  Unique |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |

## Table `orders`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `customer_id` | `uuid` |  |
| `status` | `text` |  |
| `total` | `numeric` |  |
| `shipping_address` | `text` |  |
| `tracking_number` | `text` |  |
| `notes` | `text` |  |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |

## Table `order_items`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `order_id` | `uuid` |  |
| `product_id` | `uuid` |  |
| `quantity` | `int4` |  |
| `unit_price` | `numeric` |  |
| `created_at` | `timestamptz` |  |

## Table `subscriptions`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `customer_id` | `uuid` |  |
| `plan_name` | `text` |  |
| `status` | `text` |  |
| `price` | `numeric` |  |
| `started_at` | `timestamptz` |  |
| `next_billing` | `timestamptz` |  Nullable |
| `cancelled_at` | `timestamptz` |  Nullable |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |

## Table `invoices`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `customer_id` | `uuid` |  |
| `subscription_id` | `uuid` |  Nullable |
| `order_id` | `uuid` |  Nullable |
| `amount` | `numeric` |  |
| `status` | `text` |  |
| `due_date` | `timestamptz` |  |
| `paid_at` | `timestamptz` |  Nullable |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |

## Table `customer_addresses`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `customer_id` | `uuid` |  |
| `label` | `text` |  |
| `street` | `text` |  |
| `city` | `text` |  |
| `state` | `text` |  |
| `zip` | `text` |  |
| `country` | `text` |  |
| `is_default` | `bool` |  |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |

## Table `account_metadata`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `customer_id` | `uuid` |  Unique |
| `email_verified` | `bool` |  |
| `phone_verified` | `bool` |  |
| `two_factor_enabled` | `bool` |  |
| `account_locked` | `bool` |  |
| `last_login_at` | `timestamptz` |  Nullable |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |

## Table `product_specifications`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `product_id` | `uuid` |  |
| `key` | `text` |  |
| `value` | `text` |  |
| `created_at` | `timestamptz` |  |

## Table `product_warranties`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `product_id` | `uuid` |  Unique |
| `duration_months` | `int4` |  |
| `terms` | `text` |  |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |

## Table `inventory`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `uuid` | Primary |
| `product_id` | `uuid` |  Unique |
| `stock_count` | `int4` |  |
| `low_stock` | `int4` |  |
| `updated_at` | `timestamptz` |  |


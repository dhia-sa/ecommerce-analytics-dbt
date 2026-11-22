-- Total paid should equal item prices + freight (within 1 BRL).
-- About 0.25% of orders differ (vouchers, installment interest), so this test only warns.
{{ config(severity = 'warn', warn_if = '>500', error_if = '>2000') }}

select
    order_id,
    order_value,
    total_payment,
    abs(order_value - total_payment) as difference
from {{ ref('fct_orders') }}
where item_count > 0
  and total_payment is not null
  and abs(order_value - total_payment) > 1
